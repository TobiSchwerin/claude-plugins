#!/usr/bin/env bash
# Startet brain_hook.py mit dem ersten funktionierenden Python >= 3.8.
# Windows: "python3" ist oft nur ein Store-Platzhalter, deshalb wird jeder Kandidat getestet.
# Ein fehlendes Python darf nie eine Claude-Session blockieren -> immer Exit 0.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for PY in python3 python py; do
  if command -v "$PY" >/dev/null 2>&1 && \
     "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
    exec "$PY" "$DIR/brain_hook.py" "$@"
  fi
done
echo "claude-brain-Hook: kein Python >= 3.8 gefunden, Gedächtnis nicht geladen." >&2
exit 0
