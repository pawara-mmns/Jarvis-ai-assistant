from dataclasses import dataclass
import logging
import os
from pathlib import Path
from time import monotonic, perf_counter

from agent.tools.matching import match_score, normalize_name

logger = logging.getLogger(__name__)
MIN_CONFIDENCE = 0.70
AMBIGUITY_MARGIN = 0.06
_RISKY_SHORTCUT_WORDS = {"install", "installer", "remove", "repair", "setup", "uninstall"}
_BLOCKED_SHORTCUT_WORDS = {
    "bash",
    "cmd",
    "idle",
    "powershell",
    "pydoc",
    "python",
    "run",
    "terminal",
    "wsl",
}
_BLOCKED_SHORTCUT_PHRASES = {
    "administrative tools",
    "command prompt",
    "developer command prompt",
    "developer powershell",
    "git bash",
    "git cmd",
}


@dataclass(frozen=True)
class ResolvedApplication:
    display_name: str
    executable: Path | None = None
    shell_target: str | None = None


@dataclass(frozen=True)
class ApplicationDefinition:
    display_name: str
    aliases: tuple[str, ...]
    candidates: tuple[Path, ...] = ()
    shell_target: str | None = None


@dataclass(frozen=True)
class ApplicationResolution:
    success: bool
    error: str | None = None
    application: ResolvedApplication | None = None
    candidates: tuple[str, ...] = ()
    match_type: str | None = None


