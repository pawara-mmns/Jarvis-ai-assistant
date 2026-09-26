import asyncio
from collections.abc import Awaitable, Callable, Iterable
import logging
from time import perf_counter
from typing import Any

from google.genai import types
from pydantic import ValidationError

from agent.tools.base import DesktopTool
from agent.tools.permissions import ToolPermission
from agent.tools.result import ToolResult

logger = logging.getLogger(__name__)
ToolStarted = Callable[[str, str], Awaitable[None]]


class ToolRegistry:
    def __init__(self, tools: Iterable[DesktopTool] = ()) -> None:
        self._tools: dict[str, DesktopTool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: DesktopTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool registration: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> DesktopTool | None:
        return self._tools.get(name)

    def declarations(self) -> list[types.FunctionDeclaration]:
        return [tool.declaration() for tool in self._tools.values()]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any] | None,
        on_started: ToolStarted | None = None,
    ) -> ToolResult:
        started = perf_counter()
        tool = self.get(name)
        if tool is None:
            return self._audit(name, started, ToolResult.fail("UNKNOWN_TOOL", "That action is unavailable."))
        if tool.permission is ToolPermission.BLOCKED:
            return self._audit(name, started, ToolResult.fail("BLOCKED", "That action is blocked."))
        if tool.permission is ToolPermission.CONFIRM:
            return self._audit(
                name,
                started,
                ToolResult.fail("CONFIRMATION_REQUIRED", "That action requires confirmation."),
            )

        if arguments is not None and not isinstance(arguments, dict):
            return self._audit(
                name,
                started,
                ToolResult.fail("INVALID_ARGUMENTS", "The action details were invalid."),
            )
        try:
            validated = tool.arguments_type.model_validate(arguments or {})
        except ValidationError:
            return self._audit(
                name,
                started,
                ToolResult.fail("INVALID_ARGUMENTS", "The action details were invalid."),
            )

        if on_started is not None:
            await on_started(name, tool.execution_label(validated))
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(tool.execute, validated), timeout=tool.timeout_seconds
            )
        except TimeoutError:
            result = ToolResult.fail("TIMEOUT", "The action took too long.")
        except Exception:
            logger.exception("Tool execution failed: %s", name)
            result = ToolResult.fail("EXECUTION_FAILED", "The action could not be completed.")
        return self._audit(name, started, result)

    @staticmethod
    def _audit(name: str, started: float, result: ToolResult) -> ToolResult:
        duration_ms = round((perf_counter() - started) * 1000)
        logger.info(
            "tool_audit tool=%s success=%s duration_ms=%d", name, result.success, duration_ms
        )
        return result
