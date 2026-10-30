# AKS project guide

## Purpose

This repository presents an event-driven application with an Azure Kubernetes Service deployment design. Its platform focus is AKS, ACR, Terraform, Helm, Argo CD, Prometheus and Grafana.

The application is implemented. The Azure infrastructure and delivery integrations are planned; existing execution evidence is from the local Kubernetes baseline. This guide describes the project and its Azure direction without claiming an unverified deployment.

## Application components

| Component | Responsibility | Main endpoints |
| --- | --- | --- |
| Nginx dashboard | Present orders, inventory, payments and notifications; proxy API requests | `/`, `/api/orders`, `/api/inventory`, `/api/payments`, `/api/notifications` |
| Order | Store orders and publish `order.created` | `POST /orders`, `GET /orders`, `GET /health` |
| Inventory | Reserve stock and publish success/failure events | `GET /inventory`, `GET /health`, `GET /ready` |
| Payment | Record simulated payments and publish `payment.completed` | `GET /payments`, `GET /health`, `GET /ready` |
| Notification | Record workflow events | `GET /notifications`, `GET /health`, `GET /ready` |
| RabbitMQ | Route events through durable topic exchange and queues | AMQP |
| PostgreSQL | Persist application data in separate service tables | PostgreSQL protocol |

## Azure platform design

1. Terraform defines the resource group, network, AKS, ACR and access assignments.
2. CI validates application and deployment changes, then builds immutable image versions.
3. ACR stores images that AKS retrieves using an appropriately scoped identity.
4. Helm describes the application deployment and persistent data services.
5. Argo CD reconciles the reviewed version of the Helm configuration from Git.
6. Prometheus and Grafana provide metrics, dashboards and alert investigation.

This is the proposed delivery flow. Its infrastructure files and integrations still need implementation and validation.

## Configuration decisions before Azure deployment

- Select the subscription, region, resource names and development budget.
- Replace local image tags with versioned ACR references.
- Move development credentials out of the Helm values and choose secret management.
- Review database/broker persistence and recovery requirements.
- Align readiness probes with the workers' `/ready` endpoints.
- Decide how operators and the dashboard access the cluster and services.
- Configure repository access for Argo CD without committing credentials.
- Preserve resource ownership and data when changing deployment methods.

Moving the existing RabbitMQ application to AKS does not require an Azure Service Bus migration. Any broker replacement is a separate application change.

## Validation and evidence

For a completed Azure demonstration, record the exact source revision and image versions, AKS rollout, a successful order/payment/notification flow, persistence checks, GitOps reconciliation and an observed alert. Keep local and Azure results identified by environment.

- [Existing local validation](VALIDATION.md)
- [Azure evidence checklist](DEMO.md)
- [Delivery roadmap](ROADMAP.md)
- [Detailed plan](IMPLEMENTATION_PLAN.md)

## Optional development environment

Docker Compose and [local Kubernetes instructions](MINIKUBE.md) remain available for application development. Their development credentials and image references are not cloud deployment configuration.

## Known limits

Payments are simulated; notifications are stored records. Order status propagation, idempotent event processing, transactional event publication and inventory concurrency protection remain open application work. See the [source review](REVIEW.md).
