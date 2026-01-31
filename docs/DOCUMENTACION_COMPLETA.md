# CyberOps Companion - Documentacion Completa

**Fecha de actualizacion:** 2026-02-01
**Version actual:** 0.10.0
**Fase actual:** Fase 3 - Enterprise Features (en progreso)

---

## Indice

1. [Que es CyberOps Companion](#1-que-es-cyberops-companion)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Estado Actual y Fases](#3-estado-actual-y-fases)
4. [Funcionalidades Implementadas](#4-funcionalidades-implementadas)
5. [Decisiones de Diseno](#5-decisiones-de-diseno)
6. [Estructura del Proyecto](#6-estructura-del-proyecto)
7. [Proximos Pasos](#7-proximos-pasos)

---

## 1. Que es CyberOps Companion

### Descripcion General

CyberOps Companion es una **plataforma integral de operaciones de ciberseguridad** disenada para centralizar y automatizar las funciones criticas de un equipo de seguridad. Integra multiples modulos que cubren todo el ciclo de vida de la seguridad:

| Modulo | Proposito |
|--------|-----------|
| **Incident Response** | Gestion completa de incidentes de seguridad |
| **SOC Operations** | Triaje de alertas, gestion de casos e investigaciones |
| **Vulnerability Management** | Seguimiento de CVEs, integracion con NVD |
| **Risk Management** | Registro de riesgos y evaluaciones |
| **TPRM** | Gestion de riesgos de terceros (proveedores) |
| **Compliance** | Frameworks de cumplimiento y auditorias |
| **CMDB** | Base de datos de configuracion de activos |
| **Threat Intelligence** | Catalogo de amenazas, MITRE ATT&CK |
| **Reporting & Analytics** | Dashboards, metricas, reportes automatizados |

### Por que existe este proyecto

Las organizaciones enfrentan multiples herramientas fragmentadas para gestionar su seguridad. CyberOps Companion unifica estas funciones en una sola plataforma, eliminando silos de informacion y mejorando la eficiencia operativa del equipo de seguridad.

---

## 2. Arquitectura del Sistema

### Stack Tecnologico

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  Next.js 14 + React + TypeScript + Tailwind CSS + shadcn/ui    │
│  Zustand (estado) + React Query (datos) + Recharts (graficos)   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND API                               │
│  FastAPI (Python 3.11) + SQLAlchemy (async) + Pydantic         │
│  JWT Auth + RBAC + WebSocket                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌─────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │    Redis    │  │  Celery Worker  │
│   (Database)    │  │   (Cache)   │  │ (Background)    │
└─────────────────┘  └─────────────┘  └─────────────────┘
```

### Por que estas tecnologias

| Tecnologia | Razon de eleccion |
|------------|-------------------|
| **FastAPI** | Framework moderno, async nativo, documentacion automatica OpenAPI, validacion con Pydantic |
| **Next.js** | SSR/SSG, App Router moderno, excelente DX, ecosistema React maduro |
| **PostgreSQL** | Base de datos robusta, soporte JSON, extensiones (trigram para busqueda) |
| **Redis** | Cache rapido, broker para Celery, sesiones WebSocket |
| **Celery** | Tareas en background sin bloquear API, colas separadas por prioridad |
| **Tailwind + shadcn/ui** | Desarrollo rapido de UI, componentes accesibles, tematizacion facil |

### Despliegue con Docker

```yaml
services:
  api:        # FastAPI backend
  web:        # Next.js frontend
  db:         # PostgreSQL
  redis:      # Redis
  celery:     # Celery worker
  celery-beat: # Scheduled tasks
```

---

## 3. Estado Actual y Fases

### Resumen de Progreso

| Fase | Nombre | Estado | Completitud |
|------|--------|--------|-------------|
| 0 | Foundation | ✅ Completa | 100% |
| 1 | Enhanced Features | ✅ Completa | 100% |
| 2 | Advanced Features | ✅ Completa | 100% |
| 3 | Enterprise Features | 🔄 En Progreso | ~40% |

### Fase Actual: Fase 3 - Enterprise Features

**Completado en Fase 3:**
- ✅ Audit Logging (Sistema completo de auditoria)
- ✅ SSO/SAML Integration (OAuth2/OIDC con Google, Microsoft, Okta)

**Pendiente en Fase 3:**
- 🔲 Multi-tenancy (soporte multi-organizacion)
- 🔲 API Rate Limiting (proteccion contra abuso)

### Linea de Tiempo del Proyecto

```
2026-01-30  │ Fase 0 - Inicio del proyecto, rename de IR Companion
            │
2026-01-31  │ Fase 0 - i18n, Email Service, NVD API, RBAC
            │ Fase 1 - Celery, Landing Page, Onboarding, UX Patterns
            │ Fase 2 - WebSocket, File Uploads, Analytics, Mobile Responsive
            │ Fase 3 - Audit Logging
            │
2026-02-01  │ Fase 3 - SSO/SAML Integration (OAuth2/OIDC)
            │
Futuro      │ Fase 3 - Multi-tenancy, Rate Limiting
            │ Fase 2C - ML/Predictive Analytics (cuando haya datos)
```

---

## 4. Funcionalidades Implementadas

### 4.1 Sistema de Autenticacion

#### JWT con Access/Refresh Tokens

**Que es:** Sistema de autenticacion basado en JSON Web Tokens con tokens de acceso de corta duracion y tokens de refresco de larga duracion.

**Por que se hizo asi:**
- Los JWT son stateless, no requieren consultar la base de datos en cada request
- El token de acceso corto (15 min) limita el dano si es comprometido
- El refresh token permite mantener la sesion sin re-autenticar constantemente

**Archivos clave:**
- `apps/api/src/services/auth_service.py` - Logica de autenticacion
- `apps/api/src/api/v1/auth.py` - Endpoints /login, /register, /refresh
- `apps/web/stores/auth-store.ts` - Estado de autenticacion en frontend

---

### 4.2 SSO/SAML Integration (OAuth2/OIDC)

**Que es:** Permite a usuarios autenticarse usando su cuenta corporativa de Google Workspace, Microsoft Entra ID (Azure AD) o Okta.

**Por que se implemento:**
- Las empresas necesitan integrar con su proveedor de identidad existente
- Reduce friccion para usuarios (un solo login para todo)
- Mejora seguridad (MFA del proveedor, politicas centralizadas)
- Elimina necesidad de gestionar contrasenas adicionales

**Como funciona el flujo OAuth2:**

```
1. Usuario clic "Sign in with Google"
         │
         ▼
2. Frontend → GET /api/v1/auth/sso/google/authorize
         │
         ▼
3. Backend genera state token (CSRF protection)
   y retorna URL de autorizacion de Google
         │
         ▼
4. Redirect a Google → Usuario se autentica
         │
         ▼
5. Google redirect → /auth/callback?code=XXX&state=YYY
         │
         ▼
6. Frontend → POST /api/v1/auth/sso/google/callback
         │
         ▼
7. Backend: valida state, intercambia code por tokens,
   obtiene info del usuario, crea/vincula cuenta
         │
         ▼
8. Backend retorna JWT → Frontend guarda y redirige
```

**Por que se uso state token:**
- Proteccion contra CSRF (Cross-Site Request Forgery)
- Sin el state, un atacante podria iniciar el flujo OAuth2 en nombre de la victima
- Token aleatorio de 32 bytes, uso unico, expira en 10 minutos

**JIT (Just-in-Time) Provisioning:**
- Si el usuario no existe, se crea automaticamente
- Reduce carga administrativa (no hay que crear usuarios manualmente)
- Rol por defecto configurable (`SSO_DEFAULT_ROLE`)
- Validacion de dominios permitidos (`SSO_ALLOWED_DOMAINS`)

**Archivos clave:**
- `apps/api/src/models/sso.py` - Modelos SSOProvider y SSOState
- `apps/api/src/services/sso_service.py` - Logica OAuth2 completa
- `apps/api/src/api/v1/sso.py` - Endpoints SSO
- `apps/web/app/(auth)/callback/page.tsx` - Manejo de callback
- `apps/web/components/auth/sso-buttons.tsx` - Botones SSO en login

**Documentacion:** [docs/features/SSO_SAML.md](./features/SSO_SAML.md)

---

### 4.3 Sistema de Audit Logging

**Que es:** Registro completo de todas las acciones de usuario para cumplimiento normativo, analisis forense y monitoreo de seguridad.

**Por que se implemento:**
- Requerimiento de cumplimiento (SOC 2, ISO 27001, GDPR)
- Capacidad de investigar incidentes de seguridad internos
- Detectar comportamiento anomalo de usuarios
- Responsabilidad y transparencia

**Que se registra:**
- Logins exitosos y fallidos
- Creacion, modificacion, eliminacion de recursos
- Cambios de configuracion
- Exportaciones de datos
- Accesos a informacion sensible

**Componentes:**

| Componente | Archivo | Funcion |
|------------|---------|---------|
| AuditService | `services/audit_service.py` | log_action(), list_logs(), export_logs() |
| Audit Decorator | `utils/audit_decorator.py` | Decorador para logging automatico |
| Audit API | `api/v1/audit.py` | Endpoints de consulta y exportacion |
| Audit Page | `app/(dashboard)/audit/page.tsx` | UI con filtros, tabla, exportacion |

**Seguridad del audit log:**
- Datos sensibles (passwords, tokens) se filtran automaticamente
- Severidad auto-generada segun tipo de accion
- Solo admins pueden exportar logs
- Logs son inmutables (no se pueden editar o borrar)

**Documentacion:** [docs/features/AUDIT_LOGGING.md](./features/AUDIT_LOGGING.md)

---

### 4.4 Sistema de Analytics Avanzado

**Que es:** Dashboards interactivos con graficos de tendencias, distribuciones, heatmaps, security score y metricas SLA.

**Por que se implemento:**
- Los ejecutivos necesitan visibilidad del estado de seguridad
- Los analistas necesitan identificar tendencias y patrones
- Cumplimiento de SLAs requiere metricas precisas
- Toma de decisiones basada en datos

**Componentes del Security Score:**

| Componente | Peso | Calculo |
|------------|------|---------|
| Vulnerabilities | 25% | -15 por critica, -5 por alta, -1 por media |
| Incidents | 20% | -20 por incidente critico activo |
| Compliance | 20% | Basado en estado de frameworks |
| Risks | 15% | -10 por riesgo critico no mitigado |
| SOC Operations | 10% | -15 por alerta critica sin atender |
| Patch Compliance | 10% | % de parches dentro de SLA |

**SLA Targets (configurables):**

| Severidad | Respuesta | Remediacion |
|-----------|-----------|-------------|
| Critical | 15 min | 1 dia |
| High | 1 hora | 7 dias |
| Medium | 4 horas | 30 dias |
| Low | 8 horas | 90 dias |

**Tipos de graficos implementados:**
- Line/Area charts (tendencias temporales)
- Bar charts (distribuciones)
- Pie/Donut charts (proporciones)
- Risk Heatmap 5x5 (matriz impacto/probabilidad)
- Sparklines (indicadores inline)
- Gauge (security score)

**Archivos clave:**
- `apps/api/src/services/analytics_service.py` - Tendencias, distribuciones
- `apps/api/src/services/security_score_service.py` - Calculo de score
- `apps/api/src/services/sla_service.py` - Metricas SLA
- `apps/api/src/services/analyst_metrics_service.py` - Performance de analistas
- `apps/web/components/dashboard/charts/` - Componentes de graficos
- `apps/web/hooks/useAnalytics.ts` - Hooks de React Query

**Documentacion:** [docs/ANALYTICS.md](./ANALYTICS.md)

---

### 4.5 WebSocket Notifications

**Que es:** Sistema de notificaciones en tiempo real usando WebSocket.

**Por que WebSocket y no polling:**
- Menor latencia (instantaneo vs cada N segundos)
- Menor carga en servidor (conexion persistente vs requests repetidos)
- Mejor experiencia de usuario

**Como funciona:**

```
┌─────────────────┐         ┌─────────────────┐
│    Frontend     │ ──WS──► │     Backend     │
│  (Browser)      │ ◄──WS── │    (FastAPI)    │
│                 │         │                 │
│ useNotification │         │ ConnectionMgr   │
│    WebSocket()  │         │                 │
└─────────────────┘         └─────────────────┘
         │                           │
         │                           │
    Reconexion               Broadcast a todos
    automatica               los usuarios o
    si se pierde             usuario especifico
```

**Caracteristicas:**
- Autenticacion JWT via query parameter
- Soporte multiples conexiones por usuario (tabs/dispositivos)
- Reconexion automatica con backoff exponencial
- Ping/pong keepalive (30s)
- Limpieza automatica de conexiones muertas

**Documentacion:** [docs/features/WEBSOCKET_NOTIFICATIONS.md](./features/WEBSOCKET_NOTIFICATIONS.md)

---

### 4.6 File Upload System

**Que es:** Sistema de adjuntos para incidentes, casos, vulnerabilidades con verificacion de integridad.

**Por que se implemento:**
- Evidencia digital es crucial en investigaciones
- Screenshots, logs, PCAPs necesitan asociarse a entidades
- Verificacion de integridad para cadena de custodia

**Caracteristicas:**
- Drag-and-drop con preview
- Multiples backends: local filesystem o S3/MinIO
- Hash SHA-256 para verificacion de integridad
- Deteccion de duplicados
- Categorias: evidence, screenshot, log_file, pcap, document, other
- Validacion de extensiones y tamano

**Flujo de subida:**

```
1. Usuario arrastra archivo al dropzone
         │
         ▼
2. Frontend valida extension y tamano
         │
         ▼
3. POST /api/v1/attachments/upload/{entity_type}/{entity_id}
         │
         ▼
4. Backend calcula SHA-256, verifica duplicado
         │
         ▼
5. Guarda en storage (local/S3), crea registro en DB
         │
         ▼
6. Retorna metadata incluyendo hash
```

**Documentacion:** [docs/features/FILE_UPLOADS.md](./features/FILE_UPLOADS.md)

---

### 4.7 Mobile Responsive

**Que es:** Adaptacion completa de la UI para dispositivos moviles y tablets.

**Por que se implemento:**
- Analistas a veces trabajan desde movil (on-call, emergencias)
- Ejecutivos revisan dashboards desde tablets
- Mejora accesibilidad general

**Estrategia de breakpoints:**

| Breakpoint | Pixeles | Uso |
|------------|---------|-----|
| Default | < 768px | Mobile: drawer sidebar, single column, cards en vez de tablas |
| `md:` | >= 768px | Tablet/Desktop: sidebar fijo, 2 columnas, tablas completas |
| `lg:` | >= 1024px | Desktop grande: mas columnas, layouts mas amplios |

**Cambios principales:**
- Sidebar se convierte en drawer (Sheet component)
- Header con hamburger menu en mobile
- Tablas ocultan columnas menos importantes en mobile
- Forms cambian de 2 columnas a 1 en mobile
- Dialogs se ajustan al viewport con scroll

**Documentacion:** [docs/features/MOBILE_RESPONSIVE.md](./features/MOBILE_RESPONSIVE.md)

---

### 4.8 Celery Background Tasks

**Que es:** Sistema de tareas en background para operaciones lentas o programadas.

**Por que Celery:**
- No bloquea la API mientras ejecuta tareas lentas
- Permite reintentos automaticos en caso de fallo
- Colas separadas por prioridad
- Soporte para tareas programadas (beat)

**Tareas implementadas:**
- `execute_vulnerability_scan` - Ejecuta escaneos en background
- `sync_nvd_updates` - Sincroniza CVEs de NVD (programado)
- `send_notification_async` - Envia notificaciones sin bloquear
- `cleanup_old_notifications` - Limpieza periodica

**Colas:**
- `default` - Tareas generales
- `scans` - Escaneos (pueden ser lentos)
- `notifications` - Notificaciones (deben ser rapidas)

**Documentacion:** [docs/features/CELERY_TASKS.md](./features/CELERY_TASKS.md)

---

### 4.9 Internacionalizacion (i18n)

**Que es:** Soporte multi-idioma (actualmente Ingles y Aleman).

**Por que:**
- CyberOps Companion esta pensado para uso global
- Empresas multinacionales necesitan interfaces en idioma local
- Aleman fue el primer idioma adicional por demanda

**Como funciona:**
- Archivo `translations.ts` con todas las cadenas
- Hook `useTranslations()` para acceder a traducciones
- Cambio de idioma guardado en localStorage
- Namespace structure para organizacion

**Documentacion:** [docs/features/I18N_TRANSLATIONS.md](./features/I18N_TRANSLATIONS.md)

---

### 4.10 NVD API Integration

**Que es:** Integracion con la National Vulnerability Database (NVD) de NIST.

**Por que:**
- Enriquecimiento automatico de vulnerabilidades con datos oficiales
- CVSS scores, vectores de ataque, referencias
- EPSS (probabilidad de explotacion)
- KEV (vulnerabilidades explotadas conocidas por CISA)

**Documentacion:** [docs/features/NVD_API.md](./features/NVD_API.md)

---

### 4.11 Email Service

**Que es:** Servicio de envio de emails para notificaciones.

**Caracteristicas:**
- SMTP asincrono (no bloquea)
- Templates HTML con Jinja2
- Estilos responsive
- Colores segun prioridad

**Documentacion:** [docs/features/EMAIL_SERVICE.md](./features/EMAIL_SERVICE.md)

---

### 4.12 Role-Based Access Control (RBAC)

**Que es:** Control de acceso basado en roles.

**Roles definidos:**
| Rol | Permisos |
|-----|----------|
| `admin` | Todo |
| `manager` | Crear/editar la mayoria, reportes |
| `lead` | Crear/editar en su area |
| `analyst` | Lectura y operaciones basicas |

**Documentacion:** [docs/features/ROLE_BASED_ACCESS.md](./features/ROLE_BASED_ACCESS.md)

---

### 4.13 Landing Page

**Que es:** Pagina de presentacion para usuarios no autenticados.

**Secciones:**
- Hero con propuesta de valor
- Features principales (6)
- Todos los modulos (10)
- Call-to-action

**Documentacion:** [docs/features/LANDING_PAGE.md](./features/LANDING_PAGE.md)

---

### 4.14 Onboarding Flow

**Que es:** Wizard de 5 pasos para nuevos usuarios.

**Pasos:**
1. Welcome - Introduccion
2. Organization - Perfil de empresa
3. Modules - Seleccion de modulos
4. Tour - Tour interactivo
5. Complete - Acciones rapidas

**Por que:**
- Mejora adopcion de la plataforma
- Personaliza la experiencia segun rol/industria
- Reduce tiempo al primer valor

**Documentacion:** [docs/features/ONBOARDING.md](./features/ONBOARDING.md)

---

## 5. Decisiones de Diseno

### 5.1 Monorepo con apps separadas

**Decision:** Una sola repo con `apps/api` y `apps/web` separados.

**Razones:**
- Cambios coordinados entre frontend y backend
- Compartir tipos/schemas (potencialmente)
- Un solo PR para features completas
- Simplifica CI/CD

### 5.2 Async SQLAlchemy

**Decision:** Usar SQLAlchemy 2.0 con async/await.

**Razones:**
- FastAPI es async por naturaleza
- No bloquear el event loop en queries
- Mejor performance bajo carga

### 5.3 React Query para data fetching

**Decision:** Usar TanStack Query (React Query) en vez de fetch manual.

**Razones:**
- Cache automatico
- Refetch on focus/reconnect
- Loading/error states manejados
- Invalidacion de cache declarativa

### 5.4 Zustand para estado global

**Decision:** Usar Zustand en vez de Redux o Context.

**Razones:**
- API minimalista
- Sin boilerplate
- TypeScript first
- Persistencia facil con middleware

### 5.5 shadcn/ui para componentes

**Decision:** Usar shadcn/ui (componentes copy-paste) en vez de biblioteca tradicional.

**Razones:**
- Control total del codigo
- No dependencia de actualizaciones externas
- Personalizacion completa
- Basado en Radix (accesible)

---

## 6. Estructura del Proyecto

```
cyberops-companion/
├── apps/
│   ├── api/                          # Backend FastAPI
│   │   ├── src/
│   │   │   ├── api/v1/               # Endpoints por modulo
│   │   │   │   ├── auth.py
│   │   │   │   ├── sso.py            # SSO endpoints
│   │   │   │   ├── audit.py          # Audit endpoints
│   │   │   │   ├── incidents.py
│   │   │   │   ├── analytics.py
│   │   │   │   └── ...
│   │   │   ├── models/               # SQLAlchemy models
│   │   │   │   ├── user.py
│   │   │   │   ├── sso.py            # SSOProvider, SSOState
│   │   │   │   ├── incident.py
│   │   │   │   └── ...
│   │   │   ├── schemas/              # Pydantic schemas
│   │   │   ├── services/             # Business logic
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── sso_service.py
│   │   │   │   ├── audit_service.py
│   │   │   │   ├── analytics_service.py
│   │   │   │   └── ...
│   │   │   └── utils/
│   │   ├── alembic/                  # Database migrations
│   │   └── requirements.txt
│   │
│   └── web/                          # Frontend Next.js
│       ├── app/
│       │   ├── (auth)/               # Auth pages (login, callback)
│       │   ├── (dashboard)/          # Protected pages
│       │   │   ├── incidents/
│       │   │   ├── soc/
│       │   │   ├── audit/            # Audit log page
│       │   │   └── ...
│       │   └── (landing)/            # Public pages
│       ├── components/
│       │   ├── ui/                   # shadcn components
│       │   ├── shared/               # Reusable components
│       │   ├── auth/                 # Auth components (SSO buttons)
│       │   └── dashboard/
│       │       ├── charts/           # Chart components
│       │       └── widgets/          # Dashboard widgets
│       ├── hooks/                    # Custom hooks
│       ├── stores/                   # Zustand stores
│       ├── lib/                      # Utilities
│       │   ├── api-client.ts         # API client con ssoAPI, auditAPI
│       │   └── auth.ts               # Auth helpers
│       └── i18n/
│           └── translations.ts       # All translations
│
├── docs/                             # Documentation
│   ├── features/                     # Feature-specific docs
│   │   ├── SSO_SAML.md
│   │   ├── AUDIT_LOGGING.md
│   │   └── ...
│   ├── CHANGELOG.md
│   ├── PROJECT_STATUS.md
│   └── FUTURE_ROADMAP.md
│
├── docker-compose.yml
└── .env.example
```

---

## 7. Proximos Pasos

### Pendiente en Fase 3

#### Multi-tenancy (Alta prioridad)

**Que es:** Soporte para multiples organizaciones en una sola instalacion.

**Alcance:**
- Modelo Tenant con configuracion por organizacion
- `tenant_id` en todos los modelos
- Middleware que inyecta tenant context
- Aislamiento completo de datos
- Portal de administracion de tenants

**Por que es importante:**
- Permite modelo SaaS
- Reduce costos de operacion (una instalacion para muchos clientes)
- Simplifica actualizaciones

#### API Rate Limiting (Media prioridad)

**Que es:** Limites de requests por usuario/IP.

**Configuracion propuesta:**
```python
RATE_LIMITS = {
    "default": "100/minute",
    "auth": "10/minute",      # Previene brute force
    "reports": "10/minute",   # Reportes son pesados
    "uploads": "20/minute",   # Uploads consumen recursos
}
```

### Fase 2C - ML/Predictive Analytics (Diferido)

**Por que se difeeri:**
- Los modelos ML requieren datos historicos para entrenar
- Sin datos reales, los modelos no tendrian precision util
- Se implementara cuando la plataforma este en produccion y tenga 3-6 meses de datos

**Features planeados:**
- Deteccion de anomalias en alertas
- Prediccion de incidentes
- Scoring de riesgo mejorado con ML
- Priorizacion automatica de alertas

---

## Resumen

CyberOps Companion es una plataforma madura que ha completado 3 fases de desarrollo:

- **Fase 0-1:** Fundamentos solidos (auth, i18n, background tasks, onboarding)
- **Fase 2:** Features avanzados (WebSocket, uploads, analytics, mobile)
- **Fase 3 (parcial):** Enterprise (audit logging, SSO/SAML)

El sistema esta listo para uso en produccion con las funcionalidades actuales. Las siguientes prioridades son multi-tenancy para habilitar modelo SaaS y rate limiting para proteccion.

La arquitectura esta disenada para escalar horizontalmente y las decisiones tecnicas priorizan mantenibilidad, performance y experiencia de desarrollador.

---

**Documentos relacionados:**
- [PROJECT_STATUS.md](./PROJECT_STATUS.md) - Estado detallado
- [CHANGELOG.md](./CHANGELOG.md) - Historial de cambios
- [FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md) - Roadmap futuro
- [ANALYTICS.md](./ANALYTICS.md) - Sistema de analytics
- [UX_PATTERNS.md](./UX_PATTERNS.md) - Patrones de UI/UX
