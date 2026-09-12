import hashlib
import json
import logging
import os
import threading
import time
from datetime import UTC, datetime

import pika
from fastapi import HTTPException, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field as PydanticField
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlmodel import Field, Session, SQLModel, create_engine, select

EXCHANGE = 'order.events'
BINDINGS = {
    'inventory.order-created': ['order.created'],
    'payment.inventory-reserved': ['inventory.reserved'],
    'notification.events': ['order.created', 'inventory.reserved', 'inventory.failed', 'payment.completed'],
    'order.status': ['inventory.reserved', 'inventory.failed', 'payment.completed'],
}
LOG = logging.getLogger('order-platform')
logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger('pika').setLevel(logging.WARNING)
HTTP_TIME = Histogram('platform_http_duration_seconds', 'HTTP latency', ['service', 'method', 'route', 'status'])
EVENTS = Counter('platform_events_total', 'Consumer outcomes', ['service', 'outcome'])
PENDING = Gauge('platform_outbox_pending', 'Unpublished events', ['service'])
CONNECTED = Gauge('platform_consumer_connected', 'Broker consumer connection', ['service'])


def now():
    return datetime.now(UTC)


def log(action, **fields):
    LOG.info(json.dumps({'time': now().isoformat(), 'action': action, **fields}))


class Outbox(SQLModel, table=True):
    __tablename__ = 'platform_outbox'
    id: str = Field(primary_key=True)
    owner: str = Field(index=True)
    body: str
    sent: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=now)


class Inbox(SQLModel, table=True):
    __tablename__ = 'platform_inbox'
    consumer: str = Field(primary_key=True)
    event_key: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=now)


class Timeline(SQLModel, table=True):
    __tablename__ = 'order_timeline'
    id: str = Field(primary_key=True)
    order_id: str = Field(index=True)
    event_type: str
    reason: str | None = None
    created_at: datetime = Field(default_factory=now)


class Idempotency(SQLModel, table=True):
    __tablename__ = 'order_idempotency'
    key: str = Field(primary_key=True)
    request_hash: str
    order_id: str


class Item(BaseModel):
    product_id: str = PydanticField(min_length=1, max_length=100)
    quantity: int = PydanticField(gt=0, le=100000, strict=True)


class Event(BaseModel):
    event_type: str
    order_id: str = PydanticField(min_length=1, max_length=100)
    customer_id: str = PydanticField(min_length=1, max_length=100)
    items: list[Item] | None = None
    reason: str | None = None


def event_key(event):
    # One business transition per order. A republisher cannot bypass dedup with a new UUID.
    return event['order_id'] + ':' + event['event_type']


def lock(session, key):
    if session.bind.dialect.name == 'postgresql':
        value = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big', signed=True)
        session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': value})


def emit(session, owner, event):
    event = {**event, 'created_at': now().isoformat()}
    session.add(Outbox(id=event_key(event), owner=owner, body=json.dumps(event)))


def topology(channel):
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)
    for queue, keys in BINDINGS.items():
        channel.queue_declare(queue=queue, durable=True)
        channel.queue_declare(queue=queue + '.dead', durable=True)
        for key in keys:
            channel.queue_bind(exchange=EXCHANGE, queue=queue, routing_key=key)
    channel.confirm_delivery()


