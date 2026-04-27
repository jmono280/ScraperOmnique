Ready for review
Select text to add comments on the plan
Plan: MCP Server para Dropbox (omnique_scraper)
Context
El usuario quiere un servidor MCP que exponga herramientas para acceder a Dropbox desde Claude Code. El token ya está configurado en config.py. El MCP permitirá listar, subir, descargar y buscar archivos de Dropbox directamente desde Claude Code sin salir del editor.

Archivo nuevo: mcp_dropbox.py
Usa FastMCP (librería mcp) para crear el servidor con estas 6 herramientas:

Tool	Descripción
listar_archivos(carpeta)	Lista archivos/carpetas en una ruta de Dropbox
info_archivo(ruta)	Metadata de un archivo (tamaño, fecha, etc.)
buscar_archivos(query, carpeta)	Busca archivos por nombre
subir_archivo(ruta_local, destino_dropbox)	Sube un archivo local
descargar_archivo(ruta_dropbox, destino_local)	Descarga un archivo a local
crear_carpeta(ruta)	Crea una carpeta en Dropbox
El token se lee desde config.py (CLOUD_CONFIG["dropbox_token"]), sin duplicar config.

Registro en Claude Code
Agregar en ~/.claude/settings.json:

{
  "mcpServers": {
    "dropbox-omnique": {
      "command": "/home/gutidev/Documents/Dev/omnique_scraper/.venv/bin/python",
      "args": ["mcp_dropbox.py"],
      "cwd": "/home/gutidev/Documents/Dev/omnique_scraper"
    }
  }
}
Dependencia nueva
pip install mcp dropbox
(dropbox ya puede estar instalado por uploader.py)

Archivos afectados
Nuevo: mcp_dropbox.py
Editar: ~/.claude/settings.json (agregar el servidor)
Sin cambios: config.py, uploader.py, resto del proyecto
Verificación
Reiniciar Claude Code
Ejecutar /mcp para ver que dropbox-omnique aparece en la lista
Pedir a Claude: "lista los archivos en /omnique_reportes" — debe devolver el contenido real de Dropbox