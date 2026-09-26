from typing import ClassVar

from pydantic import Field

from agent.tools.apps.resolver import ApplicationResolver
from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.platform.windows import WindowsDesktop
from agent.tools.result import ToolResult


class OpenAppArguments(ToolArguments):
    name: str = Field(min_length=1, max_length=80)


class OpenAppTool(DesktopTool):
    name = "open_app"
    description = "Open an approved application installed on this Windows PC."
    arguments_type = OpenAppArguments
    parameters: ClassVar[dict[str, object]] = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Friendly installed app name or configured logical alias.",
            }
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    def __init__(
        self,
        desktop: WindowsDesktop,
        resolver: ApplicationResolver | None = None,
    ) -> None:
        self.desktop = desktop
        self.resolver = resolver or ApplicationResolver()

    def execution_label(self, arguments: ToolArguments) -> str:
        assert isinstance(arguments, OpenAppArguments)
        display_name = self.resolver.display_name(arguments.name)
        friendly = display_name or (
            arguments.name if not any(mark in arguments.name for mark in ("\\", "/", ":")) else "application"
        )
        return f"Finding {friendly}..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        assert isinstance(arguments, OpenAppArguments)
        resolution = self.resolver.resolve(arguments.name)
        if resolution.error == "AMBIGUOUS_APP":
            return ToolResult.fail(
                "AMBIGUOUS_APP",
                "Multiple applications match that name.",
                candidates=list(resolution.candidates),
            )
        if resolution.error == "APP_NOT_ALLOWED":
            return ToolResult.fail("APP_NOT_ALLOWED", "Executable paths are not allowed.")
        app = resolution.application
        if not resolution.success or app is None:
            return ToolResult.fail("APP_NOT_FOUND", "That application was not found.")
        if app.executable is not None:
            self.desktop.launch_executable(app.executable)
        elif app.shell_target is not None:
            self.desktop.open_shell_target(app.shell_target)
        else:
            return ToolResult.fail("APP_NOT_FOUND", f"{app.display_name} was not found.")
        return ToolResult.ok(f"{app.display_name} opened.", resolved_name=app.display_name)
