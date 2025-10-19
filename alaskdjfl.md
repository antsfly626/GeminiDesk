# GeminiDesk — Cross‑Platform (Desktop + Mobile) Flet Dashboard

> Unified adaptive layout for desktop, tablet, and mobile devices using Flet’s responsive and Material 3 capabilities.

---

## File: `main.py`

```python
import asyncio
import json
import os
import flet as ft
from dotenv import load_dotenv

from styles import THEME, Colors, Spacing
from components.upload_panel import UploadPanel
from components.agent_tabs import AgentTabs
from components.sidebar import AnalyticsSidebar
from utils.api import APIClient, MockStream

APP_TITLE = "GeminiDesk — Multimodal Agent Console"

class AppState:
    def __init__(self):
        self.kpis = {"notes": 0, "tasks": 0, "receipts": 0}
        self.activity_series = []
        self.logs_queue: asyncio.Queue[str] = asyncio.Queue()
        self.router_signal: asyncio.Queue[dict] = asyncio.Queue()
        self.mock_stream = MockStream(self.logs_queue, self.router_signal)

async def main(page: ft.Page):
    load_dotenv()

    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = THEME
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.ADAPTIVE

    state = AppState()
    api = APIClient(api_base=os.getenv("API_BASE", "http://127.0.0.1:8000"), ws_url=os.getenv("WS_URL", "ws://127.0.0.1:8000/ws/logs"))
    page.session.set("state", state)
    page.session.set("api", api)

    sidebar = AnalyticsSidebar(page)
    upload_panel = UploadPanel(page, on_submit=lambda p: asyncio.create_task(submit_payload(p, api, page)))
    agent_tabs = AgentTabs(page, state.logs_queue, state.router_signal)

    drawer = ft.NavigationDrawer(
        controls=[
            ft.NavigationDrawerDestination(icon=ft.icons.INSIGHTS, label="Analytics"),
            ft.NavigationDrawerDestination(icon=ft.icons.NOTE, label="Notes"),
            ft.NavigationDrawerDestination(icon=ft.icons.TASK, label="Tasks"),
            ft.NavigationDrawerDestination(icon=ft.icons.MONETIZATION_ON, label="Budget"),
        ]
    )
    page.drawer = drawer

    def build_layout():
        page.controls.clear()
        width = page.window_width or 1080
        is_mobile = width < 700

        appbar = ft.AppBar(
            leading=ft.IconButton(ft.icons.MENU, on_click=lambda e: page.open_drawer()),
            title=ft.Text(APP_TITLE, weight=ft.FontWeight.W_600),
            bgcolor=Colors.SURFACE,
        )

        if is_mobile:
            layout = ft.Column([
                appbar,
                upload_panel.view,
                agent_tabs.view,
                ft.Container(sidebar.view, padding=Spacing.MD),
            ])
        else:
            layout = ft.Column([
                appbar,
                ft.Row([
                    sidebar.view,
                    ft.Container(
                        content=ft.Column([
                            upload_panel.view,
                            ft.Container(height=8),
                            agent_tabs.view,
                        ], spacing=Spacing.LG, expand=True, scroll=ft.ScrollMode.AUTO),
                        expand=True,
                        padding=Spacing.XL,
                        bgcolor=Colors.BACKDROP,
                        border_radius=ft.border_radius.only(top_left=18),
                    ),
                ], expand=True),
            ])
        page.add(layout)
        page.update()

    page.on_resize = lambda e: build_layout()
    build_layout()

    async def run_background():
        ws_ok = await api.try_ws(state.logs_queue)
        if not ws_ok:
            asyncio.create_task(api.poll_logs(state.logs_queue))
        if os.getenv("DEV_MOCK", "1") == "1":
            asyncio.create_task(state.mock_stream.autorun())

    asyncio.create_task(run_background())

async def submit_payload(payload: dict, api: APIClient, page: ft.Page):
    try:
        await api.post_process(payload)
        page.show_snack_bar(ft.SnackBar(ft.Text("Submitted for processing ✅")))
    except Exception as e:
        page.show_snack_bar(ft.SnackBar(ft.Text(f"Submit failed: {e}")))

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
```

---

## File: `components/upload_panel.py`

```python
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

    def _on_drop(self, e: ft.DragTargetAcceptEvent):
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
```

---

