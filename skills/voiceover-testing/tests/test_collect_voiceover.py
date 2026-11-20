"""Tests du collecteur sans macOS ni VoiceOver : read, clock et sleep sont simulés.

Lancer depuis n'importe quel dossier : python3 -B -m unittest discover -s <skill>/tests
"""

import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import collect_voiceover as cv


def fake_clock():
    """Horloge qui avance d'une seconde à chaque lecture."""
    ticks = iter(range(10_000))
    return lambda: float(next(ticks))


def run(phrases=(), seconds=10, error=None):
    rows = []
    values = iter(phrases)

    def read():
        if error is not None:
            raise error
        return next(values)

    code = cv.collect(
        seconds,
        "editor",
        rows.append,
        read=read,
        clock=fake_clock(),
        sleep=lambda _: None,
    )
    return code, rows


class CollectTest(unittest.TestCase):
    def test_deduplique_les_valeurs_consecutives(self):
        code, rows = run(["A", "A", "B", "B", "A"], seconds=6)
        self.assertEqual(code, 0)
        self.assertEqual(
            [r["phrase"] for r in rows if r["kind"] == "phrase"], ["A", "B", "A"]
        )
        self.assertEqual(rows[0]["kind"], "start")
        self.assertEqual(rows[-1]["reason"], "duration_elapsed")

    def test_fin_compte_les_phrases_distinctes(self):
        _, stale = run(["ancienne"] * 5, seconds=6)
        _, fresh = run(
            ["ancienne", "nouvelle", "nouvelle", "autre", "autre"], seconds=6
        )
        self.assertEqual(stale[-1]["phrase_count"], 1)
        self.assertEqual(fresh[-1]["phrase_count"], 3)

    def test_interruption_renvoie_130(self):
        code, rows = run(error=KeyboardInterrupt())
        self.assertEqual(code, 130)
        self.assertEqual(rows[-1]["reason"], "interrupted")
        self.assertEqual(rows[-1]["phrase_count"], 0)

    def test_erreur_osascript_renvoie_1(self):
        code, rows = run(error=RuntimeError("osascript exit 1: refus"))
        self.assertEqual(code, 1)
        self.assertEqual(rows[-1]["kind"], "error")

    def test_delai_depasse_renvoie_1(self):
        code, rows = run(error=subprocess.TimeoutExpired("osascript", 3))
        self.assertEqual(code, 1)
        self.assertEqual(rows[-1]["kind"], "error")

    def test_erreur_porte_le_nombre_de_phrases(self):
        values = iter(["A"])

        def read():
            try:
                return next(values)
            except StopIteration:
                raise RuntimeError("osascript exit 1: refus") from None

        rows = []
        code = cv.collect(
            10,
            "editor",
            rows.append,
            read=read,
            clock=fake_clock(),
            sleep=lambda _: None,
        )
        self.assertEqual(code, 1)
        self.assertEqual(rows[-1]["phrase_count"], 1)


class ArgumentsTest(unittest.TestCase):
    def call(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / "collect_voiceover.py"), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def test_duree_invalide_refusee_sans_appel_a_voiceover(self):
        result = self.call(
            "--seconds", "0", "--state", "editor", "--output", "/nonexistent/x.jsonl"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--seconds", result.stderr)

    def test_etat_vide_refuse(self):
        result = self.call("--state", " ", "--output", "/nonexistent/x.jsonl")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--state", result.stderr)

    @unittest.skipUnless(
        sys.platform == "darwin",
        "le script refuse d'abord toute plateforme autre que macOS",
    )
    def test_sortie_existante_refusee_sans_ecraser(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = pathlib.Path(tmp) / "editor.jsonl"
            existing.write_text("preuve antérieure\n", encoding="utf-8")
            result = self.call("--state", "editor", "--output", str(existing))
            self.assertEqual(result.returncode, 2)
            self.assertIn("--output", result.stderr)
            self.assertEqual(
                existing.read_text(encoding="utf-8"), "preuve antérieure\n"
            )

    @unittest.skipUnless(
        sys.platform == "darwin",
        "le script refuse d'abord toute plateforme autre que macOS",
    )
    def test_dossier_de_sortie_absent_refuse(self):
        result = self.call("--state", "editor", "--output", "/nonexistent/dir/x.jsonl")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--output", result.stderr)


class DocumentationTest(unittest.TestCase):
    def test_primitive_du_protocole_identique_au_script(self):
        protocol = (SCRIPTS.parent / "references" / "protocole-natif.md").read_text(
            encoding="utf-8"
        )
        block = protocol.split("```applescript\n", 1)[1].split("```", 1)[0]
        documented = [line.strip() for line in block.strip().splitlines()]
        self.assertEqual(documented, [line.strip() for line in cv.SCRIPT.splitlines()])


if __name__ == "__main__":
    unittest.main()
