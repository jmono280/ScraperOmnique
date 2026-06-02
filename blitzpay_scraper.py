import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import openpyxl

load_dotenv(Path(__file__).parent / ".env")

BLITZPAY_CONFIG = {
    "login_url": "https://hub.blytzpay.com/#/login",
    "username":  os.getenv("BLITZPAY_USERNAME"),
    "password":  os.getenv("BLITZPAY_PASSWORD"),
}

COLLECTOR_NAME = "Shay Carter"

SCREENSHOT_DIR = Path(__file__).parent / "downloads" / "blitzpay_test"

BASE_URL = (
    "https://hub.blytzpay.com/#/d4e08f47-3063-4717-9fd5-130278575988"
    "/merchant-collection-stats"
)


def _fecha_ayer():
    ayer = datetime.now() - timedelta(days=1)
    return {
        "url": ayer.strftime("%Y-%m-%d"),
        "ui":  ayer.strftime("%m/%d/%Y"),
        "label": ayer.strftime("%Y-%m-%d"),
    }


def _build_stats_url(date_from=None, date_to=None):
    fecha = _fecha_ayer()
    df = date_from or fecha["url"]
    dt = date_to   or fecha["url"]
    return f"{BASE_URL}?date_from={df}&date_to={dt}"


async def _screenshot(page, nombre):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ruta = SCREENSHOT_DIR / nombre
    await page.screenshot(path=str(ruta), full_page=True)
    print(f"  [screenshot] {ruta}")


async def _login(page):
    print("\n[1] Login...")
    await page.goto(BLITZPAY_CONFIG["login_url"])
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(5000)

    username_sel = None
    for sel in ['input[type="email"]', 'input[name="username"]',
                'input[name="email"]', 'input[placeholder*="email" i]']:
        if await page.query_selector(sel):
            username_sel = sel
            break

    password_sel = None
    for sel in ['input[type="password"]', 'input[name="password"]']:
        if await page.query_selector(sel):
            password_sel = sel
            break

    if not username_sel or not password_sel:
        print("  [ERROR] Formulario de login no encontrado.")
        await _screenshot(page, "01_login_error.png")
        return False

    await page.fill(username_sel, BLITZPAY_CONFIG["username"])
    await page.fill(password_sel, BLITZPAY_CONFIG["password"])

    submit_sel = None
    for sel in ['button[type="submit"]', 'button:has-text("Login")',
                'button:has-text("Sign in")']:
        if await page.query_selector(sel):
            submit_sel = sel
            break

    if not submit_sel:
        print("  [ERROR] Botón de submit no encontrado.")
        return False

    await page.click(submit_sel)
    try:
        await page.wait_for_url(lambda url: "login" not in url, timeout=15000)
    except Exception:
        pass
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(5000)
    print(f"  URL tras login: {page.url}")
    return True


async def _navegar_collection_stats(page, stats_url):
    print(f"\n[2] Navegando a Collection Stats ({stats_url})...")
    await page.goto(stats_url)
    await page.wait_for_load_state("networkidle")

    try:
        await page.wait_for_selector("table", timeout=15000)
    except Exception:
        pass

    await page.wait_for_timeout(3000)

    if "collection-stats" not in page.url and "merchant-collection" not in page.url:
        print("  [!] Router SPA no navegó directo, intentando sidebar...")
        link = await page.query_selector(
            'a:has-text("Collection Stats"), [href*="collection-stats"]'
        )
        if link:
            await link.click()
            await page.wait_for_load_state("networkidle")
            try:
                await page.wait_for_selector("table", timeout=15000)
            except Exception:
                pass
            await page.wait_for_timeout(3000)

    await _screenshot(page, "03_collection_stats.png")
    print(f"  URL final: {page.url}")


