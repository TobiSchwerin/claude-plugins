---
name: feature-workflow
description: Standardablauf für ein neues Feature von der Idee bis zum Push auf main. Verwenden, wenn der Nutzer ein neues Feature, eine Erweiterung oder einen größeren Fix beauftragt.
---

# Feature-Workflow

Der Nutzer ist Projektleiter: er gibt Ziele vor und gibt frei. Du koordinierst.

1. **Klären:** Ziel und Akzeptanzkriterien in 3–5 Punkten zusammenfassen. Nur bei echten Unklarheiten nachfragen (max. 3 Fragen auf einmal).
2. **Planen:** Den Subagent `architect` den Plan und die Arbeitspakete erstellen lassen. Plan dem Nutzer kurz zur Freigabe zeigen.
3. **Umsetzen:** Pro Arbeitspaket den Subagent `implementer` beauftragen, jeweils in einem eigenen Git-Worktree und Branch (`feat/<kurzname>`). Unabhängige Pakete parallel, abhängige nacheinander. Auf dem Pro-Plan maximal 2–3 parallel.
4. **Prüfen:** Für jeden Branch den Subagent `reviewer` laufen lassen – **vor** dem Zusammenführen. Blocker zurück an `implementer`, bis keine mehr offen sind.
5. **Abschließen:** Branches nach `main` zusammenführen, `CHANGELOG.md` ergänzen (Format siehe Arbeitsregeln: Datum, max. 3 Zeilen „Was – Warum“), committen, pushen. Ohne CHANGELOG-Eintrag blockiert der Leitplanken-Hook den Push.
6. **Gedächtnis:** Nach dem Commit stößt der Brain-Hook die Pflege der Projektkarte an. Nur Zustand festhalten, kein Tagebuch.

Abschlussbericht an den Nutzer: die CHANGELOG-Zeilen, wie geprüft wurde, offene Punkte.
