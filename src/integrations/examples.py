"""
Compliance Hub - Usage Examples

This module demonstrates how to use the Compliance Hub integrations
in your IR Companion application.

Run with: python -m src.integrations.examples
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timezone
from typing import Dict, List, Any

from src.integrations import (
    ComplianceHub,
    ComplianceFramework,
    BSIIntegration,
    NISTOSCALIntegration,
    NVDIntegration,
    MITREATTACKIntegration,
    ISOComplianceMapper,
)


def example_basic_compliance_check():
    """
    Example: Basic compliance validation for a single phase.
    """
    print("\n" + "="*60)
    print("Example 1: Basic Compliance Check")
    print("="*60)

    # Initialize the Compliance Hub
    hub = ComplianceHub(offline_mode=True)  # Use cached data only

    # Simulate incident data for the analysis phase
    incident_data = {
        "completed_actions": [
            "ANA-001",  # Memory capture
            "ANA-002",  # Ransomware variant identification
            "ANA-003",  # Document ransom note
        ],
        "evidence_collected": [
            "Memory dump captured from affected system",
            "Ransomware identified as LockBit 3.0",
            "Ransom note screenshot collected",
            "Encrypted file extensions documented: .locked",
        ],
        "documentation_provided": [
            "Incident report form completed",
            "Scope assessment document",
        ],
    }

    # Validate compliance against multiple frameworks
    results = hub.validate_phase_compliance(
        phase="analysis",
        incident_data=incident_data,
        frameworks=[
            ComplianceFramework.BSI_GRUNDSCHUTZ,
            ComplianceFramework.NIST_CSF_2,
            ComplianceFramework.ISO_27001,
        ],
        operator="Security Analyst",
    )

    # Print results
    for framework, checks in results.items():
        print(f"\n--- {framework.upper()} ---")
        for check in checks:
            status_icon = "✅" if check.status.value == "compliant" else "⚠️" if check.status.value == "partial" else "❌"
            print(f"  {status_icon} {check.control_id}: {check.control_name}")
            if check.recommendation:
                print(f"      → {check.recommendation}")


def example_threat_intelligence():
    """
    Example: Threat intelligence enrichment for an incident.
    """
    print("\n" + "="*60)
    print("Example 2: Threat Intelligence Enrichment")
    print("="*60)

    hub = ComplianceHub(offline_mode=True)

    # Preload MITRE ATT&CK data
    print("\nLoading MITRE ATT&CK data...")
    hub.mitre.load_attack_data()

    # Define IOCs from the incident
    iocs = [
        {"type": "process", "value": "powershell.exe -enc base64string"},
        {"type": "process", "value": "vssadmin delete shadows /all"},
        {"type": "file_path", "value": "C:\\Users\\Public\\malware.locked"},
        {"type": "registry", "value": "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"},
        {"type": "ip", "value": "192.168.1.100"},
    ]

    # Generate threat intelligence
    intel = hub.enrich_with_threat_intelligence(
        incident_id="INC-2024-TEST001",
        iocs=iocs,
        ransomware_family="LockBit",
    )

    print(f"\nIncident: {intel.incident_id}")
    print(f"Ransomware Family: {intel.ransomware_family}")
    print(f"\nMapped ATT&CK Techniques ({len(intel.mapped_techniques)}):")

    for tech in intel.mapped_techniques[:10]:
        print(f"  - {tech.technique_id}: {tech.name}")
        if tech.tactics:
            print(f"    Tactics: {', '.join(tech.tactics[:3])}")
        if tech.relevance_indicators:
            print(f"    Matched IOCs: {len(tech.relevance_indicators)}")

    print(f"\nPrimary Tactics: {', '.join(intel.primary_tactics[:5])}")

    if intel.detection_recommendations:
        print(f"\nDetection Recommendations:")
        for rec in intel.detection_recommendations[:3]:
            print(f"  - {rec}")

    if intel.mitigation_recommendations:
        print(f"\nMitigation Recommendations:")
        for rec in intel.mitigation_recommendations[:3]:
            print(f"  - {rec}")


def example_ransomware_techniques():
    """
    Example: Get ransomware-specific ATT&CK techniques.
    """
    print("\n" + "="*60)
    print("Example 3: Ransomware ATT&CK Techniques")
    print("="*60)

    mitre = MITREATTACKIntegration(offline_mode=True)
    mitre.load_attack_data()

    techniques = mitre.get_ransomware_techniques()

    print(f"\nRansomware-related ATT&CK Techniques ({len(techniques)}):")
    print("-" * 60)

    # Group by tactic
    by_tactic: Dict[str, List] = {}
    for tech in techniques:
        for tactic in tech.tactics:
            if tactic not in by_tactic:
                by_tactic[tactic] = []
            by_tactic[tactic].append(tech)

    for tactic, techs in sorted(by_tactic.items()):
        print(f"\n{tactic.upper()}:")
        for tech in techs[:5]:
            print(f"  [{tech.technique_id}] {tech.name}")
            if tech.mitigations:
                print(f"    Mitigations: {len(tech.mitigations)}")


def example_bsi_compliance():
    """
    Example: BSI IT-Grundschutz compliance checking.
    """
    print("\n" + "="*60)
    print("Example 4: BSI IT-Grundschutz Compliance")
    print("="*60)

    bsi = BSIIntegration(offline_mode=True)

    phases = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]

    print("\nBSI IT-Grundschutz Control Mapping by Phase:")
    print("-" * 60)

    for phase in phases:
        mapping = bsi.get_phase_mapping(phase)
        print(f"\n{phase.upper()}:")
        print(f"  Controls: {', '.join(mapping.controls[:5])}")
        print(f"  Mandatory: {', '.join(mapping.mandatory_controls)}")

    # Get Grundschutz++ info
    print("\n\nGrundschutz++ (2026) Information:")
    print("-" * 40)
    info = bsi.get_grundschutz_plus_info()
    print(f"  Effective: {info['effective_date']}")
    print(f"  Format: {info['format']}")
    print(f"  Repository: {info['repository']}")


def example_iso_compliance():
    """
    Example: ISO 27001/27035 compliance mapping.
    """
    print("\n" + "="*60)
    print("Example 5: ISO 27001/27035 Compliance")
    print("="*60)

    iso = ISOComplianceMapper()

    phase = "analysis"
    requirements = iso.get_compliance_requirements(phase)

    print(f"\nCompliance Requirements for '{phase}' Phase:")
    print("-" * 50)

    print("\nISO 27001:2022 Controls:")
    for ctrl in requirements["iso_27001_controls"]:
        mandatory = "[MANDATORY]" if ctrl in requirements["iso_27001_mandatory"] else ""
        print(f"  - {ctrl} {mandatory}")

    print("\nISO 27035 Requirements:")
    for req in requirements["iso_27035_requirements"]:
        print(f"  - {req}")

    print("\nDocumentation Required:")
    for doc in requirements["documentation_required"]:
        print(f"  - {doc}")


def example_compliance_report():
    """
    Example: Generate a full compliance report.
    """
    print("\n" + "="*60)
    print("Example 6: Generate Compliance Report")
    print("="*60)

    hub = ComplianceHub(offline_mode=True)

    # Simulate multi-phase incident data
    incident_phases = {
        "detection": {
            "completed_actions": ["DET-001", "DET-002", "DET-003", "DET-004"],
            "evidence_collected": ["Alert received", "System identified", "Initial triage completed"],
            "documentation_provided": ["Incident report form"],
        },
        "analysis": {
            "completed_actions": ["ANA-001", "ANA-002", "ANA-003"],
            "evidence_collected": ["Memory captured", "Ransomware identified", "IOCs documented"],
            "documentation_provided": ["Scope assessment"],
        },
    }

    # Validate all phases
    all_results = hub.validate_all_phases(
        incident_data=incident_phases,
        frameworks=[ComplianceFramework.BSI_GRUNDSCHUTZ, ComplianceFramework.ISO_27001],
        operator="Security Analyst",
    )

    # Generate report
    report = hub.generate_compliance_report(
        incident_id="INC-2024-EXAMPLE",
        phase_results=all_results,
        operator="Security Analyst",
    )

    print(f"\nCompliance Report Summary:")
    print("-" * 40)
    print(f"  Incident: {report.incident_id}")
    print(f"  Total Controls: {report.total_controls}")
    print(f"  Compliant: {report.compliant_count}")
    print(f"  Partial: {report.partial_count}")
    print(f"  Gaps: {report.gap_count}")
    print(f"  Compliance Score: {report.compliance_score:.1f}%")

    if report.critical_gaps:
        print(f"\nCritical Gaps ({len(report.critical_gaps)}):")
        for gap in report.critical_gaps[:3]:
            print(f"  - {gap.control_id}: {gap.control_name}")

    # Export to markdown
    print("\n--- Markdown Export (truncated) ---")
    markdown = hub.export_compliance_report(report, format="markdown", include_details=False)
    print(markdown[:500] + "...")


def example_nvd_cve_search():
    """
    Example: Search NVD for CVEs (requires network).
    """
    print("\n" + "="*60)
    print("Example 7: NVD CVE Search (requires network)")
    print("="*60)

    nvd = NVDIntegration()

    print("\nSearching for ransomware-related CVEs...")
    print("(Note: This requires network access and may be rate-limited)")

    try:
        cves, total = nvd.search_cves(
            keyword="ransomware",
            cvss_v3_severity="CRITICAL",
            results_per_page=5,
        )

        print(f"\nFound {total} total CVEs, showing top 5:")
        print("-" * 50)

        for cve in cves:
            print(f"\n{cve.cve_id}")
            print(f"  Severity: {cve.cvss_v3.severity if cve.cvss_v3 else 'N/A'}")
            print(f"  CISA KEV: {'Yes' if cve.cisa_kev else 'No'}")
            print(f"  Description: {cve.description[:100]}...")

    except Exception as e:
        print(f"  Error: {e}")
        print("  (This is expected if running offline or rate-limited)")


def example_integration_with_ir_companion():
    """
    Example: Integration with IR Companion's existing workflow.
    """
    print("\n" + "="*60)
    print("Example 8: Integration with IR Companion Workflow")
    print("="*60)

    print("""
