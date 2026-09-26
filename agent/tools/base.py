from abc import ABC, abstractmethod
from typing import Any, ClassVar

from google.genai import types
from pydantic import BaseModel, ConfigDict

from agent.tools.permissions import ToolPermission
from agent.tools.result import ToolResult


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DesktopTool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    arguments_type: ClassVar[type[ToolArguments]]
    parameters: ClassVar[dict[str, Any]]
    permission: ClassVar[ToolPermission] = ToolPermission.SAFE
    timeout_seconds: ClassVar[float] = 8.0

    def declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema=self.parameters,
            behavior=types.Behavior.BLOCKING,
        )

    @abstractmethod
    def execution_label(self, arguments: ToolArguments) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute(self, arguments: ToolArguments) -> ToolResult:
        raise NotImplementedError
