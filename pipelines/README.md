# Delivery validation

The executable workflow is .github/workflows/validate.yml. It uses read-only repository permissions and commit-pinned checkout, Python setup and artifact-upload actions. It runs transaction tests, Bandit, pip-audit, a disposable Compose integration stack, Trivy image scans and CycloneDX SBOMs, a ZAP passive baseline and Helm validation. Reports are kept for fourteen days.

The vulnerability gate fails on fixable HIGH/CRITICAL image findings; unfixed vendor findings remain visible in reports and must be reviewed. ZAP baseline warnings are reported rather than silently described as a clean scan. This is passive DAST, not a penetration test. CI deliberately has no cloud credentials or live Minikube access.

The Compose cleanup applies only to the disposable portfolio-ci project created by the workflow. Never reuse that cleanup command against the persistent Minikube lab.
