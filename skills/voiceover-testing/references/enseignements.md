# Pièges observés en essais réels (octobre 2026)

## Région live vide puis alimentée

Dans un éditeur web testé, `role=status` et l’arbre DOM corrects ne suffisaient
pas : `.notice:empty { display:none }` faisait manquer la première annonce et
celle suivant un effacement. Le remplacement du contenu était pourtant annoncé.
Une correction CSS gardant la région rendue a permis de capturer les trois
transitions dans le couple macOS/Chrome/VoiceOver testé.

Leçon réutilisable : tester le cycle de vie complet, sans prescrire ce correctif
à tous les sites. Une région live vide peut être intentionnelle. Les contrôles
positifs et négatifs, l’implémentation et la combinaison lecteur/navigateur sont
nécessaires pour qualifier le cas.

## Couverture des actions

Une démo d’éditeur web a couvert 41 commandes de l’éditeur, 13 de l’accueil et
sept dialogues. Ces nombres décrivent ces états : ils ne certifient ni tous les
composants du catalogue ni tous les états d’erreur. Les suppressions annulées
prouvent les noms des commandes, pas le comportement après suppression.

Associer les preuves par **état + contrôle + action + intervalle**. Une recherche
par sous-chaîne dans un log global peut confondre « Copier » et « Copier quand
même », ou réutiliser l’annonce « Annuler » d’un autre dialogue. Les deux boutons
homonymes d’un état demandent une observation contextualisée, pas un seul match.

## Automatisation et démo

L’arbre d’automatisation Safari était partiel alors que la navigation VoiceOver
trouvait des champs. Le parcours a été poursuivi explicitement dans Chrome for
Testing : il ne constitue donc pas une qualification Safari.

Une longue marche de tabulation peut sortir du site vers la barre du navigateur.
Borner la navigation au périmètre, réobserver l’application active et arrêter
lorsqu’un cycle est atteint. Une commande VoiceOver non reconnue est une limite
de méthode à corriger, pas une défaillance du site.

Les longs essais ont aussi montré que le nettoyage peut rester bloqué sur une
authentification système après la fin des tests. Le succès fonctionnel et la
restauration de l’environnement sont deux résultats séparés.

## Déplacement du focus et alerte (novembre 2026)

Essai du pilote sur une page de connexion de démonstration, avec macOS 27,
Safari 27 et VoiceOver en français, un seul passage par cas.

Le récapitulatif d’erreurs portait `role="alert"`. VoiceOver annonçait « Il y a
un problème » après l’envoi du formulaire vide, que le focus aille sur le
récapitulatif ou reste sur le bouton. Seule l’annonce suivante a distingué les
deux cas : « liste 2 éléments » quand le curseur était dans le récapitulatif,
« fin de principal » quand il était resté sur le bouton. Pour un déplacement de
focus, vérifier la position du curseur par l’élément suivant, pas l’annonce seule.

La saisie automatique de Safari préfixe l’annonce de l’élément qui suit un champ
mot de passe : « Fermeture du menu Se connecter bouton ». Chercher le nom en mots
entiers plutôt qu’une égalité exacte.

Au premier appel AppleScript vers VoiceOver, une invite Automatisation encore
ouverte a fait expirer l’appel (`-1712`) ; l’appel suivant a réussi. En français,
VoiceOver annonce « Entrée … contenu web » à l’entrée de la page et « Pour sortir
de cette zone web, appuyez sur … » à sa sortie.

Sur la variante DSFR de la même page (même jour, Safari), chaque champ porte un
groupe de messages `aria-live="polite"`. Après l’envoi, la dernière phrase
captée était le message du champ (« Erreur : Saisissez votre mot de passe . »),
pas le titre de l’alerte : une région live voisine peut recouvrir l’annonce
attendue dans la capture. L’élément suivant, « liste 2 éléments », restait
discriminant. Pendant le même essai, une fenêtre de navigateur d’une autre
session est passée au premier plan : la garde de cible a refusé neuf appels
(code 5) au lieu de piloter cette fenêtre. VoiceOver s’est ensuite arrêté
(`-609`, puis code 3) sans trace de plantage ; le cas défaillant n’a pas abouti.
