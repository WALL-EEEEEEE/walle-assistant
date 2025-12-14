import flet as ft
from ..config import default_model_for_provider, model_options_for_provider


def make_input_row(cfg, provider, on_send, on_model_change):
    model_dd = ft.Dropdown(
        options=[ft.dropdown.Option(o) for o in model_options_for_provider(provider)],
        value=cfg.get(f"{provider}_model", default_model_for_provider(provider)),
        width=220,
    )

    input_field = ft.TextField(hint_text="Type a message...", expand=True)
    send_button = ft.ElevatedButton("Send")

    def _on_send(e=None):
        on_send(e)

    def _on_model_change(e=None):
        on_model_change(e)

    send_button.on_click = _on_send
    model_dd.on_change = _on_model_change

    send_row = ft.Row([model_dd, input_field, send_button], vertical_alignment=ft.CrossAxisAlignment.CENTER)

    return send_row, input_field, model_dd
