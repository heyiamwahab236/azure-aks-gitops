# Roadmap

Start with the [implementation plan](IMPLEMENTATION_PLAN.md). Each stage has a checklist and required verification. Use the [stage report template](STAGE_REPORT_TEMPLATE.md) to record results and an interview explanation.

## Existing baseline
- [x] Private repository initialized
- [x] Existing source imported with local secrets excluded
- [x] Initial Minikube redeployment and end-to-end smoke test passed

See [validation evidence](VALIDATION.md). The repeatability and improvement stages below remain open.

## Implementation stages
- [ ] 01 — Repeatable local baseline
- [ ] 02 — Order status, event timeline and failure behavior
- [ ] 03 — Reliable messaging and duplicate-event protection
- [ ] 04 — Kubernetes hardening and Helm alignment
- [ ] 05 — Automated tests and CI
- [ ] 06 — Logs, metrics, dashboards and alerts
- [ ] 07 — JMeter load testing and bottleneck investigation
- [ ] 08 — Security checks, SBOMs and remediation
- [ ] 09 — GitOps delivery and recovery
- [ ] 10 — Terraform infrastructure and Azure migration
- [ ] 11 — Employer-facing documentation and demonstrations

## Next session
Begin stage 01 on the existing order-platform Minikube profile. Rebuild and redeploy from this repository, validate the order flow, and record the results. Preserve database volumes and existing secrets.
