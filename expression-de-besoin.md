# Expression de besoin du skill voiceover-testing

Expression de besoin reconstituée par rétro-ingénierie, le 20 novembre 2026, à partir du skill publié (`skills/voiceover-testing/`, commit `ea5ba7e`), de ses tests et de l’essai réel du même jour. Chaque exigence renvoie au fichier qui la porte et à sa preuve ; « non vérifié » signale ce qui n’a pas été prouvé.

## Contexte

Les tests au lecteur d’écran se font surtout à la main, et lentement. Des outils automatisent déjà VoiceOver : Guidepup, pour des tests déterministes en intégration continue, et la méthode de Craig Abbott, où Claude Code joue des scénarios Gherkin. Aucun des deux ne protège la session de la personne ni ne qualifie une capture incertaine.

Le besoin : qu’un agent (Claude Code, Codex ou tout agent qui lit un `SKILL.md`) observe les annonces réelles de VoiceOver sur un parcours web et en rende compte de façon fiable, sans nuire à la personne ni à sa machine.

## Problèmes à prévenir

Sans ce skill, un agent risque de :

- conclure sur le DOM au lieu des annonces réellement prononcées ;
- prendre une capture vide pour une absence d’annonce, ou une ancienne phrase pour une annonce nouvelle ;
- lire ou piloter la fenêtre ou la session d’une personne sans son accord ;
- modifier des réglages sans les restaurer, ou inventer l’état initial pour « vérifier » la restauration ;
- piloter VoiceOver par des scripts AppleScript libres, sans borne ni trace ;
- déduire une conformité RGAA ou WCAG d’un test exploratoire.

## Acteurs

- La personne qui demande le test : testeur ou auditeur en accessibilité.
- L’agent, qui exécute le skill.
- La personne qui utilise le Mac et VoiceOver, parfois la même que la demandeuse.
- La personne qui lit le rapport et décide de la suite.

## Périmètre

Inclus : un site ou un parcours web, VoiceOver sur macOS, un navigateur déclaré, en mode démo (une personne regarde) ou collecte (traces sans spectateur).

Exclus : audit RGAA ou WCAG, NVDA et JAWS, écoute humaine, intégration continue, correction du site testé.

## Besoins fonctionnels

- **BF-01 Déclenchement.** Se déclencher sur une demande de test avec VoiceOver ou avec le lecteur d’écran du Mac ; ne pas se déclencher pour une inspection DOM, un audit RGAA, NVDA ou JAWS. Source : description de `SKILL.md`. Preuve : smoke prompt et near-miss réussis dans une session `claude -p` neuve.
- **BF-02 Reçu de session.** Ouvrir un reçu avant toute allocation ou capture : cible, versions, langue et verbosité, outil de pilotage, allocations, inventaire, traces, nettoyage. Source : `SKILL.md` (Préparer), `references/protocole-natif.md` (Reçu de session).
- **BF-03 État initial.** Relever l’état de VoiceOver et des autorisations avant modification ; consigner comme « inconnu » un état non relevé, sans jamais le reconstituer. Source : `references/protocole-natif.md`. Preuve : pressure testing (scénario S3 respecté).
- **BF-04 Activation de VoiceOver.** N’activer VoiceOver qu’avec l’accord explicite de l’utilisateur ; sans accord, consigner le blocage et ne rien collecter. Source : `SKILL.md`, étape 2.
- **BF-05 Inventaire par état.** Lister les contrôles attendus par état, avec un dénominateur explicite et les états non exercés. Source : `SKILL.md`, étape 3.
- **BF-06 Canal vérifié.** Obtenir une annonce témoin réelle en début et en fin de séquence ; sans elle, toute absence est non concluante. Source : `SKILL.md`, étape 4.
- **BF-07 Collecte native.** Lire `content of last phrase` par sondage borné, sans activer, faire parler ni piloter VoiceOver ; écrire un JSONL neuf et horodaté ; compter les phrases distinctes. Source : `scripts/collect_voiceover.py`. Preuve : 11 tests.
- **BF-08 Pilotage du curseur.** Déplacer le curseur VoiceOver ou activer un élément (`first`, `next`, `prev`, `activate`, `find`, `last`), en assemblant les fragments de chaque annonce. Source : `scripts/pilot_voiceover.py`. Preuve : 21 tests et essai réel.
- **BF-09 Conditions du pilotage.** Refuser d’agir sans reçu citant l’accord, si VoiceOver est inactif, si le navigateur du reçu n’est pas au premier plan, ou si l’onglet ne porte pas le marqueur (8 caractères au moins, revérifié tous les 10 déplacements de `find`). Source : `scripts/pilot_voiceover.py`. Preuve : tests et refus réel en code 3.
- **BF-10 Messages dynamiques.** Exercer première apparition, remplacement et réapparition, avec un témoin négatif si possible. Source : `SKILL.md`, étape 7.
- **BF-11 Rapport et matrice.** Relier état, action horodatée, annonce exacte, effet et trace ; séparer nom vocalisé, action, annonce dynamique, effet vérifié et écoute humaine ; conclure par une décision bornée. Source : `SKILL.md`, étape 8, et checklist finale.
- **BF-12 Nettoyage vérifié.** Fermer seulement les ressources créées, restaurer l’état initial relevé avant la livraison et lire chaque réglage restauré ; « en attente » seulement si macOS exige une authentification. Source : `SKILL.md`, étape 9, `references/protocole-natif.md`. Preuve : restauration réelle du 20 novembre.

