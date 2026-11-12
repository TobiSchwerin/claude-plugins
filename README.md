# claude-plugins

Persönlicher Claude-Code-Marketplace `tobi-tools`. Enthält Agents, Skills und (später) Hooks und MCP-Konfiguration, die auf jedem Gerät gleich geladen werden.

## Struktur

```
.claude-plugin/marketplace.json     Katalog des Marketplace
plugins/core/
  .claude-plugin/plugin.json        Manifest
  agents/                           architect, implementer, reviewer
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

## Lokal testen / validieren

```
claude plugin validate .
/plugin marketplace add ./
```

## Änderungen

Agents und Skills nur hier im Repo ändern, committen, pushen, dann auf den Geräten `marketplace update`. Bei Änderungen die `version` in `plugin.json` erhöhen.
