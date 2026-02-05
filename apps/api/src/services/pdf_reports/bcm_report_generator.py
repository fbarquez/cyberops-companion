"""
BCM (Business Continuity Management) Report Generator.

Generates PDF reports for BCM assessments and emergency plans using ReportLab.
"""
import io
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, ListFlowable, ListItem
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class BCMReportGenerator:
    """
    Generator for BCM reports.

    Creates professional PDF reports including:
    - BCM Assessment reports with maturity scores
    - Emergency Plan documents
    - BIA summaries
    """

    # Criticality colors
    CRITICALITY_COLORS = {
        "critical": colors.HexColor("#DC2626"),  # Red
        "high": colors.HexColor("#F97316"),      # Orange
        "medium": colors.HexColor("#EAB308"),    # Yellow
        "low": colors.HexColor("#22C55E"),       # Green
    }

    # Risk score colors
    RISK_COLORS = {
        "high": colors.HexColor("#DC2626"),      # Red (15-25)
        "medium": colors.HexColor("#F97316"),    # Orange (8-14)
        "low": colors.HexColor("#22C55E"),       # Green (1-7)
    }

    # Plan type colors
    PLAN_TYPE_COLORS = {
        "crisis_management": colors.HexColor("#7C3AED"),
        "emergency_response": colors.HexColor("#DC2626"),
        "business_recovery": colors.HexColor("#3B82F6"),
        "it_disaster_recovery": colors.HexColor("#10B981"),
        "communication": colors.HexColor("#F59E0B"),
        "evacuation": colors.HexColor("#EF4444"),
    }

    def __init__(self, pagesize=A4):
        """Initialize the report generator."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "ReportLab is required for PDF generation. "
                "Install it with: pip install reportlab"
            )
        self.pagesize = pagesize
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor("#374151"),
            spaceBefore=20,
            spaceAfter=10,
        ))

        # Subsection style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor("#4B5563"),
            spaceBefore=15,
            spaceAfter=8,
        ))

        # Body text style
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#374151"),
            spaceAfter=8,
            leading=14,
        ))

        # Small text style
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor("#6B7280"),
        ))

        # Score style
        self.styles.add(ParagraphStyle(
            name='ScoreText',
            parent=self.styles['Normal'],
            fontSize=36,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_CENTER,
        ))

    def _get_score_color(self, score: float) -> colors.Color:
        """Get color based on score value."""
        if score >= 80:
            return colors.HexColor("#22C55E")  # Green
        elif score >= 60:
            return colors.HexColor("#EAB308")  # Yellow
        elif score >= 40:
            return colors.HexColor("#F97316")  # Orange
        else:
            return colors.HexColor("#EF4444")  # Red

    def _get_risk_color(self, score: int) -> colors.Color:
        """Get color based on risk score."""
        if score >= 15:
            return self.RISK_COLORS["high"]
        elif score >= 8:
            return self.RISK_COLORS["medium"]
        else:
            return self.RISK_COLORS["low"]

    def _create_header(self, title: str, subtitle: str = None) -> List:
        """Create report header elements."""
        elements = []

        # Title
        elements.append(Paragraph(title, self.styles['ReportTitle']))

        if subtitle:
            subtitle_style = ParagraphStyle(
                name='Subtitle',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor("#6B7280"),
                alignment=TA_CENTER,
                spaceAfter=20,
            )
            elements.append(Paragraph(subtitle, subtitle_style))

        # Date
        date_text = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        elements.append(Paragraph(date_text, self.styles['SmallText']))
        elements.append(Spacer(1, 30))

        return elements

    def _create_score_box(self, score: float, label: str) -> Table:
        """Create a score display box."""
        score_color = self._get_score_color(score)
        score_text = f"{score:.0f}%"

        data = [
            [Paragraph(score_text, self.styles['ScoreText'])],
            [Paragraph(label, self.styles['SmallText'])],
        ]

        table = Table(data, colWidths=[2*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 2, score_color),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#F9FAFB")),
        ]))

        return table

    def _create_simple_table(self, data: List[List], col_widths: List = None, header: bool = True) -> Table:
        """Create a simple styled table."""
        table = Table(data, colWidths=col_widths)

        style_commands = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]

        if header and len(data) > 0:
            style_commands.extend([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ])

        table.setStyle(TableStyle(style_commands))
        return table

    def generate_assessment_report(
        self,
        assessment,
        processes: List,
        bia_summary: Dict,
        scenarios: List,
        plans: List,
        exercises: List,
    ) -> bytes:
        """Generate a comprehensive BCM assessment report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        elements = []

        # Header
        elements.extend(self._create_header(
            "Business Continuity Management Report",
            f"Assessment: {assessment.name}"
        ))

        # Executive Summary
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))

        # Score boxes
        score_data = []
        if assessment.overall_score is not None:
            score_data.append(self._create_score_box(assessment.overall_score, "Overall BCM Maturity"))

        if score_data:
            score_table = Table([score_data])
            elements.append(score_table)
            elements.append(Spacer(1, 20))

        # Key metrics
        metrics_data = [
            ["Metric", "Value"],
            ["Total Business Processes", str(assessment.total_processes)],
            ["Critical Processes", str(assessment.critical_processes)],
            ["Processes with BIA", str(assessment.processes_with_bia)],
            ["Processes with Strategy", str(assessment.processes_with_strategy)],
            ["Active Emergency Plans", str(len([p for p in plans if hasattr(p, 'status') and str(p.status) == 'active']))],
            ["Plans Tested This Year", str(assessment.plans_tested_this_year)],
        ]
        elements.append(self._create_simple_table(metrics_data, col_widths=[3*inch, 2*inch]))
        elements.append(Spacer(1, 20))

        # Score breakdown
        elements.append(Paragraph("Maturity Score Breakdown", self.styles['SubsectionHeader']))
        score_breakdown = [
            ["Category", "Score", "Weight"],
            ["Process Coverage", f"{assessment.process_coverage_score or 0:.0f}%", "15%"],
            ["BIA Completion", f"{assessment.bia_completion_score or 0:.0f}%", "25%"],
            ["Strategy Coverage", f"{assessment.strategy_coverage_score or 0:.0f}%", "20%"],
            ["Plan Coverage", f"{assessment.plan_coverage_score or 0:.0f}%", "25%"],
            ["Test Coverage", f"{assessment.test_coverage_score or 0:.0f}%", "15%"],
        ]
        elements.append(self._create_simple_table(score_breakdown, col_widths=[3*inch, 1.5*inch, 1*inch]))

        elements.append(PageBreak())

        # Business Processes Section
        elements.append(Paragraph("Business Processes", self.styles['SectionHeader']))

        if processes:
            process_data = [["ID", "Name", "Criticality", "Owner", "Status"]]
            for p in processes:
                process_data.append([
                    p.process_id,
                    p.name[:30] + "..." if len(p.name) > 30 else p.name,
                    str(p.criticality.value).title() if hasattr(p.criticality, 'value') else str(p.criticality).title(),
                    p.owner[:20] + "..." if len(p.owner) > 20 else p.owner,
                    str(p.status.value).replace("_", " ").title() if hasattr(p.status, 'value') else str(p.status),
                ])
            elements.append(self._create_simple_table(process_data, col_widths=[0.8*inch, 2*inch, 1*inch, 1.5*inch, 1*inch]))
        else:
            elements.append(Paragraph("No processes documented.", self.styles['BodyText']))

        elements.append(Spacer(1, 20))

        # BIA Summary
        elements.append(Paragraph("Business Impact Analysis Summary", self.styles['SubsectionHeader']))
        bia_data = [
            ["Metric", "Value"],
            ["Processes with BIA", f"{bia_summary.get('processes_with_bia', 0)} / {bia_summary.get('total_processes', 0)}"],
            ["BIA Completion", f"{bia_summary.get('bia_completion_percentage', 0):.0f}%"],
            ["Average RTO", f"{bia_summary.get('average_rto_hours', 'N/A')} hours" if bia_summary.get('average_rto_hours') else "N/A"],
            ["Average RPO", f"{bia_summary.get('average_rpo_hours', 'N/A')} hours" if bia_summary.get('average_rpo_hours') else "N/A"],
        ]
        elements.append(self._create_simple_table(bia_data, col_widths=[3*inch, 2*inch]))

        elements.append(PageBreak())

        # Risk Scenarios Section
        elements.append(Paragraph("Risk Scenarios", self.styles['SectionHeader']))

        if scenarios:
            scenario_data = [["ID", "Name", "Category", "Likelihood", "Impact", "Risk"]]
            for s in scenarios:
                scenario_data.append([
                    s.scenario_id,
                    s.name[:25] + "..." if len(s.name) > 25 else s.name,
                    str(s.category.value).replace("_", " ").title() if hasattr(s.category, 'value') else str(s.category),
                    str(s.likelihood.value).title() if hasattr(s.likelihood, 'value') else str(s.likelihood),
                    str(s.impact.value).title() if hasattr(s.impact, 'value') else str(s.impact),
                    str(s.risk_score),
                ])
            elements.append(self._create_simple_table(scenario_data, col_widths=[0.7*inch, 1.8*inch, 1.2*inch, 0.9*inch, 0.9*inch, 0.5*inch]))
        else:
            elements.append(Paragraph("No risk scenarios documented.", self.styles['BodyText']))

        elements.append(Spacer(1, 20))

        # Emergency Plans Section
        elements.append(Paragraph("Emergency Plans", self.styles['SectionHeader']))

        if plans:
            plan_data = [["ID", "Name", "Type", "Status", "Version"]]
            for p in plans:
                plan_data.append([
                    p.plan_id,
                    p.name[:30] + "..." if len(p.name) > 30 else p.name,
                    str(p.plan_type.value).replace("_", " ").title() if hasattr(p.plan_type, 'value') else str(p.plan_type),
                    str(p.status.value).title() if hasattr(p.status, 'value') else str(p.status),
                    p.version,
                ])
            elements.append(self._create_simple_table(plan_data, col_widths=[0.8*inch, 2.2*inch, 1.5*inch, 0.8*inch, 0.7*inch]))
        else:
            elements.append(Paragraph("No emergency plans documented.", self.styles['BodyText']))

        elements.append(PageBreak())

        # Exercises Section
        elements.append(Paragraph("BC Exercises", self.styles['SectionHeader']))

        if exercises:
            exercise_data = [["ID", "Name", "Type", "Date", "Status"]]
            for e in exercises:
                date_str = str(e.actual_date or e.planned_date) if hasattr(e, 'actual_date') else str(e.planned_date)
                exercise_data.append([
                    e.exercise_id,
                    e.name[:30] + "..." if len(e.name) > 30 else e.name,
                    str(e.exercise_type.value).replace("_", " ").title() if hasattr(e.exercise_type, 'value') else str(e.exercise_type),
                    date_str,
                    str(e.status.value).replace("_", " ").title() if hasattr(e.status, 'value') else str(e.status),
                ])
            elements.append(self._create_simple_table(exercise_data, col_widths=[0.9*inch, 2*inch, 1.2*inch, 1*inch, 1*inch]))
        else:
            elements.append(Paragraph("No exercises documented.", self.styles['BodyText']))

        # Footer
        elements.append(Spacer(1, 40))
        elements.append(Paragraph(
            "This report was generated by CyberOps Companion BCM Module.",
            self.styles['SmallText']
        ))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def generate_plan_pdf(self, plan) -> bytes:
        """Generate a PDF document for an emergency plan."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        elements = []

        # Header
        elements.extend(self._create_header(
            plan.name,
            f"Plan ID: {plan.plan_id} | Version: {plan.version}"
        ))

        # Plan Overview
        elements.append(Paragraph("Plan Overview", self.styles['SectionHeader']))

        overview_data = [
            ["Field", "Value"],
            ["Plan Type", str(plan.plan_type.value).replace("_", " ").title() if hasattr(plan.plan_type, 'value') else str(plan.plan_type)],
            ["Status", str(plan.status.value).title() if hasattr(plan.status, 'value') else str(plan.status)],
            ["Effective Date", str(plan.effective_date)],
            ["Review Date", str(plan.review_date)],
        ]
        if plan.approved_by:
            overview_data.append(["Approved By", plan.approved_by])
        if plan.approved_at:
            overview_data.append(["Approved At", str(plan.approved_at)])

        elements.append(self._create_simple_table(overview_data, col_widths=[2*inch, 4*inch]))
        elements.append(Spacer(1, 15))

        # Scope
        elements.append(Paragraph("Scope", self.styles['SubsectionHeader']))
        elements.append(Paragraph(plan.scope_description, self.styles['BodyText']))
        elements.append(Spacer(1, 15))

        # Response Phases
        if plan.response_phases:
            elements.append(Paragraph("Response Phases", self.styles['SectionHeader']))
            for phase in plan.response_phases:
                phase_title = f"{phase.get('phase', 'Phase')} ({phase.get('duration', '')})"
                elements.append(Paragraph(phase_title, self.styles['SubsectionHeader']))
                if phase.get('description'):
                    elements.append(Paragraph(phase['description'], self.styles['BodyText']))
                if phase.get('activities'):
                    items = [ListItem(Paragraph(a, self.styles['BodyText'])) for a in phase['activities']]
                    elements.append(ListFlowable(items, bulletType='bullet', start='circle'))
                elements.append(Spacer(1, 10))

        elements.append(PageBreak())

        # Roles and Responsibilities
        if plan.roles_responsibilities:
            elements.append(Paragraph("Roles and Responsibilities", self.styles['SectionHeader']))
            for role in plan.roles_responsibilities:
                elements.append(Paragraph(role.get('role', 'Role'), self.styles['SubsectionHeader']))
                if role.get('responsibilities'):
                    items = [ListItem(Paragraph(r, self.styles['BodyText'])) for r in role['responsibilities']]
                    elements.append(ListFlowable(items, bulletType='bullet', start='circle'))
                elements.append(Spacer(1, 10))

        # Activation Checklist
        if plan.activation_checklist:
            elements.append(Paragraph("Activation Checklist", self.styles['SectionHeader']))
            checklist_data = [["Item", "Required"]]
            for item in plan.activation_checklist:
                checklist_data.append([
                    item.get('item', ''),
                    "Yes" if item.get('required') else "No"
                ])
            elements.append(self._create_simple_table(checklist_data, col_widths=[5*inch, 1*inch]))
            elements.append(Spacer(1, 15))

        # Recovery Checklist
        if plan.recovery_checklist:
            elements.append(Paragraph("Recovery Checklist", self.styles['SectionHeader']))
            checklist_data = [["Item", "Required"]]
            for item in plan.recovery_checklist:
                checklist_data.append([
                    item.get('item', ''),
                    "Yes" if item.get('required') else "No"
                ])
            elements.append(self._create_simple_table(checklist_data, col_widths=[5*inch, 1*inch]))

        # Footer
        elements.append(Spacer(1, 40))
        elements.append(Paragraph(
            f"Document generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            self.styles['SmallText']
        ))
        elements.append(Paragraph(
            "CyberOps Companion - Business Continuity Management",
            self.styles['SmallText']
        ))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
