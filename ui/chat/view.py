import flet as ft
from .messages import make_message_container
from .input_row import make_input_row


class ChatView:
    def __init__(self, page: ft.Page, cfg, provider: str, on_send, on_model_change):
        self.page = page
        self.cfg = cfg
        self.provider = provider
        self.selected_indices = set()

        self.messages_list = ft.Column(expand=True)
        self.messages_container = ft.Container(self.messages_list, expand=True, padding=10)

        # create input row and keep references
        self.send_row, self.input_field, self.model_dd = make_input_row(cfg, provider, on_send, on_model_change)

        # combined view
        self.view = ft.Column([self.messages_container, self.send_row], expand=True)

    def append_chat(self, role: str, text: str):
        idx = len(self.messages_list.controls)
        self.messages_list.controls.append(make_message_container(role, text, idx, self.toggle_select))
        self.page.update()

    def toggle_select(self, idx: int):
        if idx in self.selected_indices:
            self.selected_indices.remove(idx)
            self.messages_list.controls[idx].border = ft.border.all(1, "#E0E0E0")
        else:
            self.selected_indices.add(idx)
            self.messages_list.controls[idx].border = ft.border.all(2, "#1E88E5")
        self.page.update()

    def get_selected_texts(self):
        return [self.messages_list.controls[i].content.controls[1].value for i in sorted(self.selected_indices)]
