"""
Feed Normalizer.

Utility functions for normalizing IOCs from different CTI sources
into a consistent format for storage and analysis.
"""
import hashlib
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from src.integrations.cti_feeds.base import (
    IOCType,
    NormalizedIOC,
    ThreatLevel,
)

logger = logging.getLogger(__name__)


def normalize_ioc_value(value: str, ioc_type: IOCType) -> str:
    """
    Normalize an IOC value to a consistent format.

    Args:
        value: The IOC value to normalize.
        ioc_type: The type of IOC.

    Returns:
        Normalized value.
    """
    value = value.strip()

    if ioc_type == IOCType.IP_ADDRESS:
        # Remove leading zeros from octets
        parts = value.split(".")
        if len(parts) == 4:
            value = ".".join(str(int(p)) for p in parts if p.isdigit())

    elif ioc_type in [IOCType.DOMAIN, IOCType.HOSTNAME]:
        # Lowercase and remove trailing dot
        value = value.lower().rstrip(".")

    elif ioc_type == IOCType.URL:
        # Lowercase scheme and host
        if "://" in value:
            scheme, rest = value.split("://", 1)
            if "/" in rest:
                host, path = rest.split("/", 1)
                value = f"{scheme.lower()}://{host.lower()}/{path}"
            else:
                value = f"{scheme.lower()}://{rest.lower()}"

    elif ioc_type in [
        IOCType.FILE_HASH_MD5,
        IOCType.FILE_HASH_SHA1,
        IOCType.FILE_HASH_SHA256,
    ]:
        # Lowercase hash
        value = value.lower()

    elif ioc_type == IOCType.EMAIL:
        # Lowercase
        value = value.lower()

    elif ioc_type == IOCType.CVE:
        # Uppercase CVE prefix
        value = value.upper()

    return value


def deduplicate_iocs(iocs: List[NormalizedIOC]) -> List[NormalizedIOC]:
    """
    Deduplicate IOCs, merging metadata from duplicates.

    Args:
        iocs: List of IOCs to deduplicate.

    Returns:
        Deduplicated list with merged metadata.
    """
    seen: Dict[Tuple[str, IOCType], NormalizedIOC] = {}

    for ioc in iocs:
        normalized_value = normalize_ioc_value(ioc.value, ioc.type)
        key = (normalized_value, ioc.type)

        if key in seen:
            # Merge with existing
            existing = seen[key]
            seen[key] = merge_iocs(existing, ioc)
        else:
            # Normalize and add
            ioc.value = normalized_value
            seen[key] = ioc

    return list(seen.values())


def merge_iocs(existing: NormalizedIOC, new: NormalizedIOC) -> NormalizedIOC:
    """
    Merge two IOC records, keeping the best data from each.

    Args:
        existing: The existing IOC record.
        new: The new IOC record to merge.

    Returns:
        Merged IOC.
    """
    # Keep highest threat level
    threat_priority = {
        ThreatLevel.CRITICAL: 4,
        ThreatLevel.HIGH: 3,
        ThreatLevel.MEDIUM: 2,
        ThreatLevel.LOW: 1,
        ThreatLevel.UNKNOWN: 0,
    }
    if threat_priority.get(new.threat_level, 0) > threat_priority.get(existing.threat_level, 0):
        existing.threat_level = new.threat_level

    # Keep highest confidence
    existing.confidence = max(existing.confidence, new.confidence)

    # Merge tags (unique)
    all_tags = set(existing.tags) | set(new.tags)
    existing.tags = list(all_tags)[:20]  # Limit to 20

    # Merge categories (unique)
    all_categories = set(existing.categories) | set(new.categories)
    existing.categories = list(all_categories)[:10]

    # Update sources
    if new.source and new.source not in existing.source:
        existing.source = f"{existing.source},{new.source}"
        existing.source_ref = f"{existing.source_ref},{new.source_ref}"

    # Merge related entities
    existing.related_actors = list(set(existing.related_actors) | set(new.related_actors))[:10]
    existing.related_campaigns = list(set(existing.related_campaigns) | set(new.related_campaigns))[:10]
    existing.mitre_techniques = list(set(existing.mitre_techniques) | set(new.mitre_techniques))[:10]

    # Keep earliest first_seen
    if new.first_seen:
        if not existing.first_seen or new.first_seen < existing.first_seen:
            existing.first_seen = new.first_seen

    # Keep latest last_seen
    if new.last_seen:
        if not existing.last_seen or new.last_seen > existing.last_seen:
            existing.last_seen = new.last_seen

    # Keep geographic info if not present
    if not existing.country and new.country:
        existing.country = new.country
    if not existing.asn and new.asn:
        existing.asn = new.asn

    # Merge raw data
    existing.raw_data.update(new.raw_data)

    return existing


