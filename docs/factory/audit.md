# Factory SANDBOX : diagnostic et décisions

Relevé du 28 octobre 2026, dans `sandbox-podcast-resources`. Le prompt maître fourni par Lou est conservé dans [sources/prompt-maitre-2026-10-28.txt](sources/prompt-maitre-2026-10-28.txt). Il prime sur les anciennes cadences et les anciennes autorisations de diffusion.

Empreinte SHA-256 de cette source : `893f37901e6009bc628cee93efcc1a81d9b714c6f2a818f0256a038da899272f`. La copie conserve le texte reçu ; les règles de ponctuation s'appliquent aux textes produits, sans réécrire cette pièce de provenance.

## Ce que le dépôt contient

`tools/youtube-growth` fournit déjà du Python pour l'audit YouTube, les métadonnées, un journal SQLite ou Postgres, la transcription optionnelle, les rendus FFmpeg et les extraits thématiques. `youtube_growth.social` produit les variantes locales d'un plan relu. `youtube_growth.thematic` conserve les preuves éditoriales, les coupes, les sous-titres et les empreintes. L'analyse locale de ce dernier utilise un vocabulaire limité ; elle ne prouve pas la compréhension de toute une émission.

`tools/social-network-manager` décrit le travail éditorial, les comptes connus, des routines et les compositions de l'épisode 2. Ces fichiers aident à produire et à préparer les posts. Ils n'exécutent pas à eux seuls une chaîne autonome. Le workflow YouTube utilise `workflow_dispatch`. Les workflows de contrôle exécutent les tests ; leurs runners ne conservent pas l'état de la factory.

L'état Git était propre au début du travail. Python 3.14, FFmpeg, FFprobe, Node et Docker sont présents sur la machine inspectée. Aucun master complet d'émission n'a été trouvé dans ce clone, qui contient notamment quatre Shorts E01. Les anciens chemins de masters et transcriptions sous `C:/github/sandbox-podcast/exports/` ont aussi été contrôlés et sont absents. La recette intégrée utilise donc une fixture signalée comme synthétique. Elle ne valide ni l'analyse ni le montage éditorial de 60 à 120 minutes de conversation réelle.

## Décisions de reprise

| Élément | Décision | Motif |
| --- | --- | --- |
| Package Python `youtube_growth` et dépendances existantes | Conserver | Éviter une application concurrente et garder les commandes actuelles. |
| Rendus FFmpeg, calculs d'empreinte et fichiers de sous-titres | Réutiliser et étendre | Les médias restent locaux ; les coupes multiples et la reprise doivent garder leur provenance. |
| Journaux YouTube historiques et données de diffusion E02 | Conserver | Une ancienne réservation ou publication ne doit jamais devenir un nouvel envoi. |
| Agent social écrit et scripts indépendants | Compléter | Ajouter un état d'exécution durable, des commandes et un worker. |
| Cadences de plusieurs posts quotidiens et sélection attendue de trente extraits | Remplacer pour les nouveaux cycles | Le prompt du 28 octobre exige une sélection sans quota et une fenêtre qui finit au prochain tournage. |
| API YouTube existante | Conserver, avec écritures désactivées | Les lectures et mutations doivent garder des contrôles distincts. La simulation couvre aussi les anciens chemins d'écriture. |
| Automatisations Codex sociales | Laisser en pause | La factory doit exécuter ses jobs sans conversation ouverte et éviter deux ordonnanceurs de diffusion. |
| Assets `brand/` et compositions vidéo existantes | Conserver | Employer l'identité Sandbox et les vrais médias autorisés. |
| Archive `old/` et site web | Conserver hors périmètre | Leurs contenus et leurs responsabilités restent dans leurs emplacements actuels. |

Aucun déplacement global n'est nécessaire. La factory est un module de l'outil Python existant. Sa configuration est versionnée ; sa base, ses médias et ses reçus d'exécution restent dans un stockage local durable ignoré par Git. La base porte l'état courant. Les manifestes d'entrée et les reçus servent de provenance et d'export, sans devenir une deuxième file modifiable.

## Ordonnanceurs et reprise de l'historique

Le contrôle local a trouvé six automations SANDBOX, toutes en pause : contrôle et bilan sociaux, confirmation et publication Meta, reprise TikTok, suivi des classements. Aucune tâche Windows nommée Sandbox ou YouTube n'a été retournée lors du premier contrôle. Ce relevé ne prouve pas l'absence de réservations natives dans les plateformes.

L'archive E02 conserve 114 réservations et six publications historiques. Ces lignes ne sont pas importées comme de nouveaux travaux. Avant toute activation réelle future, réconcilier leurs identifiants et les opérations incertaines avec les plateformes. Laisser les anciennes routines en pause, puis désigner un seul propriétaire de diffusion par compte. La simulation de la nouvelle factory n'envoie rien aux comptes.

Le [manifeste des extraits A/B/C du 26 octobre](../../.local/legacy/exports/reseaux-sociaux/extraits-abc-2026-10-26/manifest.json) conserve cinq tests observés en cours dans Studio : Sillage, Harnais, Legacy, Artisans et Tickets. Ce relevé historique ne prouve pas leur état au 28 octobre. Les préserver et recontrôler leur résultat dans Studio avant de modifier leurs titres ou miniatures. La fermeture d'un cycle de nouveaux posts ne les arrête pas.

## Limites du premier périmètre

Les adaptateurs de simulation valident le calendrier, les reprises, les erreurs et la traçabilité. Ils ne prouvent aucun accès social. Les identifiants de compte connus dans les anciens documents sont des références à revalider. Les capacités et les actions humaines sont décrites dans [capacites.md](capacites.md). Les appels IA payants et les écritures réelles restent désactivés. Un vrai master, une transcription exploitable et une revue audiovisuelle restent nécessaires pour certifier le traitement éditorial d'un épisode.
