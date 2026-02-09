# Compliance Framework Sources

This document lists all official sources used for compliance frameworks in CyberOps Companion.

---

## Important Disclaimer

The compliance requirements in this application are:
- **Based on** official regulations and standards
- **Transcribed manually** into the codebase
- **Not automatically updated** when regulations change
- **Interpretations** in some cases (weights, priorities, sub-requirements)

For official compliance assessments, always refer to the original documents.

---

## EU Regulations

### DORA (Digital Operational Resilience Act)

| Resource | URL |
|----------|-----|
| **Regulation (EU) 2022/2554** | https://eur-lex.europa.eu/eli/reg/2022/2554/oj |
| EBA DORA RTS | https://www.eba.europa.eu/regulation-and-policy/operational-resilience |
| European Commission Overview | https://finance.ec.europa.eu/digital-finance/digital-operational-resilience-act-dora_en |
| EIOPA DORA Resources | https://www.eiopa.europa.eu/browse/digitalisation-and-cyber/dora_en |
| ESMA DORA Page | https://www.esma.europa.eu/policy-activities/digital-finance/dora |

**Application Date:** January 17, 2025
**Scope:** Financial entities (20+ types) in the EU
**Key Articles:** 5-45 covering 5 pillars

---

### NIS2 Directive

| Resource | URL |
|----------|-----|
| **Directive (EU) 2022/2555** | https://eur-lex.europa.eu/eli/dir/2022/2555/oj |
| ENISA NIS2 Resources | https://www.enisa.europa.eu/topics/cybersecurity-policy/nis-directive-new |
| European Commission Overview | https://digital-strategy.ec.europa.eu/en/policies/nis2-directive |
| NIS Cooperation Group | https://digital-strategy.ec.europa.eu/en/policies/nis-cooperation-group |

**Transposition Deadline:** October 17, 2024
**Application:** From October 18, 2024
**Scope:** Essential (Annex I) and Important (Annex II) entities
**Key Article:** Article 21 - Cybersecurity risk-management measures

---

### GDPR (General Data Protection Regulation)

| Resource | URL |
|----------|-----|
| **Regulation (EU) 2016/679** | https://eur-lex.europa.eu/eli/reg/2016/679/oj |
| EDPB Guidelines | https://edpb.europa.eu/our-work-tools/general-guidance/gdpr-guidelines-recommendations-best-practices_en |
| European Commission GDPR | https://commission.europa.eu/law/law-topic/data-protection_en |

**National Data Protection Authorities:**
| Country | Authority | URL |
|---------|-----------|-----|
| Germany | BfDI | https://www.bfdi.bund.de/ |
| France | CNIL | https://www.cnil.fr/ |
| UK | ICO | https://ico.org.uk/ |
| Spain | AEPD | https://www.aepd.es/ |
| Netherlands | AP | https://www.autoriteitpersoonsgegevens.nl/ |

**In Force Since:** May 25, 2018

---

## German Regulations

### KRITIS (Kritische Infrastrukturen)

| Resource | URL |
|----------|-----|
| **BSI-Gesetz (BSI Act)** | https://www.gesetze-im-internet.de/bsig_2009/ |
| **BSI-Kritisverordnung** | https://www.gesetze-im-internet.de/bsi-kritisv/ |
| BSI KRITIS Overview | https://www.bsi.bund.de/DE/Themen/KRITIS-und-regulierte-Unternehmen/Kritische-Infrastrukturen/kritische-infrastrukturen_node.html |
| UP KRITIS | https://www.bsi.bund.de/DE/Themen/KRITIS-und-regulierte-Unternehmen/UP-KRITIS/up-kritis_node.html |
| KRITIS Portal | https://www.kritis.bund.de/ |

**Sectors:** Energy, Water, Food, IT/Telecom, Health, Finance, Transport, Government
**Key Requirement:** BSI-Gesetz §8a - Security measures

---

### BSI IT-Grundschutz

| Resource | URL |
|----------|-----|
| **IT-Grundschutz Kompendium** | https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/IT-Grundschutz-Kompendium/it-grundschutz-kompendium_node.html |
| BSI Standards (200-x) | https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/BSI-Standards/bsi-standards_node.html |
| IT-Grundschutz Profiles | https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/IT-Grundschutz-Profile/it-grundschutz-profile_node.html |

**BSI Standards:**
- 200-1: Information Security Management Systems (ISMS)
- 200-2: IT-Grundschutz Methodology
- 200-3: Risk Analysis based on IT-Grundschutz
- 200-4: Business Continuity Management

**Edition 2023:** 111 Bausteine, ~1000+ Anforderungen
**Language:** German (official), English translations partial

---

## International Standards

### ISO/IEC 27001:2022

