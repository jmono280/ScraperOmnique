# Configuración de Cloud Storage

Guía de configuración para los dos proveedores soportados: **Google Drive** y **Dropbox**.

---

## Google Drive — OAuth2 con Refresh Token (cuenta personal)

Autorización única en el browser → `token.json` con refresh token → el SDK renueva automáticamente. Compatible con cuentas personales de Google.

### 1. Crear proyecto y habilitar la API

1. Ve a [console.cloud.google.com](https://console.cloud.google.com)
2. Crea un proyecto nuevo o usa uno existente
3. En el menú lateral: **APIs & Services → Library**
4. Busca **"Google Drive API"** y haz clic en **Enable**

### 2. Crear credenciales OAuth 2.0

1. Ve a **APIs & Services → Credentials**
2. Clic en **+ Create Credentials → OAuth 2.0 Client ID**
3. Si te pide configurar la pantalla de consentimiento, hazlo primero (tipo: **External**, cualquier nombre)
4. **Application type:** Desktop app
5. Clic en **Create**
6. Descarga el JSON → renómbralo a `credentials.json` y ponlo en la raíz del proyecto:

```
omnique_scraper/
├── credentials.json   ← aquí (no subir a git)
├── token.json         ← se genera automáticamente
├── config.py
└── ...
```

### 3. Autorizar la app (una sola vez)

```bash
python utils/get_gdrive_token.py
```

Se abre el browser, inicias sesión con tu cuenta de Google y autorizas. Se crea `token.json` en la raíz. De ahí en adelante el pipeline no necesita browser.

### 4. Obtener el folder ID

Copia el ID de la carpeta destino desde la URL de Google Drive:
```
https://drive.google.com/drive/folders/1aBcDeFgHiJkLmN
                                        ^^^^^^^^^^^^^^^^ este es el folder_id
```

### 5. Configurar `config.py`

```python
CLOUD_CONFIG = {
    "provider": "google_drive",
    "folder_id": "1aBcDeFgHiJkLmN",  # ID de la carpeta de Drive
    # ...claves de Dropbox se pueden dejar aunque no se usen
}
```

### 6. Instalar dependencias

```bash
pip install google-api-python-client google-auth google-auth-oauthlib
```

### Probar la conexión

```bash
python utils/test_gdrive.py
```

---

## Dropbox — OAuth2 con Refresh Token

Usa `app_key` + `app_secret` + `refresh_token`. El SDK renueva el access token automáticamente — sin los 4 horas de expiración del token simple.

### 1. Crear una App en Dropbox

1. Ve a [dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)
2. Clic en **Create app**
3. Configuración:
   - **Choose an API:** Scoped Access
   - **Type of access:** Full Dropbox
   - **Name:** `omnique-scraper` (o el que quieras)
4. Clic en **Create app**

### 2. Configurar permisos

En la pestaña **Permissions** de tu app, activa:

- `files.content.write` — para subir archivos
- `files.content.read` — para listar/descargar

Clic en **Submit** al final.

### 3. Obtener App Key y App Secret

En la pestaña **Settings**, sección **OAuth 2**, copia:
- `App key`
- `App secret`

### 4. Generar el Refresh Token (una sola vez)

Edita `utils/get_refresh_token.py` con tu `APP_KEY` y `APP_SECRET`, luego corre:

```bash
python utils/get_refresh_token.py
```

Sigue las instrucciones: abre la URL, autoriza la app, pega el código. El script imprime el `refresh_token`.

### 5. Configurar `config.py`

```python
CLOUD_CONFIG = {
    "provider": "dropbox",
    "dropbox_app_key":       "tu_app_key",
    "dropbox_app_secret":    "tu_app_secret",
    "dropbox_refresh_token": "el_token_del_paso_4",
    # ...folder_id se puede dejar aunque no se use
}
```

Los archivos quedan organizados automáticamente así en tu Dropbox:

```
/omnique_reportes/
└── 2026/
    └── 04/
        ├── hours_20260420.pdf
        ├── hours_detail_20260420.pdf
        └── work_in_progress_detail_20260420.xlsx
```

### 6. Instalar dependencias

```bash
pip install dropbox
```

### Probar la conexión

```bash
python utils/test_dropbox.py
```

---

## Cambiar de proveedor

Solo modifica `provider` en `config.py`:

```python
CLOUD_CONFIG = {
    "provider": "dropbox",      # ← "dropbox" o "google_drive"
    ...
}
```

---

## Seguridad — archivos a excluir de git

```
# .gitignore
service_account.json
```

El `refresh_token` de Dropbox y el `service_account.json` de Google son credenciales sensibles. Nunca los subas al repositorio.
