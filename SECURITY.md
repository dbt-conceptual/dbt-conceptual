# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by emailing:

**your.email@example.com**

Please do **not** open a public GitHub issue for security vulnerabilities.

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

### Response timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Resolution**: Depends on severity, typically within 30 days

## Security Best Practices for Users

- Keep dbt-conceptual updated to the latest version
- Don't commit sensitive data in your `model.yml` files
- Review schema.yml files before running `sync --create-stubs` on untrusted projects
