# SANDBOX YouTube Growth Agent

La [veille YouTube Trend Hunter](TREND-HUNTER.md) collecte les tendances publiques gratuites, produit un classement sourcé et prépare des vidéos locales de deux à cinq minutes. Son skill est `sandbox-youtube-trend-hunter`, disponible avec les autres skills `sandbox-` dans Codex et via les points d'entrée Claude Code.

Depuis le 28 octobre 2026, la factory persistante prolonge ces moteurs locaux. Commence par le [guide pour l'équipe](../../docs/factory/README.md) pour comprendre le parcours d'un épisode et les états du tableau, puis utilise les [commandes d'exploitation](../../docs/factory/exploitation.md). Les commandes historiques d'écriture (`apply --execute`, restauration réelle, commentaires, `--publish` et uploads privés) sont bloquées par une barrière commune, même avec OAuth. Les lectures et rendus locaux restent utilisables. Le [diagnostic](../../docs/factory/audit.md) et la [matrice des capacités](../../docs/factory/capacites.md) distinguent code, simulation et accès réels.

Depuis le 29 octobre, le [parcours éditorial multiformat](../../docs/factory/production-editoriale.md) étend ce moteur aux opportunités de veille, aux jugements éditoriaux sourcés, à la production narrative locale et aux comparaisons Analytics. La découverte par modèle est optionnelle et les sélections restent soumises à leurs preuves et revues.

Pour chaque nouvel épisode : [générer des Shorts adaptés à YouTube, TikTok, Instagram et X, puis des vidéos de 5 à 15 minutes](../social-network-manager/GENERER.md). La commande `youtube_growth.social` rend les variantes locales d'un plan relu ; `youtube_growth.thematic` prépare les formats horizontaux selon [son guide](THEMATIC.md). Ces deux commandes ne publient rien.

Outil Python pour [Sandbox TalkShow](https://www.youtube.com/@SandboxFR). Il complète le site existant sans modifier `old/`. Voir [ADR-0029](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0029-growth-agent-et-extraits-youtube.md), [ADR-0032](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0032-protections-et-persistance-issue-68.md) et [la livraison du 14 octobre](../../docs/site/history/2026/10/youtube-growth-2026-10-14.md).

Vidéos horizontales de 5 à 15 minutes : [commande indépendante, cache, exports et contrôles](THEMATIC.md). La [recette sur les deux épisodes](../../docs/site/history/2026/10/youtube-thematiques-2026-10-20.md) livre cinq vidéos locales, sans publication et avec les Shorts préservés.

## Connexion et audit

Python 3.12 minimum; FFmpeg et ffprobe pour les rendus. Depuis ce dossier :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m youtube_growth.cli doctor
```

Activer YouTube Data API v3 et YouTube Analytics API dans Google Cloud, puis préparer un client OAuth Desktop. Garder son JSON hors de Git.

```powershell
python -m youtube_growth.auth C:\chemin\client_secret.json
python -m youtube_growth.cli audit --video-id GgSiPkADCz4
```

Le jeton est enregistré dans `.local/youtube-token.json` après vérification de la chaîne `UCuATIBXo5uvNLVm-gCgMenA`. Une autre chaîne est refusée, même si le compte l'administre. Un navigateur connecté ne connecte pas le programme. `--token`, `YOUTUBE_LOCAL_TOKEN_PATH` et `YOUTUBE_OAUTH_TOKEN_JSON` permettent de choisir une autre source de credentials.

Le consentement initial demande `youtube.readonly` et `yt-analytics.readonly`. Après contrôle initial du pipeline, `auth --allow-writes` demande les droits d'édition et d'upload. La bibliothèque Google renouvelle les credentials; leur révocation est disponible dans les [connexions du compte Google](https://myaccount.google.com/connections).

`audit` collecte chaîne, vidéo, compteurs, uploads, playlists, sections, commentaires, pistes de sous-titres et quatre rapports Analytics. Les refus et absences de données sont explicites. Les impressions de miniatures, leur CTR et l'attribution Short vers émission demandent un relevé Studio. Les rapports bruts restent dans `.local/growth/audits/`, ignoré par Git. Ne pas publier ce dossier comme artefact public.

## Métadonnées et restauration

Préparer un JSON avec les propriétés voulues parmi `title`, `description` et `tags`, puis :

```powershell
python -m youtube_growth.cli plan --video-id GgSiPkADCz4 --patch .local/patch.json
python -m youtube_growth.cli apply .local/growth/metadata-plan.json
python -m youtube_growth.cli apply .local/growth/metadata-plan.json --execute
python -m youtube_growth.cli status
```

Sans `--execute`, `apply` simule. L'exécution préserve catégorie et langues, sauvegarde les métadonnées dans `.local/growth/backups/`, puis inscrit l'intention avant l'appel dans le journal configuré : Postgres distant ou SQLite local. Le journal conserve aussi les valeurs avant/après. Une modification faite depuis la préparation bloque le plan. Une réponse réseau perdue impose une vérification avant reprise. Aucune vidéo n'est supprimée.

`restore CHEMIN_SAUVEGARDE` simule une restauration; ajouter `--execute` pour l'appliquer. Les sauvegardes ne contiennent pas de jeton.

## Sans master

- Studio, "Extraits et Shorts" : nouvelles vidéos créées sur ses serveurs, selon l'éligibilité. Le 14 octobre, l'extrait horizontal était disponible pour l'épisode 1, mais "Nouveau Short" était désactivé.
- Application YouTube, "Remix", "Convertir en Short" : jusqu'à 60 secondes de sa propre vidéo publique, sous conditions.
- "Clip" sur la page de lecture : lien vers 5 à 60 secondes, sans nouvelle vidéo verticale.
- Studio, "Options", "Télécharger" : copie autorisée de sa propre vidéo pour le montage local. Sa résolution peut être inférieure au master.

Le programme n'appelle aucun endpoint privé et n'utilise pas de téléchargeur tiers. Exporter la transcription accessible depuis le navigateur, puis préparer les passages sans appel IA payant :

```powershell
python -m youtube_growth.cli --state-dir .local/episode-1 native-pack --transcript .local/transcript-youtube.txt --spec episodes/GgSiPkADCz4.json --duration 4701 --first "2026-10-15T17:00:00+02:00"
```

Le dossier contient huit candidats, les paroles brutes, leurs timestamps, quatre sélections et un calendrier proposé de trois publications par semaine. Aucune sélection n'est marquée publiée. Les fins des sous-titres sont inférées depuis le début suivant.

## Rendu local

Les dispositions `slide`, `panel` et `speaker` sont choisies dans `native-pack.json` après inspection des scènes. `fit` conserve le cadre complet. Ces cadrages sont vérifiés pour une source 1280 x 720. Ils ne constituent pas une détection automatique des intervenants.

```powershell
python -m youtube_growth.rendering --source "C:\chemin\copie-studio.mp4" --transcript .local/transcript-youtube.txt --pack .local/episode-1/native-pack.json --output .local/episode-1/shorts
```

Exports H.264/AAC en 1080 x 1920, sous-titres ASS, habillage bleu nuit/cyan et normalisation audio. Le fichier source reste intact. Chaque export est sondé puis décodé intégralement. Le manifeste conserve les empreintes et bornes, avec un statut de revue. Relire les sous-titres à l'écoute avant publication. L'export 1080p ne crée pas de détails supplémentaires dans la source 720p.

Le rendu refuse de remplacer un dossier dont un clip possède déjà un identifiant YouTube ou une tentative d'upload incertaine. Pour réviser un clip téléversé, choisir un nouveau dossier de rendu et conserver le manifeste précédent. Un rendu local ne met pas à jour une vidéo déjà présente sur YouTube.

Le pipeline historique `youtube_growth.shorts` reste disponible pour un nouveau master : transcription et sélection par OpenAI, facturées au compte API configuré. Aucun appel payant n'a été fait pour la sélection du premier épisode. Après génération et relecture, lancer `--approve`, puis `--publish` dans une commande distincte. La validation est liée aux médias et au texte. Un upload interrompu avec résultat incertain bloque la reprise au lieu de créer un doublon.

## Exécution manuelle à chaque épisode

Un épisode paraît chaque semaine. Lou a demandé le 18 octobre 2026 de supprimer le polling toutes les 30 minutes et de lancer le traitement manuellement à l'ajout d'un épisode. Voir [ADR-0033](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0033-optimisation-des-taches-planifiees.md).

Dans GitHub, ouvrir **Actions**, **YouTube SANDBOX**, puis **Run workflow** sur la branche par défaut. Le traitement est réservé à `workflow_dispatch`. Les tests Python continuent à chaque push et PR. Le premier passage initialise un curseur sans retraiter l'historique; `audit` peut viser explicitement le premier épisode. Il faut donc initialiser ce curseur avant l'épisode suivant pour que celui-ci soit détecté.

Le workflow vérifie sa configuration avant le checkout et l'installation. Sans OAuth, il signale un passage sans effet. Une demande d'écriture sans OAuth, sans journal Postgres ou sans validation initiale échoue. Les dépendances Python utilisent le cache pip. Le verrou du traitement est distinct de celui des tests.

Le polling refuse les écritures GitHub Actions sans `YOUTUBE_JOURNAL_DATABASE_URL` et sans `YOUTUBE_INITIAL_REVIEW_CONFIRMED=1`. Le journal Postgres conserve les intentions, résultats et curseurs entre deux runners. Le cache Actions ne sert jamais de garantie d'écriture. `YOUTUBE_POST_EPISODE_COMMENT` et `YOUTUBE_AUTO_REPLY` restent désactivés par défaut. Un commentaire de lancement doit être lié au contenu réel.

Avant une activation autorisée :

1. Sauvegarder la base cible et les anciens journaux SQLite. Vérifier la séparation Preview/Production, puis appliquer `sql/001_durable_journal.sql` dans la base choisie. Le programme ne crée aucune table automatiquement.
2. Préparer un rôle limité aux lectures et écritures des tables `youtube_operations` et `youtube_poll_state`. Configurer `YOUTUBE_JOURNAL_DATABASE_URL` avec une connexion Postgres directe et TLS (`sslmode=require` ou `verify-full`). Une URL Neon avec `-pooler` est refusée : le verrou du polling appartient à la session.
3. Réconcilier les anciennes opérations et les vidéos privées avec les journaux conservés. Une ligne `started` bloque toute reprise automatique ; vérifier le résultat dans YouTube avant de corriger son statut avec une preuve. Ne jamais effacer une intention pour forcer une nouvelle tentative.
4. Connecter OAuth à la chaîne attendue, contrôler la collecte réelle et exécuter le premier polling sans écriture. Après validation du contenu et accord du propriétaire, configurer les secrets et variables Actions, puis activer seulement les actions autorisées.

Les commentaires sont identifiés par chaîne et vidéo, les réponses par chaîne et commentaire parent, les uploads par chaîne, vidéo source et empreinte du média. Changer le texte généré ne crée pas une nouvelle autorisation d'écriture. Un verrou commun bloque deux pollings concurrents. Les tests Postgres couvrent ces reprises ; ils ne prouvent pas une connexion à la chaîne réelle.

Test natif, épinglage, podcast, Communauté, écrans de fin et vidéo associée gardent une tâche Studio. Les résultats d'un test viennent de Studio; une rotation séquentielle n'est pas un test contrôlé. Le petit échantillon de départ ne justifie pas un gagnant statistique.

```powershell
python -m unittest discover -s tests -v
```

Les trois tests Postgres nécessitent `YOUTUBE_TEST_DATABASE_URL` vers une base locale de test (`localhost` ou `127.0.0.1`). Ils créent puis retirent un schéma isolé. La CI fournit ce service ; sans URL locale, ces trois tests sont explicitement ignorés.

Références : [OAuth](https://developers.google.com/youtube/v3/guides/auth/installed-apps), [Analytics](https://developers.google.com/youtube/analytics/channel_reports), [extraits Studio](https://support.google.com/youtube/answer/15824265?hl=fr), [remix](https://support.google.com/youtube/answer/12836917?hl=fr), [téléchargement propriétaire](https://support.google.com/youtube/answer/56100?hl=fr), [tests natifs](https://support.google.com/youtube/answer/16391400?hl=fr).