class ApplicationResolver:
    def __init__(
        self,
        configured_aliases: dict[str, str] | None = None,
        start_menu_roots: tuple[Path, ...] | None = None,
        definitions: tuple[ApplicationDefinition, ...] | None = None,
        refresh_interval_seconds: int = 300,
    ) -> None:
        self.definitions = (
            definitions if definitions is not None else self._default_definitions()
        )
        self.configured_aliases = self._valid_configured_aliases(configured_aliases or {})
        self.start_menu_roots = (
            start_menu_roots
            if start_menu_roots is not None
            else self._default_start_menu_roots()
        )
        self.refresh_interval_seconds = refresh_interval_seconds
        self._available: tuple[tuple[ResolvedApplication, tuple[str, ...]], ...] = ()
        self._built_at: float | None = None
        self._recent: dict[str, ResolvedApplication] = {}

    def display_name(self, name: str) -> str | None:
        normalized = normalize_name(name)
        configured_target = self.configured_aliases.get(normalized)
        if configured_target:
            return configured_target
        for definition in self.definitions:
            if normalized in {normalize_name(alias) for alias in definition.aliases}:
                return definition.display_name
        return None

    def refresh(self) -> None:
        available: list[tuple[ResolvedApplication, tuple[str, ...]]] = []
        seen_names: set[str] = set()
        for definition in self.definitions:
            application = self._resolve_definition(definition)
            if application is None:
                continue
            name_key = normalize_name(application.display_name)
            if name_key in seen_names:
                continue
            seen_names.add(name_key)
            available.append((application, definition.aliases))
        for shortcut in self._discover_start_menu():
            name_key = normalize_name(shortcut.display_name)
            if name_key in seen_names:
                continue
            seen_names.add(name_key)
            available.append((shortcut, (shortcut.display_name,)))
        self._available = tuple(available)
        self._built_at = monotonic()

    def resolve(self, name: str) -> ApplicationResolution:
        started = perf_counter()
        normalized = normalize_name(name)
        if self._looks_like_path(name):
            return ApplicationResolution(False, error="APP_NOT_ALLOWED")

        configured_target = self.configured_aliases.get(normalized)
        requested = configured_target or name
        recent = self._recent.get(normalized)
        if recent is not None and self._application_available(recent):
            return ApplicationResolution(
                True, application=recent, match_type="recent"
            )

        available = self._get_available()
        scored: list[tuple[float, ResolvedApplication]] = []
        for application, aliases in available:
            alias_score = max((match_score(requested, alias) for alias in aliases), default=0.0)
            display_score = match_score(requested, application.display_name)
            score = max(alias_score, display_score)
            if normalize_name(requested) in {normalize_name(alias) for alias in aliases}:
                score = 1.0
            if score >= MIN_CONFIDENCE:
                scored.append((score, application))

        if not scored:
            resolution = ApplicationResolution(False, error="APP_NOT_FOUND")
        else:
            scored.sort(
                key=lambda item: (-item[0], normalize_name(item[1].display_name))
            )
            top_score = scored[0][0]
            similarly_strong = [
                application
                for score, application in scored
                if top_score - score <= AMBIGUITY_MARGIN
            ]
            candidates = tuple(
                dict.fromkeys(application.display_name for application in similarly_strong[:4])
            )
            if len(candidates) > 1:
                resolution = ApplicationResolution(
                    False, error="AMBIGUOUS_APP", candidates=candidates
                )
            else:
                selected = scored[0][1]
                self._recent[normalized] = selected
                self._recent[normalize_name(selected.display_name)] = selected
                match_type = "configured_alias" if configured_target else (
                    "exact" if top_score >= 0.95 else "fuzzy"
                )
                resolution = ApplicationResolution(
                    True, application=selected, match_type=match_type
                )
        logger.info(
            "app_resolution success=%s name=%s match=%s duration_ms=%d",
            resolution.success,
            resolution.application.display_name if resolution.application else "-",
            resolution.match_type or resolution.error or "none",
            round((perf_counter() - started) * 1000),
        )
        logger.debug("Application resolution query=%r", name)
        return resolution

    def _get_available(self) -> tuple[tuple[ResolvedApplication, tuple[str, ...]], ...]:
        if self._built_at is None or monotonic() - self._built_at >= self.refresh_interval_seconds:
            self.refresh()
        return self._available

    def _discover_start_menu(self) -> tuple[ResolvedApplication, ...]:
        shortcuts: list[ResolvedApplication] = []
        for raw_root in self.start_menu_roots:
            try:
                root = raw_root.resolve(strict=True)
            except OSError:
                continue
            if not root.is_dir():
                continue
            pending = [root]
            while pending:
                parent = pending.pop()
                try:
                    children = list(os.scandir(parent))
                except OSError:
                    continue
                for child in children:
                    try:
                        if child.is_dir(follow_symlinks=False):
                            pending.append(Path(child.path))
                            continue
                        if not child.is_file(follow_symlinks=False) or not child.name.casefold().endswith(".lnk"):
                            continue
                        shortcut = Path(child.path)
                        canonical = shortcut.resolve(strict=True)
                        canonical.relative_to(root)
                    except (OSError, ValueError):
                        continue
                    display_name = shortcut.stem.strip()
                    normalized_name = normalize_name(display_name)
                    words = set(normalized_name.split())
                    if (
                        not display_name
                        or words & _RISKY_SHORTCUT_WORDS
                        or words & _BLOCKED_SHORTCUT_WORDS
                        or any(phrase in normalized_name for phrase in _BLOCKED_SHORTCUT_PHRASES)
                    ):
                        continue
                    shortcuts.append(
                        ResolvedApplication(display_name=display_name, shell_target=str(canonical))
                    )
        return tuple(shortcuts)

    @staticmethod
    def _resolve_definition(
        definition: ApplicationDefinition,
    ) -> ResolvedApplication | None:
        if definition.shell_target:
            return ResolvedApplication(
                definition.display_name, shell_target=definition.shell_target
            )
        executable = next((path for path in definition.candidates if path.is_file()), None)
        if executable is None:
            return None
        return ResolvedApplication(definition.display_name, executable=executable.resolve())

    @staticmethod
    def _application_available(application: ResolvedApplication) -> bool:
        if application.executable is not None:
            return application.executable.is_file()
        if application.shell_target and application.shell_target.casefold().endswith(".lnk"):
            return Path(application.shell_target).is_file()
        return bool(application.shell_target)

    @staticmethod
    def _looks_like_path(name: str) -> bool:
        stripped = name.strip().casefold()
        return (
            "\\" in stripped
            or "/" in stripped
            or ":" in stripped
            or stripped.endswith((".exe", ".cmd", ".bat", ".ps1", ".lnk"))
        )

    @staticmethod
    def _valid_configured_aliases(aliases: dict[str, str]) -> dict[str, str]:
        valid: dict[str, str] = {}
        for alias, target in aliases.items():
            if ApplicationResolver._looks_like_path(target):
                logger.warning("Ignoring application alias with path-like target")
                continue
            normalized_alias = normalize_name(alias)
            normalized_target = normalize_name(target)
            if normalized_alias and normalized_target and len(target) <= 120:
                valid[normalized_alias] = target.strip()
        return valid

    @staticmethod
    def _default_start_menu_roots() -> tuple[Path, ...]:
        app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
        program_data = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        return (
            app_data / "Microsoft/Windows/Start Menu/Programs",
            program_data / "Microsoft/Windows/Start Menu/Programs",
        )

    @staticmethod
    def _default_definitions() -> tuple[ApplicationDefinition, ...]:
        windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
        program_files = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        program_files_x86 = Path(
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        )
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")
        )
        return (
            ApplicationDefinition(
                "Google Chrome",
                ("chrome", "google chrome"),
                (
                    program_files / "Google/Chrome/Application/chrome.exe",
                    program_files_x86 / "Google/Chrome/Application/chrome.exe",
                    local_app_data / "Google/Chrome/Application/chrome.exe",
                ),
            ),
            ApplicationDefinition(
                "Microsoft Edge",
                ("edge", "microsoft edge"),
                (
                    program_files_x86 / "Microsoft/Edge/Application/msedge.exe",
                    program_files / "Microsoft/Edge/Application/msedge.exe",
                ),
            ),
            ApplicationDefinition(
                "Visual Studio Code",
                ("vscode", "vs code", "visual studio code"),
                (
                    local_app_data / "Programs/Microsoft VS Code/Code.exe",
                    program_files / "Microsoft VS Code/Code.exe",
                ),
            ),
            ApplicationDefinition("Notepad", ("notepad",), (windows / "System32/notepad.exe",)),
            ApplicationDefinition(
                "Calculator", ("calculator", "calc"), (windows / "System32/calc.exe",)
            ),
            ApplicationDefinition(
                "File Explorer", ("explorer", "file explorer"), (windows / "explorer.exe",)
            ),
            ApplicationDefinition(
                "Settings", ("settings", "windows settings"), shell_target="ms-settings:"
            ),
        )