This example shows how to integrate the Compliance Hub with
IR Companion's existing incident workflow.

Code snippet for app.py or workflow.py:

```python
from src.integrations import ComplianceHub, ComplianceFramework

# Initialize hub (typically once at app startup)
compliance_hub = ComplianceHub(
    config={"nvd_api_key": os.getenv("NVD_API_KEY")},
    offline_mode=False,
)

# Preload data for faster access
compliance_hub.preload_data()

# When checking phase compliance:
def check_phase_compliance(incident, checklist, evidence_logger):
    # Gather data from existing IR Companion models
    completed_actions = [
        item.id for item in checklist.items
        if item.status == "completed"
    ]
    evidence_entries = evidence_logger.get_entries(incident.id)
    evidence_descriptions = [e.description for e in evidence_entries]

    # Validate compliance
    results = compliance_hub.validate_phase_compliance(
        phase=incident.current_phase,
        incident_data={
            "completed_actions": completed_actions,
            "evidence_collected": evidence_descriptions,
        },
        frameworks=[
            ComplianceFramework.BSI_GRUNDSCHUTZ,
            ComplianceFramework.NIST_CSF_2,
            ComplianceFramework.ISO_27001,
        ],
        operator=incident.analyst_name,
    )

    return results

# When enriching with threat intelligence:
def enrich_incident(incident, iocs):
    intel = compliance_hub.enrich_with_threat_intelligence(
        incident_id=incident.id,
        iocs=iocs,
        affected_software=[s.hostname for s in incident.affected_systems],
    )
    return intel
```
    """)


def main():
    """Run all examples."""
    print("\n" + "#"*60)
    print("# IR Companion - Compliance Hub Examples")
    print("#"*60)

    # Run examples that work offline
    example_basic_compliance_check()
    example_bsi_compliance()
    example_iso_compliance()

    # These require MITRE data (will download if not cached)
    try:
        example_threat_intelligence()
        example_ransomware_techniques()
    except Exception as e:
        print(f"\nSkipping MITRE examples (data not available): {e}")

    example_compliance_report()
    example_integration_with_ir_companion()

    # Optionally run NVD example (requires network)
    # example_nvd_cve_search()

    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
