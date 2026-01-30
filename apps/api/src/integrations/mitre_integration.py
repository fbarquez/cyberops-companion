"""
MITRE ATT&CK Integration for FastAPI.

Provides integration with MITRE ATT&CK framework for:
- Mapping IR phases to ATT&CK tactics
- Getting techniques for ransomware incidents
- Generating ATT&CK Navigator layers
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ATTACKTechnique(BaseModel):
    """MITRE ATT&CK Technique."""
    technique_id: str
    name: str
    description: str = ""
    tactics: List[str] = Field(default_factory=list)
    is_subtechnique: bool = False
    parent_technique: Optional[str] = None
    platforms: List[str] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    detection: str = ""
    url: str = ""
    mitigations: List[Dict[str, str]] = Field(default_factory=list)
    relevance_score: float = 0.0
    relevance_indicators: List[str] = Field(default_factory=list)


# MITRE ATT&CK Tactics
TACTICS = [
    {"id": "TA0043", "name": "Reconnaissance", "short_name": "reconnaissance"},
    {"id": "TA0042", "name": "Resource Development", "short_name": "resource-development"},
    {"id": "TA0001", "name": "Initial Access", "short_name": "initial-access"},
    {"id": "TA0002", "name": "Execution", "short_name": "execution"},
    {"id": "TA0003", "name": "Persistence", "short_name": "persistence"},
    {"id": "TA0004", "name": "Privilege Escalation", "short_name": "privilege-escalation"},
    {"id": "TA0005", "name": "Defense Evasion", "short_name": "defense-evasion"},
    {"id": "TA0006", "name": "Credential Access", "short_name": "credential-access"},
    {"id": "TA0007", "name": "Discovery", "short_name": "discovery"},
    {"id": "TA0008", "name": "Lateral Movement", "short_name": "lateral-movement"},
    {"id": "TA0009", "name": "Collection", "short_name": "collection"},
    {"id": "TA0011", "name": "Command and Control", "short_name": "command-and-control"},
    {"id": "TA0010", "name": "Exfiltration", "short_name": "exfiltration"},
    {"id": "TA0040", "name": "Impact", "short_name": "impact"},
]

# Phase to tactics mapping
PHASE_TO_TACTICS = {
    "detection": ["initial-access", "execution", "discovery"],
    "analysis": [
        "initial-access", "execution", "persistence", "privilege-escalation",
        "defense-evasion", "credential-access", "discovery", "lateral-movement",
        "collection", "exfiltration"
    ],
    "containment": ["lateral-movement", "command-and-control", "exfiltration"],
    "eradication": ["persistence", "privilege-escalation", "defense-evasion"],
    "recovery": ["impact"],
    "post_incident": ["initial-access", "impact"],
}

# Common ransomware techniques with full details
RANSOMWARE_TECHNIQUES: Dict[str, ATTACKTechnique] = {
    "T1486": ATTACKTechnique(
        technique_id="T1486",
        name="Data Encrypted for Impact",
        description="Adversaries may encrypt data on target systems to interrupt availability.",
        tactics=["impact"],
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["File: File Creation", "File: File Modification", "Process: Process Creation"],
        detection="Monitor for file encryption activity and ransom note creation.",
        url="https://attack.mitre.org/techniques/T1486/",
        mitigations=[
            {"id": "M1053", "name": "Data Backup", "description": "Maintain regular backups of data."},
        ],
    ),
    "T1490": ATTACKTechnique(
        technique_id="T1490",
        name="Inhibit System Recovery",
        description="Adversaries may delete or remove built-in data recovery options.",
        tactics=["impact"],
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["Process: Process Creation", "Command: Command Execution"],
        detection="Monitor for vssadmin, wmic, bcdedit, or wbadmin usage.",
        url="https://attack.mitre.org/techniques/T1490/",
        mitigations=[
            {"id": "M1053", "name": "Data Backup", "description": "Protect backups from tampering."},
        ],
    ),
    "T1059.001": ATTACKTechnique(
        technique_id="T1059.001",
        name="PowerShell",
        description="Adversaries may abuse PowerShell commands and scripts for execution.",
        tactics=["execution"],
        is_subtechnique=True,
        parent_technique="T1059",
        platforms=["Windows"],
        data_sources=["Script: Script Execution", "Process: Process Creation"],
        detection="Monitor PowerShell activity with script block logging enabled.",
        url="https://attack.mitre.org/techniques/T1059/001/",
        mitigations=[
            {"id": "M1042", "name": "Disable or Remove Feature or Program", "description": "Consider disabling PowerShell for users who don't need it."},
        ],
    ),
    "T1059.003": ATTACKTechnique(
        technique_id="T1059.003",
        name="Windows Command Shell",
        description="Adversaries may abuse the Windows command shell for execution.",
        tactics=["execution"],
        is_subtechnique=True,
        parent_technique="T1059",
        platforms=["Windows"],
        data_sources=["Process: Process Creation", "Command: Command Execution"],
        detection="Monitor cmd.exe processes and command line arguments.",
        url="https://attack.mitre.org/techniques/T1059/003/",
    ),
    "T1021.002": ATTACKTechnique(
        technique_id="T1021.002",
        name="SMB/Windows Admin Shares",
        description="Adversaries may use SMB to interact with remote systems.",
        tactics=["lateral-movement"],
        is_subtechnique=True,
        parent_technique="T1021",
        platforms=["Windows"],
        data_sources=["Network Traffic: Network Connection Creation", "Logon Session: Logon Session Creation"],
        detection="Monitor for SMB traffic and admin share access.",
        url="https://attack.mitre.org/techniques/T1021/002/",
    ),
    "T1566": ATTACKTechnique(
        technique_id="T1566",
        name="Phishing",
        description="Adversaries may send phishing messages to gain access to victim systems.",
        tactics=["initial-access"],
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["Application Log: Application Log Content", "Network Traffic: Network Traffic Content"],
        detection="Monitor email for suspicious attachments and links.",
        url="https://attack.mitre.org/techniques/T1566/",
    ),
    "T1078": ATTACKTechnique(
        technique_id="T1078",
        name="Valid Accounts",
        description="Adversaries may obtain and abuse credentials of existing accounts.",
        tactics=["defense-evasion", "persistence", "privilege-escalation", "initial-access"],
        platforms=["Windows", "Linux", "macOS", "Azure AD", "Google Workspace"],
        data_sources=["Logon Session: Logon Session Creation", "User Account: User Account Authentication"],
        detection="Monitor authentication logs for anomalous activity.",
        url="https://attack.mitre.org/techniques/T1078/",
    ),
    "T1003": ATTACKTechnique(
        technique_id="T1003",
        name="OS Credential Dumping",
        description="Adversaries may attempt to dump credentials from the operating system.",
        tactics=["credential-access"],
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["Process: Process Access", "Process: Process Creation"],
        detection="Monitor for LSASS access and credential dumping tools.",
        url="https://attack.mitre.org/techniques/T1003/",
    ),
    "T1082": ATTACKTechnique(
        technique_id="T1082",
        name="System Information Discovery",
        description="An adversary may attempt to get detailed information about the OS and hardware.",
        tactics=["discovery"],
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["Process: Process Creation", "Command: Command Execution"],
        detection="Monitor system information gathering commands.",
        url="https://attack.mitre.org/techniques/T1082/",
    ),
    "T1083": ATTACKTechnique(
        technique_id="T1083",
        name="File and Directory Discovery",
        description="Adversaries may enumerate files and directories.",
        tactics=["discovery"],
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["Process: Process Creation", "Command: Command Execution"],
        detection="Monitor for excessive file system enumeration.",
        url="https://attack.mitre.org/techniques/T1083/",
    ),
    "T1135": ATTACKTechnique(
        technique_id="T1135",
        name="Network Share Discovery",
        description="Adversaries may look for shared folders and drives.",
        tactics=["discovery"],
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["Process: Process Creation", "Command: Command Execution"],
        detection="Monitor for net share or similar commands.",
        url="https://attack.mitre.org/techniques/T1135/",
    ),
    "T1547": ATTACKTechnique(
        technique_id="T1547",
        name="Boot or Logon Autostart Execution",
        description="Adversaries may configure system settings to execute programs during startup.",
        tactics=["persistence", "privilege-escalation"],
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["Windows Registry: Windows Registry Key Modification", "File: File Creation"],
        detection="Monitor startup locations and registry run keys.",
        url="https://attack.mitre.org/techniques/T1547/",
    ),
    "T1562.001": ATTACKTechnique(
        technique_id="T1562.001",
        name="Disable or Modify Tools",
        description="Adversaries may modify or disable security tools.",
        tactics=["defense-evasion"],
        is_subtechnique=True,
        parent_technique="T1562",
        platforms=["Windows", "Linux", "macOS"],
        data_sources=["Process: Process Termination", "Windows Registry: Windows Registry Key Modification"],
        detection="Monitor for security tool processes being terminated.",
        url="https://attack.mitre.org/techniques/T1562/001/",
    ),
}


class MITREIntegration:
    """MITRE ATT&CK Integration Service."""

    def __init__(self):
        """Initialize the MITRE integration."""
        self._techniques = RANSOMWARE_TECHNIQUES.copy()

    def get_all_tactics(self) -> List[Dict[str, str]]:
        """Get all MITRE ATT&CK tactics."""
        return TACTICS

    def get_techniques_for_tactic(self, tactic_short_name: str) -> List[ATTACKTechnique]:
        """Get techniques for a specific tactic."""
        result = []
        for technique in self._techniques.values():
            if tactic_short_name in technique.tactics:
                result.append(technique)
        return result

    def get_all_techniques(self) -> List[ATTACKTechnique]:
        """Get all available techniques."""
        return list(self._techniques.values())

    def get_technique_by_id(self, technique_id: str) -> Optional[ATTACKTechnique]:
        """Get a specific technique by ID."""
        return self._techniques.get(technique_id)

    def get_ransomware_techniques(self) -> List[ATTACKTechnique]:
        """Get techniques commonly used by ransomware."""
        return list(self._techniques.values())

    def get_techniques_for_phase(self, phase: str) -> List[ATTACKTechnique]:
        """Get techniques relevant to an IR phase."""
        tactics = PHASE_TO_TACTICS.get(phase, [])
        result = []
        seen_ids = set()

        for technique in self._techniques.values():
            if technique.technique_id not in seen_ids:
                if any(tactic in technique.tactics for tactic in tactics):
                    result.append(technique)
                    seen_ids.add(technique.technique_id)

        return result

    def generate_navigator_layer(
        self,
        techniques: List[str],
        layer_name: str = "IR Companion Layer",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Generate an ATT&CK Navigator layer JSON.

        Args:
            techniques: List of technique IDs to highlight
            layer_name: Name for the layer
            description: Description for the layer

        Returns:
            Navigator layer JSON structure
        """
        technique_objects = []
        for tech_id in techniques:
            technique_objects.append({
                "techniqueID": tech_id,
                "score": 1,
                "color": "#ff6666",
                "comment": "",
                "enabled": True,
                "metadata": [],
            })

        return {
            "name": layer_name,
            "versions": {
                "attack": "14",
                "navigator": "4.9.1",
                "layer": "4.5",
            },
            "domain": "enterprise-attack",
            "description": description,
            "filters": {
                "platforms": ["Windows", "Linux", "macOS"],
            },
            "sorting": 0,
            "layout": {
                "layout": "side",
                "aggregateFunction": "average",
                "showID": True,
                "showName": True,
                "showAggregateScores": False,
                "countUnscored": False,
            },
            "hideDisabled": False,
            "techniques": technique_objects,
            "gradient": {
                "colors": ["#ffffff", "#ff6666"],
                "minValue": 0,
                "maxValue": 1,
            },
            "legendItems": [],
            "metadata": [],
            "links": [],
            "showTacticRowBackground": False,
            "tacticRowBackground": "#dddddd",
            "selectTechniquesAcrossTactics": True,
            "selectSubtechniquesWithParent": False,
        }


# Singleton instance
_mitre_integration: Optional[MITREIntegration] = None


def get_mitre_integration() -> MITREIntegration:
    """Get the MITRE integration singleton."""
    global _mitre_integration
    if _mitre_integration is None:
        _mitre_integration = MITREIntegration()
    return _mitre_integration