## File: `components/sidebar.py`

```python
import flet as ft
from styles import Colors, Spacing

class KPI(ft.UserControl):
    def __init__(self, label, value, icon):
        super().__init__()
        self.label = label
        self.value = value
        self.icon = icon

    def build(self):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(self.icon, color=Colors.ACCENT_BLUE, size=20),
                    ft.Text(self.label, color=Colors.MUTED, size=12),
                ]),
                ft.Text(str(self.value), size=22, weight=ft.FontWeight.BOLD),
            ], spacing=4),
            bgcolor=Colors.SURFACE,
            padding=Spacing.MD,
            border_radius=12,
        )

class AnalyticsSidebar:
    def __init__(self, page: ft.Page):
        self.page = page
        self.kpi_notes = KPI("Notes", 0, ft.icons.NOTE)
        self.kpi_tasks = KPI("Tasks", 0, ft.icons.CHECK_CIRCLE)
        self.kpi_receipts = KPI("Receipts", 0, ft.icons.RECEIPT_LONG)

        self.view = ft.ResponsiveRow([
            ft.Column([self.kpi_notes, self.kpi_tasks, self.kpi_receipts], spacing=Spacing.MD)
        ], run_spacing=Spacing.SM)
```

---

## File: `components/agent_tabs.py`

```python
import asyncio, json, flet as ft, plotly.graph_objects as go
from styles import Colors, Spacing

class AgentTabs:
    def __init__(self, page, logs_queue, router_signal):
        self.page = page
        self.logs_queue = logs_queue
        self.router_signal = router_signal

        self.notes_md = ft.Markdown(value="", extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)
        self.tasks = ft.ListView(auto_scroll=True, expand=True)
        self.budget_chart = ft.PlotlyChart(self._pie({"Travel":3, "Meals":2, "Misc":1}), expand=True)
        self.logs = ft.ListView(expand=True, spacing=4, auto_scroll=True)
        self.diagram_frame = ft.IFrame(src="", height=400, border_radius=12)

        self.tabs = ft.Tabs(scrollable=True, expand=True, tabs=[
            ft.Tab(text="Notes", icon=ft.icons.NOTE, content=self.notes_md),
            ft.Tab(text="Tasks", icon=ft.icons.CHECKLIST, content=self.tasks),
            ft.Tab(text="Budget", icon=ft.icons.SAVINGS, content=self.budget_chart),
            ft.Tab(text="Logs", icon=ft.icons.TERMINAL, content=self.logs),
            ft.Tab(text="Diagram", icon=ft.icons.HUB, content=self.diagram_frame),
        ])

        self.view = ft.Container(self.tabs, bgcolor=Colors.SURFACE, padding=Spacing.MD, border_radius=12)

        asyncio.create_task(self._consume_logs())

    async def _consume_logs(self):
        while True:
            msg = await self.logs_queue.get()
            try:
                data = json.loads(msg)
            except Exception:
                data = {"message": msg}
            self.logs.controls.append(ft.Text(json.dumps(data)))
            self.logs.update()

    def _pie(self, data):
        fig = go.Figure(data=[go.Pie(labels=list(data.keys()), values=list(data.values()))])
        fig.update_layout(margin=dict(l=5,r=5,t=5,b=5), height=250, paper_bgcolor="rgba(0,0,0,0)")
        return fig
```

---

## File: `styles.py`

```python
import flet as ft

class Colors:
    BACKDROP = "#0b1015"
    SURFACE = "#111827"
    MUTED = "#9ca3af"
    ACCENT_BLUE = "#38bdf8"

class Spacing:
    XS, SM, MD, LG, XL = 4, 8, 12, 16, 24

THEME = ft.Theme(
    use_material3=True,
    color_scheme_seed=Colors.ACCENT_BLUE,
    visual_density=ft.ThemeVisualDensity.COMFORTABLE,
)
```

---

### ✅ Summary of Mobile Adaptations

* **Responsive rows** + dynamic `on_resize` layout rebuild.
* **Navigation drawer** on small screens.
* **FloatingActionButton** for submission.
* **Simplified sidebar → stacked KPIs**.
* **Auto‑scroll list views** instead of wide DataTables.
* **Material3 adaptive theme** with touch‑friendly spacing.

Run `flet build apk` or `flet build ios` to deploy as mobile app.
