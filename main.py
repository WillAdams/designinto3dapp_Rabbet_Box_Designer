import flet as ft

from views.designer import DesignerWorkspace


async def main(page: ft.Page):
    page.title = "Rabbet Box Designer"
    page.bgcolor = ft.Colors.WHITE
    page.add(DesignerWorkspace(page))


ft.run(main)
