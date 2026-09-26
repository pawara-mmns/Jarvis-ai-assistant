from pathlib import Path

from agent.tools.apps.resolver import ApplicationDefinition, ApplicationResolver
from agent.tools.files.resolver import FolderResolver
from agent.tools.resolution_config import load_user_alias_config


def create_folder(root: Path, name: str) -> Path:
    path = root / name
    path.mkdir(parents=True)
    return path


def test_folder_exact_alias_normalized_prefix_and_fuzzy_matches(tmp_path: Path) -> None:
    hms = create_folder(tmp_path, "HMS - Catalyst")
    notes = create_folder(tmp_path, "German Notes")
    java = create_folder(tmp_path, "Java Projects")
    resolver = FolderResolver((tmp_path,), {"hotel system": hms})

    assert resolver.resolve("hotel system").path == hms
    assert resolver.resolve("  GERMAN---NOTES ").path == notes
    assert resolver.resolve("german note").path == notes
    assert resolver.resolve("germen nots").path == notes
    assert resolver.resolve("java project").path == java
    assert resolver.resolve("Catalyst HMS").path == hms
    assert resolver.resolve("something completely missing").error == "FOLDER_NOT_FOUND"


def test_java_intent_does_not_match_javascript_name(tmp_path: Path) -> None:
    workspace = create_folder(tmp_path, "workspace")
    create_folder(workspace, "JavaScript")
    resolver = FolderResolver((workspace,))
    assert resolver.resolve("Java project").error == "FOLDER_NOT_FOUND"


def test_folder_ambiguity_requires_candidate_selection(tmp_path: Path) -> None:
    alpha = create_folder(tmp_path, "HMS Alpha")
    create_folder(tmp_path, "HMS Backup")
    resolver = FolderResolver((tmp_path,))

    ambiguous = resolver.resolve("HMS")
    assert ambiguous.error == "AMBIGUOUS_FOLDER"
    assert ambiguous.candidates == ("HMS Alpha", "HMS Backup")

    selected = resolver.resolve("HMS", candidate="HMS Alpha")
    assert selected.success and selected.path == alpha


def test_duplicate_folder_names_return_context_candidates(tmp_path: Path) -> None:
    primary_parent = create_folder(tmp_path, "Primary")
    backup_parent = create_folder(tmp_path, "Backup")
    primary = create_folder(primary_parent, "HMS")
    create_folder(backup_parent, "HMS")
    resolver = FolderResolver((tmp_path,))

    ambiguous = resolver.resolve("HMS")
    assert ambiguous.error == "AMBIGUOUS_FOLDER"
    assert ambiguous.candidates == ("HMS (Backup)", "HMS (Primary)")
    selected = resolver.resolve("HMS", candidate="HMS (Primary)")
    assert selected.path == primary


def test_folder_explicit_paths_require_canonical_trusted_containment(tmp_path: Path) -> None:
    trusted = create_folder(tmp_path, "trusted")
    allowed = create_folder(trusted, "Java")
    outside = create_folder(tmp_path, "outside")
    resolver = FolderResolver((trusted,))

    assert resolver.resolve(str(allowed)).path == allowed
    assert resolver.resolve(str(outside)).error == "FOLDER_NOT_ALLOWED"
    assert resolver.resolve(r"..\..\Windows").error == "FOLDER_NOT_ALLOWED"

    file_path = trusted / "notes.txt"
    file_path.touch()
    assert resolver.resolve(str(file_path)).error == "NOT_A_FOLDER"


def test_folder_recent_resolution_survives_new_ambiguous_match(tmp_path: Path) -> None:
    catalyst = create_folder(tmp_path, "HMS Catalyst")
    resolver = FolderResolver((tmp_path,))
    first = resolver.resolve("HMS")
    assert first.success and first.path == catalyst

    create_folder(tmp_path, "HMS Central")
    resolver.refresh()
    repeated = resolver.resolve("HMS")
    assert repeated.path == catalyst and repeated.match_type == "recent"


