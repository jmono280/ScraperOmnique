"""
Prueba la conexión a Google Drive sin modificar nada.
Corre desde la raíz:  python utils/test_gdrive.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from config import CLOUD_CONFIG

SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "token.json")

def main():
    if not os.path.exists(TOKEN_FILE):
        print("Error: token.json no encontrado.")
        print("Corre primero:  python utils/get_gdrive_token.py")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    print("Conectando a Google Drive...")
    service = build("drive", "v3", credentials=creds)

    about = service.about().get(fields="user").execute()
    print(f"  Cuenta:  {about['user']['displayName']}")
    print(f"  Email:   {about['user']['emailAddress']}")

    folder_id = CLOUD_CONFIG["folder_id"]
    result = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(name, mimeType, size)",
        pageSize=10,
    ).execute()

    archivos = result.get("files", [])
    print(f"  Archivos en carpeta ({folder_id}): {len(archivos)}")
    for f in archivos[:5]:
        size = f.get("size", "-")
        size_kb = f"{round(int(size)/1024, 1)} KB" if size != "-" else "carpeta"
        print(f"    - {f['name']}  ({size_kb})")
    if len(archivos) > 5:
        print(f"    ... y {len(archivos) - 5} más")

    print("\nConexión OK")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
