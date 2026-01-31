# NVD API Integration

**Status:** ✅ Implemented
**Date:** 2026-01-31
**Location:** `apps/api/src/services/nvd_service.py`

---

## Overview

Integration with NIST National Vulnerability Database (NVD) API 2.0 for CVE lookup, enrichment, and vulnerability intelligence. Also integrates EPSS scores and CISA KEV catalog.

---

## Features

- CVE lookup from NVD API 2.0
- EPSS (Exploit Prediction Scoring System) integration
- CISA KEV (Known Exploited Vulnerabilities) catalog
- CVE search with multiple filters
- Automatic CVE enrichment in database
- Response caching (configurable)
- Rate limit handling

---

## Configuration

```env
# .env file
# Optional but recommended - increases rate limit from 5 to 50 requests/30s
NVD_API_KEY=your-api-key-here
```

Get your free API key at: https://nvd.nist.gov/developers/request-an-api-key

---

## API Endpoints

### Get CVE Details
```
GET /api/v1/vulnerabilities/cve/{cve_id}
Authorization: Bearer <token>

Response:
{
  "cve_id": "CVE-2024-1234",
  "description": "...",
  "cvss_v3_score": 9.8,
  "cvss_v3_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "cvss_v3_severity": "CRITICAL",
  "epss_score": 0.95,
  "epss_percentile": 99.2,
  "is_kev": true,
  "kev_date_added": "2024-01-15",
  "kev_due_date": "2024-02-05",
  "published_date": "2024-01-10T00:00:00Z",
  "last_modified_date": "2024-01-20T00:00:00Z",
  "references": [...],
  "weaknesses": ["CWE-79", "CWE-89"],
  "affected_products": [...]
}
```

### Enrich CVE
```
POST /api/v1/vulnerabilities/cve/{cve_id}/enrich
Authorization: Bearer <token>
Query: create_if_missing=true (optional)

Response: Updated CVE entry from database
```

### Search CVEs
```
GET /api/v1/vulnerabilities/cve/search/
Authorization: Bearer <token>
Query Parameters:
  - keyword: Search term
  - cpe_name: CPE match string
  - cvss_v3_severity: LOW, MEDIUM, HIGH, CRITICAL
  - has_kev: true/false
  - pub_start_date: ISO date
  - pub_end_date: ISO date
  - page: Page number (default 1)
  - size: Results per page (default 20)
```

### KEV Catalog
```
GET /api/v1/vulnerabilities/kev/catalog
Authorization: Bearer <token>

Response:
{
  "catalog_version": "2024.01.31",
  "count": 1234,
  "vulnerabilities": [...]
}
```

### NVD Status
```
GET /api/v1/vulnerabilities/nvd/status
Authorization: Bearer <token>

Response:
{
  "configured": true,
  "has_api_key": true,
  "rate_limit": "50 requests per 30 seconds"
}
```

---

## Usage in Code

```python
from src.services.nvd_service import get_nvd_service

nvd_service = get_nvd_service()

# Get CVE with all enrichments
cve_data = await nvd_service.get_cve(
    "CVE-2024-1234",
    include_epss=True,
    include_kev=True
)

if cve_data:
    print(f"CVSS Score: {cve_data.cvss_v3_score}")
    print(f"EPSS Score: {cve_data.epss_score}")
    print(f"In KEV: {cve_data.is_kev}")

# Search CVEs
results = await nvd_service.search_cves(
    keyword="apache",
    cvss_v3_severity="CRITICAL",
    results_per_page=10
)

# Get KEV catalog
kev_list = await nvd_service.get_kev_catalog()
```

---

## Data Sources

| Source | API | Purpose |
|--------|-----|---------|
| NVD | https://services.nvd.nist.gov/rest/json/cves/2.0 | CVE details, CVSS scores |
| FIRST EPSS | https://api.first.org/data/v1/epss | Exploit prediction scores |
| CISA KEV | https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json | Known exploited vulns |

---

## CVEData Model

```python
@dataclass
class CVEData:
    cve_id: str
    description: str
    cvss_v2_score: Optional[float]
    cvss_v2_vector: Optional[str]
    cvss_v3_score: Optional[float]
    cvss_v3_vector: Optional[str]
    cvss_v3_severity: Optional[str]
    epss_score: Optional[float]
    epss_percentile: Optional[float]
    is_kev: bool
    kev_date_added: Optional[str]
    kev_due_date: Optional[str]
    kev_ransomware_use: Optional[str]
    published_date: Optional[str]
    last_modified_date: Optional[str]
    references: List[Dict]
    weaknesses: List[str]
    affected_products: List[Dict]
```

---

## Files

| File | Purpose |
|------|---------|
| `services/nvd_service.py` | NVD API client and service |
| `services/vulnerability_service.py` | CVE lookup/enrichment methods |
| `api/v1/vulnerabilities.py` | API endpoints |
| `config.py` | NVD_API_KEY setting |

---

## Rate Limits

| Condition | Rate Limit |
|-----------|------------|
| Without API key | 5 requests per 30 seconds |
| With API key | 50 requests per 30 seconds |

---

## Notes

- API key is optional but highly recommended for production
- EPSS scores update daily
- KEV catalog is cached and refreshed periodically
- CVE enrichment updates database entries with latest data
