import flet as ft
from datetime import datetime, date
import requests
import pytz
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

load_dotenv()

API_URL = os.getenv("API_URL")

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.ORANGE)
    page.title = "Recibos"
    page.padding = 10

    # --- Estado / variables de la pantalla principal (RECIBOS) ---
    todos_los_recibos = []
    pagina_actual = 0
    tamanio_pagina = 100

    zona_horaria = pytz.timezone("America/Merida")
    hoy = datetime.now(zona_horaria).date()
    hoy_str = hoy.isoformat()

    # --- Widgets compartidos / Home (RECIBOS) ---
    logo = ft.Image(
        src="https://i.ibb.co/TqxbQnsq/Imagen-de-Whats-App-2025-04-23-a-las-10-14-29-559a5c08.jpg",
        width=60, height=60, fit=ft.ImageFit.CONTAIN
    )

    titulo_empresa = ft.Text("DZEMUL", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    titulo = ft.Text("Consulta de Recibos", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

    txt_fecha_desde = ft.TextField(label="Desde", read_only=True, width=150,
                                   value=hoy.strftime("%d-%m-%Y"), bgcolor=ft.Colors.WHITE)
    txt_fecha_desde.data = hoy_str

    txt_fecha_hasta = ft.TextField(label="Hasta", read_only=True, width=150,
                                   value=hoy.strftime("%d-%m-%Y"), bgcolor=ft.Colors.WHITE)
    txt_fecha_hasta.data = hoy_str

    def actualizar_fecha(txt, nueva_fecha):
        txt.data = nueva_fecha
        txt.value = datetime.fromisoformat(nueva_fecha).strftime("%d-%m-%Y")
        page.update()

    date_picker_desde = ft.DatePicker(on_change=lambda e: actualizar_fecha(txt_fecha_desde, e.data), value=date.today())
    date_picker_hasta = ft.DatePicker(on_change=lambda e: actualizar_fecha(txt_fecha_hasta, e.data), value=date.today())
    page.overlay.extend([date_picker_desde, date_picker_hasta])

    fecha_desde_btn = ft.ElevatedButton("Fecha desde", icon=ft.Icons.CALENDAR_MONTH,
                                        on_click=lambda e: page.open(date_picker_desde))
    fecha_hasta_btn = ft.ElevatedButton("Fecha hasta", icon=ft.Icons.CALENDAR_MONTH,
                                        on_click=lambda e: page.open(date_picker_hasta))

    contribuyente_input = ft.TextField(
        label="Filtrar por contribuyente (opcional)",
        width=400,
        text_size=14,
        border_color=ft.Colors.GREY,
        color=ft.Colors.BLACK,
        cursor_color=ft.Colors.BLACK
    )

    buscar_btn = ft.ElevatedButton(
        "Buscar", width=300, height=40, icon=ft.Icons.SEARCH,
        bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, icon_color=ft.Colors.WHITE
    )
    desplegar_btn = ft.ElevatedButton(
        "Resumen", width=150, height=40, icon=ft.Icons.INFO,
        bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, icon_color=ft.Colors.WHITE
    )

    cedulas_btn = ft.ElevatedButton(
        "ir a Cédulas", width=300, height=40, icon=ft.Icons.DOCK_SHARP,
        bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, icon_color=ft.Colors.WHITE
    )

    descargarpdf_btn = ft.ElevatedButton(
        "Descargar PDF", width=150, height=40, icon=ft.Icons.DOWNLOAD,
        bgcolor=ft.Colors.WHITE, color=ft.Colors.RED, icon_color=ft.Colors.RED
    )

    # Diálogo de resumen:
    desplegar_dialog = ft.AlertDialog(title=ft.Text("Despliegue de Totales"))

    # Contenedores que se renderizan dentro del View("/") (Home)
    resultado_card = ft.Container(content=ft.Column([], scroll=ft.ScrollMode.AUTO, height=200), padding=10)
    totales_card = ft.Container()
    loader = ft.ProgressRing(visible=False, color=ft.Colors.ORANGE, stroke_width=4)

    # Encabezado (Home)
    encabezado = ft.Container(
        content=ft.Column([
            ft.Row([logo, titulo_empresa]),
            titulo,
            ft.Row([fecha_desde_btn, fecha_hasta_btn]),
            ft.Row([txt_fecha_desde, txt_fecha_hasta]),
            ft.Row([buscar_btn, desplegar_btn], alignment=ft.MainAxisAlignment.START),
            cedulas_btn,
            contribuyente_input
        ]),
        padding=20,
        bgcolor=ft.Colors.ORANGE,
        border_radius=ft.BorderRadius(0, 0, 20, 20)
    )

    def fmt_api(iso_date_str: str) -> str:
        # "YYYY-MM-DD" -> "YYMMDD"
        d = datetime.fromisoformat(iso_date_str).date()
        return d.strftime("%y%m%d")
    def show_snack(msg: str, icon=ft.Icons.INFO, bg=ft.Colors.BLUE_GREY_100):
        snack_bar = ft.SnackBar(
            content=ft.Row([ft.Icon(icon), ft.Text(msg)], tight=True, spacing=8),
            bgcolor=bg,
            show_close_icon=True
        )
        page.open(snack_bar)
        page.update()

    # --- Lógica de HOME (RECIBOS) ---
    def formatear_fecha_yymmdd(f):
        try:
            return datetime.strptime(f, "%y%m%d").strftime("%d-%m-%Y")
        except Exception:
            return f

    def descargar_pdf_recibos(e):
        desde = fmt_api(txt_fecha_desde.data)
        hasta = fmt_api(txt_fecha_hasta.data)
        nombre = (contribuyente_input.value or "").strip()
        if nombre:
            url = f"{API_URL}recibos/reporte?desde={desde}&hasta={hasta}&contribuyente={quote_plus(nombre)}"
        else:
            url = f"{API_URL}recibos/reporte?desde={desde}&hasta={hasta}"
        page.launch_url(url)

    descargarpdf_btn.on_click = descargar_pdf_recibos

    def cambiar_pagina(delta):
        nonlocal pagina_actual
        pagina_actual += delta
        mostrar_pagina()

    def mostrar_resultados(data):
        nonlocal todos_los_recibos, pagina_actual
        todos_los_recibos = data
        pagina_actual = 0
        mostrar_pagina()

    def mostrar_pagina():
        nonlocal pagina_actual, tamanio_pagina, todos_los_recibos

        inicio = pagina_actual * tamanio_pagina
        fin = inicio + tamanio_pagina
        fragmento = todos_los_recibos[inicio:fin]

        recibos_widgets = []
        for r in fragmento:
            es_cancelado = r.get("status", r.get("id_status", "0")) == "1"
            color_texto = ft.Colors.GREY if es_cancelado else ft.Colors.BLACK
            estado = "❌ CANCELADO" if es_cancelado else ""

            tarjeta = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Recibo: {r['recibo']} {estado}", weight=ft.FontWeight.BOLD, size=18, color=color_texto),
                        ft.Text(f"Contribuyente: {r['contribuyente']}", color=color_texto),
                        ft.Text(f"Concepto: {r['concepto']}", color=color_texto),
                        ft.Text(f"Fecha: {formatear_fecha_yymmdd(r['fecha'])}", color=color_texto),
                        ft.Text(f"Neto: ${float(r['neto']):,.2f}", weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_800 if not es_cancelado else ft.Colors.GREY),
                        ft.Text(f"Descuento: ${float(r['descuento']):,.2f}", color=color_texto)
                    ]),
                    padding=15,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.GREY_400, offset=ft.Offset(2, 2))
                ),
                elevation=2
            )
            recibos_widgets.append(tarjeta)

        botones_navegacion = []
        if pagina_actual > 0:
            botones_navegacion.append(ft.ElevatedButton("⬅️ Anteriores 100", on_click=lambda e: cambiar_pagina(-1)))
        if fin < len(todos_los_recibos):
            botones_navegacion.append(ft.ElevatedButton("Siguientes 100 ➡️", on_click=lambda e: cambiar_pagina(1)))

        resultado_card.content = ft.Column(
            recibos_widgets + [ft.Row(botones_navegacion, alignment=ft.MainAxisAlignment.CENTER)],
            spacing=10, scroll=ft.ScrollMode.ALWAYS, height=200
        )
        page.update()

    def buscar_producto(nombre_raw):
        buscar_btn.disabled = True
        loader.visible = True
        fecha_desde_btn.disabled = True
        fecha_hasta_btn.disabled = True
        desplegar_btn.visible = False
        buscar_btn.width = 300
        page.update()

        desde_date = datetime.fromisoformat(txt_fecha_desde.data).date()
        hasta_date = datetime.fromisoformat(txt_fecha_hasta.data).date()

        desde = desde_date.strftime("%y%m%d")
        hasta = hasta_date.strftime("%y%m%d")
        params = {"desde": desde, "hasta": hasta}

        nombre = nombre_raw.strip()
        if nombre:
            params["contribuyente"] = nombre

        data = []
        try:
            url = f"{API_URL}recibos/filtrar" if "contribuyente" in params else f"{API_URL}recibos"
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                mostrar_resultados(data)
                if not data:
                    rango = f"{txt_fecha_desde.value} a {txt_fecha_hasta.value}"
                    criterio = f" para '{nombre}'" if nombre else ""
                    show_snack(f"No se encontraron recibos de {rango}{criterio}.", icon=ft.Icons.SEARCH_OFF,
                               bg=ft.Colors.RED)
                    resultado_card.content = ft.Column(
                        [ft.Container(
                            content=ft.Row([ft.Icon(ft.Icons.SEARCH_OFF), ft.Text("Sin recibos en este rango.")]),
                            padding=10,
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=10,
                        )],
                        spacing=10, scroll=ft.ScrollMode.ALWAYS, height=200
                    )
                    page.update()
            else:
                print("Error:", response.status_code, response.json().get("detail"))
        except Exception as e:
            print("Error al buscar recibos:", str(e))

        try:
            response_totales = requests.get(f"{API_URL}recibos/totales", params=params)
            if response_totales.status_code == 200:
                d = response_totales.json()
                totales_card.content = ft.Column([
                    ft.Row([ft.Text(f"Total Neto: ${float(d.get('total_neto', 0)):,.2f}", size=22, weight=ft.FontWeight.BOLD), descargarpdf_btn]),
                    ft.Text(f"Total Descuento: ${float(d.get('total_descuento', 0)):,.2f}", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Recibos encontrados: {len(data)}", size=14, color=ft.Colors.BLACK),
                    ft.Text(f"Recibos cancelados: {d.get('cantidad_status_1', 0)}", size=14, color=ft.Colors.RED_700)
                ])
        except Exception as e:
            print("Error al obtener totales:", str(e))

        loader.visible = False
        buscar_btn.disabled = False
        fecha_hasta_btn.disabled = False
        fecha_desde_btn.disabled = False
        buscar_btn.width = 150
        desplegar_btn.visible = True
        page.update()

    def mostrar_despliegue_totales():
        desde_date = datetime.fromisoformat(txt_fecha_desde.data).date()
        hasta_date = datetime.fromisoformat(txt_fecha_hasta.data).date()
        desde = desde_date.strftime("%y%m%d")
        hasta = hasta_date.strftime("%y%m%d")
        params = {"desde": desde, "hasta": hasta}
        try:
            response = requests.get(f"{API_URL}recibos/totales/despliegue", params=params)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    desplegar_dialog.content = ft.Text("No se encontraron totales en este rango de fechas.")
                    page.open(desplegar_dialog)
                    return

                items = []
                for cuenta_data in data:
                    cuenta = cuenta_data.get("cuenta", "Sin cuenta")
                    total_neto = cuenta_data.get("total_neto", 0.0)
                    total_descuento = cuenta_data.get("total_descuento", 0.0)

                    items.append(ft.Text(f"Cuenta: {cuenta}", size=18, weight=ft.FontWeight.BOLD))
                    items.append(ft.Text(f"  Total Neto: ${total_neto:,.2f}", size=16))
                    items.append(ft.Text(f"  Total Descuento: ${total_descuento:,.2f}", size=16))
                    items.append(ft.Divider())

                desplegar_dialog.content = ft.Column(items, height=400, scroll=ft.ScrollMode.ALWAYS)
                page.open(desplegar_dialog)
            else:
                desplegar_dialog.content = ft.Text(f"Error al obtener datos: {response.status_code}")
                page.open(desplegar_dialog)
        except Exception as e:
            print("Error al obtener totales:", str(e))
            desplegar_dialog.content = ft.Text("Hubo un error al intentar obtener los datos.")
            page.open(desplegar_dialog)

    # Acciones de botones (RECIBOS)
    buscar_btn.on_click = lambda e: buscar_producto(contribuyente_input.value)
    desplegar_btn.on_click = lambda e: mostrar_despliegue_totales()
    cedulas_btn.on_click = lambda e: page.go("/cedulas")  # <--- NAVEGAR

    # ----------- ROUTING -----------

    def build_home_view() -> ft.View:
        # Tu pantalla principal dentro de un View("/")
        return ft.View(
            route="/",
            controls=[
                ft.Column(
                    [encabezado, loader, totales_card, resultado_card],
                    spacing=20
                )
            ],
            padding=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def build_cedulas_view() -> ft.View:

        # --- Estado local de CÉDULAS ---
        c_todos = []
        c_pagina = 0
        c_page_size = 100

        # --- Widgets GUI (idénticos, cambiando el título) ---
        c_logo = ft.Image(
            src="https://i.ibb.co/TqxbQnsq/Imagen-de-Whats-App-2025-04-23-a-las-10-14-29-559a5c08.jpg",
            width=60, height=60, fit=ft.ImageFit.CONTAIN
        )
        c_titulo_empresa = ft.Text("DZEMUL", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        c_titulo = ft.Text("Consulta de Cédulas", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

        c_txt_desde = ft.TextField(label="Desde", read_only=True, width=150,
                                   value=hoy.strftime("%d-%m-%Y"), bgcolor=ft.Colors.WHITE)
        c_txt_desde.data = hoy_str
        c_txt_hasta = ft.TextField(label="Hasta", read_only=True, width=150,
                                   value=hoy.strftime("%d-%m-%Y"), bgcolor=ft.Colors.WHITE)
        c_txt_hasta.data = hoy_str

        def c_actualizar_fecha(txt, nueva_fecha):
            txt.data = nueva_fecha
            txt.value = datetime.fromisoformat(nueva_fecha).strftime("%d-%m-%Y")
            page.update()

        c_dp_desde = ft.DatePicker(on_change=lambda e: c_actualizar_fecha(c_txt_desde, e.data), value=date.today())
        c_dp_hasta = ft.DatePicker(on_change=lambda e: c_actualizar_fecha(c_txt_hasta, e.data), value=date.today())
        if c_dp_desde not in page.overlay:
            page.overlay.append(c_dp_desde)
        if c_dp_hasta not in page.overlay:
            page.overlay.append(c_dp_hasta)

        c_btn_desde = ft.ElevatedButton("Fecha desde", icon=ft.Icons.CALENDAR_MONTH,
                                        on_click=lambda e: page.open(c_dp_desde))
        c_btn_hasta = ft.ElevatedButton("Fecha hasta", icon=ft.Icons.CALENDAR_MONTH,
                                        on_click=lambda e: page.open(c_dp_hasta))

        c_contrib = ft.TextField(
            label="Filtrar por contribuyente (opcional)",
            width=400,
            text_size=14,
            border_color=ft.Colors.GREY,
            color=ft.Colors.BLACK,
            cursor_color=ft.Colors.BLACK
        )

        c_btn_buscar = ft.ElevatedButton(
            "Buscar", width=300, height=40, icon=ft.Icons.SEARCH,
            bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, icon_color=ft.Colors.WHITE
        )
        c_btn_resumen = ft.ElevatedButton(
            "Resumen", width=150, height=40, icon=ft.Icons.INFO,
            bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, icon_color=ft.Colors.WHITE,
            visible=False
        )

        c_btn_recibos = ft.ElevatedButton(
            "Ir a Recibos", width=300, height=40, icon=ft.Icons.DESCRIPTION,
            bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, icon_color=ft.Colors.WHITE,
            on_click=lambda e: page.go("/")
        )

        c_descargarpdf_btn = ft.ElevatedButton(
            "Descargar PDF", width=150, height=40, icon=ft.Icons.DOWNLOAD,
            bgcolor=ft.Colors.WHITE, color=ft.Colors.RED, icon_color=ft.Colors.RED
        )

        c_dialog = ft.AlertDialog(title=ft.Text("Despliegue de Totales - Cédulas"))

        c_resultado_card = ft.Container(content=ft.Column([], scroll=ft.ScrollMode.AUTO, height=200), padding=10)
        c_totales_card = ft.Container()
        c_loader = ft.ProgressRing(visible=False, color=ft.Colors.ORANGE, stroke_width=4)

        c_encabezado = ft.Container(
            content=ft.Column([
                ft.Row([c_logo, c_titulo_empresa]),
                c_titulo,
                ft.Row([c_btn_desde, c_btn_hasta]),
                ft.Row([c_txt_desde, c_txt_hasta]),
                ft.Row([c_btn_buscar, c_btn_resumen], alignment=ft.MainAxisAlignment.START),
                c_btn_recibos,
                c_contrib
            ]),
            padding=20,
            bgcolor=ft.Colors.BLUE,
            border_radius=ft.BorderRadius(0, 0, 20, 20)
        )

        # --- Utilidades / Lógica (CÉDULAS) ---
        def c_formatear_fecha_yymmdd(f):
            try:
                return datetime.strptime(f, "%y%m%d").strftime("%d-%m-%Y")
            except Exception:
                return f

        def c_descargar_pdf(e):
            desde = c_fmt_api(c_txt_desde.data)
            hasta = c_fmt_api(c_txt_hasta.data)
            nombre = (c_contrib.value or "").strip()
            if nombre:
                url = f"{API_URL}cedulas/reporte?desde={desde}&hasta={hasta}&contribuyente={quote_plus(nombre)}"
            else:
                url = f"{API_URL}cedulas/reporte?desde={desde}&hasta={hasta}"
            page.launch_url(url)

        c_descargarpdf_btn.on_click = c_descargar_pdf

        def c_fmt_api(iso_date_str: str) -> str:
            d = datetime.fromisoformat(iso_date_str).date()
            return d.strftime("%y%m%d")

        def c_mostrar_pagina():
            nonlocal c_pagina, c_page_size, c_todos
            inicio = c_pagina * c_page_size
            fin = inicio + c_page_size
            fragmento = c_todos[inicio:fin]

            widgets = []
            for r in fragmento:
                folio = r.get("folio", "")
                motivo = r.get("motivo", "")
                fecham = r.get("fecham", "")
                contrib = r.get("contribuyente", "")
                direccion = r.get("direccion") or ""  # puede venir None
                precio_unitario = float(r.get("precio_unitario") or 0)
                cantidad = float(r.get("cantidad") or 0)
                importe = precio_unitario * cantidad
                recibo_teso = r.get("recibo_teso") or None
                fecha_rteso = r.get("fecha_rteso") or None
                folio_elec = r.get("folio_electronico") or "Sin folio"



                tarjeta = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"Cédula: {folio}", weight=ft.FontWeight.BOLD, size=18),
                            ft.Text(f"Motivo: {motivo}"),
                            ft.Text(f"Folio electronico: {folio_elec}"),
                            ft.Text(f"Contribuyente: {contrib}"),
                            ft.Text(f"Dirección: {direccion}", selectable=True),
                            ft.Text(f"Fecha: {c_formatear_fecha_yymmdd(fecham)}"),
                            ft.Text(f"Importe: ${importe}"),
                            ft.Text(f"Recibo: {recibo_teso if recibo_teso != None else "Sin recibo"}"),
                            ft.Text(f"Fecha recibo: {c_formatear_fecha_yymmdd(fecha_rteso) if recibo_teso != None else "Sin recibo"}")
                        ]),
                        padding=15,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.GREY_400, offset=ft.Offset(2, 2))
                    ),
                    elevation=2
                )
                widgets.append(tarjeta)

            nav = []
            if c_pagina > 0:
                nav.append(ft.ElevatedButton("⬅️ Anteriores 100", on_click=lambda e: c_cambiar_pagina(-1)))
            if fin < len(c_todos):
                nav.append(ft.ElevatedButton("Siguientes 100 ➡️", on_click=lambda e: c_cambiar_pagina(1)))

            c_resultado_card.content = ft.Column(
                widgets + [ft.Row(nav, alignment=ft.MainAxisAlignment.CENTER)],
                spacing=10, scroll=ft.ScrollMode.ALWAYS, height=200
            )
            page.update()

        def c_cambiar_pagina(delta: int):
            nonlocal c_pagina
            c_pagina += delta
            c_mostrar_pagina()

        def c_mostrar_resultados(data):
            nonlocal c_todos, c_pagina
            c_todos = data or []
            c_pagina = 0
            c_mostrar_pagina()

        def c_buscar(nombre_raw: str):
            # Activa loader / desactiva botones
            c_btn_buscar.disabled = True
            c_loader.visible = True
            c_btn_desde.disabled = True
            c_btn_hasta.disabled = True
            c_btn_resumen.visible = False
            c_btn_buscar.width = 300
            page.update()

            # Params con formato aammdd
            desde = c_fmt_api(c_txt_desde.data)  # YYMMDD
            hasta = c_fmt_api(c_txt_hasta.data)  # YYMMDD
            params = {"desde": desde, "hasta": hasta}

            # Filtro por contribuyente: si hay texto, usamos /cedulas/filtrar
            nombre = (nombre_raw or "").strip()
            use_filter = len(nombre) > 0
            if use_filter:
                params["contribuyente"] = nombre

            data = []
            try:
                url = f"{API_URL}cedulas/filtrar" if use_filter else f"{API_URL}cedulas"
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    c_mostrar_resultados(data)
                    # Aviso si no hay resultados
                if not data:
                    rango = f"{c_txt_desde.value} a {c_txt_hasta.value}"
                    criterio = f" para '{nombre}'" if use_filter else ""
                    show_snack(f"No se encontraron cédulas de {rango}{criterio}.", icon=ft.Icons.SEARCH_OFF, bg=ft.Colors.RED)
                    c_resultado_card.content = ft.Column(
                        [ft.Container(
                            content=ft.Row([ft.Icon(ft.Icons.SEARCH_OFF), ft.Text("Sin cédulas en este rango.")]),
                            padding=10,
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=10,
                        )],
                        spacing=10, scroll=ft.ScrollMode.ALWAYS, height=200
                    )
                else:
                    print("Error:", response.status_code, getattr(response, "text", ""))
                    page.snack_bar = ft.SnackBar(ft.Text(f"Error {response.status_code} al consultar cédulas."))
                    page.snack_bar.open = True
            except Exception as e:
                print("Error al buscar cédulas:", str(e))
                page.snack_bar = ft.SnackBar(ft.Text("No se pudo consultar cédulas (revisa conexión/servidor)."))
                page.snack_bar.open = True
                show_snack("No se pudo consultar cédulas (revisa conexión/servidor).")

            # Totales: placeholder (si luego expones /cedulas/totales lo integramos)
            c_totales_card.content = ft.Column([
                ft.Row([ft.Text(f"Cédulas encontradas: {len(data)}", size=14, color=ft.Colors.BLACK), c_descargarpdf_btn])
            ])

            # Restaurar UI
            c_loader.visible = False
            c_btn_buscar.disabled = False
            c_btn_hasta.disabled = False
            c_btn_desde.disabled = False
            c_btn_buscar.width = 300
            c_btn_resumen.visible = False
            page.update()

        def c_mostrar_despliegue_totales():
            # ESQUELETO: agrega tu llamada cuando exista /cedulas/totales (o similar)
            c_dialog.content = ft.Text("Despliegue de totales de cédulas (pendiente de API).")
            page.open(c_dialog)

        # Bind acciones
        c_btn_buscar.on_click = lambda e: c_buscar(c_contrib.value)
        c_btn_resumen.on_click = lambda e: c_mostrar_despliegue_totales()

        # Armar vista
        view = ft.View(
            route="/cedulas",
            controls=[
                ft.Column([c_encabezado, c_loader, c_totales_card, c_resultado_card], spacing=20)
            ],
            padding=10,
            scroll=ft.ScrollMode.AUTO,
        )

        # Carga inicial vacía
        c_mostrar_resultados([])
        return view
    def route_change(e: ft.RouteChangeEvent | None):
        # Redibuja las views según la ruta actual
        page.views.clear()
        page.views.append(build_home_view())
        if page.route == "/cedulas":
            page.views.append(build_cedulas_view())
        page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    buscar_producto("")       # para que al abrir ya cargue algo en /
    page.go(page.route)       # dispara route_change con la ruta actual ("/" por defecto)

ft.app(target=main)
