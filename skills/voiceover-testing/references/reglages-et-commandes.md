# Réglages qui changent la preuve et commandes de référence

Source : guide Apple *VoiceOver Getting Started* pour OS X 10.8, converti dans
[guide-apple-10.8/index.md](guide-apple-10.8/index.md) (texte anglais, un
fichier par sujet). Les noms d’options ci-dessous sont ceux de 2012 : relever
le libellé réellement affiché par l’Utilitaire VoiceOver (VO-F8) de la version
testée, et noter « option absente » plutôt que la supposer.

Le relevé se fait à l’œil, en lecture seule, dans l’Utilitaire. Sur macOS
26.5.2 (25 novembre 2026), `~/Library/Preferences/com.apple.VoiceOver4/default.plist`
était vide (`{}`) : un `defaults read` ne donne pas l’état initial, et une clé
absente ne vaut pas une valeur connue.

## Réglages à relever avant la collecte

Chaque réglage ci-dessous entre dans le reçu de session (protocole natif) avec
sa valeur observée, ou « inconnu ».

Catégorie Navigation ([options](guide-apple-10.8/13-voiceover-utility-options/navigation-category.md)) :

- **Keyboard focus follows VoiceOver cursor** et **VoiceOver cursor follows
  keyboard focus** : ensemble, ils forment le suivi du curseur. Ils décident si
  Tab déplace le curseur VoiceOver et si `pilot_voiceover.py` déplace le focus
  clavier. Sans eux, « focus clavier » et « curseur VoiceOver » ne se déduisent
  pas l’un de l’autre.
- **Mouse pointer** (« Ignores », « Follows » ou « Moves VoiceOver cursor ») :
  avec « Moves VoiceOver cursor », un pointeur déplacé par l’outil
  d’automatisation déplace le curseur VoiceOver hors du script de pilotage.
- **Initial position of VoiceOver cursor**, **Allow cursor wrapping**,
  **Skip redundant labels**, **Automatically interact when using tab key** :
  changent le premier élément annoncé, le bouclage en fin de zone (garde de
  `find`) et le texte des annonces.

Catégorie Web ([navigation](guide-apple-10.8/13-voiceover-utility-options/navigation-pane-of-the-web-category.md),
[chargement](guide-apple-10.8/13-voiceover-utility-options/page-loading-pane-of-the-web-category.md)) :

- **Enable Live Regions** : décochée, VoiceOver ne lit que les régions live
  activées une à une depuis le rotor. Une région muette n’est alors pas un
  défaut du site ; l’absence est **non concluante**.
- **Navigate webpages by** (« DOM order » ou « Grouping items ») : change
  l’ordre de `next` et `prev`, donc le dénominateur parcouru par `find`.
- **Navigate images** et le regroupement des tableaux : changent les éléments
  atteints et leurs annonces.
- **Speak webpage summary**, **Automatically speak the webpage**, **While a
  webpage loads** (progression parlée par défaut) : produisent des phrases au
  chargement qui peuvent devenir `last phrase` et passer pour une annonce
  nouvelle.

Catégorie Verbosity ([indications](guide-apple-10.8/13-voiceover-utility-options/hints-pane-of-the-verbosity-category.md)) :

- **Speak instructions**, **help tags**, **Speak hints after delay** : une
  indication parlée après délai arrive après l’annonce de l’élément et peut la
  remplacer dans la capture. Attendre la fin réelle de l’indication ou relever
  ce réglage comme cause possible d’écart.

Commande à éviter pendant la collecte : **VO-Shift-F3** suspend le suivi du
curseur sans modifier l’Utilitaire ; si elle a servi, le consigner comme
changement d’état. **VO-Z** répète la dernière phrase : la répétition n’est pas
une annonce nouvelle.

## Inventaire natif croisé

Pour l’étape 3, deux mesures natives se comparent à l’inventaire tiré du DOM
sans s’y substituer. Ce sont des gestes de la personne (section suivante) : en
collecte sans spectateur, les noter « non exécutées ».

- **VO-Shift-I** : statistiques de la page (titres, liens, tableaux, repères,
  régions live), calculées sur les catégories présentes dans le rotor web.
- **VO-U** : rotor web, liste des titres, liens, repères, contrôles de
  formulaire et régions live ; touche **O** sur une région live pour
  l’activer ou la couper (changement d’état à consigner).

Un écart entre les deux inventaires est un résultat à relier à l’état et à
l’action, pas une correction de l’un par l’autre.

## Commandes de navigation pour l’étape 6

VO désigne Contrôle+Option. L’agent n’envoie jamais ces raccourcis : seul
`pilot_voiceover.py` déplace le curseur VoiceOver.

- **Démo** : la personne fait le geste ; l’agent l’observe avec le collecteur
  ou `last` et horodate l’action annoncée par la personne.
- **Collecte sans spectateur** : parcourir avec `pilot_voiceover.py` (`first`,
  `next`, `prev`, `find`) ; la navigation par catégorie ci-dessous, le rotor et
  les statistiques sont marqués « non exécutés » dans la matrice, avec cette
  raison. Ne pas les présenter comme couverts.

- Titres : VO-Command-H et VO-Command-Shift-H ; même niveau : VO-Command-M.
- Liens : VO-Command-L ; tableaux : VO-Command-T ; listes : VO-Command-X ;
  images : VO-Command-G ([commandes de recherche](guide-apple-10.8/12-commands-and-gestures/search-commands.md)).
- Entrer dans un groupe ou en sortir : VO-Shift-Flèche bas et VO-Shift-Flèche
  haut ([interaction](guide-apple-10.8/12-commands-and-gestures/interaction-commands.md)).
- Lire jusqu’à la fin de la page : VO-A ; adresse d’un lien : VO-Shift-U
  ([commandes web](guide-apple-10.8/12-commands-and-gestures/web-commands.md)).

## Mode démo

Le panneau de légende affiche ce que VoiceOver prononce (VO-Command-F10 le
masque ou l’affiche) : il aide le spectateur, il ne remplace pas la trace.
Vérifier que le rideau d’écran (VO-Shift-F11) est coupé avant une démo, sans le
modifier si la personne l’utilise.
