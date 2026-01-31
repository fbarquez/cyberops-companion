"""
NVD (National Vulnerability Database) Service.

Provides integration with:
- NVD API 2.0 for CVE data
- EPSS API for exploit prediction scores
- CISA KEV catalog for known exploited vulnerabilities

Rate limits (without API key):
- NVD: 5 requests per 30 seconds
- With API key: 50 requests per 30 seconds
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class CVSSSeverity(str, Enum):
    """CVSS Severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class CVEData:
    """Structured CVE data from NVD."""
    cve_id: str
    description: str
    cvss_score: Optional[float] = None
    cvss_version: Optional[str] = None
    cvss_vector: Optional[str] = None
    severity: Optional[str] = None
    cwe_ids: List[str] = None
    references: List[Dict[str, str]] = None
    affected_cpe: List[str] = None
    published_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    epss_score: Optional[float] = None
    epss_percentile: Optional[float] = None
    is_kev: bool = False
    kev_date_added: Optional[datetime] = None
    kev_due_date: Optional[datetime] = None

    def __post_init__(self):
        if self.cwe_ids is None:
            self.cwe_ids = []
        if self.references is None:
            self.references = []
        if self.affected_cpe is None:
            self.affected_cpe = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cve_id": self.cve_id,
            "description": self.description,
            "cvss_score": self.cvss_score,
            "cvss_version": self.cvss_version,
            "cvss_vector": self.cvss_vector,
            "severity": self.severity,
            "cwe_ids": self.cwe_ids,
            "references": self.references,
            "affected_cpe": self.affected_cpe,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "modified_date": self.modified_date.isoformat() if self.modified_date else None,
            "epss_score": self.epss_score,
            "epss_percentile": self.epss_percentile,
            "is_kev": self.is_kev,
            "kev_date_added": self.kev_date_added.isoformat() if self.kev_date_added else None,
            "kev_due_date": self.kev_due_date.isoformat() if self.kev_due_date else None,
        }


