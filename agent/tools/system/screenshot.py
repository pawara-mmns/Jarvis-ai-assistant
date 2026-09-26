from datetime import datetime
from pathlib import Path
from typing import ClassVar

from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.platform.windows import WindowsDesktop
from agent.tools.result import ToolResult


class TakeScreenshotArguments(ToolArguments):
    pass


class TakeScreenshotTool(DesktopTool):
    name = "take_screenshot"
    description = "Save a desktop screenshot locally without sending the image to Gemini."
    arguments_type = TakeScreenshotArguments
    parameters: ClassVar[dict[str, object]] = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    def __init__(self, desktop: WindowsDesktop) -> None:
        self.desktop = desktop

    def execution_label(self, arguments: ToolArguments) -> str:
        return "Taking screenshot..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        pictures = self.desktop.resolve_known_folder("pictures")
        screenshot_directory = pictures / "JARVIS" / "Screenshots"
        screenshot_directory.mkdir(parents=True, exist_ok=True)
        filename = f"jarvis-{datetime.now().strftime('%Y-%m-%d-%H%M%S-%f')}.png"
        self.desktop.capture_screenshot(screenshot_directory / filename)
        return ToolResult.ok("Screenshot saved locally.", filename=filename)
