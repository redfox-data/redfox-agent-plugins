# Security Policy

## Supported Versions

We maintain the latest state of the `main` branch. All ten plugins ship on the
same `1.0.x` version line; security fixes land on `main` first and are included
in the next tagged release.

| Version            | Supported |
| ------------------ | --------- |
| latest on `main`   | ✅        |
| older commits/tags | ❌        |

## Reporting a Vulnerability

Please do **not** open a public issue for security vulnerabilities.

Email **redfoxdata@proton.me** with:

- the affected plugin ID(s) and commit SHA
- reproduction steps or a proof of concept
- your impact assessment

We acknowledge reports within 2 business days and aim to ship a fix or
mitigation within 14 days. Reporters are credited in the release notes, or kept
anonymous on request.

## Scope

- **In scope:** plugin manifests (`plugin.json`, `marketplace.json`), skill
  definitions (`SKILL.md`), the scripts under `plugins/*/scripts/`, and the CI
  workflows in `.github/workflows/`.
- **Out of scope:** the hosted Redfox API itself (report via
  https://redfox.hk), and third-party dependencies (tracked continuously via
  Dependabot and the HOL plugin-scanner CI gate).
