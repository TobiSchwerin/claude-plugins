#!/usr/bin/env bash
# Aufruf: run.sh <skript.py> [argumente]
# Startet das Skript mit dem ersten funktionierenden Python >= 3.8.
# Windows: "python3" ist oft nur ein Store-Platzhalter, deshalb wird jeder Kandidat getestet.
# Ein fehlendes Python darf nie eine Claude-Session blockieren -> immer Exit 0.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKRIPT="$1"; shift
for PY in python3 python py; do
  if command -v "$PY" >/dev/null 2>&1 && \
     "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    exec "$PY" "$DIR/$SKRIPT" "$@"
  fi
done
if [ "$SKRIPT" = "brain_hook.py" ] && [ "$1" = "start" ]; then
  # Landet im Kontext: Claude soll Tobias darauf hinweisen.
  echo "WARNUNG an Tobias weitergeben: Auf diesem Gerät fehlt Python >= 3.8. Das claude-brain wird nicht geladen und die Leitplanken-Hooks sind AUS."
fi
echo "claude-Hooks: kein Python >= 3.8 gefunden ($SKRIPT)." >&2
exit 0
