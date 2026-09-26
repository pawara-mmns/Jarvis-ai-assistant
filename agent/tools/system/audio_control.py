from typing import ClassVar, Literal

from pydantic import model_validator

from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.platform.windows import WindowsDesktop
from agent.tools.result import ToolResult


class AudioControlArguments(ToolArguments):
    action: Literal["set_volume", "mute", "unmute"]
    level: int | None = None

    @model_validator(mode="after")
    def validate_action_level(self) -> "AudioControlArguments":
        if self.action == "set_volume":
            if self.level is None or isinstance(self.level, bool) or not 0 <= self.level <= 100:
                raise ValueError("set_volume requires an integer level from 0 to 100")
        else:
            self.level = None
        return self


class AudioControlTool(DesktopTool):
    name = "audio_control"
    description = "Set, mute, or unmute Windows system output volume."
    arguments_type = AudioControlArguments
    parameters: ClassVar[dict[str, object]] = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["set_volume", "mute", "unmute"]},
            "level": {"type": "integer", "minimum": 0, "maximum": 100},
        },
        "required": ["action"],
        "additionalProperties": False,
    }

    def __init__(self, desktop: WindowsDesktop) -> None:
        self.desktop = desktop

    def execution_label(self, arguments: ToolArguments) -> str:
        assert isinstance(arguments, AudioControlArguments)
        if arguments.action == "set_volume":
            return f"Setting volume to {arguments.level}%..."
        return "Muting system audio..." if arguments.action == "mute" else "Unmuting system audio..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        assert isinstance(arguments, AudioControlArguments)
        if arguments.action == "set_volume":
            assert arguments.level is not None
            self.desktop.set_output_volume(arguments.level)
            return ToolResult.ok(f"System volume set to {arguments.level}%.", level=arguments.level)
        muted = arguments.action == "mute"
        self.desktop.set_output_muted(muted)
        return ToolResult.ok("System audio muted." if muted else "System audio unmuted.")
