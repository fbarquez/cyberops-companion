# Contributing to ISOVA

Thank you for your interest in contributing to ISOVA! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Contributing Evidence Templates](#contributing-evidence-templates)
- [Code Style](#code-style)
- [Internationalization](#internationalization)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We expect all contributors to:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Docker and Docker Compose (optional but recommended)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/isova.git
cd isova

# Start database
docker-compose up -d postgres

# Backend setup
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run migrations
alembic upgrade head

# Start API server
uvicorn src.main:app --reload

# Frontend setup (new terminal)
cd apps/web
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd apps/api
pytest

# Frontend tests
cd apps/web
npm test

# All tests
make test
```

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Collect relevant information (version, OS, steps to reproduce)

When creating a bug report:
1. Use the bug report template
2. Provide clear reproduction steps
3. Include expected vs actual behavior
4. Attach screenshots if helpful

### Suggesting Features

Before suggesting a feature:
1. Check the roadmap and existing issues
2. Consider DACH compliance context (NIS2, ISO 27001, BSI)

When suggesting a feature:
1. Use the feature request template
2. Explain the use case clearly
3. Describe expected behavior
4. Consider impact on existing functionality

### Contributing Code

1. **Fork the repository** and create your branch from `main`
2. **Create a feature branch:**
   ```bash
   git checkout -b feat/amazing-feature
   # or
   git checkout -b fix/bug-description
   ```
3. **Make your changes** following our code style
4. **Add tests** for new functionality
5. **Run the test suite** to ensure nothing is broken
6. **Commit with conventional commits** (see below)
7. **Push and create a Pull Request**

## Contributing Evidence Templates

Evidence templates are crucial for ISOVA's usability. Here's how to contribute:

### Template Location

Templates are stored in `templates/evidence/` as YAML files.

### Template Structure

```yaml
# templates/evidence/training_attestation.yaml
id: training_attestation
version: 1
category: awareness

name:
  en: "Training Attestation"
  de: "Schulungsbestätigung"

description:
  en: "Confirm completion of security training"
  de: "Bestätigung einer durchgeführten Sicherheitsschulung"

applicable_controls:
  - nis2:M07
  - iso27001:A.6.3
  - bsi:ORP.3

fields:
  - name: training_date
    type: date
    required: true
    label:
      en: "Training Date"
      de: "Schulungsdatum"

  - name: participants
    type: number
    required: true
    min: 1
    label:
      en: "Number of Participants"
      de: "Anzahl Teilnehmer"

  - name: topic
    type: select
    required: true
    options:
      - value: phishing
        label:
          en: "Phishing Awareness"
          de: "Phishing-Erkennung"
      - value: password
        label:
          en: "Password Security"
          de: "Passwortsicherheit"

  - name: provider
    type: text
    required: false
    label:
      en: "Training Provider"
      de: "Schulungsanbieter"

basis_options:
  - observation
  - document
  - sample

default_validity_days: 365

disclaimer:
  en: "This attestation is internal documentation and does not replace formal audit evidence."
  de: "Diese Bestätigung ist eine interne Dokumentation und ersetzt keinen formalen Auditnachweis."
```

### Template Guidelines

1. **Both languages required** - All user-facing text must be in EN and DE
2. **Link to controls** - Map to NIS2, ISO 27001, and/or BSI controls
3. **Include disclaimer** - Legal disclaimer is mandatory for attestations
4. **Specify basis options** - Which confirmation basis types apply
5. **Set validity** - Define default validity period

## Code Style

### Python (Backend)

We follow PEP 8 with these additions:

```python
# Use type hints everywhere
from uuid import UUID
from datetime import datetime

async def get_evidence(evidence_id: UUID) -> Evidence | None:
    """Retrieve evidence by ID.

    Args:
        evidence_id: UUID of the evidence to retrieve

    Returns:
        Evidence object if found, None otherwise
    """
    ...

# Async/await for all database operations
async def create_evidence(db: AsyncSession, data: EvidenceCreate) -> Evidence:
    evidence = Evidence(**data.model_dump())
    db.add(evidence)
    await db.commit()
    return evidence
```

**Formatting:**
```bash
black apps/api/src
isort apps/api/src
flake8 apps/api/src
mypy apps/api/src
```

### TypeScript (Frontend)

```typescript
// Use TypeScript interfaces
interface Evidence {
  id: string;
  title: string;
  status: EvidenceStatus;
}

// Use React functional components
export function EvidenceCard({ evidence }: { evidence: Evidence }) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardTitle>{evidence.title}</CardTitle>
      <Badge>{t(`evidence.status.${evidence.status}`)}</Badge>
    </Card>
  );
}
```

**Formatting:**
```bash
npm run lint
npm run format
```

### Commit Messages

We use [Conventional Commits](https://conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Scopes:** `api`, `web`, `evidence`, `framework`, `i18n`, `docker`

**Examples:**
```bash
feat(evidence): add attestation basis field
fix(api): correct hash calculation for unicode
docs(readme): update installation instructions
```

## Internationalization

ISOVA supports German (de) and English (en). **German is primary** for the DACH market.

### Adding Translations

1. Add English strings to `apps/web/locales/en.json`:

```json
{
  "evidence": {
    "create": "Create Evidence",
    "confirm": "Confirm",
    "basis": {
      "observation": "Observation",
      "document": "Document"
    }
  }
}
```

2. Add German translations to `apps/web/locales/de.json`:

```json
{
  "evidence": {
    "create": "Nachweis erstellen",
    "confirm": "Bestätigen",
    "basis": {
      "observation": "Beobachtung",
      "document": "Dokument"
    }
  }
}
```

### Translation Guidelines

| English | German |
|---------|--------|
| Evidence | Nachweis |
| Attestation | Bestätigung |
| Measure | Maßnahme |
| Control | Kontrolle / Maßnahme |
| Assessment | Bewertung |

- **Use formal German** - Always "Sie", never "du"
- **No machine translation** - Human review required
- **Keep UI context** - Button labels short, descriptions can be longer

## Pull Request Process

### Before Submitting

1. Update documentation if you changed behavior
2. Add tests for new functionality
3. Run full test suite locally
4. Update CHANGELOG.md for user-facing changes
5. Check both EN and DE translations

### Creating the PR

1. Fill out the PR template completely
2. Link related issues (Fixes #123)
3. Request review from appropriate team members

### Review Criteria

- [ ] Code quality and style consistency
- [ ] Test coverage for new code
- [ ] Documentation updates
- [ ] i18n completeness (EN + DE)
- [ ] Compliance impact assessment
- [ ] Security considerations

## Project Structure

```
isova/
├── apps/
│   ├── api/                 # FastAPI Backend
│   │   └── src/
│   │       ├── api/         # API endpoints
│   │       ├── models/      # SQLAlchemy models
│   │       ├── services/    # Business logic
│   │       └── frameworks/  # NIS2, ISO, BSI definitions
│   │
│   └── web/                 # Next.js Frontend
│       ├── app/             # App Router pages
│       ├── components/      # React components
│       └── locales/         # i18n translations
│
├── docs/                    # Documentation
├── examples/                # Demo datasets
├── templates/               # Evidence templates
└── .github/                 # PR templates, workflows
```

## License

By contributing to ISOVA, you agree that your contributions will be licensed under the AGPL-3.0 License.

## Questions?

- [GitHub Discussions](https://github.com/your-org/isova/discussions)
- [GitHub Issues](https://github.com/your-org/isova/issues)
- Security issues: See [SECURITY.md](./SECURITY.md)

Thank you for contributing to ISOVA!
