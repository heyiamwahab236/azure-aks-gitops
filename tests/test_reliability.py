"""Fast transaction tests. Live PostgreSQL/broker checks are separate acceptance tests."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlmodel import Session, SQLModel, create_engine, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DATABASE_URL', 'sqlite://')
os.environ.setdefault('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
from shared.runtime import Inbox, Outbox, Timeline, emit


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'services/{name}-service/app/main.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


order, inventory, payment, notification = [load(name) for name in ['order', 'inventory', 'payment', 'notification']]


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///' + str(tmp_path / 'test.db'))
    SQLModel.metadata.create_all(engine)
    for module in (order, inventory, payment, notification):
        monkeypatch.setattr(module, 'engine', engine)
        monkeypatch.setattr(module.runtime, 'engine', engine)
    with Session(engine) as session:
        inventory.seed(session)
        session.commit()
    yield engine
    engine.dispose()


def created(order_id='test-order', quantity=1):
    return {'event_type': 'order.created', 'order_id': order_id, 'customer_id': 'test', 'items': [{'product_id': 'sku-1', 'quantity': quantity}]}


def test_duplicate_reservation_has_one_effect(database):
    assert inventory.runtime.process(created())
    assert not inventory.runtime.process(created())
    with Session(database) as session:
        assert session.get(inventory.InventoryItem, 'sku-1').quantity == 99
        assert len(session.exec(select(inventory.InventoryReservation)).all()) == 1
        assert len(session.exec(select(Outbox)).all()) == 1


def test_insufficient_stock_is_atomic(database):
    event = created(quantity=1)
    event['items'].append({'product_id': 'missing', 'quantity': 1})
    inventory.runtime.process(event)
    with Session(database) as session:
        assert session.get(inventory.InventoryItem, 'sku-1').quantity == 100
        assert json.loads(session.exec(select(Outbox)).one().body)['event_type'] == 'inventory.failed'


def test_handler_error_rolls_back_inbox_and_stock(database, monkeypatch):
    def fail(session, event):
        inventory.reserve(session, event)
        raise RuntimeError('crash before commit')
    monkeypatch.setattr(inventory.runtime, 'handler', fail)
    with pytest.raises(RuntimeError):
        inventory.runtime.process(created())
    with Session(database) as session:
        assert session.get(inventory.InventoryItem, 'sku-1').quantity == 100
        assert not session.exec(select(Inbox)).all()
        assert not session.exec(select(Outbox)).all()


def test_unconfirmed_publish_stays_pending(database):
    inventory.runtime.process(created())
    class BrokenChannel:
        def basic_publish(self, **kwargs):
            raise ConnectionError('confirmation lost')
    with pytest.raises(ConnectionError):
        inventory.runtime.publish_pending(BrokenChannel())
    with Session(database) as session:
        assert session.exec(select(Outbox)).one().sent is False


def test_payment_and_notification_deduplicate(database):
    event = {**created(), 'event_type': 'inventory.reserved'}
    payment.runtime.process(event)
    assert not payment.runtime.process(event)
    notification.runtime.process(event)
    assert not notification.runtime.process(event)
    with Session(database) as session:
        assert len(session.exec(select(payment.Payment)).all()) == 1
        assert len(session.exec(select(notification.Notification)).all()) == 1


def test_idempotency_and_out_of_order_status(database):
    request = order.CreateOrderRequest(customer_id='test', items=[{'product_id': 'sku-1', 'quantity': 1}])
    first = order.create_order(request, 'request-key')
    assert order.create_order(request, 'request-key') == first
    changed = order.CreateOrderRequest(customer_id='different', items=request.items)
    with pytest.raises(HTTPException) as error:
        order.create_order(changed, 'request-key')
    assert error.value.status_code == 409
    event = {**created(first['order_id']), 'event_type': 'payment.completed'}
    order.runtime.process(event)
    order.runtime.process({**event, 'event_type': 'inventory.reserved'})
    assert order.order_detail(first['order_id'])['status'] == 'completed'
    assert len(order.order_detail(first['order_id'])['timeline']) == 3


@pytest.mark.parametrize('items', [[], [{'product_id':'sku-1','quantity':0}], [{'product_id':'sku-1','quantity':1.2}], [{'product_id':'sku-1','quantity':1}]*2])
def test_invalid_orders_rejected(items):
    with pytest.raises(ValidationError):
        order.CreateOrderRequest(customer_id='test', items=items)
