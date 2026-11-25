"""Pilote sur une fenêtre de document (Aperçu, Word, PowerPoint), sans macOS ni VoiceOver.

Lancer depuis le dossier du skill : python3 -B -m unittest discover -s tests
"""

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_pilot_voiceover import FakeMac, pv

FENETRE = "rapport-recette-7f3a.pdf – Page 1 sur 21"


class FakeDocumentMac(FakeMac):
    """Ajoute à FakeMac les fenêtres de l'application de document au premier plan."""

    def __init__(self, windows=None, **kwargs):
        kwargs.setdefault("frontmost", "/System/Applications/Preview.app/")
        super().__init__(**kwargs)
        self.windows = [FENETRE] if windows is None else windows

    def osascript(self, script, timeout=3):
        if "System Events" in script and "name of window" in script:
            self.scripts.append(script)
            return "\n".join([self.windows[0], *self.windows]) if self.windows else ""
        return super().osascript(script, timeout)


class PilotDocumentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        self.journal = self.dir / "journal.jsonl"
        self.receipt = self.write_receipt()

    def tearDown(self):
        self.tmp.cleanup()

    def write_receipt(self, **champs):
        data = {
            "accord": "Utilisateur : « oui, pilote VoiceOver sur ce PDF »",
            "app": "Preview",
            "marker": "rapport-recette-7f3a",
        }
        data.update(champs)
        data = {k: v for k, v in data.items() if v is not None}
        path = self.dir / "recu.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def run_pilot(self, mac, *args):
        return pv.main(
            ["--receipt", str(self.receipt), "--journal", str(self.journal), *args],
            mac=mac,
        )

    def last_row(self):
        return json.loads(self.journal.read_text(encoding="utf-8").splitlines()[-1])

    def test_next_dans_la_fenetre_possedee_journalise_app_et_fenetre(self):
        mac = FakeDocumentMac(moves=[["Page 2 contenant niveau d’en-tête 1 SOMMAIRE"]])
        self.assertEqual(self.run_pilot(mac, "next"), pv.OK)
        row = self.last_row()
        self.assertEqual((row["app"], row["window"]), ("Preview", FENETRE))
        self.assertNotIn("url", row)
        self.assertEqual(
            row["announcement"], "Page 2 contenant niveau d’en-tête 1 SOMMAIRE"
        )

    def test_into_et_out_envoient_les_deplacements_voiceover(self):
        mac = FakeDocumentMac(moves=[["Entrée Page 1"], ["Page 1"]])
        self.assertEqual(self.run_pilot(mac, "into"), pv.OK)
        self.assertEqual(self.run_pilot(mac, "out"), pv.OK)
        self.assertEqual(mac.actions, ["move into item", "move out of item"])

    def test_autre_application_au_premier_plan_refusee_sans_geste(self):
        mac = FakeDocumentMac(frontmost="/Applications/Safari.app/", moves=[["x"]])
        self.assertEqual(self.run_pilot(mac, "next"), pv.TARGET)
        self.assertEqual(mac.actions, [])

    def test_fenetre_de_tete_sans_marqueur_refusee(self):
        mac = FakeDocumentMac(
            windows=["Courrier confidentiel.pdf", FENETRE], moves=[["x"]]
        )
        self.assertEqual(self.run_pilot(mac, "next"), pv.TARGET)
        self.assertEqual(mac.actions, [])

    def test_deux_fenetres_avec_le_marqueur_refusees(self):
        mac = FakeDocumentMac(windows=[FENETRE, FENETRE + " (copie)"], moves=[["x"]])
        self.assertEqual(self.run_pilot(mac, "next"), pv.TARGET)
        self.assertIn("ambiguë", self.last_row()["refused"])

    def test_recus_invalides_refuses(self):
        for champs in (
            {"browser": "Safari", "url_marker": "127.0.0.1:8765/x"},
            {"app": "TextEdit"},
            {"marker": "court"},
            {"app": "Microsoft Word"},
        ):
            with self.subTest(champs=champs):
                self.receipt = self.write_receipt(**champs)
                self.assertEqual(self.run_pilot(FakeDocumentMac(), "next"), pv.RECEIPT)

    def test_word_admis_avec_ses_reperes_de_contenu_declares(self):
        self.receipt = self.write_receipt(
            app="Microsoft Word", web_area_markers=["zone de texte du document"]
        )
        mac = FakeDocumentMac(
            frontmost="/Applications/Microsoft Word.app/", moves=[["Titre 1, Bilan"]]
        )
        self.assertEqual(self.run_pilot(mac, "next"), pv.OK)

    def test_first_entre_dans_le_document_par_le_repere_observe_d_apercu(self):
        mac = FakeDocumentMac(
            moves=[
                ["barre d’outils"],
                ["document groupe"],
                [
                    "Entrée document groupe 21 éléments Page 1 contenant niveau d’en-tête 1"
                ],
            ]
        )
        self.assertEqual(self.run_pilot(mac, "first"), pv.OK)
        self.assertEqual(
            mac.actions, ["move to first item", "move right", "move into item"]
        )

    def test_find_sans_repere_de_fin_ne_prouve_pas_l_unicite(self):
        mac = FakeDocumentMac(
            moves=[["document groupe"], ["Entrée Page 1 SOMMAIRE"], ["Page 2"], [], []],
            under_cursor="SOMMAIRE",
        )
        code = self.run_pilot(mac, "find", "SOMMAIRE")
        self.assertIn(code, (pv.ELEMENT, pv.NOT_FOUND))
        self.assertNotEqual(self.last_row().get("unique"), True)
        self.assertEqual(self.run_pilot(mac, "activate", "SOMMAIRE"), pv.ELEMENT)
        self.assertNotIn("perform action", mac.actions)


if __name__ == "__main__":
    unittest.main()
