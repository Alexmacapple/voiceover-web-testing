#!/usr/bin/env python3
"""Move the VoiceOver cursor in an owned browser tab and capture what VoiceOver says.

Never starts, stops or configures VoiceOver. Each call needs a session receipt that
quotes the human agreement and appends one JSONL line to the journal, refusals
included. The frontmost tab is checked by title and URL before every gesture, and
`activate` only follows a `find` that proved the named element unique.
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
# One "title<TAB>URL" line for the front tab, then one per open tab.
TAB_STATE = """tell application "{app}"
set sep to character id 9
set out to ({title} of {front} of front window) & sep & (URL of {front} of front window)
repeat with w in windows
repeat with t in tabs of w
try
set u to (URL of t) as text
on error
set u to ""
end try
set out to out & linefeed & ({title} of t) & sep & u
end repeat
end repeat
return out
end tell"""
TAB_TERMS = {
    "Safari": {"title": "name", "front": "current tab"},
    "Google Chrome": {"title": "title", "front": "active tab"},
}
# Window titles of the frontmost document application: front window, then each window.
WINDOW_STATE = """tell application "System Events" to tell process "{app}"
set out to name of window 1
repeat with w in windows
set out to out & linefeed & (name of w)
end repeat
return out
end tell"""
# Content markers: Preview observed in a real run (macOS 26.5, French). Word and
# PowerPoint were only surveyed in French (references/documents.md), so their
# receipt must declare web_area_markers.
DOCUMENT_APPS = {
    "Preview": ["document groupe", "document group"],
    "Microsoft Word": None,
    "Microsoft PowerPoint": None,
}
BODIES = {
    "next": "tell vo cursor to move right",
    "prev": "tell vo cursor to move left",
    "into": "tell vo cursor to move into item",
    "out": "tell vo cursor to move out of item",
    "activate": "tell vo cursor to perform action",
}
WEB_AREA = ["web content", "contenu web"]
# Français relevé en essai réel (macOS 27) ; anglais repris du script de Craig Abbott.
EXIT_MARKERS = ["exit this web area", "sortir de cette zone web"]
MAX_MOVES = 200
MIN_MARKER = 8
OK, ERROR, NOT_RUNNING, RECEIPT, TARGET, NOT_FOUND, NOT_FRESH, ELEMENT = (
    0,
    1,
    3,
    4,
    5,
    6,
    7,
    8,
)
BY_HAND_TAB = (
    " Aucun geste envoyé. Laissez l’onglet de test seul ouvert et au premier plan"
    " avant de relancer, ou poursuivez à la main."
)
BY_HAND_ELEMENT = (
    " Aucune activation envoyée. Placez-vous sur l’élément voulu et activez-le"
    " vous-même (VO-Espace) ; l’observation reprend ensuite avec next ou prev."
)


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
    if ("app" in data) == ("browser" in data):
        raise Refused(RECEIPT, "reçu : indiquer soit « browser », soit « app »")
    document = "app" in data
    keys = (
        ("accord", "app", "marker")
        if document
        else ("accord", "browser", "marker", "url_marker")
    )
    for key in keys:
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise Refused(RECEIPT, f"reçu sans champ « {key} »")
    if document and data["app"] not in DOCUMENT_APPS:
        raise Refused(RECEIPT, f"application non prise en charge : {data['app']}")
    if not document and data["browser"] not in TAB_TERMS:
        raise Refused(RECEIPT, f"navigateur non pris en charge : {data['browser']}")
    if (
        document
        and DOCUMENT_APPS[data["app"]] is None
        and not data.get("web_area_markers")
    ):
        raise Refused(
            RECEIPT,
            f"{data['app']} : repères de contenu non observés, déclarer « web_area_markers »",
        )
    for key in keys[2:]:
        if len(data[key].strip()) < MIN_MARKER:
            raise Refused(RECEIPT, f"« {key} » de moins de {MIN_MARKER} caractères")
    return data


def check_target(mac, receipt):
    if not mac.voiceover_running():
        raise Refused(NOT_RUNNING, "VoiceOver non lancé : ce script ne le démarre pas")
    app = Path(
        mac.osascript("POSIX path of (path to frontmost application)").rstrip("/")
    ).stem
    expected = receipt.get("app") or receipt["browser"]
    if app != expected:
        raise Refused(
            TARGET,
            f"application au premier plan : {app}, attendu {expected}." + BY_HAND_TAB,
        )
    if "app" in receipt:
        return check_window(mac, receipt, app)
    state = mac.osascript(TAB_STATE.format(app=app, **TAB_TERMS[app]))
    tabs = [line.split("\t") for line in state.split("\n")]
    if len(tabs) < 2 or any(len(tab) != 2 for tab in tabs):
        raise Refused(TARGET, "état des onglets illisible." + BY_HAND_TAB)

    def owned(tab):
        return receipt["marker"] in tab[0] and receipt["url_marker"] in tab[1]

    if not owned(tabs[0]):
        raise Refused(
            TARGET,
            f"onglet au premier plan sans le titre et l’adresse du reçu : {tabs[0][0]}."
            + BY_HAND_TAB,
        )
    twins = sum(owned(tab) for tab in tabs[1:])
    if twins != 1:
        raise Refused(
            TARGET,
            f"{twins} onglets portent le titre et l’adresse du reçu : cible ambiguë."
            + BY_HAND_TAB,
        )
    return {"browser": app, "tab": tabs[0][0], "url": tabs[0][1]}


def check_window(mac, receipt, app):
    """Document target: the front window, and only it, carries the receipt marker."""
    names = mac.osascript(WINDOW_STATE.format(app=app)).split("\n")
    if len(names) < 2 or not names[0]:
        raise Refused(TARGET, "fenêtres illisibles." + BY_HAND_TAB)
    if receipt["marker"] not in names[0]:
        raise Refused(
            TARGET,
            f"fenêtre au premier plan sans le marqueur du reçu : {names[0]}."
            + BY_HAND_TAB,
        )
    twins = sum(receipt["marker"] in name for name in names[1:])
    if twins != 1:
        raise Refused(
            TARGET,
            f"{twins} fenêtres portent le marqueur du reçu : cible ambiguë."
            + BY_HAND_TAB,
        )
    return {"app": app, "window": names[0]}


def gesture(mac, receipt, body):
    """Send one VoiceOver command, only after confirming the owned tab again."""
    check_target(mac, receipt)
    mac.osascript(vo_script(body))


def cursor_text(mac, cursor):
    """Text under the VoiceOver or keyboard cursor; None when it cannot be read."""
    try:
        text = mac.osascript(vo_script(f"get text under cursor of {cursor}"))
    except (subprocess.TimeoutExpired, RuntimeError, OSError):
        return None
    return text.replace("\n", " ")


def last_phrase(mac):
    return mac.osascript(vo_script("get content of last phrase")).replace("\n", " ")


def act(mac, receipt, body):
    """Run one VoiceOver command, then join the fresh fragments it announces."""
    before = last_phrase(mac)
    gesture(mac, receipt, body)
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
    default = DOCUMENT_APPS[receipt["app"]] if "app" in receipt else WEB_AREA
    markers = [m.lower() for m in receipt.get("web_area_markers") or default]
    gesture(mac, receipt, "tell vo cursor to move to first item")
    for _ in range(12):
        mac.sleep(0.3)
        if any(m in last_phrase(mac).lower() for m in markers):
            return act(mac, receipt, "tell vo cursor to move into item")
        gesture(mac, receipt, "tell vo cursor to move right")
    return act(mac, receipt, "tell vo cursor to move to first item")


def phrase_has(phrase, name, others):
    low = phrase.lower()
    if not low or any(o.lower() not in low for o in others):
        return False
    return re.search(r"(?<!\w)" + re.escape(name.lower()) + r"(?!\w)", low) is not None


def find(mac, receipt, name, others, max_moves):
    """Walk the whole web area, then return to the named element if it is unique.

    Returns the announcement, the number of matching elements and whether the
    cursor now sits on the only one. Uniqueness needs the end of the web area and
    a fresh announcement at every step: two neighbours announced alike are captured
    as silence, which could hide a twin.
    """
    # A document has no observed end marker: uniqueness stays unproven unless declared.
    default = [] if "app" in receipt else EXIT_MARKERS
    exits = [m.lower() for m in receipt.get("exit_markers", default)]
    move_right = "tell vo cursor to move right"
    announcement, empties = ", ".join(enter_web_content(mac, receipt)), 0
    hits, complete, blind, first_hit = [], False, False, ""
    for move in range(max_moves + 1):
        if phrase_has(announcement, name, others):
            hits.append(move)
            first_hit = first_hit or announcement
        complete = any(m in announcement.lower() for m in exits)
        empties = empties + 1 if not announcement else 0
        blind = blind or not announcement
        if complete or empties >= 2 or move == max_moves:
            break
        announcement = ", ".join(act(mac, receipt, move_right))
    if len(hits) != 1 or not complete or blind:
        return first_hit or announcement, len(hits), False
    announcement = ", ".join(enter_web_content(mac, receipt))
    for _ in range(hits[0]):
        announcement = ", ".join(act(mac, receipt, move_right))
    under = cursor_text(mac, "vo cursor") or ""
    back = phrase_has(announcement, name, others) and phrase_has(under, name, [])
    return announcement, 1, back


def check_element(mac, row, args):
    """Refuse to activate unless the last journal line proves this element unique."""
    lines = (
        args.journal.read_text(encoding="utf-8").splitlines()
        if args.journal.exists()
        else []
    )
    proof = json.loads(lines[-1]) if lines else {}
    same = all(
        proof.get(k) == row.get(k)
        for k in ("receipt_sha256", "tab", "url", "app", "window")
    )
    if not (
        proof.get("command") == "find"
        and proof.get("unique") is True
        and proof.get("words") == args.words
        and same
    ):
        raise Refused(
            ELEMENT,
            "élément visé non confirmé : la dernière ligne du journal n’est pas un"
            " find réussi sur ces mêmes mots, dans ce même onglet." + BY_HAND_ELEMENT,
        )
    row["vo_cursor_before"] = cursor_text(mac, "vo cursor")
    if not phrase_has(row["vo_cursor_before"] or "", args.words[0], []):
        raise Refused(
            ELEMENT,
            f"élément visé non confirmé : le curseur VoiceOver est sur"
            f" « {row['vo_cursor_before']} »." + BY_HAND_ELEMENT,
        )


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
    message = row.get("refused") or row.get("announcement") or row.get("error") or ""
    return message, row.get("exit_code", ERROR)


def run(args, mac):
    row = {"command": args.command, "words": args.words, "receipt": str(args.receipt)}
    try:
        row["receipt_sha256"] = hashlib.sha256(args.receipt.read_bytes()).hexdigest()
    except OSError:
        row["receipt_sha256"] = None
    try:
        receipt = load_receipt(args.receipt)
        row.update(check_target(mac, receipt))
        if args.command == "find":
            if "app" in receipt and not receipt.get("exit_markers"):
                raise Refused(
                    ELEMENT,
                    "find dans un document : le parcours part de la page affichée et"
                    " la fin du document est un silence, donc ni absence ni unicité"
                    " ne sont prouvables sans « exit_markers »." + BY_HAND_ELEMENT,
                )
            row["announcement"], row["matches"], row["unique"] = find(
                mac, receipt, args.words[0], args.words[1:], args.max
            )
            code = OK if row["unique"] else NOT_FOUND
            if row["matches"] and not row["unique"]:
                raise Refused(
                    ELEMENT,
                    f"élément visé incertain : {row['matches']} élément(s) répondent"
                    f" à « {args.words[0]} », unicité ou retour non prouvés."
                    + BY_HAND_ELEMENT,
                )
        else:
            if args.command == "activate":
                check_element(mac, row, args)
            fragments = (
                enter_web_content(mac, receipt)
                if args.command == "first"
                else act(mac, receipt, BODIES[args.command])
            )
            row["fragments"], row["announcement"] = fragments, ", ".join(fragments)
            code = OK if fragments else NOT_FRESH
        row["fresh"] = bool(row["announcement"])
        row["vo_cursor"] = cursor_text(mac, "vo cursor")
        row["keyboard_cursor"] = cursor_text(mac, "keyboard cursor")
    except Refused as exc:
        code, row["refused"] = exc.code, str(exc)
    except (subprocess.TimeoutExpired, RuntimeError, OSError) as exc:
        code, row["error"] = ERROR, str(exc)
    row["exit_code"] = code
    append_journal(args.journal, row)
    message = row.get("refused") or row.get("announcement") or row.get("error") or ""
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
        "command", choices=["first", "next", "prev", "into", "out", "activate", "find", "last"]
    )
    parser.add_argument(
        "words", nargs="*", help="find, activate: name, then other required words"
    )
    args = parser.parse_args(argv)
    if not 1 <= args.max <= MAX_MOVES:
        parser.error(f"--max must be between 1 and {MAX_MOVES}")
    if args.command in ("find", "activate") and not args.words:
        parser.error(f"{args.command} needs a name")
    if not args.journal.parent.is_dir():
        parser.error("--journal must be in an existing directory")
    if args.command == "last":
        message, code = last_entry(args.journal)
        print(message, file=sys.stdout if code == OK else sys.stderr)
        return code
    return run(args, mac or RealMac())


if __name__ == "__main__":
    sys.exit(main())
