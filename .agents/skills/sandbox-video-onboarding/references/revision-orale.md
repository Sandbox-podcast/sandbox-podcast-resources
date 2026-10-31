# Révision pour l'oral

Les trois collections installées ne contiennent pas de skill « Spoken Script Editor ». Cette étape combine deux skills existants, un diagnostic automatique de la factory et la relecture ci-dessous. Elle intervient après la révision du français, sur le texte adapté au narrateur.

## 1. Diagnostic automatique

```powershell
& $py -m youtube_growth.factory video-onboarding spoken-check .local/video-onboarding/SESSION/texte.md --target-minutes 6
```

Le fichier peut être un texte (un paragraphe par réplique, titres `#` ignorés) ou un scénario StoryTelling en JSON. Le rapport compte les mots, estime la durée à 155 mots par minute et liste les points à reprendre :

| Code | Bloquant | Correction |
| --- | --- | --- |
| `digits` | oui | Écrire le nombre comme il se dit : « mille quatre cent quatre-vingt-huit », « en deux mille vingt-six », « le troisième ». |
| `symbols` | oui | Remplacer `%`, `€`, `/`, `&`, `+`, `°` par des mots. |
| `abbreviation` | oui | « etc. », « M. », « n° », « cf. » en toutes lettres. |
| `brackets` | oui | Une parenthèse ne s'entend pas : intégrer l'incise ou la supprimer. |
| `url` | oui | Retirer l'adresse ou la dire en mots. |
| `acronym` | non | Décider si le sigle s'épelle ou se lit, puis l'ajouter aux prononciations de la voix. |
| `long_sentence` | non | Couper une phrase de plus de 28 mots ; une respiration par idée. |
| `same_opening`, `repetition` | non | Varier les débuts de phrase et les mots répétés à courte distance, sauf effet voulu. |
| `dash` | non | Un tiret ne garantit pas une pause : virgule ou point. |
| `final_punctuation` | non | Terminer chaque réplique par une ponctuation. |
| `long_unit` | non | Découper une réplique de plus d'une minute. |

Le contrôle `spoken_report` de l'étape échoue tant qu'un code bloquant subsiste. Les autres points demandent un jugement : une répétition peut servir de refrain.

## 2. Réécriture pour l'oreille

Charger `teleprompter-script-writer` puis `voice-over-script-writer` (anglais) en leur donnant le texte existant à réécrire, la durée et le narrateur. Garder la langue française et les faits. Points à vérifier pour chaque réplique :

- le sujet et le verbe arrivent tôt ; pas de longue subordonnée avant l'information principale ;
- une seule information nouvelle par phrase, les chiffres arrondis quand la précision n'apporte rien à l'écoute ;
- les mots difficiles à enchaîner (consonnes groupées, homophones gênants) sont remplacés ;
- la ponctuation place les respirations là où le sens les demande ;
- le rythme suit le format : phrases plus longues et posées pour un documentaire, courtes et relancées pour un commentaire dynamique ;
- les noms propres et sigles ont une prononciation décidée (`--pronounce`).

## 3. Intentions et cohérence

Pour un scénario StoryTelling, renseigner `delivery` de chaque réplique (`emotion`, `pace`, `intensity`) de façon cohérente d'une scène à l'autre : la tension monte vers la révélation et retombe à la conclusion. Ces intentions guident l'écriture et la relecture ; Voice Studio ne les reçoit pas comme réglages (voir [voix.md](voix.md)). Seul `delivery.pause_after_seconds` agit sur le rendu : un silence après la réplique, utile avant une révélation ou un changement de scène. Avec VoxCPM2, ne pas renseigner `delivery.speed` : la factory refuserait la génération.

Relancer `spoken-check` sur la version finale, puis enregistrer l'étape avec ce fichier. L'écoute de la voix produite reste un contrôle humain de l'étape « Contrôles ».
