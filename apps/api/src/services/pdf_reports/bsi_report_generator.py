"""BSI IT-Grundschutz Report Generator."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .pdf_service import PDFReportService

logger = logging.getLogger(__name__)

# Category names in German
KATEGORIE_NAMES = {
    "ISMS": "Sicherheitsmanagement",
    "ORP": "Organisation und Personal",
    "CON": "Konzeption und Planung",
    "OPS": "Betrieb",
    "DER": "Detektion und Reaktion",
    "APP": "Anwendungen",
    "SYS": "IT-Systeme",
    "NET": "Netze und Kommunikation",
    "INF": "Infrastruktur",
    "IND": "Industrielle IT",
}

SCHUTZBEDARF_NAMES = {
    "basis": "Basis-Absicherung",
    "standard": "Standard-Absicherung",
    "hoch": "Kern-Absicherung (Hoch)",
}

STATUS_NAMES = {
    "compliant": "Konform",
    "partial": "Teilweise",
    "gap": "Luecke",
    "not_evaluated": "Nicht bewertet",
    "not_applicable": "Nicht anwendbar",
}


class BSIReportGenerator:
    """Generator for BSI IT-Grundschutz compliance reports."""

    def __init__(self):
        self.pdf_service = PDFReportService()

    def generate_report(
        self,
        organization_name: str,
        schutzbedarf: str,
        overview_data: Dict[str, Any],
        category_data: List[Dict[str, Any]],
        detailed_findings: Optional[List[Dict[str, Any]]] = None,
        gap_analysis: Optional[List[Dict[str, Any]]] = None,
        classification: str = "Vertraulich",
        version: str = "1.0",
    ) -> Optional[bytes]:
        """Generate a BSI compliance report PDF."""

        # Calculate totals
        total = overview_data.get("total", 0)
        compliant = overview_data.get("compliant", 0)
        partial = overview_data.get("partial", 0)
        gap = overview_data.get("gap", 0)
        not_evaluated = overview_data.get("not_evaluated", 0)
        not_applicable = overview_data.get("not_applicable", 0)
        score = overview_data.get("overall_score_percent", 0)

        # Calculate percentages
        def calc_percent(value: int) -> float:
            return (value / total * 100) if total > 0 else 0

        # Prepare data for template
        data = {
            # Document metadata
            "organization": organization_name,
            "date": datetime.now(),
            "version": version,
            "classification": classification,
            "period": f"{datetime.now().strftime('%d.%m.%Y')}",

            # Schutzbedarf
            "schutzbedarf": SCHUTZBEDARF_NAMES.get(schutzbedarf, schutzbedarf),

            # Overall score
            "score": f"{score:.0f}",

            # Counts
            "compliant_count": str(compliant),
            "partial_count": str(partial),
            "gap_count": str(gap),
            "not_evaluated_count": str(not_evaluated),
            "not_applicable_count": str(not_applicable),

            # Percentages
            "compliant_percent": f"{calc_percent(compliant):.1f}",
            "partial_percent": f"{calc_percent(partial):.1f}",
            "gap_percent": f"{calc_percent(gap):.1f}",
            "not_evaluated_percent": f"{calc_percent(not_evaluated):.1f}",
            "not_applicable_percent": f"{calc_percent(not_applicable):.1f}",

            # Totals
            "total_bausteine": str(len(category_data)) if category_data else "0",
            "total_anforderungen": str(total),

            # Distribution list
            "distribution_list": self._generate_distribution_list(),

            # Executive summary
            "executive_summary": self._generate_executive_summary(
                score, compliant, partial, gap, total, schutzbedarf
            ),

            # Category results
            "category_results": self._generate_category_results(category_data),

            # Detailed findings
            "detailed_findings": self._generate_detailed_findings(detailed_findings),

            # Gap analysis
            "gap_analysis": self._generate_gap_analysis(gap_analysis),

            # Recommendations
            "recommendations": self._generate_recommendations(gap_analysis, score),

            # Action items
            "action_items": self._generate_action_items(gap_analysis),
        }

        return self.pdf_service.generate_report(
            "bsi_report.tex",
            data,
            f"BSI_Compliance_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

    def _generate_distribution_list(self) -> str:
        """Generate distribution list table rows."""
        rows = [
            "Informationssicherheitsbeauftragter & ISB & Vollzugriff \\\\",
            "Geschaeftsfuehrung & Management & Lesezugriff \\\\",
            "IT-Leitung & IT & Lesezugriff \\\\",
        ]
        return "\n\\hline\n".join(rows)

    def _generate_executive_summary(
        self,
        score: float,
        compliant: int,
        partial: int,
        gap: int,
        total: int,
        schutzbedarf: str
    ) -> str:
        """Generate executive summary text."""
        if score >= 80:
            assessment = (
                "Die Organisation zeigt einen hohen Grad an Konformitaet mit dem "
                "BSI IT-Grundschutz. Die implementierten Sicherheitsmassnahmen "
                "entsprechen den Anforderungen des gewaehlten Schutzbedarfs."
            )
        elif score >= 60:
            assessment = (
                "Die Organisation zeigt eine gute Basis-Konformitaet mit dem "
                "BSI IT-Grundschutz. Es bestehen jedoch Verbesserungspotenziale, "
                "die zeitnah adressiert werden sollten."
            )
        elif score >= 40:
            assessment = (
                "Die Organisation weist erhebliche Luecken in der Umsetzung des "
                "BSI IT-Grundschutz auf. Es wird dringend empfohlen, die "
                "identifizierten Massnahmen zeitnah umzusetzen."
            )
        else:
            assessment = (
                "Die Organisation weist kritische Maengel in der Informationssicherheit auf. "
                "Sofortige Massnahmen sind erforderlich, um ein Mindestmass an Sicherheit "
                "zu gewaehrleisten."
            )

        summary = (
            f"\\textbf{{Gesamtbewertung:}} {assessment}\n\n"
            f"Von insgesamt {total} bewerteten Anforderungen sind:\n"
            f"\\begin{{itemize}}\n"
            f"\\item {compliant} vollstaendig umgesetzt (konform)\n"
            f"\\item {partial} teilweise umgesetzt\n"
            f"\\item {gap} nicht umgesetzt (Luecken)\n"
            f"\\end{{itemize}}\n\n"
            f"Der Gesamtscore von \\textbf{{{score:.0f}\\%}} basiert auf dem "
            f"Schutzbedarf \\textbf{{{SCHUTZBEDARF_NAMES.get(schutzbedarf, schutzbedarf)}}}."
        )

        return summary

    def _generate_category_results(self, category_data: List[Dict[str, Any]]) -> str:
        """Generate category-wise results."""
        if not category_data:
            return "Keine Kategoriedaten verfuegbar."

        result = []
        for cat in category_data:
            kategorie = cat.get("kategorie", "")
            name = KATEGORIE_NAMES.get(kategorie, kategorie)
            total = cat.get("total", 0)
            compliant = cat.get("compliant", 0)
            partial = cat.get("partial", 0)
            gap = cat.get("gap", 0)
            score = cat.get("score_percent", 0)

            # Determine color based on score
            if score >= 80:
                color = "bsigreen"
            elif score >= 50:
                color = "bsiyellow"
            else:
                color = "bsired"

            section = f"""
