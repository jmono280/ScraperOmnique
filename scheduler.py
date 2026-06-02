import argparse
import asyncio
import schedule
import time
import os
from scraper import descargar_todos, descargar_reporte_hours
from blitzpay_scraper import scrape_payment_report
from uploader import subir_archivo
from logger import logger, notify_zapier
from config import OMNIQUE_CONFIG

parser = argparse.ArgumentParser(description="Scheduler Omnique + Blitzpay")
parser.add_argument("--hora",      default="14:00",  help="Hora de ejecución diaria (HH:MM)")
parser.add_argument("--fecha",     default=None,      help="Fecha inicio para Blitzpay (YYYY-MM-DD). Implica --run-now")
parser.add_argument("--fecha-fin", default=None,      help="Fecha fin para Blitzpay (YYYY-MM-DD). Default: igual a --fecha")
parser.add_argument("--run-now",   action="store_true", help="Ejecutar ambos pipelines inmediatamente y salir")
args = parser.parse_args()

# --fecha implica ejecución inmediata
if args.fecha:
    args.run_now = True



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


def pipeline_blitzpay(date_from=None, date_to=None):
    logger.info("=" * 60)
    logger.info("Iniciando pipeline Blitzpay")
    notify_zapier("blitzpay_start", "info", "Pipeline Blitzpay iniciado")
    try:
        ruta = asyncio.run(scrape_payment_report(date_from=date_from, date_to=date_to))
        if ruta:
            subir_archivo(ruta, carpeta="blitzpay_reportes")
            os.remove(ruta)
            logger.debug(f"Archivo local eliminado: {ruta}")
            logger.info("Pipeline Blitzpay completado")
            notify_zapier("blitzpay_success", "ok", "Reporte Blitzpay procesado correctamente")
        else:
            logger.warning("Pipeline Blitzpay: scrape_payment_report no retornó archivo")
    except Exception as e:
        logger.error(f"Error en pipeline Blitzpay: {e}", exc_info=True)
        notify_zapier("blitzpay_error", "error", f"Error pipeline Blitzpay: {e}")


if args.run_now:
    # Modo one-shot: ejecutar ambos pipelines inmediatamente y salir
    date_from = args.fecha
    date_to   = args.fecha_fin or args.fecha
    logger.info(f"Modo one-shot | Blitzpay fechas: {date_from or 'ayer'} → {date_to or 'ayer'}")
    pipeline_omnique()
    pipeline_blitzpay(date_from=date_from, date_to=date_to)
else:
    # Modo scheduler: programar ejecución diaria a la hora indicada
    schedule.every().day.at(args.hora).do(pipeline_omnique)
    schedule.every().day.at(args.hora).do(pipeline_blitzpay)
    logger.info(f"Scheduler activo — ejecución diaria a las {args.hora}")
    notify_zapier("scheduler_start", "info", f"Scheduler iniciado, ejecución programada a las {args.hora}")
    while True:
        schedule.run_pending()
        time.sleep(60)


# python scheduler.py                                        # scheduler diario a las 14:00
# python scheduler.py --hora 08:00                          # scheduler diario a las 8am
# python scheduler.py --run-now                             # ejecutar ahora (fechas por defecto)
# python scheduler.py --fecha 2026-05-13                    # ejecutar ahora, Blitzpay con fecha específica
# python scheduler.py --fecha 2026-05-01 --fecha-fin 2026-05-15  # ejecutar ahora con rango
