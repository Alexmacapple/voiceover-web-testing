# Collecte native et restauration

Lire d’abord [la garde de cible et de propriété](cible-et-propriete.md). Un échec de focus suspend la collecte ; la fermeture reste limitée au handle créé et enregistré, avec identité revalidée.

## Reçu de session

Créer un dossier neuf avec : cible/version et date UTC ; navigateur/moteur ;
macOS/VoiceOver/langue/verbosité ; outil de pilotage choisi ; allocations ;
inventaire par état ; journal des actions ; traces ; rapport et nettoyage.
Conserver les versions effectivement observées.

Relever **avant modification** :

- VoiceOver actif ou non ;
- Utilitaire VoiceOver → Général → « Permettre à AppleScript de contrôler
  VoiceOver » (macOS en anglais : « Allow VoiceOver to be controlled with
  AppleScript ») ;
- Confidentialité et sécurité → Automatisation → application réellement
  porteuse des Apple Events → VoiceOver ;
- onglets, processus et serveur créés pour l’essai ; presse-papiers si une copie
  est prévue. Conserver toute sauvegarde privée hors du rapport et la retirer
  après restauration vérifiée.

Si un réglage a été modifié avant ce relevé, son état initial est **inconnu** :
le consigner tel quel, ne rien restaurer par supposition, demander la valeur
d’origine à l’utilisateur et lui signaler l’écart au protocole avant de
continuer. Ne jamais reconstituer un reçu après coup.

Le porteur peut différer du programme affiché dans le terminal : relever celui
que macOS présente réellement. Ne pas réinitialiser TCC, accorder l’accès complet
au disque ou élargir l’accessibilité pour résoudre une collecte refusée. Respecter
les approbations natives et les confirmations exigées par les outils disponibles.
Toute saisie de mot de passe/Touch ID est effectuée par l’utilisateur dans macOS.
Une demande « teste le site » ne supprime pas les règles d’autorisation des outils.

## Lire la sortie

Quand le canal est déjà autorisé, la primitive observée est celle du helper
(`SCRIPT` dans `scripts/collect_voiceover.py`, égalité vérifiée par les tests) :

```applescript
with timeout of 2 seconds
if application id "com.apple.VoiceOver" is not running then error "VoiceOver is not running"
tell application id "com.apple.VoiceOver" to get content of last phrase
end timeout
```

Sans la ligne de garde, `tell` pourrait lancer VoiceOver : ne jamais l’omettre.
Elle lit la dernière phrase native et ne déclenche aucune navigation. Le helper
requiert VoiceOver déjà actif, n’active pas le lecteur et n’accorde aucun droit :

```sh
python3 scripts/collect_voiceover.py --seconds 60 --state editor --output /chemin/neuf/editor.jsonl
```

Lancer la commande depuis le dossier du skill, ou indiquer le chemin complet du
script ; choisir un fichier de sortie inexistant. Le code de sortie est non nul
en cas d’erreur, d’interruption ou d’indisponibilité. Un code 0 signifie
seulement que la durée est écoulée : la ligne `stop` porte `phrase_count`, et la
valeur 1 indique qu’aucune annonce nouvelle n’a été captée (cas non concluant).
Arrêter le collecteur avant de révoquer son autorisation. Les tests du helper,
sans VoiceOver : `python3 -B -m unittest discover -s tests` depuis le dossier du
skill.

**Ce n’est pas un flux vocal exhaustif** : un sondage peut manquer des phrases
rapides, tronquées ou répétées à l’identique. Espacer les actions d’après la fin
réelle de l’annonce ; conserver les dates des actions. Une ancienne phrase encore
présente n’est pas la preuve d’une annonce nouvelle. Le collecteur déduplique les
valeurs consécutives ; il ne permet donc pas de compter leurs répétitions.

Pour prouver une absence : canal positif avant/après, fenêtre temporelle définie,
action confirmée, recherche dans les traces complètes de cette fenêtre et prise
en compte des limites d’échantillonnage. Sinon résultat **non concluant**, pas
« aucun message annoncé ».

