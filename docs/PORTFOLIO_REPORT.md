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

- Final stable load rerun and broker recovery drill are being recorded.
- GitHub CI workflow is implemented; remote run verification is pending publication.
- Argo CD is installed. Private-repository read-only access requires user confirmation before the prepared deploy key can be registered. Reconciliation/drift recovery is not yet claimed.
- Azure deployment is intentionally pending subscription, region and budget decisions. Terraform validation is not proof of cloud deployment.

## Limitations

Single-node local infrastructure; simulated payment and notification; shared database credentials; no public authentication/TLS; monitoring history is ephemeral. Event transport is at-least-once, with inbox-protected business effects. Dead-letter messages need operator remediation after the retry limit. Historical baseline documents describe earlier behavior and are labelled accordingly.
