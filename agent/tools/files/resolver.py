from dataclasses import dataclass
import logging
import os
from pathlib import Path
from time import perf_counter

from agent.tools.files.index import FolderEntry, FolderIndex
from agent.tools.matching import match_score, normalize_name
from agent.tools.platform.windows import WindowsDesktop

logger = logging.getLogger(__name__)
MIN_CONFIDENCE = 0.70
AMBIGUITY_MARGIN = 0.06


@dataclass(frozen=True)
class FolderResolution:
    success: bool
    error: str | None = None
    path: Path | None = None
    display_name: str | None = None
    candidates: tuple[str, ...] = ()
    match_type: str | None = None


class FolderResolver:
    def __init__(
        self,
        roots: tuple[Path, ...],
        aliases: dict[str, Path] | None = None,
        max_depth: int = 3,
        refresh_interval_seconds: int = 300,
    ) -> None:
        self.roots = self._valid_roots(roots)
        self.aliases = self._valid_aliases(aliases or {})
        self.index = FolderIndex(self.roots, max_depth, refresh_interval_seconds)
        self._recent: dict[str, Path] = {}

    def refresh(self) -> None:
        self.index.refresh()

    def resolve(self, query: str, candidate: str | None = None) -> FolderResolution:
        started = perf_counter()
        requested = candidate.strip() if candidate else query.strip()
        if self._looks_like_path(requested):
            resolution = self._resolve_explicit_path(requested)
        else:
            resolution = self._resolve_name(query, candidate)
        logger.info(
            "folder_resolution success=%s name=%s match=%s duration_ms=%d",
            resolution.success,
            resolution.display_name or "-",
            resolution.match_type or resolution.error or "none",
            round((perf_counter() - started) * 1000),
        )
        logger.debug("Folder resolution query=%r", query)
        return resolution

    def _resolve_name(self, query: str, candidate: str | None) -> FolderResolution:
        normalized_query = normalize_name(query)
        requested = candidate or query
        normalized_requested = normalize_name(requested)

        alias_path = self.aliases.get(normalized_requested) or (
            self.aliases.get(normalized_query) if candidate is None else None
        )
        if alias_path is not None and self._path_is_available(alias_path):
            self._remember(query, alias_path)
            return FolderResolution(
                True, path=alias_path, display_name=alias_path.name, match_type="alias"
            )

        recent = self._recent.get(normalized_query)
        if candidate is None and recent is not None and self._path_is_available(recent):
            return FolderResolution(
                True, path=recent, display_name=recent.name, match_type="recent"
            )

        scored: list[tuple[float, FolderEntry]] = []
        entries = self.index.get_entries()
        labels = self._entry_labels(entries)
        for entry in entries:
            label = labels[entry.path]
            score = (
                1.0
                if candidate is not None and normalize_name(candidate) == normalize_name(label)
                else match_score(requested, entry.name)
            )
            if score >= MIN_CONFIDENCE:
                scored.append((score, entry))
        if not scored:
            return FolderResolution(False, error="FOLDER_NOT_FOUND")
        scored.sort(key=lambda item: (-item[0], normalize_name(item[1].name), str(item[1].path)))

        top_score = scored[0][0]
        similarly_strong = [
            entry for score, entry in scored if top_score - score <= AMBIGUITY_MARGIN
        ]
        if candidate is None and len(similarly_strong) > 1:
            candidates = tuple(labels[entry.path] for entry in similarly_strong[:4])
            return FolderResolution(
                False, error="AMBIGUOUS_FOLDER", candidates=candidates
            )

        selected = scored[0][1]
        self._remember(query, selected.path)
        self._recent[normalize_name(selected.name)] = selected.path
        match_type = "exact" if normalize_name(requested) == normalize_name(selected.name) else "fuzzy"
        return FolderResolution(
            True,
            path=selected.path,
            display_name=selected.name,
            match_type=match_type,
        )

    @staticmethod
    def _entry_labels(entries: tuple[FolderEntry, ...]) -> dict[Path, str]:
        counts: dict[str, int] = {}
        for entry in entries:
            key = normalize_name(entry.name)
            counts[key] = counts.get(key, 0) + 1
        return {
            entry.path: (
                f"{entry.name} ({Path(entry.context).name})"
                if counts[normalize_name(entry.name)] > 1
                else entry.name
            )
            for entry in entries
        }

    def _resolve_explicit_path(self, value: str) -> FolderResolution:
        expanded = os.path.expandvars(os.path.expanduser(value))
        path = Path(expanded)
        if not path.is_absolute():
            return FolderResolution(False, error="FOLDER_NOT_ALLOWED")
        try:
            canonical = path.resolve(strict=True)
        except (OSError, RuntimeError):
            return FolderResolution(False, error="FOLDER_NOT_FOUND")
        if not canonical.is_dir():
            return FolderResolution(False, error="NOT_A_FOLDER")
        if not self._is_allowed(canonical):
            return FolderResolution(False, error="FOLDER_NOT_ALLOWED")
        return FolderResolution(
            True, path=canonical, display_name=canonical.name, match_type="approved_path"
        )

    def _is_allowed(self, path: Path) -> bool:
        if any(path == alias_path for alias_path in self.aliases.values()):
            return True
        return any(path == root or path.is_relative_to(root) for root in self.roots)

    def _path_is_available(self, path: Path) -> bool:
        return path.is_dir() and self._is_allowed(path)

    def _remember(self, query: str, path: Path) -> None:
        self._recent[normalize_name(query)] = path

    @staticmethod
    def _looks_like_path(value: str) -> bool:
        return (
            ".." in Path(value).parts
            or Path(value).is_absolute()
            or value.startswith(("~", "%"))
            or "\\" in value
            or "/" in value
        )

    @staticmethod
    def _valid_roots(roots: tuple[Path, ...]) -> tuple[Path, ...]:
        valid: list[Path] = []
        seen: set[str] = set()
        for root in roots:
            try:
                canonical = root.expanduser().resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            key = os.path.normcase(str(canonical))
            if not canonical.is_dir() or key in seen:
                continue
            seen.add(key)
            valid.append(canonical)
        return tuple(valid)

    def _valid_aliases(self, aliases: dict[str, Path]) -> dict[str, Path]:
        valid: dict[str, Path] = {}
        for alias, target in aliases.items():
            try:
                canonical = target.expanduser().resolve(strict=True)
            except (OSError, RuntimeError):
                logger.warning("Ignoring folder alias with missing target")
                continue
            if not canonical.is_dir():
                logger.warning("Ignoring folder alias whose target is not a directory")
                continue
            valid[normalize_name(alias)] = canonical
        return valid


