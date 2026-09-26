from typing import ClassVar

from pydantic import Field, field_validator, model_validator

from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.files.resolver import FolderResolver
from agent.tools.platform.windows import WindowsDesktop
from agent.tools.result import ToolResult


class OpenFolderArguments(ToolArguments):
    query: str | None = Field(default=None, min_length=1, max_length=512)
    candidate: str | None = Field(default=None, min_length=1, max_length=160)
    path: str | None = Field(default=None, min_length=1, max_length=512, exclude=True)

    @field_validator("query", "candidate", "path")
    @classmethod
    def non_blank_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or any(ord(character) < 32 for character in value):
            raise ValueError("folder request is invalid")
        return value

    @model_validator(mode="after")
    def require_query(self) -> "OpenFolderArguments":
        if self.query is None and self.path is None:
            raise ValueError("query is required")
        if self.query is None:
            self.query = self.path
        return self


class OpenFolderTool(DesktopTool):
    name = "open_folder"
    description = "Open a local folder by friendly name, alias, or approved path."
    arguments_type = OpenFolderArguments
    parameters: ClassVar[dict[str, object]] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Friendly folder name, alias, or approved path.",
            },
            "candidate": {
                "type": "string",
                "description": "Exact candidate name selected after an ambiguous result.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def __init__(self, desktop: WindowsDesktop, resolver: FolderResolver) -> None:
        self.desktop = desktop
        self.resolver = resolver

    def execution_label(self, arguments: ToolArguments) -> str:
        assert isinstance(arguments, OpenFolderArguments)
        target = arguments.candidate or arguments.query or "folder"
        friendly = target if len(target) <= 60 and not any(mark in target for mark in ("\\", "/", ":")) else "folder"
        return f"Finding {friendly}..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        assert isinstance(arguments, OpenFolderArguments)
        assert arguments.query is not None
        resolution = self.resolver.resolve(arguments.query, arguments.candidate)
        if resolution.error == "AMBIGUOUS_FOLDER":
            return ToolResult.fail(
                "AMBIGUOUS_FOLDER",
                "Multiple folders match that name.",
                candidates=list(resolution.candidates),
            )
        if resolution.error == "FOLDER_NOT_ALLOWED":
            return ToolResult.fail("FOLDER_NOT_ALLOWED", "That folder is outside approved locations.")
        if resolution.error == "NOT_A_FOLDER":
            return ToolResult.fail("NOT_A_FOLDER", "That path is not a folder.")
        if not resolution.success or resolution.path is None or resolution.display_name is None:
            return ToolResult.fail("FOLDER_NOT_FOUND", "I couldn't find a matching folder.")
        self.desktop.open_shell_target(str(resolution.path))
        return ToolResult.ok(
            f"{resolution.display_name} folder opened.", resolved_name=resolution.display_name
        )
