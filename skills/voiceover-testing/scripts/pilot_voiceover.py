#!/usr/bin/env python3
"""Move the VoiceOver cursor in an owned browser tab and capture what VoiceOver says.

Never starts, stops or configures VoiceOver. Each call needs a session receipt that
quotes the human agreement, checks the frontmost browser and the tab marker, and
appends one JSONL line to the journal, refusals included.
"""
# PDG-LARGE-FILE-JUSTIFICATION: script autonome et sans dépendance, copié tel quel
# dans l'export public ; garde, pilotage, capture et journal forment une seule
# responsabilité, et le formateur du workspace porte ce code au-delà de 200 lignes.

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VO = 'application id "com.apple.VoiceOver"'
GUARD = f'if {VO} is not running then error "VoiceOver is not running"'
TAB_TITLE = {
    "Safari": 'tell application "Safari" to get name of current tab of front window',
    "Google Chrome": 'tell application "Google Chrome" to get title of active tab of front window',
}
BODIES = {
    "next": "tell vo cursor to move right",
    "prev": "tell vo cursor to move left",
    "activate": "tell vo cursor to perform action",
}
WEB_AREA = ["web content", "contenu web"]
# Français relevé en essai réel (macOS 27) ; anglais repris du script de Craig Abbott.
EXIT_MARKERS = ["exit this web area", "sortir de cette zone web"]
MAX_MOVES = 200
MIN_MARKER = 8
RECHECK_EVERY = 10
OK, ERROR, NOT_RUNNING, RECEIPT, TARGET, NOT_FOUND, NOT_FRESH = 0, 1, 3, 4, 5, 6, 7


class Refused(Exception):
    def __init__(self, code, reason):
        super().__init__(reason)
        self.code = code


class RealMac:
    """Real macOS calls; tests replace this object."""

    def voiceover_running(self):
        return (
            subprocess.run(
                ["/usr/bin/pgrep", "-x", "VoiceOver"], capture_output=True, check=False
            ).returncode
            == 0
        )

    def osascript(self, script, timeout=3):
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(
                f"osascript exit {result.returncode}: {result.stderr.strip()}"
            )
        return result.stdout.rstrip("\n")

    def sleep(self, seconds):
        time.sleep(seconds)


def vo_script(body):
    """Bounded VoiceOver call; the guard prevents `tell` from launching VoiceOver."""
    return f"with timeout of 2 seconds\n{GUARD}\ntell {VO} to {body}\nend timeout"


