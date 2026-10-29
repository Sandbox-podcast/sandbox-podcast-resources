# Scénario, voix et reprises

Lire cette référence pour une histoire originale traitée par `storytelling-*`. Le [tutoriel du moteur](../../../../docs/factory/storytelling-generator.md) décrit les schémas et paramètres ; suivre le brief de Lou pour le sujet, le corpus narratif pour la méthode d'écriture.

## Produire le scénario et les fichiers

1. Créer le cadrage avec `storytelling-frame`, puis lancer `storytelling-run` sur le même état persistant.
2. Si le modèle local manque, lire le `request_path` exporté, traiter la demande avec les outils de la conversation et écrire le scénario intégral selon son schéma. L'importer avec `storytelling-script`. Faire relire sources et texte par un critique distinct si le workflow actif le demande.
3. Conserver identifiants, sources et voix du scénario. Enregistrer les fichiers reçus avant de continuer ; la copie de production doit résoudre les téléchargements en pistes locales mesurées. Une scène verrouillée protège également ses voix et médias.
4. Reprendre avec `storytelling-run` ou sa file durable. Vérifier MP4, sous-titres et manifeste, puis préciser les contrôles effectués. Une correction crée une version et recalcule ses dépendances.

Pour un documentaire autonome, conserver une vérification éditoriale distincte. Un compte rendu de contrôle technique ne la remplace pas.

## Utiliser ElevenLabs dans le navigateur

Lire cette section seulement si Lou a choisi ce mode. Respecter `budget.browser_credit_limit` et les demandes `storytelling_browser_request` du même Store. Le backend prépare les demandes ; une session Codex active pilote le navigateur intégré avec les outils de computer use.

Avant chaque clic de génération, appeler `record_attempt` avec l'estimation visible et une preuve du contexte. Après téléchargement, appeler `complete_request` avec le fichier exact et sa provenance, puis reprendre le même projet. Utiliser les fonctions du [module navigateur](../../../../tools/youtube-growth/src/youtube_growth/factory/storytelling_browser.py) selon leur contrat courant.

Une tentative `submitted` ou `unknown` exige de retrouver son résultat avant une autre soumission pour la même ancre. Ne pas contourner cette reprise par un nouveau texte ou une nouvelle version. Ne récupérer aucun cookie ou secret de session.
