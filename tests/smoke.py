"""Create one test order and verify asynchronous payment and notification records."""
import json
import sys
import time
import uuid
from urllib.request import Request, urlopen

base = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/')

def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(base + path, data=data, headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=10) as response:
        return json.load(response)

stock = request('/api/inventory')
product = next((item for item in stock if item['quantity'] > 0), None)
if not product:
    raise SystemExit('FAIL: no stocked product available; no order created.')
order = request('/api/orders', {
    'customer_id': 'smoke-' + uuid.uuid4().hex[:8],
    'items': [{'product_id': product['product_id'], 'quantity': 1}],
})
order_id = order['order_id']
deadline = time.monotonic() + 60
while time.monotonic() < deadline:
    payments = request('/api/payments')
    notifications = request('/api/notifications')
    paid = any(row['order_id'] == order_id and row['status'] == 'completed' for row in payments)
    notified = any(row['order_id'] == order_id and row['event_type'] == 'payment.completed' for row in notifications)
    if paid and notified:
        print(f'PASS: {order_id}: order -> inventory -> simulated payment -> notification record')
        break
    time.sleep(2)
else:
    raise SystemExit(f'FAIL: timed out waiting for payment and notification for {order_id}')
