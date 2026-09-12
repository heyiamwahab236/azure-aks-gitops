# Ten-minute demonstration

1. Open the browser dashboard at http://localhost:18080. Explain the four service responsibilities and show the architecture.
2. Submit a one-unit order with a unique demonstration customer. Select it and watch the timeline reach completed. Show the simulated payment and notification records.
3. Submit more than available stock. Show failed status, inventory.failed and its reason, with no payment.
4. Explain the outbox/inbox transaction boundary using shared/runtime.py. Show the duplicate-delivery and competing-stock test results in PORTFOLIO_REPORT.md.
5. Open Grafana at http://localhost:13000/d/order-platform. Show request rate, p95 latency, consumer connections and pending events. Open Prometheus alerts at http://localhost:19090/alerts.
6. Walk through the JMeter before/after evidence. Describe what the DNS logs established and what a laptop test cannot establish about production capacity.
7. Open the GitHub Actions workflow and its available run/report evidence. Explain the difference between SAST, dependency analysis, image scanning, SBOM generation and passive DAST.
8. Show the Helm chart and Argo CD application configuration. Only claim live GitOps reconciliation if its verification is marked complete in the report.
9. Show Terraform validation and explain which Azure details are still required. Do not describe AKS as deployed.

## Optional live recovery drill

With the lab idle and the dashboard port-forward active, run `python tests/broker_outage.py`. It temporarily stops the lab broker, submits an order into the outbox, restores the original replica count in a finally block and verifies completion. It consumes one stock unit. Do not run during another demonstration or load test.

## Interview questions to prepare

- Why can a confirmed event still be delivered twice?
- Where do the business write and inbox/outbox commit together?
- How do row locks prevent two buyers from taking the last unit?
- What happens to a malformed message, and how would you safely replay it after fixing the cause?
- How are dependency vulnerability findings different from proof of exploitability?
- What would need to change before using this with real users, payments or multiple regions?
