#!/usr/bin/env python3
"""Leitplanken als PreToolUse-Hook.

Drei Stufen:
    deny  – passiert nie (Secrets anzeigen, Git-Historie überschreiben, rm -rf auf breite Pfade,
            Push auf main ohne CHANGELOG-Eintrag)
    ask   – nur nach Rückfrage bei Tobias (Volumes/Datenbanken löschen, UFW/SSH ändern,
            Repo löschen, ungesicherte Arbeit verwerfen, echte .env überschreiben)
    frei  – alles andere

Ein "ask" erzwingt laut Doku auch im Auto-Modus eine Rückfrage. In unbeaufsichtigten
Läufen (-p) wird daraus eine Ablehnung, die Claude mit Begründung zurückbekommt.

Der Hook ist bewusst fail-open: Ein Fehler hier darf die Arbeit nicht lahmlegen.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------------ Muster

# Secret-Dateien. .env.example/.sample/.template/.test sind ausdrücklich erlaubt.
ERLAUBTE_ENV = r"(?:example|sample|template|dist|test|defaults)"
SECRET_DATEI = re.compile(
    r"""(?ix)
    (?:^|[\s/\\'"=:(<>])            # Grenze davor
    (?:
        \.env(?!\.""" + ERLAUBTE_ENV + r"""\b)(?:\.[\w.-]+)?   # .env, .env.local, .env.production
      | [\w.-]*\.(?:pem|key|p12|pfx|keystore|jks)
      | id_(?:rsa|dsa|ecdsa|ed25519)(?:_[\w-]+)?(?!\.pub)
      | \.ssh[/\\](?!(?:config|known_hosts(?:\.old)?|[^\s'"/\\]+\.pub)(?=$|[\s'"`;|&)<>]))[^\s'"]*
      | \.netrc | \.git-credentials | \.pgpass
      | credentials(?:\.json)?
      | secrets?[/\\][^\s'"]*
    )
    (?=$|[\s'"`;|&)<>])               # Grenze danach
    """
)

# Bash-Befehle, die eine Secret-Datei nur *benutzen*, ohne den Inhalt anzuzeigen.
SECRET_NUTZUNG_OK = re.compile(
    r"""(?x)^\s*(?:
        docker(?:-compose|\s+compose)?\b(?!.*\b(?:exec|run)\b.*\b(?:cat|env|printenv)\b)
      | ls\b | test\s | \[\s | stat\b | chmod\b | chown\b
      | git\s+(?:check-ignore|status|ls-files)\b
      | ssh\b(?!.*\b(?:cat|less|more|head|tail|type|grep|sed|awk|printenv|env)\b)
      | scp\b | ssh-add\b | ssh-keygen\s+-(?:l|y)\b
    )"""
)

DENY_BASH = [
    (re.compile(r"\bgit\b[^;&|]*\bpush\b[^;&|]*(?:\s--force(?!-with-lease)\b|\s-[a-zA-Z]*f\b|\s\+[\w/.-]+)"),
     "Force-Push überschreibt Git-Historie. Erlaubt ist höchstens --force-with-lease auf eigenen Feature-Branches."),
    (re.compile(r"\bgit\b[^;&|]*\b(?:filter-branch|filter-repo)\b"),
     "Umschreiben der kompletten Git-Historie ist gesperrt."),
    (re.compile(r"""(?ix)\b(?:rm\s+(?:-\w*\s+)*-\w*r\w*|Remove-Item\b[^;&|]*-Recurse)[^;&|]*?\s
                    ['"]?(?:/|/\*|~|~/|~/\*|\$HOME|\$HOME/|\$env:USERPROFILE|[A-Z]:\\?|[A-Z]:/|~/docker/?|/home(?:/[^/\s]+)?/?|/etc/?|/var/?|/opt/?|/srv/?)['"]?
                    (?=$|[\s;&|])"""),
     "Rekursives Löschen auf einem breiten Pfad (Root, Home, Laufwerk, ~/docker) ist gesperrt."),
]

ASK_BASH = [
    (re.compile(r"\bdocker\b[^;&|]*\bvolume\s+(?:rm|prune)\b"),
     "Docker-Volume löschen – darin liegen dauerhafte Daten (z. B. Messwerte)."),
    (re.compile(r"\bdocker\b[^;&|]*\b(?:system|volume)\s+prune\b[^;&|]*--volumes\b|\bdocker\b[^;&|]*\bsystem\s+prune\b[^;&|]*\s-\w*a\w*\b[^;&|]*--volumes"),
     "Docker-Prune inklusive Volumes."),
    (re.compile(r"\bdocker(?:-compose|\s+compose)\b[^;&|]*\bdown\b[^;&|]*\s(?:-v\b|--volumes\b)"),
     "compose down mit -v löscht die Volumes des Stacks."),
    (re.compile(r"""(?ix)\b(?:rm|del|erase|Remove-Item|unlink|shred|truncate)\b[^;&|]*\.(?:db|sqlite3?|db-wal|db-shm)\b"""),
     "Datenbankdatei löschen oder leeren."),
    (re.compile(r"\bsqlite3\b[^;&|]*\b(?:DROP|DELETE\s+FROM)\b", re.I),
     "Daten in einer SQLite-Datenbank löschen."),
    (re.compile(r"\bufw\s+(?:--\S+\s+)*(?:allow|deny|reject|limit|delete|insert|route|default|disable|reset|reload|enable)\b"),
     "Firewall-Regeln (UFW) ändern – Fehler können den SSH-Zugang zum Pi sperren."),
    (re.compile(r"sshd_config|/etc/ssh/"),
     "SSH-Server-Konfiguration ändern – Fehler können den Zugang zum Pi sperren."),
    (re.compile(r"\bgh\s+repo\s+delete\b|\bgh\s+api\b[^;&|]*-X\s*DELETE[^;&|]*/repos/[^/\s]+/[^/\s]+/?(?:\s|$)"),
     "GitHub-Repository löschen."),
    (re.compile(r"\bgit\b[^;&|]*\breset\b[^;&|]*--hard\b"),
     "git reset --hard verwirft nicht committete Arbeit unwiderruflich."),
    (re.compile(r"\bgit\b[^;&|]*\bclean\b[^;&|]*\s-\w*[fdx]\w*\b"),
     "git clean löscht ungetrackte Dateien – mit -x auch ignorierte wie .env."),
]

SSH_CONFIG_PFAD = re.compile(r"(?:^|[/\\])(?:sshd_config|sshd_config\.d[/\\].*)$|^/etc/ssh/")
UFW_PFAD = re.compile(r"^/etc/(?:ufw|default/ufw)\b")


# ------------------------------------------------------------------ Entscheidungen

def antwort(entscheidung: str, grund: str) -> int:
    prefix = {"deny": "Leitplanke (gesperrt): ", "ask": "Leitplanke (Rückfrage): "}[entscheidung]
    text = prefix + grund
    if entscheidung == "ask":
        text += " Freigeben nur mit nachvollziehbarer Begründung von Claude."
    else:
        text += " Nicht umgehen; Tobias informieren, falls es wirklich nötig ist."
    ausgabe = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": entscheidung,
        "permissionDecisionReason": text,
    }}
    sys.stdout.write(json.dumps(ausgabe, ensure_ascii=False))
    return 0


def ist_secret_pfad(pfad: str) -> bool:
    if not pfad:
        return False
    return bool(SECRET_DATEI.search(" " + pfad.replace("\\", "/") + " "))


def git(*args: str, cwd: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def changelog_fehlt(befehl: str, cwd: str) -> bool:
    """True, wenn auf main/master gepusht wird und kein ausstehender Commit CHANGELOG.md berührt."""
    if not re.search(r"\bgit\b[^;&|]*\bpush\b", befehl) or not cwd or not Path(cwd).is_dir():
        return False
    m = re.search(r"\bgit\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)", befehl)
    if m:
        cwd = str((Path(cwd) / m.group(1).strip("'\"")).resolve())
    wurzel = git("rev-parse", "--show-toplevel", cwd=cwd)
    if not wurzel or Path(wurzel).name == "claude-brain":
        return False
    zweig = git("rev-parse", "--abbrev-ref", "HEAD", cwd=wurzel)
    ziel_main = re.search(r"\bpush\b[^;&|]*\b(?:main|master)\b", befehl)
    if zweig not in ("main", "master") and not ziel_main:
        return False
    if not git("rev-parse", "--abbrev-ref", "@{u}", cwd=wurzel):
        return False  # erster Push ohne Upstream: nicht blockieren
    ausstehend = git("log", "--format=%H", "@{u}..HEAD", cwd=wurzel)
    if not ausstehend:
        return False
    geaendert = git("diff", "--name-only", "@{u}..HEAD", cwd=wurzel).splitlines()
    return not any(Path(d).name.upper() == "CHANGELOG.MD" for d in geaendert)


def pruefe_bash(befehl: str, cwd: str) -> int:
    for muster, grund in DENY_BASH:
        if muster.search(befehl):
            return antwort("deny", grund)

    # Secrets: nur Anzeigen/Kopieren ist gesperrt, Benutzen (docker compose, ls, chmod) nicht.
    for teil in re.split(r"\s*(?:&&|\|\||;|\n)\s*", befehl):
        if SECRET_DATEI.search(" " + teil + " ") and not SECRET_NUTZUNG_OK.search(teil):
            if re.search(r"(?:>|\btee\b|\bcp\b|\bmv\b|\bCopy-Item\b|\bSet-Content\b|\bOut-File\b)[^|]*" +
                         r"(?:^|[\s/\\'\"])\.env(?!\." + ERLAUBTE_ENV + r"\b)", teil) and \
               not re.search(r"\b(?:cat|type|Get-Content|gc|less|more|head|tail|grep|rg|sed|awk)\b[^|>]*\.env(?!\." + ERLAUBTE_ENV + r"\b)", teil):
                return antwort("ask", "Die echte .env wird überschrieben oder ersetzt – darin stehen Secrets, die nur Tobias kennt.")
            return antwort("deny", "Secret-Dateien (.env, Schlüssel, Zugangsdaten) werden nie angezeigt oder ausgelesen. "
                                   "Nur Variablennamen verwenden (.env.example pflegen); fehlende Werte bei Tobias anfordern.")

    for muster, grund in ASK_BASH:
        if muster.search(befehl):
            return antwort("ask", grund)

    if changelog_fehlt(befehl, cwd):
        return antwort("deny", "Push auf main ohne CHANGELOG.md-Eintrag. Zuerst CHANGELOG.md ergänzen "
                               "(Datum als Überschrift, 1–3 kurze Zeilen 'Was – Warum'), committen, dann pushen.")
    return 0


def pruefe_datei(werkzeug: str, pfad: str) -> int:
    p = pfad.replace("\\", "/")
    if werkzeug in ("Read", "Grep", "NotebookRead") and ist_secret_pfad(p):
        return antwort("deny", f"Secret-Datei '{Path(p).name}' wird nicht gelesen. Nur Variablennamen verwenden; "
                               "fehlende Werte bei Tobias anfordern.")
    if werkzeug in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        if ist_secret_pfad(p) and re.search(r"(?:^|/)\.env", p):
            return antwort("ask", f"'{Path(p).name}' enthält echte Secrets und würde überschrieben.")
        if ist_secret_pfad(p):
            return antwort("deny", f"Schlüssel-/Zugangsdatei '{Path(p).name}' wird nicht verändert.")
        if SSH_CONFIG_PFAD.search(p):
            return antwort("ask", "SSH-Server-Konfiguration ändern – Fehler können den Zugang zum Pi sperren.")
        if UFW_PFAD.search(p):
            return antwort("ask", "Firewall-Konfiguration (UFW) ändern – Fehler können den SSH-Zugang sperren.")
    return 0


def main() -> int:
    try:
        daten = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace") or "{}")
    except (OSError, ValueError):
        return 0
    werkzeug = daten.get("tool_name", "")
    eingabe = daten.get("tool_input") or {}
    cwd = daten.get("cwd", "")
    try:
        if werkzeug in ("Bash", "PowerShell"):
            return pruefe_bash(str(eingabe.get("command", "")), cwd)
        pfad = eingabe.get("file_path") or eingabe.get("notebook_path") or eingabe.get("path") or ""
        return pruefe_datei(werkzeug, str(pfad))
    except Exception as fehler:  # fail-open, aber sichtbar
        print(f"Leitplanken-Hook fehlgeschlagen: {fehler}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