async def _aplicar_fecha(page, fecha_ui):
    print(f"\n[3] Aplicando fecha en UI: {fecha_ui}...")

    inputs_fecha = await page.query_selector_all(
        'input[type="date"], input[type="text"][class*="date" i], '
        'input[placeholder*="date" i], input[placeholder*="MM" i]'
    )

    if not inputs_fecha:
        todos = await page.query_selector_all("input")
        for inp in todos:
            val = await inp.get_attribute("value") or ""
            if "/" in val and len(val) == 10:
                inputs_fecha.append(inp)

    if len(inputs_fecha) >= 2:
        print(f"  Inputs de fecha encontrados: {len(inputs_fecha)}")
        for inp in inputs_fecha[:2]:
            await inp.click(click_count=3)
            await inp.type(fecha_ui)
        await page.keyboard.press("Tab")
        await page.wait_for_load_state("networkidle")
        try:
            await page.wait_for_selector("table", timeout=10000)
        except Exception:
            pass
        await page.wait_for_timeout(3000)
        await _screenshot(page, "04_fecha_aplicada.png")
        print("  Fecha actualizada en UI.")
    else:
        print("  [WARN] No se encontraron inputs de fecha en la página.")
        print("  (La fecha se aplica desde la URL — probablemente suficiente)")


async def _filtrar_collector(page, nombre):
    print(f"\n[4] Filtrando por '{nombre}'...")

    search_sel = None
    for sel in [
        'input[placeholder*="Search collectors" i]',
        'input[placeholder*="collector" i]',
        'input[placeholder*="search" i]',
    ]:
        el = await page.query_selector(sel)
        if el:
            search_sel = sel
            break

    if not search_sel:
        print("  [WARN] Search box de collectors no encontrado.")
        return False

    print(f"  Search box: {search_sel}")
    await page.fill(search_sel, nombre)
    await page.wait_for_timeout(1500)

    try:
        await page.wait_for_selector(f'td:has-text("{nombre}")', timeout=8000)
    except Exception:
        pass

    await _screenshot(page, "05_filtrado.png")
    return True


async def _extraer_datos(page, nombre):
    print(f"\n[5] Extrayendo datos para '{nombre}'...")

    try:
        await page.wait_for_selector("table tr", timeout=10000)
    except Exception:
        pass

    resultado = await page.evaluate(f"""() => {{
        const tabla = document.querySelector('table');
        if (!tabla) return null;

        const headers = Array.from(tabla.querySelectorAll('th'))
                             .map(h => h.innerText.trim());

        const filas = Array.from(tabla.querySelectorAll('tr')).slice(1);
        const fila = filas.find(r => r.innerText.includes('{nombre}'));
        if (!fila) return {{ headers, fila: null, todas: filas.map(r =>
            Array.from(r.querySelectorAll('td')).map(c => c.innerText.trim())
        )}};

        const celdas = Array.from(fila.querySelectorAll('td'))
                            .map(c => c.innerText.trim());
        return {{ headers, fila: celdas }};
    }}""")

    if not resultado:
        print("  [ERROR] No se encontró tabla en la página.")
        return None

    headers = resultado.get("headers", [])
    fila = resultado.get("fila")

    if not fila:
        print(f"  [WARN] '{nombre}' no apareció en la tabla.")
        todas = resultado.get("todas", [])
        print(f"  Filas disponibles: {[f[0] for f in todas if f]}")
        return None

    datos = dict(zip(headers, fila))
    print(f"\n  {'='*40}")
    print(f"  Collector: {nombre}")
    for k, v in datos.items():
        if k:
            print(f"  {k}: {v}")
    print(f"  {'='*40}")
    return datos


def _agregar_hoja_stats(ruta_excel, datos, date_from, date_to):
    wb = openpyxl.load_workbook(ruta_excel)
    ws = wb.create_sheet(title="Collection Stats")

    # Los th del DOM incluyen "\n(Click to sort ...)" — limpiar
    headers = [k.split("\n")[0].strip() for k in datos.keys()]
    values  = list(datos.values())

    ws.append(headers)
    ws.append(values)
    ws.append([])
    ws.append([f"Período: {date_from} → {date_to}"])
    ws.append([f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])

    wb.save(ruta_excel)
    print(f"  Hoja 'Collection Stats' agregada: {ruta_excel}")


