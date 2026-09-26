import asyncio
from pathlib import Path
from typing import Any, ClassVar

from google.genai import types
import pytest

from agent.tools.apps.open_app import OpenAppTool
from agent.tools.apps.resolver import ApplicationResolution, ResolvedApplication
from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.browser.open_url import OpenUrlTool
from agent.tools.browser.search_web import SearchWebTool
from agent.tools.files.open_folder import OpenFolderTool
from agent.tools.files.resolver import FolderResolver
from agent.tools.permissions import ToolPermission
from agent.tools.platform.windows import ActiveWindow
from agent.tools.registry import ToolRegistry
from agent.tools.result import ToolResult
from agent.tools.system.active_window import GetActiveWindowTool
from agent.tools.system.audio_control import AudioControlTool
from agent.tools.system.screenshot import TakeScreenshotTool


class FakeDesktop:
    def __init__(self, known_folder: Path) -> None:
        self.known_folder = known_folder
        self.launched: list[Path] = []
        self.opened: list[str] = []
        self.volumes: list[int] = []
        self.mutes: list[bool] = []
        self.screenshots: list[Path] = []

    def launch_executable(self, executable: Path) -> None:
        self.launched.append(executable)

    def open_shell_target(self, target: str) -> None:
        self.opened.append(target)

    def resolve_known_folder(self, alias: str) -> Path:
        return self.known_folder

    def set_output_volume(self, level: int) -> None:
        self.volumes.append(level)

    def set_output_muted(self, muted: bool) -> None:
        self.mutes.append(muted)

    def get_active_window(self) -> ActiveWindow:
        return ActiveWindow("Visual Studio Code", "JARVIS Desktop AI")

    def capture_screenshot(self, destination: Path) -> None:
        destination.touch()
        self.screenshots.append(destination)


class FakeAppResolver:
    executable = Path(r"C:\Trusted\Code.exe")

    def display_name(self, name: str) -> str | None:
        return "Visual Studio Code" if name.casefold() in {"vscode", "vs code"} else None

    def resolve(self, name: str) -> ApplicationResolution:
        if "\\" in name or name.casefold().endswith(".exe"):
            return ApplicationResolution(False, error="APP_NOT_ALLOWED")
        if self.display_name(name) is None:
            return ApplicationResolution(False, error="APP_NOT_FOUND")
        return ApplicationResolution(
            True,
            application=ResolvedApplication(
                display_name="Visual Studio Code", executable=self.executable
            ),
        )


class EmptyArguments(ToolArguments):
    pass


class StubTool(DesktopTool):
    name = "stub"
    description = "Test tool."
    arguments_type = EmptyArguments
    parameters: ClassVar[dict[str, object]] = {"type": "object", "properties": {}}

    def __init__(self, result: ToolResult | None = None, raises: bool = False) -> None:
        self.result = result or ToolResult.ok("done")
        self.raises = raises
        self.calls = 0

    def execution_label(self, arguments: ToolArguments) -> str:
        return "Doing test action..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        self.calls += 1
        if self.raises:
            raise RuntimeError("private technical detail")
        return self.result


def run_tool(registry: ToolRegistry, name: str, arguments: dict[str, Any]) -> ToolResult:
    return asyncio.run(registry.execute(name, arguments))


def test_registry_resolves_known_tool_rejects_unknown_and_normalizes_exceptions() -> None:
    success_tool = StubTool()
    registry = ToolRegistry((success_tool,))
    assert run_tool(registry, "stub", {}).success
    assert success_tool.calls == 1
    unknown = run_tool(registry, "missing", {})
    assert not unknown.success and unknown.error == "UNKNOWN_TOOL"

    failed = run_tool(ToolRegistry((StubTool(raises=True),)), "stub", {})
    assert not failed.success and failed.error == "EXECUTION_FAILED"
    assert "private" not in failed.message


def test_all_phase_four_declarations_are_explicitly_blocking(tmp_path: Path) -> None:
    desktop = FakeDesktop(tmp_path)
    folder_resolver = FolderResolver((tmp_path,), {"downloads": tmp_path})
    registry = ToolRegistry(
        (
            OpenAppTool(desktop, FakeAppResolver()),
            OpenUrlTool(desktop),
            SearchWebTool(desktop, "https://www.google.com/search?q={query}"),
            OpenFolderTool(desktop, folder_resolver),
            AudioControlTool(desktop),
            GetActiveWindowTool(desktop),
            TakeScreenshotTool(desktop),
        )
    )
    declarations = registry.declarations()
    assert {declaration.name for declaration in declarations} == {
        "open_app",
        "open_url",
        "search_web",
        "open_folder",
        "audio_control",
        "get_active_window",
        "take_screenshot",
    }
    assert all(declaration.behavior is types.Behavior.BLOCKING for declaration in declarations)


