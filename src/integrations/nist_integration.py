"""
NIST Integration Module.

Provides integration with:
- NIST OSCAL (Open Security Controls Assessment Language)
- NIST NVD (National Vulnerability Database) API
- NIST CSF 2.0 (Cybersecurity Framework)
- NIST SP 800-61r3 (Incident Response Guide)
- NIST SP 800-53 (Security Controls)

API Documentation: https://nvd.nist.gov/developers
OSCAL Repository: https://github.com/usnistgov/OSCAL
"""

import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import hashlib

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from src.integrations.models import (
    ComplianceFramework,
    ComplianceControl,
    ComplianceCheck,
    ComplianceStatus,
    PhaseComplianceMapping,
    CVEInfo,
    CVSSScore,
    OSCALCatalog,
)

logger = logging.getLogger(__name__)


class NISTOSCALIntegration:
    """
    Integration with NIST OSCAL for SP 800-53 and CSF controls.

    OSCAL provides machine-readable security control catalogs in
    JSON, XML, and YAML formats. This class fetches and parses
    those catalogs for compliance validation.

    Features:
    - Fetch SP 800-53 Rev 5 controls in OSCAL format
    - Fetch CSF 2.0 profiles
    - Map IR phases to CSF functions
    - Map IR phases to SP 800-53 controls
    """

    OSCAL_CONTENT_BASE = "https://raw.githubusercontent.com/usnistgov/oscal-content/main"

    # CSF 2.0 Function mapping to IR phases
    # Based on SP 800-61r3 (April 2025) alignment with CSF 2.0
    CSF_PHASE_MAPPING = {
        "detection": {
            "functions": ["DE.AE", "DE.CM"],
            "categories": [
                "DE.AE-01",  # Anomalies and events are analyzed
                "DE.AE-02",  # Potentially adverse events are analyzed
                "DE.AE-03",  # Event data are collected
                "DE.CM-01",  # Networks are monitored
                "DE.CM-02",  # Physical environment is monitored
                "DE.CM-03",  # Personnel activity is monitored
            ],
            "description": "Detect - Adverse events are discovered",
        },
        "analysis": {
            "functions": ["RS.AN", "RS.CO"],
            "categories": [
                "RS.AN-01",  # Incident analysis is conducted
                "RS.AN-02",  # Incident impact is understood
                "RS.AN-03",  # Forensics are performed
                "RS.CO-01",  # Incident status is communicated
                "RS.CO-02",  # Incident reports are shared
            ],
            "description": "Respond - Analysis of detected events",
        },
        "containment": {
            "functions": ["RS.MI"],
            "categories": [
                "RS.MI-01",  # Incidents are contained
                "RS.MI-02",  # Incidents are mitigated
            ],
            "description": "Respond - Mitigation actions",
        },
        "eradication": {
            "functions": ["RS.MI", "PR.DS"],
            "categories": [
                "RS.MI-01",  # Incidents are contained
                "RS.MI-02",  # Incidents are mitigated
                "PR.DS-01",  # Data-at-rest is protected
                "PR.DS-02",  # Data-in-transit is protected
            ],
            "description": "Respond/Protect - Threat removal",
        },
        "recovery": {
            "functions": ["RC.RP", "RC.CO"],
            "categories": [
                "RC.RP-01",  # Recovery plan is executed
                "RC.CO-01",  # Recovery is communicated
                "RC.CO-02",  # Recovery status is reported
            ],
            "description": "Recover - System restoration",
        },
        "post_incident": {
            "functions": ["RS.IM", "GV.OC"],
            "categories": [
                "RS.IM-01",  # Response plans incorporate lessons learned
                "RS.IM-02",  # Response strategies are updated
                "GV.OC-01",  # Organizational context is understood
            ],
            "description": "Respond/Govern - Lessons learned",
        },
    }

    # SP 800-53 Rev 5 control mapping for IR
    SP800_53_PHASE_MAPPING = {
        "detection": {
            "controls": [
                "IR-4",   # Incident Handling
                "IR-6",   # Incident Reporting
                "AU-6",   # Audit Record Review
                "SI-4",   # System Monitoring
            ],
            "description": "Incident detection and initial reporting",
        },
        "analysis": {
            "controls": [
                "IR-4",   # Incident Handling
                "IR-5",   # Incident Monitoring
                "AU-6",   # Audit Record Review
                "AU-12",  # Audit Record Generation
            ],
            "description": "Incident analysis and scope determination",
        },
        "containment": {
            "controls": [
                "IR-4",   # Incident Handling
                "SC-7",   # Boundary Protection
                "AC-2",   # Account Management
            ],
            "description": "Incident containment procedures",
        },
        "eradication": {
            "controls": [
                "IR-4",   # Incident Handling
                "SI-3",   # Malicious Code Protection
                "SI-7",   # Software, Firmware, and Information Integrity
            ],
            "description": "Threat eradication",
        },
        "recovery": {
            "controls": [
                "CP-10",  # System Recovery and Reconstitution
                "CP-9",   # System Backup
                "IR-4",   # Incident Handling
            ],
            "description": "System recovery procedures",
        },
        "post_incident": {
            "controls": [
                "IR-4",   # Incident Handling (lessons learned)
                "IR-8",   # Incident Response Plan
                "CA-7",   # Continuous Monitoring
            ],
            "description": "Post-incident activities",
        },
    }

    def __init__(self, cache_dir: Optional[Path] = None, offline_mode: bool = False):
        """
        Initialize NIST OSCAL integration.

        Args:
            cache_dir: Directory for caching downloaded catalogs
            offline_mode: If True, only use cached data
        """
        self.cache_dir = cache_dir or Path.home() / ".cyberops_companion" / "nist_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode
        self._sp800_53_catalog: Optional[Dict] = None
        self._csf_profile: Optional[Dict] = None

    def _get_cache_path(self, identifier: str) -> Path:
        """Get cache file path."""
        safe_name = hashlib.md5(identifier.encode()).hexdigest()
        return self.cache_dir / f"{safe_name}.json"

    def _load_from_cache(self, identifier: str) -> Optional[Dict]:
        """Load from cache if available."""
        cache_path = self._get_cache_path(identifier)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Cache read error: {e}")
        return None

    def _save_to_cache(self, identifier: str, data: Dict) -> None:
        """Save to cache."""
        cache_path = self._get_cache_path(identifier)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.warning(f"Cache write error: {e}")

    def fetch_sp800_53_catalog(self) -> Optional[Dict]:
        """
        Fetch NIST SP 800-53 Rev 5 catalog in OSCAL format.

        Returns:
            OSCAL catalog as dictionary
        """
        if self._sp800_53_catalog:
            return self._sp800_53_catalog

        cache_key = "sp800_53_rev5_catalog"
        cached = self._load_from_cache(cache_key)
        if cached:
            self._sp800_53_catalog = cached
            return cached

        if self.offline_mode or not REQUESTS_AVAILABLE:
            return None

        try:
            url = f"{self.OSCAL_CONTENT_BASE}/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            self._save_to_cache(cache_key, data)
            self._sp800_53_catalog = data
            return data
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch SP 800-53 catalog: {e}")
            return None

    def fetch_csf_profile(self) -> Optional[Dict]:
        """
        Fetch NIST CSF 2.0 profile in OSCAL format.

        Returns:
            OSCAL profile as dictionary
        """
        if self._csf_profile:
            return self._csf_profile

        cache_key = "csf_2_profile"
        cached = self._load_from_cache(cache_key)
        if cached:
            self._csf_profile = cached
            return cached

        if self.offline_mode or not REQUESTS_AVAILABLE:
            return None

        # Note: CSF 2.0 OSCAL content URL may vary
        # Using placeholder - check actual NIST OSCAL content repository
        try:
            # The actual URL structure may differ
            url = f"{self.OSCAL_CONTENT_BASE}/nist.gov/CSF/2.0/json/NIST_CSF_2.0.json"
            response = requests.get(url, timeout=60)
            if response.ok:
                data = response.json()
                self._save_to_cache(cache_key, data)
                self._csf_profile = data
                return data
            else:
                logger.info("CSF 2.0 OSCAL not available, using static mapping")
                return None
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch CSF profile: {e}")
            return None

    def get_csf_mapping_for_phase(self, phase: str) -> PhaseComplianceMapping:
        """
        Get CSF 2.0 mapping for an IR phase.

        Based on SP 800-61r3 (April 2025) alignment with CSF 2.0.

        Args:
            phase: IR phase name

        Returns:
            PhaseComplianceMapping with CSF controls
        """
        phase_data = self.CSF_PHASE_MAPPING.get(phase, {})

        return PhaseComplianceMapping(
            phase=phase,
            framework=ComplianceFramework.NIST_CSF_2,
            controls=phase_data.get("categories", []),
            mandatory_controls=phase_data.get("functions", []),
            documentation_required=self._get_csf_documentation_requirements(phase),
        )

    def get_sp800_53_mapping_for_phase(self, phase: str) -> PhaseComplianceMapping:
        """
        Get SP 800-53 Rev 5 mapping for an IR phase.

        Args:
            phase: IR phase name

        Returns:
            PhaseComplianceMapping with SP 800-53 controls
        """
        phase_data = self.SP800_53_PHASE_MAPPING.get(phase, {})

        return PhaseComplianceMapping(
            phase=phase,
            framework=ComplianceFramework.NIST_800_53,
            controls=phase_data.get("controls", []),
            mandatory_controls=[],  # All listed are recommended
            documentation_required=self._get_sp800_53_documentation_requirements(phase),
        )

    def get_controls_for_phase(
        self, phase: str, framework: str = "csf"
    ) -> List[ComplianceControl]:
        """
        Get NIST controls relevant to an IR phase.

        Args:
            phase: IR phase name
            framework: "csf" or "sp800_53"

        Returns:
            List of ComplianceControl objects
        """
        if framework == "csf":
            mapping = self.CSF_PHASE_MAPPING.get(phase, {})
            categories = mapping.get("categories", [])
            fw = ComplianceFramework.NIST_CSF_2
        else:
            mapping = self.SP800_53_PHASE_MAPPING.get(phase, {})
            categories = mapping.get("controls", [])
            fw = ComplianceFramework.NIST_800_53

        controls = []
        for control_id in categories:
            control = ComplianceControl(
                framework=fw,
                control_id=control_id,
                control_name=self._get_control_name(control_id, framework),
                description=self._get_control_description(control_id, framework),
            )
            controls.append(control)

        return controls

    def validate_phase_compliance(
        self,
        phase: str,
        completed_actions: List[str],
        evidence_collected: List[str],
        framework: str = "csf",
        operator: str = "",
    ) -> List[ComplianceCheck]:
        """
        Validate compliance for a phase.

        Args:
            phase: IR phase name
            completed_actions: Completed checklist items
            evidence_collected: Evidence entry descriptions
            framework: "csf" or "sp800_53"
            operator: Operator name

        Returns:
            List of ComplianceCheck results
        """
        controls = self.get_controls_for_phase(phase, framework)
        checks = []

        for control in controls:
            status = self._evaluate_control_compliance(
                control.control_id,
                completed_actions,
                evidence_collected,
                framework,
            )

            check = ComplianceCheck(
                framework=control.framework,
                control_id=control.control_id,
                control_name=control.control_name,
                status=status,
                evidence_required=self._get_evidence_requirements(
                    control.control_id, framework
                ),
                recommendation=self._get_recommendation(control.control_id, status),
                evaluated_by=operator,
            )
            checks.append(check)

        return checks

    def _get_control_name(self, control_id: str, framework: str) -> str:
        """Get control name."""
        if framework == "csf":
            csf_names = {
                "DE.AE-01": "Anomalies and events are analyzed",
                "DE.AE-02": "Potentially adverse events are analyzed",
                "DE.AE-03": "Event data are collected and correlated",
                "DE.CM-01": "Networks are monitored",
                "DE.CM-02": "Physical environment is monitored",
                "DE.CM-03": "Personnel activity is monitored",
                "RS.AN-01": "Incident analysis is conducted",
                "RS.AN-02": "Incident impact is understood",
                "RS.AN-03": "Forensics are performed",
                "RS.CO-01": "Incident status is communicated",
                "RS.CO-02": "Incident reports are shared",
                "RS.MI-01": "Incidents are contained",
                "RS.MI-02": "Incidents are mitigated",
                "RS.IM-01": "Response plans incorporate lessons learned",
                "RS.IM-02": "Response strategies are updated",
                "RC.RP-01": "Recovery plan is executed",
                "RC.CO-01": "Recovery is communicated",
                "RC.CO-02": "Recovery status is reported",
                "GV.OC-01": "Organizational context is understood",
                "PR.DS-01": "Data-at-rest is protected",
                "PR.DS-02": "Data-in-transit is protected",
            }
            return csf_names.get(control_id, f"CSF {control_id}")
        else:
            sp800_names = {
                "IR-4": "Incident Handling",
                "IR-5": "Incident Monitoring",
                "IR-6": "Incident Reporting",
                "IR-8": "Incident Response Plan",
                "AU-6": "Audit Record Review, Analysis, and Reporting",
                "AU-12": "Audit Record Generation",
                "SI-3": "Malicious Code Protection",
                "SI-4": "System Monitoring",
                "SI-7": "Software, Firmware, and Information Integrity",
                "SC-7": "Boundary Protection",
                "AC-2": "Account Management",
                "CP-9": "System Backup",
                "CP-10": "System Recovery and Reconstitution",
                "CA-7": "Continuous Monitoring",
            }
            return sp800_names.get(control_id, f"SP 800-53 {control_id}")

    def _get_control_description(self, control_id: str, framework: str) -> str:
        """Get control description."""
        # Simplified descriptions - in production, fetch from OSCAL catalog
        return f"NIST {framework.upper()} control {control_id}"

    def _get_evidence_requirements(
        self, control_id: str, framework: str
    ) -> List[str]:
        """Get evidence requirements for a control."""
        requirements = {
            "IR-4": [
                "Incident handling procedures",
                "Incident response records",
                "Lessons learned documentation",
            ],
            "IR-6": [
                "Incident report forms",
                "Notification records",
                "Escalation documentation",
            ],
            "AU-6": [
                "Audit log analysis reports",
                "Anomaly investigation records",
            ],
            "RS.AN-01": [
                "Incident analysis documentation",
                "Investigation timeline",
            ],
            "RS.MI-01": [
                "Containment action records",
                "Isolation verification",
            ],
            "RC.RP-01": [
                "Recovery plan execution records",
                "System restoration verification",
            ],
        }
        return requirements.get(control_id, ["Documented evidence of control implementation"])

    def _get_csf_documentation_requirements(self, phase: str) -> List[str]:
        """Get CSF documentation requirements for a phase."""
        docs = {
            "detection": [
                "Monitoring and alerting records",
                "Event correlation logs",
                "Detection timestamp documentation",
            ],
            "analysis": [
                "Incident analysis report",
                "Impact assessment",
                "Forensic findings",
            ],
            "containment": [
                "Containment actions log",
                "Network isolation records",
            ],
            "eradication": [
                "Threat removal verification",
                "System integrity checks",
            ],
            "recovery": [
                "Recovery plan execution",
                "System restoration verification",
            ],
            "post_incident": [
                "Lessons learned report",
                "Improvement recommendations",
            ],
        }
        return docs.get(phase, [])

    def _get_sp800_53_documentation_requirements(self, phase: str) -> List[str]:
        """Get SP 800-53 documentation requirements for a phase."""
        # Similar structure to CSF but mapped to 800-53 controls
        return self._get_csf_documentation_requirements(phase)

    def _evaluate_control_compliance(
        self,
        control_id: str,
        completed_actions: List[str],
        evidence_collected: List[str],
        framework: str,
    ) -> ComplianceStatus:
        """Evaluate compliance status for a control."""
        # Simplified evaluation - in production, use more sophisticated matching
        evidence_text = " ".join(evidence_collected).lower()

        keywords = {
            "IR-4": ["incident", "handling", "response"],
            "IR-6": ["report", "notification", "escalat"],
            "AU-6": ["audit", "log", "analysis"],
            "RS.AN-01": ["analysis", "investigation"],
            "RS.MI-01": ["contain", "isolat"],
            "RC.RP-01": ["recover", "restor"],
        }

        control_keywords = keywords.get(control_id, [])
        if not control_keywords:
            return ComplianceStatus.NOT_EVALUATED

        matches = sum(1 for kw in control_keywords if kw in evidence_text)

        if matches >= len(control_keywords):
            return ComplianceStatus.COMPLIANT
        elif matches > 0:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.GAP

    def _get_recommendation(
        self, control_id: str, status: ComplianceStatus
    ) -> Optional[str]:
        """Get recommendation based on status."""
        if status == ComplianceStatus.COMPLIANT:
            return None

        recommendations = {
            "IR-4": "Ensure incident handling procedures are documented and followed.",
            "IR-6": "Document all incident reporting and notification activities.",
            "AU-6": "Perform and document audit log review and analysis.",
            "RS.AN-01": "Conduct and document incident analysis activities.",
            "RS.MI-01": "Document all containment and mitigation actions taken.",
            "RC.RP-01": "Execute and document recovery plan procedures.",
        }
        return recommendations.get(control_id, f"Review requirements for {control_id}")


