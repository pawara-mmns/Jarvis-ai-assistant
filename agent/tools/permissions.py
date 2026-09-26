from enum import StrEnum


class ToolPermission(StrEnum):
    SAFE = "safe"
    CONFIRM = "confirm"
    BLOCKED = "blocked"
