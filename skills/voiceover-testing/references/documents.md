# Documents : PDF dans Aperçu, Word et PowerPoint

Même protocole que pour le web : reçu, accord cité, canal positif avant et après,
matrice, nettoyage vérifié. Seule la cible change : une fenêtre de document
repérée par son titre, au lieu d’un onglet repéré par son titre et son adresse.

## Reçu du pilote

```json
{"accord": "citation exacte de l’accord", "app": "Preview", "marker": "recette-vo-7f3a"}
```

`app` remplace `browser` et `url_marker` (les deux formes sont exclusives) :
`Preview`, `Microsoft Word` ou `Microsoft PowerPoint`. `marker` (8 caractères au
moins) figure dans le titre de la fenêtre ; ouvrir une copie au nom unique pour
qu’il soit distinctif. Avant chaque geste, le pilote exige l’application au
premier plan, sa fenêtre de tête portant le marqueur, et aucune autre fenêtre de
cette application le portant (code 5 sinon).

Commandes utiles : `first` (entre dans le contenu), `next`, `prev`, `into`
(entrer dans une page ou un groupe), `out`. Repère d’entrée observé pour Aperçu :
« document groupe ». Pour Word et PowerPoint, le reçu doit déclarer
`web_area_markers` (code 4 sinon) : les repères relevés ci-dessous ne valent
que pour VoiceOver en français.

Pilote exécuté le 25 novembre 2026 dans Aperçu : `first` entre par « document
groupe » et se pose sur la page affichée (pas forcément la page 1) ; `next`,
`into` et `out` annoncent pages, titres et alternatives. Le terminal qui lance
le pilote reprend souvent le premier plan entre deux appels : la garde refuse
alors (code 5, aucun geste). Réactiver la fenêtre du document juste avant
chaque appel ; un `find` long peut être interrompu de la même façon.

Dans Aperçu, la fin du document est un silence : après la dernière page,
`next` ne produit aucune annonce nouvelle (code 7). Le parcours de `find` part
en outre de la page affichée : le 25 novembre 2026, lancé en page 8, il a
répondu « introuvable » pour le titre de la page 2. Sans `exit_markers`
déclarés, `find` est donc refusé d’emblée sur un document (code 8, aucun geste),
et `activate` aussi. Un document se lit ; activer un lien reste un geste humain.

## Aperçu : ce qui a été observé

Essai réel du 25 novembre 2026, macOS 26.5.2, VoiceOver 10, français, un PDF
remédié et son export d’origine comme témoin :

- Aperçu transmet la structure balisée : « Page 1 contenant niveau d’en-tête 1
  … », alternatives d’images suivies de « image », liens, listes (« Liste du
  contenu 2 éléments »), tableaux (« colonne 1, rang 1 »), signets dans la
  barre latérale.
- Le témoin non balisé perd ces informations de façon audible : titre sans
  niveau, « image » sans alternative, navigation par titres qui saute des pages.
- Le titre de fenêtre (VO+F2) annonce le nom du fichier : Aperçu n’exploite pas
  `DisplayDocTitle`. Le titre du document ne se vérifie pas ici.
- Chaque page est un élément : `into` pour lire son contenu, `out` pour revenir.

Gestes de la personne en démo, non pilotés par le script : VO+Cmd+H (titres),
VO+Cmd+L (liens), VO+Cmd+G (images), VO+Cmd+T (tableaux), VO+U (rotor).
VO+Cmd+Maj+H (titre précédent) n’a pas été confirmé lors de l’essai.

## Word et PowerPoint : repères relevés

Relevé du 26 novembre 2026, Mac Studio, macOS 27.0, Office 16.93, VoiceOver en
français, par exploration gardée (pas encore par le pilote) :

- Word : `web_area_markers: ["contenu de la page"]`. Le contenu est annoncé
  « Contenu de la page 1 page 1 sur 2 modifier le texte », suivi du texte ; pied
  de page et en-tête sont des éléments séparés. Fin de parcours : « page »
  répété, puis silence.
- PowerPoint : `web_area_markers: ["volet éditeur de diapositives"]`. Annonce
  « Volet Éditeur de diapositives, Diapositive 1 sur 21 zone de présentation » ;
  `into` donne « 4 éléments » puis titre, pied de page, numéro et date. Au
  dernier élément de la diapositive, `next` le répète au lieu de se taire ; le
  volet de notes se tait.
- Ouvrir le document peut faire surgir une boîte de récupération d’un autre
  fichier, ou une demande d’autorisation « sshd-keygen-wrapper » pour une
  session à distance : la garde de premier plan refuse alors, la personne y
  répond.

## Ce que la recette ne prouve pas

Ni la conformité PDF/UA, ni le rendu d’un autre lecteur (NVDA, JAWS, Acrobat).
Elle prouve ce que VoiceOver annonce dans Aperçu pour les états exercés. Les
réglages d’Aperçu et la version de macOS changent la preuve : les relever.
