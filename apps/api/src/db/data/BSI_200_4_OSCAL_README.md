# BSI Standard 200-4 OSCAL Catalog

## Overview

This directory contains a machine-readable representation of **BSI Standard 200-4: Business Continuity Management** in [OSCAL](https://pages.nist.gov/OSCAL/) (Open Security Controls Assessment Language) format.

## File

- `bsi_200_4_catalog.json` - Complete BSI 200-4 catalog in OSCAL JSON format

## Structure

The catalog follows the OSCAL Catalog Model v1.1.2 and contains:

### Groups (Families)

| ID | Title (DE) | Title (EN) | Controls |
|----|------------|------------|----------|
| BCM-1 | BCMS-Rahmenwerk | BCMS Framework | 5 |
| BCM-2 | Business Impact Analysis | Business Impact Analysis | 6 |
| BCM-3 | Risikoanalyse | Risk Assessment | 4 |
| BCM-4 | Kontinuitätsstrategien | BC Strategies | 4 |
| BCM-5 | Notfallpläne | Emergency Plans | 7 |
| BCM-6 | Übungen und Tests | Exercises and Testing | 5 |
| BCM-7 | Pflege und Verbesserung | Maintenance and Improvement | 5 |
| BCM-8 | Krisenmanagement | Crisis Management | 4 |

**Total: 8 groups, 40 controls**

### Control Properties

Each control includes:
- `id` - Unique identifier (e.g., BCM-2.4)
- `title` / `title-en` - German and English titles
- `priority` - Requirement level: `must`, `should`, `informative`
- `iso22301-mapping` - Mapping to ISO 22301:2019 clauses
- `parts`:
  - `statement` - The requirement text
  - `guidance` - Implementation guidance
  - `assessment-objective` - Audit objectives

### Parameters

Parameterized values for organizational customization:
- Criticality levels
- Impact categories
- Time periods for BIA
- Threat categories
- Strategy types
- Exercise types

## ISO 22301 Mapping

The catalog includes mappings to ISO 22301:2019:

| BSI 200-4 | ISO 22301:2019 |
|-----------|----------------|
| BCM-1 | Clause 4, 5 (Context, Leadership) |
| BCM-2 | Clause 8.2.2 (BIA) |
| BCM-3 | Clause 8.2.3 (Risk Assessment) |
| BCM-4 | Clause 8.3 (BC Strategies) |
| BCM-5 | Clause 8.4 (BC Plans) |
| BCM-6 | Clause 8.5 (Exercise Programme) |
| BCM-7 | Clause 9, 10 (Evaluation, Improvement) |

## Usage

### Loading in Python

```python
import json

with open('bsi_200_4_catalog.json', 'r') as f:
    catalog = json.load(f)

# Access groups
for group in catalog['catalog']['groups']:
    print(f"{group['id']}: {group['title']}")
    for control in group.get('controls', []):
        print(f"  {control['id']}: {control['title']}")
```

### Validation

Validate against OSCAL schema:

```bash
# Using oscal-cli (https://github.com/usnistgov/oscal-cli)
oscal-cli catalog validate bsi_200_4_catalog.json
```

## License

This OSCAL representation is provided under **CC-BY-SA-4.0**.

The original BSI Standard 200-4 is published by the [Bundesamt für Sicherheit in der Informationstechnik (BSI)](https://www.bsi.bund.de).

## Disclaimer

This is a **community contribution**, not an official BSI product. While we strive for accuracy, always refer to the [official BSI publication](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/BSI_Standards/standard_200_4.html) for authoritative requirements.

## Contributing

Contributions welcome! Please:
1. Validate changes against OSCAL schema
2. Maintain bilingual (DE/EN) content
3. Update ISO 22301 mappings if applicable
4. Follow existing formatting conventions

## References

- [BSI Standard 200-4 (Official)](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/BSI-Standards/BSI-Standard-200-4-Business-Continuity-Management/bsi-standard-200-4_Business_Continuity_Management_node.html)
- [ISO 22301:2019](https://www.iso.org/standard/75106.html)
- [OSCAL Documentation](https://pages.nist.gov/OSCAL/)
- [BSI GitHub (Stand-der-Technik-Bibliothek)](https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek)

---

*Created: 2026-02-05*
*Version: 1.0.0*
