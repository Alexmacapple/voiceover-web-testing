# Page de test de connexion : description et expression de besoin

Ce document décrit la page `demo/sign-in.html` et son serveur `demo/server.js`, assez précisément pour les recréer, puis exprime le besoin auquel ils répondent. Il est établi le 20 novembre 2026 à partir des fichiers du dossier et de l’essai réel du même jour.

## Description pour recréer la page

### But

Une page de connexion fictive, en français, sert de cible à un test VoiceOver. Elle a un comportement correct connu et un défaut connu, déclenchable sans modifier de fichier.

### Serveur

- Node 18 ou plus, sans dépendance, lancé par `node demo/server.js`.
- Écoute uniquement sur `127.0.0.1`, port 8765 ou celui de la variable `PORT`.
- `/` redirige vers `/sign-in` (code 302).
- `/sign-in` sert la page en GET comme en POST, pour qu’un envoi sans JavaScript réaffiche la page.
- `/assets/…` ne sert que des types connus (polices, SVG, CSS), sans sortie du dossier ; tout le reste répond 404 « Introuvable ».

### Structure de la page

- Langue `fr`, titre « Connexion - Service d’exemple ».
- En-tête avec le nom du service, « Service d’exemple », en lien vers `/sign-in`.
- Région principale `main` contenant, dans l’ordre :
  - un récapitulatif d’erreurs masqué au départ : un conteneur focalisable par script (`tabindex="-1"`) qui porte `role="alert"`, un titre de niveau 2 « Il y a un problème » et une liste vide ;
  - un titre de niveau 1 « Connexion » ;
  - un formulaire `novalidate` avec deux champs étiquetés : « Adresse électronique » (`type="email"`, `autocomplete="email"`) et « Mot de passe » (`type="password"`, `autocomplete="current-password"`) ;
  - pour chaque champ, un message d’erreur masqué, précédé du texte masqué visuellement « Erreur : » (« Saisissez votre adresse électronique », « Saisissez votre mot de passe ») ;
  - un bouton « Se connecter » ;
  - un panneau de succès masqué et focalisable : titre « Connexion réussie » et texte « L’exemple s’arrête ici. ».
- Focus visible sur tous les éléments, y compris le récapitulatif et le panneau de succès. Thème clair ou sombre selon le système. Aucune police externe ni logo.

### Comportement du script

À l’envoi du formulaire, le script empêche l’envoi réel, efface les erreurs précédentes, puis :

- si un champ est vide, il affiche son message, le relie au champ par `aria-describedby` et ajoute au récapitulatif un lien vers ce champ ; il affiche ensuite le récapitulatif et **y place le focus** ;
- si les deux champs sont remplis, il masque le formulaire, affiche le panneau de succès et y place le focus ;
- un lien du récapitulatif place le focus sur le champ qu’il désigne.

### Témoin négatif

Avec l’adresse `/sign-in?defaut=focus`, le récapitulatif s’affiche mais **le focus n’y est pas déplacé** : il reste sur le bouton. C’est le défaut connu, reproduit sans modifier la page.

## Expression de besoin

### Besoin

Qualifier un outil de test VoiceOver exige une cible dont on connaît à l’avance le bon et le mauvais résultat. Sans elle, on ne sait pas si un échec vient du site, de la capture ou de l’outil. La page fournit ce couple : un cas où le focus va sur le récapitulatif d’erreurs et un cas où il n’y va pas, avec les mêmes fichiers.

### Exigences

- **EP-01 Couple de témoins.** Fournir un cas correct et un cas défaillant distincts, sélectionnés par l’adresse seule.
- **EP-02 Comportement déterministe.** Aucune donnée distante, aucun état serveur, aucune temporisation : le même envoi produit toujours le même résultat.
- **EP-03 Accessibilité correcte hors défaut.** Champs étiquetés, erreurs reliées aux champs, récapitulatif titré, focus visible, langue déclarée.
- **EP-04 Confinement.** Écoute locale seulement, sans dépendance ni ressource externe, pour pouvoir tester hors réseau et sans exposer la page.
- **EP-05 Français.** Textes, langue et annonces attendues en français.
- **EP-06 Provenance tracée.** Page dérivée de celle de Craig Abbott, sous sa licence MIT conservée dans `demo/LICENSE`, avec les modifications listées dans le README.

### Critères d’acceptation

Vérifiés le 20 novembre 2026 :

- dans Chromium sans interface : formulaire vide, le focus arrive sur le récapitulatif ; avec `?defaut=focus`, il reste sur « Se connecter » ; formulaire rempli, il arrive sur « Connexion réussie » ;
- sur le serveur : écoute sur `127.0.0.1` seulement, 302 sur `/`, 200 sur `/sign-in` en GET et en POST, 404 sur les chemins inconnus et les tentatives de sortie du dossier `assets` ;
- avec VoiceOver réel (macOS 27, Safari 27, en français), un passage par cas : « Il y a un problème » est annoncé dans les deux cas, car le récapitulatif porte `role="alert"`. L’élément suivant distingue les cas : « liste 2 éléments » quand le focus est sur le récapitulatif, « fin de principal » quand il est resté sur le bouton.

