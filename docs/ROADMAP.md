# AKS delivery roadmap

AKS is the primary deployment target. Local tooling supports development and preserves earlier evidence; it is not the destination of the platform design.

## Available application foundation

- [x] Four FastAPI services, Nginx dashboard, RabbitMQ and PostgreSQL.
- [x] Dockerfiles, Kubernetes manifests and a Helm chart.
- [x] Local Kubernetes baseline and smoke-test evidence.
- [x] AKS architecture and delivery documentation.

The local baseline is documented in [validation](VALIDATION.md) and the [Stage 01 report](STAGE_01_REPORT.md).

## Azure platform work

- [ ] Adapt the Helm chart for cloud image references, secrets, persistent storage and readiness.
- [ ] Define Azure networking, ACR, AKS and identities in Terraform.
- [ ] Validate and publish versioned application images through CI.
- [ ] Configure Argo CD for reviewed Helm releases.
- [ ] Add Prometheus metrics, Grafana dashboards and actionable alerts.
- [ ] Deploy an approved Azure environment and verify the complete workflow.
- [ ] Record persistence, recovery, GitOps and alert evidence.
- [ ] Document costs, retained data and resource cleanup.

## Application improvements

- [ ] Correct order status and event timeline.
- [ ] Add duplicate-event protection and reliable event publication.
- [ ] Protect inventory updates against concurrency errors.
- [ ] Expand automated tests, security checks and measured load tests.

See the [detailed plan](IMPLEMENTATION_PLAN.md) for acceptance criteria. No Azure implementation or deployment is marked complete by this documentation update.
