# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of CyberOps Companion seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via [GitHub Security Advisories](https://github.com/fbarquez/cyberops-companion/security/advisories/new).

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours.
- **Communication**: We will keep you informed about the progress of fixing the vulnerability.
- **Timeline**: We aim to release a fix within 90 days, depending on the complexity.
- **Credit**: We will credit you in our release notes (unless you prefer to remain anonymous).

### Safe Harbor

We support safe harbor for security researchers who:

- Make a good faith effort to avoid privacy violations, destruction of data, and interruption or degradation of our services
- Only interact with accounts you own or with explicit permission of the account holder
- Do not exploit a security issue for purposes other than verification
- Report vulnerabilities promptly and do not publicly disclose before a fix is available

## Security Best Practices for Deployment

When deploying CyberOps Companion, please follow these security recommendations:

### Environment Variables

- Never commit `.env` files to version control
- Use strong, unique values for `SECRET_KEY` and `JWT_SECRET`
- Rotate secrets regularly
- Use environment-specific configurations

### Database

- Use strong passwords for PostgreSQL
- Enable SSL/TLS for database connections in production
- Regularly backup your database
- Restrict database network access

### Network

- Always use HTTPS in production
- Configure proper CORS origins
- Use a reverse proxy (nginx) with security headers
- Enable rate limiting

### Authentication

- Enforce strong password policies
- Enable MFA where possible
- Review and audit user access regularly
- Use SSO/SAML for enterprise deployments

### Updates

- Keep all dependencies updated
- Subscribe to security advisories
- Apply security patches promptly

## Security Features

CyberOps Companion includes several built-in security features:

- **JWT Authentication** with configurable expiration
- **Role-Based Access Control (RBAC)** with granular permissions
- **Rate Limiting** with Redis-based sliding window
- **Audit Logging** for compliance and forensics
- **Multi-tenancy** with data isolation
- **Evidence Chain** with SHA-256 hash verification
- **Input Validation** with Pydantic schemas
- **SQL Injection Protection** via SQLAlchemy ORM

## Acknowledgments

We would like to thank the following security researchers for responsibly disclosing vulnerabilities:

*No vulnerabilities reported yet.*

---

Thank you for helping keep CyberOps Companion and its users safe!