Conséquence pour les tests : vérifier la position du curseur VoiceOver, pas seulement l’annonce.

## Variante DSFR

`demo/sign-in-dsfr.html`, servie sur `/sign-in-dsfr`, reprend la même page avec le Design System de l’État (DSFR 1.15.4), produite le 20 novembre 2026 par le Builder de la compétence `dsfr-components`.

- Source : tête, liens d’évitement, pied de page et scripts DSFR de `generate_page.py --type login --brand-mode neutral` ; en-tête neutre de `generate_component.py header`.
- Aide de format sur le champ « Adresse électronique » : « Format attendu : nom@example.com », texte d’aide repris du bloc `generate_field.py email` du Builder.
- Composition manuelle du contenu principal, avec des composants officiels : alerte d’erreur (récapitulatif), groupes de champs avec l’état `fr-input-group--error` et le message `fr-message--error` relié par `aria-describedby`, bouton, alerte de succès.
- Mode neutre : ni bloc marque « République française », ni Marianne en logo, ni FranceConnect. La page est inspirée des fondamentaux DSFR ; elle ne revendique aucune conformité.
- Mêmes témoins : `/sign-in-dsfr` (focus sur le récapitulatif) et `/sign-in-dsfr?defaut=focus` (focus resté sur le bouton).
- Le CSS et le JavaScript DSFR viennent du CDN jsdelivr : la variante exige un accès réseau, contrairement à la page d’origine.

### Vérification bornée

Statut : **écarts observés**, aucun bloquant, dans le périmètre lu (références `fields.md` et `alerts.md` du skill, sorties du Builder).

Vérifié :

- contrôles du Builder : `check_generated_outputs.py` PASS (12 pages, 137 composants), `check_golden_outputs.py` PASS (21 cas) ;
- inspection du HTML : aucun `href="#"`, cibles ARIA, labels et ancres présents, aucun identifiant en double, aucune contrainte `required` ou `aria-invalid` au repos, `lang="fr"`, `role="banner"` et `role="contentinfo"` ;
- dans Chromium sans interface : les trois comportements de la page d’origine, DSFR 1.15.4 chargé et démarré, aucune erreur de page ; rendu contrôlé en bureau et à 390 px de large ;
- focus au clavier : après un envoi par la touche Entrée, contour visible sur le récapitulatif, puis sur le premier lien d’erreur ;
- aide de format : le préaudit local AY11 (non décisionnel, test 11.10.5) détecte une indication de format sur `input#email` avec l’aide, aucune sans ;
- avec VoiceOver réel (macOS 27, Safari 27, en français), cas correct seulement : après l’envoi, l’élément suivant est « liste 2 éléments », donc le focus est sur le récapitulatif. La dernière phrase captée est le message du champ mot de passe (« Erreur : Saisissez votre mot de passe . »), émis par son groupe de messages `aria-live` : il recouvre l’annonce du récapitulatif dans la capture.

Écarts mineurs :

- après un envoi à la souris, le récapitulatif reçoit le focus sans contour visible : le DSFR ne trace le contour qu’au focus clavier (`:focus-visible`), alors que la page d’origine le traçait toujours ;
- le récapitulatif porte `role="alert"` alors qu’il est présent, masqué, dès le chargement ; la référence `alerts.md` réserve `role="alert"` aux alertes insérées après le chargement. L’annonce a fonctionné avec VoiceOver sur la page d’origine, de même structure ; sur la variante, la capture n’a retenu que le message du champ, donc l’annonce de l’alerte n’y est ni confirmée ni infirmée ;
- une liste à puces dans le corps de l’alerte n’est pas documentée par la référence lue ;
- le champ mot de passe utilise le composant de saisie standard, pas le composant mot de passe du DSFR (bouton « Afficher »), pour garder la même séquence de test que la page d’origine ;
- les liens du pied de page (plan du site, accessibilité, mentions légales, données personnelles, cookies) mènent à des pages non servies (404).

Non vérifié : cas défaillant avec VoiceOver (VoiceOver s’est arrêté pendant l’essai, erreur `-609`, sans trace de plantage), Google Chrome, mode sombre, contraste mesuré, script Playwright du skill.

### Limites

- Un seul état d’erreur est exercé : champs vides. Adresse mal formée et mot de passe incorrect ne sont pas simulés : la variante DSFR annonce le format attendu de l’adresse mais ne le contrôle pas.
- Les deux variantes ont le même titre d’onglet : un outil qui identifie l’onglet par son titre ne les distingue pas.
- La saisie automatique des mots de passe du navigateur peut préfixer les annonces (« Fermeture du menu Se connecter bouton »).
