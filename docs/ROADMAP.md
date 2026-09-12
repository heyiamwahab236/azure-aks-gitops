# Four-stage delivery plan

The original repeatable Minikube baseline is complete. Related follow-up work is grouped into four stages:

| Stage | Scope | Verification |
| --- | --- | --- |
| 1. Complete the application | Status, timeline, failure handling, outbox, deduplication, stock locks | Transaction tests and live order/reliability checks |
| 2. Automate deployment | Containers, probes/resources, Helm, CI and GitOps | Image builds, rollouts, Helm validation and delivery evidence |
| 3. Prove performance and security | Metrics, dashboard/alerts, JMeter, SAST/SCA/image scans/SBOM/DAST | Measured reports and remediation |
| 4. Prepare the portfolio | Architecture, demo, runbooks and optional Azure Terraform | Reviewable documentation and Terraform validation |

See [PORTFOLIO_REPORT.md](PORTFOLIO_REPORT.md) for current verification and remaining dependencies. Azure deployment is optional and requires subscription, region and budget choices. The historical Stage 01 report describes the original baseline, not the current application's limitations.
