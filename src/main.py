import flet as ft
import datetime
import requests

API_URL = "api-telchac-production.up.railway.app/"

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.RED)
    page.title = "Recibos"
    page.padding = 10

    hoy = datetime.date.today()
    hoy_str = hoy.isoformat()


    logo = ft.Image(
        src="https://i.ibb.co/PvvPNzhk/Imagen-de-Whats-App-2025-04-22-a-las-15-46-24-f6a2c21e.jpg", 
        width=60,
        height=60,
        fit=ft.ImageFit.CONTAIN
    )

    titulo_empresa = ft.Text(
        "TELCHAC PUERTO",
        size=26,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.WHITE
    )

    titulo = ft.Text(
        "Buscar Recibos por Contribuyente",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.WHITE
    )

    contribuyente_input = ft.TextField(
        label="Contribuyente", 
        width=1000, 
        color=ft.colors.WHITE, 
        border_color=ft.colors.WHITE, 
        cursor_color=ft.colors.WHITE
    )

    txt_fecha_desde = ft.TextField(label="Desde", read_only=True, width=150, value=hoy_str)
    txt_fecha_hasta = ft.TextField(label="Hasta", read_only=True, width=150, value=hoy_str)

    def actualizar_fecha(text_field, nueva_fecha):
        fecha_obj = datetime.datetime.fromisoformat(nueva_fecha)
        fecha_formateada = fecha_obj.date().isoformat()
        text_field.value = fecha_formateada
        page.update()

    date_picker_desde = ft.DatePicker(
        on_change=lambda e: actualizar_fecha(txt_fecha_desde, e.data),
    )
    date_picker_hasta = ft.DatePicker(
        on_change=lambda e: actualizar_fecha(txt_fecha_hasta, e.data),
    )
    page.overlay.extend([date_picker_desde, date_picker_hasta])

    fecha_desde_btn = ft.ElevatedButton(
        "Fecha desde",
        icon=ft.Icons.CALENDAR_MONTH,
        on_click=lambda e: page.open(date_picker_desde)
    )

    fecha_hasta_btn = ft.ElevatedButton(
        "Fecha hasta",
        icon=ft.Icons.CALENDAR_MONTH,
        on_click=lambda e: page.open(date_picker_hasta)
    )

    loader = ft.ProgressRing(visible=False)

    encabezado = ft.Container(
        content=ft.Column([
            ft.Row([logo, titulo_empresa]),
            contribuyente_input,
            ft.Row([fecha_desde_btn, fecha_hasta_btn]),
            ft.Row([txt_fecha_desde, txt_fecha_hasta])
        ]),
        padding=20,
        bgcolor=ft.colors.RED,
        border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=20, bottom_right=20),
    )

    resultado_card = ft.Container(
        content=ft.Column([], scroll=ft.ScrollMode.AUTO, height=400),
        padding=10
    )

    totales_card = ft.Container(
        content=ft.Text("Totales: ", size=18, weight=ft.FontWeight.BOLD),
        padding=10
    )


    

    def mostrar_resultados(data):
        recibos_widgets = []

        for recibo in data:
            tarjeta = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Recibo: {recibo['recibo']}", weight=ft.FontWeight.BOLD, size=18),
                        ft.Text(f"Contribuyente: {recibo['contribuyente']}"),
                        ft.Text(f"Concepto: {recibo['concepto']}"),
                        ft.Text(f"Fecha: {recibo['fecha']}"),
                        ft.Text(f"Neto: ${recibo['neto']}", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_800),
                        ft.Text(f"Descuento: ${recibo['descuento']}")
                    ]),
                    padding=15,
                    bgcolor=ft.colors.WHITE,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        blur_radius=8,
                        color=ft.colors.GREY_400,
                        offset=ft.Offset(2, 2)
                    )
                ),
                elevation=2
            )
            recibos_widgets.append(tarjeta)
        resultado_card.content = ft.Column(recibos_widgets, spacing=10, scroll=ft.ScrollMode.AUTO)
        page.update()

    def buscar_producto(nombre):
        # Mostrar el loader
        loader.visible = True
        page.update()

        desde = txt_fecha_desde.value
        hasta = txt_fecha_hasta.value
        desde_formateada = desde.replace("-", "")[2:]
        hasta_formateada = hasta.replace("-", "")[2:]

        print(f"Contribuyente: {nombre}, Desde: {desde_formateada}, Hasta: {hasta_formateada}")

        try:
            if nombre: 
                url = f"https://{API_URL}recibos/filtrar"
                params = {
                    "desde": desde_formateada,
                    "hasta": hasta_formateada,
                    "contribuyente": nombre
                }
            else: 
                url = f"https://{API_URL}recibos"
                params = {
                    "desde": desde_formateada,
                    "hasta": hasta_formateada
                }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                print("Recibos encontrados:", data)
                mostrar_resultados(data)
            else:
                print("Error:", response.status_code, response.json().get("detail"))

        except Exception as e:
            print("Ocurrió un error al hacer la petición:", str(e))
        
        try:
            if nombre:
                url_totales = f"https://{API_URL}recibos/totales"
                params_totales = {
                    "desde": desde_formateada,
                    "hasta": hasta_formateada,
                    "contribuyente": nombre
                }
            else:
                url_totales = f"https://{API_URL}recibos/totales"
                params_totales = {
                    "desde": desde_formateada,
                    "hasta": hasta_formateada
                }

            response_totales = requests.get(url_totales, params=params_totales)

            if response_totales.status_code == 200:
                totales_data = response_totales.json()
                total_neto = totales_data.get("total_neto", 0)
                total_descuento = totales_data.get("total_descuento", 0)

                totales_card.content = ft.Column([
                    ft.Text(f"Total Neto: ${format(total_neto, ',.2f')}", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                    ft.Text(f"Total Descuento: ${format(total_descuento, ',.2f')}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_800)
                ])
            else:
                print("Error en totales:", response_totales.status_code, response_totales.json().get("detail"))

        except Exception as e:
            print("Ocurrió un error al obtener los totales:", str(e))
        
        # Ocultar el loader
        loader.visible = False
        page.update()


    botones = ft.Row([
        ft.ElevatedButton("Buscar", on_click=lambda e: buscar_producto(contribuyente_input.value.strip()), width=300, height=40, icon=ft.icons.SEARCH, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE, icon_color=ft.colors.WHITE),
    ], alignment=ft.MainAxisAlignment.CENTER)

    page.add(
        ft.Column([
            encabezado,
            botones,
            ft.Row([
                loader,
            ],alignment=ft.MainAxisAlignment.CENTER),
            totales_card,
            ft.Column([resultado_card], scroll=ft.ScrollMode.AUTO, height=400)
        ], spacing=20)
    )
    buscar_producto(None)

ft.app(target=main)
