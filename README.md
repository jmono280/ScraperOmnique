# Omnique Scraper

Scraper automatizado para descargar reportes desde [Omnique](https://app.omnique.com) y subirlos a la nube (Google Drive o Dropbox).

---

## Estructura

```
omnique_scraper/
├── config.py              # Credenciales y configuración de destino cloud
├── scraper.py             # Playwright: login + descarga de reportes
├── uploader.py            # Subida a cloud (Google Drive / Dropbox)
├── scheduler.py           # Pipeline automático con schedule
├── service_account.json   # Credenciales de Google Drive (no subir a git)
├── downloads/             # Carpeta temporal de descargas
└── utils/
    ├── get_refresh_token.py  # Obtener refresh token de Dropbox (una sola vez)
    ├── test_gdrive.py        # Probar conexión a Google Drive
    └── test_dropbox.py       # Probar conexión a Dropbox
```

---

## Configuración

Editar `config.py`:

```python
OMNIQUE_CONFIG = {
    "url": "https://app.omnique.com/Login.aspx",
    "username": "tu_usuario",
    "password": "tu_password",
    "download_dir": "./downloads"
}

CLOUD_CONFIG = {
    "provider": "dropbox",        # "dropbox" | "google_drive"

    # Dropbox — OAuth2 con refresh token (no expira)
    "dropbox_app_key":       "tu_app_key",
    "dropbox_app_secret":    "tu_app_secret",
    "dropbox_refresh_token": "tu_refresh_token",

    # Google Drive — service account
    "folder_id": "ID_DE_LA_CARPETA_DE_DRIVE",
}
```

Para instrucciones detalladas de cada proveedor ver [`config_cloud.md`](config_cloud.md).

---

## Instalación y puesta en marcha

### 1. Verificar la versión de Python

El proyecto corre en **Python 3.14**. Para confirmar la versión del entorno:

```bash
# Con el entorno activo
python --version

# O directamente desde el venv
.venv/bin/python --version
```

### 2. Crear el entorno virtual

```bash
python3.14 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 3. Instalar dependencias

```bash
pip install playwright schedule dropbox google-api-python-client google-auth google-auth-oauthlib
playwright install chromium
```

O si ya tienes `requirements.txt`:

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Generar requirements.txt (para replicar en servidor)

```bash
pip freeze > requirements.txt
```

### 5. Configurar credenciales cloud

Seguir las instrucciones de [`config_cloud.md`](config_cloud.md) según el proveedor elegido.

---

## Uso

### Descargar reportes manualmente

Cada función genera el nombre de archivo automáticamente con la fecha del día.

```python
import asyncio
from scraper import (
    descargar_reporte_hours,
    descargar_reporte_hours_detail,
    descargar_reporte_daily_sales,
    descargar_reporte_work_in_progress_detail,
    descargar_todos,
)

# Reporte individual (abre su propia sesión)
asyncio.run(descargar_reporte_hours())
asyncio.run(descargar_reporte_hours_detail())
asyncio.run(descargar_reporte_daily_sales())
asyncio.run(descargar_reporte_work_in_progress_detail())

# Los 4 de una vez — un solo login
asyncio.run(descargar_todos())

# Con navegador visible (debug)
asyncio.run(descargar_todos(headless=False))
```

### Subir a la nube

```python
from uploader import subir_archivo

subir_archivo("downloads/hours_20260420.pdf")
```

El proveedor se toma de `CLOUD_CONFIG["provider"]` en `config.py`.

### Pipeline automático

```bash
python scheduler.py               # usa 14:00 por defecto
python scheduler.py --hora 08:00  # ejecuta a las 8am
```

Ejecuta el pipeline todos los días a la hora indicada: descarga los reportes, los sube a Dropbox y limpia los archivos locales.

---

## Despliegue con Docker

### Requisitos previos en el servidor

- Docker y Docker Compose instalados.
- Archivo `.env` con las variables de entorno (ver `.env.example`).

### 1. Subir el proyecto al servidor

```bash
# Desde tu máquina local
scp -r . usuario@ip-servidor:/ruta/omnique_scraper
```

O clonar el repositorio directamente en el servidor si está en git.

### 2. Crear el `.env` en el servidor

```bash
cp .env.example .env
nano .env   # completar con credenciales reales
```

### 3. Construir y levantar el contenedor

```bash
docker compose up -d --build
```

### 4. Ver logs en tiempo real

```bash
docker compose logs -f
```

### 5. Cambiar la hora de ejecución

Editar `docker-compose.yml`, línea `command:`, y aplicar:

```bash
docker compose up -d
```

### 6. Detener el scheduler

```bash
docker compose down
```

---

## Probar la conexión

```bash
python utils/test_gdrive.py      # Google Drive
python utils/test_dropbox.py     # Dropbox
```

Ambos scripts verifican autenticación y listan los archivos en la carpeta destino sin modificar nada.

---

## Reportes disponibles

| Función                                    | Reporte                        | Formato      |
|--------------------------------------------|--------------------------------|--------------|
| `descargar_reporte_hours`                  | Sales > Hours                  | PDF w/Legend |
| `descargar_reporte_hours_detail`           | Sales > HoursDetail            | PDF          |
| `descargar_reporte_daily_sales`            | Sales > DailySales             | PDF          |
| `descargar_reporte_work_in_progress_detail`| Sales > WorkinProgressDetail   | XLSX         |

Todos descargan el rango del mes actual (primer día al día de hoy).
`descargar_todos()` ejecuta los 4 con un único login.

---

## Notas de desarrollo

### Inspeccionar campos de un formulario

Para identificar los `id` de los inputs de una página antes de scrapearla:

```python
inputs = await page.evaluate("""
    () => Array.from(document.querySelectorAll('input')).map(el => ({
        id: el.id, name: el.name, type: el.type, placeholder: el.placeholder
    }))
""")
print("Inputs encontrados:", inputs)
```

Se puede hacer lo mismo con `select`, `button`, etc. cambiando el selector en `querySelectorAll`.

## Comandos ejecución test_blitzpay

### Collection Stats — Shay Carter

```bash
# Ayer (default)
python blitzpay_scraper.py

# Fecha específica
python blitzpay_scraper.py 2026-05-13

# Rango de fechas
python blitzpay_scraper.py 2026-05-01 2026-05-13

# Modo headless (sin ventana)
python blitzpay_scraper.py --headless
python blitzpay_scraper.py 2026-05-13 --headless
```

Descarga la tabla **Collection Stats** filtrada por Shay Carter y la imprime en consola.  
Screenshots en `downloads/blitzpay_test/`.

---

### Payment Report — Paid + Merchant Portal + Shay Carter

```bash
# Ayer (default)
python blitzpay_scraper.py pay-report

# Fecha específica
python blitzpay_scraper.py pay-report 2026-05-13

# Rango de fechas
python blitzpay_scraper.py pay-report 2026-05-10 2026-05-15

# Modo headless
python blitzpay_scraper.py pay-report 2026-05-10 2026-05-15 --headless
```

Aplica filtros: **Status = Paid**, **Payment Origin = Merchant Portal**, **User = Shay Carter**.  
Descarga el Excel en `downloads/blitzpay_test/payment_report_YYYYMMDD_HHMMSS.xlsx`.

---

### Explorar Payment Report (debug)

```bash
python blitzpay_scraper.py pay-explore
```

Navega al Payment Report, toma screenshots y vuelca en consola todos los controles
interactivos (selects, checkboxes, inputs ARIA) para diagnosticar la estructura de la página.