import flet as ft
def main(page: ft.Page):
    page.title = "GeminiDesk Dashboard"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 40

    # Title text
    title = ft.Text(
        "🌌 GeminiDesk",
        size=36,
        weight=ft.FontWeight.BOLD,
    )

    # Subtitle
    subtitle = ft.Text(
        "Multimodal AI Workspace",
        size=18,
        color="grey400"
    )

    page.add(title, subtitle)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