class Runtime:
    def __init__(self, name, queue):
        self.name, self.queue = name, queue
        database_url = make_url(os.environ['DATABASE_URL'])
        if os.getenv('DATABASE_HOST'):
            database_url = database_url.set(host=os.environ['DATABASE_HOST'])
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.connected = threading.Event()
        self.handler = None

    def connection(self):
        params = pika.URLParameters(os.environ['RABBITMQ_URL'])
        if os.getenv('RABBITMQ_HOST'):
            params.host = os.environ['RABBITMQ_HOST']
        params.heartbeat = 30
        params.blocked_connection_timeout = 10
        params.socket_timeout = 5
        return pika.BlockingConnection(params)

    def process(self, event):
        validated = Event.model_validate(event)
        if validated.event_type not in BINDINGS[self.queue]:
            raise ValueError('Unsupported event type')
        if validated.event_type == 'order.created':
            if not validated.items or len({i.product_id for i in validated.items}) != len(validated.items):
                raise ValueError('Order must contain distinct, valid items')
        key = event_key(event)
        with Session(self.engine) as session:
            lock(session, self.name + ':' + key)
            if session.get(Inbox, (self.name, key)):
                return False
            self.handler(session, event)
            session.add(Inbox(consumer=self.name, event_key=key))
            session.commit()
        return True

    def consume(self):
        while True:
            try:
                with self.connection() as connection:
                    channel = connection.channel()
                    topology(channel)
                    channel.basic_qos(prefetch_count=1)

                    def callback(ch, method, properties, body):
                        try:
                            event = json.loads(body)
                            changed = self.process(event)
                            EVENTS.labels(self.name, 'processed' if changed else 'duplicate').inc()
                            log('event_processed', service=self.name, order_id=event['order_id'], event_type=event['event_type'], duplicate=not changed)
                        except Exception as error:
                            headers = dict(properties.headers or {})
                            attempt = int(headers.get('attempt', 0)) + 1
                            invalid = isinstance(error, (ValueError, TypeError, KeyError))
                            dead = invalid or attempt >= 3
                            headers['attempt'] = attempt
                            headers['error_type'] = type(error).__name__
                            # Confirm transfer before acknowledging the original delivery.
                            ch.basic_publish(exchange='', routing_key=self.queue + ('.dead' if dead else ''),
                                             body=body, mandatory=True,
                                             properties=pika.BasicProperties(delivery_mode=2, headers=headers))
                            EVENTS.labels(self.name, 'dead_letter' if dead else 'retry').inc()
                            log('event_failed', service=self.name, error_type=type(error).__name__, attempt=attempt, dead_letter=dead)
                            if not dead:
                                time.sleep(1)
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                    channel.basic_consume(queue=self.queue, on_message_callback=callback)
                    self.connected.set()
                    CONNECTED.labels(self.name).set(1)
                    channel.start_consuming()
            except Exception as error:
                log('consumer_reconnecting', service=self.name, error_type=type(error).__name__)
            finally:
                self.connected.clear()
                CONNECTED.labels(self.name).set(0)
            time.sleep(2)

    def publish_pending(self, channel):
        with Session(self.engine) as session:
            rows = session.exec(select(Outbox).where(Outbox.owner == self.name, Outbox.sent == False)
                                .order_by(Outbox.created_at).limit(50).with_for_update(skip_locked=True)).all()
            for row in rows:
                event = json.loads(row.body)
                channel.basic_publish(exchange=EXCHANGE, routing_key=event['event_type'], body=row.body,
                                      mandatory=True, properties=pika.BasicProperties(delivery_mode=2, message_id=row.id))
                row.sent = True
                session.add(row)
            session.commit()
            pending = session.execute(text('SELECT count(*) FROM platform_outbox WHERE owner=:owner AND sent=false'), {'owner': self.name}).scalar()
            PENDING.labels(self.name).set(pending)

    def publish(self):
        while True:
            try:
                with self.connection() as connection:
                    channel = connection.channel()
                    topology(channel)
                    while connection.is_open:
                        self.publish_pending(channel)
                        connection.sleep(0.25)
            except Exception as error:
                log('outbox_reconnecting', service=self.name, error_type=type(error).__name__)
                # Keep pending metric meaningful during a broker outage.
                try:
                    with Session(self.engine) as session:
                        count = session.execute(text('SELECT count(*) FROM platform_outbox WHERE owner=:owner AND sent=false'), {'owner': self.name}).scalar()
                        PENDING.labels(self.name).set(count)
                except Exception:
                    pass
                time.sleep(2)

    def install(self, app, handler, seed=None):
        self.handler = handler

        @app.on_event('startup')
        def startup():
            for attempt in range(30):
                try:
                    with self.engine.begin() as connection:
                        if self.engine.dialect.name == 'postgresql':
                            connection.execute(text('SELECT pg_advisory_xact_lock(837211)'))
                        SQLModel.metadata.create_all(connection)
                    if seed:
                        with Session(self.engine) as session:
                            lock(session, 'inventory-seed')
                            seed(session)
                            session.commit()
                    break
                except Exception:
                    if attempt == 29:
                        raise
                    time.sleep(2)
            threading.Thread(target=self.consume, daemon=True).start()
            threading.Thread(target=self.publish, daemon=True).start()

        @app.get('/health')
        def health():
            return {'status': 'ok', 'service': self.name}

        @app.get('/ready')
        def ready():
            try:
                with self.engine.connect() as connection:
                    connection.execute(text('SELECT 1'))
            except Exception:
                raise HTTPException(503, 'Database unavailable')
            # Order API can accept into the outbox while RabbitMQ is unavailable.
            if self.name != 'order' and not self.connected.is_set():
                raise HTTPException(503, 'Consumer disconnected')
            return {'status': 'ready'}

        @app.get('/metrics', include_in_schema=False)
        def metrics():
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

        @app.middleware('http')
        async def observe(request, call_next):
            started = time.monotonic()
            response = await call_next(request)
            route = request.scope.get('route')
            if request.url.path != '/metrics':
                HTTP_TIME.labels(self.name, request.method, getattr(route, 'path', 'unmatched'), str(response.status_code)).observe(time.monotonic() - started)
            return response
