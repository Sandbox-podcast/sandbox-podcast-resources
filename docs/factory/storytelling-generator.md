# Utiliser StoryTelling Generator

StoryTelling Generator prépare une vidéo narrative dans la factory SANDBOX : il conserve tes sources, le scénario, les voix, les plans et les versions du montage. Tu peux le piloter dans Codex et suivre l'histoire dans le tableau local. Les fichiers produits restent sur ton ordinateur, sous `.local/factory/`.

Pour une nouvelle vidéo dont le type, le sujet ou la voix restent à choisir, dis simplement « Je veux créer une nouvelle vidéo » : l'[onboarding vidéo](onboarding-video.md) pose les questions dans le chat, choisit les skills de chaque étape et pilote ce générateur jusqu'aux exports.

Dans un chat Codex ouvert sur ce dépôt, utilise le skill [`sandbox-storytelling-generator`](../../.agents/skills/sandbox-storytelling-generator/SKILL.md). Pour ouvrir l'interface :

```text
$sandbox-storytelling-generator Ouvre le générateur.
```

Codex vérifie l'état local et ouvre `/storytelling`, en lançant le serveur si nécessaire. Cette demande n'engage aucune production. Pour créer une vidéo, donne ton sujet, tes sources et le résultat attendu :

```text
$sandbox-storytelling-generator
Crée une vidéo sur [mon sujet] avec les fichiers joints.
Durée : [durée souhaitée]. Public : [public visé].
Utilise ElevenLabs dans le navigateur intégré pour le son.
```

Le skill prépare le cadrage, traite le scénario et conduit les étapes disponibles jusqu'au MP4. Il demande les choix déterminants manquants et respecte les plafonds définis pour cette histoire. Pour reprendre, indique l'histoire concernée et la correction souhaitée ; Codex retrouve ses versions dans le même état local.

Précise si tu veux un documentaire, une fiction ou un récit mêlant faits et reconstitutions. Ajoute la durée, le public et les éléments obligatoires si tu les connais. Codex peut préparer le scénario à partir de la requête de la factory, puis l'importer et poursuivre le parcours. L'accès à ElevenLabs dans le navigateur demande une session Codex active et un compte connecté.

## Ouvrir la factory

Prérequis : Python 3.12 ou supérieur, FFmpeg et ffprobe dans le `PATH`. Depuis la racine du dépôt, dans PowerShell, la première installation utilise :

```powershell
python -m venv .local/factory-venv
& ./.local/factory-venv/Scripts/python.exe -m pip install -r tools/youtube-growth/requirements.txt
```

Lance ensuite le tableau :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
& ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory serve
```

Ouvre [StoryTelling Generator](http://127.0.0.1:8765/storytelling). Le tableau principal de la factory donne accès à la même page.

Les travaux en file utilisent le worker existant. S'il n'est pas déjà lancé par la tâche Windows de la factory, ouvre un second terminal :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
& ./.local/factory-venv/Scripts/python.exe -m youtube_growth.factory worker
```

Le serveur affiche l'état ; le worker exécute les travaux locaux. La [documentation d'exploitation](exploitation.md) décrit l'installation du worker Windows, son diagnostic et ses conditions de fonctionnement.

## Parcourir les sept étapes

### 1. Sources et brief

Clique sur **Nouvelle histoire**, saisis ton sujet et ajoute tes notes, liens, documents et médias. Tu peux indiquer des chemins locaux ou importer des fichiers depuis la page. L'import depuis le navigateur accepte jusqu'à 10 Mio par fichier ; pour un média plus lourd, renseigne son chemin local.

Ajoute les éléments obligatoires, les exclusions et les références créatives. Déclare les droits des médias que tu fournis. Le programme crée des copies de travail et conserve leurs empreintes SHA‑256 pour retrouver chaque version sans remplacer l'original.

Les documents UTF‑8, DOCX et PDF textuels sont importés en texte. Le moteur PDF utilise `pypdf`, installé avec les dépendances de la factory. Un PDF scanné doit d'abord être transcrit ou traité par un outil OCR. Les liens doivent viser des pages HTTPS publiques accessibles sans exécution JavaScript. Si une page ne peut pas être lue, fournis une copie texte autorisée. Les sons et vidéos importés restent des médias : ce parcours ne les transcrit pas automatiquement.