def calculate_risk_score(ioc: NormalizedIOC) -> float:
    """
    Calculate a risk score (0-100) for an IOC based on its attributes.

    Args:
        ioc: The IOC to score.

    Returns:
        Risk score from 0-100.
    """
    score = 0.0

    # Base score from threat level
    threat_scores = {
        ThreatLevel.CRITICAL: 80,
        ThreatLevel.HIGH: 60,
        ThreatLevel.MEDIUM: 40,
        ThreatLevel.LOW: 20,
        ThreatLevel.UNKNOWN: 10,
    }
    score += threat_scores.get(ioc.threat_level, 10)

    # Confidence modifier (-10 to +10)
    score += (ioc.confidence - 0.5) * 20

    # Multiple sources bonus
    if ioc.source and "," in ioc.source:
        source_count = len(ioc.source.split(","))
        score += min(source_count * 2, 10)

    # Related actors/campaigns bonus
    if ioc.related_actors:
        score += min(len(ioc.related_actors) * 3, 9)
    if ioc.related_campaigns:
        score += min(len(ioc.related_campaigns) * 3, 9)

    # MITRE techniques bonus
    if ioc.mitre_techniques:
        score += min(len(ioc.mitre_techniques) * 2, 6)

    # High-risk tags
    high_risk_tags = [
        "ransomware", "c2", "apt", "malware", "trojan",
        "botnet", "phishing", "exploit", "backdoor", "rat"
    ]
    for tag in ioc.tags:
        tag_lower = tag.lower()
        if any(risk in tag_lower for risk in high_risk_tags):
            score += 5
            break

    # Clamp to 0-100
    return max(0, min(100, score))


def filter_iocs(
    iocs: List[NormalizedIOC],
    min_confidence: float = 0.0,
    min_threat_level: Optional[ThreatLevel] = None,
    allowed_types: Optional[List[IOCType]] = None,
    exclude_tags: Optional[List[str]] = None,
) -> List[NormalizedIOC]:
    """
    Filter IOCs based on criteria.

    Args:
        iocs: List of IOCs to filter.
        min_confidence: Minimum confidence score.
        min_threat_level: Minimum threat level.
        allowed_types: Only include these IOC types.
        exclude_tags: Exclude IOCs with these tags.

    Returns:
        Filtered list of IOCs.
    """
    threat_order = [
        ThreatLevel.UNKNOWN,
        ThreatLevel.LOW,
        ThreatLevel.MEDIUM,
        ThreatLevel.HIGH,
        ThreatLevel.CRITICAL,
    ]

    min_level_index = 0
    if min_threat_level:
        try:
            min_level_index = threat_order.index(min_threat_level)
        except ValueError:
            pass

    filtered = []
    exclude_set = set(t.lower() for t in (exclude_tags or []))

    for ioc in iocs:
        # Check confidence
        if ioc.confidence < min_confidence:
            continue

        # Check threat level
        try:
            ioc_level_index = threat_order.index(ioc.threat_level)
            if ioc_level_index < min_level_index:
                continue
        except ValueError:
            pass

        # Check type
        if allowed_types and ioc.type not in allowed_types:
            continue

        # Check excluded tags
        if exclude_set:
            ioc_tags_lower = set(t.lower() for t in ioc.tags)
            if ioc_tags_lower & exclude_set:
                continue

        filtered.append(ioc)

    return filtered


def enrich_with_mitre(iocs: List[NormalizedIOC]) -> List[NormalizedIOC]:
    """
    Enrich IOCs with MITRE ATT&CK technique mappings based on tags.

    Args:
        iocs: List of IOCs to enrich.

    Returns:
        IOCs with added MITRE technique mappings.
    """
    tag_to_technique = {
        "c2": ["T1071 - Application Layer Protocol"],
        "command-and-control": ["T1071 - Application Layer Protocol"],
        "ransomware": ["T1486 - Data Encrypted for Impact", "T1490 - Inhibit System Recovery"],
        "phishing": ["T1566 - Phishing"],
        "spearphishing": ["T1566.001 - Spearphishing Attachment"],
        "credential_theft": ["T1003 - OS Credential Dumping"],
        "trojan": ["T1204 - User Execution"],
        "rat": ["T1219 - Remote Access Software"],
        "keylogger": ["T1056 - Input Capture"],
        "dropper": ["T1105 - Ingress Tool Transfer"],
        "tor": ["T1090.003 - Multi-hop Proxy"],
        "cobalt_strike": ["T1071.001 - Web Protocols", "T1059.001 - PowerShell"],
        "emotet": ["T1566.001 - Spearphishing Attachment", "T1055 - Process Injection"],
        "bruteforce": ["T1110 - Brute Force"],
        "scanner": ["T1595 - Active Scanning"],
        "dga": ["T1568.002 - Domain Generation Algorithms"],
        "exfiltration": ["T1041 - Exfiltration Over C2 Channel"],
        "persistence": ["T1547 - Boot or Logon Autostart Execution"],
        "lateral_movement": ["T1021 - Remote Services"],
        "privilege_escalation": ["T1068 - Exploitation for Privilege Escalation"],
    }

    for ioc in iocs:
        existing_techniques = set(ioc.mitre_techniques)

        for tag in ioc.tags:
            tag_lower = tag.lower().replace("-", "_").replace(" ", "_")
            for key, techniques in tag_to_technique.items():
                if key in tag_lower:
                    for tech in techniques:
                        if tech not in existing_techniques:
                            existing_techniques.add(tech)

        ioc.mitre_techniques = list(existing_techniques)[:15]

    return iocs


