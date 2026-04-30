# ============================================================
# INSTRUCCIONES DE INSTALACIÓN Y EJECUCIÓN
# Clínica Odontológica El Alba — Sistema de Gestión
# ============================================================

## FASE 5 — INSTRUCCIONES COMPLETAS

### 1. PRERREQUISITOS

Antes de comenzar, asegúrate de tener instalado:
- Python 3.11+
- MariaDB 10.11+
- pip
- virtualenv o venv

---

### 2. CREAR Y ACTIVAR EL ENTORNO VIRTUAL

```bash
# En la raíz del proyecto (clinica_alba/)
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

---

### 3. INSTALAR DEPENDENCIAS

```bash
pip install -r requirements.txt
```

**Nota para Windows**: si `mysqlclient` falla al instalar, usa este comando alternativo:
```bash
pip install mysqlclient --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/
```
O instala primero el conector de Microsoft:
```bash
pip install pymysql
# Luego en config/__init__.py agregar:
# import pymysql; pymysql.install_as_MySQLdb()
```

---

### 4. CONFIGURAR VARIABLES DE ENTORNO

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tu editor preferido
nano .env  # o notepad .env en Windows
```

Valores mínimos a configurar en `.env`:
```
SECRET_KEY=clave-super-secreta-larga-y-aleatoria
DEBUG=True
DB_NAME=clinica_alba
DB_USER=root
DB_PASSWORD=tu_password_de_mysql
DB_HOST=127.0.0.1
DB_PORT=3306
```

---

### 5. CONFIGURAR MARIADB

#### 5.1 Crear la base de datos

```sql
-- Conectarse a MariaDB
mysql -u root -p

-- Crear la base de datos (CHARACTER SET obligatorio para utf8mb4)
CREATE DATABASE clinica_alba
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Crear usuario dedicado (recomendado para producción)
CREATE USER 'clinica_user'@'localhost' IDENTIFIED BY 'password_seguro';
GRANT ALL PRIVILEGES ON clinica_alba.* TO 'clinica_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 5.2 Opción A: Base de datos nueva (Django gestiona la estructura)

```bash
# Django creará todas las tablas via migraciones
python manage.py makemigrations
python manage.py migrate
```

#### 5.3 Opción B: Base de datos existente con el script SQL proporcionado

```bash
# Primero ejecutar el script SQL original para crear tablas y triggers
mysql -u root -p clinica_alba < schema_original.sql

# Luego crear las migraciones sin aplicarlas (solo registrar el estado)
python manage.py migrate --fake-initial
```

---

### 6. CARGAR DATOS SEMILLA

El script SQL ya incluye los datos iniciales (sexos, roles, especialidades, etc.).
Si partiste de una BD vacía con migraciones, carga el fixture:

```bash
# Los datos del SQL ya están incluidos en el fixture
python manage.py loaddata fixtures/initial_data.json
```

---

### 7. CREAR SUPERUSUARIO

```bash
# Opción A: Script dedicado
python crear_superusuario.py

# El script crea:
# username: admin
# password: Admin1234!
# ⚠️ CAMBIA LA CONTRASEÑA después del primer inicio de sesión
```

---

### 8. RECOPILAR ARCHIVOS ESTÁTICOS

```bash
python manage.py collectstatic --noinput
```

---

### 9. EJECUTAR EL SERVIDOR DE DESARROLLO

```bash
python manage.py runserver
```

Accede en: **http://127.0.0.1:8000**

Login inicial: `admin` / `Admin1234!`

---

### 10. EJECUTAR LOS TESTS

```bash
# Todos los tests
python manage.py test tests

# Un módulo específico
python manage.py test tests.test_agenda
python manage.py test tests.test_pagos
python manage.py test tests.test_auth

# Con verbosidad
python manage.py test tests -v 2
```

---

### 11. CONFIGURACIÓN DJANGO_SETTINGS_MODULE

El `manage.py` usa `config.settings.development` por defecto.
Para producción:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
# o en Windows:
set DJANGO_SETTINGS_MODULE=config.settings.production
```

---

### 12. ESTRUCTURA FINAL DEL PROYECTO

```
clinica_alba/
├── manage.py
├── requirements.txt
├── .env.example
├── crear_superusuario.py
├── config/
│   ├── settings/base.py, development.py
│   └── urls.py
├── apps/
│   ├── core/          → middlewares, mixins, utils, tags
│   ├── accounts/      → auth custom, roles
│   ├── personas/      → identidad base
│   ├── pacientes/     → gestión de pacientes
│   ├── odontologos/   → odontólogos, especialidades, horarios
│   ├── agenda/        → citas, calendario, historial
│   ├── fichas/        → fichas clínicas, evoluciones, adjuntos
│   ├── antecedentes/  → antecedentes médicos
│   ├── odontograma/   → odontograma visual
│   ├── tratamientos/  → tratamientos y planes
│   ├── presupuestos/  → presupuestos y emisión
│   ├── pagos/         → pagos y validación anti-sobrepago
│   ├── caja/          → apertura, cierre, movimientos
│   ├── dashboard/     → KPIs y gráficos
│   └── auditoria/     → bitácora de acciones
├── templates/         → templates por app
├── static/css/main.css → diseño pastel profesional
├── media/             → adjuntos clínicos
└── tests/             → suite de pruebas
```

---

### 13. DECISIONES TÉCNICAS IMPORTANTES

| Decisión | Razón |
|---|---|
| `AbstractBaseUser` propio | La tabla `usuarios` ya existe y no es `auth_user` |
| `CustomAuthBackend` | Valida `estado_acceso` antes de autenticar |
| `UsuarioRol` custom | Evita la complejidad del sistema de permisos de Django |
| `select_for_update()` en pagos | Previene race conditions de sobrepago concurrente |
| Solapamiento en `CitaService` | Filtra estados `cancelada`/`reprogramada` que liberan el slot |
| `db_table` en todos los modelos | Mapeo exacto al esquema SQL original |
| `CharField(primary_key=True)` en `PiezaDental` | La PK es VARCHAR en el SQL original |
| HTMX + Django Templates | Sin SPA: interactividad sin complejidad de framework JS |
| Triggers SQL como fallback | Los servicios validan primero; los triggers protegen la integridad en BD |

---

### 14. SEGURIDAD EN PRODUCCIÓN

```python
# settings/production.py (crear cuando corresponda)
DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
ALLOWED_HOSTS = ["tu-dominio.cl"]
```

---

### 15. VARIABLES DE ENTORNO EN PRODUCCIÓN

Usar un gestor de secretos (AWS Secrets Manager, HashiCorp Vault, etc.)
o al menos un archivo `.env` fuera del repositorio con permisos `600`.
