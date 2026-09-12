> Historical baseline document. See README.md and PORTFOLIO_REPORT.md for the current implementation.

# Event-Driven Order Processing Platform

Local-first microservices platform using Python, FastAPI, Docker, Kubernetes, and Helm.

Full explanation and migration guide:

```text
docs/PROJECT_GUIDE.md
```

Architecture diagrams:

```text
docs/ARCHITECTURE_DIAGRAMS.md
```

## Services

- `order-service`: accepts orders and publishes `order.created`
- `inventory-service`: reserves stock and publishes `inventory.reserved` or `inventory.failed`
- `payment-service`: processes simulated payment and publishes `payment.completed`
- `notification-service`: consumes events and records notification logs

## Local Architecture

```text
Client
  |
  v
order-service API
  |
  v
RabbitMQ exchange: order.events
  |
  +--> inventory-service
          |
          v
      payment-service
          |
          v
      notification-service

PostgreSQL stores service data.
```

RabbitMQ is used locally as the event broker. In production, the same messaging boundary can be implemented with Azure Service Bus topics and subscriptions.

## Run Locally With Docker Compose

```bash
docker compose up --build
```

Create an order:

```bash
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\":\"cust-1\",\"items\":[{\"product_id\":\"sku-1\",\"quantity\":2}]}"
```

Useful URLs:

- Frontend dashboard: `http://localhost:8080`
- Order API: `http://localhost:8001/docs`
- RabbitMQ UI: `http://localhost:15672` using `guest` / `guest`

## Run On Minikube

Start Minikube:

```bash
minikube start
minikube addons enable ingress
```

Build images inside Minikube:

```bash
minikube image build -t order-service:local ./services/order-service
minikube image build -t inventory-service:local ./services/inventory-service
minikube image build -t payment-service:local ./services/payment-service
minikube image build -t notification-service:local ./services/notification-service
minikube image build -t order-platform-frontend:local ./frontend
```

Install with Helm:

```bash
helm upgrade --install order-platform ./helm/order-platform
```

Port-forward the order API:

```bash
kubectl port-forward svc/order-service 8001:8000
```

Then open:

```text
http://localhost:8001/docs
```

Port-forward the frontend dashboard:

```bash
kubectl port-forward svc/frontend-service 8080:80
```

Then open:

```text
http://localhost:8080
```

## Next Production Step

After the Minikube baseline works, production can add:

- Azure Container Registry
- AKS
- Azure Service Bus
- Azure PostgreSQL Flexible Server
- Azure Key Vault
- Terraform modules
- Azure DevOps pipeline
- ArgoCD GitOps sync
