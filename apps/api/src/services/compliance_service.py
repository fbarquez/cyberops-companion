"""
Compliance Service - Business logic for compliance operations.

This service wraps the ComplianceHub and provides methods for:
- Validating compliance for incidents
- Generating compliance reports
- Cross-framework mapping
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.compliance_hub import ComplianceHub
from src.integrations.models import (
    FrameworkInfo,
    ComplianceValidationResult,
    ComplianceReport,
    CrossFrameworkMapping,
)

logger = logging.getLogger(__name__)


class ComplianceService:
    """
    Service for compliance-related operations.

    Provides high-level methods for:
    - Framework information retrieval
    - Phase compliance validation
    - Compliance report generation
    - Cross-framework mapping
    """

    _instance: Optional["ComplianceService"] = None
    _hub: Optional[ComplianceHub] = None

    @classmethod
    def get_instance(cls) -> "ComplianceService":
        """Get singleton instance of ComplianceService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the compliance service.

        Args:
            cache_dir: Optional cache directory for compliance data
        """
        if self._hub is None:
            self._hub = ComplianceHub(cache_dir=cache_dir, offline_mode=False)

    @property
    def hub(self) -> ComplianceHub:
        """Get the compliance hub instance."""
        if self._hub is None:
            self._hub = ComplianceHub()
        return self._hub

    async def get_frameworks(self) -> List[FrameworkInfo]:
        """
        Get all available compliance frameworks.

        Returns:
            List of FrameworkInfo objects
        """
        return self.hub.get_frameworks()

    async def get_framework(self, framework_id: str) -> Optional[FrameworkInfo]:
        """
        Get a specific framework by ID.

        Args:
            framework_id: Framework identifier

        Returns:
            FrameworkInfo or None if not found
        """
        return self.hub.get_framework(framework_id)

    async def validate_phase_compliance(
        self,
        db: AsyncSession,
        incident_id: str,
        phase: str,
        frameworks: List[str],
        operator: str = "",
    ) -> Dict[str, ComplianceValidationResult]:
        """
        Validate compliance for an incident phase.

        Args:
            db: Database session
            incident_id: Incident identifier
            phase: IR phase name
            frameworks: List of framework IDs to validate
            operator: Operator performing validation

        Returns:
            Dictionary mapping framework ID to validation result
        """
        # Fetch incident data from database
        incident_data = await self._get_incident_data(db, incident_id, phase)

        # Validate against frameworks
        results = self.hub.validate_phase_compliance(
            phase=phase,
            incident_data=incident_data,
            frameworks=frameworks,
            operator=operator,
        )

        return results

    async def validate_incident_compliance(
        self,
        db: AsyncSession,
        incident_id: str,
        frameworks: List[str],
        operator: str = "",
    ) -> Dict[str, Dict[str, ComplianceValidationResult]]:
        """
        Validate compliance for all phases of an incident.

        Args:
            db: Database session
            incident_id: Incident identifier
            frameworks: List of framework IDs to validate
            operator: Operator performing validation

        Returns:
            Nested dictionary: phase -> framework -> result
        """
        phases = ["detection", "analysis", "containment", "eradication", "recovery", "post_incident"]
        all_results = {}

        for phase in phases:
            incident_data = await self._get_incident_data(db, incident_id, phase)
            if incident_data.get("completed_actions") or incident_data.get("evidence_collected"):
                all_results[phase] = self.hub.validate_phase_compliance(
                    phase=phase,
                    incident_data=incident_data,
                    frameworks=frameworks,
                    operator=operator,
                )

        return all_results

    async def generate_compliance_report(
        self,
        db: AsyncSession,
        incident_id: str,
        frameworks: List[str],
        operator: str = "",
    ) -> ComplianceReport:
        """
        Generate a comprehensive compliance report for an incident.

        Args:
            db: Database session
            incident_id: Incident identifier
            frameworks: List of framework IDs to include
            operator: Operator generating the report

        Returns:
            ComplianceReport object
        """
        # Get validation results for all phases
        phase_results = await self.validate_incident_compliance(
            db=db,
            incident_id=incident_id,
            frameworks=frameworks,
            operator=operator,
        )

        # Generate report
        report = self.hub.generate_compliance_report(
            incident_id=incident_id,
            phase_results=phase_results,
            operator=operator,
        )

        return report

    async def export_compliance_report(
        self,
        db: AsyncSession,
        incident_id: str,
        frameworks: List[str],
        format: str = "markdown",
        operator: str = "",
    ) -> str:
        """
        Export compliance report in specified format.

        Args:
            db: Database session
            incident_id: Incident identifier
            frameworks: List of framework IDs to include
            format: Output format (markdown, json)
            operator: Operator generating the report

        Returns:
            Formatted report string
        """
        report = await self.generate_compliance_report(
            db=db,
            incident_id=incident_id,
            frameworks=frameworks,
            operator=operator,
        )

        return self.hub.export_compliance_report(
            report=report,
            format=format,
            include_details=True,
        )

    async def get_cross_framework_mapping(
        self,
        phase: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get cross-framework control mapping.

        Args:
            phase: Optional IR phase to filter controls

        Returns:
            Cross-framework mapping data
        """
        return self.hub.get_cross_framework_mapping(phase=phase)

    async def find_equivalent_controls(
        self,
        control_id: str,
        framework: str,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Find equivalent controls in other frameworks.

        Args:
            control_id: Source control ID
            framework: Source framework name

        Returns:
            Dictionary mapping framework names to equivalent controls
        """
        return self.hub.find_equivalent_controls(control_id, framework)

    async def get_control_details(
        self,
        control_id: str,
        framework: str,
    ) -> Dict[str, Any]:
        """
        Get detailed information about a control.

        Args:
            control_id: Control ID
            framework: Framework name

        Returns:
            Control details with cross-references
        """
        return self.hub.get_control_details(control_id, framework)

    async def calculate_coverage(
        self,
        db: AsyncSession,
        incident_id: str,
    ) -> Dict[str, Any]:
        """
        Calculate compliance coverage for an incident.

        Args:
            db: Database session
            incident_id: Incident identifier

        Returns:
            Coverage statistics
        """
        # Get completed controls from incident data
        completed_controls = await self._get_completed_controls(db, incident_id)

        return self.hub.calculate_unified_coverage(completed_controls)

    async def _get_incident_data(
        self,
        db: AsyncSession,
        incident_id: str,
        phase: str,
    ) -> Dict[str, Any]:
        """
        Get incident data for compliance validation.

        Args:
            db: Database session
            incident_id: Incident identifier
            phase: IR phase name

        Returns:
            Dictionary with completed_actions, evidence_collected, documentation_provided
        """
        # Import here to avoid circular imports
        from src.models.incident import Incident
        from src.models.evidence import EvidenceEntry
        from src.models.checklist import ChecklistItem, ChecklistStatus

        # Get completed checklist items for the phase
        completed_actions = []
        try:
            from sqlalchemy import select

            result = await db.execute(
                select(ChecklistItem)
                .where(ChecklistItem.incident_id == incident_id)
                .where(ChecklistItem.phase == phase)
                .where(ChecklistItem.status == ChecklistStatus.COMPLETED)
            )
            progress_items = result.scalars().all()
            completed_actions = [p.item_id for p in progress_items]
        except Exception as e:
            logger.warning(f"Could not fetch checklist progress: {e}")

        # Get evidence entries for the phase
        evidence_collected = []
        try:
            from sqlalchemy import select
            
            result = await db.execute(
                select(EvidenceEntry)
                .where(EvidenceEntry.incident_id == incident_id)
                .where(EvidenceEntry.phase == phase)
            )
            evidence_items = result.scalars().all()
            evidence_collected = [e.description for e in evidence_items if e.description]
        except Exception as e:
            logger.warning(f"Could not fetch evidence: {e}")

        return {
            "completed_actions": completed_actions,
            "evidence_collected": evidence_collected,
            "documentation_provided": evidence_collected,  # Use evidence as documentation for now
        }

    async def _get_completed_controls(
        self,
        db: AsyncSession,
        incident_id: str,
    ) -> Dict[str, List[str]]:
        """
        Get completed controls for an incident grouped by framework.

        This maps completed checklist items to framework controls.

        Args:
            db: Database session
            incident_id: Incident identifier

        Returns:
            Dictionary mapping framework ID to list of completed control IDs
        """
        # For now, return empty - this would need mapping logic
        # from checklist items to framework controls
        return {}


# Dependency injection helper
def get_compliance_service() -> ComplianceService:
    """Get compliance service instance for dependency injection."""
    return ComplianceService.get_instance()
