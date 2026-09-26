from typing import ClassVar
from urllib.parse import quote_plus

from pydantic import Field, field_validator

from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.browser.open_url import validate_web_url
from agent.tools.platform.windows import WindowsDesktop
from agent.tools.result import ToolResult


class SearchWebArguments(ToolArguments):
    query: str = Field(min_length=1, max_length=500)

    @field_validator("query")
    @classmethod
    def non_blank_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("query must not be blank")
        return value


class SearchWebTool(DesktopTool):
    name = "search_web"
    description = "Open a web search for a query in the default browser."
    arguments_type = SearchWebArguments
    parameters: ClassVar[dict[str, object]] = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Search terms."}},
        "required": ["query"],
        "additionalProperties": False,
    }

    def __init__(self, desktop: WindowsDesktop, search_url_template: str) -> None:
        if search_url_template.count("{query}") != 1:
            raise ValueError("search URL template must contain one {query} placeholder")
        validate_web_url(search_url_template.replace("{query}", "test"))
        self.desktop = desktop
        self.search_url_template = search_url_template

    def execution_label(self, arguments: ToolArguments) -> str:
        return "Searching the web..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        assert isinstance(arguments, SearchWebArguments)
        url = self.search_url_template.replace("{query}", quote_plus(arguments.query))
        self.desktop.open_shell_target(url)
        return ToolResult.ok("Web search opened.")
