# Rate Limiting (API Protection)

## Resumen

Esta documentacion describe la implementacion del sistema de rate limiting en ISORA, que protege la API contra abuso y garantiza un uso justo de los recursos basado en el plan de suscripcion de cada organizacion.

**Fecha de implementacion:** 2026-02-01
**Version:** 1.0.0

---

## Tabla de Contenidos

1. [Motivacion y Objetivos](#motivacion-y-objetivos)
2. [Arquitectura](#arquitectura)
3. [Limites por Plan](#limites-por-plan)
4. [Backend - Implementacion](#backend---implementacion)
5. [Frontend - Implementacion](#frontend---implementacion)
6. [Configuracion](#configuracion)
7. [Headers HTTP](#headers-http)
8. [Manejo de Errores](#manejo-de-errores)
9. [Exclusiones](#exclusiones)
10. [Troubleshooting](#troubleshooting)

---

## Motivacion y Objetivos

### Por que Rate Limiting?

Sin rate limiting, la API es vulnerable a:

- **Ataques de fuerza bruta** en endpoints de autenticacion
- **Abuso de recursos** por usuarios o scripts malintencionados
- **Denegacion de servicio (DoS)** involuntaria o intencional
- **Uso desproporcionado** que afecta a otros usuarios
- **Scraping masivo** de datos de la plataforma

### Objetivos de la Implementacion

| Objetivo | Descripcion |
|----------|-------------|
| **Proteccion de API** | Limitar requests excesivos para mantener estabilidad |
| **Limites por plan** | Diferentes limites segun el plan de suscripcion |
| **Limites por endpoint** | Proteccion especial para endpoints sensibles (login, register) |
| **Transparencia** | Headers informativos en cada respuesta |
| **Experiencia de usuario** | Banner y manejo gracioso de errores 429 |
| **Bypass para admins** | Super admins pueden omitir limites si es necesario |

---

## Arquitectura

### Algoritmo Sliding Window

Se implemento **Sliding Window** usando Redis Sorted Sets para un conteo preciso de requests:

```
┌─────────────────────────────────────────────────────────────┐
│                        Request                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 RateLimitMiddleware                          │
│  1. Verificar si path esta excluido                          │
│  2. Extraer IP y tenant info                                 │
│  3. Verificar limite de endpoint (por IP)                    │
│  4. Verificar limite de tenant (por plan)                    │
│  5. Agregar headers a response                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  RateLimitService                            │
│  - Sliding window con Redis sorted sets                      │
│  - Limpia entradas expiradas                                 │
│  - Cuenta requests en ventana                                │
│  - Calcula remaining y reset_at                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Redis DB 1                              │
│  - Separado de Celery (DB 0)                                 │
│  - Sorted sets por tenant/IP/endpoint                        │
│  - TTL automatico para limpieza                              │
└─────────────────────────────────────────────────────────────┘
```

### Como Funciona el Sliding Window

```
Ventana de 1 minuto (60 segundos)
─────────────────────────────────────────────────────►
|  R1  R2    R3 R4      R5 R6 R7  R8         R9    |
|  ↑   ↑     ↑  ↑       ↑  ↑  ↑   ↑          ↑     |
| t-55 t-50  t-40 t-35  t-20 t-15 t-10 t-5   t=now |
─────────────────────────────────────────────────────

1. En cada request, se eliminan entradas mas viejas que (now - window)
2. Se cuenta el numero de entradas restantes
3. Si count < limit, se agrega la nueva entrada con timestamp actual
4. Si count >= limit, se rechaza con 429
```

### Ventajas del Sliding Window

- **Precision:** No hay "burst" al inicio de cada minuto
- **Justicia:** Distribucion uniforme de requests permitidos
- **Eficiencia:** Operaciones O(log N) en Redis sorted sets
- **Atomicidad:** Pipeline de Redis para operaciones atomicas

---

## Limites por Plan

### Limites de Tenant (por organizacion)

| Plan | Requests/Hora | Requests/Minuto |
|------|---------------|-----------------|
| **FREE** | 1,000 | 60 |
| **STARTER** | 5,000 | 200 |
| **PROFESSIONAL** | 20,000 | 500 |
| **ENTERPRISE** | 100,000 | 2,000 |

### Limites de Endpoint (por IP)

| Endpoint | Limite | Ventana |
|----------|--------|---------|
| `/api/v1/auth/login` | 5 requests | 1 minuto |
| `/api/v1/auth/register` | 3 requests | 1 minuto |
| `/api/v1/auth/forgot-password` | 3 requests | 1 minuto |
| `/api/v1/auth/reset-password` | 5 requests | 1 minuto |

### Limite para Requests No Autenticados

| Tipo | Limite | Ventana |
|------|--------|---------|
| Sin token (por IP) | 30 requests | 1 minuto |

---

## Backend - Implementacion

### Archivos Creados

| Archivo | Proposito |
|---------|-----------|
| `src/core/redis.py` | Connection pool de Redis con cliente async |
| `src/core/rate_limit_config.py` | Configuracion de limites por plan y endpoint |
| `src/services/rate_limit_service.py` | Logica sliding window con Redis sorted sets |
| `src/middleware/rate_limit_middleware.py` | Middleware principal de FastAPI |

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `src/config.py` | Agregadas settings RATE_LIMIT_* |
| `src/main.py` | Registro de middleware, cierre de Redis en shutdown |
| `src/middleware/__init__.py` | Export de RateLimitMiddleware |
| `src/core/__init__.py` | Exports de Redis y rate limit config |

### Redis Key Structure

```bash
# Limites por tenant (sliding window)
ratelimit:sw:tenant:{tenant_id}:hour     # Requests por hora
ratelimit:sw:tenant:{tenant_id}:minute   # Requests por minuto

# Limites por IP
ratelimit:sw:ip:{ip}:minute              # Requests no autenticados

# Limites por endpoint
ratelimit:sw:endpoint:{path}:ip:{ip}     # Endpoints sensibles

# Cache de plan (opcional)
ratelimit:meta:{tenant_id}:plan          # Cache del plan por 5 minutos
```

### Componentes Principales

#### RedisManager (`src/core/redis.py`)

```python
class RedisManager:
    """Manages Redis connection pool."""

    @classmethod
    async def get_client(cls, db: int = 0) -> Redis:
        """Get Redis client with connection pool."""

    @classmethod
    async def get_rate_limit_client(cls) -> Redis:
        """Get client for rate limiting (DB 1)."""

    @classmethod
    async def close(cls) -> None:
        """Close connection pool on shutdown."""
```

#### RateLimitService (`src/services/rate_limit_service.py`)

```python
class RateLimitService:
    """Sliding window rate limiting with Redis."""

    async def check_rate_limit(
        self,
        tenant_id: Optional[str],
        ip: str,
        path: str,
        plan: Optional[OrganizationPlan] = None,
        is_super_admin: bool = False,
    ) -> RateLimitResult:
        """Check if request is within rate limits."""

    async def _check_sliding_window(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> RateLimitResult:
        """Sliding window algorithm with Redis sorted sets."""
```

#### RateLimitMiddleware (`src/middleware/rate_limit_middleware.py`)

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Skip if disabled or path excluded
        # 2. Get client IP (handles X-Forwarded-For)
        # 3. Extract tenant info from JWT
        # 4. Check rate limits
        # 5. Return 429 or add headers to response
```

---

## Frontend - Implementacion

### Archivos Creados

| Archivo | Proposito |
|---------|-----------|
| `components/shared/rate-limit-banner.tsx` | Banner con countdown para rate limit |

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `lib/api-client.ts` | RateLimitError, event system, parseRateLimitHeaders |
| `components/shared/providers.tsx` | Agregado RateLimitBanner al arbol de componentes |

### API Client Updates

```typescript
// Nueva interfaz para info de rate limit
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetAt: number;
  retryAfter?: number;
}

// Nueva clase de error
export class RateLimitError extends APIError {
  constructor(message: string, public rateLimitInfo: RateLimitInfo) {
    super(429, message);
    this.name = "RateLimitError";
  }
}

// Sistema de eventos para notificar rate limit
export function onRateLimitExceeded(listener: RateLimitListener): () => void;
```

### RateLimitBanner Component

```typescript
export function RateLimitBanner({ className }: RateLimitBannerProps) {
  // Suscripcion a eventos de rate limit
  // Countdown timer con auto-dismiss
  // UI con warning y tiempo restante
}

// Hook para componentes que necesitan estado de rate limit
export function useRateLimitState() {
  const [isRateLimited, setIsRateLimited] = useState(false);
  const [retryAfter, setRetryAfter] = useState<number | null>(null);
  // ...
}
```

---

## Configuracion

### Variables de Entorno

```bash
# Rate Limiting General
RATE_LIMIT_ENABLED=true              # Activar/desactivar rate limiting
RATE_LIMIT_REDIS_DB=1                # Base de datos Redis (separada de Celery)
RATE_LIMIT_BYPASS_SUPER_ADMIN=true   # Super admins omiten limites

# Limites por Plan (override desde .env)
RATE_LIMIT_FREE_HOUR=1000
RATE_LIMIT_FREE_MINUTE=60
RATE_LIMIT_STARTER_HOUR=5000
RATE_LIMIT_STARTER_MINUTE=200
RATE_LIMIT_PROFESSIONAL_HOUR=20000
RATE_LIMIT_PROFESSIONAL_MINUTE=500
RATE_LIMIT_ENTERPRISE_HOUR=100000
RATE_LIMIT_ENTERPRISE_MINUTE=2000
```

### Pydantic Settings

```python
class Settings(BaseSettings):
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REDIS_DB: int = 1
    RATE_LIMIT_BYPASS_SUPER_ADMIN: bool = True

    # Per-plan limits
    RATE_LIMIT_FREE_HOUR: int = 1000
    RATE_LIMIT_FREE_MINUTE: int = 60
    # ... etc
```

### Modificar Limites en Codigo

```python
# src/core/rate_limit_config.py

# Modificar limites de plan
PLAN_LIMITS: Dict[OrganizationPlan, RateLimitTier] = {
    OrganizationPlan.FREE: RateLimitTier(
        requests_per_hour=1000,
        requests_per_minute=60,
    ),
    # ...
}

# Agregar endpoint con limite especial
ENDPOINT_LIMITS: Dict[str, EndpointRateLimit] = {
    "/api/v1/auth/login": EndpointRateLimit(requests_per_minute=5, by_ip=True),
    "/api/v1/custom/endpoint": EndpointRateLimit(requests_per_minute=10, by_ip=True),
}
```

---

## Headers HTTP

### Headers en Todas las Respuestas

```http
X-RateLimit-Limit: 60         # Limite maximo en la ventana
X-RateLimit-Remaining: 45     # Requests restantes
X-RateLimit-Reset: 1706745720 # Unix timestamp cuando se resetea
```

### Headers Adicionales en 429

```http
Retry-After: 35               # Segundos hasta poder reintentar
```

---

## Manejo de Errores

### Response 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "limit": 60,
    "retry_after": 35,
    "reset_at": 1706745720
  }
}
```

### Frontend Error Handling

```typescript
try {
  const data = await incidentsAPI.list(token);
} catch (error) {
  if (error instanceof RateLimitError) {
    // Mostrar mensaje amigable
    toast.error(`Rate limit exceeded. Retry in ${error.rateLimitInfo.retryAfter}s`);
  }
}
```

---

## Exclusiones

### Paths Sin Rate Limit

Los siguientes paths estan excluidos del rate limiting:

```python
EXCLUDED_PATHS = {
    "/health",              # Health checks
    "/",                    # Root endpoint
    "/api/docs",            # Swagger UI
    "/api/redoc",           # ReDoc
    "/api/openapi.json",    # OpenAPI schema
}

EXCLUDED_PREFIXES = (
    "/api/v1/ws/",          # WebSocket connections
)
```

### Super Admin Bypass

Si `RATE_LIMIT_BYPASS_SUPER_ADMIN=true`, los usuarios con `is_super_admin=true` en su JWT omiten todos los limites.

---

## Troubleshooting

### "Rate limit exceeded" inesperado

**Causa:** El tenant esta excediendo el limite de su plan.

**Diagnostico:**
```bash
# Verificar uso actual del tenant
redis-cli -n 1 ZCARD "ratelimit:sw:tenant:{tenant_id}:minute"
redis-cli -n 1 ZCARD "ratelimit:sw:tenant:{tenant_id}:hour"
```

**Solucion:**
1. Esperar al reset del limite
2. Considerar upgrade de plan
3. Optimizar llamadas a la API (caching, batching)

### Rate limit no funciona

**Causa:** Redis no esta conectado o rate limiting esta deshabilitado.

**Verificar:**
```bash
# Verificar conexion a Redis
redis-cli -n 1 PING

# Verificar setting
grep RATE_LIMIT_ENABLED .env
```

### Headers X-RateLimit no aparecen

**Causa:** Path esta excluido o error en middleware.

**Verificar:**
```bash
# Hacer request y verificar headers
curl -I http://localhost:8000/api/v1/incidents

# Verificar logs
docker compose logs api | grep -i ratelimit
```

### Login bloqueado por rate limit

**Causa:** Demasiados intentos de login desde la misma IP.

**Solucion:**
```bash
# Limpiar limite de IP para endpoint especifico
redis-cli -n 1 DEL "ratelimit:sw:endpoint:_api_v1_auth_login:ip:{client_ip}"
```

### Reset manual de limites para tenant

```bash
# Limpiar todos los limites de un tenant
redis-cli -n 1 DEL "ratelimit:sw:tenant:{tenant_id}:hour"
redis-cli -n 1 DEL "ratelimit:sw:tenant:{tenant_id}:minute"
```

---

## Monitoreo

### Metricas Recomendadas

| Metrica | Descripcion |
|---------|-------------|
| `rate_limit_exceeded_total` | Total de requests rechazados por rate limit |
| `rate_limit_remaining_avg` | Promedio de requests restantes |
| `rate_limit_by_plan` | Uso por plan de suscripcion |
| `rate_limit_by_endpoint` | Endpoints mas limitados |

### Logs

El middleware genera logs de warning cuando se excede un limite:

```
WARNING - Rate limit exceeded: ip=192.168.1.100, tenant=abc123, path=/api/v1/incidents
```

---

## Consideraciones de Seguridad

### Proteccion contra IP Spoofing

El middleware obtiene la IP del cliente en orden de prioridad:

1. `X-Forwarded-For` (primer IP en la cadena)
2. `X-Real-IP`
3. `request.client.host`

**Nota:** Asegurarse que el reverse proxy (nginx, etc.) configure correctamente estos headers.

### Separacion de Redis

Rate limiting usa `Redis DB 1` para evitar conflictos con:
- Celery (DB 0)
- Cache de aplicacion (DB 2, si existe)

### Rate Limit en Autenticacion

Los endpoints de autenticacion tienen limites mas estrictos para prevenir:
- Ataques de fuerza bruta
- Enumeracion de usuarios
- Account takeover

---

## Referencias

- **Redis Sorted Sets:** https://redis.io/docs/data-types/sorted-sets/
- **Sliding Window Algorithm:** https://blog.cloudflare.com/counting-things-a-lot-of-different-things/
- **RFC 6585 (429 Status Code):** https://tools.ietf.org/html/rfc6585#section-4

---

## Changelog

### v1.0.0 (2026-02-01)

- Implementacion inicial de rate limiting
- Sliding window algorithm con Redis sorted sets
- Limites por plan: FREE, STARTER, PROFESSIONAL, ENTERPRISE
- Limites por endpoint para auth (login, register)
- Limites por IP para requests no autenticados
- Headers X-RateLimit-* en todas las respuestas
- Response 429 con retry_after
- Frontend: RateLimitBanner con countdown
- Frontend: RateLimitError y event system
- Configuracion via environment variables
- Super admin bypass opcional
- Exclusion de paths (health, docs, websocket)