def test_open_app_accepts_approved_alias_and_rejects_paths(tmp_path: Path) -> None:
    desktop = FakeDesktop(tmp_path)
    tool = OpenAppTool(desktop, FakeAppResolver())
    registry = ToolRegistry((tool,))
    assert run_tool(registry, "open_app", {"name": "vs code"}).success
    assert desktop.launched == [FakeAppResolver.executable]
    rejected = run_tool(registry, "open_app", {"name": r"C:\random\malware.exe"})
    assert not rejected.success and rejected.error == "APP_NOT_ALLOWED"
    assert desktop.launched == [FakeAppResolver.executable]


@pytest.mark.parametrize("url", ["https://example.com/path", "http://localhost:3000"])
def test_open_url_accepts_http_and_https(tmp_path: Path, url: str) -> None:
    desktop = FakeDesktop(tmp_path)
    result = run_tool(ToolRegistry((OpenUrlTool(desktop),)), "open_url", {"url": url})
    assert result.success
    assert desktop.opened == [url]


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "file:///C:/secret", "data:text/plain,test", "https://"]
)
def test_open_url_rejects_unsafe_or_malformed_urls(tmp_path: Path, url: str) -> None:
    desktop = FakeDesktop(tmp_path)
    result = run_tool(ToolRegistry((OpenUrlTool(desktop),)), "open_url", {"url": url})
    assert not result.success and result.error == "INVALID_ARGUMENTS"
    assert desktop.opened == []


def test_search_web_encodes_query(tmp_path: Path) -> None:
    desktop = FakeDesktop(tmp_path)
    tool = SearchWebTool(desktop, "https://www.google.com/search?q={query}")
    assert run_tool(ToolRegistry((tool,)), "search_web", {"query": "C++ constructors & types"}).success
    assert desktop.opened == ["https://www.google.com/search?q=C%2B%2B+constructors+%26+types"]


def test_open_folder_resolves_alias_and_rejects_missing_or_file(tmp_path: Path) -> None:
    desktop = FakeDesktop(tmp_path)
    resolver = FolderResolver((tmp_path,), {"downloads": tmp_path})
    registry = ToolRegistry((OpenFolderTool(desktop, resolver),))
    assert run_tool(registry, "open_folder", {"path": "downloads"}).success
    assert desktop.opened == [str(tmp_path)]

    missing = run_tool(registry, "open_folder", {"path": str(tmp_path / "missing")})
    assert not missing.success and missing.error == "FOLDER_NOT_FOUND"
    file_path = tmp_path / "file.txt"
    file_path.touch()
    file_result = run_tool(registry, "open_folder", {"path": str(file_path)})
    assert not file_result.success and file_result.error == "NOT_A_FOLDER"


def test_audio_control_validates_levels_and_supports_mute(tmp_path: Path) -> None:
    desktop = FakeDesktop(tmp_path)
    registry = ToolRegistry((AudioControlTool(desktop),))
    assert run_tool(registry, "audio_control", {"action": "set_volume", "level": 0}).success
    assert run_tool(registry, "audio_control", {"action": "set_volume", "level": 100}).success
    assert run_tool(registry, "audio_control", {"action": "mute"}).success
    assert run_tool(registry, "audio_control", {"action": "unmute", "level": -4}).success
    assert desktop.volumes == [0, 100]
    assert desktop.mutes == [True, False]
    for level in (-1, 101):
        result = run_tool(
            registry, "audio_control", {"action": "set_volume", "level": level}
        )
        assert not result.success and result.error == "INVALID_ARGUMENTS"


def test_active_window_and_screenshot_return_only_minimal_data(tmp_path: Path) -> None:
    desktop = FakeDesktop(tmp_path)
    registry = ToolRegistry((GetActiveWindowTool(desktop), TakeScreenshotTool(desktop)))
    active = run_tool(registry, "get_active_window", {})
    assert active.for_model() == {
        "success": True,
        "message": "Active window checked.",
        "app": "Visual Studio Code",
        "title": "JARVIS Desktop AI",
    }
    screenshot = run_tool(registry, "take_screenshot", {})
    assert screenshot.success
    assert screenshot.data["filename"].startswith("jarvis-")
    assert "path" not in screenshot.for_model()
    assert desktop.screenshots[0].parent == tmp_path / "JARVIS" / "Screenshots"
