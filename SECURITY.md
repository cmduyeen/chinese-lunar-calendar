# Security policy

This repository generates public calendar files. Calendar generation is offline; it does not read email, contacts or private calendars, and it does not need a production server or paid API. Optional maintenance uses the current user's authenticated GitHub CLI solely to inspect the selected repository and manage its workflow. It stores no new token or password.

Report security issues using GitHub private vulnerability reporting when available. Otherwise, open an issue containing only a high-level description and ask for a private reporting route. Never include live credentials, personal calendar data or exploit details in a public issue.

## Trust and permissions

- Only the supported main branch is intended for production subscriptions. Verify the repository owner before copying a feed URL.
- PR/build jobs have read-only repository permission. A separate publish job can write only after a successful trusted main-branch build and checksum verification. It runs no package installer. Its checkout does not persist credentials.
- External GitHub Actions are pinned to full commit SHAs. Bootstrap/build tools, runtime packages and development tools are version/hash pinned; npm development dependencies use a lockfile and install without lifecycle scripts.
- Publication accepts only bounded, portable calendar/metadata names, rejects symlinks and verifies the artifact again after copying to a private temporary directory. Unrecorded artifact extras cannot be published. Checksums detect corruption; they are not a signature or proof of date accuracy.
- JSON configuration has a 256 KiB limit and rejects duplicate keys, nonfinite constants, unknown settings and invalid types. Custom feed names cannot contain paths or shell syntax. Subprocess invocation uses argument lists with timeouts and no shell.
- The development browser server is ephemeral, bound to loopback, and serves an allowlist of public test assets. Repository metadata, virtual environments and maintenance logs are denied. It is not a production web service.

## Maintenance

Run audits after dependency or code changes. CI enforces Ruff formatting/lint, Bandit checks, dependency advisory checks, redacted secret scanning and regression tests on PRs/main code pushes. Annual unchanged runs avoid installing audit/browser tools. Dependency updates and engine changes require review and reference-date tests; do not auto-merge them merely because a feed builds.

Advisory databases and scanners cannot prove that code has no vulnerabilities. This audit does not certify the Python interpreter, OS, calendar application or GitHub availability. Use a supported, patched Python version and keep the hosting account protected. No secret, local environment or audit-cache directory should be committed.
