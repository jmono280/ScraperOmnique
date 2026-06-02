from config import CLOUD_CONFIG
from logger import logger

# ── Google Drive ──────────────────────────────────────────
def subir_a_google_drive(ruta_archivo):
    """pip install google-api-python-client google-auth google-auth-oauthlib"""
    import os, mimetypes
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    SCOPES = ["https://www.googleapis.com/auth/drive"]
    TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError(
                "token.json no existe o no es válido. "
                "Corre utils/get_gdrive_token.py una vez para autorizarte."
            )

    service = build("drive", "v3", credentials=creds)

    nombre_archivo = ruta_archivo.split("/")[-1]
    file_metadata = {
        "name": nombre_archivo,
        "parents": [CLOUD_CONFIG["folder_id"]]
    }
    mime, _ = mimetypes.guess_type(ruta_archivo)
    if mime is None:
        mime = "application/octet-stream"
    media = MediaFileUpload(ruta_archivo, mimetype=mime)
    archivo = service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()

    logger.info(f"Subido a Google Drive: {nombre_archivo} (ID: {archivo['id']})")
    return archivo["id"]


# ── Dropbox ───────────────────────────────────────────────
def subir_a_dropbox(ruta_archivo, carpeta="omnique_reportes"):
    """pip install dropbox"""
    import dropbox
    from datetime import datetime

    dbx = dropbox.Dropbox(
        app_key=CLOUD_CONFIG["dropbox_app_key"],
        app_secret=CLOUD_CONFIG["dropbox_app_secret"],
        oauth2_refresh_token=CLOUD_CONFIG["dropbox_refresh_token"],
    )
    nombre = ruta_archivo.split("/")[-1]
    destino = f"/{carpeta}/{datetime.now().strftime('%Y/%m')}/{nombre}"

    with open(ruta_archivo, "rb") as f:
        dbx.files_upload(f.read(), destino,
                         mode=dropbox.files.WriteMode.overwrite)
    logger.info(f"Subido a Dropbox: {destino}")
    return destino


def subir_archivo(ruta_archivo, carpeta="omnique_reportes"):
    """Router: elige el cloud según config"""
    provider = CLOUD_CONFIG["provider"]
    if provider == "google_drive":
        return subir_a_google_drive(ruta_archivo)
    elif provider == "dropbox":
        return subir_a_dropbox(ruta_archivo, carpeta)