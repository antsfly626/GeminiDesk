import asyncio, json, flet as ft, plotly.graph_objects as go
from app.styles import Colors, Spacing
from app.utils.api import APIClient

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