Les textes importés servent de matière documentaire. Le modèle reçoit ces textes dans un champ de données distinct des règles de rédaction. Une instruction trouvée dans un document ne donne aucune permission au moteur de production.

Après avoir remplacé un fichier original au même emplacement, utilise **Réimporter les sources** pour créer une nouvelle révision. Une reprise normale réutilise les copies déjà enregistrées.

### 2. Cadrage

Choisis le type de récit et son autonomie. Le mode **Production autonome** enchaîne les étapes disponibles. Le mode **Valider scénario et storyboard** attend ta décision avant la production sonore et le rendu.

Renseigne le public, la durée, le format, le ton et le parcours sonore. Les propositions initiales sont : français, public curieux non spécialiste, vingt minutes, horizontal 16:9 et export 1080p. Tu peux conserver tes préférences pour les prochaines histoires.

Définis le plafond monétaire et sa devise. Un plafond de `0` autorise le travail local sans dépense. Pour **ElevenLabs dans le navigateur**, définis aussi un plafond de crédits à partir du compte connecté. Le programme suit ces crédits séparément des euros ; il n'invente aucune conversion entre les deux.

Enregistre le cadrage, puis clique sur **Lancer la production**. Les choix manquants et les blocages restent visibles dans l'histoire.

### 3. Scénario

Le scénario contient la question centrale, la réponse visée, la continuité et toutes les paroles. Chaque scène précise ce que le public comprend avant et après, les locuteurs, les sources ou son statut fictionnel, les plans et les intentions sonores.

Deux chemins de rédaction sont disponibles :

- Avec un modèle local configuré, le worker lui transmet la requête structurée, contrôle sa réponse et conserve la révision du scénario.
- Dans Codex, demande à l'agent de traiter la requête de rédaction exportée, puis d'importer le scénario complet. Tu peux aussi utiliser **Importer ou exporter un scénario JSON** dans la page.

Sans modèle configuré, la factory prépare la requête et attend une réponse. Elle conserve le blocage au lieu de remplir le récit avec un texte générique.

Le programme vérifie les champs requis, les références et les citations exactes dans les documents importés. Le statut `source_supported` signifie qu'une citation soutient le propos. Un statut `confirmed` demande une attestation déjà fournie avec les métadonnées de la source. Ces contrôles de structure ne remplacent pas l'examen des faits et des causalités.

Un documentaire autonome exige une critique éditoriale séparée du scénario. Si le modèle critique manque ou signale un défaut, l'histoire passe à **Vérification des sources attendue**. Configure ce contrôle ou choisis le mode avec validation éditoriale et examine les sources avant de poursuivre.

### 4. Storyboard

Examine les plans et leur fonction dans le récit. Chaque plan est lié aux répliques qu'il accompagne. Les textes affichés restent modifiables dans le scénario.

Le moteur local compose des schémas et utilise les images ou vidéos importées dont les droits sont renseignés. Une illustration générée ne peut pas être déclarée comme preuve. Les intentions de cadrage et de mouvement sont conservées ; le rendu actuel applique son habillage local et ses fondus. Un mouvement spécialisé absent du moteur demande une ressource préparée ou une adaptation du rendu.

### 5. Voix et son

Pour **ElevenLabs dans le navigateur**, Codex utilise le compte connecté dans le navigateur intégré. La page présente les demandes à produire, le texte oral et les paramètres à conserver avec les résultats. La factory ne stocke ni cookie de session ni mot de passe.

Avant chaque génération, Codex enregistre l'estimation de crédits et la preuve du contexte de soumission. La réservation utilise le plafond commun de l'histoire, y compris si plusieurs demandes sont préparées. Une tentative au résultat incertain reste réservée et bloque sa relance jusqu'à rapprochement avec le résultat réel.

