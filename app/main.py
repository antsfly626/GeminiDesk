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