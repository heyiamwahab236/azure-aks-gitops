# AKS delivery and application improvement plan

## Starting point

AKS is the primary platform target. This document records future implementation and acceptance criteria; it does not report an existing AKS deployment. Local development is optional supporting infrastructure.

The application is imported and its existing Minikube deployment passed a smoke test on 12 September 2026. See VALIDATION.md for evidence. That is an initial baseline, not completion of the stages below. Payments are simulated and notifications are database records.

The stages separate application improvements from Azure platform delivery. Select dependencies deliberately, finish the relevant checks and record results before marking work complete. No stage is complete merely because a tool has been installed.

| Stage | Work | Exit criteria | Suggested branch |
|---|---|---|---|
| 01 | Repeatable local setup | Repository rebuild, redeploy and smoke test succeed; setup and secret prerequisites are documented | stage/01-local-baseline |
| 02 | Order status and timeline | Successful, rejected and invalid orders have correct state; timeline agrees with stored events | stage/02-order-workflow |
| 03 | Reliable messaging | Duplicate events do not duplicate effects; accepted orders survive broker failure; poison messages are isolated | stage/03-messaging-reliability |
| 04 | Kubernetes hardening | Probes, resources, graceful shutdown and persistent storage are verified; Helm and manifests agree | stage/04-kubernetes |
| 05 | Tests and CI | Tests, manifest validation and image builds run automatically; an intentionally broken change fails | stage/05-ci |
| 06 | Observability | Trace an order through logs and metrics; trigger and observe an actionable alert | stage/06-observability |
| 07 | Load testing | Reproduce a workload, measure latency/errors/backlog, and compare a justified improvement | stage/07-performance |
| 08 | Secure delivery | Scans and SBOM generation run; a finding is fixed and the rerun passes; thresholds are documented | stage/08-security |
| 09 | GitOps | Reviewed image reference changes deploy through Argo CD; previous application version can be restored | stage/09-gitops |
| 10 | Terraform and Azure | Approved infrastructure plan applies; Azure application flow passes; cleanup is documented | stage/10-azure |
| 11 | Portfolio demonstration | README, diagram, demo and reproduction guide reflect only verified behavior | stage/11-portfolio |

## 01 — Repeatable local baseline

- [ ] Confirm explicit context/profile `order-platform`, namespace, Docker readiness and existing workloads.
- [ ] Record current images and PVC names; preserve original source and existing data.
- [ ] Add a repeatable build/deploy/check script with explicit context and error handling.
- [ ] Document secret creation for a fresh disposable environment without committing credentials.
- [ ] Verify the repository includes every Docker build dependency.
- [ ] Run happy-path smoke test and characterize current out-of-stock and invalid-input behavior.
- [ ] Save commands, results and known limitations in a stage report.

## 02 — Correct order workflow

- [ ] Define allowed order states and transitions before coding.
- [ ] Update order state from downstream events; retain an event timeline.
- [ ] Add order details API and dashboard view.
- [ ] Validate nonempty items and aggregate/reject duplicate products consistently.
- [ ] Test successful orders, unknown products, insufficient stock and malformed input.
- [ ] Keep payments explicitly simulated; define failure simulation and stock release behavior if added.

## 03 — Messaging reliability

- [ ] Introduce stable event IDs and an event envelope with order correlation.
- [ ] Add transactional outbox publishing and publisher confirmation/recovery.
- [ ] Add transactional duplicate-event protection for each consumer.
- [ ] Protect stock updates against concurrent reservation races.
- [ ] Implement bounded retry and dead-letter routing with diagnostic context.
- [ ] Test duplicate deliveries, consumer restart between write and acknowledgement, broker outage and poison messages.
- [ ] Document delivery guarantees and remaining failure windows; do not claim exactly-once transport.

## 04 — Kubernetes hardening

