# YouTube Trend Hunter SANDBOX

Le skill `sandbox-youtube-trend-hunter` recherche des sujets de vidéos françaises de deux à cinq minutes. Il collecte des signaux publics gratuits, conserve leurs dates et classe les opportunités suffisamment documentées. Les scripts et les médias restent locaux. Aucun compte social ne reçoit d'écriture.

Les huit skills du dépôt portent le préfixe `sandbox-`. Leur source est `.agents/skills/`. Les fichiers `.claude/skills/` sont de courts points d'entrée vers ces sources, sans copie de logique métier. `python tools/repository/sync_skills.py` vérifie les noms et ces liens ; `--write` régénère les points d'entrée après modification d'un nom ou d'une description.

## Installation et première collecte

Prérequis : Python 3.12+, FFmpeg avec le filtre `subtitles`, FFprobe. Le moteur de collecte utilise la bibliothèque standard. Pillow sert aux schémas PNG et `tzdata` fournit les fuseaux sur Windows.

Depuis la racine du dépôt, dans PowerShell :

```powershell
python -m venv .local/trend-hunter-venv
& ./.local/trend-hunter-venv/Scripts/python.exe -m pip install -r tools/youtube-growth/requirements-trend-hunter.txt
$env:PYTHONPATH = 'tools/youtube-growth/src'
& ./.local/trend-hunter-venv/Scripts/python.exe -m youtube_growth.trend_hunter doctor
& ./.local/trend-hunter-venv/Scripts/python.exe -m youtube_growth.trend_hunter analyze
```

Les exemples suivants utilisent `python` pour alléger les commandes. Active cet environnement ou remplace `python` par son chemin ci-dessus. Le rapport Markdown commence par le classement ; le JSON contient les mêmes preuves, les composantes du score, les statuts des sources et les rejets. Les sorties sont sous `.local/youtube-trend-hunter/reports/`. Le classement peut contenir moins de dix sujets, y compris zéro.

Dans Codex, invoque `$sandbox-youtube-trend-hunter`, puis précise éventuellement `general`, `ai-tech`, `prepare 1` ou `render 1`. Dans Claude Code, utilise `/sandbox-youtube-trend-hunter` avec les mêmes arguments. Le chargement du nouveau skill dépend du catalogue de la session ; recharge les skills ou redémarre le harnais s'il n'apparaît pas. La présence des fichiers ne prouve pas leur chargement dans une session déjà ouverte.

```powershell
python -m youtube_growth.trend_hunter general
python -m youtube_growth.trend_hunter ai-tech
python -m youtube_growth.trend_hunter demo
```

`demo` écrit dans `.local/youtube-trend-hunter-demo/`, avec des données explicitement synthétiques. Les états réel et démonstration sont séparés. La commande ne lance aucune tâche quotidienne. Tu peux relancer la veille chaque jour ; une automatisation future demande une instruction distincte.

## Configuration et clés facultatives

Les valeurs par défaut sont dans [config/youtube-trend-hunter.json](../../config/youtube-trend-hunter.json). Copie ce fichier dans `.local/` pour l'adapter :

```powershell
Copy-Item config/youtube-trend-hunter.json .local/trend-hunter-config.json
python -m youtube_growth.trend_hunter --config .local/trend-hunter-config.json analyze
```

Les paramètres placés avant la sous-commande sont `--config` et `--state-dir`. Le mode par défaut est `ai-tech` ; `general` retire le filtre lexical tech. Les catégories simples sont `ai-tech`, `general`, `sensitive`. La langue de rédaction prise en charge est `fr`. Les régions sont configurables ; les recherches YouTube comparent FR/fr et US/en. La difficulté est une estimation lexicale de 1 à 3, à revoir pendant la préparation. Les poids, la durée maximale, le seuil minimal de score, le nombre de recommandations et les budgets sont configurables.

`topic_aliases` associe un intitulé canonique à ses variantes, par exemple `{"OpenAI Codex": ["outil Codex", "Codex coding agent"]}`. Utilise des noms précis : un alias trop large fusionnerait des événements différents. Sans alias, le regroupement compare les mots des titres et peut manquer des équivalences entre anglais et français.

Les variables facultatives sont décrites dans [trend-hunter.env.example](trend-hunter.env.example). Le moteur ne charge pas automatiquement de fichier `.env` et n'affiche jamais les clés.

```powershell
$env:YOUTUBE_TREND_API_KEY = 'CLE_LOCALE'
python -m youtube_growth.trend_hunter analyze
```

La clé YouTube suffit pour les lectures publiques ; aucun OAuth n'est nécessaire. Active seulement YouTube Data API v3 dans un projet sans facturation supplémentaire. Le moteur n'active aucun service Google. Sans clé, Trends, News, Reddit et Hacker News continuent ; les statistiques vidéo et la concurrence restent absentes. Aucune API OpenAI, Anthropic, Apify, RapidAPI ou autre fournisseur payant n'est appelée.

