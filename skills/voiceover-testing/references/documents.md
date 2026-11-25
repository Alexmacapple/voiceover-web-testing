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
« document groupe ». Word et PowerPoint n’ont pas été observés : leur reçu doit
déclarer `web_area_markers` (code 4 sinon), relevés au préalable à la main.

Pilote exécuté le 25 novembre 2026 dans Aperçu : `first` entre par « document
groupe » et se pose sur la page affichée (pas forcément la page 1) ; `next`,
`into` et `out` annoncent pages, titres et alternatives. Le terminal qui lance
le pilote reprend souvent le premier plan entre deux appels : la garde refuse
alors (code 5, aucun geste). Réactiver la fenêtre du document juste avant
chaque appel ; un `find` long peut être interrompu de la même façon.

Aucun repère de fin de document n’a été observé : `find` ne prouve donc pas
l’unicité et `activate` reste refusé (code 8), sauf `exit_markers` déclarés
après observation. Un document se lit ; activer un lien reste un geste humain.

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

## Ce que la recette ne prouve pas

Ni la conformité PDF/UA, ni le rendu d’un autre lecteur (NVDA, JAWS, Acrobat).
Elle prouve ce que VoiceOver annonce dans Aperçu pour les états exercés. Les
réglages d’Aperçu et la version de macOS changent la preuve : les relever.