def create_folder_resolver(
    desktop: WindowsDesktop,
    configured_roots: str = "",
    configured_aliases: dict[str, str] | None = None,
    max_depth: int = 3,
    refresh_interval_seconds: int = 300,
) -> FolderResolver:
    known_names = ("desktop", "documents", "downloads", "pictures", "videos", "music")
    roots = [desktop.resolve_known_folder(name) for name in known_names]
    home = Path.home()
    roots.extend(
        path
        for path in (
            home / "Projects",
            Path("D:/Project"),
            Path("D:/Projects"),
            Path("D:/Work"),
            Path("D:/Documents"),
        )
        if path.is_dir()
    )
    roots.extend(Path(value.strip()) for value in configured_roots.split(";") if value.strip())

    aliases: dict[str, Path] = {}
    alias_phrases = {
        "downloads": ("downloads", "download", "download folder", "my downloads"),
        "documents": ("documents", "docs", "document folder", "my documents"),
        "desktop": ("desktop", "my desktop"),
        "pictures": ("pictures", "photos", "my pictures"),
        "videos": ("videos", "my videos"),
        "music": ("music", "my music"),
    }
    for name, phrases in alias_phrases.items():
        target = desktop.resolve_known_folder(name)
        if target.is_dir():
            aliases.update({phrase: target for phrase in phrases})
    for alias, raw_path in (configured_aliases or {}).items():
        aliases[alias] = Path(os.path.expandvars(raw_path))
    return FolderResolver(
        tuple(roots), aliases, max_depth=max_depth, refresh_interval_seconds=refresh_interval_seconds
    )