## Sources et calculs

| Source | Lecture | Limite explicitée |
| --- | --- | --- |
| Google Trends | RSS officiel FR et US | Instantané courant ; le volume reste une indication textuelle telle que `20K+`. Aucun pourcentage inventé. |
| Google News | RSS par région, avec filtre IA/tech dans ce mode | Sert à confirmer un sujet ; les copies d'un même titre ne comptent pas comme plusieurs confirmations indépendantes. |
| Reddit | RSS public des communautés configurées | Les votes sont absents du RSS. Un refus 403/429 est consigné, sans contournement. |
| Hacker News | Recherche publique Algolia, publications récentes avec plus de 20 points | Échantillon tech ; points et commentaires sont horodatés. |
| YouTube | Data API v3 : search, videos, channels et playlistItems | Échantillons FR/EN, historique borné des uploads ; pas de scraping sans clé. |

Les autres sources optionnelles, dont GitHub et Wikipedia, ne sont pas ajoutées à cette version : les collecteurs ci-dessus couvrent déjà plusieurs signaux d'intérêt, et chaque source supplémentaire augmenterait les appels et le travail de rapprochement. Les connecteurs se désactivent indépendamment.

Les fenêtres 24h, 48h et 7j comptent les éléments publiés dans chaque période. Le programme accumule les observations au fil des exécutions. Le premier appel ne récupère pas sept jours complets de Trends à partir du seul RSS. Les éléments sans date de publication restent archivés et ne participent pas au classement courant.

La médiane de référence utilise au moins cinq vidéos longues de la même chaîne, observées à un âge comparable, avec une tolérance de 35 %. Sans échantillon suffisant, la surperformance reste `null`. Les vidéos de trois minutes ou moins restent dans `unknown_short_or_long`, car Data API n'indique pas leur orientation ni un statut Short fiable. Elles sont conservées séparément et ne servent pas de référence aux vidéos longues.

La moyenne des vues par heure divise les vues par l'âge de la vidéo. Une vitesse mesurée demande deux observations séparées d'au moins cinq minutes ; une accélération compare deux intervalles et demande trois observations. Un résultat de cache garde sa date d'origine et ne crée pas de nouvelle mesure.

Les poids initiaux sont 25/20/15/15/15/10 pour surperformance, croissance, confirmation, concurrence, production et pertinence française. Le score arrondi reste un outil de tri. Une composante absente apporte zéro point et les autres poids ne sont pas augmentés. Le rapport donne la couverture des critères. La croissance sans historique d'intervalles utilise la vitesse moyenne comme indice limité, sans l'appeler accélération. La confirmation compte les origines des signaux et écarte les titres manifestement syndiqués ; elle ne vérifie pas la vérité des nouvelles.

Google News seul ne suffit pas pour une recommandation. Le seuil initial est 25/100. Les sujets sensibles repérés par le filtre lexical sont exclus par défaut, mais ce filtre ne remplace pas la revue éditoriale. Le score de concurrence repose sur des vidéos longues dont la langue audio ou la langue déclarée est connue. `relevanceLanguage=fr` est une indication de recherche, pas une preuve de langue. Des langues inconnues ou une recherche absente laissent la concurrence non mesurée. Une faible concurrence sans indice français de demande ne rapporte aucun point.

Les sujets récemment proposés attendent 48 heures avant de revenir, sauf hausse d'au moins dix points. L'identité repose sur les mots du sujet ou son alias canonique ; des titres très reformulés peuvent échapper à cette déduplication. La confiance reste faible sans statistiques YouTube ; un classement issu du seul mode sans clé constitue une piste de recherche.

## Préparer une vidéo

Dans le chat, `prepare 1` demande à Codex ou Claude Code de réaliser la recherche et de rédiger le scénario avec l'abonnement existant. Le moteur Python fournit les fichiers et vérifie les contrats ; il ne se substitue pas au rédacteur par une API payante.

```powershell
python -m youtube_growth.trend_hunter prepare 1 --run IDENTIFIANT_ANALYSE
```

Cette première commande crée un dossier `research_required`, les fichiers attendus et `production-request.json`. Elle ne prétend pas avoir rédigé un scénario vérifié. L'agent lit les sources primaires, archive leur texte, documente les affirmations puis produit le JSON éditorial selon le [contrat du skill](../../.agents/skills/sandbox-youtube-trend-hunter/references/editorial.md). Le contrôle documentaire de la factory est réutilisé pour les citations et les empreintes.

```powershell
python -m youtube_growth.trend_hunter prepare 1 --run IDENTIFIANT_ANALYSE --editorial .local/mon-sujet/editorial.json
```

Le pack complet contient `research.md`, `script.md`, `storyboard.json`, `titles.md`, `thumbnail.md`, `description.md`, `assets/`, `attributions.md`, `audio/` et `render/`. Il passe à `ready_for_voice`. Chaque préparation crée une nouvelle version. Les visuels automatiques sont des cartes typographiques originales en SVG et PNG. Ils servent à une première version ; aucune photographie n'est téléchargée et aucune licence d'image n'est présumée.

