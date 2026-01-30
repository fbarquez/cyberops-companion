"""
MITRE ATT&CK Integration.

Provides integration with MITRE ATT&CK framework via:
- STIX 2.1 data from GitHub repository
- TAXII 2.1 server (rate limited)

Repository: https://github.com/mitre-attack/attack-stix-data
TAXII Server: https://attack-taxii.mitre.org

Features:
- Map IR phases to ATT&CK tactics
- Identify relevant techniques for ransomware
- Get mitigations for identified techniques
- Correlate IOCs with ATT&CK techniques
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import hashlib

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from src.integrations.models import (
    ATTACKTechnique,
    ThreatIntelligence,
)

logger = logging.getLogger(__name__)


class MITREATTACKIntegration:
    """
    Integration with MITRE ATT&CK framework.

    Uses GitHub STIX data repository instead of TAXII server
    to avoid rate limiting (10 requests/10 minutes on TAXII).

    Features:
    - Load ATT&CK Enterprise matrix
    - Get ransomware-related techniques
    - Map techniques to IR phases
    - Get mitigations and detections
    """

    GITHUB_STIX_BASE = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master"
    ENTERPRISE_ATTACK_URL = f"{GITHUB_STIX_BASE}/enterprise-attack/enterprise-attack.json"

    # TAXII server (use sparingly due to rate limits)
    TAXII_SERVER = "https://attack-taxii.mitre.org"
    TAXII_API_ROOT = "/api/v21/"

    # Ransomware-specific technique IDs
    RANSOMWARE_TECHNIQUES = {
        # Impact
        "T1486": "Data Encrypted for Impact",
        "T1490": "Inhibit System Recovery",
        "T1489": "Service Stop",
        "T1491": "Defacement",
        "T1561": "Disk Wipe",

        # Discovery
        "T1082": "System Information Discovery",
        "T1083": "File and Directory Discovery",
        "T1135": "Network Share Discovery",
        "T1018": "Remote System Discovery",
        "T1016": "System Network Configuration Discovery",

        # Lateral Movement
        "T1021": "Remote Services",
        "T1021.001": "Remote Desktop Protocol",
        "T1021.002": "SMB/Windows Admin Shares",
        "T1570": "Lateral Tool Transfer",

        # Execution
        "T1059": "Command and Scripting Interpreter",
        "T1059.001": "PowerShell",
        "T1059.003": "Windows Command Shell",
        "T1047": "Windows Management Instrumentation",

        # Persistence
        "T1053": "Scheduled Task/Job",
        "T1543": "Create or Modify System Process",
        "T1547": "Boot or Logon Autostart Execution",

        # Defense Evasion
        "T1562": "Impair Defenses",
        "T1562.001": "Disable or Modify Tools",
        "T1070": "Indicator Removal",
        "T1027": "Obfuscated Files or Information",

        # Credential Access
        "T1003": "OS Credential Dumping",
        "T1555": "Credentials from Password Stores",

        # Collection
        "T1560": "Archive Collected Data",

        # Exfiltration
        "T1041": "Exfiltration Over C2 Channel",
        "T1567": "Exfiltration Over Web Service",

        # Initial Access
        "T1566": "Phishing",
        "T1190": "Exploit Public-Facing Application",
        "T1078": "Valid Accounts",
    }

    # Mapping of IR phases to ATT&CK tactics
    PHASE_TO_TACTICS = {
        "detection": [
            "initial-access",
            "execution",
            "discovery",
        ],
        "analysis": [
            "initial-access",
            "execution",
            "persistence",
            "privilege-escalation",
            "defense-evasion",
            "credential-access",
            "discovery",
            "lateral-movement",
            "collection",
            "exfiltration",
        ],
        "containment": [
            "lateral-movement",
            "command-and-control",
            "exfiltration",
        ],
        "eradication": [
            "persistence",
            "privilege-escalation",
            "defense-evasion",
        ],
        "recovery": [
            "impact",
        ],
        "post_incident": [
            "initial-access",  # Root cause
            "impact",
        ],
    }

    def __init__(self, cache_dir: Optional[Path] = None, offline_mode: bool = False):
        """
        Initialize MITRE ATT&CK integration.

        Args:
            cache_dir: Directory for caching STIX data
            offline_mode: If True, only use cached data
        """
        self.cache_dir = cache_dir or Path.home() / ".cyberops_companion" / "mitre_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode
        self._attack_data: Optional[Dict] = None
        self._techniques: Dict[str, ATTACKTechnique] = {}
        self._mitigations: Dict[str, Dict] = {}
        self._relationships: List[Dict] = []

    def _get_cache_path(self, identifier: str) -> Path:
        """Get cache file path."""
        safe_name = hashlib.md5(identifier.encode()).hexdigest()
        return self.cache_dir / f"{safe_name}.json"

    def _load_from_cache(self, identifier: str) -> Optional[Dict]:
        """Load from cache."""
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
                json.dump(data, f, ensure_ascii=False)
        except IOError as e:
            logger.warning(f"Cache write error: {e}")

    def load_attack_data(self) -> bool:
        """
        Load ATT&CK Enterprise data from GitHub or cache.

        Returns:
            True if data loaded successfully
        """
        if self._attack_data:
            return True

        cache_key = "enterprise_attack"
        cached = self._load_from_cache(cache_key)

        if cached:
            self._attack_data = cached
            self._parse_attack_data()
            return True

        if self.offline_mode or not REQUESTS_AVAILABLE:
            logger.warning("ATT&CK data not available (offline mode or no requests)")
            return False

        try:
            logger.info("Fetching ATT&CK data from GitHub...")
            response = requests.get(self.ENTERPRISE_ATTACK_URL, timeout=120)
            response.raise_for_status()
            self._attack_data = response.json()
            self._save_to_cache(cache_key, self._attack_data)
            self._parse_attack_data()
            logger.info("ATT&CK data loaded successfully")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to fetch ATT&CK data: {e}")
            return False

    def _parse_attack_data(self) -> None:
        """Parse STIX data into internal structures."""
        if not self._attack_data:
            return

        objects = self._attack_data.get("objects", [])

        for obj in objects:
            obj_type = obj.get("type", "")

            if obj_type == "attack-pattern":
                technique = self._parse_technique(obj)
                if technique:
                    self._techniques[technique.technique_id] = technique

            elif obj_type == "course-of-action":
                self._mitigations[obj.get("id", "")] = {
                    "name": obj.get("name", ""),
                    "description": obj.get("description", ""),
                    "external_id": self._get_external_id(obj),
                }

            elif obj_type == "relationship":
                self._relationships.append(obj)

        # Link mitigations to techniques
        self._link_mitigations()

    def _parse_technique(self, obj: Dict) -> Optional[ATTACKTechnique]:
        """Parse STIX attack-pattern into ATTACKTechnique."""
        external_id = self._get_external_id(obj)
        if not external_id:
            return None

        # Get tactics from kill chain phases
        tactics = []
        for phase in obj.get("kill_chain_phases", []):
            if phase.get("kill_chain_name") == "mitre-attack":
                tactics.append(phase.get("phase_name", ""))

        # Check if subtechnique
        is_subtechnique = "." in external_id
        parent_technique = None
        if is_subtechnique:
            parent_technique = external_id.split(".")[0]

        # Get platforms
        platforms = obj.get("x_mitre_platforms", [])

        # Get data sources
        data_sources = []
        for ds in obj.get("x_mitre_data_sources", []):
            if isinstance(ds, str):
                data_sources.append(ds)

        return ATTACKTechnique(
            technique_id=external_id,
            name=obj.get("name", ""),
            description=obj.get("description", ""),
            tactics=tactics,
            is_subtechnique=is_subtechnique,
            parent_technique=parent_technique,
            platforms=platforms,
            data_sources=data_sources,
            detection=obj.get("x_mitre_detection", ""),
            url=f"https://attack.mitre.org/techniques/{external_id.replace('.', '/')}/",
        )

    def _get_external_id(self, obj: Dict) -> Optional[str]:
        """Get ATT&CK external ID from STIX object."""
        for ref in obj.get("external_references", []):
            if ref.get("source_name") == "mitre-attack":
                return ref.get("external_id")
        return None

    def _link_mitigations(self) -> None:
        """Link mitigations to techniques via relationships."""
        for rel in self._relationships:
            if rel.get("relationship_type") == "mitigates":
                source_ref = rel.get("source_ref", "")
                target_ref = rel.get("target_ref", "")

                # Find technique by STIX ID
                for technique in self._techniques.values():
                    # Match by checking if target_ref contains the technique ID
                    if technique.technique_id in target_ref:
                        mitigation = self._mitigations.get(source_ref, {})
                        if mitigation:
                            technique.mitigations.append({
                                "id": mitigation.get("external_id", ""),
                                "name": mitigation.get("name", ""),
                                "description": mitigation.get("description", "")[:500],
                            })

    def get_ransomware_techniques(self) -> List[ATTACKTechnique]:
        """
        Get ATT&CK techniques commonly used by ransomware.

        Returns:
            List of relevant ATTACKTechnique objects
        """
        if not self._techniques:
            self.load_attack_data()

        techniques = []
        for tech_id in self.RANSOMWARE_TECHNIQUES:
            technique = self._techniques.get(tech_id)
            if technique:
                techniques.append(technique)

        return techniques

    def get_techniques_for_phase(self, phase: str) -> List[ATTACKTechnique]:
        """
        Get ATT&CK techniques relevant to an IR phase.

        Args:
            phase: IR phase name

        Returns:
            List of relevant techniques
        """
        if not self._techniques:
            self.load_attack_data()

        tactics = self.PHASE_TO_TACTICS.get(phase, [])
        techniques = []

        for technique in self._techniques.values():
            if any(tactic in technique.tactics for tactic in tactics):
                # Also check if it's a ransomware technique
                if technique.technique_id in self.RANSOMWARE_TECHNIQUES:
                    technique.relevance_score = 1.0
                else:
                    technique.relevance_score = 0.5
                techniques.append(technique)

        # Sort by relevance
        techniques.sort(key=lambda t: t.relevance_score, reverse=True)

        return techniques[:20]  # Limit results

    def get_technique_by_id(self, technique_id: str) -> Optional[ATTACKTechnique]:
        """
        Get a specific technique by ID.

        Args:
            technique_id: ATT&CK technique ID (e.g., "T1486")

        Returns:
            ATTACKTechnique or None
        """
        if not self._techniques:
            self.load_attack_data()
        return self._techniques.get(technique_id)

    def get_mitigations_for_technique(self, technique_id: str) -> List[Dict]:
        """
        Get mitigations for a specific technique.

        Args:
            technique_id: ATT&CK technique ID

        Returns:
            List of mitigation dictionaries
        """
        technique = self.get_technique_by_id(technique_id)
        if technique:
            return technique.mitigations
        return []

    def correlate_iocs_to_techniques(
        self,
        iocs: List[Dict[str, str]],
    ) -> List[ATTACKTechnique]:
        """
        Correlate Indicators of Compromise to ATT&CK techniques.

        Args:
            iocs: List of IOCs with "type" and "value" keys
                  Types: "ip", "domain", "hash", "file_path", "registry", "process"

        Returns:
            List of relevant techniques with relevance indicators
        """
        if not self._techniques:
            self.load_attack_data()

        # IOC type to technique mapping
        ioc_technique_map = {
            "ip": ["T1041", "T1071", "T1095"],  # C2, Application Layer Protocol
            "domain": ["T1071", "T1568", "T1102"],  # Domain-based C2
            "hash": ["T1204", "T1059"],  # Malicious files, execution
            "file_path": {
                "\\AppData\\": ["T1547", "T1053"],  # Persistence locations
                "\\Temp\\": ["T1059", "T1204"],  # Execution
                "\\System32\\": ["T1543", "T1574"],  # System modification
                ".locked": ["T1486"],  # Ransomware encryption
                ".encrypted": ["T1486"],
            },
            "registry": ["T1547", "T1112", "T1546"],  # Registry persistence
            "process": {
                "powershell": ["T1059.001"],
                "cmd": ["T1059.003"],
                "wmic": ["T1047"],
                "psexec": ["T1021.002", "T1570"],
                "vssadmin": ["T1490"],  # Shadow copy deletion
                "bcdedit": ["T1490"],  # Boot config modification
                "wbadmin": ["T1490"],  # Backup deletion
            },
        }

        matched_techniques: Set[str] = set()
        technique_indicators: Dict[str, List[str]] = {}

        for ioc in iocs:
            ioc_type = ioc.get("type", "").lower()
            ioc_value = ioc.get("value", "").lower()

            mapping = ioc_technique_map.get(ioc_type, [])

            if isinstance(mapping, list):
                for tech_id in mapping:
                    matched_techniques.add(tech_id)
                    if tech_id not in technique_indicators:
                        technique_indicators[tech_id] = []
                    technique_indicators[tech_id].append(f"{ioc_type}: {ioc_value}")

            elif isinstance(mapping, dict):
                for pattern, tech_ids in mapping.items():
                    if pattern.lower() in ioc_value:
                        for tech_id in tech_ids:
                            matched_techniques.add(tech_id)
                            if tech_id not in technique_indicators:
                                technique_indicators[tech_id] = []
                            technique_indicators[tech_id].append(
                                f"{ioc_type}: {ioc_value} (matched: {pattern})"
                            )

        # Get full technique objects
        result = []
        for tech_id in matched_techniques:
            technique = self.get_technique_by_id(tech_id)
            if technique:
                technique.relevance_indicators = technique_indicators.get(tech_id, [])
                technique.relevance_score = len(technique.relevance_indicators) / len(iocs)
                result.append(technique)

        # Sort by relevance
        result.sort(key=lambda t: t.relevance_score, reverse=True)

        return result

    def generate_threat_intelligence(
        self,
        incident_id: str,
        iocs: List[Dict[str, str]],
        ransomware_family: Optional[str] = None,
    ) -> ThreatIntelligence:
        """
        Generate comprehensive threat intelligence for an incident.

        Args:
            incident_id: Incident identifier
            iocs: List of IOCs from the incident
            ransomware_family: Known ransomware family name

        Returns:
            ThreatIntelligence object with mapped techniques and recommendations
        """
        # Load ATT&CK data if needed
        self.load_attack_data()

        # Get ransomware techniques
        ransomware_techniques = self.get_ransomware_techniques()

        # Correlate IOCs
        correlated_techniques = self.correlate_iocs_to_techniques(iocs) if iocs else []

        # Combine and deduplicate
        all_techniques: Dict[str, ATTACKTechnique] = {}
        for tech in ransomware_techniques:
            all_techniques[tech.technique_id] = tech
        for tech in correlated_techniques:
            if tech.technique_id in all_techniques:
                # Merge relevance indicators
                existing = all_techniques[tech.technique_id]
                existing.relevance_indicators.extend(tech.relevance_indicators)
                existing.relevance_score = max(existing.relevance_score, tech.relevance_score)
            else:
                all_techniques[tech.technique_id] = tech

        # Get primary tactics
        tactics_count: Dict[str, int] = {}
        for tech in all_techniques.values():
            for tactic in tech.tactics:
                tactics_count[tactic] = tactics_count.get(tactic, 0) + 1

        primary_tactics = sorted(tactics_count.keys(), key=lambda t: tactics_count[t], reverse=True)

        # Collect unique mitigations
        mitigation_set: Dict[str, Dict] = {}
        for tech in all_techniques.values():
            for mitigation in tech.mitigations:
                mit_id = mitigation.get("id", "")
                if mit_id and mit_id not in mitigation_set:
                    mitigation_set[mit_id] = mitigation

        # Generate recommendations
        detection_recommendations = self._generate_detection_recommendations(
            list(all_techniques.values())
        )
        mitigation_recommendations = self._generate_mitigation_recommendations(
            list(mitigation_set.values())
        )

        return ThreatIntelligence(
            incident_id=incident_id,
            mapped_techniques=list(all_techniques.values()),
            primary_tactics=primary_tactics[:5],
            recommended_mitigations=list(mitigation_set.values())[:10],
            ransomware_family=ransomware_family,
            known_iocs=iocs,
            detection_recommendations=detection_recommendations,
            mitigation_recommendations=mitigation_recommendations,
        )

    def _generate_detection_recommendations(
        self, techniques: List[ATTACKTechnique]
    ) -> List[str]:
        """Generate detection recommendations based on techniques."""
        recommendations = set()

        for tech in techniques:
            if tech.data_sources:
                for ds in tech.data_sources[:3]:
                    recommendations.add(f"Enable monitoring for: {ds}")

            if tech.detection:
                # Extract first sentence of detection guidance
                first_sentence = tech.detection.split(".")[0]
                if len(first_sentence) < 200:
                    recommendations.add(first_sentence)

        return list(recommendations)[:10]

    def _generate_mitigation_recommendations(
        self, mitigations: List[Dict]
    ) -> List[str]:
        """Generate mitigation recommendations."""
        recommendations = []

        for mit in mitigations[:10]:
            name = mit.get("name", "")
            description = mit.get("description", "")
            if name:
                # Extract actionable recommendation
                rec = f"{name}"
                if description:
                    first_sentence = description.split(".")[0]
                    if len(first_sentence) < 150:
                        rec += f": {first_sentence}"
                recommendations.append(rec)

        return recommendations

    def export_attack_mapping(
        self,
        techniques: List[ATTACKTechnique],
        format: str = "markdown",
    ) -> str:
        """
        Export ATT&CK technique mapping.

        Args:
            techniques: List of techniques to export
            format: "markdown" or "json"

        Returns:
            Formatted mapping
        """
        if format == "json":
            return json.dumps(
                [tech.model_dump() for tech in techniques],
                indent=2,
                default=str,
            )

        # Markdown format
        lines = [
            "# MITRE ATT&CK Mapping",
            "",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Identified Techniques",
            "",
            "| ID | Name | Tactics | Relevance |",
            "|----|------|---------|-----------|",
        ]

        for tech in techniques:
            tactics_str = ", ".join(tech.tactics[:3])
            relevance = f"{tech.relevance_score:.0%}" if tech.relevance_score else "N/A"
            lines.append(
                f"| [{tech.technique_id}]({tech.url}) | {tech.name} | "
                f"{tactics_str} | {relevance} |"
            )

        # Add mitigations section
        all_mitigations: Dict[str, Dict] = {}
        for tech in techniques:
            for mit in tech.mitigations:
                mit_id = mit.get("id", "")
                if mit_id and mit_id not in all_mitigations:
                    all_mitigations[mit_id] = mit

        if all_mitigations:
            lines.extend([
                "",
                "## Recommended Mitigations",
                "",
            ])
            for mit in list(all_mitigations.values())[:10]:
                lines.append(f"- **{mit.get('id', '')}**: {mit.get('name', '')}")

        return "\n".join(lines)