- [ ] Align broker-aware readiness, liveness and startup behavior.
- [ ] Set measured resource requests/limits and graceful termination behavior.
- [ ] Align Helm with plain manifests and define resource ownership before migrating management.
- [ ] Move reusable secret references out of literal chart configuration.
- [ ] Verify persistence and worker restart recovery without deleting volumes.

## 05 — Automated tests and CI

- [ ] Establish unit, database/broker integration and end-to-end tests.
- [ ] Add linting, manifest/chart validation and container builds.
- [ ] Use immutable image versions and record source revision.
- [ ] Prove a failing test prevents release; publish test results.
- [ ] Choose the CI host explicitly; Azure DevOps is the intended primary path for this application.

## 06 — Observability

- [ ] Add structured logs with order/event IDs, without secrets or unnecessary customer data.
- [ ] Add request duration/error metrics and worker throughput/failure/processing-time metrics.
- [ ] Collect broker backlog and consumer metrics.
- [ ] Deploy Prometheus/Grafana and add focused dashboards.
- [ ] Validate a service failure alert and document investigation using the collected evidence.

## 07 — Performance

- [ ] Define JMeter workload, duration, ramp-up, data preparation and success criteria.
- [ ] Measure API latency, error rates and asynchronous completion time separately.
- [ ] Record pod resources and queue backlog alongside load results.
- [ ] Investigate one observed bottleneck and rerun the same workload after a change.
- [ ] Label results as local-lab measurements, not production capacity.

## 08 — Security

- [ ] Add code, dependency, image and configuration scanning incrementally.
- [ ] Generate an SBOM tied to an application/image version.
- [ ] Define blocking thresholds, exceptions, owners and review dates.
- [ ] Review container user/permissions, secret handling and service access boundaries.
- [ ] Demonstrate one finding, remediation and a passing rerun.
- [ ] Add DAST only against the authorized local test deployment after functional tests are stable.

## 09 — GitOps

- [ ] Separate source builds from deployment configuration updates.
- [ ] Use CI to propose a versioned image update in Git.
- [ ] Configure Argo CD to reconcile reviewed Helm configuration.
- [ ] Demonstrate deployment and Git-revert recovery.
- [ ] Document that image rollback does not undo database migrations or already-processed events.

## 10 — Terraform and Azure

- [ ] Confirm subscription, region, spending limit and resource ownership before provisioning.
- [ ] Choose PostgreSQL hosting and networking to fit the development budget.
- [ ] Bootstrap remote Terraform state in Azure Storage and document state access.
- [ ] Build one development environment first: resource group, network, ACR, AKS, persistent PostgreSQL/RabbitMQ storage and scoped identities. Evaluate managed data services and Key Vault separately.
- [ ] Review Terraform plan before apply; do not import or alter unrelated Azure resources.
- [ ] Keep RabbitMQ for the initial AKS deployment. If Azure Service Bus is selected later, implement and test a separate messaging adapter.
- [ ] Verify application identity and access in the actual Azure deployment.
- [ ] Repeat functional, delivery and observability checks; document teardown and resources retained for state/data.

## 11 — Employer presentation

- [ ] Update architecture diagram to match the verified runtime.
- [ ] Record a short normal-flow demo and one failure/recovery demo.
- [ ] Write a concise case study: problem, implementation, evidence, limitation.
- [ ] Check setup from documentation and inspect content before making the repository public.

## Relationship to the other repositories

This repository owns the application and its Azure delivery path. The self-managed Kubernetes lab will reuse a stable service version to demonstrate Linux/Ansible/K3s operations. The secure-delivery repository will reference a stable application version and document reusable security configuration and remediation evidence. Avoid maintaining three divergent copies of the application.

## Working agreement

For future implementation work, prepare a reviewable change, validate it, deploy only to the agreed environment, and record the actual results before marking the stage complete. Keep destructive failure exercises in a disposable environment. Never reset the existing cluster or erase PVCs as routine setup. Do not commit real secrets, Terraform state or private employer material.
