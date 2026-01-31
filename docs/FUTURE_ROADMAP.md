# CyberOps Companion - Future Roadmap

**Last Updated:** 2026-01-31

This document outlines features planned for future development phases.

---

## Current Status

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0 - Foundation | ✅ Complete | 100% |
| Phase 1 - Enhanced Features | ✅ Complete | 100% |
| Phase 2 - Advanced Features | 🔄 In Progress | 75% |
| Phase 3 - Enterprise Features | 🔲 Not Started | 0% |

---

## Phase 2 - Remaining Items

### Mobile Responsive Improvements

**Priority:** Medium
**Effort:** Medium
**Status:** Not Started

**Scope:**
- Responsive navigation improvements for mobile devices
- Touch-friendly interactions
- Mobile-optimized charts and data tables
- Bottom navigation for mobile users
- Swipe gestures for common actions

**Files to modify:**
- `apps/web/components/layout/` - Navigation components
- `apps/web/components/dashboard/charts/` - Chart responsiveness
- All page components for mobile layouts

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

### SSO/SAML Integration

**Priority:** High
**Effort:** Medium
**Status:** Not Started

**Description:**
Enterprise Single Sign-On support for corporate identity providers.

**Planned providers:**
- SAML 2.0 (generic)
- Azure AD / Entra ID
- Okta
- Google Workspace
- LDAP/Active Directory

**Technical approach:**
- python3-saml library for SAML
- OAuth2/OIDC for modern providers
- JIT (Just-in-Time) user provisioning
- Group-to-role mapping
- SSO session management

**New endpoints:**
```
GET  /auth/sso/providers          # List configured providers
GET  /auth/sso/{provider}/login   # Initiate SSO flow
POST /auth/sso/{provider}/callback # SSO callback
POST /auth/sso/logout             # SSO logout
```

---

### Audit Logging

**Priority:** Medium
**Effort:** Medium
**Status:** Not Started

**Description:**
Comprehensive audit trail for compliance and forensics.

**Events to log:**
- Authentication (login, logout, failed attempts)
- Authorization (permission checks, role changes)
- Data access (reads of sensitive data)
- Data modifications (CRUD operations)
- Configuration changes
- Export operations
- API access

**Audit log model:**
```python
class AuditLog(Base):
    id = Column(UUID)
    timestamp = Column(DateTime, index=True)
    user_id = Column(UUID, nullable=True)
    action = Column(String)  # CREATE, READ, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String)  # incident, user, alert, etc.
    resource_id = Column(UUID, nullable=True)
    details = Column(JSON)  # Additional context
    ip_address = Column(String)
    user_agent = Column(String)
    success = Column(Boolean)
    tenant_id = Column(UUID)  # For multi-tenancy
```

**Features:**
- Tamper-evident logging (hash chain)
- Log retention policies
- Search and filter UI
- Export for SIEM integration
- Compliance reports (who accessed what)

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
