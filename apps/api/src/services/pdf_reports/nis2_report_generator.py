"""
NIS2 Directive Compliance Report Generator.

Generates PDF reports for NIS2 compliance assessments using ReportLab.
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
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# NIS2 Article names
NIS2_ARTICLES = {
    "article_21": "Cybersecurity Risk-Management Measures",
    "article_23": "Reporting Obligations",
    "article_24": "Use of Certification Schemes",
    "article_25": "Standardisation",
    "article_26": "Technical Assistance",
    "article_27": "Voluntary Cybersecurity Information Sharing",
}

# Sector classifications
SECTOR_NAMES = {
    "energy": "Energy",
    "transport": "Transport",
    "banking": "Banking",
    "financial_market": "Financial Market Infrastructure",
    "health": "Health",
    "drinking_water": "Drinking Water",
    "waste_water": "Waste Water",
    "digital_infrastructure": "Digital Infrastructure",
    "ict_service_management": "ICT Service Management",
    "public_administration": "Public Administration",
    "space": "Space",
    "postal": "Postal and Courier Services",
    "waste_management": "Waste Management",
    "manufacturing": "Manufacturing",
    "food": "Food Production and Distribution",
    "chemicals": "Chemicals",
    "research": "Research",
    "digital_providers": "Digital Providers",
}

# Entity types
ENTITY_TYPES = {
    "essential": "Essential Entity",
    "important": "Important Entity",
    "not_applicable": "Not Subject to NIS2",
}


class NIS2ReportGenerator:
    """
    Generator for NIS2 Directive compliance reports.

    Creates professional PDF reports including:
    - Executive summary with compliance scores
    - Entity classification and sector analysis
    - Security measures assessment
    - Gap analysis with remediation plans
    - Regulatory requirements mapping
    """

    STATUS_COLORS = {
        "compliant": colors.HexColor("#22C55E"),
        "partial": colors.HexColor("#EAB308"),
        "gap": colors.HexColor("#EF4444"),
        "not_evaluated": colors.HexColor("#9CA3AF"),
        "not_applicable": colors.HexColor("#6B7280"),
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

        # Body text
        self.styles['BodyText'].fontSize = 10
        self.styles['BodyText'].textColor = colors.HexColor("#374151")
        self.styles['BodyText'].alignment = TA_JUSTIFY
        self.styles['BodyText'].spaceAfter = 8

    def generate_report(
        self,
        assessment: Dict[str, Any],
        classification: Dict[str, Any],
        measures: List[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
        recommendations: List[str],
        language: str = "en",
    ) -> bytes:
        """
        Generate a complete NIS2 compliance report.

        Args:
            assessment: Assessment data including scores
            classification: Entity classification data
            measures: Security measures assessment results
            gaps: Gap analysis results
            recommendations: List of recommendations
            language: Report language (en, de, es)

        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        story = []

        # Title page
        story.extend(self._create_title_page(assessment, classification))
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary(assessment, classification))
        story.append(PageBreak())

        # Entity classification
        story.extend(self._create_classification_section(classification))
        story.append(PageBreak())

        # Security measures assessment
        if measures:
            story.extend(self._create_measures_section(measures))
            story.append(PageBreak())

        # Gap analysis
        if gaps:
            story.extend(self._create_gap_section(gaps))
            story.append(PageBreak())

        # Recommendations
        if recommendations:
            story.extend(self._create_recommendations_section(recommendations))

        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)

        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    def _create_title_page(self, assessment: Dict[str, Any], classification: Dict[str, Any]) -> List:
        """Create the title page."""
        elements = []

        # Add spacing
        elements.append(Spacer(1, 2 * inch))

        # Title
        elements.append(Paragraph(
            "NIS2 Directive",
            self.styles['ReportTitle']
        ))
        elements.append(Paragraph(
            "Compliance Assessment Report",
            self.styles['SectionHeader']
        ))

        elements.append(Spacer(1, 0.5 * inch))

        # Assessment name
        elements.append(Paragraph(
            assessment.get('name', 'Untitled Assessment'),
            self.styles['SubsectionHeader']
        ))

        elements.append(Spacer(1, 1.5 * inch))

        # Assessment details table
        entity_type = classification.get('entity_type', 'unknown')
        sector = classification.get('sector', 'unknown')

        details = [
            ['Assessment Date:', datetime.now().strftime('%Y-%m-%d')],
            ['Organization:', assessment.get('organization_name', 'N/A')],
            ['Entity Classification:', ENTITY_TYPES.get(entity_type, entity_type)],
            ['Sector:', SECTOR_NAMES.get(sector, sector)],
            ['Status:', assessment.get('status', 'N/A').replace('_', ' ').title()],
        ]

        table = Table(details, colWidths=[2 * inch, 4 * inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#374151")),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 2 * inch))

        # Footer note
        elements.append(Paragraph(
            "Generated by ISORA",
            ParagraphStyle(
                name='FooterNote',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor("#9CA3AF"),
                alignment=TA_CENTER,
            )
        ))

        return elements

    def _create_executive_summary(self, assessment: Dict[str, Any], classification: Dict[str, Any]) -> List:
        """Create the executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        # Overall score
        score = assessment.get('overall_score', 0)
        score_color = self._get_score_color(score)
        compliance_level = assessment.get('compliance_level', 'Unknown')

        score_table_data = [
            [Paragraph(f"<font size='36' color='{score_color}'>{score:.0f}%</font>", self.styles['Normal'])],
            [Paragraph("Overall Compliance Score", ParagraphStyle(name='ScoreLabel', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=10))],
            [Paragraph(f"<b>{compliance_level}</b>", ParagraphStyle(name='ComplianceLevel', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=12))],
        ]

        score_table = Table(score_table_data, colWidths=[3 * inch])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Executive summary text
        entity_type = classification.get('entity_type', 'unknown')
        sector = classification.get('sector', 'unknown')

        summary_text = assessment.get('executive_summary', '')
        if not summary_text:
            if entity_type == 'essential':
                summary_text = (
                    f"As an Essential Entity in the {SECTOR_NAMES.get(sector, sector)} sector, "
                    f"your organization is subject to the full requirements of the NIS2 Directive. "
                    f"Based on the assessment, your current compliance level is {compliance_level} "
                    f"with an overall score of {score:.0f}%."
                )
            elif entity_type == 'important':
                summary_text = (
                    f"As an Important Entity in the {SECTOR_NAMES.get(sector, sector)} sector, "
                    f"your organization must comply with key NIS2 requirements. "
                    f"Based on the assessment, your current compliance level is {compliance_level} "
                    f"with an overall score of {score:.0f}%."
                )
            else:
                summary_text = (
                    f"Based on the assessment criteria, your organization may not fall under "
                    f"the direct scope of NIS2. However, maintaining strong cybersecurity practices "
                    f"is still recommended."
                )

        elements.append(Paragraph(summary_text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.2 * inch))

        # Key metrics
        gaps_count = assessment.get('gaps_count', len(assessment.get('gaps', [])))
        measures_compliant = assessment.get('measures_compliant', 0)
        measures_total = assessment.get('measures_total', 0)

        metrics_data = [
            ['Metric', 'Value'],
            ['Entity Type', ENTITY_TYPES.get(entity_type, entity_type)],
            ['Sector', SECTOR_NAMES.get(sector, sector)],
            ['Measures Compliant', f"{measures_compliant} / {measures_total}"],
            ['Gaps Identified', str(gaps_count)],
        ]

        metrics_table = Table(metrics_data, colWidths=[3 * inch, 2.5 * inch])
        metrics_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(metrics_table)

        return elements

    def _create_classification_section(self, classification: Dict[str, Any]) -> List:
        """Create the entity classification section."""
        elements = []

        elements.append(Paragraph("Entity Classification", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        entity_type = classification.get('entity_type', 'unknown')
        sector = classification.get('sector', 'unknown')
        subsector = classification.get('subsector', '')
        employee_count = classification.get('employee_count', 0)
        annual_revenue = classification.get('annual_revenue', 0)

        # Classification result box
        if entity_type == 'essential':
            bg_color = colors.HexColor("#FEE2E2")
            border_color = colors.HexColor("#EF4444")
            text_color = "#991B1B"
            classification_text = "ESSENTIAL ENTITY"
            description = (
                "Your organization is classified as an Essential Entity under NIS2. "
                "This means you are subject to stricter supervision, including proactive oversight "
                "by national authorities and higher potential penalties for non-compliance."
            )
        elif entity_type == 'important':
            bg_color = colors.HexColor("#FEF3C7")
            border_color = colors.HexColor("#EAB308")
            text_color = "#92400E"
            classification_text = "IMPORTANT ENTITY"
            description = (
                "Your organization is classified as an Important Entity under NIS2. "
                "While subject to lighter supervision (reactive), you must still comply "
                "with cybersecurity risk-management and reporting obligations."
            )
        else:
            bg_color = colors.HexColor("#D1FAE5")
            border_color = colors.HexColor("#22C55E")
            text_color = "#065F46"
            classification_text = "NOT IN SCOPE"
            description = (
                "Based on the provided information, your organization does not appear to fall "
                "within the scope of the NIS2 Directive. However, best practices suggest "
                "maintaining strong cybersecurity measures."
            )

        class_table = Table([
            [Paragraph(f"<font color='{text_color}'><b>{classification_text}</b></font>", self.styles['Normal'])]
        ], colWidths=[5 * inch])
        class_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 2, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(class_table)
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(description, self.styles['BodyText']))
        elements.append(Spacer(1, 0.3 * inch))

        # Classification criteria
        elements.append(Paragraph("Classification Criteria", self.styles['SubsectionHeader']))

        criteria_data = [
            ['Criterion', 'Value', 'Threshold'],
            ['Sector', SECTOR_NAMES.get(sector, sector), 'Listed in Annex I/II'],
            ['Subsector', subsector or 'N/A', '-'],
            ['Employee Count', str(employee_count) if employee_count else 'N/A', '>= 50 (Essential) / >= 10 (Important)'],
            ['Annual Revenue', f"EUR {annual_revenue:,.0f}" if annual_revenue else 'N/A', '>= EUR 10M (Essential) / >= EUR 2M (Important)'],
        ]

        criteria_table = Table(criteria_data, colWidths=[2 * inch, 2 * inch, 2.5 * inch])
        criteria_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(criteria_table)

        return elements

    def _create_measures_section(self, measures: List[Dict[str, Any]]) -> List:
        """Create security measures assessment section."""
        elements = []

        elements.append(Paragraph("Security Measures Assessment", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "The following security measures have been assessed according to Article 21 "
            "of the NIS2 Directive requirements.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Status summary
        status_counts = {'compliant': 0, 'partial': 0, 'gap': 0, 'not_evaluated': 0}
        for measure in measures:
            status = measure.get('status', 'not_evaluated')
            status_counts[status] = status_counts.get(status, 0) + 1

        summary_data = [
            ['Status', 'Count', 'Percentage'],
            ['Compliant', str(status_counts.get('compliant', 0)), f"{status_counts.get('compliant', 0) / len(measures) * 100:.0f}%" if measures else "0%"],
            ['Partial', str(status_counts.get('partial', 0)), f"{status_counts.get('partial', 0) / len(measures) * 100:.0f}%" if measures else "0%"],
            ['Gap', str(status_counts.get('gap', 0)), f"{status_counts.get('gap', 0) / len(measures) * 100:.0f}%" if measures else "0%"],
            ['Not Evaluated', str(status_counts.get('not_evaluated', 0)), f"{status_counts.get('not_evaluated', 0) / len(measures) * 100:.0f}%" if measures else "0%"],
        ]

        summary_table = Table(summary_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('BACKGROUND', (0, 1), (0, 1), colors.HexColor("#D1FAE5")),
            ('BACKGROUND', (0, 2), (0, 2), colors.HexColor("#FEF3C7")),
            ('BACKGROUND', (0, 3), (0, 3), colors.HexColor("#FEE2E2")),
            ('BACKGROUND', (0, 4), (0, 4), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Measures details
        elements.append(Paragraph("Detailed Assessment", self.styles['SubsectionHeader']))

        measures_data = [['Measure', 'Status', 'Implementation']]
        for measure in measures[:15]:  # Limit to 15
            name = measure.get('name', measure.get('measure_name', 'N/A'))
            if len(name) > 40:
                name = name[:37] + '...'
            status = measure.get('status', 'not_evaluated').replace('_', ' ').title()
            level = measure.get('implementation_level', 0)

            measures_data.append([name, status, f"{level}%"])

        if len(measures) > 15:
            measures_data.append(['...', f'({len(measures) - 15} more)', ''])

        measures_table = Table(measures_data, colWidths=[3.5 * inch, 1.5 * inch, 1.2 * inch])
        measures_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(measures_table)

        return elements

    def _create_gap_section(self, gaps: List[Dict[str, Any]]) -> List:
        """Create gap analysis section."""
        elements = []

        elements.append(Paragraph("Gap Analysis", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            f"This section identifies {len(gaps)} gaps in NIS2 compliance that require attention.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Priority summary
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for gap in gaps:
            priority = gap.get('priority', 3)
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        priority_data = [
            ['Priority', 'Count', 'Timeline'],
            ['Critical (P1)', str(priority_counts.get(1, 0)), 'Immediate action required'],
            ['High (P2)', str(priority_counts.get(2, 0)), 'Within 30 days'],
            ['Medium (P3)', str(priority_counts.get(3, 0)), 'Within 90 days'],
            ['Low (P4)', str(priority_counts.get(4, 0)), 'Within 180 days'],
        ]

        priority_table = Table(priority_data, colWidths=[1.5 * inch, 1 * inch, 3 * inch])
        priority_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('BACKGROUND', (0, 1), (0, 1), colors.HexColor("#FEE2E2")),
            ('BACKGROUND', (0, 2), (0, 2), colors.HexColor("#FEF3C7")),
            ('BACKGROUND', (0, 3), (0, 3), colors.HexColor("#E0E7FF")),
            ('BACKGROUND', (0, 4), (0, 4), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(priority_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Gap details
        elements.append(Paragraph("Gap Details", self.styles['SubsectionHeader']))

        for gap in gaps[:10]:
            measure_name = gap.get('measure_name', gap.get('name', 'N/A'))
            priority = gap.get('priority', 3)
            priority_labels = {1: 'Critical', 2: 'High', 3: 'Medium', 4: 'Low'}

            elements.append(Paragraph(
                f"<b>{measure_name}</b> (Priority: {priority_labels.get(priority, 'N/A')})",
                self.styles['BodyText']
            ))

            if gap.get('gap_description'):
                elements.append(Paragraph(
                    f"<i>Gap:</i> {gap.get('gap_description')}",
                    self.styles['BodyText']
                ))

            if gap.get('remediation_plan'):
                elements.append(Paragraph(
                    f"<i>Remediation:</i> {gap.get('remediation_plan')}",
                    self.styles['BodyText']
                ))

            elements.append(Spacer(1, 0.1 * inch))

        if len(gaps) > 10:
            elements.append(Paragraph(
                f"... and {len(gaps) - 10} more gaps",
                ParagraphStyle(name='MoreNote', parent=self.styles['BodyText'], textColor=colors.gray)
            ))

        return elements

    def _create_recommendations_section(self, recommendations: List[str]) -> List:
        """Create recommendations section."""
        elements = []

        elements.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "Based on the assessment, the following actions are recommended to improve NIS2 compliance:",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        for i, rec in enumerate(recommendations[:10], 1):
            elements.append(Paragraph(
                f"<b>{i}.</b> {rec}",
                self.styles['BodyText']
            ))

        elements.append(Spacer(1, 0.3 * inch))

        # Next steps
        elements.append(Paragraph("Next Steps", self.styles['SubsectionHeader']))

        next_steps = [
            "Review and prioritize identified gaps based on risk assessment",
            "Develop remediation plans with clear ownership and timelines",
            "Implement necessary security measures according to Article 21",
            "Establish incident reporting procedures as per Article 23",
            "Schedule regular compliance reviews and updates",
        ]

        for i, step in enumerate(next_steps, 1):
            elements.append(Paragraph(
                f"<b>{i}.</b> {step}",
                self.styles['BodyText']
            ))

        return elements

    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        canvas.saveState()

        # Header
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 20, "NIS2 Directive Compliance Report")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin + 20, datetime.now().strftime('%Y-%m-%d'))

        # Footer
        canvas.drawString(doc.leftMargin, 30, "Confidential - For Internal Use Only")
        canvas.drawRightString(doc.width + doc.leftMargin, 30, f"Page {canvas.getPageNumber()}")

        canvas.restoreState()

    def _get_score_color(self, score: Optional[float]) -> str:
        """Get color based on score value."""
        if score is None:
            return "#9CA3AF"
        if score >= 80:
            return "#22C55E"
        if score >= 60:
            return "#EAB308"
        return "#EF4444"