\\subsection{{{kategorie} - {name}}}

\\begin{{center}}
\\scorebar{{{score:.0f}}}
\\end{{center}}

\\begin{{tabularx}}{{\\textwidth}}{{|l|c|c|c|c|}}
\\hline
\\rowcolor{{tableheader}}
\\textcolor{{white}}{{\\textbf{{Status}}}} & \\textcolor{{white}}{{\\textbf{{Anzahl}}}} & \\textcolor{{white}}{{\\textbf{{Prozent}}}} \\\\
\\hline
Konform & {compliant} & {(compliant/total*100) if total > 0 else 0:.1f}\\% \\\\
\\hline
Teilweise & {partial} & {(partial/total*100) if total > 0 else 0:.1f}\\% \\\\
\\hline
Luecke & {gap} & {(gap/total*100) if total > 0 else 0:.1f}\\% \\\\
\\hline
\\end{{tabularx}}
"""
            result.append(section)

        return "\n".join(result)

    def _generate_detailed_findings(
        self,
        findings: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Generate detailed findings section."""
        if not findings:
            return "Detaillierte Ergebnisse werden bei vollstaendiger Bewertung generiert."

        result = []
        for finding in findings[:20]:  # Limit to 20 findings
            baustein_id = finding.get("baustein_id", "")
            titel = finding.get("titel", "")
            status = finding.get("status", "")
            notes = finding.get("notes", "")

            status_display = STATUS_NAMES.get(status, status)

            entry = f"""
\\textbf{{{baustein_id}: {titel}}}\\\\
Status: {status_display}\\\\
{f'Anmerkungen: {notes}' if notes else ''}
\\vspace{{0.3cm}}
"""
            result.append(entry)

        return "\n".join(result)

    def _generate_gap_analysis(
        self,
        gaps: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Generate gap analysis section."""
        if not gaps:
            return (
                "\\textcolor{bsigreen}{Keine kritischen Luecken identifiziert.}\n\n"
                "Die Organisation erfuellt die wesentlichen Anforderungen des "
                "BSI IT-Grundschutz."
            )

        result = [
            "\\begin{longtable}{|p{2.5cm}|p{5cm}|p{2cm}|p{4cm}|}",
            "\\hline",
            "\\rowcolor{tableheader}",
            "\\textcolor{white}{\\textbf{Anforderung}} & "
            "\\textcolor{white}{\\textbf{Beschreibung}} & "
            "\\textcolor{white}{\\textbf{Prioritaet}} & "
            "\\textcolor{white}{\\textbf{Empfehlung}} \\\\",
            "\\hline",
            "\\endhead"
        ]

        for gap in gaps[:15]:  # Limit to 15 gaps
            anforderung_id = gap.get("anforderung_id", "")
            beschreibung = gap.get("beschreibung", "")[:100]
            priority = gap.get("priority", 3)
            recommendation = gap.get("recommendation", "")[:150]

            priority_text = {1: "Kritisch", 2: "Hoch", 3: "Mittel", 4: "Niedrig"}.get(
                priority, "Mittel"
            )

            result.append(
                f"{anforderung_id} & {beschreibung} & {priority_text} & {recommendation} \\\\"
            )
            result.append("\\hline")

        result.append("\\end{longtable}")

        return "\n".join(result)

    def _generate_recommendations(
        self,
        gaps: Optional[List[Dict[str, Any]]],
        score: float
    ) -> str:
        """Generate recommendations section."""
        recommendations = []

        if score < 50:
            recommendations.append(
                "\\item \\textbf{Sofortmassnahmen:} Priorisieren Sie die Behebung "
                "kritischer Luecken in den Bereichen Detektion und Reaktion (DER) "
                "sowie Sicherheitsmanagement (ISMS)."
            )

        if score < 80:
            recommendations.append(
                "\\item \\textbf{Mittelfristige Massnahmen:} Erstellen Sie einen "
                "detaillierten Umsetzungsplan fuer alle identifizierten Luecken "
                "mit klaren Verantwortlichkeiten und Terminen."
            )

        recommendations.append(
            "\\item \\textbf{Kontinuierliche Verbesserung:} Fuehren Sie regelmaessige "
            "Ueberpruefungen durch (mindestens jaehrlich) und aktualisieren Sie "
            "die Dokumentation entsprechend."
        )

        if gaps and len(gaps) > 5:
            recommendations.append(
                "\\item \\textbf{Ressourcen:} Erwaegen Sie die Einbindung externer "
                "Berater zur Beschleunigung der Umsetzung bei komplexen Anforderungen."
            )

        return "\\begin{itemize}\n" + "\n".join(recommendations) + "\n\\end{itemize}"

    def _generate_action_items(
        self,
        gaps: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Generate action items table rows."""
        if not gaps:
            return (
                "\\rowcolor{tablerow1}\n"
                "-- & Keine offenen Massnahmen & Abgeschlossen & -- & -- \\\\"
            )

        rows = []
        for i, gap in enumerate(gaps[:10]):  # Limit to 10 action items
            priority = gap.get("priority", 3)
            anforderung_id = gap.get("anforderung_id", "")
            recommendation = gap.get("recommendation", "Massnahme definieren")[:80]

            priority_text = {1: "Kritisch", 2: "Hoch", 3: "Mittel", 4: "Niedrig"}.get(
                priority, "Mittel"
            )

            row_color = "tablerow1" if i % 2 == 0 else "tablerow2"

            rows.append(
                f"\\rowcolor{{{row_color}}}\n"
                f"{priority_text} & {recommendation} & {anforderung_id} & "
                f"Zuzuweisen & Offen \\\\"
            )

        return "\n\\hline\n".join(rows)
