"""Explicit local fault-injection drill; always restores the original RabbitMQ replicas."""
import json
import subprocess
import time
import uuid
from urllib.request import Request, urlopen

KUBE = ['kubectl', '--context=order-platform', '-n', 'order-platform']
BASE = 'http://127.0.0.1:18080/api/'


def kubectl(*args):
    return subprocess.check_output(KUBE + list(args), text=True)


def api(path, payload=None):
    with urlopen(Request(BASE + path, data=None if payload is None else json.dumps(payload).encode(),
                         headers={'Content-Type':'application/json'}), timeout=10) as response:
        return json.load(response)


replicas = json.loads(kubectl('get','statefulset','rabbitmq','-o','json'))['spec']['replicas']
assert replicas == 1, 'Drill expects the single-node lab broker'
product = next(row for row in api('inventory') if row['quantity'] > 0)
try:
    print(kubectl('scale','statefulset/rabbitmq','--replicas=0'), flush=True)
    kubectl('wait','--for=delete','pod/rabbitmq-0','--timeout=90s')
    order = api('orders', {'customer_id':'outage-'+uuid.uuid4().hex[:8], 'items':[{'product_id':product['product_id'],'quantity':1}]})
    time.sleep(5)
    assert api('orders/'+order['order_id'])['status'] == 'created'
    print('PASS: API accepted and persisted order while broker was stopped: '+order['order_id'], flush=True)
finally:
    print(kubectl('scale','statefulset/rabbitmq',f'--replicas={replicas}'), flush=True)
    kubectl('rollout','status','statefulset/rabbitmq','--timeout=180s')
for _ in range(90):
    if api('orders/'+order['order_id'])['status'] == 'completed':
        print('PASS: pending outbox event delivered after broker recovery; order completed.', flush=True)
        break
    time.sleep(1)
else:
    raise SystemExit('FAIL: recovered broker but order did not complete')
