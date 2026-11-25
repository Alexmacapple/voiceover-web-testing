import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def relative_links(path):
    for target in LINK.findall(path.read_text(encoding="utf-8")):
        if not re.match(r"^[a-z]+:", target):
            yield target


class ReferencesTest(unittest.TestCase):
    def test_tous_les_liens_relatifs_existent(self):
        broken = [
            f"{md.relative_to(SKILL)} -> {target}"
            for md in sorted(SKILL.rglob("*.md"))
            for target in relative_links(md)
            if not (md.parent / target).exists()
        ]
        self.assertEqual(broken, [])

    def test_reglages_relies_au_skill_et_au_protocole(self):
        for source, target in (
            ("SKILL.md", "references/reglages-et-commandes.md"),
            ("references/protocole-natif.md", "reglages-et-commandes.md"),
        ):
            with self.subTest(source=source):
                self.assertIn(target, list(relative_links(SKILL / source)))

    def test_le_corpus_apple_est_atteignable_depuis_la_synthese(self):
        links = list(relative_links(SKILL / "references/reglages-et-commandes.md"))
        self.assertIn("guide-apple-10.8/index.md", links)


if __name__ == "__main__":
    unittest.main()
