# Azure AKS Application with GitOps Delivery

**Status: scaffold only — implementation pending.**

An event-driven order-processing application with Terraform-managed Azure infrastructure and automated delivery.

This repository is initialized for future project files. The items below describe intended scope, not completed or validated functionality.

## Planned scope

- React/TypeScript frontend served by Nginx; Go and Python backend services
- Azure Service Bus messaging and PostgreSQL persistence
- Terraform infrastructure, AKS, ACR, Docker and Helm
- Azure DevOps builds and Git-managed delivery through Argo CD
- Key Vault, scoped access and application monitoring

## Getting started

No application or deployment commands are available yet. Import the actual project files first, then document verified prerequisites and setup commands.

## Documentation

- [Roadmap](docs/ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Demo and evidence](docs/DEMO.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Current limitations

No infrastructure has been provisioned, no CI/CD jobs are enabled, and no scan or test results are claimed by this scaffold.