def load_receipt(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refused(RECEIPT, f"reçu illisible : {exc}") from None
    for key in ("accord", "browser", "marker"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise Refused(RECEIPT, f"reçu sans champ « {key} »")
    if data["browser"] not in TAB_TITLE:
        raise Refused(RECEIPT, f"navigateur non pris en charge : {data['browser']}")
    if len(data["marker"].strip()) < MIN_MARKER:
        raise Refused(RECEIPT, f"marqueur de moins de {MIN_MARKER} caractères")
    return data


def check_target(mac, receipt):
    if not mac.voiceover_running():
        raise Refused(NOT_RUNNING, "VoiceOver non lancé : ce script ne le démarre pas")
    app = Path(
        mac.osascript("POSIX path of (path to frontmost application)").rstrip("/")
    ).stem
    if app != receipt["browser"]:
        raise Refused(
            TARGET, f"application au premier plan : {app}, attendu {receipt['browser']}"
        )
    title = mac.osascript(TAB_TITLE[receipt["browser"]])
    if receipt["marker"] not in title:
        raise Refused(TARGET, f"onglet sans le marqueur du reçu : {title}")
    return app, title


def last_phrase(mac):
    return mac.osascript(vo_script("get content of last phrase")).replace("\n", " ")


def act(mac, body):
    """Run one VoiceOver command, then join the fresh fragments it announces."""
    before = last_phrase(mac)
    mac.osascript(vo_script(body))
    fragments, previous, quiet = [], None, 0
    for _ in range(12):
        mac.sleep(0.1)
        phrase = last_phrase(mac)
        if phrase and phrase != previous and (fragments or phrase != before):
            fragments.append(phrase)
            previous, quiet = phrase, 0
        elif fragments:
            quiet += 1
            if quiet >= 4:
                break
    return fragments


def enter_web_content(mac, receipt):
    markers = [m.lower() for m in receipt.get("web_area_markers", WEB_AREA)]
    mac.osascript(vo_script("tell vo cursor to move to first item"))
    for _ in range(12):
        mac.sleep(0.3)
        if any(m in last_phrase(mac).lower() for m in markers):
            return act(mac, "tell vo cursor to move into item")
        mac.osascript(vo_script("tell vo cursor to move right"))
    return act(mac, "tell vo cursor to move to first item")


def phrase_has(phrase, name, others):
    low = phrase.lower()
    if not low or any(o.lower() not in low for o in others):
        return False
    return re.search(r"(?<!\w)" + re.escape(name.lower()) + r"(?!\w)", low) is not None


def find(mac, receipt, name, others, max_moves):
    exits = [m.lower() for m in receipt.get("exit_markers", EXIT_MARKERS)]
    announcement, empties = ", ".join(enter_web_content(mac, receipt)), 0
    for move in range(max_moves):
        if move and move % RECHECK_EVERY == 0:
            check_target(mac, receipt)
        if phrase_has(announcement, name, others):
            return announcement, True
        if any(m in announcement.lower() for m in exits):
            break
        empties = empties + 1 if not announcement else 0
        if empties >= 2:
            break
        announcement = ", ".join(act(mac, "tell vo cursor to move right"))
    return announcement, phrase_has(announcement, name, others)


def append_journal(path, row):
    row["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as journal:
        journal.write(json.dumps(row, ensure_ascii=False) + "\n")


def last_entry(path):
    """Return the last journal line's message and exit code; no journal is an error."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if not lines:
        return "", ERROR
    row = json.loads(lines[-1])
    message = row.get("announcement") or row.get("refused") or row.get("error") or ""
    return message, row.get("exit_code", ERROR)


def run(args, mac):
    row = {"command": args.command, "words": args.words, "receipt": str(args.receipt)}
    try:
        row["receipt_sha256"] = hashlib.sha256(args.receipt.read_bytes()).hexdigest()
    except OSError:
        row["receipt_sha256"] = None
    try:
        receipt = load_receipt(args.receipt)
        row["browser"], row["tab"] = check_target(mac, receipt)
        if args.command == "find":
            row["announcement"], found = find(
                mac, receipt, args.words[0], args.words[1:], args.max
            )
            code = OK if found else NOT_FOUND
        else:
            fragments = (
                enter_web_content(mac, receipt)
                if args.command == "first"
                else act(mac, BODIES[args.command])
            )
            row["fragments"], row["announcement"] = fragments, ", ".join(fragments)
            code = OK if fragments else NOT_FRESH
        row["fresh"] = bool(row["announcement"])
    except Refused as exc:
        code, row["refused"] = exc.code, str(exc)
    except (subprocess.TimeoutExpired, RuntimeError, OSError) as exc:
        code, row["error"] = ERROR, str(exc)
    row["exit_code"] = code
    append_journal(args.journal, row)
    message = row.get("announcement") or row.get("refused") or row.get("error") or ""
    print(message, file=sys.stdout if code == OK else sys.stderr)
    return code


def main(argv=None, mac=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--receipt", required=True, type=Path, help="Session receipt (JSON)"
    )
    parser.add_argument(
        "--journal", required=True, type=Path, help="Private JSONL journal"
    )
    parser.add_argument("--max", type=int, default=80, help="Maximum moves for find")
    parser.add_argument(
        "command", choices=["first", "next", "prev", "activate", "find", "last"]
    )
    parser.add_argument(
        "words", nargs="*", help="find: name, then other required words"
    )
    args = parser.parse_args(argv)
    if not 1 <= args.max <= MAX_MOVES:
        parser.error(f"--max must be between 1 and {MAX_MOVES}")
    if args.command == "find" and not args.words:
        parser.error("find needs a name")
    if not args.journal.parent.is_dir():
        parser.error("--journal must be in an existing directory")
    if args.command == "last":
        message, code = last_entry(args.journal)
        print(message, file=sys.stdout if code == OK else sys.stderr)
        return code
    return run(args, mac or RealMac())


if __name__ == "__main__":
    sys.exit(main())
