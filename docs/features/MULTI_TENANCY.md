# Multi-Tenancy (Organizaciones)

## Resumen

Esta documentacion describe la implementacion del sistema multi-tenant en ISORA, que permite a multiples organizaciones usar la plataforma con aislamiento completo de datos.

**Fecha de implementacion:** 2026-02-01
**Version:** 1.0.0

---

## Tabla de Contenidos

1. [Motivacion y Objetivos](#motivacion-y-objetivos)
2. [Arquitectura](#arquitectura)
3. [Modelos de Base de Datos](#modelos-de-base-de-datos)
4. [Backend - Implementacion](#backend---implementacion)
5. [Frontend - Implementacion](#frontend---implementacion)
6. [Migraciones](#migraciones)
7. [Uso del Sistema](#uso-del-sistema)
8. [Consideraciones de Seguridad](#consideraciones-de-seguridad)
9. [Troubleshooting](#troubleshooting)

---

## Motivacion y Objetivos

### Por que Multi-Tenancy?

Antes de esta implementacion, ISORA era una aplicacion **single-tenant**, lo que significaba:

- Todos los usuarios compartian los mismos datos
- No habia aislamiento entre equipos u organizaciones
- Imposible ofrecer la plataforma como SaaS a multiples clientes
- Sin soporte para empresas con multiples divisiones o subsidiarias

### Objetivos de la Implementacion

| Objetivo | Descripcion |
|----------|-------------|
| **Aislamiento de datos** | Cada organizacion solo ve sus propios incidentes, alertas, vulnerabilidades, etc. |
| **Multi-organizacion** | Un usuario puede pertenecer a multiples organizaciones |
| **Cambio de contexto** | Cambiar entre organizaciones sin cerrar sesion |
| **Roles por organizacion** | Un usuario puede ser Admin en una org y Viewer en otra |
| **Super Admin** | Usuarios especiales que pueden acceder a cualquier organizacion |
| **Migracion transparente** | Los datos existentes se migran automaticamente |

---

## Arquitectura

### Estrategia de Tenant Isolation

Se implemento **Row-Level Security** mediante un campo `tenant_id` en todas las tablas que contienen datos de negocio:

```
┌─────────────────────────────────────────────────────────────┐
│                        Request                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   TenantMiddleware                           │
│  - Extrae tenant_id del JWT                                  │
│  - Establece TenantContext (ContextVar)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 TenantAwareService                           │
│  - Filtra automaticamente por tenant_id                      │
│  - Asigna tenant_id en creacion                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database                                │
│  WHERE tenant_id = 'current_tenant'                          │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Clave

1. **TenantContext** (`src/core/tenant_context.py`)
   - Usa `ContextVar` para almacenamiento thread-safe
   - Disponible en toda la request sin pasar parametros

2. **TenantMiddleware** (`src/middleware/tenant_middleware.py`)
   - Intercepta cada request
   - Extrae informacion del tenant del JWT
   - Establece el contexto para la request

3. **TenantAwareService** (`src/services/base_service.py`)
   - Clase base para todos los servicios
   - Filtrado automatico en queries
   - Asignacion automatica en creacion

4. **TenantMixin** (`src/models/mixins.py`)
   - Mixin para agregar `tenant_id` a modelos
   - Foreign key a `organizations`

---

## Modelos de Base de Datos

### Organization

```python
class Organization(Base):
    __tablename__ = "organizations"

    id: str                    # UUID
    name: str                  # "Acme Corp"
    slug: str                  # "acme-corp" (unico)
    description: str | None
    status: OrganizationStatus # active, suspended, trial, cancelled
    plan: OrganizationPlan     # free, starter, professional, enterprise
    logo_url: str | None
    max_users: int             # Limite de usuarios
    settings: dict             # Configuracion JSON
    created_at: datetime
    updated_at: datetime | None
```

### OrganizationMember

```python
class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id: str
    organization_id: str       # FK -> organizations
    user_id: str               # FK -> users
    org_role: OrgMemberRole    # owner, admin, member, viewer
    is_active: bool
    is_default: bool           # Organizacion por defecto al login
    joined_at: datetime
    invited_by: str | None     # Usuario que invito
```

### Roles de Organizacion

| Rol | Permisos |
|-----|----------|
| **owner** | Control total, puede eliminar la organizacion |
| **admin** | Gestionar miembros, configuracion |
| **member** | Crear y editar recursos |
| **viewer** | Solo lectura |

### User (Modificaciones)

```python
# Nuevos campos agregados a User
is_super_admin: bool  # Puede acceder a cualquier organizacion

# Nueva relacion
organization_memberships: List[OrganizationMember]
```

### Tablas con tenant_id

Todas las siguientes tablas ahora tienen `tenant_id`:

- `incidents`, `affected_systems`
- `evidence_entries`
- `soc_alerts`, `alert_comments`
- `soc_cases`, `case_tasks`, `case_timeline`
- `soc_playbooks`, `playbook_executions`
- `soc_metrics`, `shift_handovers`
- `assets`, `vulnerabilities`, `vulnerability_comments`
- `vulnerability_scans`, `scan_schedules`
- `risks`, `risk_controls`, `risk_assessments`
- `treatment_actions`, `risk_appetite`
- `teams`, `team_members`
- `notifications`, `integrations`

---

## Backend - Implementacion

### Archivos Creados

| Archivo | Proposito |
|---------|-----------|
| `src/models/organization.py` | Modelos Organization y OrganizationMember |
| `src/models/mixins.py` | TenantMixin e ImmutableTenantMixin |
| `src/core/tenant_context.py` | ContextVar para tenant actual |
| `src/middleware/tenant_middleware.py` | Middleware de extraccion de tenant |
| `src/services/base_service.py` | TenantAwareService base |
| `src/services/organization_service.py` | CRUD de organizaciones |
| `src/schemas/organization.py` | Schemas Pydantic |
| `src/api/v1/organizations.py` | Endpoints REST |

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `src/models/user.py` | Agregado `is_super_admin`, relacion con memberships |
| `src/services/auth_service.py` | JWT con tenant_id, switch_tenant() |
| `src/api/deps.py` | Dependencies con tenant context |
| `src/main.py` | Registro de TenantMiddleware |
| `src/api/v1/router.py` | Incluido organizations router |
| Modelos de dominio | Agregado TenantMixin |

### JWT Token - Nuevo Payload

```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "role": "analyst",
  "type": "access",
  "tenant_id": "org-uuid",
  "org_role": "admin",
  "is_super_admin": false,
  "available_tenants": ["org-uuid-1", "org-uuid-2"]
}
```

### API Endpoints

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/api/v1/organizations` | Crear organizacion (usuario = owner) |
| GET | `/api/v1/organizations/me` | Listar organizaciones del usuario |
| GET | `/api/v1/organizations/{id}` | Obtener organizacion |
| PATCH | `/api/v1/organizations/{id}` | Actualizar (requiere admin) |
| DELETE | `/api/v1/organizations/{id}` | Eliminar (requiere owner) |
| GET | `/api/v1/organizations/{id}/members` | Listar miembros |
| POST | `/api/v1/organizations/{id}/members` | Agregar miembro |
| PATCH | `/api/v1/organizations/{id}/members/{user_id}` | Actualizar rol |
| DELETE | `/api/v1/organizations/{id}/members/{user_id}` | Remover miembro |
| POST | `/api/v1/organizations/switch` | Cambiar organizacion activa |

---

## Frontend - Implementacion

### Archivos Creados

| Archivo | Proposito |
|---------|-----------|
| `stores/tenant-store.ts` | Zustand store para estado de tenant |
| `components/shared/tenant-selector.tsx` | Componente selector de organizacion |

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `stores/auth-store.ts` | Carga tenants en login, limpia en logout |
| `components/shared/header.tsx` | Agregado TenantSelector |
| `components/shared/index.ts` | Export de TenantSelector |
| `i18n/translations.ts` | Traducciones EN/DE para organizations |

### Tenant Store

```typescript
interface TenantState {
  currentTenant: Organization | null;
  availableTenants: Organization[];
  isLoading: boolean;

  setCurrentTenant: (tenant: Organization | null) => void;
  setAvailableTenants: (tenants: Organization[]) => void;
  switchTenant: (tenantId: string) => Promise<void>;
  loadTenants: (token: string) => Promise<void>;
  clearTenants: () => void;
}
```

### Flujo de Cambio de Organizacion

```
1. Usuario selecciona organizacion en TenantSelector
2. switchTenant() llama a POST /organizations/switch
3. Backend genera nuevos tokens con nuevo tenant_id
4. Frontend guarda tokens y recarga la pagina
5. Todos los datos se cargan con el nuevo contexto
```

---

## Migraciones

### Estrategia de Migracion

La migracion se dividio en dos partes para seguridad:

#### Migration 1: `a1b2c3d4e5f6_add_multi_tenancy_tables`

**Objetivo:** Crear estructura sin romper datos existentes

```python
def upgrade():
    # 1. Crear tabla organizations
    op.create_table('organizations', ...)

    # 2. Crear tabla organization_members
    op.create_table('organization_members', ...)

    # 3. Agregar is_super_admin a users
    op.add_column('users', Column('is_super_admin', Boolean))

    # 4. Agregar tenant_id NULLABLE a todas las tablas
    for table in TENANT_TABLES:
        op.add_column(table, Column('tenant_id', String(36), nullable=True))
```

#### Migration 2: `b2c3d4e5f6g7_migrate_to_multi_tenancy`

**Objetivo:** Migrar datos y finalizar schema

```python
def upgrade():
    # 1. Crear organizacion por defecto
    default_org_id = str(uuid4())
    op.bulk_insert(organizations, [{
        'id': default_org_id,
        'name': 'Default Organization',
        'slug': 'default',
        'status': 'active',
        'plan': 'enterprise',
    }])

    # 2. Vincular usuarios existentes a org por defecto
    op.execute("""
        INSERT INTO organization_members (...)
        SELECT ... FROM users
    """)

    # 3. Establecer primer admin como super_admin
    op.execute("""
        UPDATE users SET is_super_admin = true
        WHERE id = (SELECT id FROM users WHERE role = 'admin' LIMIT 1)
    """)

    # 4. Asignar tenant_id a todos los registros existentes
    for table in TENANT_TABLES:
        op.execute(f"UPDATE {table} SET tenant_id = '{default_org_id}'")

    # 5. Hacer tenant_id NOT NULL y agregar foreign keys
    for table in TENANT_TABLES:
        op.alter_column(table, 'tenant_id', nullable=False)
        op.create_foreign_key(...)
```

### Problemas Encontrados y Soluciones

#### Problema 1: Driver de Base de Datos

**Error:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Causa:** Alembic necesita un driver sincrono, pero solo `asyncpg` estaba instalado.

**Solucion:** Agregar `psycopg2-binary` a requirements.txt:
```
psycopg2-binary>=2.9.9  # Sync driver for Alembic migrations
```

#### Problema 2: Enum Type Already Exists

**Error:**
```
psycopg2.errors.DuplicateObject: type "organizationstatus" already exists
```

**Causa:** Migracion parcial dejo tipos enum huerfanos.

**Solucion:** Limpiar manualmente antes de reintentar:
```sql
DROP TYPE IF EXISTS organizationstatus CASCADE;
DROP TYPE IF EXISTS organizationplan CASCADE;
DROP TYPE IF EXISTS organizationmemberrole CASCADE;
DROP TABLE IF EXISTS organization_members CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
```

#### Problema 3: Enum Comparison in SQL

**Error:**
```
psycopg2.errors.InvalidTextRepresentation: invalid input value for enum userrole: "admin"
```

**Causa:** La columna `role` es un enum PostgreSQL, no se puede comparar directamente con strings.

**Solucion:** Castear el enum a texto:
```sql
-- Antes (error)
WHERE role = 'admin'

-- Despues (correcto)
WHERE role::text = 'admin'
```

### Comandos de Migracion

```bash
# Ejecutar migraciones
sudo docker compose exec api alembic upgrade head

# Ver estado actual
sudo docker compose exec api alembic current

# Revertir una migracion
sudo docker compose exec api alembic downgrade -1

# Ver historial
sudo docker compose exec api alembic history
```

---

## Uso del Sistema

### Login con Tenant

El login ahora retorna informacion de organizaciones:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

El token contiene `tenant_id` y `available_tenants`.

### Cambiar de Organizacion

**Frontend:** El usuario selecciona en el dropdown del header.

**API:**
```bash
POST /api/v1/organizations/switch
Content-Type: application/json
Authorization: Bearer <token>

{
  "tenant_id": "nuevo-org-uuid"
}
```

**Respuesta:** Nuevos tokens con el nuevo tenant_id.

### Crear Nueva Organizacion

```bash
POST /api/v1/organizations
Authorization: Bearer <token>

{
  "name": "Mi Empresa",
  "slug": "mi-empresa",
  "description": "Descripcion opcional"
}
```

El usuario que crea la organizacion se convierte automaticamente en **owner**.

### Invitar Miembros

```bash
POST /api/v1/organizations/{org_id}/members
Authorization: Bearer <token>

{
  "user_id": "user-uuid",
  "org_role": "member"
}
```

---

## Consideraciones de Seguridad

### Aislamiento de Datos

- **Automatico:** TenantAwareService filtra todas las queries
- **Validado:** El middleware verifica acceso al tenant en cada request
- **Inmutable:** Evidence entries usan ImmutableTenantMixin (tenant_id no puede cambiar)

### Super Admin

- Puede acceder a cualquier organizacion via header `X-Tenant-ID`
- Todas las acciones son auditadas
- Solo el primer usuario admin existente se convierte en super_admin

### Tokens

- `tenant_id` embebido en JWT
- `available_tenants` lista organizaciones permitidas
- Token se invalida al cambiar de organizacion

### Validaciones

```python
# En deps.py
async def get_current_user_with_tenant(...):
    # Verificar que el usuario tiene acceso al tenant
    if not user.is_super_admin and tenant_id not in payload.available_tenants:
        raise HTTPException(403, "No access to this tenant")
```

---

## Troubleshooting

### "No organizations found"

**Causa:** El usuario no esta vinculado a ninguna organizacion.

**Solucion:**
```sql
INSERT INTO organization_members (id, organization_id, user_id, org_role, is_active, is_default, joined_at)
VALUES (gen_random_uuid()::text, 'org-id', 'user-id', 'member', true, true, now());
```

### "Tenant context not set"

**Causa:** Request a endpoint protegido sin token valido.

**Solucion:** Verificar que el token incluye `tenant_id`.

### "No access to this tenant"

**Causa:** El usuario intenta acceder a una organizacion a la que no pertenece.

**Solucion:** Agregar el usuario como miembro de la organizacion.

### Datos no visibles despues de migracion

**Causa:** `tenant_id` no se asigno a los registros.

**Verificar:**
```sql
SELECT COUNT(*) FROM incidents WHERE tenant_id IS NULL;
```

**Solucion:**
```sql
UPDATE incidents SET tenant_id = 'default-org-id' WHERE tenant_id IS NULL;
```

---

## Referencias

- **Migraciones:** `apps/api/alembic/versions/`
- **Modelos:** `apps/api/src/models/organization.py`
- **Servicios:** `apps/api/src/services/organization_service.py`

---

## Changelog

### v1.0.0 (2026-02-01)

- Implementacion inicial de multi-tenancy
- Modelos Organization y OrganizationMember
- TenantMiddleware y TenantAwareService
- Migracion de datos existentes a organizacion por defecto
- Frontend: TenantSelector y tenant-store
- Soporte para cambio de organizacion
- Traducciones EN/DE