## Piloter sans mélanger les canaux

Charger le site et saisir les champs avec l’outil d’automatisation du navigateur
ou du bureau disponible dans l’environnement (par exemple Playwright ou un outil
d’accessibilité de bureau), et consigner l’outil choisi dans le reçu. Déplacer
le curseur VoiceOver ou activer un élément seulement avec
`scripts/pilot_voiceover.py` (section suivante). Tout autre pilotage de
VoiceOver par AppleScript ou System Events est exclu, même pour poursuivre un
travail déjà commencé. Pour le navigateur, AppleScript ou System Events n’est
utilisable que si les instructions de l’environnement le permettent ou si la
technologie est explicitement demandée. Ne jamais contrôler une application dont
l’accès a été refusé par un outil via un autre canal.

Lors des essais réels, Tab et Maj+Tab avec VoiceOver actif ont fourni les
noms et rôles natifs. Cela ne remplace pas la navigation propre au lecteur.
Distinguer bouton en focus clavier, curseur VoiceOver, activation et effet.
Un arbre AX incomplet dans l’outil ne prouve pas que VoiceOver voit un arbre vide.

## Piloter le curseur VoiceOver

Après l’accord explicite de l’utilisateur, écrire dans le dossier de session un
`recu.json` qui cite cet accord mot pour mot, nomme le navigateur et un marqueur
du titre de l’onglet possédé :

```json
{"accord": "citation exacte de l’accord", "browser": "Safari", "marker": "Service d’exemple"}
```

Ne jamais écrire ce fichier sans accord réel : il trace l’accord, il ne le prouve
pas. Les champs facultatifs `web_area_markers` et `exit_markers` remplacent les
annonces attendues de la zone web (par défaut en anglais et en français).

```sh
python3 scripts/pilot_voiceover.py --receipt /chemin/session/recu.json --journal /chemin/session/pilote.jsonl first
python3 scripts/pilot_voiceover.py --receipt /chemin/session/recu.json --journal /chemin/session/pilote.jsonl find "Se connecter" bouton
```

Commandes : `first` (premier élément de la page), `next`, `prev`, `activate`,
`find <nom> [mots…]` (80 déplacements au plus, `--max` jusqu’à 200) et `last`
(relit la dernière ligne du journal et sort avec son code ; sans journal, code 1). Avant chaque action, le script vérifie que VoiceOver tourne,
que le navigateur du reçu est au premier plan (Safari ou Google Chrome) et que le
titre de l’onglet contient le marqueur, long d’au moins 8 caractères. `find`
revérifie cette cible tous les 10 déplacements. Il ne démarre, n’arrête ni ne
règle jamais VoiceOver, et chaque appel AppleScript est borné à 2 secondes.

Codes de sortie : 0 annonce nouvelle captée, 1 erreur ou délai dépassé,
2 arguments invalides, 3 VoiceOver inactif, 4 reçu invalide, 5 cible incorrecte,
6 nom introuvable, 7 action faite sans annonce nouvelle (cas non concluant).
Chaque appel, refus compris, ajoute au journal une ligne horodatée avec l’annonce
assemblée, ses fragments et l’empreinte SHA-256 du reçu. La capture assemble les
fragments pendant un peu plus d’une seconde ; une annonce plus longue peut être
tronquée.

## Nettoyage vérifié

Restaurer l’état initial relevé de chaque réglage modifié, en particulier le
lecteur et les droits ajoutés, sauf réglage que l’utilisateur a explicitement
demandé de laisser actif : consigner ce choix dans le reçu. Une autorisation
préexistante n’est pas révoquée. Désactiver une seule permission temporaire,
sans toucher aux autres. Après chaque action, lire le réglage affiché :
tentative de clic ≠ restauration.

Si une feuille Touch ID/mot de passe apparaît, ne pas contourner ni déclarer
l’opération faite : expliquer « macOS demande votre empreinte ou votre mot de
passe pour retirer l’autorisation temporaire ». Garder le reçu en attente ; une
session ultérieure relit l’état courant avant de reprendre.
