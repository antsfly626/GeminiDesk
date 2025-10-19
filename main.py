import os
import flet as ft
import asyncio
import json

# ── AGENTS ─────────────────────────────────────────────
from app.agents.ocr_agent import extract_text
from app.agents.router_agent import route_text
from app.agents.note_agent import run_note_agent
from app.agents.task_agent import parse as parse_task
from app.agents.cal_agent import parse_with_gemini, create_calendar_event


# ─────────────────────────────────────────────
#  MAIN FLET APP
# ─────────────────────────────────────────────
def main(page: ft.Page):
    page.title = "GeminiDesk – Multimodal AI Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 25

    # LOG AREA: shows the agent’s "thought process"
    log = ft.ListView(expand=True, spacing=8, auto_scroll=True)
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # INPUT AREA
    text_input = ft.TextField(
        label="Enter text or paste notes / tasks / events",
        multiline=True,
        min_lines=4,
        expand=True,
    )

    preview_image = ft.Image(
        src=None,
        width=250,
        height=250,
        fit=ft.ImageFit.CONTAIN,
        visible=False,
    )

    # UTIL ───────────────────────────
    def log_step(msg: str, emoji: str = "💭"):
        log.controls.append(ft.Text(f"{emoji} {msg}", size=14))
        page.update()

    def reset_log():
        log.controls.clear()
        page.update()

    # FILE PICKER CALLBACK ───────────
    def pick_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            f = e.files[0]
            text_input.value = f"📎 Selected file: {f.name}"
            preview_image.src = f.path
            preview_image.visible = True
            page.update()

    file_picker.on_result = pick_file_result

    # MAIN PIPELINE ──────────────────
    async def process_input(e):
        reset_log()
        file_path = None
        text = text_input.value.strip()

        # Determine input type
        if file_picker.result and file_picker.result.files:
            file_path = file_picker.result.files[0].path
        elif not text:
            log_step("Please upload a file or enter text.", "⚠️")
            return

        try:
            # 1️⃣ OCR or direct text
            if file_path:
                log_step(f"Extracting text from file: {os.path.basename(file_path)}", "🧠")
                text = extract_text(file_path)
                log_step(f"OCR extracted {len(text)} characters of text.", "📄")
            else:
                log_step("Using provided text input.", "✍️")

            # 2️⃣ Route content
            log_step("Routing to best-suited agent...", "🤖")
            routing = route_text(text)
            log_step(f"Router result:\n{json.dumps(routing, indent=2)}", "🔎")

            agent = routing.get("agent")
            confidence = routing.get("confidence", 0)

            if not agent or confidence < 0.5:
                log_step("Low-confidence classification. Stopping.", "⚠️")
                return

            # 3️⃣ Execute appropriate agent
            if agent == "TaskAgent":
                log_step("Detected Task → Sending to Task Agent...", "🗓️")
                result = await parse_task({"text": text})
                log_step("✅ Task created in Notion!")
                log_step(json.dumps(result, indent=2), "📘")

            elif agent == "NoteAgent":
                log_step("Detected Note → Sending to Note Agent...", "📘")
                result = run_note_agent(file_path or "note.txt")
                log_step("✅ Document added to Notion Document Hub.")
                log_step(json.dumps(result, indent=2), "📗")

            elif agent == "EventAgent":
                log_step("Detected Event → Sending to Calendar Agent...", "📅")
                parsed = parse_with_gemini(text)
                link = create_calendar_event(parsed, port=8083)
                log_step(f"✅ Calendar event created: {link}", "📅")

            elif agent == "FinanceAgent":
                log_step("Detected Finance/Receipt → (Future Agent)", "💰")

            else:
                log_step(f"Unknown agent type: {agent}", "❓")

        except Exception as err:
            log_step(f"❌ Error: {err}")

    # ─────────────────────────────────────────────
    #  UI LAYOUT
    # ─────────────────────────────────────────────
    header = ft.Text("🧩 GeminiDesk: Multimodal AI Dashboard", size=22, weight=ft.FontWeight.BOLD)
    subtitle = ft.Text(
        "Upload an image, capture from camera, or enter text. "
        "The system will extract text, classify it, and run the right agent automatically.",
        size=14,
    )

    controls = ft.Column(
        [
            header,
            subtitle,
            ft.Divider(),
            text_input,
            preview_image,
            ft.Row(
                [
                    ft.ElevatedButton(
                        "📷 Capture from Camera",
                        on_click=lambda _: file_picker.pick_files(accept='image/*', capture=True)
                    ),
                    ft.ElevatedButton(
                        "📂 Upload File",
                        on_click=lambda _: file_picker.pick_files(allow_multiple=False)
                    ),
                    ft.ElevatedButton(
                        "🚀 Process",
                        on_click=lambda e: asyncio.run(process_input(e))
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            ft.Divider(),
            ft.Text("🧠 Thought Process", size=16, weight=ft.FontWeight.BOLD),
            log,
        ],
        expand=True,
        spacing=12,
    )

    page.add(controls)


# ─────────────────────────────────────────────
#  RUN APP
# ─────────────────────────────────────────────
if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER)
