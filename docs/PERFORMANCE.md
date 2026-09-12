# Local performance evidence - 2026-09-12

JMeter 5.6.3 tested three read-only dashboard endpoints through localhost port forwarding to a single-node Minikube cluster. The final run used 25 users, 100 loops and 7,500 total requests in approximately 141 seconds (53.1 requests/second). It made no order submissions.

| Endpoint | Requests | Errors | p50 ms | p95 ms | Maximum ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Orders | 2,500 | 0 | 221 | 783 | 1,876 |
| Inventory | 2,500 | 0 | 181 | 614 | 1,512 |
| Notifications | 2,500 | 0 | 881 | 1,492 | 2,381 |

The zero-error objective passed. The per-endpoint p95 target of 1,000 ms did not pass for notifications. This is a measured local limitation, not a production capacity claim.

## Diagnosed and corrected

An earlier equivalent run produced 278 errors (3.71%). Application logs showed PostgreSQL hostname-resolution failures; CoreDNS logs showed short database names being forwarded to an upstream resolver that timed out. Explicit fully qualified cluster service names with a trailing dot removed these errors in the final run. Credentials and persistent volumes were preserved.

A five-user baseline had zero errors across 300 requests, with p95 values of 64, 55 and 61 ms respectively. An intermediate rerun was invalidated by a frontend rollout that interrupted port forwarding and is excluded from the comparison.

## Reproduction and limits

Use tests/load/dashboard-read.jmx and tests/load/summarize.py. Raw local evidence: work/load-5.jtl, work/load-25.jtl and work/load-25-release.jtl in the parent workspace. Do not deploy or restart the forwarded pod during a run. These results reflect one run, synthetic records, local forwarding and resource-limited pods; they do not establish sustained production throughput. Investigate notification query size, serialization and CPU saturation before selecting an optimization.
