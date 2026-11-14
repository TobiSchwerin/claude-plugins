---
feature: F-012
spec: ../specs/F-012-lese-api-auth.md
---

# Plan F-012

## Architektur
- **Betroffene Teile:** (Oberfläche, Server, Daten, Firmware …) und wie sie zusammenhängen
- **Datenmodell:** neue/geänderte Tabellen und Felder, wer darf was lesen/ändern
- **Verhalten:** Zustände, Abläufe, Fehlerfälle
- **Ist-Zustand genutzt:** bestehende Module/Tabellen/Libraries, die wiederverwendet werden (nichts doppelt erfinden)
- **Entscheidungen:** Entscheidung – Alternative – warum verworfen (große Entscheidungen zusätzlich in `docs/decisions/`)

## Aufgaben
Status: `[ ]` offen · `[x]` erledigt (nur mit Testnachweis) · `[!]` blockiert

- [ ] **1. Kurzbeschreibung** – erfüllt: F-012.A1, F-012.A2 – Dateien: `src/…` – parallel zu: 2
  - Test: `cargo test f012_a1` · rot: (Fehlermeldung) · grün: (Ergebnis)
- [ ] **2. …** – erfüllt: F-012.A5 – parallel zu: 1
- [ ] **3. NUR TOBIAS:** Variable `X` in `.env` auf dem Pi eintragen (Wert: …)

## Abdeckung
| ID | Aufgaben |
|---|---|
| F-012.A1 | 1 |
| F-012.A5 | 2 |

## Haltepunkte
Nach Aufgabe 2: Tests grün, kann so stehen bleiben.
