# claude-plugins

Persönlicher Claude-Code-Marketplace `tobi-tools`. Enthält Agents, Skills und (später) Hooks und MCP-Konfiguration, die auf jedem Gerät gleich geladen werden.

## Struktur

```
.claude-plugin/marketplace.json       Katalog des Marketplace
plugins/core/
  .claude-plugin/plugin.json          Manifest
  agents/                             architect (Plan), implementer (Test zuerst), reviewer (unabhängige Prüfung)
  skills/requirements/                Requirements Engineer: Interview → Spec mit Anforderungs-IDs (+ Vorlagen)
  skills/feature-workflow/            Spec → Plan → Build → Prüfung → CHANGELOG → Push (+ Vorlagen)
  skills/projekt-onboarding/          bestehendes Repo in die Struktur bringen
  hooks/                              claude-brain (brain_hook.py) und Leitplanken (guard.py)
```

## Ablauf pro Feature

`requirements` (Interview, **Freigabe 1**) → `feature-workflow`: `architect` → `implementer` (je Aufgabe, Test erst rot)
→ `reviewer` (frische Instanz, nur Spec) → **Freigabe 2** → CHANGELOG → Push.
Rückverfolgbarkeit: ID `F-012.A1` steht in Spec, Plan-Aufgabe, Testname und Prüfbericht.

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
| SessionStart | 4 Hooks (je max. 10.000 Zeichen): `git pull` + `index.md`, Brain-Regeln, Arbeitsregeln, Projektkarte des aktuellen Repos |
| Stop | Brain geändert → Index bauen, committen, pushen. Neuer Commit im Arbeits-Repo → einmal Pflege anstoßen |
| SessionEnd | Letzte Brain-Änderungen committen und pushen |

## Leitplanken (guard.py, PreToolUse)

| Stufe | Was |
|---|---|
| deny | Secret-Dateien anzeigen/lesen, Force-Push, Historie umschreiben, `rm -rf` auf breite Pfade, Push auf main ohne CHANGELOG-Eintrag |
| ask | Docker-Volumes/Datenbanken löschen, UFW/SSH-Konfiguration, Repo löschen, `git reset --hard`, `git clean`, echte `.env` überschreiben |
| frei | alles andere |

`ask` erzwingt auch im Auto-Modus eine Rückfrage. Ohne Python >= 3.8 sind die Hooks aus; der Start-Hook meldet das.

## Lokal testen / validieren

```
claude plugin validate .
/plugin marketplace add ./
```

## Änderungen

Agents und Skills nur hier im Repo ändern, committen, pushen, dann auf den Geräten `marketplace update`. Bei Änderungen die `version` in `plugin.json` erhöhen.
