# Contributing to CyberOps Companion

Thank you for your interest in contributing to CyberOps Companion! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cyberops-companion.git
   cd cyberops-companion
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/cyberops-companion.git
   ```

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

When filing a bug report, include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Screenshots (if applicable)
- Environment details (OS, browser, Docker version, etc.)

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature has already been requested
- Provide a clear use case
- Explain why this feature would benefit other users

### Contributing Code

1. Check the [issues](../../issues) for tasks labeled `good first issue` or `help wanted`
2. Comment on the issue to let others know you're working on it
3. Fork and create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.12+ (for backend development)
- pnpm (recommended) or npm

### Quick Start with Docker

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Local Development

**Backend:**
```bash
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

**Frontend:**
```bash
cd apps/web
pnpm install
pnpm dev
```

### Running Tests

```bash
# Backend tests
cd apps/api
pytest tests/ -v

# Frontend tests
cd apps/web
pnpm test
```

## Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our style guidelines

3. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "feat: add new feature description"
   ```

   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** against the `main` branch

6. **Address review feedback** if requested

### PR Requirements

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally
- [ ] New features include tests
- [ ] Documentation is updated if needed
- [ ] Commit messages follow conventional commits

## Style Guidelines

### Python (Backend)

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Use async/await for database operations
- Run `ruff check` before committing

### TypeScript (Frontend)

- Follow the existing code style
- Use TypeScript strict mode
- Use functional components with hooks
- Run `pnpm lint` before committing

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests when relevant

## Project Structure

```
cyberops-companion/
├── apps/
│   ├── api/          # FastAPI Backend
│   │   └── src/
│   │       ├── api/        # API endpoints
│   │       ├── models/     # SQLAlchemy models
│   │       ├── schemas/    # Pydantic schemas
│   │       └── services/   # Business logic
│   │
│   └── web/          # Next.js Frontend
│       ├── app/            # App Router pages
│       ├── components/     # React components
│       └── lib/            # Utilities
│
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## License

By contributing to CyberOps Companion, you agree that your contributions will be licensed under the AGPL-3.0 License.

## Questions?

If you have questions, feel free to:
- Open a [Discussion](../../discussions)
- Check existing [Issues](../../issues)

Thank you for contributing!
