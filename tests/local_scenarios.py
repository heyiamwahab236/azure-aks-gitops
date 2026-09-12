"""Black-box local acceptance tests. Leaves two labelled orders; consumes one stock unit.

Run without concurrent writers. The negative payment assertion has a bounded window.
"""
import json
import sys
import time
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/')
RUN = 'baseline-' + uuid.uuid4().hex[:10]


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(BASE + '/api/' + path, data=data, headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=10) as response:
        return json.load(response)


def check(condition, message):
    if not condition:
        raise SystemExit('FAIL: ' + message)


def wait_event(order_id, event):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        rows = request('notifications')
        if any(row['order_id'] == order_id and row['event_type'] == event for row in rows):
            return
        time.sleep(1)
    raise SystemExit(f'FAIL: {order_id}: no {event} notification within 60 seconds')


product = next((row for row in request('inventory') if row['quantity'] > 0), None)
check(product, 'no stocked product; no orders created')
sku = product['product_id']


def stock():
    return next(row['quantity'] for row in request('inventory') if row['product_id'] == sku)


def order(customer, quantity):
    return request('orders', {'customer_id': customer, 'items': [{'product_id': sku, 'quantity': quantity}]})


before = stock()
happy = order(RUN + '-happy', 1)['order_id']
wait_event(happy, 'payment.completed')
check(any(row['order_id'] == happy and row['status'] == 'completed' for row in request('payments')), 'completed payment missing')
check(stock() == before - 1, 'successful order did not deduct exactly one unit')
print(f'PASS happy: {happy}; payment and notification recorded; stock {before} -> {stock()}', flush=True)

before = stock()
failed = order(RUN + '-out-of-stock', before + 1)['order_id']
wait_event(failed, 'inventory.failed')
deadline = time.monotonic() + 10
while time.monotonic() < deadline:
    check(not any(row['order_id'] == failed for row in request('payments')), 'insufficient-stock order produced a payment')
    check(stock() == before, 'insufficient-stock order changed stock')
    time.sleep(1)
print(f'PASS insufficient stock: {failed}; inventory.failed recorded; stock unchanged; no payment during 10-second observation', flush=True)

for quantity in (0, -1):
    try:
        order(RUN + '-invalid', quantity)
    except HTTPError as error:
        check(error.code == 422, f'quantity {quantity}: expected 422, got {error.code}')
    else:
        raise SystemExit(f'FAIL: quantity {quantity} accepted')
try:
    request('orders', {'customer_id': RUN + '-invalid'})
except HTTPError as error:
    check(error.code == 422, f'missing items: expected 422, got {error.code}')
else:
    raise SystemExit('FAIL: missing items accepted')
orders = request('orders')
check(not any(row['customer_id'] == RUN + '-invalid' for row in orders), 'invalid request persisted an order')
print('PASS invalid input: zero quantity, negative quantity, and missing items return 422; no order persisted', flush=True)
for order_id in (happy, failed):
    row = next(row for row in orders if row['id'] == order_id)
    print(f'OBSERVED order status: {order_id}: {row["status"]} (status propagation is Stage 2)', flush=True)
