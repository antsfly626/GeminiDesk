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
    visual_density=ft.VisualDensity.COMFORTABLE,
)