from dataclasses import dataclass
import os
from pathlib import Path
from time import monotonic

_SKIPPED_DIRECTORY_NAMES = {
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "venv",
}


@dataclass(frozen=True)
class FolderEntry:
    name: str
    path: Path
    context: str


class FolderIndex:
    def __init__(
        self,
        roots: tuple[Path, ...],
        max_depth: int = 3,
        refresh_interval_seconds: int = 300,
    ) -> None:
        self.roots = roots
        self.max_depth = max_depth
        self.refresh_interval_seconds = refresh_interval_seconds
        self.entries: tuple[FolderEntry, ...] = ()
        self.built_at: float | None = None

    def get_entries(self) -> tuple[FolderEntry, ...]:
        if self.built_at is None or monotonic() - self.built_at >= self.refresh_interval_seconds:
            self.refresh()
        return self.entries

    def refresh(self) -> tuple[FolderEntry, ...]:
        entries: list[FolderEntry] = []
        seen: set[str] = set()
        for root in self.roots:
            self._add_entry(entries, seen, root, root.name or str(root), root.parent.name)
            self._scan_root(root, entries, seen)
        self.entries = tuple(entries)
        self.built_at = monotonic()
        return self.entries

    def _scan_root(
        self, root: Path, entries: list[FolderEntry], seen: set[str]
    ) -> None:
        pending: list[tuple[Path, int]] = [(root, 0)]
        while pending:
            parent, depth = pending.pop()
            if depth >= self.max_depth:
                continue
            try:
                children = list(os.scandir(parent))
            except OSError:
                continue
            for child in children:
                try:
                    normalized_name = child.name.casefold()
                    if child.name.startswith(".") or normalized_name in _SKIPPED_DIRECTORY_NAMES:
                        continue
                    if not child.is_dir(follow_symlinks=False):
                        continue
                    path = Path(child.path).resolve(strict=True)
                    path.relative_to(root)
                except (OSError, ValueError):
                    continue
                relative_parent = path.parent.relative_to(root)
                context = root.name if relative_parent == Path(".") else str(relative_parent)
                self._add_entry(entries, seen, path, child.name, context)
                pending.append((path, depth + 1))

    @staticmethod
    def _add_entry(
        entries: list[FolderEntry], seen: set[str], path: Path, name: str, context: str
    ) -> None:
        key = os.path.normcase(str(path))
        if key in seen:
            return
        seen.add(key)
        entries.append(FolderEntry(name=name, path=path, context=context))
