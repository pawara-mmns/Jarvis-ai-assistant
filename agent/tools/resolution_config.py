from dataclasses import dataclass, field
import json
import logging
from pathlib import Path

from agent.tools.matching import normalize_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UserAliasConfig:
    folders: dict[str, str] = field(default_factory=dict)
    apps: dict[str, str] = field(default_factory=dict)


def load_user_alias_config(path: Path) -> UserAliasConfig:
    if not path.is_file():
        return UserAliasConfig()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        logger.warning("Ignoring invalid user alias configuration")
        return UserAliasConfig()
    if not isinstance(raw, dict):
        logger.warning("Ignoring user alias configuration with invalid root value")
        return UserAliasConfig()
    return UserAliasConfig(
        folders=_string_mapping(raw.get("folders"), "folder"),
        apps=_string_mapping(raw.get("apps"), "application"),
    )


def _string_mapping(value: object, kind: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        logger.warning("Ignoring invalid %s aliases", kind)
        return {}
    result: dict[str, str] = {}
    for raw_alias, raw_target in value.items():
        if not isinstance(raw_alias, str) or not isinstance(raw_target, str):
            logger.warning("Ignoring invalid %s alias entry", kind)
            continue
        alias = normalize_name(raw_alias)
        target = raw_target.strip()
        if not alias or len(alias) > 80 or not target or len(target) > 512:
            logger.warning("Ignoring invalid %s alias entry", kind)
            continue
        result[alias] = target
    return result
