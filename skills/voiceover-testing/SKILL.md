---
name: voiceover-testing
description: "VoiceOver réellement exécuté sur macOS : tester un site, un parcours web ou un document (PDF dans Aperçu, Word, PowerPoint) et relier chaque annonce native à un état et à une action, en démo visible ou en collecte tracée. Utiliser quand un test avec VoiceOver ou avec le lecteur d’écran du Mac est demandé. Pas pour une inspection DOM seule, un audit RGAA ni NVDA ou JAWS."
compatibility: "macOS avec VoiceOver ; python3 3.7 ou plus ; osascript ; autorisation Automatisation vers VoiceOver ; outil de pilotage du navigateur ou du bureau ; Aperçu, Word ou PowerPoint pour un document"
---

# Test VoiceOver natif

Promesse : chaque conclusion repose sur une annonce native horodatée, reliée à
un état et à une action, sur un canal vérifié. Le résultat peut être partiel ou
bloqué ; un DOM correct ne suffit pas à déclarer une annonce réussie.

Deux modes : **démo** (l’utilisateur regarde : montrer chaque étape à rythme
humain) et **collecte** (traces horodatées sans spectateur). Les deux exigent le
reçu de session, le canal vérifié et la matrice ; seule la mise en scène de
l’étape 6 change.

## Seuil et excuses interdites

Le skill s’applique dès qu’une annonce VoiceOver sert de preuve, même pour une
seule lecture : le reçu se réduit alors à ses champs obligatoires (cible,
allocations ou « aucune », état initial relevé ou inconnu, outil de pilotage,
accord cité si la ressource est préexistante), il ne disparaît pas. Cinq
éléments restent incompressibles, y compris en urgence ou en réponse courte :
reçu de session, accord réel cité avant tout pilotage, canal positif avant et
après, vérification de chaque restauration, absence qualifiée **non concluante**
sans preuve complète. Un code de sortie autre que 0 du pilote ou du collecteur
n’est jamais un succès.

- « Ce n’est qu’une lecture de `last phrase` » : elle lit la parole du lecteur,
  texte privé compris ; même garde que toute capture.
- « La fenêtre est déjà ouverte, je n’alloue rien » : une fenêtre, un onglet, un
  profil ou une session préexistants de l’utilisateur ne sont ni pilotés ni lus
  sans son accord explicite et nominatif ; sinon allouer une cible neuve.
- « Un `osascript` direct ira plus vite » : seul `scripts/pilot_voiceover.py`
  déplace le curseur VoiceOver, avec reçu, cible vérifiée et journal. Un geste
  déjà fait hors du script se signale à l’utilisateur, se rejoue par le script et
  ne sert pas de preuve.
- « L’accord est implicite, j’écris `recu.json` moi-même » : seule une phrase de
  l’utilisateur, citée mot pour mot, vaut accord. Une demande générale (« teste
  mon site ») ou l’accord d’un tiers n’en tient pas lieu ; sans citation, ne pas
  piloter et signaler le blocage.
- « Je reconstituerai l’état initial à la fin » : un réglage non relevé avant
  modification a un état initial **inconnu** (protocole natif), jamais supposé.
- « Livre maintenant, le nettoyage après » : restaurer chaque réglage modifié
  avant de livrer. Le nettoyage n’est en attente que si macOS exige une
  authentification (étape 9) ; tout autre blocage se signale à l’utilisateur en
  une phrase (réglage, valeur initiale, risque restant) et attend sa
  confirmation avant la livraison.
- « Le client attend un verdict » : sans canal de fin vérifié, sans matrice
  complète ou avec un nettoyage en attente, la conclusion s’écrit « partiel » ou
  « non concluant », jamais « réussi » ni « conforme ».

## Préparer

Avant toute allocation de navigateur, processus, onglet ou fenêtre, et avant
toute capture, lire [la garde de cible et de propriété](references/cible-et-propriete.md)
et ouvrir le reçu de session qu’elle exige.

