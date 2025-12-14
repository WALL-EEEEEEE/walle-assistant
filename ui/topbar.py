import flet as ft


def make_top_bar(set_api_key_cb, clear_api_key_cb, summarize_cb, switch_cb=None):
    items = [
        ft.ElevatedButton("Set API Key", on_click=set_api_key_cb),
        ft.ElevatedButton("Clear API Key", on_click=clear_api_key_cb),
        ft.ElevatedButton("Summarize Selection", on_click=summarize_cb),
    ]
    if switch_cb is not None:
        # put the view switch button on the left
        items.insert(0, ft.ElevatedButton("Switch View", on_click=switch_cb))

    return ft.Row(items, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
