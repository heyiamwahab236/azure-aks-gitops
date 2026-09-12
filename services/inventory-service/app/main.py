import json
import logging
import os
from sqlalchemy.exc import OperationalError
import threading
import time
from datetime import datetime, UTC

import pika
from fastapi import FastAPI, HTTPException
from sqlmodel import Field, SQLModel, Session, create_engine, select


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///inventory.db")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE = "order.events"
QUEUE = "inventory.order-created"


engine = create_engine(DATABASE_URL, echo=False)
app = FastAPI(title="Inventory Service", version="0.1.0")


class InventoryItem(SQLModel, table=True):
    __tablename__ = "inventory_items"

    product_id: str = Field(primary_key=True)
    quantity: int


class InventoryReservation(SQLModel, table=True):
    __tablename__ = "inventory_reservations"

    id: int | None = Field(default=None, primary_key=True)
    order_id: str
    status: str
    created_at: datetime


def publish_event(channel, routing_key: str, event: dict) -> None:
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(event).encode("utf-8"),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )


def handle_order_created(channel, method, properties, body) -> None:
    event = json.loads(body)
    order_id = event["order_id"]
    items = event["items"]
    status = "reserved"

    with Session(engine) as session:
        for item in items:
            product = session.get(InventoryItem, item["product_id"])
            if product is None or product.quantity < item["quantity"]:
                status = "failed"
                break

        if status == "reserved":
            for item in items:
                product = session.get(InventoryItem, item["product_id"])
                product.quantity -= item["quantity"]
                session.add(product)

        session.add(InventoryReservation(order_id=order_id, status=status, created_at=datetime.now(UTC)))
        session.commit()

    routing_key = "inventory.reserved" if status == "reserved" else "inventory.failed"
    publish_event(
        channel,
        routing_key,
        {
            "event_type": routing_key,
            "order_id": order_id,
            "customer_id": event["customer_id"],
            "items": items,
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    channel.basic_ack(delivery_tag=method.delivery_tag)


consumer_ready = threading.Event()
logger = logging.getLogger(__name__)


def consume() -> None:
    while True:
        connection = None
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.queue_declare(queue=QUEUE, durable=True)
            channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key="order.created")
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE, on_message_callback=handle_order_created)
            consumer_ready.set()
            channel.start_consuming()
        except (pika.exceptions.AMQPConnectionError, OSError) as exc:
            logger.warning("RabbitMQ unavailable (%s); retrying in 5 seconds", type(exc).__name__)
        finally:
            consumer_ready.clear()
            if connection is not None and connection.is_open:
                try:
                    connection.close()
                except (pika.exceptions.AMQPError, OSError):
                    pass
        time.sleep(5)


@app.get("/ready")
def ready() -> dict:
    if not consumer_ready.is_set():
        raise HTTPException(status_code=503, detail="RabbitMQ consumer is disconnected")
    return {"status": "ready"}


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
    with Session(engine) as session:
        if session.get(InventoryItem, "sku-1") is None:
            session.add(InventoryItem(product_id="sku-1", quantity=100))
            session.add(InventoryItem(product_id="sku-2", quantity=50))
            session.commit()
    threading.Thread(target=consume, daemon=True).start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "inventory-service"}


@app.get("/inventory")
def inventory() -> list[InventoryItem]:
    with Session(engine) as session:
        return session.exec(select(InventoryItem)).all()