def generate_ioc_fingerprint(ioc: NormalizedIOC) -> str:
    """
    Generate a unique fingerprint for an IOC.

    Used for deduplication and change detection.

    Args:
        ioc: The IOC to fingerprint.

    Returns:
        SHA256 fingerprint string.
    """
    normalized_value = normalize_ioc_value(ioc.value, ioc.type)
    fingerprint_data = f"{ioc.type.value}:{normalized_value}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


def validate_ioc(value: str, ioc_type: IOCType) -> Tuple[bool, Optional[str]]:
    """
    Validate an IOC value against its type.

    Args:
        value: The IOC value to validate.
        ioc_type: The type of IOC.

    Returns:
        Tuple of (is_valid, error_message).
    """
    value = value.strip()

    if not value:
        return False, "Empty value"

    if ioc_type == IOCType.IP_ADDRESS:
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(pattern, value):
            return False, "Invalid IPv4 address format"

    elif ioc_type == IOCType.DOMAIN:
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            return False, "Invalid domain format"

    elif ioc_type == IOCType.FILE_HASH_MD5:
        if not re.match(r'^[a-fA-F0-9]{32}$', value):
            return False, "Invalid MD5 hash format (expected 32 hex characters)"

    elif ioc_type == IOCType.FILE_HASH_SHA1:
        if not re.match(r'^[a-fA-F0-9]{40}$', value):
            return False, "Invalid SHA1 hash format (expected 40 hex characters)"

    elif ioc_type == IOCType.FILE_HASH_SHA256:
        if not re.match(r'^[a-fA-F0-9]{64}$', value):
            return False, "Invalid SHA256 hash format (expected 64 hex characters)"

    elif ioc_type == IOCType.EMAIL:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            return False, "Invalid email format"

    elif ioc_type == IOCType.CVE:
        if not re.match(r'^CVE-\d{4}-\d{4,}$', value, re.IGNORECASE):
            return False, "Invalid CVE format (expected CVE-YYYY-NNNNN)"

    elif ioc_type == IOCType.URL:
        if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', value, re.IGNORECASE):
            return False, "Invalid URL format"

    return True, None


def sanitize_tags(tags: List[str], max_length: int = 50) -> List[str]:
    """
    Sanitize and normalize tags.

    Args:
        tags: List of tags to sanitize.
        max_length: Maximum length for each tag.

    Returns:
        Sanitized list of tags.
    """
    sanitized = []
    seen = set()

    for tag in tags:
        if not tag or not isinstance(tag, str):
            continue

        # Clean up
        tag = tag.strip()
        tag = re.sub(r'[^\w\s\-_:.]', '', tag)  # Remove special chars
        tag = tag[:max_length]

        # Skip duplicates (case-insensitive)
        tag_lower = tag.lower()
        if tag_lower in seen:
            continue
        seen.add(tag_lower)

        if tag:
            sanitized.append(tag)

    return sanitized


def extract_related_iocs(ioc: NormalizedIOC) -> List[str]:
    """
    Extract potentially related IOCs from an IOC's metadata.

    For example, extract domain from URL, or look for referenced hashes.

    Args:
        ioc: The IOC to analyze.

    Returns:
        List of potentially related IOC values.
    """
    related = []

    if ioc.type == IOCType.URL:
        # Extract domain from URL
        match = re.search(r'https?://([^/]+)', ioc.value)
        if match:
            domain = match.group(1)
            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]
            related.append(domain)

    # Look for hashes in description
    if ioc.description:
        md5_matches = re.findall(r'\b[a-fA-F0-9]{32}\b', ioc.description)
        sha256_matches = re.findall(r'\b[a-fA-F0-9]{64}\b', ioc.description)
        related.extend(md5_matches)
        related.extend(sha256_matches)

    # Look for IPs in description
    if ioc.description:
        ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        ip_matches = re.findall(ip_pattern, ioc.description)
        related.extend(ip_matches)

    # Remove the original IOC value
    related = [r for r in related if r.lower() != ioc.value.lower()]

    return list(set(related))