async def test_blitzpay(date_from=None, date_to=None, headless=True):
    fecha = _fecha_ayer()
    stats_url = _build_stats_url(date_from, date_to)

    print("=" * 60)
    print("BLITZPAY — Collection Stats")
    print(f"Collector: {COLLECTOR_NAME}")
    print(f"Fecha: {date_from or fecha['label']} → {date_to or fecha['label']}")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
        )
        page = await context.new_page()

        login_ok = await _login(page)
        if not login_ok:
            print("\n[FALLO] Login fallido.")
            await browser.close()
            return None

        await _navegar_collection_stats(page, stats_url)
        await _aplicar_fecha(page, fecha["ui"])
        await _filtrar_collector(page, COLLECTOR_NAME)
        datos = await _extraer_datos(page, COLLECTOR_NAME)

        await _screenshot(page, "06_final.png")
        await browser.close()

    print(f"\nScreenshots: {SCREENSHOT_DIR}")
    return datos


PAYMENT_REPORT_URL = "https://hub.blytzpay.com/#/payment-report"


async def _set_fecha_payment(page, fecha_start, fecha_end):
    start = page.locator('input[name="start_date"]')
    await start.click(click_count=3)
    await start.type(fecha_start, delay=50)
    await page.wait_for_timeout(300)

    await page.keyboard.press("Tab")
    await page.wait_for_timeout(300)
    await page.keyboard.press("Control+a")
    await page.keyboard.type(fecha_end, delay=50)
    await page.keyboard.press("Tab")
    await page.wait_for_timeout(800)


async def _configurar_dropdown(page, btn_texto, seleccionar, nombre_ss=None):
    btn = await page.query_selector(
        f'button:has-text("{btn_texto}"), [class*="btn"]:has-text("{btn_texto}")'
    )
    if not btn:
        print(f"  [WARN] Botón '{btn_texto}' no encontrado")
        return False

    await btn.click()
    await page.wait_for_timeout(1500)
    ss = nombre_ss or btn_texto.lower().replace(" ", "_")
    await _screenshot(page, f"pay_dropdown_{ss}.png")

    menu = None
    for sel in [
        ".dropdown-menu.show",
        "[class*='dropdown-menu'][class*='show']",
        "ul.show",
        "div.show[class*='dropdown']",
    ]:
        menu = await page.query_selector(sel)
        if menu:
            break

    if not menu:
        print(f"  [WARN] Contenedor .dropdown-menu.show no encontrado para '{btn_texto}'")
        btns = await page.query_selector_all("button")
        for b in btns:
            cls = await b.get_attribute("class") or ""
            if "show" in cls or "active" in cls or "open" in cls:
                print(f"    {await b.inner_text()[:30]} → {cls[:80]}")
        return False

    labels = await menu.query_selector_all("label")
    textos = [(lbl, (await lbl.inner_text()).strip()) for lbl in labels]
    print(f"  Labels en menú: {[t for _, t in textos]}")

    for el, texto in textos:
        if texto.lower() == "select all":
            await el.click()
            await page.wait_for_timeout(500)
            print("  ✓ Select All clickeado")
            break

    for opcion in seleccionar:
        for el, texto in textos:
            if opcion.lower() in texto.lower():
                await el.click()
                await page.wait_for_timeout(300)
                print(f"  ✓ Seleccionado: {texto}")
                break

    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    return True


async def _seleccionar_usuario(page, nombre):
    print(f"\n  Seleccionando usuario: {nombre}...")

    await _screenshot(page, "pay_antes_usuario.png")
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)
    await page.mouse.click(600, 200)
    await page.wait_for_timeout(500)

    # input[name="name"] es interno de Vue Multiselect — clickear el contenedor padre
    contenedor = page.locator('input[name="name"]').locator('..')
    try:
        await contenedor.scroll_into_view_if_needed(timeout=5000)
        await contenedor.click(timeout=8000)
    except Exception:
        print("  Click en contenedor falló, usando force=True...")
        await contenedor.click(force=True)

    await page.wait_for_timeout(1500)
    await _screenshot(page, "pay_usuario_dropdown.png")

    for sel in [
        f'[role="option"]:has-text("{nombre}")',
        f'li:has-text("{nombre}")',
        f'[class*="option"]:has-text("{nombre}")',
    ]:
        try:
            await page.locator(sel).first.click(timeout=4000)
            await page.wait_for_timeout(500)
            print(f"  ✓ Usuario seleccionado: {nombre}")
            return True
        except Exception:
            continue

    print("  Listbox sin match, filtrando por texto...")
    try:
        inp = page.locator('input[name="name"]')
        await inp.fill(nombre[:4])
        await page.wait_for_timeout(1000)
        await page.locator(f'[role="option"]:has-text("{nombre}")').first.click(timeout=4000)
        await page.wait_for_timeout(500)
        print(f"  ✓ Usuario seleccionado (búsqueda): {nombre}")
        return True
    except Exception as e:
        print(f"  [ERROR] No se pudo seleccionar '{nombre}': {e}")
        await _screenshot(page, "pay_usuario_error.png")
        return False


