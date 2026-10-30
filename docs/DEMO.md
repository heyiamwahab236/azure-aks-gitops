# AKS demo and evidence

The demonstration target is the application running on Azure Kubernetes Service with versioned images, GitOps delivery and monitoring. Azure evidence has not yet been recorded.

## Evidence to collect after deployment

1. Azure resource overview identifying the intended AKS cluster and ACR.
2. Source commit and corresponding image versions.
3. Successful application rollout and ready pods.
4. Order submission followed by inventory reservation, simulated payment and a notification record.
5. Persistent data surviving a controlled workload restart.
6. A reviewed Git change reconciled by Argo CD.
7. Prometheus targets, a Grafana dashboard and a deliberately triggered alert with recovery.

Record actual dates, commands and outcomes. Sanitize account identifiers and credentials before publishing evidence. Describe payments and notifications as simulations.

Historical local results are in [validation](VALIDATION.md). They remain local results and are not relabelled as AKS evidence.
