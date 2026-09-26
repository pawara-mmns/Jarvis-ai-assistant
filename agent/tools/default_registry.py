from pathlib import Path

from agent.core.config import settings
from agent.tools.apps.open_app import OpenAppTool
from agent.tools.apps.resolver import ApplicationResolver
from agent.tools.browser.open_url import OpenUrlTool
from agent.tools.browser.search_web import SearchWebTool
from agent.tools.files.open_folder import OpenFolderTool
from agent.tools.files.resolver import create_folder_resolver
from agent.tools.platform.windows import WindowsDesktop
from agent.tools.registry import ToolRegistry
from agent.tools.resolution_config import load_user_alias_config
from agent.tools.system.active_window import GetActiveWindowTool
from agent.tools.system.audio_control import AudioControlTool
from agent.tools.system.screenshot import TakeScreenshotTool


def create_default_tool_registry() -> ToolRegistry:
    desktop = WindowsDesktop()
    alias_config = load_user_alias_config(Path(settings.user_aliases_path))
    folder_resolver = create_folder_resolver(
        desktop,
        configured_roots=settings.folder_roots,
        configured_aliases=alias_config.folders,
        max_depth=settings.folder_index_max_depth,
        refresh_interval_seconds=settings.resolver_refresh_seconds,
    )
    app_resolver = ApplicationResolver(
        configured_aliases=alias_config.apps,
        refresh_interval_seconds=settings.resolver_refresh_seconds,
    )
    return ToolRegistry(
        (
            OpenAppTool(desktop, app_resolver),
            OpenUrlTool(desktop),
            SearchWebTool(desktop, settings.search_url_template),
            OpenFolderTool(desktop, folder_resolver),
            AudioControlTool(desktop),
            GetActiveWindowTool(desktop),
            TakeScreenshotTool(desktop),
        )
    )