def test_folder_index_is_bounded_by_configured_depth(tmp_path: Path) -> None:
    level_one = create_folder(tmp_path, "one")
    level_two = create_folder(level_one, "two")
    create_folder(level_two, "Hidden Target")
    resolver = FolderResolver((tmp_path,), max_depth=2)
    assert resolver.resolve("Hidden Target").error == "FOLDER_NOT_FOUND"


def app_definition(display_name: str, aliases: tuple[str, ...], executable: Path) -> ApplicationDefinition:
    executable.touch()
    return ApplicationDefinition(display_name, aliases, (executable,))


def test_app_alias_normalized_name_and_configured_alias(tmp_path: Path) -> None:
    code = tmp_path / "Code.exe"
    resolver = ApplicationResolver(
        configured_aliases={"code editor": "Visual Studio Code"},
        start_menu_roots=(),
        definitions=(app_definition("Visual Studio Code", ("vscode", "vs code"), code),),
    )

    assert resolver.resolve("vs code").application.executable == code
    assert resolver.resolve("visual---studio code").application.executable == code
    configured = resolver.resolve("code editor")
    assert configured.application.executable == code
    assert configured.match_type == "configured_alias"


def test_app_start_menu_discovery_unknown_and_path_rejection(tmp_path: Path) -> None:
    start_menu = create_folder(tmp_path, "Start Menu")
    shortcut = start_menu / "Catalyst Console.lnk"
    shortcut.touch()
    (start_menu / "Uninstall Catalyst.lnk").touch()
    (start_menu / "Command Prompt.lnk").touch()
    (start_menu / "Windows PowerShell.lnk").touch()
    resolver = ApplicationResolver(start_menu_roots=(start_menu,), definitions=())

    discovered = resolver.resolve("catalyst console")
    assert discovered.success
    assert discovered.application.shell_target == str(shortcut.resolve())
    assert resolver.resolve("unknown utility").error == "APP_NOT_FOUND"
    assert resolver.resolve(r"C:\Temp\test.exe").error == "APP_NOT_ALLOWED"
    assert resolver.resolve("Uninstall Catalyst").error == "APP_NOT_FOUND"
    assert resolver.resolve("Command Prompt").error == "APP_NOT_FOUND"
    assert resolver.resolve("PowerShell").error == "APP_NOT_FOUND"


def test_app_ambiguity_and_recent_resolution(tmp_path: Path) -> None:
    alpha_exe = tmp_path / "alpha.exe"
    beta_exe = tmp_path / "beta.exe"
    resolver = ApplicationResolver(
        start_menu_roots=(),
        definitions=(
            app_definition("Photo Alpha", ("photo alpha",), alpha_exe),
            app_definition("Photo Beta", ("photo beta",), beta_exe),
        ),
    )
    ambiguous = resolver.resolve("photo")
    assert ambiguous.error == "AMBIGUOUS_APP"
    assert ambiguous.candidates == ("Photo Alpha", "Photo Beta")

    recent_resolver = ApplicationResolver(
        start_menu_roots=(),
        definitions=(app_definition("Catalyst Editor", ("catalyst",), alpha_exe),),
    )
    first = recent_resolver.resolve("catalyst")
    assert first.success
    repeated = recent_resolver.resolve("catalyst")
    assert repeated.application == first.application
    assert repeated.match_type == "recent"


def test_user_alias_config_ignores_invalid_entries_without_crashing(tmp_path: Path) -> None:
    config_path = tmp_path / "aliases.json"
    config_path.write_text(
        '{"folders":{"hms":"D:/Projects/HMS","bad":4},'
        '"apps":{"editor":"Visual Studio Code","bad":false}}',
        encoding="utf-8",
    )
    config = load_user_alias_config(config_path)
    assert config.folders == {"hms": "D:/Projects/HMS"}
    assert config.apps == {"editor": "Visual Studio Code"}

    config_path.write_text("not-json", encoding="utf-8")
    assert load_user_alias_config(config_path).folders == {}
