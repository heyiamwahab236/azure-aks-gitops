"""Generate credentials only in an empty local order-platform namespace."""
import json
import secrets
import subprocess

KUBE = ['kubectl', '--context=order-platform', '-n', 'order-platform']


def main():
    result = subprocess.run(KUBE + ['get', 'pvc,statefulset,secret', '-o', 'json'],
                            check=True, capture_output=True, text=True)
    if json.loads(result.stdout)['items']:
        raise SystemExit('Refusing: namespace contains storage, StatefulSets or secrets. Preserve existing credentials.')
    db_password, mq_password = secrets.token_hex(24), secrets.token_hex(24)
    records = {
        'postgres-credentials': {
            'POSTGRES_USER': 'app', 'POSTGRES_PASSWORD': db_password,
            'DATABASE_URL': f'postgresql+psycopg://app:{db_password}@postgres:5432/orders',
        },
        'rabbitmq-credentials': {
            'RABBITMQ_DEFAULT_USER': 'app', 'RABBITMQ_DEFAULT_PASS': mq_password,
            'RABBITMQ_URL': f'amqp://app:{mq_password}@rabbitmq:5672/',
        },
    }
    payload = {'apiVersion': 'v1', 'kind': 'List', 'items': [
        {'apiVersion': 'v1', 'kind': 'Secret', 'type': 'Opaque',
         'metadata': {'name': name, 'namespace': 'order-platform'}, 'stringData': values}
        for name, values in records.items()
    ]}
    # Stdin avoids credentials in process arguments; capture errors to avoid payload disclosure.
    result = subprocess.run(KUBE + ['create', '-f', '-'], input=json.dumps(payload), capture_output=True, text=True)
    if result.returncode:
        raise SystemExit('Credential creation failed or was partial. Inspect secret names; do not overwrite credentials.')
    print('Created both lab secrets without printing credentials or saving them to local files.')


if __name__ == '__main__':
    main()
