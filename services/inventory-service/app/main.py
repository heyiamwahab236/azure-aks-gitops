from datetime import datetime
from fastapi import FastAPI
from sqlmodel import Field, SQLModel, Session, select
from shared.runtime import Runtime, emit, now

runtime = Runtime('inventory', 'inventory.order-created')
engine = runtime.engine
app = FastAPI(title='Inventory Service', version='0.2.0')


class InventoryItem(SQLModel, table=True):
    __tablename__ = 'inventory_items'
    product_id: str = Field(primary_key=True)
    quantity: int


class InventoryReservation(SQLModel, table=True):
    __tablename__ = 'inventory_reservations'
    id: int | None = Field(default=None, primary_key=True)
    order_id: str
    status: str
    created_at: datetime


def reserve(session, event):
    products = {}
    for item in sorted(event['items'], key=lambda item: item['product_id']):
        products[item['product_id']] = session.exec(select(InventoryItem).where(InventoryItem.product_id == item['product_id']).with_for_update()).first()
    failed = any(products[i['product_id']] is None or products[i['product_id']].quantity < i['quantity'] for i in event['items'])
    if not failed:
        for item in event['items']:
            product = products[item['product_id']]
            product.quantity -= item['quantity']
            session.add(product)
    session.add(InventoryReservation(order_id=event['order_id'], status='failed' if failed else 'reserved', created_at=now()))
    emit(session, 'inventory', {**event, 'event_type': 'inventory.failed' if failed else 'inventory.reserved',
                               'reason': 'Insufficient stock or unknown product' if failed else None})


def seed(session):
    for sku, quantity in [('sku-1', 100), ('sku-2', 50)]:
        if session.get(InventoryItem, sku) is None:
            session.add(InventoryItem(product_id=sku, quantity=quantity))


runtime.install(app, reserve, seed)


@app.get('/inventory')
def inventory():
    with Session(engine) as session:
        return session.exec(select(InventoryItem).order_by(InventoryItem.product_id)).all()
