---
feature: F-012
geprüft_gegen: <commit vor dem Feature>..<commit geprüft>
runde: 1
---

# Prüfbericht F-012

| ID | Ergebnis | Nachweis |
|---|---|---|
| F-012.A1 | bestanden | Test `f012_a1_…` (war ohne Fix rot), manuell: `curl …` → 401 |
| F-012.A2 | nicht bestanden | Reproduktion: 1. … 2. … erwartet … tatsächlich … |
| F-012.A3 | nicht prüfbar | Grund: braucht echten Sensor |

## Sicherheit
Kann Nutzer A Daten von Nutzer B sehen? Ungeschützte Endpunkte? Secrets in Code/Logs? – Befund oder „keine Befunde“.

## Regression
Gesamte Testsuite: X bestanden, Y fehlgeschlagen. Production-Build: ok/fehlgeschlagen.

## Zusammenfassung
Eine Zeile: freigabefähig ja/nein, was fehlt.
