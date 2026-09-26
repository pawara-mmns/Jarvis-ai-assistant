from typing import ClassVar

from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.platform.windows import WindowsDesktop
from agent.tools.result import ToolResult


class GetActiveWindowArguments(ToolArguments):
    pass


class GetActiveWindowTool(DesktopTool):
    name = "get_active_window"
    description = "Get the active application's name and window title without capturing contents."
    arguments_type = GetActiveWindowArguments
    parameters: ClassVar[dict[str, object]] = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    def __init__(self, desktop: WindowsDesktop) -> None:
        self.desktop = desktop

    def execution_label(self, arguments: ToolArguments) -> str:
        return "Checking the active window..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        active = self.desktop.get_active_window()
        title = active.title or active.app
        return ToolResult.ok("Active window checked.", app=active.app, title=title)
