import json
import os
from sqlalchemy.exc import OperationalError
import uuid
import time
from datetime import datetime, UTC

import pika
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlmodel import Field as SqlField, SQLModel, Session, create_engine, select


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///orders.db")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE = "order.events"


engine = create_engine(DATABASE_URL, echo=False)
app = FastAPI(title="Order Service", version="0.1.0")


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: str = SqlField(primary_key=True)
    customer_id: str
    status: str
    payload: str
    created_at: datetime


class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    customer_id: str
    items: list[OrderItem]


def publish_event(routing_key: str, event: dict) -> None:
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(event).encode("utf-8"),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )
    connection.close()


@app.on_event("startup")
def on_startup() -> None:
    # Allow database/DNS recovery during a cluster restart.
    for attempt in range(24):
        try:
            SQLModel.metadata.create_all(engine)
            break
        except OperationalError:
            if attempt == 23:
                raise
            time.sleep(5)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "order-service"}


@app.post("/orders", status_code=201)
def create_order(request: CreateOrderRequest) -> dict:
    order_id = f"ord-{uuid.uuid4().hex[:12]}"
    now = datetime.now(UTC)
    event = {
        "event_type": "order.created",
        "order_id": order_id,
        "customer_id": request.customer_id,
        "items": [item.model_dump() for item in request.items],
        "created_at": now.isoformat(),
    }
    order = Order(
        id=order_id,
        customer_id=request.customer_id,
        status="created",
        payload=json.dumps(event),
        created_at=now,
    )
    with Session(engine) as session:
        session.add(order)
        session.commit()

    publish_event("order.created", event)
    return {"order_id": order_id, "status": "created"}


@app.get("/orders")
def list_orders() -> list[dict]:
    with Session(engine) as session:
        orders = session.exec(select(Order)).all()
    return [
        {
            "id": order.id,
            "customer_id": order.customer_id,
            "status": order.status,
            "created_at": order.created_at,
        }
        for order in orders
    ]
