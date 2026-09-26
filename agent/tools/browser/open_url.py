from typing import ClassVar
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, field_validator

from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.platform.windows import WindowsDesktop
from agent.tools.result import ToolResult


def validate_web_url(value: str) -> str:
    if any(ord(character) < 32 for character in value):
        raise ValueError("URL contains control characters")
    parsed = urlsplit(value.strip())
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc or parsed.hostname is None:
        raise ValueError("only absolute HTTP(S) URLs are allowed")
    try:
        parsed.port
    except ValueError as error:
        raise ValueError("URL port is invalid") from error
    return urlunsplit((parsed.scheme.casefold(), parsed.netloc, parsed.path, parsed.query, parsed.fragment))


class OpenUrlArguments(ToolArguments):
    url: str = Field(min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def valid_url(cls, value: str) -> str:
        return validate_web_url(value)


class OpenUrlTool(DesktopTool):
    name = "open_url"
    description = "Open an HTTP or HTTPS URL in the default browser."
    arguments_type = OpenUrlArguments
    parameters: ClassVar[dict[str, object]] = {
        "type": "object",
        "properties": {"url": {"type": "string", "description": "Absolute http:// or https:// URL."}},
        "required": ["url"],
        "additionalProperties": False,
    }

    def __init__(self, desktop: WindowsDesktop) -> None:
        self.desktop = desktop

    def execution_label(self, arguments: ToolArguments) -> str:
        return "Opening website..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        assert isinstance(arguments, OpenUrlArguments)
        self.desktop.open_shell_target(arguments.url)
        return ToolResult.ok("Website opened.")
