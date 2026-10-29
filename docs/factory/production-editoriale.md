# Production éditoriale multiformat

La factory conserve Python, SQLite, le worker et FFmpeg. Elle ajoute une découverte de sujets depuis la transcription, des évaluations éditoriales justifiées, une recherche documentaire archivée, des vidéos narratives locales et des comparaisons de performances. Le travail du 29 octobre 2026 est suivi dans l'[issue #10](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/10).

Toutes les commandes suivantes partent de la racine du dépôt. Activer l'environnement Python décrit dans [l'exploitation](exploitation.md), puis définir séparément :

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
$env:PYTHONUTF8 = '1'
python -m youtube_growth.factory doctor
```

Les médias, dossiers de recherche, réponses de modèles et reçus restent sous `.local/`. Aucune commande de cette page ne publie ni ne programme un contenu distant. LinkedIn reste manuel.

## Découvrir et évaluer les sujets

Après ingestion et analyse de l'épisode :

```powershell
python -m youtube_growth.factory discover episode-003
python -m youtube_growth.factory discover episode-003 --proposals .local/mes-propositions.json
python -m youtube_growth.factory editorial episode-003
python -m youtube_growth.factory editorial episode-003 --judgments .local/mes-jugements.json
```

Sans réponse fournie ni modèle local, `discover` écrit une requête contenant toute la transcription et indique le modèle manquant. `editorial` prépare les candidats avec leur contexte textuel et un contrat de réponse. Leurs sorties donnent le chemin du fichier à confier à l'agent. Ces exports permettent le travail avec Codex dans la conversation ; ils ne connectent pas le compte de la conversation au worker.

`discover --proposals` accepte des candidats avec titre, public, motif, angle, coupes et citation exacte de l'accroche avec ses secondes. Il vérifie les bornes et la présence des paroles dans le texte fourni. Il conserve ces propositions à part des sélections validées. Un modèle ne peut pas attribuer lui-même une revue audiovisuelle.

Les jugements portent sur dix critères : intérêt pour le public, originalité, pertinence temporelle, curiosité, potentiel narratif, effet concret, sources, accroche, apport de Sandbox et nouveauté par rapport à l'historique connu. Chaque critère demande une note sur 100, une raison et des références ou limites explicites. Le jugement cite aussi l'empreinte du candidat, son auteur et sa date, l'angle, l'accroche, le bénéfice pour le spectateur, un `topic_key` stable, le format et son motif. Le contrat complet est dans le `request.json` exporté.

Le score est la moyenne des dix notes. Le seuil configurable vaut 70 par défaut. Les blocages, l'expiration, les sources insuffisantes et les répétitions priment sur la moyenne. Les formats sont :

| Format | Durée finale admissible | Condition supplémentaire |
| --- | --- | --- |
| `short` | 15 à 90 secondes | Une idée autonome et une accroche dans les deux premières secondes. |
| `extract` | 180 à 900 secondes | Une discussion autonome, avec ses objections et réserves. |
| `narrative` | 180 à 600 secondes | Une nouvelle production, soumise à sa recherche et à son scénario. |
| `none` | Sans objet | Aucun contenu recommandé avec ces éléments. |

La durée d'une extraction est la somme de ses coupes, même si elles sont éloignées dans le master. Un format hors plage reste à retravailler ; le programme ne l'allonge pas. Aucun nombre de contenus n'est imposé. Une recommandation ne remplace ni la sélection ni la revue du montage. Les chiffres ne prédisent pas les vues.

Pour la veille, fournir un JSON `{"candidates": [...]}` dont chaque sujet contient au moins `title` et `source_urls`, puis :

```powershell
python -m youtube_growth.factory opportunities .local/veille.json
python -m youtube_growth.factory opportunities .local/veille.json --judgments .local/jugements-veille.json
```

Le dédoublonnage examine le sujet déclaré, la proximité des titres et le recouvrement des coupes d'un même master. Sa couverture se limite aux opportunités enregistrées ; il ne constitue pas une connaissance complète des contenus déjà publiés. Une réévaluation défavorable bloque les packs concernés. Le rendu, la planification et l'envoi simulé revérifient le jugement enregistré, son empreinte et son expiration.

## Modèle local optionnel

`generation` dans `config/factory.json` définit `local_command`, `model_revision`, `network`, `cost_per_call`, `timeout_seconds` et `auto_editorial`. La commande est une liste d'arguments, exécutée sans shell. Elle lit un objet JSON sur l'entrée standard et doit répondre par un objet JSON sur la sortie standard. Sa sortie d'erreur n'entre pas dans les événements de la factory.

Les seules configurations admises déclarent `network=false` et `cost_per_call=0`. Cette déclaration décrit le fournisseur choisi ; elle ne constitue pas une isolation réseau du système d'exploitation. La révision du modèle entre dans la clé de cache. Chaque appel conserve la requête et une réponse vérifiée par empreinte ; les contrats métier restent contrôlés après génération.

```powershell
python -m youtube_growth.factory discover episode-003 --generate
python -m youtube_growth.factory editorial episode-003 --generate
```

`auto_editorial=true` raccorde ces deux appels au traitement d'un épisode. Il reste désactivé dans la configuration livrée. Sans modèle installé, `--generate` indique `local_editorial_model_not_configured` et fournit la requête à traiter. Aucun service IA payant n'est activé et le fournisseur OpenAI historique des vidéos thématiques n'est pas appelé par ce parcours.

## Rechercher et vérifier

Le manifeste de sources contient `sources`, avec pour chaque document `source_id`, `title`, `url`, `kind` (`primary`, `secondary` ou `episode`) et `rights`. Une date de publication connue peut être fournie dans `published_at`, avec son fuseau. La collecte ne la déduit pas de sa propre date.

```powershell
python -m youtube_growth.factory research-fetch .local/sources-a-chercher.json
python -m youtube_growth.factory research .local/dossier-recherche.json
```

`research-fetch` lit les URL HTTPS fournies et archive le texte de chaque révision sous son empreinte. Il ne découvre pas seul les annonces sur le Web. L'agent de recherche choisit les URL et compare les documents ; ce choix peut être préparé avec les outils de recherche de la conversation. Les PDF et les pages qui exigent une exécution JavaScript doivent être importés en texte par un outil adapté.

Le dossier vérifié ajoute `snapshot`, `sha256` et `retrieved_at` aux sources. Il contient des `claims` avec identifiant, texte, nature (`fact`, `analysis`, `hypothesis`, `testimony`), références et vérification. Une référence cite `source_id` et `quote` ; la citation doit exister dans la copie archivée. La vérification `confirmed` demande `reviewer`, `checked_at` et `reason`. Un fait demande au moins une source primaire. `cross_check_required=true` exige deux documents distincts ; cela ne prouve pas leur indépendance éditoriale.

Une transcription automatique peut soutenir un témoignage avec `verification.status=transcript_supported`. Le programme autorise un brouillon en conservant `oral_verification_pending`. La validation finale attend une confirmation d'écoute documentée dans la recherche. Un fait insuffisamment confirmé bloque le scénario concerné. `expires_at`, s'il est fourni au dossier, bloque une recherche périmée. La présence d'une citation et d'une attestation ne constitue pas une vérification automatique de sa vérité : le responsable doit aussi examiner les dates, chiffres, contradictions et causalités.

## Écrire et produire une vidéo narrative

```powershell
python -m youtube_growth.factory draft-story .local/brief-narratif.json
python -m youtube_growth.factory draft-story .local/brief-narratif.json --generate
python -m youtube_growth.factory narrative .local/scenario.json --stage storyboard
python -m youtube_growth.factory narrative .local/scenario.json --stage voice
python -m youtube_growth.factory narrative .local/scenario.json
python -m youtube_growth.factory narrative .local/scenario.json --format vertical --draft
```

Le brief indique le sujet, l'angle, le public, le chemin `research` et la voix souhaitée. `draft-story` exporte le contrat complet ou appelle le modèle local configuré. Une réponse générée passe les mêmes contrôles qu'un scénario fourni par un agent. Le scénario comporte :

- `story_id`, `title`, `angle`, `audience`, `sandbox_analysis`, `research`, `voice` et, si le sujet vient d'un épisode, `episode_id` ;
- des scènes `beats`, chacune avec `beat_id`, `role`, `heading`, `narration`, `claim_ids`, `statement_kind` et `visual` ;
- `metadata`, avec trois titres, une description, des mots-clés et trois concepts de miniature motivés. Les concepts suivent l'ordre des titres ; `title_index` peut le préciser.

La première scène porte l'accroche et la dernière une conclusion concrète. Les étapes intermédiaires restent libres. Chaque scène cite les affirmations de la recherche. Le programme refuse de présenter une analyse ou un témoignage comme un fait confirmé. Cette vérification de structure ne remplace pas la relecture phrase par phrase du scénario.

Le storyboard prépare des schémas `flow`, `comparison`, `timeline` ou `cards` avec deux à quatre libellés. Le [guide de direction artistique](direction-artistique-narrative.md) décrit ces composants. Les personnages, illustrations générées, captures, musiques et bruitages tiers ne sont pas intégrés à cette première bibliothèque. Elle ne produit donc pas encore toute la variété d'un documentaire illustré.

La voix locale `system` utilise Windows `System.Speech` et un nom de voix standard installé. La recette de ce poste utilise `Microsoft Hortense Desktop`, en français. `cloned=false` et une justification `authorization` sont obligatoires. `rate` règle le débit de -5 à 5 ; `pronunciations` associe les termes techniques à des alias parlés. Les sous-titres conservent le texte original. Les phrases sont synthétisées séparément, puis assemblées avec une pause de 180 ms, pour obtenir leurs bornes audio. Il n'y a pas d'alignement mot à mot prétendument mesuré.

Sur un autre système, `voice.provider=recordings` importe des WAV autorisés. `voice.recordings` associe chaque `beat_id` à la liste des fichiers de ses phrases, avec `path` et `sha256`. Les fichiers doivent partager leurs paramètres PCM. Le débit et la durée sont mesurés ; une narration hors de 3 à 10 minutes est refusée, sans silence ajouté pour atteindre le minimum.

ElevenLabs reste une possibilité d'import de pistes produites séparément avec une voix autorisée. Aucun client ElevenLabs ni appel facturé n'est activé ici. Ses dictionnaires permettent notamment des alias de prononciation, avec des différences selon les modèles : consulter la [documentation officielle](https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/pronunciation-dictionaries) avant une future intégration.

Le rendu standard produit du H.264/AAC à 24 images/s, en 1280 × 720 ou 1080 × 1920. `--draft` produit une prévisualisation à 12 images/s, en 960 × 540 ou 540 × 960. Le portrait reconstruit la disposition des schémas ; il ne recadre pas le paysage. La sortie contient MP4, SRT, images d'inspection, reçus et contrôles. Les métadonnées ajoutent les principales sources et les chapitres. Les miniatures restent des concepts à produire et à examiner avec la [procédure existante](miniatures.md).

## Reprendre et valider

Les étapes `research`, `script`, `storyboard`, `voice`, `render` et `metadata` ont leurs reçus séparés. `--stage` réutilise les prérequis compatibles. Une correction de titre ou de ratio peut réutiliser la voix ; les sorties vidéo compatibles sont aussi réutilisées. Une modification des fichiers terminés bloque la reprise au lieu de les écraser. Les voix et les scènes restent dans les sauvegardes portables avec leurs sources documentaires.

```powershell
python -m youtube_growth.factory narrative .local/scenario.json --queue
python -m youtube_growth.factory worker --once
python -m youtube_growth.factory status --episode-id episode-003
```

`--queue` utilise le worker existant et ses réservations. Il conserve l'empreinte du scénario ; un fichier remplacé rend le job ancien sans objet. Les erreurs restent visibles dans les jobs et les reçus. Les montages narratifs ne créent aucun job social.

Après contrôle réel du contenu, des faits, de la voix et du packaging, `review-narrative` consigne le responsable et les preuves sur le `story_id:revision` visible dans l'état :

```powershell
python -m youtube_growth.factory review-narrative $recordId --reviewer $responsable --evidence $preuve --checks facts editorial visual audio subtitles packaging
```

Cette commande vérifie les empreintes, la présence des étapes et la validité actuelle de la recherche. Une reprise ciblée contrôle également les fichiers des étapes conservées avant de réutiliser leur approbation. Elle ne regarde ni n'écoute à la place du responsable. Elle n'autorise aucune publication distante. Les previews de recette du 29 octobre restent en attente de cette validation.

Les Shorts et extraits conservent leur montage FFmpeg et leurs sous-titres réutilisables. Les segments de sous-titres ont maintenant une animation d'entrée ; aucune précision mot à mot n'est inventée. Une réorganisation des coupes exige `edit_order_review` avec `reviewer`, `evidence`, `reason` et `preserves_meaning=true`. Les coupes restent distinctes, sans chevauchement, avec leur correspondance source/sortie. Une introduction contextuelle rédigée et la revue du sens restent des travaux éditoriaux ; elles ne sont pas déduites automatiquement des mots-clés.

## Réutiliser les observations Analytics

L'outil d'audit existant sait lire YouTube avec OAuth en lecture seule. Importer son JSON dans la factory :

```powershell
python -m youtube_growth.cli audit --video-id IDENTIFIANT
python -m youtube_growth.factory import-analytics .local/chemin/audit.json
python -m youtube_growth.factory learn --contexts .local/contextes-performances.json
python -m youtube_growth.factory brief --episode-id episode-003
```

La documentation [des métriques](https://developers.google.com/youtube/analytics/metrics) définit notamment durée moyenne, pourcentage moyen visionné et ratios de rétention. Les jours des rapports suivent le fuseau Pacific, avec ses changements d'heure, selon [les dimensions de l'API](https://developers.google.com/youtube/analytics/dimensions). L'import conserve ce fuseau et les positions de rétention ou sources de trafic séparées. Il ne somme pas les fenêtres et n'invente ni dénominateur ni mesure absente. `--fixture` marque une recette synthétique, exclue des recommandations réelles.

Le fichier de contexte contient `contents`, avec `entity_id`, `format` (`short`, `extract`, `narrative`), `duration_seconds`, `published_at`, `topic`, `hook`, `visual_style` et `provenance`. Les impressions sont des observations distinctes, sur la même entité, le même périmètre et la même période. Les définitions Studio doivent rester explicites lors de leur import avec `record --kind observation`.

`learn` compare uniquement des pairs compatibles : même plateforme, compte, métrique, définition, unité, dimensions et format ; rapport de durée au plus 1,3, d'ancienneté au plus 1,25 et d'impressions au plus 2 ; écart de longueur de période au plus une heure. Les contrôles s'appliquent entre tous les membres d'un groupe. Les médianes par sujet, accroche ou style sont descriptives, avec leur effectif. Un seul contenu ou des impressions manquantes ne donnent pas de classement comparable. Les conclusions alimentent les requêtes éditoriales et le brief, sans changer automatiquement les poids ni déclarer un effet causal.

Les impressions, le CTR des miniatures et les nouveaux spectateurs ne sont pas fournis par l'import des quatre rapports historiques. Un relevé Studio disponible reste nécessaire. Les tests natifs de titre et miniature continuent à utiliser le registre d'expériences existant ; leur lancement et leur résultat exigent l'éligibilité et les preuves Studio.
