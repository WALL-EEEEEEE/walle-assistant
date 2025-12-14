import flet as ft


def make_message_container(role: str, text: str, idx: int, select_handler):
    bg = "#E8F0FE" if role == "User" else "#F6F6F6"
    return ft.Container(
        content=ft.Column([
            ft.Text(f"{role}", weight=ft.FontWeight.BOLD, size=12),
            ft.Text(text, selectable=True)
        ]),
        padding=10,
        margin=ft.margin.only(bottom=8),
        bgcolor=bg,
        border=ft.border.all(1, "#E0E0E0"),
        border_radius=8,
        on_click=lambda e: select_handler(idx),
    )
