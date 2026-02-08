"""
ISO 27001:2022 Compliance Report Generator.

Generates PDF reports for ISO 27001 compliance assessments using ReportLab.
"""
import io
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, ListFlowable, ListItem
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ISO27001ReportGenerator:
    """
    Generator for ISO 27001:2022 compliance reports.

    Creates professional PDF reports including:
    - Executive summary with compliance scores
    - Theme-by-theme breakdown
    - Gap analysis with remediation plans
    - Cross-framework mapping
    - Statement of Applicability (SoA)
    """

    # ISO 27001 Theme colors
    THEME_COLORS = {
        "A.5": colors.HexColor("#3B82F6"),  # Blue - Organizational
        "A.6": colors.HexColor("#22C55E"),  # Green - People
        "A.7": colors.HexColor("#F97316"),  # Orange - Physical
        "A.8": colors.HexColor("#A855F7"),  # Purple - Technological
    }

    THEME_NAMES = {
        "A.5": "Organizational Controls",
        "A.6": "People Controls",
        "A.7": "Physical Controls",
        "A.8": "Technological Controls",
    }

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
            borderColor=colors.HexColor("#E5E7EB"),
            borderWidth=0,
            borderPadding=5,
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

        # Body text (override existing BodyText style)
        self.styles['BodyText'].fontSize = 10
        self.styles['BodyText'].textColor = colors.HexColor("#374151")
        self.styles['BodyText'].alignment = TA_JUSTIFY
        self.styles['BodyText'].spaceAfter = 8

        # Score style (large number)
        self.styles.add(ParagraphStyle(
            name='ScoreText',
            parent=self.styles['Normal'],
            fontSize=36,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_CENTER,
        ))

    def generate_report(
        self,
        assessment: Dict[str, Any],
        overview: Dict[str, Any],
        soa_entries: List[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
        cross_framework: Optional[Dict[str, Any]] = None,
        language: str = "en",
        include_soa: bool = True,
        include_gaps: bool = True,
        include_mapping: bool = True,
    ) -> bytes:
        """
        Generate a complete ISO 27001 compliance report.

        Args:
            assessment: Assessment data including scores
            overview: Overview with theme breakdowns
            soa_entries: Statement of Applicability entries
            gaps: Gap analysis results
            cross_framework: Cross-framework mapping data
            language: Report language (en, de, es)
            include_soa: Include SoA section
            include_gaps: Include gap analysis section
            include_mapping: Include cross-framework mapping

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
        story.extend(self._create_title_page(assessment))
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary(assessment, overview))
        story.append(PageBreak())

        # Theme breakdown
        story.extend(self._create_theme_breakdown(overview))
        story.append(PageBreak())

        # Statement of Applicability
        if include_soa and soa_entries:
            story.extend(self._create_soa_section(soa_entries))
            story.append(PageBreak())

        # Gap analysis
        if include_gaps and gaps:
            story.extend(self._create_gap_section(gaps))
            story.append(PageBreak())

        # Cross-framework mapping
        if include_mapping and cross_framework:
            story.extend(self._create_mapping_section(cross_framework))

        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)

        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    def _create_title_page(self, assessment: Dict[str, Any]) -> List:
        """Create the title page."""
        elements = []

        # Add spacing
        elements.append(Spacer(1, 2 * inch))

        # Title
        elements.append(Paragraph(
            "ISO 27001:2022",
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
        details = [
            ['Assessment Date:', datetime.now().strftime('%Y-%m-%d')],
            ['Status:', assessment.get('status', 'N/A').replace('_', ' ').title()],
            ['Scope:', assessment.get('scope_description', 'Not defined')[:50] + '...' if assessment.get('scope_description') and len(assessment.get('scope_description', '')) > 50 else assessment.get('scope_description', 'Not defined')],
        ]

        if assessment.get('completed_at'):
            details.insert(1, ['Completed:', assessment.get('completed_at')[:10]])

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

    def _create_executive_summary(self, assessment: Dict[str, Any], overview: Dict[str, Any]) -> List:
        """Create the executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        # Overall score
        score = overview.get('overall_score')
        score_color = self._get_score_color(score)

        score_table_data = [
            [Paragraph(f"<font size='36' color='{score_color}'>{score:.0f}%</font>" if score is not None else "N/A", self.styles['Normal'])],
            [Paragraph("Overall Compliance Score", ParagraphStyle(name='ScoreLabel', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=10))],
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

        # Key metrics
        metrics_data = [
            ['Metric', 'Count'],
            ['Total Controls', '93'],
            ['Applicable Controls', str(overview.get('total_applicable', 0))],
            ['Compliant', str(overview.get('total_compliant', 0))],
            ['Partial Implementation', str(overview.get('total_partial', 0))],
            ['Gaps Identified', str(overview.get('total_gap', 0))],
        ]

        metrics_table = Table(metrics_data, colWidths=[3 * inch, 1.5 * inch])
        metrics_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Assessment status summary
        elements.append(Paragraph("Assessment Status", self.styles['SubsectionHeader']))

        status = assessment.get('status', 'unknown')
        status_text = {
            'draft': 'The assessment is in draft status and has not been started.',
            'scoping': 'The assessment scope is being defined.',
            'soa': 'The Statement of Applicability is being created.',
            'assessment': 'Control assessment is in progress.',
            'gap_analysis': 'Gap analysis and remediation planning is in progress.',
            'completed': 'The assessment has been completed.',
            'archived': 'The assessment has been archived.',
        }.get(status, 'Status unknown')

        elements.append(Paragraph(status_text, self.styles['BodyText']))

        return elements

    def _create_theme_breakdown(self, overview: Dict[str, Any]) -> List:
        """Create theme-by-theme breakdown section."""
        elements = []

        elements.append(Paragraph("Compliance by Theme", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "ISO 27001:2022 Annex A contains 93 controls organized into 4 themes. "
            "The following breakdown shows compliance status for each theme.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        themes = overview.get('themes', [])

        for theme in themes:
            theme_id = theme.get('theme_id', '')
            theme_name = self.THEME_NAMES.get(theme_id, theme.get('theme_name', theme_id))
            theme_color = self.THEME_COLORS.get(theme_id, colors.gray)

            # Theme header
            elements.append(Paragraph(
                f"<font color='#{theme_color.hexval()[2:]}'>{theme_id}</font> - {theme_name}",
                self.styles['SubsectionHeader']
            ))

            # Theme metrics table
            score = theme.get('score')
            theme_data = [
                ['Total Controls', 'Applicable', 'Compliant', 'Partial', 'Gaps', 'Score'],
                [
                    str(theme.get('total_controls', 0)),
                    str(theme.get('applicable_controls', 0)),
                    str(theme.get('compliant_controls', 0)),
                    str(theme.get('partial_controls', 0)),
                    str(theme.get('gap_controls', 0)),
                    f"{score:.0f}%" if score is not None else "N/A",
                ],
            ]

            theme_table = Table(theme_data, colWidths=[1.2 * inch] * 6)
            theme_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(theme_table)
            elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _create_soa_section(self, soa_entries: List[Dict[str, Any]]) -> List:
        """Create Statement of Applicability section."""
        elements = []

        elements.append(Paragraph("Statement of Applicability", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "The Statement of Applicability (SoA) documents which ISO 27001 controls are applicable "
            "to the organization and the justification for any exclusions.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Group by theme
        themes = {}
        for entry in soa_entries:
            theme = entry.get('control_theme', 'Unknown')
            if theme not in themes:
                themes[theme] = []
            themes[theme].append(entry)

        for theme_id in sorted(themes.keys()):
            entries = themes[theme_id]
            theme_name = self.THEME_NAMES.get(theme_id, theme_id)

            elements.append(Paragraph(
                f"{theme_id} - {theme_name}",
                self.styles['SubsectionHeader']
            ))

            # Create table for this theme
            table_data = [['Control', 'Title', 'Applicability', 'Status', 'Level']]

            for entry in entries[:10]:  # Limit to prevent overly long reports
                applicability = entry.get('applicability', 'N/A')
                status = entry.get('status', 'N/A')

                table_data.append([
                    entry.get('control_code', 'N/A'),
                    (entry.get('control_title', 'N/A')[:30] + '...') if len(entry.get('control_title', '')) > 30 else entry.get('control_title', 'N/A'),
                    applicability.replace('_', ' ').title(),
                    status.replace('_', ' ').title(),
                    f"{entry.get('implementation_level', 0)}%",
                ])

            if len(entries) > 10:
                table_data.append(['...', f'({len(entries) - 10} more controls)', '', '', ''])

            soa_table = Table(table_data, colWidths=[0.8 * inch, 2.5 * inch, 1.2 * inch, 1 * inch, 0.7 * inch])
            soa_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (4, 0), (4, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(soa_table)
            elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _create_gap_section(self, gaps: List[Dict[str, Any]]) -> List:
        """Create gap analysis section."""
        elements = []

        elements.append(Paragraph("Gap Analysis", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            f"This section identifies {len(gaps)} gaps in ISO 27001 compliance and outlines "
            "recommended remediation actions.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Priority summary
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        for gap in gaps:
            priority = gap.get('priority', 3)
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        priority_data = [
            ['Priority', 'Count', 'Description'],
            ['Critical (P1)', str(priority_counts.get(1, 0)), 'Immediate action required'],
            ['High (P2)', str(priority_counts.get(2, 0)), 'Address within 30 days'],
            ['Medium (P3)', str(priority_counts.get(3, 0)), 'Address within 90 days'],
            ['Low (P4)', str(priority_counts.get(4, 0)), 'Address within 180 days'],
        ]

        priority_table = Table(priority_data, colWidths=[1.5 * inch, 0.8 * inch, 3 * inch])
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

        # Gap details (top 10)
        elements.append(Paragraph("Gap Details", self.styles['SubsectionHeader']))

        for gap in gaps[:10]:
            control_code = gap.get('control_code', 'N/A')
            control_title = gap.get('control_title', 'N/A')
            priority = gap.get('priority', 3)
            priority_labels = {1: 'Critical', 2: 'High', 3: 'Medium', 4: 'Low'}

            elements.append(Paragraph(
                f"<b>{control_code}</b> - {control_title} (Priority: {priority_labels.get(priority, 'N/A')})",
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
                f"... and {len(gaps) - 10} more gaps (see full SoA for details)",
                ParagraphStyle(name='MoreNote', parent=self.styles['BodyText'], textColor=colors.gray)
            ))

        return elements

    def _create_mapping_section(self, cross_framework: Dict[str, Any]) -> List:
        """Create cross-framework mapping section."""
        elements = []

        elements.append(Paragraph("Cross-Framework Mapping", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "ISO 27001 controls map to other security frameworks, enabling organizations "
            "to leverage existing compliance efforts across multiple standards.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Framework summary
        summary_data = [
            ['Framework', 'Related Controls'],
            ['BSI IT-Grundschutz', str(cross_framework.get('total_bsi_references', 0))],
            ['NIS2', str(cross_framework.get('total_nis2_references', 0))],
            ['NIST CSF', str(cross_framework.get('total_nist_references', 0))],
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 1.5 * inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)

        return elements

    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        canvas.saveState()

        # Header
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 20, "ISO 27001:2022 Compliance Report")
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
