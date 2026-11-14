---
name: feature-workflow
description: Baut ein Feature mit freigegebener Spec von der Architektur bis zum Push auf main – Plan mit Aufgaben pro Anforderungs-ID, Build mit Test-zuerst, unabhängige Prüfung, Prüfbericht, CHANGELOG. Verwenden, wenn Tobias ein Feature umsetzen lassen will oder ein abgebrochener Build fortgesetzt werden soll.
---

# Feature-Workflow

Tobias ist Projektleiter. Du koordinierst die Agents `architect`, `implementer`, `reviewer` und schreibst selbst keinen
Produktivcode. Der rote Faden: **jede Anforderungs-ID ist von der Spec über Aufgabe und Test bis zum Prüfbericht verfolgbar.**

## 0. Voraussetzungen und Wiedereinstieg
1. Spec `docs/specs/F-<NNN>-*.md` mit `status: freigegeben` (oder `in-arbeit` beim Fortsetzen). Keine Spec →
   Skill `requirements`. Kleine Fehlerbehebungen ohne neues Verhalten brauchen keine Spec, aber einen Test, der den Fehler zeigt.
2. Existiert `docs/plans/F-<NNN>.md`, dort weitermachen: offene Aufgaben ab dem ersten nicht erledigten Häkchen.
3. Spec und FEATURES.md auf `in-arbeit` setzen.

## 1. Architektur und Plan
Subagent `architect` mit Spec-Pfad und dem **absoluten** Pfad zu `vorlagen/plan.md` aus dem Verzeichnis dieses Skills beauftragen
(Subagents kennen den Plugin-Pfad nicht). Ergebnis: `docs/plans/F-<NNN>.md`.
Prüfe selbst, bevor es weitergeht:
- Jede ID der Spec steckt in mindestens einer Aufgabe. Fehlende IDs → zurück an `architect`.
- Jede Aufgabe ist klein genug für einen frischen Kontext (Richtwert: ≤ 5 Dateien, ein klarer Zweck).
- „Nur Tobias“-Aufgaben sind markiert.

**Freigabe nur bei großen Features:** neues Datenmodell/Migration, neuer Dienst oder Container, Änderung an Infrastruktur,
Sicherheit oder Sensor-API → Tobias Architektur und Aufgabenliste kurz zeigen und freigeben lassen. Sonst weiter.

## 2. Build
Pro Aufgabe einen `implementer` mit: Spec-Pfad, Plan-Pfad, Aufgabennummer. Parallel nur Aufgaben, die der Plan als
parallel markiert, jeweils in eigenem Worktree/Branch `feat/F-<NNN>-<aufgabe>`. Auf Pro höchstens 2–3 gleichzeitig.
- Nach jeder Aufgabe: Häkchen und Testnachweis im Plan prüfen (rot → grün dokumentiert). Fehlt der Nachweis, gilt sie nicht als erledigt.
- Meldet ein `implementer`, dass die Spec nicht stimmt: **stoppen**, Tobias fragen, Spec über `requirements` anpassen.
- Branches nach `main` zusammenführen (ohne Push), gesamte Testsuite und Production-Build einmal laufen lassen.

## 3. Unabhängige Prüfung
Einen **frischen** Subagent `reviewer` starten. Er bekommt nur: Spec-Pfad, Basis-Commit vor dem Feature, wie die App startet,
absoluten Pfad zu `vorlagen/review.md` aus dem Verzeichnis dieses Skills.
Nicht: Plan-Notizen, Build-Verlauf, deine Einschätzung. Ergebnis: `docs/reviews/F-<NNN>.md` nach `vorlagen/review.md`.
- Nicht bestanden → Befund mit Reproduktionsweg an einen neuen `implementer`, danach Prüfung nur der betroffenen IDs
  plus Regressionstests. Nach **3 Runden** ohne Erfolg: stoppen und Tobias die Lage schildern.

## 4. Freigabe 2 und Abschluss
Tobias den Bericht kompakt zeigen: Tabelle ID – Ergebnis, nicht prüfbare Punkte mit Grund, Übergaben an ihn.
Nach seinem OK:
1. `CHANGELOG.md` ergänzen (Datum, max. 3 Zeilen „Was – Warum“), Spec/FEATURES.md auf `fertig`.
2. Committen und auf `main` pushen. Der Leitplanken-Hook prüft den CHANGELOG-Eintrag.
3. Deploy nur, wenn das Repo dafür einen dokumentierten Ablauf hat (siehe CLAUDE.md des Repos).

Abschlussbericht an Tobias: CHANGELOG-Zeilen, Prüfergebnis in einer Zeile, offene Punkte und Übergaben.