| Resource | URL |
|----------|-----|
| **ISO/IEC 27001:2022** (Purchase) | https://www.iso.org/standard/27001 |
| ISO/IEC 27002:2022 (Controls) | https://www.iso.org/standard/75652.html |
| ISO 27001 Overview | https://www.iso.org/isoiec-27001-information-security.html |
| ISO 27000 Family | https://www.iso.org/iso-27001-information-security.html |
| Certification Bodies | https://www.iso.org/certification.html |

**2022 Edition Changes:**
- 93 controls in Annex A (reduced from 114 in 2013)
- 4 control themes: Organizational, People, Physical, Technological
- 11 new controls added

**Note:** ISO standards are copyrighted. Full documents must be purchased.

---

### NIST Cybersecurity Framework 2.0

| Resource | URL |
|----------|-----|
| **NIST CSF 2.0** | https://www.nist.gov/cyberframework |
| CSF 2.0 Core (Excel/JSON) | https://www.nist.gov/document/csf-20-core-spreadsheet |
| CSF Reference Tool | https://csf.tools/ |
| NIST SP 800-53 Rev. 5 | https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final |
| Informative References | https://www.nist.gov/cyberframework/informative-references |

**CSF 2.0 Released:** February 26, 2024
**Functions:** GOVERN (new), IDENTIFY, PROTECT, DETECT, RESPOND, RECOVER
**Categories:** 22 | **Subcategories:** 106

**Note:** NIST CSF is a free, public US government framework.

---

### COBIT 2019

| Resource | URL |
|----------|-----|
| **ISACA COBIT 2019** | https://www.isaca.org/resources/cobit |
| COBIT 2019 Design Guide | https://www.isaca.org/resources/cobit/cobit-2019-design-guide |
| COBIT Implementation Guide | https://www.isaca.org/resources/cobit/cobit-2019-implementation-guide |
| COBIT Certifications | https://www.isaca.org/credentialing/cobit-certifications |

**Domains:** EDM, APO, BAI, DSS, MEA
**Objectives:** 40 governance and management objectives
**Capability Levels:** Based on ISO/IEC 33000 (SPICE)

**Note:** COBIT is a proprietary framework. Full documentation requires ISACA membership.

---

## Automotive Industry

### TISAX

| Resource | URL |
|----------|-----|
| **ENX Association** | https://www.enx.com/tisax/ |
| TISAX Documents | https://www.enx.com/tisax/tisax-documents/ |
| VDA ISA Catalog | https://www.vda.de/en/topics/information-security |
| Assessment Providers | https://www.enx.com/tisax/tisax-assessment-providers/ |
| TISAX Portal | https://portal.enx.com/ |

**Assessment Levels:**
- AL1: Normal protection needs
- AL2: High protection needs
- AL3: Very high protection needs

**Labels:** Information Security, Prototype Protection, Data Protection

**Note:** VDA ISA catalog requires VDA membership for full access.

---

## Cross-Framework Mapping

The application supports mapping controls across frameworks:

| Source | Maps To |
|--------|---------|
| NIS2 Art. 21 | ISO 27001 Annex A |
| DORA Art. 5-16 | ISO 27001, NIST CSF |
| BSI IT-Grundschutz | ISO 27001 |
| KRITIS §8a | NIS2, ISO 27001 |

**Mapping Sources:**
- ENISA NIS2 to ISO 27001 mapping
- DORA to ISO 27001 mapping guidance (ESAs)
- BSI IT-Grundschutz to ISO 27001 Kreuzreferenztabelle

---

## Keeping Data Current

Since compliance data is static, updates require:

1. **Monitor official sources** for regulation changes
2. **Review RTS/ITS** (Regulatory/Implementing Technical Standards)
3. **Update model files** with new requirements
4. **Run migrations** if database schema changes
5. **Update frontend** if UI changes needed

**Recommended Update Frequency:**
- EU Regulations: Annually or when RTS published
- ISO Standards: On new edition release
- NIST CSF: On version updates
- BSI IT-Grundschutz: Annually (new Kompendium edition)

---

## Contributing

To update compliance data:

1. Find the model file in `apps/api/src/models/`
2. Update requirements/controls based on official sources
3. Add source references in docstring
4. Update this documentation
5. Submit PR with links to official sources

---

## License and Copyright

- **EU Regulations:** Public domain (EUR-Lex)
- **ISO Standards:** Copyrighted by ISO
- **NIST CSF:** Public domain (US Government)
- **COBIT:** Copyrighted by ISACA
- **BSI IT-Grundschutz:** Creative Commons BY-ND (BSI)
- **TISAX/VDA ISA:** Copyrighted by VDA/ENX

This application uses publicly available information from these frameworks.
For official assessments, always obtain and refer to original documents.
