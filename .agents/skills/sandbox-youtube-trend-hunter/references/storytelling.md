# Passer d'une tendance choisie à StoryTelling

Le parcours attendu est : liste de tendances, choix de Lou dans le chat, dossier d'entrée pour StoryTelling Generator. Le format cible est celui de [`storytelling.frame` dans la PR #19](https://github.com/Sandbox-podcast/sandbox-podcast-resources/blob/2e0266f522530174f618641425a8f10b63722c7c/tools/youtube-growth/src/youtube_growth/factory/storytelling.py). Il reçoit un brief avant de rédiger son propre scénario.

## Préparer le dossier après le choix

1. Retrouver le `run_id`, le rang et le `topic_id` du rapport montré à Lou. Conserver les mots du choix dans `--selection-note` et le responsable réel dans `--selected-by`. Une nouvelle collecte ne remplace pas ce choix. Si la collecte est périmée, actualiser ses preuves et garder la provenance du sujet choisi.
2. Lire les sources primaires utiles avec les outils de la conversation. Archiver leurs textes dans `.local/`, relever leurs dates et vérifier les affirmations retenues. Préparer le dossier de recherche v1 de `youtube_growth.factory.research` : sources avec `snapshot`, `sha256`, `kind`, `rights`, `retrieved_at` ; affirmations avec références exactes et vérification documentée. Le [contrat éditorial](editorial.md) donne ce format. Réutiliser `research-fetch` pour des URL explicites accessibles, puis compléter la vérification sans inventer de revue humaine.
3. Exécuter le transfert, sans écrire le scénario complet ni produire de voix :

```powershell
python -m youtube_growth.trend_hunter storytelling RANG --run IDENTIFIANT --selected-by Lou --selection-note "Choix exprimé dans la conversation" --research-dossier .local/mon-sujet/recherche.json --angle "Angle proposé et soutenu par les sources"
```

Le résultat `ready_for_storytelling_framing` signifie que le dossier documentaire est fourni, pas que le film est validé. Sans recherche primaire, le transfert reste `research_required`. Une reprise identique réutilise ses fichiers ; une modification du cadrage crée une nouvelle version avec le même `story_id`. Les empreintes empêchent de réutiliser silencieusement un transfert modifié.

## Ce que reçoit le générateur

`storytelling-brief.json` porte le sujet, l'angle dans les notes, les obligations et exclusions, le public, la durée, le format, le ton, les documents et `source_metadata` indexé par leur chemin local. Le moteur cible calcule ses `source_id` à partir de ces chemins : `source-map.json` et `research-facts.json` utilisent déjà ces identifiants pour les citations.

Les observations de veille restent dans `trend-evidence.json`. Elles décrivent l'intérêt, le score, les vidéos et les limites ; elles ne deviennent pas des faits confirmés du récit. Les textes primaires sont copiés séparément dans `sources/`. Les citations soutenues portent `source_supported` ; aucune attestation `confirmed` n'est fabriquée pour le scénario. Les URL originales restent dans le dossier sans imposer une nouvelle lecture réseau à l'import.

Les valeurs proposées sont documentaire, validation éditoriale, français, durée de deux à cinq minutes issue du Trend Hunter, 16:9 et 1080p. Elles remplacent notamment la durée de vingt minutes par défaut de la PR #19. Le budget monétaire reste à zéro. Le parcours sonore utilise ElevenLabs dans le navigateur avec zéro crédit autorisé tant qu'un plafond n'a pas été donné. Ajouter `--voice-name` et `--browser-credit-limit` seulement pour reprendre des choix effectivement exprimés par Lou. Les choix non faits restent dans `remaining_decisions`.

## Livrer puis passer le relais

Fournir à Lou le sujet choisi, le dossier, le chemin du brief et les réserves encore utiles. Expliquer qu'il peut donner ce dossier à StoryTelling. Ne pas lui demander de recopier les sources ou de remplir les fichiers déjà produits.

Si Lou demande aussi de démarrer StoryTelling et que la PR #19 est installée, importer `storytelling-brief.json` avec `python -m youtube_growth.factory storytelling-frame CHEMIN_BRIEF`, puis poursuivre le `story_id` retourné selon le parcours du générateur, dans le même état factory. Une validation du sujet seule ne déclenche pas ce lancement. Ne pas confondre le JSON de scénario historique du Trend Hunter avec celui de StoryTelling.
