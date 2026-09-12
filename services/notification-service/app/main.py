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


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///notifications.db")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE = "order.events"
QUEUE = "notification.events"


engine = create_engine(DATABASE_URL, echo=False)
app = FastAPI(title="Notification Service", version="0.1.0")


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: int | None = Field(default=None, primary_key=True)
    order_id: str
    event_type: str
    status: str
    created_at: datetime


def handle_event(channel, method, properties, body) -> None:
    event = json.loads(body)
    with Session(engine) as session:
        session.add(
            Notification(
                order_id=event["order_id"],
                event_type=event["event_type"],
                status="sent",
                created_at=datetime.now(UTC),
            )
        )
        session.commit()
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
            for key in ["order.created", "inventory.reserved", "inventory.failed", "payment.completed", "payment.failed"]:
                channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=key)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE, on_message_callback=handle_event)
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
    threading.Thread(target=consume, daemon=True).start()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "notification-service"}


@app.get("/notifications")
def notifications() -> list[Notification]:
    with Session(engine) as session:
        return session.exec(select(Notification)).all()
