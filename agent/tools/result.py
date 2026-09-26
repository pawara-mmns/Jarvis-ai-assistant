from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    success: bool
    message: str
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, message: str, **data: Any) -> "ToolResult":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, error: str, message: str, **data: Any) -> "ToolResult":
        return cls(success=False, error=error, message=message, data=data)

    def for_model(self) -> dict[str, Any]:
        result: dict[str, Any] = {"success": self.success, "message": self.message}
        if self.error is not None:
            result["error"] = self.error
        result.update(self.data)
        return result
