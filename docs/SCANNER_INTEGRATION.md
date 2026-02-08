# Vulnerability Scanner Integration Guide

This guide explains how to configure and use vulnerability scanners (Nessus, OpenVAS, Qualys) with CyberOps Companion.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Supported Scanners](#supported-scanners)
- [Configuration](#configuration)
  - [Nessus / Tenable.io](#nessus--tenableio)
  - [OpenVAS / Greenbone](#openvas--greenbone)
  - [Qualys VMDR](#qualys-vmdr)
- [Creating Scans](#creating-scans)
- [Real-Time Progress](#real-time-progress)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## Overview

CyberOps Companion integrates with enterprise vulnerability scanners to provide:

- **Unified vulnerability management** - Aggregate findings from multiple scanners
- **Real-time scan progress** - WebSocket-based progress updates
- **Normalized findings** - Consistent severity mapping across scanners
- **Graceful fallback** - Simulation mode when no scanner is configured

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Scans Tab      │  │ ScanProgressCard│  │ ScanProgressDlg │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │ WebSocket                      │
└────────────────────────────────┼────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                        Backend (FastAPI)                         │
│                                │                                │
│  ┌─────────────────────────────▼─────────────────────────────┐  │
│  │              WebSocket Endpoint                            │  │
│  │         /api/v1/ws/scans/{scan_id}/progress               │  │
│  └─────────────────────────────┬─────────────────────────────┘  │
│                                │ Redis Pub/Sub                  │
│  ┌─────────────────────────────▼─────────────────────────────┐  │
│  │                    Celery Worker                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              Scanner Adapters                        │  │  │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │  │  │
│  │  │  │ Nessus  │  │ OpenVAS │  │ Qualys  │             │  │  │
│  │  │  └────┬────┘  └────┬────┘  └────┬────┘             │  │  │
│  │  └───────┼────────────┼───────────┼───────────────────┘  │  │
│  └──────────┼────────────┼───────────┼──────────────────────┘  │
└─────────────┼────────────┼───────────┼──────────────────────────┘
              │            │           │
              ▼            ▼           ▼
         ┌─────────┐  ┌─────────┐  ┌─────────┐
         │ Nessus  │  │ OpenVAS │  │ Qualys  │
         │   API   │  │   GMP   │  │   API   │
         └─────────┘  └─────────┘  └─────────┘
```

## Supported Scanners

| Scanner | Protocol | Library | Auth Method |
|---------|----------|---------|-------------|
| Nessus / Tenable.io | REST API | pyTenable | API Key + Secret |
| OpenVAS / Greenbone | GMP (XML) | python-gvm | Username + Password |
| Qualys VMDR | REST API | httpx | Username + Password |

---

## Configuration

Scanner integrations are configured in the **Integration Hub** (`/integrations`).

### Nessus / Tenable.io

#### Prerequisites

- Nessus Professional, Expert, or Tenable.io subscription
- API access enabled
- API keys generated

#### Getting API Keys

**Tenable.io:**
1. Go to Settings > My Account > API Keys
2. Click "Generate" to create Access Key and Secret Key

**Nessus (on-premise):**
1. Go to Settings > Accounts > API Keys
2. Generate keys for your user account

#### Configuration Steps

1. Navigate to **Integrations** > **Add Integration**
2. Select **Nessus** from the templates
3. Fill in the configuration:

| Field | Description | Example |
|-------|-------------|---------|
| Name | Display name | `Nessus Production` |
| Base URL | Nessus server URL | `https://cloud.tenable.com` or `https://nessus.company.com:8834` |
| API Key | Access Key | `a1b2c3d4-e5f6-...` |
| API Secret | Secret Key | `x9y8z7w6-v5u4-...` |
| Verify SSL | Validate certificates | `true` (recommended) |

4. Click **Test Connection** to verify
5. Click **Save**

#### Nessus-Specific Settings

```json
{
  "scan_template": "basic",
  "folder_id": 3,
  "policy_id": null
}
```

- `scan_template`: Nessus scan template (basic, discovery, webapp, etc.)
- `folder_id`: Folder to store scans (optional)
- `policy_id`: Custom policy ID (optional)

---

### OpenVAS / Greenbone

#### Prerequisites

- OpenVAS/GVM installed and running
- GMP (Greenbone Management Protocol) access enabled
- Scanner user account with scan permissions

#### Connection Types

OpenVAS supports two connection methods:

1. **Unix Socket** (local installations)
   - Path: `/var/run/gvmd/gvmd.sock`

2. **TLS Connection** (remote installations)
   - Default port: 9390

#### Configuration Steps

1. Navigate to **Integrations** > **Add Integration**
2. Select **OpenVAS** from the templates
3. Fill in the configuration:

| Field | Description | Example |
|-------|-------------|---------|
| Name | Display name | `OpenVAS Scanner` |
| Base URL | GVM server | `unix:///var/run/gvmd/gvmd.sock` or `tls://gvm.company.com:9390` |
| Username | GVM username | `admin` |
| Password | GVM password | `********` |
| Verify SSL | Validate TLS cert | `true` |

4. Click **Test Connection** to verify
5. Click **Save**

#### OpenVAS-Specific Settings

```json
{
  "scan_config_id": "daba56c8-73ec-11df-a475-002264764cea",
  "scanner_id": "08b69003-5fc2-4037-a479-93b440211c73",
  "port_list_id": "33d0cd82-57c6-11e1-8ed1-406186ea4fc5"
}
```

- `scan_config_id`: Scan configuration (Full and fast, Discovery, etc.)
- `scanner_id`: Scanner to use (default: OpenVAS Default)
- `port_list_id`: Port list for scanning

**Common Scan Configs:**
| Name | UUID |
|------|------|
| Full and fast | `daba56c8-73ec-11df-a475-002264764cea` |
| Full and very deep | `698f691e-7489-11df-9d8c-002264764cea` |
| Discovery | `8715c877-47a0-438d-98a3-27c7a6ab2196` |

---

### Qualys VMDR

#### Prerequisites

- Qualys VMDR subscription
- API access enabled
- User account with API permissions

#### Getting API Credentials

1. Log in to Qualys
2. Go to Users > User Management
3. Create or edit a user with API access
4. Note the username and password

#### API Platform URL

Qualys has different API endpoints by region:

| Platform | API URL |
|----------|---------|
| US Platform 1 | `https://qualysapi.qualys.com` |
| US Platform 2 | `https://qualysapi.qg2.apps.qualys.com` |
| US Platform 3 | `https://qualysapi.qg3.apps.qualys.com` |
| EU Platform 1 | `https://qualysapi.qualys.eu` |
| EU Platform 2 | `https://qualysapi.qg2.apps.qualys.eu` |

#### Configuration Steps

1. Navigate to **Integrations** > **Add Integration**
2. Select **Qualys** from the templates
3. Fill in the configuration:

| Field | Description | Example |
|-------|-------------|---------|
| Name | Display name | `Qualys VMDR` |
| Base URL | Qualys API URL | `https://qualysapi.qualys.com` |
| Username | Qualys username | `api_user` |
| Password | Qualys password | `********` |

4. Click **Test Connection** to verify
5. Click **Save**

#### Qualys-Specific Settings

```json
{
  "option_profile_id": "123456",
  "scanner_appliance_type": "EXTERNAL"
}
```

- `option_profile_id`: Qualys option profile for scans
- `scanner_appliance_type`: EXTERNAL or INTERNAL

---

## Creating Scans

### Via UI

1. Navigate to **Vulnerabilities** > **Scans** tab
2. Click **New Scan**
3. Fill in the scan details:
   - **Name**: Descriptive scan name
   - **Type**: network, web_app, container, cloud, code, compliance
   - **Scanner**: nessus, openvas, qualys, trivy
   - **Target Scope**: IP addresses, hostnames, or CIDR ranges
4. Click **Create & Start**

### Via API

```bash
# Create scan
curl -X POST /api/v1/vulnerabilities/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Network Scan",
    "scan_type": "network",
    "scanner": "nessus",
    "target_scope": "192.168.1.0/24"
  }'

# Start scan
curl -X POST /api/v1/vulnerabilities/scans/{scan_id}/start \
  -H "Authorization: Bearer $TOKEN"
```

### Target Scope Format

```
# Single IP
192.168.1.1

# Multiple IPs (comma-separated)
192.168.1.1, 192.168.1.2, 192.168.1.3

# CIDR range
192.168.1.0/24

# Hostname
server.company.com

# Mixed
192.168.1.1, 10.0.0.0/8, webapp.company.com
```

---

## Real-Time Progress

Scan progress is streamed via WebSocket:

### WebSocket Connection

```javascript
const ws = new WebSocket(
  `wss://api.example.com/api/v1/ws/scans/${scanId}/progress?token=${jwtToken}`
);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
  // {
  //   "event": "scan:progress",
  //   "data": {
  //     "scan_id": "abc123",
  //     "progress_percent": 45,
  //     "state": "running",
  //     "hosts_total": 10,
  //     "hosts_completed": 4,
  //     "current_host": "192.168.1.5",
  //     "message": "Scanning host 5 of 10"
  //   },
  //   "timestamp": "2024-01-15T10:30:00Z"
  // }
};
```

### Events

| Event | Description |
|-------|-------------|
| `connection:established` | WebSocket connected |
| `scan:started` | Scan has started |
| `scan:progress` | Progress update |
| `scan:completed` | Scan finished successfully |
| `scan:failed` | Scan encountered an error |
| `scan:cancelled` | Scan was cancelled |

### Progress Data

```typescript
interface ScanProgressData {
  scan_id: string;
  progress_percent: number;      // 0-100
  state: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  hosts_total: number;
  hosts_completed: number;
  current_host?: string;
  message?: string;
  error?: string;                // Only for failed state
  total_findings?: number;       // Only for completed state
  severity_counts?: {            // Only for completed state
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
}
```

---

## API Reference

### Scans

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/vulnerabilities/scans` | List scans |
| POST | `/api/v1/vulnerabilities/scans` | Create scan |
| GET | `/api/v1/vulnerabilities/scans/{id}` | Get scan details |
| POST | `/api/v1/vulnerabilities/scans/{id}/start` | Start scan |
| POST | `/api/v1/vulnerabilities/scans/{id}/cancel` | Cancel scan |

### Integrations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/integrations` | List integrations |
| POST | `/api/v1/integrations` | Create integration |
| POST | `/api/v1/integrations/test-connection` | Test new connection |
| POST | `/api/v1/integrations/{id}/test-connection` | Test saved integration |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://host/api/v1/ws/scans/{scan_id}/progress?token=JWT` | Scan progress stream |

---

## Troubleshooting

### Connection Issues

#### Nessus: "Connection refused"

```
ScannerConnectionError: Unable to connect to Nessus at https://nessus:8834
```

**Solutions:**
1. Verify Nessus service is running: `systemctl status nessusd`
2. Check firewall allows port 8834
3. Verify URL includes protocol (`https://`)
4. For self-signed certs, set `verify_ssl: false` (not recommended for production)

#### OpenVAS: "Authentication failed"

```
ScannerConnectionError: GMP authentication failed
```

**Solutions:**
1. Verify username/password are correct
2. Check user has scanner permissions in GVM
3. For socket connection, verify socket path exists
4. For TLS, verify certificates are valid

#### Qualys: "401 Unauthorized"

```
ScannerAPIError: Qualys API returned 401
```

**Solutions:**
1. Verify username/password are correct
2. Check user has API access enabled
3. Verify correct API platform URL for your region
4. Check API rate limits haven't been exceeded

### Scan Issues

#### "No scanner integration configured"

The scan runs in simulation mode because no scanner is configured.

**Solution:**
1. Configure a scanner integration in the Integration Hub
2. Ensure the integration is **enabled** and **active**
3. The scanner type must match the scan's `scanner` field

#### "Scan timed out"

```
TimeoutError: Scan timed out after 14400 seconds
```

**Solutions:**
1. Reduce target scope
2. Increase `SCANNER_MAX_RUNTIME` in config
3. Check scanner health on the external platform

#### Progress not updating

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Verify Celery worker is running
3. Check WebSocket connection in browser DevTools
4. Verify JWT token is valid

### Severity Mapping

Findings are normalized to a consistent severity scale:

| Scanner | Original | Normalized |
|---------|----------|------------|
| Nessus | 0 (Info) | info |
| Nessus | 1 (Low) | low |
| Nessus | 2 (Medium) | medium |
| Nessus | 3 (High) | high |
| Nessus | 4 (Critical) | critical |
| OpenVAS | CVSS 0.0 | info |
| OpenVAS | CVSS 0.1-3.9 | low |
| OpenVAS | CVSS 4.0-6.9 | medium |
| OpenVAS | CVSS 7.0-8.9 | high |
| OpenVAS | CVSS 9.0-10.0 | critical |
| Qualys | 1 | info |
| Qualys | 2 | low |
| Qualys | 3 | medium |
| Qualys | 4 | high |
| Qualys | 5 | critical |

---

## Environment Variables

```bash
# Scanner polling interval (seconds)
SCANNER_POLL_INTERVAL=30

# Maximum scan runtime (seconds) - 4 hours default
SCANNER_MAX_RUNTIME=14400

# Connection timeout (seconds)
SCANNER_CONNECTION_TIMEOUT=60

# Redis URL for pub/sub
REDIS_URL=redis://localhost:6379/0
```

---

## Security Considerations

1. **Store credentials securely** - Integration credentials are encrypted at rest
2. **Use TLS** - Always use HTTPS/TLS connections to scanners
3. **Least privilege** - Create dedicated scanner accounts with minimal permissions
4. **Network segmentation** - Scanners should only access necessary networks
5. **Audit logging** - All scan operations are logged

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/fbarquez/cyberops-companion/issues
- Documentation: https://github.com/fbarquez/cyberops-companion/docs
