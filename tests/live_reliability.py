"""Run inside the order container in the disposable local lab. Leaves labelled evidence."""
import json
import time
import uuid
from urllib.request import Request, urlopen

import pika
from sqlalchemy import text
from app.main import runtime

run = 'reliability-' + uuid.uuid4().hex[:8]


def request(path, payload=None, key=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Idempotency-Key'] = key
    with urlopen(Request('http://order-service/orders' + path, data=data, headers=headers), timeout=10) as response:
        return json.load(response)


def terminal(order_id):
    for _ in range(60):
        detail = request('/' + order_id)
        if detail['status'] in ('completed', 'failed'):
            return detail
        time.sleep(1)
    raise AssertionError('Order did not reach terminal state')


with runtime.engine.begin() as connection:
    connection.execute(text('INSERT INTO inventory_items (product_id,quantity) VALUES (:sku,2)'), {'sku':run})
payload = {'customer_id':run, 'items':[{'product_id':run,'quantity':1}]}
first = request('', payload, run)['order_id']
assert request('', payload, run)['order_id'] == first
assert terminal(first)['status'] == 'completed'
with runtime.engine.connect() as connection:
    event = json.loads(connection.execute(text('SELECT payload FROM orders WHERE id=:id'), {'id':first}).scalar_one())
with runtime.connection() as connection:
    channel = connection.channel()
    channel.confirm_delivery()
    for _ in range(5):
        channel.basic_publish(exchange='order.events', routing_key='order.created', body=json.dumps(event), mandatory=True,
                              properties=pika.BasicProperties(delivery_mode=2))
time.sleep(5)
with runtime.engine.connect() as connection:
    assert connection.execute(text('SELECT quantity FROM inventory_items WHERE product_id=:sku'), {'sku':run}).scalar_one() == 1
    assert connection.execute(text('SELECT count(*) FROM payments WHERE order_id=:id'), {'id':first}).scalar_one() == 1
print('PASS: retried HTTP submission returns one order; five duplicate broker deliveries produce one stock deduction and one payment.', flush=True)

# Competing orders for the one remaining unit: PostgreSQL locks prevent overselling.
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(lambda _: request('', payload)['order_id'], range(2)))
states = sorted(terminal(order_id)['status'] for order_id in results)
assert states == ['completed','failed'], states
with runtime.engine.connect() as connection:
    assert connection.execute(text('SELECT quantity FROM inventory_items WHERE product_id=:sku'), {'sku':run}).scalar_one() == 0
print('PASS: competing orders for final unit yield one completed and one failed; stock remains zero.', flush=True)

with runtime.connection() as connection:
    channel = connection.channel()
    channel.confirm_delivery()
    before = channel.queue_declare(queue='inventory.order-created.dead', durable=True).method.message_count
    channel.basic_publish(exchange='', routing_key='inventory.order-created', body=b'{invalid-json', mandatory=True,
                          properties=pika.BasicProperties(delivery_mode=2))
    for _ in range(20):
        after = channel.queue_declare(queue='inventory.order-created.dead', durable=True).method.message_count
        if after > before:
            break
        connection.sleep(1)
    assert after == before + 1
print('PASS: malformed delivery transferred to dead-letter queue; specimen retained for inspection.', flush=True)
print('Evidence customer/product: ' + run)
