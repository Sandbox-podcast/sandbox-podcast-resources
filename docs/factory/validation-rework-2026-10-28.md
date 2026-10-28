# Validation du rework de la factory, 28 octobre 2026

## Périmètre

Les contrôles couvrent les révisions éditoriales, les reprises, le calendrier simulé, l'intégrité des sauvegardes et l'interface locale. La base affichée à l'adresse `http://127.0.0.1:8765/` reste `.local/factory-miniatures-validation-v2`. Ses médias et résultats sont synthétiques.

## Régressions couvertes

La suite finale du package a exécuté **208 tests en 126,810 secondes : 205 réussis et 3 tests PostgreSQL ignorés**, avec `FACTORY_MEDIA_INTEGRATION=1`. Le journal est conservé dans `.local/factory-rework-final-tests.txt`. La compilation Python et `git diff --check` passent également. Le worker Windows opérationnel a conservé un dernier résultat d'exécution égal à zéro pendant la vérification.

Commande exécutée depuis la racine, avec `PYTHONPATH=tools/youtube-growth/src` et `FACTORY_MEDIA_INTEGRATION=1` :

```powershell
& ./.local/factory-venv/Scripts/python.exe -m unittest discover -s tools/youtube-growth/tests -v
```

- Une sélection retirée, rejetée ou manquante bloque la préparation et l'envoi du pack concerné.
- Une nouvelle révision éditoriale invalide immédiatement les anciens packs ; une QA vidéo seule ne les réactive pas.
- Un job de rendu obsolète ne reproduit pas les anciens paramètres.
- Deux épisodes utilisant le même média conservent chacun leurs candidats et leurs rendus.
- Le plafond journalier tient compte des envois effectifs du compte, sur le jour Europe/Paris.
- Un blocage local connu conserve son motif ; le texte arbitraire d'une erreur de fournisseur n'est pas enregistré.
- Les miniatures, aperçus, briefs et reçus nécessaires sont présents dans l'inventaire portable. Une image altérée ou omise est refusée, y compris si son empreinte dans l'inventaire a été remplacée.
- Une revue de miniature persistée exige un responsable, une preuve et une date avec fuseau.
- Le diagnostic distingue l'horloge de recette d'un passage réel, rattache les fenêtres au bon épisode et filtre l'historique avant sa limite de cinquante événements.
- L'export respecte les filtres d'épisode et de plateforme. Les actions HTTP refusent un hôte ou une origine étrangers et les requêtes JSON mal formées.

La passe finale a également corrigé l'ordre de fermeture de SQLite : le serveur ferme la connexion avant d'envoyer l'état JSON. Un test de pack LinkedIn a été complété avec son candidat retenu, devenu obligatoire.

## Recette navigateur

Le test utilise une instance Chrome sans interface, indépendante du navigateur personnel, contre le serveur local réel. L'accès automatisé au navigateur intégré de Codex renvoyait `browser.user is unavailable` ; aucune vérification dans cet onglet n'est revendiquée.

Le script `tools/youtube-growth/scripts/test_factory_dashboard.cjs` a vérifié :

- Les six vues et leurs liens de navigation.
- La conservation du même lecteur pendant une lecture vidéo et une actualisation.
- La conservation d'un détail ouvert après actualisation.
- Le chargement effectif des trois miniatures.
- La restauration du filtre réseau et de la vue après rechargement de l'URL.
- La recherche sans résultat et le téléchargement du diagnostic.
- L'absence de débordement horizontal à 375 px dans chacune des six vues.
- Le maintien des dernières données et l'affichage d'une erreur après une panne réseau simulée.
- L'absence d'erreur JavaScript pendant ce parcours.

Les captures desktop, mobile et miniatures ont été examinées visuellement. Elles sont conservées dans `.local/factory-rework-desktop.png`, `.local/factory-rework-mobile.png` et `.local/factory-rework-thumbnails.png`. La recette ne remplace pas un test d'accessibilité complet avec lecteur d'écran.

Pour rejouer ce parcours, lancer le serveur sur la base de recette des miniatures, rendre le module Node `playwright` disponible, puis exécuter depuis la racine du dépôt :

```powershell
node tools/youtube-growth/scripts/test_factory_dashboard.cjs
```

Le script lit les données et télécharge le diagnostic. Il ne publie rien et ne modifie pas la file.

## Limites

Les tests PostgreSQL demandent une base dédiée absente sur ce poste. Les sauvegardes et médias testés sont des fixtures. L'analyse audiovisuelle autonome, les comptes sociaux réels et les performances d'un épisode réel restent à vérifier selon [l'audit](audit-rework-2026-10-28.md).

Aucun commit, push ou PR n'a été créé. Aucune mutation sociale n'a été exécutée.