Copie `script.md` dans ElevenLabs avec les limites de ton abonnement, puis importe le fichier obtenu :

```powershell
python -m youtube_growth.trend_hunter voice 1 --run IDENTIFIANT_ANALYSE --import C:/chemin/narration.mp3
# Si les repères ElevenLabs sont disponibles :
python -m youtube_growth.trend_hunter voice 1 --run IDENTIFIANT_ANALYSE --import C:/chemin/narration.mp3 --alignment C:/chemin/alignment.json
python -m youtube_growth.trend_hunter render 1 --run IDENTIFIANT_ANALYSE
```

L'export est en H.264/AAC 1920 × 1080. Il inclut fondus, mouvements légers et sous-titres. Avec un alignement ElevenLabs, les sous-titres utilisent les repères par caractère. Sinon, les temps suivent la proportion de mots ; il faut les corriger à l'écoute. Les durées des scènes restent estimées par proportion de mots dans les deux cas. La vidéo ne remplace jamais le MP3 ni un rendu précédent. Le reçu enregistre les empreintes, vérifie la résolution, l'audio, la durée et le décodage complet ; la revue audiovisuelle reste à réaliser.

### Génération API ElevenLabs facultative

Elle reste désactivée par défaut. Pour l'utiliser, active `elevenlabs.enabled`, configure une voix stock `premade` sans tarif personnalisé et définis `ELEVENLABS_API_KEY` dans la session. Demande ensuite explicitement :

```powershell
python -m youtube_growth.trend_hunter --config .local/trend-hunter-config.json voice 1 --generate --included-credits-only
```

Avant la synthèse, le moteur lit l'abonnement, le modèle disponible et les propriétés de la voix. Il exige un dépassement désactivé côté compte, un statut actif, des limites vérifiables et assez de crédits inclus. Il ne change aucun paramètre de facturation. Une information absente bloque la génération et laisse l'import manuel disponible. Il n'essaie aucun autre endpoint après un refus. Une tentative est enregistrée avant le POST ; un résultat incertain demande une réconciliation et ne relance pas automatiquement la consommation. Aucun appel ElevenLabs n'a lieu dans `analyze` ou `prepare`.

## Relevés après publication manuelle

`record-result` prend un JSON avec `run_id`, `topic_id`, `video_url`, `published_at`, `observed_at`, `views` et `evidence`. Ce dernier champ décrit la provenance du relevé. Les dates incluent leur fuseau. Le score initial est conservé avec la mesure ; les poids ne changent pas automatiquement.

```powershell
python -m youtube_growth.trend_hunter record-result .local/mes-resultats.json
python -m youtube_growth.trend_hunter results
```

## Quotas, conservation et contrôles

Documentation officielle vérifiée le 29 octobre 2026 : `search.list` dispose de son propre budget de 100 appels/jour à un point par appel. Les autres méthodes partagent 10 000 unités/jour ; les quatre lectures utilisées coûtent un point chacune. Les budgets locaux sont plus bas : 30 recherches et 500 unités. Le compteur réserve avant chaque tentative réseau, y compris échouée ; le cache évite une nouvelle réservation. Le jour de quota suit minuit Pacifique. Les compteurs locaux ne connaissent pas les appels faits par d'autres outils ou depuis un autre dossier d'état.

Le cache, les observations et les rapports de collecte conservent au plus trente jours dans l'état actif, avec purge au prochain `analyze`. Les vidéos suivies sont réactualisées dans la limite du budget et du nombre configuré. Les dossiers de production archivés sont des sources de travail figées ; leurs compteurs ne doivent pas être présentés comme actuels. Les relevés saisis par le propriétaire restent distincts des données API.

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
python -m unittest discover -s tools/youtube-growth/tests -p test_trend_hunter.py -v
python -m unittest discover -s tools/youtube-growth/tests -v
python tools/repository/sync_skills.py
python tools/repository/check_repository.py
```

Les tests utilisent des fixtures, dont une courte vidéo synthétique FFmpeg. Ils ne prouvent pas l'accès à un vrai compte YouTube ou ElevenLabs. Les sources indisponibles et les données manquantes apparaissent dans les rapports réels.

Références : [quotas YouTube](https://developers.google.com/youtube/data/determine_quota_cost), [recherche YouTube](https://developers.google.com/youtube/v3/docs/search/list), [Trends et export RSS](https://support.google.com/trends/answer/3076011?hl=en), [Algolia Hacker News](https://hn.algolia.com/api), [skills Claude Code](https://code.claude.com/docs/en/skills), [abonnement ElevenLabs](https://elevenlabs.io/docs/api-reference/user/subscription/get), [modèles](https://elevenlabs.io/docs/api-reference/models/list), [propriétés des voix](https://elevenlabs.io/docs/api-reference/voices/get), [synthèse avec repères](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps).
