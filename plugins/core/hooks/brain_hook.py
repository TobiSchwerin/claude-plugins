#!/usr/bin/env python3
"""Hooks für das claude-brain (zentrales Gedächtnis als Git-Repo).

    start  SessionStart: brain pullen, Index + Projektkarte in den Kontext geben
    stop   Stop:         Brain-Änderungen sofort synchronisieren (Index bauen, commit, push);
                         nach einem neuen Commit im Arbeits-Repo einmal die Pflege anstoßen
    end    SessionEnd:   letzte Brain-Änderungen synchronisieren

Pfad des Brain (in dieser Reihenfolge):
    1. Umgebungsvariable CLAUDE_BRAIN_DIR
    2. "env": {"CLAUDE_BRAIN_DIR": ...} in ~/.claude/settings.json
    3. ~/claude-brain

Grundsatz: Ein Fehler im Hook darf nie die Claude-Session blockieren. Alles wird
abgefangen; Probleme erscheinen als Hinweis im Kontext bzw. auf stderr.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

GIT_TIMEOUT = 20


# ---------------------------------------------------------------- Hilfsfunktionen

def brain_dir() -> Path:
    wert = os.environ.get("CLAUDE_BRAIN_DIR", "").strip()
    if not wert:
        try:
            settings = json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8"))
            wert = str(settings.get("env", {}).get("CLAUDE_BRAIN_DIR", "")).strip()
        except (OSError, ValueError):
            wert = ""
    return Path(wert).expanduser() if wert else Path.home() / "claude-brain"


def git(*args: str, cwd: Path, timeout: int = GIT_TIMEOUT) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as fehler:
        return subprocess.CompletedProcess(args, 1, "", str(fehler))


def repo_wurzel(pfad: str | None) -> Path | None:
    if not pfad or not Path(pfad).is_dir():
        return None
    r = git("rev-parse", "--show-toplevel", cwd=Path(pfad))
    return Path(r.stdout.strip()).resolve() if r.returncode == 0 and r.stdout.strip() else None


def head(repo: Path) -> str:
    r = git("rev-parse", "HEAD", cwd=repo)
    return r.stdout.strip() if r.returncode == 0 else ""


def zustand_datei(brain: Path, session_id: str) -> Path:
    ordner = brain / ".git" / "claude-hooks"
    ordner.mkdir(parents=True, exist_ok=True)
    sicher = "".join(c for c in session_id if c.isalnum() or c in "-_") or "unbekannt"
    return ordner / f"{sicher}.json"


def zustand_lesen(datei: Path) -> dict:
    try:
        return json.loads(datei.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def zustand_schreiben(datei: Path, daten: dict) -> None:
    try:
        datei.write_text(json.dumps(daten), encoding="utf-8")
    except OSError:
        pass


def ist_brain(brain: Path) -> bool:
    return (brain / ".git").exists() and (brain / "CLAUDE.md").is_file()


def ausgabe(text: str) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    sys.stdout.write(text)


# ---------------------------------------------------------------- Synchronisation

def synchronisieren(brain: Path, anlass: str) -> str | None:
    """Index bauen, committen, pullen, pushen. Gibt eine Fehlermeldung zurück oder None."""
    if not git("status", "--porcelain", cwd=brain).stdout.strip():
        return push_ausstehend(brain)

    skript = brain / "tools" / "build-index.py"
    if skript.is_file():
        try:
            r = subprocess.run([sys.executable, str(skript)], cwd=str(brain), capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=60)
        except (OSError, subprocess.TimeoutExpired) as fehler:
            return f"Index-Build nicht ausführbar: {fehler}"
        if r.returncode == 2:
            return "INDEX:" + (r.stderr.strip() or r.stdout.strip())

    git("add", "-A", cwd=brain)
    nachricht = f"brain: {anlass} ({socket.gethostname()})"
    r = git("commit", "-q", "-m", nachricht, cwd=brain)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        return f"Commit fehlgeschlagen: {(r.stderr or r.stdout).strip()}"
    return push_ausstehend(brain)


def push_ausstehend(brain: Path) -> str | None:
    if not git("remote", cwd=brain).stdout.strip():
        return None
    r = git("pull", "--rebase", "--autostash", "-q", cwd=brain, timeout=40)
    if r.returncode != 0:
        git("rebase", "--abort", cwd=brain)
        return f"Pull fehlgeschlagen (lokale Commits bleiben erhalten): {r.stderr.strip()[:300]}"
    erste_zeile = (git("status", "-sb", cwd=brain).stdout.splitlines() or [""])[0]
    if "ahead" in erste_zeile:
        r = git("push", "-q", cwd=brain, timeout=40)
        if r.returncode != 0:
            return f"Push fehlgeschlagen: {r.stderr.strip()[:300]}"
    return None


# ---------------------------------------------------------------- Ereignisse

def bei_start(daten: dict, brain: Path) -> int:
    if not ist_brain(brain):
        ausgabe(
            "## claude-brain nicht gefunden\n"
            f"Erwartet unter `{brain}`. Einrichten: `git clone git@github.com:TobiSchwerin/claude-brain.git` "
            "und den Pfad als `CLAUDE_BRAIN_DIR` im `env`-Block von `~/.claude/settings.json` eintragen.\n"
        )
        return 0

    hinweise: list[str] = []
    if git("remote", cwd=brain).stdout.strip():
        fehler = push_ausstehend(brain)
        if fehler:
            hinweise.append(fehler)

    repo = repo_wurzel(daten.get("cwd"))
    zustand_schreiben(zustand_datei(brain, daten.get("session_id", "")), {
        "repo": str(repo) if repo else "",
        "start_head": head(repo) if repo else "",
        "erinnert_bei": "",
    })

    teile = [
        "## claude-brain – zentrales Gedächtnis von Tobias",
        f"Pfad: `{brain}`. Regeln, Arbeitsregeln und Projektkarte folgen in eigenen Abschnitten.",
        "Notizen bei Bedarf über die Links im Index lesen. Änderungen am Brain werden nach jeder Antwort "
        "automatisch indiziert, committet und gepusht – nicht selbst committen.",
        "",
    ]
    index = brain / "index.md"
    if index.is_file():
        teile.append(index.read_text(encoding="utf-8"))
    if hinweise:
        teile += ["", "## Warnungen claude-brain"] + [f"- {h}" for h in hinweise]
    ausgabe(begrenzen("\n".join(teile) + "\n", brain / "index.md"))
    return 0


def bei_start_regeln(daten: dict, brain: Path) -> int:
    """Weiterer SessionStart-Hook: Regeln des Brain. Jeder Hook hat seine eigene 10.000-Zeichen-Grenze.

    Läuft parallel zum ersten Hook, deshalb hier kein git pull (Regeln ändern sich selten).
    """
    if not ist_brain(brain):
        return 0
    teile: list[str] = []
    regeln = brain / "CLAUDE.md"
    if regeln.is_file():
        teile += ["## Regeln des claude-brain (CLAUDE.md, verbindlich für jede Änderung am Brain)",
                  regeln.read_text(encoding="utf-8")]
    ausgabe(begrenzen("\n".join(teile) + "\n", regeln))
    return 0


def bei_start_arbeitsregeln(daten: dict, brain: Path) -> int:
    """Arbeitsregeln von Tobias – gelten in jeder Session, nicht nur bei Brain-Änderungen."""
    datei = brain / "user" / "arbeitsregeln.md"
    if ist_brain(brain) and datei.is_file():
        ausgabe(begrenzen("## Arbeitsregeln von Tobias (verbindlich in jeder Session)\n"
                          + datei.read_text(encoding="utf-8") + "\n", datei))
    return 0


def bei_start_projekt(daten: dict, brain: Path) -> int:
    """Projektkarte des aktuellen Repos."""
    if not ist_brain(brain):
        return 0
    teile: list[str] = []
    repo = repo_wurzel(daten.get("cwd"))
    if repo and repo != brain.resolve():
        karte = brain / "projects" / f"{repo.name}.md"
        if karte.is_file():
            teile += ["", f"## Projektkarte für das aktuelle Repo `{repo.name}`", karte.read_text(encoding="utf-8")]
        else:
            teile += ["", f"Hinweis: Für das aktuelle Repo `{repo.name}` gibt es noch keine Projektkarte "
                          f"(`projects/{repo.name}.md`). Bei Gelegenheit anlegen."]
    if teile:
        ausgabe(begrenzen("\n".join(teile) + "\n", brain / "projects"))
    return 0


GRENZE = 9500  # Claude Code lagert Hook-Ausgaben ab 10.000 Zeichen in eine Datei aus


def begrenzen(text: str, quelle: Path) -> str:
    """Hält die Ausgabe unter der Grenze und sagt es laut, statt still Inhalt zu verlieren."""
    if len(text) <= GRENZE:
        return text
    hinweis = (f"\n\n[GEKÜRZT: Ausgabe hat {len(text)} Zeichen, Grenze {GRENZE}. Vollständig in `{quelle}` lesen. "
               "Tobias darauf hinweisen: Beschreibungen kürzen oder Notizen zusammenfassen.]\n")
    return text[:GRENZE - len(hinweis)] + hinweis


def bei_stop(daten: dict, brain: Path) -> int:
    if not ist_brain(brain) or daten.get("stop_hook_active"):
        return 0

    datei = zustand_datei(brain, daten.get("session_id", ""))
    zustand = zustand_lesen(datei)
    repo_name = Path(zustand["repo"]).name if zustand.get("repo") else "ohne Repo"

    # 1) Brain wurde geändert -> sofort synchronisieren
    fehler = synchronisieren(brain, f"Aktualisierung aus {repo_name}")
    if fehler and fehler.startswith("INDEX:"):
        ausgabe(json.dumps({
            "decision": "block",
            "reason": "Der Index des claude-brain konnte nicht gebaut werden, Änderungen sind NICHT gespeichert. "
                      "Korrigiere die Frontmatter laut CLAUDE.md:\n" + fehler[6:],
        }, ensure_ascii=False))
        return 0
    if fehler:
        print(f"claude-brain: {fehler}", file=sys.stderr)

    # 2) Neuer Commit im Arbeits-Repo -> einmal Pflege anstoßen
    repo = Path(zustand["repo"]) if zustand.get("repo") else None
    if not repo or not repo.is_dir() or repo.resolve() == brain.resolve():
        return 0
    jetzt = head(repo)
    if not jetzt or jetzt == zustand.get("start_head") or jetzt == zustand.get("erinnert_bei"):
        return 0

    zustand["erinnert_bei"] = jetzt
    zustand_schreiben(datei, zustand)
    ausgabe(json.dumps({
        "decision": "block",
        "reason": (
            f"Im Repo `{repo.name}` gibt es neue Commits. Prüfe jetzt kurz das claude-brain "
            f"(`{brain}`) nach CLAUDE.md, Abschnitt 'Abschluss eines Arbeitsblocks':\n"
            "1. Haben sich Fakten geändert (Stack, Ports, Container, Status, Infrastruktur)? An ihrer einen Stelle korrigieren, `updated` setzen.\n"
            f"2. Stimmen Status und nächste Schritte in `projects/{repo.name}.md`? Fehlt die Karte, anlegen.\n"
            "3. Neue projektübergreifende Erkenntnis -> `knowledge/`, neue Idee -> `ideas/`.\n"
            "Nur den Zustand beschreiben, kein Tagebuch. Nicht selbst committen, das macht der Hook. "
            "Ist nichts zu ändern, antworte nur mit: 'Brain: nichts zu aktualisieren.'"
        ),
    }, ensure_ascii=False))
    return 0


def bei_ende(daten: dict, brain: Path) -> int:
    if not ist_brain(brain):
        return 0
    fehler = synchronisieren(brain, "Sitzungsende")
    if fehler:
        print(f"claude-brain: {fehler}", file=sys.stderr)
    try:
        zustand_datei(brain, daten.get("session_id", "")).unlink()
    except OSError:
        pass
    return 0


def main() -> int:
    ereignis = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        roh = sys.stdin.buffer.read().decode("utf-8", errors="replace") if not sys.stdin.isatty() else ""
        daten = json.loads(roh) if roh.strip() else {}
    except (OSError, ValueError):
        daten = {}
    brain = brain_dir()
    try:
        return {"start": bei_start, "start-regeln": bei_start_regeln, "start-arbeitsregeln": bei_start_arbeitsregeln,
                "start-projekt": bei_start_projekt, "stop": bei_stop, "end": bei_ende}.get(ereignis, lambda d, b: 0)(daten, brain)
    except Exception as fehler:  # niemals die Session blockieren
        print(f"claude-brain-Hook ({ereignis}) fehlgeschlagen: {fehler}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
