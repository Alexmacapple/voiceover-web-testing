# VoiceOver Web Testing

Skill d’agent, au format [Agent Skills](https://agentskills.io/), pour tester un site ou un parcours web avec VoiceOver réellement exécuté sur macOS et relier chaque annonce native à un état et à une action.

Le skill et sa documentation sont rédigés en français. Le besoin auquel il répond, ses exigences et ses critères d’acceptation sont décrits dans l’[expression de besoin](expression-de-besoin.md).

## Ce que fait le skill

- Il guide l’agent pas à pas : reçu de session, état initial relevé, inventaire par état, canal vérifié en début et en fin, matrice état → action → annonce → effet, nettoyage vérifié.
- Son collecteur, `scripts/collect_voiceover.py`, lit par sondage borné la dernière phrase prononcée par VoiceOver (`content of last phrase`) et l’écrit dans un fichier JSONL neuf, horodaté et privé. Il n’active pas VoiceOver, ne parle pas et ne navigue pas.
- Son pilote, `scripts/pilot_voiceover.py`, déplace le curseur VoiceOver ou active un élément dans l’onglet possédé, après un accord de l’utilisateur cité dans `recu.json`. Il refuse d’agir si VoiceOver est inactif ou si l’onglet au premier plan n’est pas le bon, borne chaque appel et journalise chaque action. Il ne démarre ni n’arrête VoiceOver.

## Ce qu’il ne fait pas

- Aucun verdict de conformité RGAA ou WCAG.
- Ni NVDA ni JAWS, ni autre navigateur que celui testé.
- Pas de transcription exhaustive : le sondage peut manquer des phrases rapides ou répétées.
- Il ne remplace pas l’écoute de personnes qui utilisent un lecteur d’écran au quotidien.

## Prérequis

- macOS avec VoiceOver, Python 3.7 ou plus et `/usr/bin/osascript`.
- Utilitaire VoiceOver → Général → « Permettre à AppleScript de contrôler VoiceOver » (« Allow VoiceOver to be controlled with AppleScript »).
- L’autorisation Automatisation de l’application qui lance les commandes, vers VoiceOver et vers le navigateur (Safari ou Google Chrome) ; macOS la demande au premier appel.
- Un outil de pilotage du navigateur ou du bureau, par exemple Playwright, pour charger la page et saisir les champs.

Les versions de macOS et de VoiceOver ne sont pas qualifiées : le skill demande de les relever dans chaque reçu de session. Un seul essai réel a eu lieu, le 20 novembre 2026, sur la page de démonstration (macOS 27, Safari 27, VoiceOver en français) : le pilote y a distingué la page correcte du témoin négatif par la position du curseur VoiceOver.

## Installation

Copier le dossier `skills/voiceover-testing/` :

- Claude Code : dans `~/.claude/skills/` pour tous les projets, ou dans `.claude/skills/` d’un projet ;
- Codex : dans `~/.codex/skills/` ; le fichier `agents/openai.yaml` fournit le nom affiché et l’invite par défaut propres à Codex ;
- autre agent : lui indiquer le chemin du `SKILL.md`.

## Tests

```bash
cd skills/voiceover-testing
python3 -B -m unittest discover -s tests
```

Les tests simulent VoiceOver et ne lancent jamais le lecteur. Deux tests d’arguments ne s’exécutent que sur macOS.

## Démonstration

Le dossier `demo/` contient une page de connexion d’exemple, en français, et son serveur Node sans dépendance (Node 18 ou plus) :

```bash
node demo/server.js
```

Ouvrir ensuite http://127.0.0.1:8080/sign-in ; la variable `PORT` change le port. Le serveur n’écoute que sur `127.0.0.1`.

- Témoin positif : envoyer le formulaire vide. Le focus arrive sur le récapitulatif « Il y a un problème ».
- Témoin négatif : ouvrir `/sign-in?defaut=focus`, puis envoyer le formulaire vide. Le récapitulatif s’affiche, mais le focus reste sur le bouton « Se connecter ».

Origine : page et serveur du dépôt [voiceover-testing-with-claude](https://github.com/abbott567/voiceover-testing-with-claude) de Craig Abbott, sous licence MIT reproduite dans `demo/LICENSE`. Modifications : textes, commentaires et langue de la page traduits en français ; logo et polices IBM Plex Sans retirés (la page utilise Arial) ; écoute limitée à `127.0.0.1` ; témoin négatif activé par l’adresse au lieu de commenter une ligne.

## Confidentialité

Les traces peuvent contenir du texte privé lu par VoiceOver, y compris hors du site testé. Les conserver localement ; le `.gitignore` exclut les fichiers `*.jsonl`.

## Voir aussi

- Craig Abbott, [Automated screen reader testing with Claude Code, VoiceOver and Gherkin](https://www.craigabbott.co.uk/blog/2026/automated-screen-reader-testing-with-claude-code-voiceover-and-gherkin/), et son dépôt [voiceover-testing-with-claude](https://github.com/abbott567/voiceover-testing-with-claude) : pilotage de VoiceOver par AppleScript et scénarios Gherkin.
- [Guidepup](https://www.guidepup.dev/) : tests de lecteurs d’écran déterministes, adaptés à l’intégration continue.

## Licence

MIT, voir [LICENSE](LICENSE). Le dossier `demo/` reste sous la licence MIT de Craig Abbott, reproduite dans `demo/LICENSE`.
