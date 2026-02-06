# 🆓 Deploy Gratis en Oracle Cloud Free Tier

Guía para desplegar CyberOps Companion 100% gratis usando Oracle Cloud.

## ¿Por qué Oracle Cloud?

- ✅ **Gratis PARA SIEMPRE** (no solo 12 meses)
- ✅ **4 OCPU + 24GB RAM** en instancias ARM Ampere
- ✅ **200GB de storage**
- ✅ **10TB de ancho de banda/mes**
- ✅ Sin tarjeta de crédito (solo verificación)

---

## Paso 1: Crear cuenta en Oracle Cloud

1. Ve a [cloud.oracle.com/free](https://www.oracle.com/cloud/free/)
2. Click en "Start for free"
3. Completa el registro (necesitas tarjeta para verificación, NO te cobran)
4. Selecciona tu región (recomendado: Frankfurt o Amsterdam para EU)

> ⚠️ **Importante:** Las instancias ARM Ampere son muy demandadas. Si no hay disponibilidad, intenta a las 3-4 AM UTC o cambia de región.

---

## Paso 2: Crear la instancia (VM)

1. En el Dashboard, ve a **Compute > Instances > Create Instance**

2. Configuración:
   ```
   Name: cyberops-companion
   Image: Ubuntu 22.04 (o Canonical Ubuntu)
   Shape: VM.Standard.A1.Flex (ARM - Always Free)

   OCPU: 4 (máximo gratis)
   Memory: 24 GB (máximo gratis)

   Boot Volume: 100 GB
   ```

3. En **Networking**:
   - Crear nueva VCN o usar existente
   - Asignar IP pública

4. En **Add SSH keys**:
   - Generar nuevo par de claves o subir tu clave pública
   - **¡DESCARGA LA CLAVE PRIVADA!**

5. Click **Create**

---

## Paso 3: Configurar Firewall (Security List)

1. Ve a **Networking > Virtual Cloud Networks**
2. Click en tu VCN > **Security Lists** > Default
3. Añadir **Ingress Rules**:

   | Source CIDR | Protocol | Port | Descripción |
   |-------------|----------|------|-------------|
   | 0.0.0.0/0 | TCP | 80 | HTTP |
   | 0.0.0.0/0 | TCP | 443 | HTTPS |
   | 0.0.0.0/0 | TCP | 22 | SSH |

---

## Paso 4: Conectar y Configurar el Servidor

```bash
# Conectar (reemplaza con tu IP y ruta a la clave)
ssh -i ~/oracle-key.pem ubuntu@TU_IP_PUBLICA

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu

# Cerrar sesión y reconectar para aplicar grupo docker
exit
ssh -i ~/oracle-key.pem ubuntu@TU_IP_PUBLICA

# Verificar Docker
docker --version
docker compose version
```

---

## Paso 5: Desplegar CyberOps Companion

```bash
# Clonar repositorio
git clone https://github.com/fbarquez/cyberops-companion.git
cd cyberops-companion

# Crear archivo de configuración
cp .env.production.example .env

# Generar secretos automáticamente
cat >> .env << EOF
JWT_SECRET=$(openssl rand -hex 32)
SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=')
REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=')
EOF

# Editar configuración
nano .env
```

### Configuración mínima en .env:

```bash
# Cambiar esto:
DOMAIN=TU_IP_PUBLICA  # o tu dominio si tienes

# Para AI Copilot (opcional - elige uno):
COPILOT_PROVIDER=groq  # Groq tiene tier gratis
GROQ_API_KEY=gsk_xxx   # Obtener en console.groq.com
```

### Desplegar:

```bash
# Ejecutar deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Crear usuario admin
docker compose -f docker-compose.prod.yml exec api python -m src.scripts.create_admin
```

---

## Paso 6: Configurar Dominio (Opcional pero Recomendado)

### Opción A: Dominio gratis con Freenom/DuckDNS

1. Ve a [duckdns.org](https://www.duckdns.org/)
2. Crea una cuenta (login con GitHub/Google)
3. Crea un subdominio: `tuapp.duckdns.org`
4. Apúntalo a tu IP de Oracle

### Opción B: Usar tu propio dominio

En tu proveedor DNS (Cloudflare, etc.):
```
A    tudominio.com    → IP_DE_ORACLE
```

### Actualizar configuración:

```bash
# Editar .env
nano .env
# Cambiar DOMAIN=tuapp.duckdns.org

# Reiniciar Caddy para obtener SSL
docker compose -f docker-compose.prod.yml restart caddy
```

---

## Paso 7: ¡Listo!

Accede a tu aplicación:
- **Con dominio:** https://tuapp.duckdns.org
- **Sin dominio:** http://TU_IP_PUBLICA (sin HTTPS)

Login:
```
📧 Email: admin@cyberops.local
🔑 Password: CyberOps2024!
```

---

## 🤖 AI Copilot Gratis

Para el AI Copilot, opciones gratuitas:

| Proveedor | Gratis | Cómo obtener |
|-----------|--------|--------------|
| **Groq** | 14,400 req/día | [console.groq.com](https://console.groq.com) |
| **Google AI** | 60 req/min | [aistudio.google.com](https://aistudio.google.com) |
| **Ollama** | Ilimitado (local) | Requiere más RAM |

### Configurar Groq (Recomendado):

1. Crea cuenta en [console.groq.com](https://console.groq.com)
2. Genera API Key
3. Configura en `.env`:
   ```bash
   COPILOT_PROVIDER=groq
   COPILOT_MODEL=llama-3.1-70b-versatile
   GROQ_API_KEY=gsk_xxxxx
   ```
4. Reiniciar: `docker compose -f docker-compose.prod.yml restart api`

---

## 🔄 Actualizar la Aplicación

Cuando hagas cambios en el código:

```bash
# En tu PC local
git add . && git commit -m "cambios" && git push

# En el servidor Oracle
cd cyberops-companion
./scripts/update.sh
```

---

## 🛠️ Comandos Útiles

```bash
# Ver logs
docker compose -f docker-compose.prod.yml logs -f

# Ver estado
docker compose -f docker-compose.prod.yml ps

# Reiniciar todo
docker compose -f docker-compose.prod.yml restart

# Backup de base de datos
docker compose -f docker-compose.prod.yml exec db pg_dump -U cyberops cyberops_companion > backup.sql
```

---

## ⚠️ Troubleshooting

### "No hay instancias ARM disponibles"
- Intenta a las 3-4 AM UTC
- Cambia de región (Frankfurt, Amsterdam, London)
- Usa el script de auto-retry de la comunidad

### "Container se reinicia constantemente"
```bash
docker compose -f docker-compose.prod.yml logs api
# Revisar errores y corregir .env
```

### "No puedo conectar por SSH"
- Verifica Security List tiene puerto 22 abierto
- Verifica que usas la clave correcta
- Verifica el usuario correcto (`ubuntu` para Ubuntu, `opc` para Oracle Linux)

---

## 📊 Resumen de Costos

| Concepto | Costo |
|----------|-------|
| Oracle Cloud VM | $0 |
| Storage 100GB | $0 |
| Dominio DuckDNS | $0 |
| SSL (Caddy) | $0 |
| Groq API | $0 |
| **TOTAL** | **$0** |

🎉 **¡Deployment 100% gratis!**
