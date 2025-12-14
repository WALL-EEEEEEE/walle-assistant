import json
import os
import threading
import flet as ft
from ai_client import AIClient
from tools import summarize_text

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".ai_assistant_config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except Exception as e:
        print("Warning: failed to save config:", e)


def default_model_for_provider(provider: str):
    if provider == "openai":
        return "gpt-3.5-turbo"
    if provider == "gemini":
        return "text-bison-001"
    return None


def model_options_for_provider(provider: str):
    if provider == "openai":
        return ["gpt-3.5-turbo", "gpt-4", "gpt-4o"]
    if provider == "gemini":
        return ["text-bison-001"]
    return []


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


def main(page: ft.Page):
    page.title = "AI Assistant Tools"
    page.window_width = 900
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.LIGHT

    cfg = load_config()
    provider = cfg.get("provider", "openai")
    client = None

    selected_indices = set()

    messages_list = ft.Column(expand=True)

    status = ft.Text(f"Welcome to AI Assistant Tools. Provider: {provider}. Set API keys in Settings.")

    def ensure_client():
        nonlocal client
        provider = cfg.get("provider", "openai")
        key = cfg.get(f"{provider}_api_key")
        if client:
            # if provider changed we need to re-init
            if getattr(client, "provider", None) == provider:
                return True
            client = None
        if not key:
            dlg = ft.AlertDialog(title=ft.Text("API Key"), content=ft.Text(f"Please set your {provider} API key first."), actions=[ft.TextButton("OK", on_click=lambda e: setattr(page.dialog, "open", False))])
            page.dialog = dlg
            dlg.open = True
            page.update()
            return False
        try:
            client = AIClient(api_key=key, provider=provider, model=cfg.get(f"{provider}_model"))
            # update status text
            status.value = f"Provider: {provider}"
            page.update()
            return True
        except Exception as e:
            dlg = ft.AlertDialog(title=ft.Text("Error"), content=ft.Text(f"Failed to initialize AI client: {e}"), actions=[ft.TextButton("OK", on_click=lambda e: setattr(page.dialog, "open", False))])
            page.dialog = dlg
            dlg.open = True
            page.update()
            return False

    def append_chat(role, text):
        idx = len(messages_list.controls)
        messages_list.controls.append(make_message_container(role, text, idx, toggle_select))
        page.update()

    def toggle_select(idx: int):
        # toggle selection state visually
        if idx in selected_indices:
            selected_indices.remove(idx)
            messages_list.controls[idx].border = ft.border.all(1, "#E0E0E0")
        else:
            selected_indices.add(idx)
            messages_list.controls[idx].border = ft.border.all(2, "#1E88E5")
        page.update()

    input_field = ft.TextField(hint_text="Type a message...", expand=True)

    # model selection dropdown to the left of the input field
    model_dd = ft.Dropdown(
        options=[ft.dropdown.Option(o) for o in model_options_for_provider(provider)],
        value=cfg.get(f"{provider}_model", default_model_for_provider(provider)),
        width=220,
    )

    def model_changed(e=None):
        nonlocal client, cfg, provider
        sel = model_dd.value or default_model_for_provider(provider)
        cfg[f"{provider}_model"] = sel
        save_config(cfg)
        client = None
        page.update()

    model_dd.on_change = model_changed

    def do_send(e=None):
        nonlocal client
        message = input_field.value.strip()
        if not message:
            return
        append_chat("User", message)
        input_field.value = ""
        page.update()

        if not ensure_client():
            return

        def worker():
            try:
                messages = [{"role": "user", "content": message}]
                response = client.chat(messages)
                append_chat("Assistant", response)
            except Exception as e:
                append_chat("Error", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def set_api_key_dialog(e=None):
        nonlocal client, cfg, provider
        # provider selection dropdown
        provider_dd = ft.Dropdown(options=[ft.dropdown.Option("openai"), ft.dropdown.Option("gemini")], value=cfg.get("provider", "openai"), width=200)
        key_field = ft.TextField(hint_text="Enter API key for selected provider", password=True, autofocus=True)

        # model selection for the dialog; will be updated when provider changes
        model_select = ft.Dropdown(
            options=[ft.dropdown.Option(o) for o in model_options_for_provider(provider_dd.value or "openai")],
            value=cfg.get(f"{provider}_model", default_model_for_provider(provider_dd.value or "openai")),
            width=240,
        )

        # prefill from config
        key_field.value = cfg.get(f"{provider}_api_key", "")

        def provider_changed(ev=None):
            sel = provider_dd.value or "openai"
            opts = [ft.dropdown.Option(o) for o in model_options_for_provider(sel)]
            model_select.options = opts
            model_select.value = cfg.get(f"{sel}_model", default_model_for_provider(sel))
            page.update()

        provider_dd.on_change = provider_changed

        def do_set(ev):
            nonlocal client, cfg, provider
            sel = provider_dd.value or "openai"
            if key_field.value:
                cfg[f"{sel}_api_key"] = key_field.value.strip()
            cfg["provider"] = sel
            # save selected model for this provider
            if model_select.value:
                cfg[f"{sel}_model"] = model_select.value
            save_config(cfg)
            provider = sel
            # update top-level model dropdown to reflect new provider & model
            model_dd.options = [ft.dropdown.Option(o) for o in model_options_for_provider(provider)]
            model_dd.value = cfg.get(f"{provider}_model", default_model_for_provider(provider))
            client = None
            status.value = f"Provider: {provider}"
            page.dialog.open = False
            page.update()

        content = ft.Column([
            ft.Row([ft.Text("Provider:"), provider_dd]),
            ft.Row([ft.Text("API Key:"), key_field]),
            ft.Row([ft.Text("Model:"), model_select]),
        ])
        dlg = ft.AlertDialog(title=ft.Text("Settings"), content=content, actions=[ft.TextButton("Save", on_click=do_set), ft.TextButton("Cancel", on_click=lambda e: setattr(page.dialog, "open", False))])
        page.dialog = dlg
        page.dialog.open = True
        page.update()

    def clear_api_key(e=None):
        nonlocal client, cfg, provider
        # Clear API key for the currently selected provider
        cfg.pop(f"{provider}_api_key", None)
        # Optionally unset provider selection
        cfg.pop("provider", None)
        save_config(cfg)
        client = None
        page.snack_bar = ft.SnackBar(ft.Text("API key cleared"))
        page.snack_bar.open = True
        # reset provider variable and status
        provider = cfg.get("provider", "openai")
        status.value = f"Provider: {provider}"
        page.update()

    def summarize_selection(e=None):
        nonlocal client
        # collect selected text
        selected_texts = [messages_list.controls[i].content.controls[1].value for i in sorted(selected_indices)]
        if not selected_texts:
            # prompt to paste or summarize last message
            dlg_field = ft.TextField(hint_text="Paste text to summarize", multiline=True, width=600, height=200)

            def do_summ(ev):
                text = dlg_field.value.strip()
                if not text:
                    page.dialog.open = False
                    page.update()
                    return
                if not ensure_client():
                    page.dialog.open = False
                    page.update()
                    return

                def worker():
                    summary = summarize_text(client, text)
                    append_chat("Assistant (Summary)", summary)

                threading.Thread(target=worker, daemon=True).start()
                page.dialog.open = False
                page.update()

            dlg = ft.AlertDialog(title=ft.Text("Summarize Text"), content=dlg_field, actions=[ft.TextButton("Summarize", on_click=do_summ), ft.TextButton("Cancel")])
            page.dialog = dlg
            dlg.open = True
            page.update()
            return

        # summarize combined selected texts
        text = "\n\n".join(selected_texts)
        if not ensure_client():
            return

        def worker():
            summary = summarize_text(client, text)
            append_chat("Assistant (Summary)", summary)

        threading.Thread(target=worker, daemon=True).start()

    top_bar = ft.Row([ft.ElevatedButton("Set API Key", on_click=set_api_key_dialog), ft.ElevatedButton("Clear API Key", on_click=clear_api_key), ft.ElevatedButton("Summarize Selection", on_click=summarize_selection)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    send_row = ft.Row([model_dd, input_field, ft.ElevatedButton("Send", on_click=do_send)], vertical_alignment=ft.CrossAxisAlignment.CENTER)

    page.add(status, ft.Divider(), top_bar, ft.Container(messages_list, expand=True, padding=10), send_row)