async def scrape_payment_report(date_from=None, date_to=None, headless=True):
    """
    Navega al Payment Report, aplica filtros (Status=Paid, Origin=Merchant Portal,
    User=Shay Carter), descarga el Excel y agrega una hoja con Collection Stats.
    """
    fecha = _fecha_ayer()
    df_ui = datetime.strptime(date_from, "%Y-%m-%d").strftime("%m/%d/%Y") if date_from else fecha["ui"]
    dt_ui = datetime.strptime(date_to,   "%Y-%m-%d").strftime("%m/%d/%Y") if date_to   else fecha["ui"]

    print("=" * 60)
    print("BLITZPAY — Payment Report (Excel)")
    print(f"Fechas:  {df_ui} → {dt_ui}")
    print("Filtros: Status=Paid | Origin=Merchant Portal")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
        )
        page = await context.new_page()

        login_ok = await _login(page)
        if not login_ok:
            await browser.close()
            return None

        print("\n[2] Navegando a Payment Report...")
        await page.goto(PAYMENT_REPORT_URL)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(8000)
        await _screenshot(page, "pay_01_inicial.png")

        print(f"\n[3] Aplicando fechas: {df_ui} - {dt_ui}...")
        await _set_fecha_payment(page, df_ui, dt_ui)

        print("\n[4] Statuses → solo Paid...")
        await _configurar_dropdown(page, "Statuses", ["paid"])

        print("\n[5] Payment Origin → solo Merchant Portal...")
        await _configurar_dropdown(page, "Payment Origin", ["merchant portal"])

        print("\n[6] All users → solo Shay Carter...")
        await _seleccionar_usuario(page, COLLECTOR_NAME)

        print("\n[7] Ejecutando búsqueda...")
        search_btn = await page.query_selector('button:has-text("Search")')
        if search_btn:
            await search_btn.click()
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(5000)

        await _screenshot(page, "pay_02_resultados.png")

        print("\n[8] Descargando Excel...")
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_base = SCREENSHOT_DIR / f"payment_report_{ts}"

        export_loc = page.locator(
            'button:has-text("Export as excel"), '
            'a:has-text("Export as excel"), '
            'button:has-text("Export"), '
            'a:has-text("Export")'
        ).first

        ruta_final = None
        try:
            await export_loc.wait_for(state="visible", timeout=8000)
            async with page.expect_download(timeout=30000) as dl_info:
                await export_loc.click()
            dl = await dl_info.value
            ext = Path(dl.suggested_filename).suffix or ".xlsx"
            ruta_final = str(ruta_base) + ext
            await dl.save_as(ruta_final)
            print(f"  Descargado: {ruta_final}")
        except Exception as e:
            print(f"  [ERROR] Descarga falló: {e}")
            await _screenshot(page, "pay_03_error.png")

        datos_stats = None
        if ruta_final:
            print("\n[9] Scrapeando Collection Stats (misma sesión)...")
            stats_url = _build_stats_url(date_from, date_to)
            await _navegar_collection_stats(page, stats_url)
            fecha_ui = datetime.strptime(date_from, "%Y-%m-%d").strftime("%m/%d/%Y") if date_from else _fecha_ayer()["ui"]
            await _aplicar_fecha(page, fecha_ui)
            await _filtrar_collector(page, COLLECTOR_NAME)
            datos_stats = await _extraer_datos(page, COLLECTOR_NAME)

        await browser.close()

    if ruta_final and datos_stats:
        _agregar_hoja_stats(
            ruta_final,
            datos_stats,
            date_from or _fecha_ayer()["label"],
            date_to   or _fecha_ayer()["label"],
        )

    return ruta_final


