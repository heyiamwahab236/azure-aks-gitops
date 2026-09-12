# Validation — 12 September 2026

## Environment
Existing Minikube profile and namespace: order-platform. Docker Desktop Linux engine. No Azure deployment performed.

## Results
- Five application images built with tag portfolio-20260912.
- Kubernetes server-side dry run passed for application manifests.
- All five application deployments rolled out successfully.
- Seven pods Running and Ready: frontend, four APIs/workers, PostgreSQL and RabbitMQ.
- Existing PostgreSQL and RabbitMQ PVCs remained Bound and were not replaced.
- End-to-end smoke check passed: ord-719861685f79 reached simulated payment completion and a payment.completed notification record. The check consumed one unit of inventory.
- Mocked consumer recovery checks passed inside inventory, payment and notification containers: DNS retry, readiness transitions and connection cleanup. These are mocked tests, not a live broker outage exercise.

## Browser
During this session the application is forwarded at http://localhost:18080. The forwarding process must remain running.

## Limitations
Order status remains created. Payments are simulated. Notifications are database records. Idempotency, transactional event publication, cloud migration and security hardening remain future work.