1. Pour un document (PDF, Word, PowerPoint), lire d’abord
   [la cible document](references/documents.md) : reçu par fenêtre, repères
   observés dans Aperçu, limites. Relever la cible/version, le navigateur ou l’application choisis, macOS, la version, la langue
   et la verbosité de VoiceOver, le périmètre (page, parcours ou commandes de
   plusieurs états). Employer une session et des données isolées lorsque le
   parcours crée du contenu. Ne pas substituer un autre navigateur sans expliquer
   la différence de périmètre.
2. Lire [le protocole natif](references/protocole-natif.md) avant la collecte.
   Relever les réglages initiaux et les ressources possédées dans le reçu de
   session. Si VoiceOver est inactif, ne l’activer qu’avec l’accord explicite de
   l’utilisateur (raccourci natif Cmd+F5, ou en lui demandant de le faire) et
   consigner l’état initial « inactif » ; sans accord, consigner le blocage et ne
   rien collecter. Ce skill ne confère aucun droit système et ne permet pas de
   contourner un refus d’accès.
3. Inventorier les contrôles attendus **par état**, avant de compter les annonces :
   identifiant, rôle, nom attendu, état actif/désactivé. Inclure les dialogues,
   erreurs et panneaux pertinents au parcours demandé. Documenter les états non
   exercés. Une demande « tous les boutons » exige un dénominateur explicite ;
   ne pas s’arrêter au premier écran. Les statistiques VoiceOver (VO-Shift-I)
   et le rotor web (VO-U), gestes de la personne en démo, croisent cet inventaire sans
   le remplacer ([réglages et commandes](references/reglages-et-commandes.md)).

Préparation terminée quand la cible, l’inventaire et l’état initial sont consignés.

## Exécuter et tracer

4. Vérifier le canal avec une annonce positive provenant réellement du lecteur
   (navigation native ou témoin de test distinct de l’application). Vérifier de
   nouveau ce canal en fin de séquence. Une panne du canal rend les absences
   d’annonces **non concluantes**. Ne pas injecter les phrases attendues avec
   une commande de synthèse vocale : la trace prouverait la commande, pas le site.
   Critère de fin : deux annonces témoins horodatées, en début et en fin de
   séquence, figurent dans la trace.
5. Collecter la sortie native via `scripts/collect_voiceover.py` si AppleScript
   est disponible et autorisé ; sinon employer une capture native autorisée ou
   noter le blocage. Ce script lit seulement `content of last phrase`. Pour
   déplacer le curseur VoiceOver ou activer un élément, utiliser seulement
   `scripts/pilot_voiceover.py`, après l’accord de l’utilisateur cité dans
   `recu.json` (protocole natif, section « Piloter le curseur VoiceOver ») ; il
   revérifie avant chaque geste le titre et l’adresse de l’onglet (ou le titre de la fenêtre de document) au premier
   plan, n’active qu’un élément prouvé unique par `find`, et journalise chaque
   appel. S’il refuse (codes 5 et 8), la personne fait le geste et l’observation
   continue ; relire chaque annonce avant d’enchaîner. La collecte
   peut contenir du texte privé : limiter la cible et conserver les traces
   localement.
6. Exécuter le vrai parcours en montrant les étapes utiles si l’utilisateur
   regarde. Tester les noms des actions par tabulation et la navigation VoiceOver
   par titres, liens, régions et formulaires selon le périmètre : en démo, la
   personne fait les commandes de référence ; en collecte, seul
   `pilot_voiceover.py` parcourt et la navigation par catégorie est notée non
   exécutée. Le bon intitulé
   d’un bouton ne prouve pas que son action ou le retour de focus fonctionne.
   Relier état → action horodatée → annonce → effet visible. Utiliser des repères
   temporels et des phrases uniques pour distinguer une annonce fraîche d’une
   ancienne phrase répétée. Rafraîchir les repères UI après une mutation.
   Critère de fin : chaque contrôle de l’inventaire de l’état courant a une ligne
   état → action horodatée → annonce → effet, ou une raison de non-exécution.
