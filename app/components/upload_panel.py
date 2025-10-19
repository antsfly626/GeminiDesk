import flet as ft
from styles import Colors, Spacing

class UploadPanel:
    def __init__(self, page: ft.Page, on_submit):
        self.page = page
        self.on_submit = on_submit
        self.files = []
        self.previews = ft.ResponsiveRow(run_spacing=Spacing.SM)

        self.text_input = ft.TextField(
            hint_text="Type a prompt or message for Gemini…",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=12,
            filled=True,
            expand=True,
        )

        self.fp = ft.FilePicker(on_result=self._on_pick)
        page.overlay.append(self.fp)

        self.drop = ft.DragTarget(
            group="uploads",
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Drop files here or pick below", size=12, color=Colors.MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                height=100,
                bgcolor=Colors.SURFACE,
                border_radius=12,
            ),
            on_accept=self._on_drop,
        )

        self.submit_btn = ft.FloatingActionButton(
            icon=ft.icons.SEND, text="Send", on_click=lambda e: self._submit(),
        )

        self.view = ft.Column(
            controls=[
                ft.Row([
                    ft.Text("Upload", weight=ft.FontWeight.W_600, size=18),
                    ft.Container(expand=True),
                    ft.IconButton(ft.icons.UPLOAD_FILE, tooltip="Pick files", on_click=lambda e: self.fp.pick_files(allow_multiple=True)),
                ]),
                self.drop,
                self.previews,
                self.text_input,
                self.submit_btn,
            ],
            spacing=Spacing.MD,
            responsive=True,
        )

    def _on_pick(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.files.extend(e.files)
            self._refresh_previews()

    def _on_drop(self, e: ft.DragTargetEvent):
        self._refresh_previews()

    def _refresh_previews(self):
        previews = []
        for f in self.files[:6]:
            previews.append(ft.Container(
                content=ft.Text(f.name, size=11),
                width=100,
                height=60,
                bgcolor=Colors.SURFACE,
                border_radius=8,
                alignment=ft.alignment.center,
            ))
        self.previews.controls = previews
        self.previews.update()

    def _submit(self):
        payload = {"text": self.text_input.value, "files": [{"name": f.name} for f in self.files]}
        self.on_submit(payload)