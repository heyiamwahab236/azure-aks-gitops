# Existing Minikube deployment

Use the `order-platform` profile and namespace explicitly. This avoids other Kubernetes contexts.

```powershell
minikube start -p order-platform
kubectl --context=order-platform get nodes
kubectl --context=order-platform -n order-platform get pods,pvc
```

## Secrets

`k8s/config/secrets.yaml` is deliberately excluded from Git. The existing cluster requires `postgres-credentials` (including DATABASE_URL) and `rabbitmq-credentials` (RABBITMQ_URL). Preserve the existing secrets and database passwords. For a new cluster, provision credentials locally before deployment; do not commit them.

## Application images

Build all service images in Minikube using the same tag referenced in the manifests. The imported backend manifests reference `portfolio-20260912`; the frontend references `portfolio-20260912`. Prefer a new immutable tag on each update.

```powershell
minikube -p order-platform image build -t order-service:portfolio-20260912 ./services/order-service
minikube -p order-platform image build -t inventory-service:portfolio-20260912 ./services/inventory-service
minikube -p order-platform image build -t payment-service:portfolio-20260912 ./services/payment-service
minikube -p order-platform image build -t notification-service:portfolio-20260912 ./services/notification-service
minikube -p order-platform image build -t order-platform-frontend:portfolio-20260912 ./frontend
```

For an existing cluster, apply only application manifests after reviewing the diff. Do not delete the namespace, PVCs, StatefulSets or Vault storage.

```powershell
kubectl --context=order-platform apply -f k8s/order -f k8s/inventory -f k8s/payment -f k8s/notification -f k8s/frontend
kubectl --context=order-platform -n order-platform port-forward svc/frontend-service 8080:80
```

Run `python tests/smoke.py http://localhost:8080` to create one small test order and verify its payment and notification records. This test consumes one unit of stock.

