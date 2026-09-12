# Portfolio implementation report — 2026-09-12

## Implemented and verified

- Ten transaction tests pass: duplicate handling, atomic stock failure, rollback, unconfirmed-publish recovery, payment/notification deduplication, HTTP idempotency, out-of-order status and invalid inputs.
- Local acceptance checks pass: completed and failed orders have timelines; invalid input is rejected.
- Live PostgreSQL/RabbitMQ checks pass: five duplicate deliveries have one business effect; competing orders cannot oversell; malformed input reaches a dead-letter queue. Evidence product/customer: reliability-7dfd258b.
- Release portfolio-v2-20260912e deploys five stateless components on the existing Minikube lab. Both existing PVC identities and bindings are preserved.
- The additive migration preserved historical records and established deduplication evidence for old orders.
- Prometheus scrapes all four services; Grafana's provisioned order-platform dashboard is available. Alert rules are configured locally.
- Helm lint passes for the application-only chart. Terraform init/fmt/validate passes without Azure resource creation.
- Security scans found and drove dependency/base-image/header remediation. See SECURITY.md for unresolved vendor findings.

## Verification in progress / external dependencies

- Final load run: 7,500 requests, zero errors; notification p95 1,492 ms exceeds the 1,000 ms target. See PERFORMANCE.md.
- Broker outage recovery passed: order ord-1e43ae389894 was accepted while RabbitMQ was down and completed after recovery.
- Draft PR #2 is published. GitHub Actions run 34691690532 could not start because GitHub reports failed account payments or a spending-limit restriction. No remote tests ran.
- Argo CD authenticated with the corrected read-only deploy key and reached Synced/Healthy on stage/portfolio-completion. A deliberate notification-service replica change from one to two was automatically restored to one, verifying self-healing.
- Azure deployment is intentionally pending subscription, region and budget decisions. Terraform validation is not proof of cloud deployment.

## Limitations

Single-node local infrastructure; simulated payment and notification; shared database credentials; no public authentication/TLS; monitoring history is ephemeral. Event transport is at-least-once, with inbox-protected business effects. Dead-letter messages need operator remediation after the retry limit. Historical baseline documents describe earlier behavior and are labelled accordingly.
