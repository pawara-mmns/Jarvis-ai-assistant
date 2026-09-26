# Smart Resolution

## Folders

`FolderResolver` owns all name and path interpretation. Its in-memory `FolderIndex` records directory names and parent-relative context only; it never reads files. The default maximum depth is 3, dependency/build/hidden trees are skipped, results are cached for 5 minutes, and `refresh()` supports an explicit rebuild.

Trusted roots are existing Desktop, Documents, Downloads, Pictures, Videos, and Music folders; existing conventional `Projects`, `D:/Project`, `D:/Projects`, `D:/Work`, and `D:/Documents` roots; and semicolon-separated `JARVIS_FOLDER_ROOTS`. The resolver never scans a whole drive.

Matching is deterministic: configured/built-in alias, exact normalized name, intent-normalized name, prefix/token overlap, then `difflib` similarity. Scores below 0.70 are rejected. Matches within 0.06 of the best score return `AMBIGUOUS_FOLDER` with short display-name candidates. A follow-up call supplies the selected `candidate`.

Explicit paths are resolved canonically and must be inside a trusted root or exactly match a configured folder alias. Relative traversal, missing paths, files, and outside-root paths are rejected before Explorer opens.

## Applications

`ApplicationResolver` combines fixed safe definitions with `.lnk` discovery under the current-user and all-users Start Menu only. Discovery is cached and excludes installer, repair, removal, and uninstall shortcuts. Matching and ambiguity rules mirror folder resolution. Executable, script, shortcut, and arbitrary path inputs remain blocked.

## Local Aliases

Copy `config/user-aliases.example.json` to `config/user-aliases.json` (gitignored):

```json
{
  "folders": {
    "hms": "D:/Projects/HMS",
    "german notes": "D:/Documents/German Notes"
  },
  "apps": {
    "code editor": "Visual Studio Code"
  }
}
```

Folder targets must resolve to existing directories. Application targets must be logical installed names, never executable paths. Missing, malformed, or invalid entries are ignored without stopping the agent. Recent successful mappings remain in memory only and are revalidated before reuse.
