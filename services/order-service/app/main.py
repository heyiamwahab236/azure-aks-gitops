import hashlib
import json
import uuid
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlmodel import Field as SqlField, SQLModel, Session, select
from shared.runtime import Runtime, Item, Timeline, Idempotency, emit, event_key, lock, now

runtime = Runtime('order', 'order.status')
engine = runtime.engine
app = FastAPI(title='Order Service', version='0.2.0')


class Order(SQLModel, table=True):
    __tablename__ = 'orders'
    id: str = SqlField(primary_key=True)
    customer_id: str
    status: str
    payload: str
    created_at: datetime


class CreateOrderRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=100, pattern=r'^\S(?:.*\S)?$')
    items: list[Item] = Field(min_length=1, max_length=50)

    @model_validator(mode='after')
    def distinct_products(self):
        if len({item.product_id for item in self.items}) != len(self.items):
            raise ValueError('Use one item per product')
        return self


def status_event(session, event):
    order = session.exec(select(Order).where(Order.id == event['order_id']).with_for_update()).first()
    if order is None:
        raise RuntimeError('Order not found')
    status = {'inventory.reserved': 'reserved', 'inventory.failed': 'failed', 'payment.completed': 'completed'}[event['event_type']]
    # A delayed reservation must never regress a terminal outcome.
    if order.status not in ('completed', 'failed'):
        order.status = status
        session.add(order)
    session.add(Timeline(id=event_key(event), order_id=order.id, event_type=event['event_type'], reason=event.get('reason')))


runtime.install(app, status_event)


@app.post('/orders', status_code=201)
def create_order(request: CreateOrderRequest, idempotency_key: str | None = Header(default=None, max_length=128)):
    payload = request.model_dump()
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    with Session(engine) as session:
        if idempotency_key:
            lock(session, 'request:' + idempotency_key)
            previous = session.get(Idempotency, idempotency_key)
            if previous:
                if previous.request_hash != digest:
                    raise HTTPException(409, 'Idempotency key already used for different content')
                order = session.get(Order, previous.order_id)
                return {'order_id': order.id, 'status': order.status}
        order_id = 'ord-' + uuid.uuid4().hex[:12]
        event = {'event_type': 'order.created', 'order_id': order_id, **payload}
        session.add(Order(id=order_id, customer_id=request.customer_id, status='created', payload=json.dumps(event), created_at=now()))
        session.add(Timeline(id=event_key(event), order_id=order_id, event_type='order.created'))
        emit(session, 'order', event)
        if idempotency_key:
            session.add(Idempotency(key=idempotency_key, request_hash=digest, order_id=order_id))
        session.commit()
    return {'order_id': order_id, 'status': 'created'}


@app.get('/orders')
def list_orders():
    with Session(engine) as session:
        return [{'id': row.id, 'customer_id': row.customer_id, 'status': row.status, 'created_at': row.created_at}
                for row in session.exec(select(Order).order_by(Order.created_at.desc()).limit(200)).all()]


@app.get('/orders/{order_id}')
def order_detail(order_id: str):
    with Session(engine) as session:
        row = session.get(Order, order_id)
        if row is None:
            raise HTTPException(404, 'Order not found')
        timeline = session.exec(select(Timeline).where(Timeline.order_id == order_id).order_by(Timeline.created_at)).all()
        return {'id': row.id, 'customer_id': row.customer_id, 'status': row.status, 'items': json.loads(row.payload)['items'], 'timeline': timeline}
