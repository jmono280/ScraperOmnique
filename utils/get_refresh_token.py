"""
Script de un solo uso para obtener el refresh_token de Dropbox.
Requiere APP_KEY y APP_SECRET de https://www.dropbox.com/developers/apps

Instrucciones:
  1. Reemplaza APP_KEY y APP_SECRET con los valores de tu app en Dropbox
  2. Corre:  python get_refresh_token.py
  3. Abre la URL en el navegador y autoriza la app
  4. Pega el código de autorización
  5. Copia el REFRESH TOKEN y pégalo en config.py → dropbox_refresh_token
  6. Borra este archivo (ya no lo necesitas)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dropbox import DropboxOAuth2FlowNoRedirect
from config import CLOUD_CONFIG


APP_KEY    = CLOUD_CONFIG["dropbox_app_key"]
APP_SECRET = CLOUD_CONFIG["dropbox_app_secret"]

auth_flow = DropboxOAuth2FlowNoRedirect(
    APP_KEY, APP_SECRET, token_access_type="offline"
)

authorize_url = auth_flow.start()
print("1. Ve a esta URL y autoriza la app:")
print("  ", authorize_url)
print()
auth_code = input("2. Pega el código de autorización aquí: ").strip()

oauth_result = auth_flow.finish(auth_code)
print()
print("=" * 60)
print("REFRESH TOKEN (cópialo en config.py):")
print(oauth_result.refresh_token)
print("=" * 60)
