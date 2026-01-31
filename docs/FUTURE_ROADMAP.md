# CyberOps Companion - Future Roadmap

**Last Updated:** 2026-02-01

This document outlines features planned for future development phases.

---

## Current Status

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0 - Foundation | ✅ Complete | 100% |
| Phase 1 - Enhanced Features | ✅ Complete | 100% |
| Phase 2 - Advanced Features | ✅ Complete | 100% |
| Phase 3 - Enterprise Features | 🔄 In Progress | 50% |

---

## Phase 2 - Completed Items

### Mobile Responsive Improvements ✅

**Status:** Complete (2026-01-31)

**Implemented:**
- Mobile drawer sidebar (Sheet component)
- Hamburger menu in header
- Responsive tables with column hiding
- Responsive forms (single/multi-column)
- Touch-friendly dialogs
- Responsive charts

**Documentation:** [MOBILE_RESPONSIVE.md](./features/MOBILE_RESPONSIVE.md)

---

## Phase 3 - Completed Items

### Audit Logging ✅

**Status:** Complete (2026-01-31)

**Implemented:**
- Complete audit trail for all user actions
- AuditService with log_action, list_logs, export_logs
- API endpoints with filters and pagination
- Frontend page with stats, filters, table, export
- Automatic sensitive data filtering
- EN/DE translations

**Documentation:** [AUDIT_LOGGING.md](./features/AUDIT_LOGGING.md)

---

### SSO/SAML Integration ✅

**Status:** Complete (2026-02-01)

**Implemented:**
- OAuth2/OIDC protocol support
- Providers: Google Workspace, Microsoft Entra ID (Azure AD), Okta
- SSOProvider and SSOState models
- User model extended with SSO fields
- SSOService with full OAuth2 flow
- CSRF protection via state tokens
- JIT (Just-in-Time) user provisioning
- Email domain validation
- Frontend: SSO buttons, callback page
- EN/DE translations

**Documentation:** [SSO_SAML.md](./features/SSO_SAML.md)

---

## Phase 2C - ML/Predictive Analytics

**Priority:** Low (requires data)
**Effort:** High
**Status:** Deferred

**Rationale for deferral:**
ML models require substantial historical data to train effectively. This feature should be implemented after the platform has been in production and accumulated sufficient data.

**Planned Features:**

### 1. Anomaly Detection
```
Purpose: Identify unusual patterns in security events
Approach: Statistical methods (IQR, Z-score) initially, ML models later
Data needed: 3-6 months of alert/incident data
```

### 2. Incident Prediction
```
Purpose: Predict likelihood of incidents based on indicators
Approach: Classification models (Random Forest, XGBoost)
Data needed: Historical incidents with labeled outcomes
```

### 3. Risk Scoring (ML-Enhanced)
```
Purpose: Improve risk predictions beyond static rules
Approach: Regression models based on historical risk outcomes
Data needed: Risk assessments with actual impact data
```

### 4. Alert Prioritization
```
Purpose: Auto-prioritize alerts based on historical resolution
Approach: Learn from analyst behavior patterns
Data needed: Alert triage history with outcomes
```

### 5. Vulnerability Exploit Prediction
```
Purpose: Predict which CVEs will be exploited
Approach: Feature engineering from CVE characteristics + ML
Data needed: Historical CVE data with exploit status
```

**Technical Requirements:**
- Python ML libraries: scikit-learn, pandas, numpy
- Model storage and versioning
- Background training jobs (Celery)
- API endpoints for predictions
- Model monitoring and retraining pipeline

**Proposed Architecture:**
```
apps/api/src/ml/
├── __init__.py
├── models/
│   ├── anomaly_detector.py
│   ├── incident_predictor.py
│   └── risk_scorer.py
├── training/
│   ├── data_preparation.py
│   └── model_trainer.py
├── inference/
│   └── prediction_service.py
└── utils/
    └── feature_engineering.py
```

---

## Phase 3 - Enterprise Features

### Multi-tenancy

**Priority:** High
**Effort:** High
**Status:** Not Started

**Description:**
Support multiple organizations/tenants on a single deployment with data isolation.

**Components:**
- Tenant model and database schema
- Tenant-aware queries (all models)
- Tenant context middleware
- Tenant-specific settings
- Tenant admin portal
- Data isolation verification

**Database changes:**
```python
# Add to all models
tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)

# Tenant model
class Tenant(Base):
    id = Column(UUID)
    name = Column(String)
    slug = Column(String, unique=True)
    settings = Column(JSON)
    created_at = Column(DateTime)
    is_active = Column(Boolean)
```

---

### SSO/SAML Integration ✅ COMPLETED

See [Phase 3 - Completed Items](#phase-3---completed-items) above and [SSO_SAML.md](./features/SSO_SAML.md).

---

### Audit Logging ✅ COMPLETED

See [Phase 3 - Completed Items](#phase-3---completed-items) above and [AUDIT_LOGGING.md](./features/AUDIT_LOGGING.md).

---

### API Rate Limiting

**Priority:** Medium
**Effort:** Low
**Status:** Not Started

**Description:**
Protect API from abuse and ensure fair usage.

**Implementation:**
- Redis-based rate limiting
- Per-user and per-IP limits
- Configurable limits per endpoint
- Rate limit headers in responses
- Graceful degradation

**Configuration:**
```python
RATE_LIMITS = {
    "default": "100/minute",
    "auth": "10/minute",
    "reports": "10/minute",
    "uploads": "20/minute",
    "api_heavy": "30/minute",
}
```

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706745600
```

---

## Technical Debt & Improvements

### Real Scanner Integration

**Priority:** Medium
**Effort:** High
**Status:** Placeholder exists

**Current state:**
The vulnerability scanner currently simulates scan results. Real integration is needed.

**Planned integrations:**
- Nessus (Tenable)
- OpenVAS
- Qualys
- Rapid7 InsightVM
- AWS Inspector
- Azure Defender

**Integration approach:**
```
apps/api/src/integrations/scanners/
├── __init__.py
├── base_scanner.py          # Abstract base class
├── nessus_scanner.py
├── openvas_scanner.py
├── qualys_scanner.py
└── result_normalizer.py     # Normalize results to common format
```

---

### Performance Optimizations

**Items to address:**
1. Database query optimization (add missing indexes)
2. Caching layer for expensive queries
3. Pagination improvements for large datasets
4. Background job optimization
5. Frontend bundle size reduction

---

### Testing Coverage

**Current state:** Minimal tests
**Target:** 80% coverage

**Areas needing tests:**
- Unit tests for services
- Integration tests for API endpoints
- E2E tests for critical flows
- Performance/load tests

---

## Version Planning

| Version | Focus | Target |
|---------|-------|--------|
| v0.9.0 | Mobile responsive | TBD |
| v1.0.0 | Production ready, Phase 2 complete | TBD |
| v1.1.0 | Multi-tenancy | TBD |
| v1.2.0 | SSO/SAML | TBD |
| v1.3.0 | Audit logging | TBD |
| v2.0.0 | ML/Predictive analytics | When data available |

---

## Contributing

When implementing future features:

1. Create a feature branch from `main`
2. Implement with tests
3. Update documentation in `docs/features/`
4. Update `CHANGELOG.md`
5. Update `PROJECT_STATUS.md`
6. Create pull request with description

---

## Notes

- Priority and effort estimates are relative
- Features may be reordered based on user feedback
- ML features depend on data availability
- Enterprise features may require licensing changes
