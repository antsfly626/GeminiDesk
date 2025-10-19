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