## Exigences non fonctionnelles

- **ENF-01 Sûreté.** Aucun script ne démarre, n’arrête ni ne règle VoiceOver ; chaque appel AppleScript porte la garde « VoiceOver déjà lancé ». Pas de `pkill`, de `killall`, de `tccutil reset` ni d’élargissement des droits. Preuve : test de la garde et refus réel sans démarrage.
- **ENF-02 Bornage temporel.** Appels AppleScript bornés à 2 secondes, sous-processus à 3 secondes, durée de collecte de 3 600 secondes au plus. Preuve : expiration réelle en 2 secondes (`-1712`), sans blocage.
- **ENF-03 Confidentialité.** Traces locales en mode 600, texte hors cible exclu des preuves publiques, traces exclues du dépôt par `.gitignore`.
- **ENF-04 Traçabilité.** Horodatage UTC de chaque ligne, empreinte SHA-256 du reçu dans le journal du pilote, refus journalisés.
- **ENF-05 Honnêteté des verdicts.** Une capture vide, ancienne ou ambiguë est non concluante ; un code de sortie autre que 0 n’est jamais un succès (code 7 : action sans annonce nouvelle) ; aucune conclusion de conformité.
- **ENF-06 Portabilité.** Format Agent Skills, sans renvoi à un environnement de travail particulier ni chemin local ; Python 3.7 ou plus, bibliothèque standard seule ; utilisable par Claude Code et Codex.
- **ENF-07 Testabilité.** Fonctions qui reçoivent VoiceOver, l’horloge et les pauses en paramètre, pour des tests sans macOS ni VoiceOver.
- **ENF-08 Sobriété.** `SKILL.md` court (173 lignes), détails en références lues au bon moment.
- **ENF-09 Langue.** Skill et documentation en français ; identifiants lus par un programme en anglais.

## Contraintes

- macOS avec VoiceOver ; le contrôle par AppleScript se règle dans l’Utilitaire VoiceOver et ne se change pas en ligne de commande.
- Autorisations Automatisation de macOS vers VoiceOver et vers le navigateur, accordées par la personne.
- Pilotage limité à Safari et Google Chrome.
- Le sondage n’est pas un flux exhaustif : il peut manquer ou tronquer des phrases.
- Les annonces dépendent de la langue de VoiceOver ; les marqueurs de zone web existent en anglais et en français.

## Critères d’acceptation

Vérifiés le 20 novembre 2026 :

- **CA-01** : smoke prompt réussi et near-miss réussi (BF-01).
- **CA-02** : 32 tests sans VoiceOver réussis (BF-07, BF-08, BF-09, ENF-01, ENF-05).
- **CA-03** : VoiceOver éteint, le pilote refuse en code 3 sans le démarrer (BF-09, ENF-01).
- **CA-04** : une invite en attente fait expirer l’appel en 2 secondes, sans blocage (ENF-02).
- **CA-05** : sur la démo, la page correcte et le témoin négatif se distinguent par la position du curseur, un passage par cas (BF-08, BF-11).
- **CA-06** : onglets, serveur et VoiceOver restaurés et vérifiés (BF-12).
- **CA-07** : structure 65/65 ; pressure testing 5/5 sur le texte du skill, 4/5 sur le pilotage avant la dernière correction.

Non vérifiés :

- évaluation répétée cinq fois et juge externe ;
- pilotage dans Google Chrome ;
- VoiceOver dans une autre langue que le français ;
- un parcours réel hors de la page de démonstration.

## Risques résiduels

- Le reçu trace l’accord, il ne le prouve pas : un agent peut l’écrire lui-même.
- Rien n’empêche mécaniquement un `osascript` direct hors des scripts.
- Le pilote vérifie l’onglet, pas la position du curseur VoiceOver dans la page.
- Une annonce longue peut être tronquée par le sondage.
- Deux onglets de même titre ne se distinguent pas par le marqueur.

## Questions ouvertes

- Faut-il imposer un compte macOS dédié aux essais plutôt que la session de la personne ?
- Faut-il qualifier Safari et Google Chrome séparément, puisque l’arbre d’automatisation de Safari a déjà été trouvé partiel ?
- Faut-il un contrôle automatique de la position du curseur, plutôt que la lecture de l’annonce suivante ?
- Quel seuil de répétition (N=5 ou plus) suffit pour un « GO comportemental » ?
