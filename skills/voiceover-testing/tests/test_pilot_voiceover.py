"""Tests du pilote sans macOS ni VoiceOver : VoiceOver, le navigateur et osascript sont simulés.

Lancer depuis le dossier du skill : python3 -B -m unittest discover -s tests
"""

import hashlib
import json
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import pilot_voiceover as pv

TITLE = "Connexion - Service d’exemple"


class FakeMac:
    """Simule VoiceOver : chaque action consomme la liste de fragments suivante."""

    def __init__(
        self,
        moves=(),
        running=True,
        frontmost="/Applications/Safari.app/",
        title=TITLE,
        initial="ancienne phrase",
        fail_on_action=None,
        retitle_after=None,
        new_title="Boîte de réception",
    ):
        self.moves = [list(m) for m in moves]
        self.running, self.frontmost, self.title = running, frontmost, title
        self.current, self.pending = initial, []
        self.scripts, self.actions = [], []
        self.fail_on_action = fail_on_action
        self.retitle_after, self.new_title = retitle_after, new_title

    def voiceover_running(self):
        return self.running

    def sleep(self, _seconds):
        pass

    def osascript(self, script, timeout=3):
        self.scripts.append(script)
        if "path to frontmost application" in script:
            return self.frontmost
        if "current tab of front window" in script:
            if (
                self.retitle_after is not None
                and len(self.actions) >= self.retitle_after
            ):
                return self.new_title
            return self.title
        if "content of last phrase" in script:
            if self.pending:
                self.current = self.pending.pop(0)
            return self.current
        if self.fail_on_action is not None:
            raise self.fail_on_action
        self.actions.append(script.split("tell vo cursor to ")[-1].split("\n")[0])
        self.pending = self.moves.pop(0) if self.moves else []
        return ""


class PilotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        self.journal = self.dir / "journal.jsonl"
        self.receipt = self.write_receipt()

    def tearDown(self):
        self.tmp.cleanup()

    def write_receipt(self, **overrides):
        data = {
            "accord": "Utilisateur : « oui, tu peux piloter VoiceOver sur la démo »",
            "browser": "Safari",
            "marker": "Service d’exemple",
        }
        data.update(overrides)
        path = self.dir / "recu.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def run_pilot(self, mac, *args):
        return pv.main(
            ["--receipt", str(self.receipt), "--journal", str(self.journal), *args],
            mac=mac,
        )

    def rows(self):
        return [
            json.loads(line)
            for line in self.journal.read_text(encoding="utf-8").splitlines()
        ]

    def test_next_assemble_les_fragments_et_journalise(self):
        mac = FakeMac(moves=[["Adresse électronique", "champ de texte"]])
        self.assertEqual(self.run_pilot(mac, "next"), 0)
        row = self.rows()[-1]
        self.assertEqual(row["announcement"], "Adresse électronique, champ de texte")
        self.assertTrue(row["fresh"])
        self.assertEqual(row["exit_code"], 0)
        self.assertIn("timestamp", row)
        self.assertEqual(stat.S_IMODE(self.journal.stat().st_mode), 0o600)

    def test_ancienne_phrase_n_est_pas_une_annonce(self):
        mac = FakeMac(moves=[[]])
        self.assertEqual(self.run_pilot(mac, "next"), 7)
        row = self.rows()[-1]
        self.assertEqual(row["announcement"], "")
        self.assertFalse(row["fresh"])
        self.assertEqual(row["exit_code"], 7)

    def test_marqueur_trop_court_refuse(self):
        self.receipt = self.write_receipt(marker="Conn")
        mac = FakeMac()
        self.assertEqual(self.run_pilot(mac, "next"), 4)
        self.assertEqual(mac.scripts, [])

    def test_find_reverifie_la_cible_pendant_le_parcours(self):
        moves = [["contenu web"], ["élément 0"]] + [
            [f"élément {i}"] for i in range(1, 60)
        ]
        mac = FakeMac(moves=moves, retitle_after=12)
        self.assertEqual(self.run_pilot(mac, "--max", "40", "find", "introuvable"), 5)
        self.assertLess(mac.actions.count("move right"), 40)

    def test_journal_porte_l_empreinte_du_recu(self):
        self.run_pilot(FakeMac(moves=[["Mot de passe"]]), "next")
        expected = hashlib.sha256(self.receipt.read_bytes()).hexdigest()
        self.assertEqual(self.rows()[-1]["receipt_sha256"], expected)

    def test_first_entre_dans_le_contenu_web(self):
        mac = FakeMac(moves=[["contenu web"], ["Connexion", "titre de niveau 1"]])
        self.assertEqual(self.run_pilot(mac, "first"), 0)
        self.assertEqual(mac.actions, ["move to first item", "move into item"])
        self.assertEqual(
            self.rows()[-1]["announcement"], "Connexion, titre de niveau 1"
        )

    def test_find_s_arrete_sur_le_nom_en_mots_entiers(self):
        moves = [
            ["contenu web"],
            ["Connexion, titre de niveau 1"],
            ["Adresse électronique"],
            ["Se connecter, bouton"],
        ]
        mac = FakeMac(moves=moves)
        self.assertEqual(self.run_pilot(mac, "find", "Se connecter", "bouton"), 0)
        self.assertEqual(self.rows()[-1]["announcement"], "Se connecter, bouton")

    def test_find_refuse_un_mot_partiel(self):
        moves = [["contenu web"], ["Connexion, titre de niveau 1"], [], []]
        mac = FakeMac(moves=moves)
        self.assertEqual(self.run_pilot(mac, "find", "Connex"), 6)

    def test_find_s_arrete_sur_l_indication_reelle_de_sortie_en_francais(self):
        # Annonce relevée lors de l'essai réel du 20 novembre 2026 (macOS 27, VoiceOver en français).
        hint = (
            "Vous êtes actuellement sur principal, dans du contenu web.  Pour sortir de cette zone "
            "web, appuyez sur Contrôle-Option-Maj-Flèche Vers Le Haut."
        )
        moves = [["contenu web"], ["Connexion"], [hint]] + [
            [f"élément {i}"] for i in range(20)
        ]
        mac = FakeMac(moves=moves)
        self.assertEqual(self.run_pilot(mac, "find", "introuvable"), 6)
        self.assertEqual(mac.actions.count("move right"), 1)

    def test_find_borne_le_nombre_de_deplacements(self):
        moves = [["contenu web"], ["élément 0"]] + [
            [f"élément {i}"] for i in range(1, 50)
        ]
        mac = FakeMac(moves=moves)
        self.assertEqual(self.run_pilot(mac, "--max", "3", "find", "introuvable"), 6)
        self.assertEqual(mac.actions.count("move right"), 3)

    def test_refuse_si_voiceover_inactif_sans_le_lancer(self):
        mac = FakeMac(running=False)
        self.assertEqual(self.run_pilot(mac, "next"), 3)
        self.assertEqual(mac.scripts, [])
        self.assertEqual(self.rows()[-1]["exit_code"], 3)

    def test_refuse_une_autre_application_au_premier_plan(self):
        mac = FakeMac(frontmost="/System/Applications/Utilities/Terminal.app/")
        self.assertEqual(self.run_pilot(mac, "next"), 5)
        self.assertEqual(mac.actions, [])

    def test_refuse_un_onglet_sans_le_marqueur(self):
        mac = FakeMac(title="Boîte de réception")
        self.assertEqual(self.run_pilot(mac, "next"), 5)
        self.assertEqual(mac.actions, [])

    def test_refuse_un_recu_sans_accord(self):
        self.receipt = self.write_receipt(accord=" ")
        mac = FakeMac()
        self.assertEqual(self.run_pilot(mac, "next"), 4)
        self.assertEqual(mac.scripts, [])

    def test_refuse_un_navigateur_non_pris_en_charge(self):
        self.receipt = self.write_receipt(browser="Firefox")
        self.assertEqual(self.run_pilot(FakeMac(), "next"), 4)

    def test_delai_depasse_journalise_l_erreur(self):
        mac = FakeMac(fail_on_action=subprocess.TimeoutExpired("osascript", 3))
        self.assertEqual(self.run_pilot(mac, "next"), 1)
        self.assertIn("error", self.rows()[-1])

    def test_chaque_appel_a_voiceover_porte_la_garde(self):
        mac = FakeMac(moves=[["contenu web"], ["Connexion"]])
        self.run_pilot(mac, "first")
        vo_scripts = [s for s in mac.scripts if "com.apple.VoiceOver" in s]
        self.assertTrue(vo_scripts)
        for script in vo_scripts:
            self.assertIn("is not running then error", script)
            self.assertIn("with timeout of", script)

    def test_last_relit_le_journal_sans_appeler_voiceover(self):
        self.run_pilot(FakeMac(moves=[["Mot de passe"]]), "next")
        mac = FakeMac()
        self.assertEqual(self.run_pilot(mac, "last"), 0)
        self.assertEqual(mac.scripts, [])

    def test_last_rend_le_code_de_la_derniere_action(self):
        self.run_pilot(FakeMac(moves=[["Mot de passe"]]), "next")
        self.run_pilot(FakeMac(title="Boîte de réception"), "activate")
        self.assertEqual(self.run_pilot(FakeMac(), "last"), 5)

    def test_last_sans_journal_n_est_pas_un_succes(self):
        self.assertEqual(self.run_pilot(FakeMac(), "last"), 1)

    def test_arguments_invalides(self):
        for args in (["--max", "0", "next"], ["find"], ["inconnu"]):
            with self.assertRaises(SystemExit) as ctx:
                self.run_pilot(FakeMac(), *args)
            self.assertEqual(ctx.exception.code, 2, args)
        with self.assertRaises(SystemExit) as ctx:
            pv.main(
                [
                    "--receipt",
                    str(self.receipt),
                    "--journal",
                    "/nonexistent/j.jsonl",
                    "next",
                ],
                mac=FakeMac(),
            )
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
