---
name: projekt-onboarding
description: Bringt ein bestehendes Repo in die Arbeitsstruktur – CLAUDE.md, docs/ mit PROJEKT.md, FEATURES.md (aus dem Code abgeleitet), Specs für Bestandsfeatures, CHANGELOG.md, Detailnotizen aus claude-brain/_migration übernehmen. Verwenden beim ersten Arbeiten in einem Repo ohne docs/ oder wenn Tobias ein Projekt „einrichten“ will.
---

# Projekt-Onboarding (bestehendes Repo)

Ziel: Jede spätere Session versteht das Projekt aus dem Repo heraus, ohne Chatverlauf.
Den vorhandenen Stack respektieren – nichts umbauen, nur dokumentieren. Kein Produktivcode in diesem Skill.

## 1. Bestand erfassen (ohne Tobias zu fragen)
1. Code, Build-Dateien, Dockerfiles, CI, vorhandene Doku und lose Berichte im Repo lesen (z. B. nicht committete `*.md`).
2. Projektkarte und `_migration/<repo>-details.md` im claude-brain lesen.
3. Prüfen, wie gebaut, getestet und gestartet wird – Befehle **ausführen**, nicht raten. Notieren, was fehlschlägt.

## 2. Vorschlag an Tobias (eine Nachricht)
- Zweck und Abgrenzung des Projekts in 3 Zeilen
- Liste der erkannten Features (Kurzname, eine Zeile, vermuteter Status)
- Auffälligkeiten: offene Sicherheitsbefunde, veraltete Skripte, fehlende Tests, Widersprüche zwischen Doku und Code
- Höchstens 3 Fragen zu dem, was sich aus dem Code nicht ableiten lässt
Auf Bestätigung oder Korrektur warten.

## 3. Struktur anlegen
| Datei | Inhalt |
|---|---|
| `CLAUDE.md` | Stack, Befehle (build/test/run/deploy), Ordnerstruktur, Konventionen, Was nie passieren darf. **Max. 150 Zeilen**, nur Zustand |
| `docs/PROJEKT.md` | nach `../requirements/vorlagen/projekt.md` |
| `docs/FEATURES.md` | nach `../requirements/vorlagen/features.md`, bestehende Features als `fertig` ab `F-001` |
| `docs/specs/` | Specs nur für Features mit wichtigem oder sicherheitsrelevantem Verhalten, Kriterien aus dem Code abgeleitet und als `fertig` markiert. Bekannte offene Befunde als neues Feature mit Status `idee` |
| `docs/decisions/` | Entscheidungen aus der Detailnotiz (je Datei: Kontext, Entscheidung, Gründe, verworfen) |
| `docs/betrieb.md` | Deploy, Container, Umgebungsvariablen (nur Namen), Pi-Pfade – aus der Detailnotiz |
| `CHANGELOG.md` | Leer mit Überschrift, falls nicht vorhanden |
| `.env.example` | Alle Variablennamen mit Platzhaltern, falls nicht vorhanden |

Nicht committete Berichte (z. B. Sicherheitsberichte) nicht ungefragt committen – Tobias fragen, ob sie nach `docs/` sollen.

## 4. Abschluss
1. Committen (`docs: Projekt-Onboarding`), CHANGELOG-Zeile „Projekt-Doku angelegt – Grundlage für den Feature-Workflow“, pushen.
2. Im claude-brain: Projektkarte auf Zweck/Repo/Status/Infra kürzen und auf `docs/` verweisen,
   `_migration/<repo>-details.md` löschen. Der Brain-Hook synchronisiert.
3. Bericht an Tobias: angelegte Dateien, erkannte Features, offene Befunde mit Vorschlag für die nächste Spec.