7. Pour les messages dynamiques, exercer première apparition, remplacement et
   réapparition après effacement, plus un témoin négatif si l’environnement de
   test le permet. Exercer le chemin utilisateur réel ; une injection de messages
   en environnement isolé est une contre-épreuve séparée, explicitement qualifiée.

Exécution terminée quand chaque cas prévu a un résultat étayé ou une raison
explicite de non-exécution.

## Pièges

Lire [les pièges observés en essais réels](references/enseignements.md) devant
un déplacement de focus à prouver, une région live silencieuse, un arbre
d’automatisation incomplet, une recherche par sous-chaîne dans un journal
global ou un nettoyage bloqué par une
authentification système. Devant une annonce inattendue, une région live muette
ou un curseur qui saute, relire d’abord les réglages relevés dans le reçu : le
suivi des curseurs, les régions live et les indications après délai changent
la preuve. Le guide Apple d’origine (OS X 10.8, anglais) se lit par sujet
depuis [son index](references/guide-apple-10.8/index.md).

## Conclure et nettoyer

8. Produire un rapport et une matrice : état, contrôle/cas, action, résultat,
   annonce exacte, fichier et horodatage, limites. Séparer **nom vocalisé**,
   **action exercée**, **annonce dynamique**, **effet/focus vérifié** et
   **écoute humaine**. Une transcription native ne prouve pas la perception
   audio humaine. Compter les contrôles attendus par état, pas les lignes de log.
   Conserver les essais négatifs et les changements de méthode.
9. Arrêter uniquement les collecteurs/serveurs et fermer les onglets possédés,
   sauf livrable demandé ouvert. Restaurer selon le nettoyage vérifié du
   protocole natif. Si macOS exige une authentification, demander la prise en
   main et conserver le nettoyage **en attente**, même si les tests sont terminés.

Clôture : rapport livré, preuves conservées, couverture bornée et état du
nettoyage vérifié. Ne pas déduire une conformité RGAA/WCAG globale, une expérience
NVDA/JAWS ou une compatibilité d’un autre navigateur depuis ce seul test.

## Exemple

« Avec VoiceOver, crée un brouillon dans ce site, vérifie les commandes de
l’éditeur et des confirmations, puis exporte-le sans envoyer ni publier. »

Livrer le brouillon/export, les annonces avec leurs actions et la liste des
états non testés. Une correction produit, un commit ou une publication restent
une opération distincte qui dépend de la demande de l’utilisateur.

Extrait illustratif de trace pour l’état `editor`, puis la ligne de matrice qui
s’y rattache ; les valeurs ne sont pas des résultats attendus :

```text
{"kind": "phrase", "state": "editor", "source": "voiceover.native.last_phrase", "phrase": "Enregistrer, bouton", "timestamp": "2026-11-20T14:02:10.412000+00:00"}
{"kind": "stop", "state": "editor", "reason": "duration_elapsed", "phrase_count": 2, "timestamp": "2026-11-20T14:03:10.415000+00:00"}

editor | bouton Enregistrer | Tab puis Espace, 14:02:09Z | « Enregistrer, bouton » | message affiché, focus conservé | editor.jsonl, ligne 3 | écoute humaine non faite
```

## Checklist finale

Chaque point non vérifié arrête la conclusion et se signale `NON VÉRIFIÉ`, avec
sa raison.

- [ ] Reçu de session ouvert avant toute allocation ou capture ; état initial relevé, ou déclaré inconnu.
- [ ] Inventaire par état avec dénominateur explicite et états non exercés listés.
- [ ] Canal positif horodaté en début et en fin de séquence.
- [ ] Chaque ligne de matrice relie état, action horodatée, annonce exacte, effet et trace.
- [ ] Absences qualifiées non concluantes sauf preuve complète ; `phrase_count` relu.
- [ ] Curseur VoiceOver piloté seulement par `pilot_voiceover.py`, avec accord cité ; journal relu.
- [ ] Nettoyage vérifié réglage par réglage, ou en attente uniquement pour authentification macOS, signalé à l’utilisateur.
- [ ] Conclusion bornée au couple macOS, navigateur ou application et VoiceOver testé.