Codex récupère le fichier terminé dans ElevenLabs, puis l'attache à sa demande avec sa provenance et le nom de la voix utilisée. La première réplique fixe la correspondance entre ce locuteur et sa voix ; les résultats suivants doivent conserver cette attribution. Une voix déjà nommée dans le cadrage doit correspondre à la sélection déclarée. Ce contrôle porte sur les informations fournies avec le fichier ; l'écoute reste nécessaire pour vérifier la voix réellement entendue.

La factory copie le fichier, contrôle son empreinte et mesure sa durée. Les textes longs passent par de courts segments ; le programme les assemble et conserve leurs bornes audio mesurées pour les sous-titres. Les noms des locuteurs et les consignes de montage restent hors du texte envoyé à la voix.

Les demandes musicales et les effets suivent le même parcours lorsqu'ils sont présents dans le scénario. Chaque ressource conserve son fichier et sa fonction. Le montage réduit le fond sonore sous les voix, ajoute des fondus et contrôle les crêtes.

Ce parcours navigateur s'arrête quand aucune session Codex ne peut effectuer les manipulations ElevenLabs. Le worker peut continuer les traitements locaux déjà prêts. Il reprend le montage lorsque tous les fichiers attendus sont disponibles.

Pour **Voice Studio**, le brief porte le profil choisi, son empreinte, le moteur et les réglages vérifiés pour la version installée. Le worker vérifie le service local (`voicestudio.base_url`, `http://127.0.0.1:3900` par défaut), le profil et le moteur, puis génère une prise par phrase et insère entre les phrases un silence mesuré. Les prises restent dans le cache local et sont réutilisées tant que le texte et la voix sont inchangés. Un réglage que le moteur n'applique pas, comme la vitesse avec VoxCPM2, est refusé au lieu d'être ignoré. La [référence voix](../../.agents/skills/sandbox-video-onboarding/references/voix.md) décrit le lancement du service, les réglages réels et les erreurs.

Quel que soit le fournisseur de voix, `delivery.pause_after_seconds` d'une réplique (0 à 10 s) ajoute un silence après cette réplique dans le montage ; les plans et les sous-titres suivent cette durée mesurée. Les autres intentions de `delivery` restent des indications d'écriture.

Les voix Windows et les enregistrements autorisés restent utilisables pour une production locale. L'intégration API serveur est une option distincte, désactivée dans la configuration livrée ; son installation et ses limites figurent dans le [guide sonore](elevenlabs-storytelling.md).

### 6. Production

La page montre l'étape en cours, les travaux et les blocages. **Interrompre** demande l'arrêt aux points de reprise entre les étapes ; une opération déjà envoyée à un fournisseur peut encore se terminer. **Annuler les travaux restants** conserve les fichiers et l'historique. **Reprendre** réutilise les ressources compatibles.

Si tu as choisi la validation éditoriale, relis le scénario et le storyboard, puis clique sur **Valider scénario et storyboard**. Cette décision porte sur cette révision. Une correction du scénario l'invalide.

Les montants engagés, les estimations et les coûts confirmés gardent leurs statuts. Un résultat produit ne constitue pas une facture confirmée. Pour le navigateur, le nombre réel de crédits reste inconnu tant qu'il n'a pas été observé et renseigné.

### 7. Vidéo et exports

La page donne accès à une prévisualisation et à l'export MP4. Le rendu final utilise H.264/AAC en 1920 × 1080 pour le paysage et 1080 × 1920 pour le portrait. Les sous-titres SRT et VTT, le scénario, les sources, les pistes sonores et la timeline restent disponibles avec le manifeste de production.

Les voix mesurées déterminent la durée et les positions finales. Les plans et sous-titres suivent cette horloge. Une durée souhaitée reste un objectif éditorial : si le texte déborde, révise le récit plutôt que d'accélérer artificiellement la voix.

L'état **Export terminé** confirme la production des fichiers et leurs contrôles techniques. Regarde et écoute la vidéo pour examiner les paroles, la lisibilité, le mix et le sens du montage. Les revues de contenu restent distinctes des contrôles de décodage. Aucune commande de ce parcours ne publie la vidéo sur un compte social.