class NVDService:
    """
    Service for fetching CVE data from NVD and related sources.

    Usage:
        nvd = NVDService()
        cve_data = await nvd.get_cve("CVE-2021-44228")
    """

    NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    EPSS_API_BASE = "https://api.first.org/data/v1/epss"
    KEV_CATALOG_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NVD service.

        Args:
            api_key: NVD API key (optional, increases rate limit)
        """
        self.api_key = api_key or getattr(settings, 'NVD_API_KEY', None)
        self._kev_cache: Optional[Dict[str, Dict]] = None
        self._kev_cache_time: Optional[datetime] = None
        self._rate_limit_delay = 6.0 if not self.api_key else 0.6  # seconds between requests

    async def get_cve(
        self,
        cve_id: str,
        include_epss: bool = True,
        include_kev: bool = True
    ) -> Optional[CVEData]:
        """
        Get CVE data from NVD.

        Args:
            cve_id: CVE ID (e.g., "CVE-2021-44228")
            include_epss: Whether to fetch EPSS data
            include_kev: Whether to check KEV catalog

        Returns:
            CVEData object or None if not found
        """
        # Validate CVE ID format
        if not self._validate_cve_id(cve_id):
            logger.warning(f"Invalid CVE ID format: {cve_id}")
            return None

        try:
            # Fetch from NVD
            nvd_data = await self._fetch_from_nvd(cve_id)
            if not nvd_data:
                return None

            cve_data = self._parse_nvd_response(nvd_data)

            # Enrich with EPSS data
            if include_epss:
                epss_data = await self._fetch_epss(cve_id)
                if epss_data:
                    cve_data.epss_score = epss_data.get("epss")
                    cve_data.epss_percentile = epss_data.get("percentile")

            # Check KEV catalog
            if include_kev:
                kev_data = await self._check_kev(cve_id)
                if kev_data:
                    cve_data.is_kev = True
                    cve_data.kev_date_added = kev_data.get("date_added")
                    cve_data.kev_due_date = kev_data.get("due_date")

            return cve_data

        except Exception as e:
            logger.error(f"Error fetching CVE {cve_id}: {e}")
            return None

    async def search_cves(
        self,
        keyword: Optional[str] = None,
        cpe_name: Optional[str] = None,
        cvss_severity: Optional[str] = None,
        pub_start_date: Optional[datetime] = None,
        pub_end_date: Optional[datetime] = None,
        results_per_page: int = 20,
        start_index: int = 0
    ) -> Dict[str, Any]:
        """
        Search CVEs with filters.

        Args:
            keyword: Keyword search
            cpe_name: CPE name to search for
            cvss_severity: Severity level (critical, high, medium, low)
            pub_start_date: Filter by publication start date
            pub_end_date: Filter by publication end date
            results_per_page: Number of results per page (max 2000)
            start_index: Starting index for pagination

        Returns:
            Dictionary with results and pagination info
        """
        params = {
            "resultsPerPage": min(results_per_page, 2000),
            "startIndex": start_index
        }

        if keyword:
            params["keywordSearch"] = keyword
        if cpe_name:
            params["cpeName"] = cpe_name
        if cvss_severity:
            params["cvssV3Severity"] = cvss_severity.upper()
        if pub_start_date:
            params["pubStartDate"] = pub_start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        if pub_end_date:
            params["pubEndDate"] = pub_end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.api_key:
                    headers["apiKey"] = self.api_key

                response = await client.get(
                    self.NVD_API_BASE,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()

                # Parse results
                vulnerabilities = []
                for item in data.get("vulnerabilities", []):
                    cve_data = self._parse_nvd_response(item)
                    if cve_data:
                        vulnerabilities.append(cve_data.to_dict())

                return {
                    "total_results": data.get("totalResults", 0),
                    "results_per_page": data.get("resultsPerPage", 0),
                    "start_index": data.get("startIndex", 0),
                    "vulnerabilities": vulnerabilities
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"NVD API HTTP error: {e}")
            return {"error": str(e), "vulnerabilities": []}
        except Exception as e:
            logger.error(f"Error searching CVEs: {e}")
            return {"error": str(e), "vulnerabilities": []}

    async def get_recent_cves(
        self,
        days: int = 7,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[CVEData]:
        """
        Get recently published CVEs.

        Args:
            days: Number of days to look back
            severity: Filter by severity (optional)
            limit: Maximum number of results

        Returns:
            List of CVEData objects
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        result = await self.search_cves(
            pub_start_date=start_date,
            pub_end_date=end_date,
            cvss_severity=severity,
            results_per_page=limit
        )

        return [
            CVEData(**{k: v for k, v in cve.items() if k != 'published_date' and k != 'modified_date'})
            for cve in result.get("vulnerabilities", [])
        ]

    # ==================== Private Methods ====================

    def _validate_cve_id(self, cve_id: str) -> bool:
        """Validate CVE ID format."""
        import re
        pattern = r"^CVE-\d{4}-\d{4,}$"
        return bool(re.match(pattern, cve_id.upper()))

    async def _fetch_from_nvd(self, cve_id: str) -> Optional[Dict]:
        """Fetch CVE data from NVD API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.api_key:
                    headers["apiKey"] = self.api_key

                response = await client.get(
                    self.NVD_API_BASE,
                    params={"cveId": cve_id},
                    headers=headers
                )

                if response.status_code == 404:
                    logger.info(f"CVE {cve_id} not found in NVD")
                    return None

                response.raise_for_status()
                data = response.json()

                vulnerabilities = data.get("vulnerabilities", [])
                if vulnerabilities:
                    return vulnerabilities[0]
                return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.warning("NVD API rate limit exceeded. Consider using an API key.")
            else:
                logger.error(f"NVD API error for {cve_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching from NVD: {e}")
            return None

    def _parse_nvd_response(self, data: Dict) -> Optional[CVEData]:
        """Parse NVD API response into CVEData."""
        try:
            cve = data.get("cve", {})
            cve_id = cve.get("id")

            if not cve_id:
                return None

            # Get description (prefer English)
            descriptions = cve.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            if not description and descriptions:
                description = descriptions[0].get("value", "")

            # Get CVSS metrics (prefer v3.1, then v3.0, then v2.0)
            cvss_score = None
            cvss_version = None
            cvss_vector = None
            severity = None

            metrics = cve.get("metrics", {})

            # Try CVSS 3.1
            if "cvssMetricV31" in metrics:
                cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_version = "3.1"
                cvss_vector = cvss_data.get("vectorString")
                severity = cvss_data.get("baseSeverity", "").lower()

            # Try CVSS 3.0
            elif "cvssMetricV30" in metrics:
                cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_version = "3.0"
                cvss_vector = cvss_data.get("vectorString")
                severity = cvss_data.get("baseSeverity", "").lower()

            # Try CVSS 2.0
            elif "cvssMetricV2" in metrics:
                cvss_data = metrics["cvssMetricV2"][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore")
                cvss_version = "2.0"
                cvss_vector = cvss_data.get("vectorString")
                # Map CVSS 2.0 score to severity
                if cvss_score:
                    if cvss_score >= 9.0:
                        severity = "critical"
                    elif cvss_score >= 7.0:
                        severity = "high"
                    elif cvss_score >= 4.0:
                        severity = "medium"
                    else:
                        severity = "low"

            # Get CWEs
            cwe_ids = []
            weaknesses = cve.get("weaknesses", [])
            for weakness in weaknesses:
                for desc in weakness.get("description", []):
                    cwe_value = desc.get("value", "")
                    if cwe_value.startswith("CWE-"):
                        cwe_ids.append(cwe_value)

            # Get references
            references = []
            for ref in cve.get("references", []):
                references.append({
                    "url": ref.get("url"),
                    "source": ref.get("source"),
                    "tags": ref.get("tags", [])
                })

            # Get affected CPEs
            affected_cpe = []
            configurations = cve.get("configurations", [])
            for config in configurations:
                for node in config.get("nodes", []):
                    for cpe_match in node.get("cpeMatch", []):
                        if cpe_match.get("vulnerable"):
                            affected_cpe.append(cpe_match.get("criteria", ""))

            # Parse dates
            published_date = None
            modified_date = None
            if cve.get("published"):
                try:
                    published_date = datetime.fromisoformat(cve["published"].replace("Z", "+00:00"))
                except:
                    pass
            if cve.get("lastModified"):
                try:
                    modified_date = datetime.fromisoformat(cve["lastModified"].replace("Z", "+00:00"))
                except:
                    pass

            return CVEData(
                cve_id=cve_id,
                description=description,
                cvss_score=cvss_score,
                cvss_version=cvss_version,
                cvss_vector=cvss_vector,
                severity=severity,
                cwe_ids=cwe_ids,
                references=references,
                affected_cpe=affected_cpe[:20],  # Limit to 20 CPEs
                published_date=published_date,
                modified_date=modified_date
            )

        except Exception as e:
            logger.error(f"Error parsing NVD response: {e}")
            return None

    async def _fetch_epss(self, cve_id: str) -> Optional[Dict]:
        """Fetch EPSS score from FIRST API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.EPSS_API_BASE,
                    params={"cve": cve_id}
                )
                response.raise_for_status()
                data = response.json()

                if data.get("data"):
                    epss_data = data["data"][0]
                    return {
                        "epss": float(epss_data.get("epss", 0)),
                        "percentile": float(epss_data.get("percentile", 0))
                    }
                return None

        except Exception as e:
            logger.debug(f"Error fetching EPSS for {cve_id}: {e}")
            return None

    async def _check_kev(self, cve_id: str) -> Optional[Dict]:
        """Check if CVE is in CISA KEV catalog."""
        try:
            # Use cached KEV data if fresh (cache for 1 hour)
            if (
                self._kev_cache is not None
                and self._kev_cache_time
                and datetime.utcnow() - self._kev_cache_time < timedelta(hours=1)
            ):
                return self._kev_cache.get(cve_id)

            # Fetch KEV catalog
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.KEV_CATALOG_URL)
                response.raise_for_status()
                data = response.json()

                # Build cache
                self._kev_cache = {}
                for vuln in data.get("vulnerabilities", []):
                    kev_cve_id = vuln.get("cveID")
                    if kev_cve_id:
                        date_added = None
                        due_date = None
                        try:
                            if vuln.get("dateAdded"):
                                date_added = datetime.strptime(vuln["dateAdded"], "%Y-%m-%d")
                            if vuln.get("dueDate"):
                                due_date = datetime.strptime(vuln["dueDate"], "%Y-%m-%d")
                        except:
                            pass

                        self._kev_cache[kev_cve_id] = {
                            "date_added": date_added,
                            "due_date": due_date,
                            "vendor": vuln.get("vendorProject"),
                            "product": vuln.get("product"),
                            "name": vuln.get("vulnerabilityName"),
                            "short_description": vuln.get("shortDescription"),
                            "required_action": vuln.get("requiredAction")
                        }

                self._kev_cache_time = datetime.utcnow()
                return self._kev_cache.get(cve_id)

        except Exception as e:
            logger.debug(f"Error checking KEV catalog: {e}")
            return None

    async def get_kev_catalog(self) -> List[Dict]:
        """
        Get the full CISA KEV catalog.

        Returns:
            List of known exploited vulnerabilities
        """
        # Ensure cache is populated
        await self._check_kev("CVE-0000-0000")

        if self._kev_cache:
            return [
                {"cve_id": cve_id, **data}
                for cve_id, data in self._kev_cache.items()
            ]
        return []


# Singleton instance
_nvd_service: Optional[NVDService] = None


def get_nvd_service() -> NVDService:
    """Get the NVD service singleton."""
    global _nvd_service
    if _nvd_service is None:
        _nvd_service = NVDService()
    return _nvd_service
