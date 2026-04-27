"""
Prueba la conexión a Dropbox sin modificar nada.
Corre desde la raíz:  python utils/test_dropbox.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dropbox
from config import CLOUD_CONFIG

def main():
    print("Conectando a Dropbox...")
    dbx = dropbox.Dropbox(
        app_key=CLOUD_CONFIG["dropbox_app_key"],
        app_secret=CLOUD_CONFIG["dropbox_app_secret"],
        oauth2_refresh_token=CLOUD_CONFIG["dropbox_refresh_token"],
    )

    cuenta = dbx.users_get_current_account()
    print(f"  Cuenta:  {cuenta.name.display_name}")
    print(f"  Email:   {cuenta.email}")

    result = dbx.files_list_folder("/omnique_reportes")
    entradas = result.entries
    print(f"  Archivos en /omnique_reportes: {len(entradas)}")
    for e in entradas[:5]:
        print(f"    - {e.name}")
    if len(entradas) > 5:
        print(f"    ... y {len(entradas) - 5} más")

    print("\nConexión OK")

if __name__ == "__main__":
    try:
        main()
    except dropbox.exceptions.AuthError as e:
        print(f"Error de autenticación: {e}")
        print("Verifica que el refresh_token en config.py sea correcto.")
    except dropbox.exceptions.ApiError as e:
        print(f"Error de API: {e}")