async def explorar_payment_report(date_from=None, headless=False):
    """Modo diagnóstico: vuelca controles interactivos del Payment Report en consola."""
    fecha = _fecha_ayer()
    print("=" * 60)
    print("EXPLORACIÓN — Payment Report")
    print(f"Fecha: {date_from or fecha['label']}")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
        )
        page = await context.new_page()

        login_ok = await _login(page)
        if not login_ok:
            await browser.close()
            return

        print(f"\n[2] Navegando a {PAYMENT_REPORT_URL}...")
        await page.goto(PAYMENT_REPORT_URL)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(8000)
        await _screenshot(page, "pay_01_inicial.png")
        print(f"  URL: {page.url}")
        print(f"  Título: {await page.title()}")

        controles = await page.evaluate("""() => {
            const resultado = [];
            document.querySelectorAll('select').forEach((el, i) => {
                resultado.push({ tipo: 'select', indice: i, id: el.id || '',
                    name: el.name || '', clase: el.className.slice(0, 60),
                    multiple: el.multiple,
                    opciones: Array.from(el.options).map(o => ({
                        value: o.value, text: o.text.trim(), selected: o.selected
                    }))
                });
            });
            document.querySelectorAll('input:not([type="hidden"])').forEach((el, i) => {
                resultado.push({ tipo: 'input', indice: i, inputType: el.type,
                    id: el.id || '', name: el.name || '',
                    placeholder: el.placeholder || '', value: el.value || '',
                    clase: el.className.slice(0, 60), checked: el.checked
                });
            });
            document.querySelectorAll('[role="checkbox"], [role="option"], [role="listbox"]').forEach((el, i) => {
                resultado.push({ tipo: 'aria-' + el.getAttribute('role'), indice: i,
                    texto: el.innerText.trim().slice(0, 80),
                    checked: el.getAttribute('aria-checked'),
                    selected: el.getAttribute('aria-selected'),
                    clase: el.className.slice(0, 60)
                });
            });
            return resultado;
        }""")

        print(f"\n  Controles encontrados: {len(controles)}")
        for c in controles:
            tipo = c.get("tipo", "?")
            if tipo == "select":
                print(f"\n  [SELECT #{c['indice']}] id={c['id']} name={c['name']} multiple={c['multiple']}")
                for op in c.get("opciones", []):
                    marca = "✓" if op["selected"] else " "
                    print(f"    [{marca}] {op['text']} (value={op['value']})")
            elif tipo == "input":
                tp = c.get("inputType", "")
                if tp in ("checkbox", "radio"):
                    print(f"  [INPUT {tp}] id={c['id']} name={c['name']} checked={c['checked']} | {c['placeholder']}")
                elif tp not in ("submit", "button"):
                    print(f"  [INPUT {tp}] id={c['id']} name={c['name']} placeholder={c['placeholder']} value={c['value'][:30]}")
            else:
                print(f"  [{tipo.upper()} #{c['indice']}] checked={c.get('checked')} | {c.get('texto', '')[:60]}")

        texto = await page.evaluate("""() => {
            const el = document.querySelector('main, [class*="content"], body');
            return el ? el.innerText.trim().slice(0, 1500) : '';
        }""")
        print(f"\n  [Texto visible]\n  " + texto[:800].replace("\n", "\n  "))
        await browser.close()

    print(f"\nScreenshots: {SCREENSHOT_DIR}")


if __name__ == "__main__":
    headless = "--headless" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    modo = args[0] if args else "collection"

    if modo == "pay-explore":
        asyncio.run(explorar_payment_report(headless=headless))

    elif modo == "pay-report":
        date_from = args[1] if len(args) > 1 else None
        date_to   = args[2] if len(args) > 2 else args[1] if len(args) > 1 else None
        asyncio.run(scrape_payment_report(date_from=date_from, date_to=date_to, headless=headless))

    else:
        date_from = args[0] if len(args) > 0 else None
        date_to   = args[1] if len(args) > 1 else args[0] if len(args) > 0 else None
        asyncio.run(test_blitzpay(date_from=date_from, date_to=date_to, headless=headless))
