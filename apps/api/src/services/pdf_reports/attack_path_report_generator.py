"""
Attack Path Analysis Report Generator.

Generates PDF reports for attack path analysis using ReportLab.
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


class AttackPathReportGenerator:
    """
    Generator for Attack Path Analysis reports.

    Creates professional PDF reports including:
    - Executive summary with risk overview
    - Attack graph statistics
    - Critical attack paths listing
    - Crown jewels inventory
    - Entry points inventory
    - Chokepoint analysis
    - Remediation recommendations
    """

    # Risk level colors
    RISK_COLORS = {
        "critical": colors.HexColor("#DC2626"),  # Red
        "high": colors.HexColor("#EA580C"),       # Orange
        "medium": colors.HexColor("#CA8A04"),     # Yellow
        "low": colors.HexColor("#16A34A"),        # Green
    }

    STATUS_COLORS = {
        "active": colors.HexColor("#EF4444"),
        "mitigated": colors.HexColor("#22C55E"),
        "accepted": colors.HexColor("#3B82F6"),
        "false_positive": colors.HexColor("#9CA3AF"),
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

        # Body text
        self.styles['BodyText'].fontSize = 10
        self.styles['BodyText'].textColor = colors.HexColor("#374151")
        self.styles['BodyText'].alignment = TA_JUSTIFY
        self.styles['BodyText'].spaceAfter = 8

        # Score style
        self.styles.add(ParagraphStyle(
            name='ScoreText',
            parent=self.styles['Normal'],
            fontSize=36,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_CENTER,
        ))

        # Risk label style
        self.styles.add(ParagraphStyle(
            name='RiskLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
        ))

    def generate_report(
        self,
        graph: Dict[str, Any],
        paths: List[Dict[str, Any]],
        crown_jewels: List[Dict[str, Any]],
        entry_points: List[Dict[str, Any]],
        chokepoints: List[Dict[str, Any]],
        simulations: Optional[List[Dict[str, Any]]] = None,
        language: str = "en",
        include_paths: bool = True,
        include_assets: bool = True,
        include_recommendations: bool = True,
    ) -> bytes:
        """
        Generate a complete attack path analysis report.

        Args:
            graph: Attack graph data with statistics
            paths: List of attack paths
            crown_jewels: List of crown jewel assets
            entry_points: List of entry points
            chokepoints: List of chokepoint analysis
            simulations: List of what-if simulations
            language: Report language (en, de, es)
            include_paths: Include attack paths section
            include_assets: Include crown jewels/entry points
            include_recommendations: Include remediation section

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
        story.extend(self._create_title_page(graph))
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary(graph, paths, crown_jewels, entry_points))
        story.append(PageBreak())

        # Attack paths section
        if include_paths and paths:
            story.extend(self._create_paths_section(paths))
            story.append(PageBreak())

        # Crown jewels and entry points
        if include_assets:
            if crown_jewels:
                story.extend(self._create_crown_jewels_section(crown_jewels))
                story.append(PageBreak())
            if entry_points:
                story.extend(self._create_entry_points_section(entry_points))
                story.append(PageBreak())

        # Chokepoint analysis
        if chokepoints:
            story.extend(self._create_chokepoints_section(chokepoints))
            story.append(PageBreak())

        # Simulations
        if simulations:
            story.extend(self._create_simulations_section(simulations))
            story.append(PageBreak())

        # Recommendations
        if include_recommendations:
            story.extend(self._create_recommendations_section(paths, chokepoints))

        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)

        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    def _create_title_page(self, graph: Dict[str, Any]) -> List:
        """Create the title page."""
        elements = []

        # Add spacing
        elements.append(Spacer(1, 2 * inch))

        # Title
        elements.append(Paragraph(
            "Attack Path Analysis",
            self.styles['ReportTitle']
        ))
        elements.append(Paragraph(
            "Security Assessment Report",
            self.styles['SectionHeader']
        ))

        elements.append(Spacer(1, 0.5 * inch))

        # Graph name
        elements.append(Paragraph(
            graph.get('name', 'Untitled Graph'),
            self.styles['SubsectionHeader']
        ))

        elements.append(Spacer(1, 1.5 * inch))

        # Assessment details table
        computed_at = graph.get('computed_at')
        if isinstance(computed_at, str):
            computed_at = computed_at[:10] if computed_at else 'N/A'
        elif hasattr(computed_at, 'strftime'):
            computed_at = computed_at.strftime('%Y-%m-%d')
        else:
            computed_at = 'N/A'

        details = [
            ['Report Date:', datetime.now().strftime('%Y-%m-%d')],
            ['Graph Status:', graph.get('status', 'N/A').replace('_', ' ').title()],
            ['Computed:', computed_at],
            ['Total Nodes:', str(graph.get('total_nodes', 0))],
            ['Total Edges:', str(graph.get('total_edges', 0))],
        ]

        scope_desc = graph.get('description', '')
        if scope_desc:
            details.append(['Scope:', (scope_desc[:50] + '...') if len(scope_desc) > 50 else scope_desc])

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

    def _create_executive_summary(
        self,
        graph: Dict[str, Any],
        paths: List[Dict[str, Any]],
        crown_jewels: List[Dict[str, Any]],
        entry_points: List[Dict[str, Any]]
    ) -> List:
        """Create the executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        # Risk distribution calculation
        critical_paths = len([p for p in paths if p.get('risk_score', 0) >= 8.0])
        high_paths = len([p for p in paths if 6.0 <= p.get('risk_score', 0) < 8.0])
        medium_paths = len([p for p in paths if 4.0 <= p.get('risk_score', 0) < 6.0])
        low_paths = len([p for p in paths if p.get('risk_score', 0) < 4.0])

        # Overall risk level
        if critical_paths > 0:
            overall_risk = "CRITICAL"
            risk_color = "#DC2626"
        elif high_paths > 0:
            overall_risk = "HIGH"
            risk_color = "#EA580C"
        elif medium_paths > 0:
            overall_risk = "MEDIUM"
            risk_color = "#CA8A04"
        else:
            overall_risk = "LOW"
            risk_color = "#16A34A"

        # Risk score display
        risk_table_data = [
            [Paragraph(f"<font size='36' color='{risk_color}'>{overall_risk}</font>", self.styles['Normal'])],
            [Paragraph("Overall Risk Level", self.styles['RiskLabel'])],
        ]

        risk_table = Table(risk_table_data, colWidths=[3 * inch])
        risk_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(risk_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Key metrics
        metrics_data = [
            ['Metric', 'Count'],
            ['Total Attack Paths', str(len(paths))],
            ['Critical Risk Paths', str(critical_paths)],
            ['High Risk Paths', str(high_paths)],
            ['Medium Risk Paths', str(medium_paths)],
            ['Low Risk Paths', str(low_paths)],
            ['Crown Jewels', str(len(crown_jewels))],
            ['Entry Points', str(len(entry_points))],
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
            # Color code risk rows
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#FEE2E2")),  # Critical
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#FEF3C7")),  # High
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor("#FEF9C3")),  # Medium
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Summary text
        elements.append(Paragraph("Analysis Overview", self.styles['SubsectionHeader']))

        active_paths = len([p for p in paths if p.get('status') == 'active'])
        summary_text = (
            f"This analysis identified <b>{len(paths)} attack paths</b> from "
            f"{len(entry_points)} entry points to {len(crown_jewels)} crown jewel assets. "
            f"Of these, <b>{critical_paths} paths are rated as critical</b> and require "
            f"immediate attention. Currently, <b>{active_paths} paths remain active</b> "
            f"and unmitigated."
        )
        elements.append(Paragraph(summary_text, self.styles['BodyText']))

        return elements

    def _create_paths_section(self, paths: List[Dict[str, Any]]) -> List:
        """Create the attack paths section."""
        elements = []

        elements.append(Paragraph("Attack Paths", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "The following attack paths have been identified, ordered by risk score. "
            "Each path represents a potential route an attacker could take from an "
            "entry point to a critical asset.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Sort paths by risk score (descending)
        sorted_paths = sorted(paths, key=lambda x: x.get('risk_score', 0), reverse=True)

        # Show top 15 paths
        for i, path in enumerate(sorted_paths[:15], 1):
            risk_score = path.get('risk_score', 0)
            if risk_score >= 8.0:
                risk_label = "CRITICAL"
                risk_color = "#DC2626"
            elif risk_score >= 6.0:
                risk_label = "HIGH"
                risk_color = "#EA580C"
            elif risk_score >= 4.0:
                risk_label = "MEDIUM"
                risk_color = "#CA8A04"
            else:
                risk_label = "LOW"
                risk_color = "#16A34A"

            status = path.get('status', 'active').replace('_', ' ').title()

            elements.append(Paragraph(
                f"<b>{i}. {path.get('name', 'Unnamed Path')}</b> "
                f"(<font color='{risk_color}'>{risk_label}</font> - Score: {risk_score:.1f})",
                self.styles['SubsectionHeader']
            ))

            # Path details table
            path_data = [
                ['Entry Point:', path.get('entry_point_name', 'N/A')],
                ['Target:', path.get('target_name', 'N/A')],
                ['Hop Count:', str(path.get('hop_count', 0))],
                ['Vulnerabilities:', str(path.get('exploitable_vulns', 0))],
                ['Status:', status],
            ]

            path_table = Table(path_data, colWidths=[1.5 * inch, 4 * inch])
            path_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#4B5563")),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(path_table)
            elements.append(Spacer(1, 0.15 * inch))

        if len(sorted_paths) > 15:
            elements.append(Paragraph(
                f"... and {len(sorted_paths) - 15} more paths (see full data export for details)",
                ParagraphStyle(name='MoreNote', parent=self.styles['BodyText'], textColor=colors.gray)
            ))

        return elements

    def _create_crown_jewels_section(self, crown_jewels: List[Dict[str, Any]]) -> List:
        """Create the crown jewels inventory section."""
        elements = []

        elements.append(Paragraph("Crown Jewel Assets", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "Crown jewels are critical assets that represent high-value targets for attackers. "
            "These assets contain sensitive data or provide critical business functions.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Crown jewels table
        table_data = [['Asset', 'Type', 'Impact', 'Classification', 'Owner']]

        for jewel in crown_jewels[:20]:
            asset_name = jewel.get('asset_name') or jewel.get('asset_id', 'N/A')
            if len(str(asset_name)) > 25:
                asset_name = str(asset_name)[:25] + '...'

            table_data.append([
                asset_name,
                jewel.get('jewel_type', 'N/A').replace('_', ' ').title(),
                jewel.get('business_impact', 'N/A').replace('_', ' ').title(),
                (jewel.get('data_classification') or 'N/A').replace('_', ' ').title(),
                jewel.get('business_owner', 'N/A')[:15],
            ])

        jewels_table = Table(table_data, colWidths=[1.5 * inch, 1 * inch, 0.9 * inch, 1.1 * inch, 1 * inch])
        jewels_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(jewels_table)

        if len(crown_jewels) > 20:
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph(
                f"... and {len(crown_jewels) - 20} more crown jewels",
                ParagraphStyle(name='MoreNote', parent=self.styles['BodyText'], textColor=colors.gray)
            ))

        return elements

    def _create_entry_points_section(self, entry_points: List[Dict[str, Any]]) -> List:
        """Create the entry points inventory section."""
        elements = []

        elements.append(Paragraph("Entry Points", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "Entry points are assets that could serve as initial footholds for attackers. "
            "These typically include internet-facing services, VPN endpoints, and email gateways.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Entry points table
        table_data = [['Asset', 'Type', 'Exposure', 'Auth', 'MFA', 'Vulns']]

        for point in entry_points[:20]:
            asset_name = point.get('asset_name') or point.get('asset_id', 'N/A')
            if len(str(asset_name)) > 25:
                asset_name = str(asset_name)[:25] + '...'

            table_data.append([
                asset_name,
                point.get('entry_type', 'N/A').replace('_', ' ').title(),
                point.get('exposure_level', 'N/A').replace('_', ' ').title(),
                'Yes' if point.get('authentication_required') else 'No',
                'Yes' if point.get('mfa_enabled') else 'No',
                str(point.get('known_vulnerabilities', 0)),
            ])

        entry_table = Table(table_data, colWidths=[1.5 * inch, 1.2 * inch, 1 * inch, 0.6 * inch, 0.6 * inch, 0.6 * inch])
        entry_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(entry_table)

        if len(entry_points) > 20:
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph(
                f"... and {len(entry_points) - 20} more entry points",
                ParagraphStyle(name='MoreNote', parent=self.styles['BodyText'], textColor=colors.gray)
            ))

        return elements

    def _create_chokepoints_section(self, chokepoints: List[Dict[str, Any]]) -> List:
        """Create the chokepoint analysis section."""
        elements = []

        elements.append(Paragraph("Chokepoint Analysis", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "Chokepoints are assets that appear in multiple attack paths. Securing these assets "
            "has the highest impact on reducing overall attack surface.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Chokepoints table
        table_data = [['Asset', 'Type', 'Paths Affected', 'Risk Mitigated', 'Priority']]

        for choke in chokepoints[:15]:
            asset_name = choke.get('asset_name', 'N/A')
            if len(str(asset_name)) > 25:
                asset_name = str(asset_name)[:25] + '...'

            priority = choke.get('priority_score', 0)
            if priority >= 8:
                priority_label = "Critical"
            elif priority >= 6:
                priority_label = "High"
            elif priority >= 4:
                priority_label = "Medium"
            else:
                priority_label = "Low"

            table_data.append([
                asset_name,
                choke.get('asset_type', 'N/A'),
                str(choke.get('paths_affected', 0)),
                f"{choke.get('total_risk_mitigated', 0):.1f}",
                priority_label,
            ])

        choke_table = Table(table_data, colWidths=[1.8 * inch, 1 * inch, 1 * inch, 1 * inch, 0.8 * inch])
        choke_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(choke_table)

        return elements

    def _create_simulations_section(self, simulations: List[Dict[str, Any]]) -> List:
        """Create the what-if simulations section."""
        elements = []

        elements.append(Paragraph("What-If Simulations", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "The following simulations have been run to evaluate the impact of potential "
            "security improvements.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        for sim in simulations[:10]:
            sim_type = sim.get('simulation_type', 'unknown').replace('_', ' ').title()
            status = sim.get('status', 'pending')

            elements.append(Paragraph(
                f"<b>{sim.get('name', 'Unnamed Simulation')}</b> ({sim_type})",
                self.styles['SubsectionHeader']
            ))

            if status == 'completed':
                risk_reduction = sim.get('risk_reduction_percent', 0)
                paths_eliminated = sim.get('paths_eliminated', 0)

                sim_data = [
                    ['Original Paths:', str(sim.get('original_paths_count', 0))],
                    ['Paths Eliminated:', str(paths_eliminated)],
                    ['Risk Reduction:', f"{risk_reduction:.1f}%"],
                ]

                if sim.get('recommendation'):
                    sim_data.append(['Recommendation:', sim.get('recommendation')[:60]])

                sim_table = Table(sim_data, colWidths=[1.5 * inch, 4 * inch])
                sim_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#4B5563")),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(sim_table)
            else:
                elements.append(Paragraph(
                    f"Status: {status.title()}",
                    self.styles['BodyText']
                ))

            elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _create_recommendations_section(
        self,
        paths: List[Dict[str, Any]],
        chokepoints: List[Dict[str, Any]]
    ) -> List:
        """Create the recommendations section."""
        elements = []

        elements.append(Paragraph("Remediation Recommendations", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "Based on the attack path analysis, the following remediation actions are recommended:",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        # Priority 1: Secure top chokepoints
        if chokepoints:
            elements.append(Paragraph(
                "<b>1. Secure Critical Chokepoints</b>",
                self.styles['SubsectionHeader']
            ))
            elements.append(Paragraph(
                "Focus remediation efforts on the following chokepoint assets as they "
                "will have the greatest impact on reducing attack paths:",
                self.styles['BodyText']
            ))

            for i, choke in enumerate(chokepoints[:5], 1):
                recommendations = choke.get('recommendations', [])
                rec_text = recommendations[0] if recommendations else "Apply security hardening"
                elements.append(Paragraph(
                    f"• <b>{choke.get('asset_name', 'N/A')}</b>: {rec_text}",
                    self.styles['BodyText']
                ))

            elements.append(Spacer(1, 0.15 * inch))

        # Priority 2: Address critical paths
        critical_paths = [p for p in paths if p.get('risk_score', 0) >= 8.0]
        if critical_paths:
            elements.append(Paragraph(
                "<b>2. Mitigate Critical Attack Paths</b>",
                self.styles['SubsectionHeader']
            ))
            elements.append(Paragraph(
                f"There are {len(critical_paths)} critical-risk attack paths that require "
                f"immediate attention:",
                self.styles['BodyText']
            ))

            for path in critical_paths[:5]:
                elements.append(Paragraph(
                    f"• <b>{path.get('name', 'Unnamed')}</b>: "
                    f"Path from {path.get('entry_point_name', 'N/A')} to {path.get('target_name', 'N/A')} "
                    f"with {path.get('exploitable_vulns', 0)} exploitable vulnerabilities",
                    self.styles['BodyText']
                ))

            elements.append(Spacer(1, 0.15 * inch))

        # Priority 3: General recommendations
        elements.append(Paragraph(
            "<b>3. General Security Improvements</b>",
            self.styles['SubsectionHeader']
        ))

        general_recs = [
            "Implement network segmentation to isolate critical assets",
            "Enable multi-factor authentication on all entry points",
            "Patch vulnerabilities on assets in critical attack paths",
            "Review and restrict unnecessary network connectivity",
            "Conduct regular attack path analysis after infrastructure changes",
        ]

        for rec in general_recs:
            elements.append(Paragraph(f"• {rec}", self.styles['BodyText']))

        return elements

    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        canvas.saveState()

        # Header
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 20, "Attack Path Analysis Report")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin + 20, datetime.now().strftime('%Y-%m-%d'))

        # Footer
        canvas.drawString(doc.leftMargin, 30, "Confidential - For Internal Use Only")
        canvas.drawRightString(doc.width + doc.leftMargin, 30, f"Page {canvas.getPageNumber()}")

        canvas.restoreState()

    def _get_risk_color(self, score: float) -> str:
        """Get color based on risk score."""
        if score >= 8.0:
            return "#DC2626"
        if score >= 6.0:
            return "#EA580C"
        if score >= 4.0:
            return "#CA8A04"
        return "#16A34A"
