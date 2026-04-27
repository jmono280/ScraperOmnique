"""
Autorización inicial de Google Drive (una sola vez).
Requiere credentials.json descargado de Google Cloud Console
(tipo: OAuth 2.0 Client ID → Desktop app).

Instrucciones:
  1. Coloca credentials.json en la raíz del proyecto
  2. Corre:  python utils/get_gdrive_token.py
  3. Se abre el browser — inicia sesión y autoriza
  4. Se crea token.json en la raíz del proyecto
  5. Ya puedes correr el pipeline normalmente
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "token.json")

if not os.path.exists(CREDENTIALS_FILE):
    print("Error: no se encuentra credentials.json en la raíz del proyecto.")
    print("Descárgalo de Google Cloud Console → APIs & Services → Credentials")
    print("Tipo: OAuth 2.0 Client ID → Desktop app")
    sys.exit(1)

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
creds = flow.run_local_server(port=0)

with open(TOKEN_FILE, "w") as f:
    f.write(creds.to_json())

print(f"\ntoken.json guardado en: {os.path.abspath(TOKEN_FILE)}")
print("Ya puedes correr el pipeline.")
