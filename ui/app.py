import threading
import flet as ft
from ai_client import AIClient
from tools import summarize_text
from .config import load_config, save_config, default_model_for_provider, model_options_for_provider
from .topbar import make_top_bar
from .chat.view import ChatView



def main(page: ft.Page):
    page.title = "AI Assistant Tools"
    page.window_width = 900
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.LIGHT

    cfg = load_config()
    provider = cfg.get("provider", "openai")
    client = None

    status = ft.Text(f"Welcome to AI Assistant Tools. Provider: {provider}. Set API keys in Settings.")

    # placeholder variables for view switching (chat_view created later)
    other_view = ft.Container(content=ft.Text("Alternate View"), expand=True, alignment=ft.alignment.center)
    content_slot = None
    current_view_is_chat = True

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

    # Chat view will provide message container and selection logic

    # input + model selection row will be created after handlers are defined

    def do_send(e=None):
        nonlocal client
        message = chat_view.input_field.value.strip()
        if not message:
            return
        chat_view.append_chat("User", message)
        chat_view.input_field.value = ""
        page.update()

        if not ensure_client():
            return

        def worker():
            try:
                messages = [{"role": "user", "content": message}]
                response = client.chat(messages)
                chat_view.append_chat("Assistant", response)
            except Exception as e:
                chat_view.append_chat("Error", str(e))

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
            # update chat view's model dropdown if present
            if 'chat_view' in locals():
                chat_view.model_dd.options = [ft.dropdown.Option(o) for o in model_options_for_provider(provider)]
                chat_view.model_dd.value = cfg.get(f"{provider}_model", default_model_for_provider(provider))
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
        selected_texts = chat_view.get_selected_texts() if 'chat_view' in locals() else []
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

    # model change handler
    def model_changed(e=None):
        nonlocal client, cfg, provider
        sel = chat_view.model_dd.value or default_model_for_provider(provider)
        cfg[f"{provider}_model"] = sel
        save_config(cfg)
        client = None
        page.update()

    # now create chat view using the send handler and model change handler
    chat_view = ChatView(page, cfg, provider, on_send=do_send, on_model_change=model_changed)

    # content slot for view switching
    content_slot = ft.Container(content=chat_view.view, expand=True)

    def toggle_view(e=None):
        nonlocal current_view_is_chat
        if current_view_is_chat:
            content_slot.content = other_view
        else:
            content_slot.content = chat_view.view
        current_view_is_chat = not current_view_is_chat
        page.update()

    top_bar = make_top_bar(set_api_key_dialog, clear_api_key, summarize_selection, switch_cb=toggle_view)

    page.add(status, ft.Divider(), top_bar, content_slot)
