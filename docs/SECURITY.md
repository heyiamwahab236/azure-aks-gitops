# Security verification

The project implements security checks and remediation; it is not a production security certification.

| Method | Tool and scope | Observed result |
| --- | --- | --- |
| SAST | Bandit, service and shared Python source | No medium/high findings |
| SCA | pip-audit, resolved application dependencies | Older Starlette findings fixed; patched set reports zero known findings |
| Container scan | Trivy, OS and installed packages | Python image retains vendor-unfixed high/critical package findings; tracked in evidence/security-summary.json |
| Frontend image | Trivy, replacement unprivileged Nginx base | Zero high/critical findings in replacement base scan |
| SBOM | Trivy CycloneDX | Runtime package inventory generated; CI retains per-image reports |
| Passive DAST | OWASP ZAP baseline against local frontend | CSP and header findings identified and remediated; see final report for rerun result |

The frontend now uses a digest-pinned current unprivileged Nginx image, disables server version disclosure and sends CSP, anti-framing, content-type, permissions and cross-origin isolation headers. Backend images run as UID 10001. Application pods use a read-only root filesystem, no privilege escalation, dropped capabilities, RuntimeDefault seccomp and no service-account token.

The initial backend scan lists 56 high/critical package findings without a vendor fix version. Multiple findings can refer to one CVE across several packages; this is not 56 distinct exploitable application vulnerabilities. These findings are not suppressed or represented as resolved. The CI image gate blocks fixable high/critical findings and retains unfixed findings for review. Rebuild and rescan when upstream fixes become available.

## Remaining controls before real users

Authentication/authorization, TLS, database role separation, encrypted broker transport, durable backups and restore drills, network-policy enforcement, secret rotation and a real payment design remain outside this local portfolio release. The current lab must stay local and contain synthetic data only. Do not claim that a passive baseline scan is an active penetration test.

References: [ZAP baseline scope](https://www.zaproxy.org/docs/docker/baseline-scan/), [Trivy SBOM](https://trivy.dev/docs/latest/target/sbom/).