class NVDIntegration:
    """
    Integration with NIST National Vulnerability Database (NVD) API.

    API Documentation: https://nvd.nist.gov/developers/vulnerabilities

    Features:
    - Search CVEs by keyword, CPE, or date range
    - Get detailed CVE information
    - Check for CISA KEV (Known Exploited Vulnerabilities)
    - Rate limiting support (with/without API key)

    Rate Limits:
    - Without API key: 5 requests per 30 seconds
    - With API key: 50 requests per 30 seconds
    """

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Initialize NVD integration.

        Args:
            api_key: NVD API key (optional but recommended)
                     Get one at: https://nvd.nist.gov/developers/request-an-api-key
            cache_dir: Directory for caching CVE data
        """
        self.api_key = api_key
        self.cache_dir = cache_dir or Path.home() / ".cyberops_companion" / "nvd_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.requests_per_window = 50 if api_key else 5
        self.window_seconds = 30
        self._request_times: List[float] = []

    def _rate_limit(self) -> None:
        """Apply rate limiting."""
        now = time.time()
        self._request_times = [
            t for t in self._request_times
            if now - t < self.window_seconds
        ]

        if len(self._request_times) >= self.requests_per_window:
            sleep_time = self.window_seconds - (now - self._request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limiting: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)

        self._request_times.append(time.time())

    def _make_request(
        self, params: Dict[str, Any], timeout: int = 60
    ) -> Optional[Dict]:
        """Make API request with rate limiting."""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available")
            return None

        self._rate_limit()

        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"NVD API request failed: {e}")
            return None

    def search_cves(
        self,
        keyword: Optional[str] = None,
        cpe_name: Optional[str] = None,
        cve_id: Optional[str] = None,
        cvss_v3_severity: Optional[str] = None,
        pub_start_date: Optional[datetime] = None,
        pub_end_date: Optional[datetime] = None,
        results_per_page: int = 20,
        start_index: int = 0,
    ) -> Tuple[List[CVEInfo], int]:
        """
        Search for CVEs in NVD.

        Args:
            keyword: Keyword search (e.g., "ransomware", "lockbit")
            cpe_name: CPE name to filter by
            cve_id: Specific CVE ID to retrieve
            cvss_v3_severity: Severity filter (CRITICAL, HIGH, MEDIUM, LOW)
            pub_start_date: Published after this date
            pub_end_date: Published before this date
            results_per_page: Results per page (max 2000)
            start_index: Pagination start index

        Returns:
            Tuple of (List of CVEInfo, total_results)
        """
        params: Dict[str, Any] = {
            "resultsPerPage": min(results_per_page, 2000),
            "startIndex": start_index,
        }

        if keyword:
            params["keywordSearch"] = keyword
        if cpe_name:
            params["cpeName"] = cpe_name
        if cve_id:
            params["cveId"] = cve_id
        if cvss_v3_severity:
            params["cvssV3Severity"] = cvss_v3_severity
        if pub_start_date:
            params["pubStartDate"] = pub_start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        if pub_end_date:
            params["pubEndDate"] = pub_end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

        result = self._make_request(params)
        if not result:
            return [], 0

        total_results = result.get("totalResults", 0)
        vulnerabilities = result.get("vulnerabilities", [])

        cves = []
        for vuln in vulnerabilities:
            cve_data = vuln.get("cve", {})
            cve_info = self._parse_cve(cve_data)
            if cve_info:
                cves.append(cve_info)

        return cves, total_results

    def get_cve(self, cve_id: str) -> Optional[CVEInfo]:
        """
        Get details for a specific CVE.

        Args:
            cve_id: CVE ID (e.g., "CVE-2024-12345")

        Returns:
            CVEInfo or None if not found
        """
        cves, _ = self.search_cves(cve_id=cve_id)
        return cves[0] if cves else None

    def search_ransomware_cves(
        self,
        ransomware_name: Optional[str] = None,
        days_back: int = 365,
    ) -> List[CVEInfo]:
        """
        Search for CVEs commonly associated with ransomware.

        Args:
            ransomware_name: Specific ransomware family name
            days_back: Look back period in days

        Returns:
            List of relevant CVEs
        """
        keywords = [ransomware_name] if ransomware_name else [
            "ransomware",
            "encryption",
            "remote code execution",
        ]

        all_cves = []
        pub_start = datetime.now(timezone.utc) - timedelta(days=days_back)

        for keyword in keywords[:3]:  # Limit to avoid rate limiting
            cves, _ = self.search_cves(
                keyword=keyword,
                cvss_v3_severity="CRITICAL",
                pub_start_date=pub_start,
                results_per_page=10,
            )
            all_cves.extend(cves)

        # Deduplicate by CVE ID
        seen = set()
        unique_cves = []
        for cve in all_cves:
            if cve.cve_id not in seen:
                seen.add(cve.cve_id)
                unique_cves.append(cve)

        return unique_cves

    def get_kev_cves(self) -> List[CVEInfo]:
        """
        Get CVEs that are in CISA's Known Exploited Vulnerabilities catalog.

        These are high-priority CVEs that are actively exploited.

        Returns:
            List of KEV CVEs
        """
        # NVD doesn't have a direct KEV filter, but CVEs in KEV have
        # cisaExploitAdd, cisaActionDue fields in the response
        # For a full KEV list, use CISA's KEV JSON directly:
        # https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json

        cves, _ = self.search_cves(
            cvss_v3_severity="CRITICAL",
            results_per_page=50,
        )

        kev_cves = [cve for cve in cves if cve.cisa_kev]
        return kev_cves

    def _parse_cve(self, cve_data: Dict) -> Optional[CVEInfo]:
        """Parse NVD CVE response into CVEInfo model."""
        try:
            cve_id = cve_data.get("id", "")
            if not cve_id:
                return None

            # Get description (English)
            descriptions = cve_data.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break

            # Parse dates
            published = datetime.fromisoformat(
                cve_data.get("published", "").replace("Z", "+00:00")
            )
            last_modified = datetime.fromisoformat(
                cve_data.get("lastModified", "").replace("Z", "+00:00")
            )

            # Parse CVSS v3
            cvss_v3 = None
            metrics = cve_data.get("metrics", {})
            cvss_v31_data = metrics.get("cvssMetricV31", [])
            if cvss_v31_data:
                cvss_data = cvss_v31_data[0].get("cvssData", {})
                cvss_v3 = CVSSScore(
                    version="3.1",
                    vector_string=cvss_data.get("vectorString"),
                    base_score=cvss_data.get("baseScore", 0),
                    severity=cvss_data.get("baseSeverity", "UNKNOWN"),
                    exploitability_score=cvss_v31_data[0].get("exploitabilityScore"),
                    impact_score=cvss_v31_data[0].get("impactScore"),
                )

            # Check for CISA KEV
            cisa_kev = "cisaExploitAdd" in cve_data
            cisa_action_due = None
            cisa_required_action = None
            if cisa_kev:
                if cve_data.get("cisaActionDue"):
                    cisa_action_due = datetime.fromisoformat(
                        cve_data["cisaActionDue"].replace("Z", "+00:00")
                    )
                cisa_required_action = cve_data.get("cisaRequiredAction")

            # Get references
            references = [
                ref.get("url", "")
                for ref in cve_data.get("references", [])
                if ref.get("url")
            ]

            # Get weaknesses (CWE)
            weaknesses = []
            for weakness in cve_data.get("weaknesses", []):
                for desc in weakness.get("description", []):
                    if desc.get("lang") == "en":
                        weaknesses.append(desc.get("value", ""))

            return CVEInfo(
                cve_id=cve_id,
                source_identifier=cve_data.get("sourceIdentifier"),
                description=description,
                published=published,
                last_modified=last_modified,
                cvss_v3=cvss_v3,
                vuln_status=cve_data.get("vulnStatus", ""),
                cisa_kev=cisa_kev,
                cisa_action_due=cisa_action_due,
                cisa_required_action=cisa_required_action,
                references=references[:10],  # Limit references
                weaknesses=weaknesses,
            )

        except Exception as e:
            logger.warning(f"Failed to parse CVE data: {e}")
            return None

    def enrich_incident_with_cves(
        self,
        affected_software: List[str],
        ransomware_family: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enrich incident with CVE information.

        Args:
            affected_software: List of affected software names
            ransomware_family: Known ransomware family name

        Returns:
            Dictionary with CVE enrichment data
        """
        enrichment = {
            "queried_at": datetime.now(timezone.utc).isoformat(),
            "software_cves": {},
            "ransomware_cves": [],
            "critical_cves": [],
            "kev_cves": [],
            "total_cves_found": 0,
        }

        # Search for software-specific CVEs
        for software in affected_software[:5]:  # Limit queries
            cves, total = self.search_cves(keyword=software, results_per_page=5)
            enrichment["software_cves"][software] = {
                "cves": [cve.cve_id for cve in cves],
                "total_available": total,
            }
            enrichment["total_cves_found"] += len(cves)

            # Collect critical and KEV CVEs
            for cve in cves:
                if cve.is_critical():
                    enrichment["critical_cves"].append(cve.cve_id)
                if cve.cisa_kev:
                    enrichment["kev_cves"].append(cve.cve_id)

        # Search for ransomware-specific CVEs
        if ransomware_family:
            ransomware_cves = self.search_ransomware_cves(ransomware_family)
            enrichment["ransomware_cves"] = [cve.cve_id for cve in ransomware_cves]

        return enrichment
