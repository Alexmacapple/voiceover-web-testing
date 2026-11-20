# Cible et propriété avant chaque action

Termes : **recette** = exécution de test identifiée par un identifiant unique ;
**identité de naissance** = handle ou couple PID et heure de création observé au
lancement ; **marqueur** = valeur unique (titre ou fragment d’URL) chargée par la
première navigation de la ressource créée.

Ce garde est une consigne de workflow à vérifier par les traces ; il ne constitue
pas un verrou mécanique contre tous les outils.

## Allocations du reçu

Avant allocation ou capture, ouvrir le reçu de session
([protocole natif](protocole-natif.md#reçu-de-session)) et y inscrire, pour
chaque allocation : identifiant de recette, cible/version, ressource créée et
moyen de fermeture possédé. Le reçu distingue « non alloué » et « création
réussie » avec handle et identité observés.

- Navigateur neuf : handle du navigateur ou du contexte d’automatisation
  (Browser/BrowserContext), profil jetable, URL et marqueur.
- Processus lancé : handle enfant et identité de naissance ; un PID seul est
  insuffisant. Une application activée via `open -a` n’est pas nécessairement
  l’instance créée.

## Avant chaque action et capture

Amorcer le marqueur par la première navigation de la ressource créée. Avant
chaque action UI et capture vocale, vérifier application, fenêtre et marqueur de
la page possédée. La barre d’adresse, le terminal ou une autre fenêtre rendent la
mesure non concluante. Suspendre le collecteur avant de rechercher la cible ; ne
pas publier de texte hors cible comme preuve du site. Ne pas lancer de boucle de
navigation aveugle.

Le collecteur lit une phrase globale, quelle que soit l’application : aucune
collecte continue non surveillée ne satisfait la garde. Employer des captures
bornées vérifiées avant et après, ou une surveillance externe effective. Le
contenu privé du presse-papiers ou des fenêtres étrangères reste hors des preuves
publiques.

## Fermeture

Revalider l’identité, puis utiliser seulement le handle d’une ressource
enregistrée comme créée par la recette. Ne jamais fermer une application entière,
utiliser `close --all`, `pkill`, `killall` ou signaler un PID supposé possédé. Si
l’identité est perdue ou la fermeture échoue, consigner `cleanup_error` dans le
reçu, séparément du résultat applicatif ; ne pas élargir le nettoyage. Sans
allocation, aucune fermeture.

Distinguer abandon contrôlé et interruption brutale : si le processus hôte est
interrompu et que le nettoyage n’est pas observé, annoncer son état inconnu ; une
consigne dans le skill ne garantit pas l’exécution après interruption.

## Qualifier la garde

Créer intentionnellement deux ressources jetables, témoin et session : succès,
erreur et abandon ferment seulement la session, tandis que le témoin reste
utilisable. Aucune ressource réelle préexistante ne sert de victime d’essai.
