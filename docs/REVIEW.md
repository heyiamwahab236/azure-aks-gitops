# Architecture review

Reviewed source: D:/Job Apply/4_Projects/Resume projects/multiservice python project

## What is implemented
- Static HTML/CSS/JavaScript frontend served by Nginx; this folder is not React/TypeScript.
- Four Python/FastAPI services; no Go service found in the inspected source.
- Order publishes order.created after committing an order.
- Inventory consumes order.created, reserves stock and publishes inventory.reserved or inventory.failed.
- Payment consumes inventory.reserved and records a simulated completed payment.
- Notification subscribes to multiple workflow events and records notifications with status sent; no actual email/SMS integration in its handler.
- RabbitMQ durable topic exchange and queues, persistent message flags, manual consumer acknowledgements and reconnect loops.
- Shared PostgreSQL database in the provided Compose configuration, with distinct tables used by each service.
- Docker Compose, Kubernetes manifests, Helm chart and a mocked consumer-recovery test are present. No runtime test performed in this review.

## Important implementation gaps
- Order status never advances beyond created.
- Database commits and event publication are separate; an outbox or other recovery mechanism is needed to address partial failures.
- Duplicate event processing can repeat stock changes and insert duplicate payment/notification records; idempotency needs implementation.
- Inventory lacks concurrency protection and duplicate-product aggregation in an order.
- No real payment failure path or stock compensation flow.
- Helm readiness probes use /health despite workers exposing broker-aware /ready.
- Azure migration, Terraform, CI/CD, Argo CD and production observability are not established by this source tree.

## Diagram interpretation
The PDF and PNG show current source-level behavior. The Azure footer is explicitly a roadmap. Data connections are summarized in a shared persistence panel to avoid clutter. The diagram is not proof of a live deployment.