## Corriger une histoire

Ouvre la scène, modifie le texte puis enregistre. La correction crée une nouvelle révision. La voix concernée et ses bornes doivent être recalculées ; les ressources indépendantes restent réutilisables. **Régénérer** demande une nouvelle version de la réplique, même si son texte est identique. Le parcours ElevenLabs demande alors une nouvelle soumission dans la limite de crédits autorisée.

Tu peux verrouiller une scène satisfaisante. Le verrou protège aussi ses dépendances, notamment sa voix et ses médias. Déverrouille-la avant de changer ces éléments. Une nouvelle soumission ne permet pas de contourner une ancienne tentative dont le résultat reste incertain.

Pour remplacer un visuel, importe le nouveau média, renseigne ses droits et affecte sa référence au plan dans le scénario. Codex peut effectuer cette correction ciblée depuis le chat. Le texte affiché, les répliques et les intentions sonores restent éditables après l'export.

## Commandes avancées

Les options globales `--config` et `--state-dir` précèdent la commande. Garde le même dossier d'état pour le serveur, le worker et les traitements d'une histoire.

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
python -m youtube_growth.factory storytelling-frame .local/mon-brief.json
python -m youtube_growth.factory storytelling-run mon-histoire
python -m youtube_growth.factory storytelling-script mon-histoire .local/mon-scenario.json
python -m youtube_growth.factory storytelling-run mon-histoire --queue
python -m youtube_growth.factory worker --once
```

Le cadrage accepte `"audio_workflow": "voicestudio"` avec un locuteur dont la voix a pour fournisseur `voicestudio` ; `video-onboarding frame` le prépare à partir du profil choisi. `voicestudio status`, `profiles` et `plan` lisent le service sans rien générer.

Le premier lancement sans modèle exporte la requête de rédaction. La commande `storytelling-script` importe la réponse contrôlée. Un passage `worker --once` traite un seul travail disponible ; le worker continu traite la file.

```powershell
python -m youtube_growth.factory storytelling-control mon-histoire pause
python -m youtube_growth.factory storytelling-control mon-histoire resume
python -m youtube_growth.factory storytelling-control mon-histoire approve
python -m youtube_growth.factory storytelling-control mon-histoire lock --scene-id ma-scene
python -m youtube_growth.factory storytelling-control mon-histoire unlock --scene-id ma-scene
```

`generation.local_command` dans la configuration de la factory désigne le modèle local. Cette commande reçoit un objet JSON sur l'entrée standard et répond par un objet JSON sur la sortie standard. Elle s'exécute sans shell ; `model_revision` entre dans les clés de réutilisation. Le chargeur actuel demande `network=false` et `cost_per_call=0`. Le [guide éditorial](production-editoriale.md#modèle-local-optionnel) décrit ce contrat.

Les formes du scénario et des demandes figurent dans [storytelling_contracts.py](../../tools/youtube-growth/src/youtube_growth/factory/storytelling_contracts.py) et [storytelling_editorial.py](../../tools/youtube-growth/src/youtube_growth/factory/storytelling_editorial.py). Les enregistrements et visuels y désignent des sources importées ; un scénario ne peut pas introduire une commande de montage ou un chemin à exécuter.

## Sauvegarder et restaurer

```powershell
python -m youtube_growth.factory backup .local/backups/avant-correction --include-media
python -m youtube_growth.factory --state-dir .local/factory-restauree restore .local/backups/avant-correction
```

Une sauvegarde avec `--include-media` conserve les fichiers enregistrés et les reçus avec la base. Une sauvegarde de base seule dépend encore des médias d'origine. La restauration utilise un dossier distinct et laisse les travaux en pause. Vérifie les fichiers et l'état de l'histoire avant de reprendre sa production.

Les identifiants de compte et les sessions de navigateur ne font pas partie de la sauvegarde. Une génération déjà soumise dont le résultat reste inconnu demande un rapprochement avant toute nouvelle soumission. Le [guide d'exploitation](exploitation.md#sauvegarde-restauration-et-limites-dactivation) détaille les règles de restauration de la factory.
