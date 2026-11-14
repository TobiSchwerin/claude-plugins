# claude-plugins

Persönlicher Claude-Code-Marketplace `tobi-tools`. Enthält Agents, Skills und (später) Hooks und MCP-Konfiguration, die auf jedem Gerät gleich geladen werden.

## Struktur

```
.claude-plugin/marketplace.json     Katalog des Marketplace
plugins/core/
  .claude-plugin/plugin.json        Manifest
  agents/                           architect, implementer, reviewer
  hooks/                            claude-brain: laden, Pflege anstoßen, Auto-Sync
  skills/feature-workflow/SKILL.md  Standardablauf Feature → PR
```

## Installation auf einem neuen Gerät

In Claude Code:

```
/plugin marketplace add TobiSchwerin/claude-plugins
/plugin install core@tobi-tools
```

Aktualisieren nach Änderungen im Repo:

```
/plugin marketplace update tobi-tools
```

## claude-brain-Hooks

Voraussetzungen auf jedem Gerät: Git, Python >= 3.8 und ein Klon von `TobiSchwerin/claude-brain`.
Pfad in `~/.claude/settings.json` eintragen (sonst Standard `~/claude-brain`):

```json
{ "env": { "CLAUDE_BRAIN_DIR": "D:/Programmieren/claude-brain" } }
```

| Ereignis | Was passiert |
|---|---|
| SessionStart | `git pull` im Brain, `index.md` und die Projektkarte des aktuellen Repos kommen in den Kontext |
| Stop | Brain geändert → Index bauen, committen, pushen. Neuer Commit im Arbeits-Repo → einmal Pflege anstoßen |
| SessionEnd | Letzte Brain-Änderungen committen und pushen |

## Lokal testen / validieren

```
claude plugin validate .
/plugin marketplace add ./
```

## Änderungen

Agents und Skills nur hier im Repo ändern, committen, pushen, dann auf den Geräten `marketplace update`. Bei Änderungen die `version` in `plugin.json` erhöhen.
