import asyncio
from playwright.async_api import async_playwright
from config import OMNIQUE_CONFIG
import os
from datetime import datetime
from logger import logger
from uploader import subir_archivo


REPORT_URLS = {
    "hours": "https://app.omnique.com/Company/954200/Shop/1/Reports/Reporting/Index#section/Sales/report/Hours",
    "hours_detail": "https://app.omnique.com/Company/954200/Shop/1/Reports/Reporting/Index#section/Sales/report/HoursDetail",
    "daily_sales": "https://app.omnique.com/Company/954200/Shop/1/Reports/Reporting/Index#section/Sales/report/DailySales",
    "work_in_progress_detail": "https://app.omnique.com/Company/954200/Shop/1/Reports/Reporting/Index#section/Sales/report/WorkinProgressDetail",
}


async def _login(page):
    logger.info("Accediendo a Omnique...")
    await page.goto(OMNIQUE_CONFIG["url"])
    await page.wait_for_load_state("networkidle")
    await page.fill('input[name="Username"]', OMNIQUE_CONFIG["username"])
    await page.fill('input[name="Password"]', OMNIQUE_CONFIG["password"])
    await page.click('button[type="submit"]')
    await page.wait_for_load_state("networkidle")
    logger.info("Login exitoso")


# ── Funciones privadas: reciben page ya autenticada ──────────────────────────

async def _descargar_hours(page):
    logger.info("Navegando al reporte Hours...")
    await page.goto(REPORT_URLS["hours"])
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2000)

    hoy = datetime.now()
    primer_dia = hoy.replace(day=1).strftime("%m/%d/%Y")
    ultimo_dia = hoy.strftime("%m/%d/%Y")

    await page.fill('#startDate', primer_dia)
    await page.fill('#endDate', ultimo_dia)
    logger.debug(f"Fechas configuradas: {primer_dia} - {ultimo_dia}")
    await page.select_option('#Format', value='PDFLegend')
    logger.debug("Formato: PDF w/Legend")

    fecha_str = hoy.strftime("%Y%m%d")
    ruta_local = f"{OMNIQUE_CONFIG['download_dir']}/hours_{fecha_str}.pdf"
    async with page.expect_download(timeout=60000) as download_info:
        await page.click('button:has-text("Run Report")')
    await (await download_info.value).save_as(ruta_local)
    logger.info(f"Reporte descargado: {ruta_local}")
    return ruta_local


async def _descargar_hours_detail(page):
    logger.info("Navegando al reporte Hours Detail...")
    await page.goto(REPORT_URLS["hours_detail"])
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(15000)

    hoy = datetime.now()
    primer_dia = hoy.replace(day=1).strftime("%m/%d/%Y")
    ultimo_dia = hoy.strftime("%m/%d/%Y")

    await page.fill('#StartDate', primer_dia)
    await page.fill('#EndDate', ultimo_dia)
    logger.debug(f"Fechas configuradas: {primer_dia} - {ultimo_dia}")
    await page.select_option('#Format', value='PDF')
    logger.debug("Formato: PDF")

    fecha_str = hoy.strftime("%Y%m%d")
    ruta_local = f"{OMNIQUE_CONFIG['download_dir']}/hours_detail_{fecha_str}.pdf"
    async with page.expect_download(timeout=60000) as download_info:
        await page.click('button:has-text("Run Report")')
    await (await download_info.value).save_as(ruta_local)
    logger.info(f"Reporte descargado: {ruta_local}")
    return ruta_local


async def _descargar_daily_sales(page):
    logger.info("Navegando al reporte Daily Sales...")
    await page.goto(REPORT_URLS["daily_sales"])
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(15000)

    hoy = datetime.now()
    primer_dia = hoy.replace(day=1).strftime("%m/%d/%Y")
    ultimo_dia = hoy.strftime("%m/%d/%Y")

    await page.fill('#StartDate', primer_dia)
    await page.fill('#EndDate', ultimo_dia)
    logger.debug(f"Fechas configuradas: {primer_dia} - {ultimo_dia}")
    await page.select_option('#ReportFormat', value='PDF')
    logger.debug("Formato: PDF")

    fecha_str = hoy.strftime("%Y%m%d")
    ruta_local = f"{OMNIQUE_CONFIG['download_dir']}/daily_sales_{fecha_str}.pdf"
    async with page.expect_download(timeout=60000) as download_info:
        await page.click('button:has-text("Run Report")')
    await (await download_info.value).save_as(ruta_local)
    logger.info(f"Reporte descargado: {ruta_local}")
    return ruta_local


async def _descargar_work_in_progress_detail(page):
    logger.info("Navegando al reporte Work In Progress Detail...")
    await page.goto(REPORT_URLS["work_in_progress_detail"])
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(15000)

    hoy = datetime.now()
    primer_dia = hoy.replace(day=1).strftime("%m/%d/%Y")
    ultimo_dia = hoy.strftime("%m/%d/%Y")

    await page.fill('#StartDate', primer_dia)
    await page.fill('#EndDate', ultimo_dia)
    logger.debug(f"Fechas configuradas: {primer_dia} - {ultimo_dia}")

    fecha_str = hoy.strftime("%Y%m%d")
    ruta_local = f"{OMNIQUE_CONFIG['download_dir']}/work_in_progress_detail_{fecha_str}.xlsx"
    async with page.expect_download(timeout=60000) as download_info:
        await page.click('button:has-text("Run Report")')
    await (await download_info.value).save_as(ruta_local)
    logger.info(f"Reporte descargado: {ruta_local}")
    return ruta_local


# ── Funciones públicas: sesión propia (uso standalone) ───────────────────────

async def descargar_reporte_hours(headless=True):
    os.makedirs(OMNIQUE_CONFIG["download_dir"], exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await _login(page)
        ruta = await _descargar_hours(page)
        await browser.close()
    return ruta


async def descargar_reporte_hours_detail(headless=True):
    os.makedirs(OMNIQUE_CONFIG["download_dir"], exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await _login(page)
        ruta = await _descargar_hours_detail(page)
        await browser.close()
    return ruta


async def descargar_reporte_daily_sales(headless=True):
    os.makedirs(OMNIQUE_CONFIG["download_dir"], exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await _login(page)
        ruta = await _descargar_daily_sales(page)
        await browser.close()
    return ruta


async def descargar_reporte_work_in_progress_detail(headless=True):
    os.makedirs(OMNIQUE_CONFIG["download_dir"], exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await _login(page)
        ruta = await _descargar_work_in_progress_detail(page)
        await browser.close()
    return ruta


async def descargar_todos(headless=True):
    """Login único — descarga los 4 reportes en una sola sesión."""
    os.makedirs(OMNIQUE_CONFIG["download_dir"], exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await _login(page)
        ruta_hours                   = await _descargar_hours(page)
        ruta_hours_detail            = await _descargar_hours_detail(page)
        ruta_daily_sales             = await _descargar_daily_sales(page)
        ruta_work_in_progress_detail = await _descargar_work_in_progress_detail(page)
        await browser.close()
    return ruta_hours, ruta_hours_detail, ruta_daily_sales, ruta_work_in_progress_detail


if __name__ == "__main__":
    archivos = os.listdir(OMNIQUE_CONFIG["download_dir"])
    for archivo in archivos:
        subir_archivo(OMNIQUE_CONFIG["download_dir"] + "/" + archivo)
        logger.debug(f"Archivo local eliminado: {archivo}")
