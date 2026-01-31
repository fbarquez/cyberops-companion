# Internationalization (i18n)

**Status:** ✅ Implemented
**Date:** 2026-01-31
**Location:** `apps/web/src/i18n/`

---

## Overview

Multi-language support using `next-intl` for the Next.js frontend. Currently supports English (EN) and German (DE).

---

## Supported Languages

| Language | Code | Status |
|----------|------|--------|
| English | `en` | ✅ Complete |
| German | `de` | ✅ Complete |

---

## Translation Structure

```
apps/web/src/i18n/
├── config.ts           # i18n configuration
├── request.ts          # Server-side i18n
└── messages/
    ├── en.json         # English translations
    └── de.json         # German translations
```

---

## Translated Modules

| Module | Namespace | Status |
|--------|-----------|--------|
| Common | `common` | ✅ |
| Navigation | `nav` | ✅ |
| Dashboard | `dashboard` | ✅ |
| Incidents | `incidents` | ✅ |
| SOC (Alerts/Cases) | `soc` | ✅ |
| Vulnerabilities | `vulnerabilities` | ✅ |
| Risks | `risks` | ✅ |
| Threats | `threats` | ✅ |
| TPRM | `tprm` | ✅ |
| Compliance | `compliance` | ✅ |
| CMDB | `cmdb` | ✅ |
| Integrations | `integrations` | ✅ |
| Reporting | `reporting` | ✅ |
| Users | `users` | ✅ |
| Notifications | `notifications` | ✅ |
| Settings | `settings` | ✅ |
| Simulation | `simulation` | ✅ |
| Lessons Learned | `lessons` | ✅ |
| Templates | `templates` | ✅ |
| Navigator | `navigator` | ✅ |
| Playbook | `playbook` | ✅ |

---

## Usage

### In Components

```tsx
import { useTranslations } from 'next-intl';

export function MyComponent() {
  const t = useTranslations('incidents');

  return (
    <div>
      <h1>{t('title')}</h1>
      <p>{t('description')}</p>
      <button>{t('actions.create')}</button>
    </div>
  );
}
```

### With Parameters

```tsx
const t = useTranslations('common');

// Translation: "Showing {count} of {total} items"
t('pagination.showing', { count: 10, total: 100 });
```

### Pluralization

```tsx
// Translation:
// "one": "{count} item"
// "other": "{count} items"
t('items', { count: 5 }); // "5 items"
```

---

## Adding New Translations

1. Add key to `messages/en.json`:
```json
{
  "myModule": {
    "title": "My Module",
    "description": "Description here"
  }
}
```

2. Add same key to `messages/de.json`:
```json
{
  "myModule": {
    "title": "Mein Modul",
    "description": "Beschreibung hier"
  }
}
```

3. Use in component:
```tsx
const t = useTranslations('myModule');
return <h1>{t('title')}</h1>;
```

---

## Translation Key Structure

```json
{
  "moduleName": {
    "title": "Page Title",
    "description": "Page description",
    "tabs": {
      "overview": "Overview",
      "details": "Details"
    },
    "actions": {
      "create": "Create",
      "edit": "Edit",
      "delete": "Delete"
    },
    "table": {
      "columns": {
        "name": "Name",
        "status": "Status"
      }
    },
    "form": {
      "fields": {
        "name": "Name",
        "email": "Email"
      },
      "placeholders": {
        "name": "Enter name..."
      },
      "validation": {
        "required": "This field is required"
      }
    },
    "messages": {
      "success": "Operation successful",
      "error": "An error occurred"
    }
  }
}
```

---

## Language Switching

The language is determined by:
1. URL path prefix (`/en/dashboard`, `/de/dashboard`)
2. Browser preference (fallback)
3. Default locale (`en`)

---

## Files

| File | Purpose |
|------|---------|
| `i18n/config.ts` | Locale configuration |
| `i18n/request.ts` | Server request handling |
| `i18n/messages/en.json` | English translations |
| `i18n/messages/de.json` | German translations |
| `middleware.ts` | Locale routing |

---

## Adding New Language

1. Add locale to `config.ts`:
```ts
export const locales = ['en', 'de', 'es'] as const;
```

2. Create `messages/es.json` with all translations

3. Update middleware if needed

---

## Notes

- All user-facing text should use translations
- Keep translation keys consistent across languages
- Use nested objects for organization
- Avoid hardcoded strings in components
