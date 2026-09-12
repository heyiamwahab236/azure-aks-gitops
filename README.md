# Event-Driven Order Processing Platform

**Current implementation: Python/FastAPI, JavaScript dashboard, Nginx, RabbitMQ and PostgreSQL.**
Docker Compose, Minikube manifests and a Helm chart are included. AKS, Terraform and Azure Service Bus remain planned migration work; the repository name describes that target.

## Workflow

1. The browser calls APIs through Nginx.
2. Order stores an order and publishes `order.created`.
3. Inventory reserves stock and publishes `inventory.reserved` or `inventory.failed`.
4. Payment consumes reservations, records a simulated payment and publishes `payment.completed`.
5. Notification records several workflow events. It does not send real email or SMS.

All services use separate tables within the shared PostgreSQL application database.

## Repository layout

- `services/`: four backend services and Dockerfiles.
- `frontend/`: static dashboard and Nginx configuration.
- `k8s/`: existing Minikube deployment manifests.
- `helm/order-platform/`: alternative Helm packaging; do not install over existing plain-manifest resources without a migration plan.
- `tests/`: consumer recovery and end-to-end smoke checks.
- `infra/vault/`: existing optional Vault lab configuration.
- `infra/terraform/`, `deploy/argocd/`, `pipelines/`: future work placeholders.

## Run on the existing Minikube cluster

See [Minikube instructions](docs/MINIKUBE.md). Existing data and secrets must be preserved during redeployment.

## Local Docker Compose alternative

Run `docker compose up --build` and open `http://localhost:8080`. Compose and the legacy Helm chart contain disposable lab credentials only; never use those defaults for a public or cloud deployment.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Review and limitations](docs/REVIEW.md)
- [Roadmap](docs/ROADMAP.md)
- [Validation](docs/VALIDATION.md)

No real payment processing or external notification delivery is implemented. Order status currently remains `created`; duplicate-event handling and transactional event publication need improvement.
