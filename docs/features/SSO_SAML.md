# SSO/SAML Integration

This document describes the Single Sign-On (SSO) integration with OAuth2/OIDC support for enterprise authentication in CyberOps Companion.

## Overview

CyberOps Companion supports enterprise SSO authentication through OAuth2/OIDC protocols, enabling seamless integration with identity providers like Google Workspace, Microsoft Entra ID (Azure AD), and Okta.

## Supported Providers

| Provider | Protocol | Status |
|----------|----------|--------|
| Google Workspace | OAuth2/OIDC | Supported |
| Microsoft Entra ID (Azure AD) | OAuth2/OIDC | Supported |
| Okta | OAuth2/OIDC | Supported |

## Architecture

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|     Frontend     |---->|   Backend API    |---->|   SSO Provider   |
|                  |     |                  |     |   (Google/Azure) |
|   /login         |     |   /auth/sso/*    |     |                  |
|   /auth/callback |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
```

### Authentication Flow

1. User clicks "Sign in with Google/Microsoft" on login page
2. Frontend requests authorization URL from backend
3. Backend generates state token (CSRF protection) and returns OAuth2 URL
4. User is redirected to identity provider
5. User authenticates with their corporate credentials
6. Provider redirects back to `/auth/callback` with authorization code
7. Frontend sends code + state to backend
8. Backend exchanges code for tokens, fetches user info
9. Backend creates/links user account (JIT provisioning)
10. Backend returns JWT tokens to frontend
11. User is logged in and redirected to dashboard

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Google OAuth2
SSO_GOOGLE_ENABLED=true
SSO_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
SSO_GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx

# Microsoft Entra ID (Azure AD)
SSO_AZURE_ENABLED=true
SSO_AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SSO_AZURE_CLIENT_SECRET=xxxxx
SSO_AZURE_TENANT_ID=common  # Use your tenant ID for single-tenant apps

# Okta
SSO_OKTA_ENABLED=true
SSO_OKTA_CLIENT_ID=xxxxx
SSO_OKTA_CLIENT_SECRET=xxxxx
SSO_OKTA_DOMAIN=dev-123456.okta.com

# General SSO Settings
SSO_AUTO_CREATE_USERS=true          # Enable JIT user provisioning
SSO_DEFAULT_ROLE=analyst            # Default role for new SSO users
SSO_ALLOWED_DOMAINS=company.com     # Comma-separated list of allowed email domains
SSO_CALLBACK_URL=                   # Optional: Override callback URL
```

### Google Workspace Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Navigate to APIs & Services > Credentials
4. Create OAuth 2.0 Client ID (Web application)
5. Add authorized redirect URI: `https://your-domain.com/auth/callback`
6. Copy Client ID and Client Secret to `.env`

### Microsoft Entra ID Setup

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to Azure Active Directory > App registrations
3. Create new registration
4. Add redirect URI: `https://your-domain.com/auth/callback`
5. Create client secret under Certificates & secrets
6. Copy Application (client) ID and secret to `.env`

### Okta Setup

1. Log in to your Okta Admin Console
2. Navigate to Applications > Create App Integration
3. Select OIDC - OpenID Connect and Web Application
4. Add sign-in redirect URI: `https://your-domain.com/auth/callback`
5. Copy Client ID and Client Secret to `.env`

## Database Schema

### User Model Extensions

```python
# SSO fields added to User model
sso_provider = Column(String(50), nullable=True)    # google, azure, okta
sso_id = Column(String(255), nullable=True)         # Provider's unique user ID
sso_email = Column(String(255), nullable=True)      # Email from SSO provider
sso_linked_at = Column(DateTime, nullable=True)     # When SSO was linked
```

### SSOProvider Model

```python
class SSOProvider(Base):
    __tablename__ = "sso_providers"

    id = Column(String(36), primary_key=True)
    name = Column(String(100))              # "Google Workspace"
    slug = Column(String(50), unique=True)  # "google"
    provider_type = Column(String(20))      # "oauth2"
    client_id = Column(String(255))
    client_secret = Column(String(500))
    authorization_url = Column(String(500))
    token_url = Column(String(500))
    userinfo_url = Column(String(500))
    scopes = Column(String(500))
    enabled = Column(Boolean, default=True)
    default_role = Column(String(50))
    allowed_domains = Column(Text)
    auto_create_users = Column(Boolean)
```

## API Endpoints

### GET /api/v1/auth/sso/providers

Returns list of enabled SSO providers for the login page.

**Response:**
```json
{
  "providers": [
    {
      "slug": "google",
      "name": "Google Workspace",
      "icon": "google",
      "button_text": "Sign in with Google"
    },
    {
      "slug": "azure",
      "name": "Microsoft",
      "icon": "microsoft",
      "button_text": "Sign in with Microsoft"
    }
  ]
}
```

### GET /api/v1/auth/sso/{provider}/authorize

Generates OAuth2 authorization URL with state token.

**Query Parameters:**
- `redirect_uri` (optional): Override callback URL

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-token"
}
```

### POST /api/v1/auth/sso/{provider}/callback

Exchanges authorization code for tokens and authenticates user.

**Request:**
```json
{
  "code": "authorization-code",
  "state": "state-token"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@company.com",
    "full_name": "John Doe",
    "role": "analyst",
    "sso_provider": "google",
    "is_new_user": false
  }
}
```

### POST /api/v1/auth/sso/{provider}/unlink

Removes SSO connection from user account.

**Response:**
```json
{
  "message": "Successfully unlinked google from your account"
}
```

## Security Considerations

### CSRF Protection

State tokens are generated for each authorization request and validated on callback:
- Cryptographically random tokens (32 bytes, URL-safe)
- Stored in database with expiration (10 minutes)
- One-time use (deleted after validation)

### Domain Validation

Email domain restrictions can be enforced per provider:
- Configure `allowed_domains` as comma-separated list
- Only users with matching email domains can authenticate
- Prevents unauthorized access from personal accounts

### Token Security

- SSO provider tokens are NOT stored
- Only internal JWT tokens are issued
- Client secrets encrypted at rest

### Audit Logging

All SSO events are logged:
- SSO login attempts (success/failure)
- New user creation via JIT provisioning
- Account linking/unlinking

## JIT (Just-in-Time) User Provisioning

When `SSO_AUTO_CREATE_USERS=true`:

1. User authenticates with SSO provider
2. Backend checks if user exists (by SSO ID or email)
3. If not found, creates new user account:
   - Email from SSO provider
   - Full name from profile
   - Role from `SSO_DEFAULT_ROLE`
   - Random password (SSO users can't use password login)
4. If found by email, links SSO to existing account

## Frontend Integration

### Login Page

The login page displays SSO buttons when providers are configured:

```tsx
<SSOButtons onError={(err) => setError(err)} />
```

### Callback Page

Handles OAuth2 callbacks at `/auth/callback`:
- Validates state token
- Exchanges code for tokens
- Saves tokens to storage
- Redirects to dashboard

## Troubleshooting

### Common Issues

**"Invalid or expired state token"**
- User took too long to authenticate (>10 minutes)
- User refreshed the page during authentication
- Solution: Retry the SSO login flow

**"Email domain not allowed"**
- User's email domain not in `allowed_domains`
- Solution: Add domain to configuration or use approved email

**"User not found and auto-creation is disabled"**
- `SSO_AUTO_CREATE_USERS=false` and user doesn't exist
- Solution: Create user manually or enable auto-creation

### Debug Mode

Enable debug logging for SSO:
```bash
DEBUG=true
```

Check logs for detailed OAuth2 flow information.

## Migration

To enable SSO for existing deployment:

1. Add environment variables
2. Run database migrations (adds SSO columns to users table)
3. Configure providers in admin panel or database
4. Restart application

```bash
# Example migration
alembic upgrade head
```

## Related Documentation

- [Role-Based Access Control](./ROLE_BASED_ACCESS.md)
- [Audit Logging](./AUDIT_LOGGING.md)
- [OAuth2 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OpenID Connect](https://openid.net/connect/)
