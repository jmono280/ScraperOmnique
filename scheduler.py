import argparse
import asyncio
import schedule
import time
import os
from scraper import descargar_todos, descargar_reporte_hours
from uploader import subir_archivo
from logger import logger, notify_zapier
from config import OMNIQUE_CONFIG

parser = argparse.ArgumentParser(description="Scheduler Omnique")
parser.add_argument("--hora", default="14:00", help="Hora de ejecución diaria (formato HH:MM, e.g. 08:00)")
args = parser.parse_args()



def pipeline_omnique():
    logger.info("=" * 60)
    logger.info("Iniciando pipeline Omnique")
    notify_zapier("pipeline_start", "info", "Pipeline iniciado")

    archivos_subidos = []
    try:
        # 1. Descargar reportes
        logger.info("Descargando reportes...")
        archivos = asyncio.run(descargar_todos())

        #2. Subir cada uno al cloud y limpiar local
        for archivo in archivos:
            subir_archivo(archivo)
            
            archivos_subidos.append(os.path.basename(archivo))
            os.remove(archivo)
            logger.debug(f"Archivo local eliminado: {archivo}")

        logger.info(f"Pipeline completado. Archivos subidos: {len(archivos_subidos)}")
        notify_zapier(
            "pipeline_success",
            "ok",
            f"{len(archivos_subidos)} reportes procesados correctamente",
            archivos=archivos_subidos
        )

    except Exception as e:
        logger.error(f"Error en el pipeline: {e}", exc_info=True)
        notify_zapier(
            "pipeline_error",
            "error",
            f"Error en el pipeline: {e}"
        )


# Programar: todos los días a la hora indicada (--hora HH:MM, default 16:30)
schedule.every().day.at(args.hora).do(pipeline_omnique)

# O los lunes a las 7am para reporte semanal
# schedule.every().monday.at("07:00").do(pipeline_omnique)

logger.info("Scheduler Omnique activo. Esperando próxima ejecución...")
notify_zapier("scheduler_start", "info", "Scheduler iniciado, esperando ejecución programada")

while True:
    schedule.run_pending()
    time.sleep(60)


# python scheduler.py               # usa 16:30 por defecto
# python scheduler.py --hora 08:00  # ejecuta a las 8am
