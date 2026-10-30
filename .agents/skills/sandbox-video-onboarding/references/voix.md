# Narrateur et interprétation avec Voice Studio

Voice Studio est installé sur chaque poste, hors de Git. Sur le poste de Lou, l'installation et son README se trouvent dans `.local/voicestudio/` du checkout principal. La factory n'interroge que son API locale, `http://127.0.0.1:3900` par défaut (`voicestudio.base_url` dans `config/factory.json`).

## Vérifier le service

```powershell
& $py -m youtube_growth.factory voicestudio status
```

La réponse donne la version, le périphérique, les profils, les moteurs disponibles, les traitements audio et les réglages vérifiés pour chaque moteur. Elle ne contient ni le texte de référence des profils ni leurs chemins.

Si le statut est `unavailable`, vérifier d'abord qu'aucun autre travail n'utilise ou n'arrête le service. Deux façons de le lancer :

- l'application, avec `Ouvrir-VoiceStudio.cmd` dans le dossier d'installation ;
- le backend seul, dans une fenêtre masquée avec des journaux locaux, depuis PowerShell :

```powershell
$vs = 'CHEMIN\DU\CHECKOUT\.local\voicestudio'   # dossier d'installation sur ce poste
$env:OMNIVOICE_DATA_DIR = Join-Path $vs 'data'
$env:OMNIVOICE_CACHE_DIR = Join-Path $vs 'models'
$env:OMNIVOICE_ENGINES_DIR = Join-Path $vs 'engines'
$runtime = Join-Path $vs 'desktop/runtime'
$python = Join-Path $runtime '.python/cpython-3.11-windows-x86_64-none/python.exe'   # vérifier ce chemin après une mise à jour
Start-Process $python -ArgumentList '-m','uvicorn','main:app','--app-dir','backend','--host','127.0.0.1','--port','3900' `
  -WorkingDirectory (Join-Path $runtime 'project') -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $vs 'backend.out.log') -RedirectStandardError (Join-Path $vs 'backend.err.log')
```

Attendre que `/health` réponde avant de continuer. Ne pas arrêter le service à la fin si quelqu'un d'autre s'en sert.

## Choisir la voix

Présenter à Lou les profils renvoyés par `voicestudio profiles` : nom, langue, consentement et moteurs utilisables. La liste est lue à chaque fois ; un profil ajouté par un autre membre apparaît sans changement de code.

| Consentement | Signification | Conduite |
| --- | --- | --- |
| `own_voice_attested` | La personne a attesté dans Voice Studio qu'il s'agit de sa voix. | Utilisable après le choix de Lou. |
| `demo_voice` | Voix de démonstration fournie avec Voice Studio, en anglais. | Réservée aux essais. |
| `declared_…` | Une base de consentement est déclarée sans attestation datée. | Faire confirmer l'autorisation par la personne concernée. |
| `not_recorded` | Aucun consentement enregistré. | `--authorization` obligatoire, avec l'accord écrit de la personne. |

Cette procédure ne crée et ne clone aucun profil. Pour ajouter la voix d'un membre, la personne l'enregistre elle-même dans Voice Studio.

```powershell
& $py -m youtube_growth.factory video-onboarding voice SESSION --profile f92d4b17 --confirmation "Prends ma voix pour celle-ci"
```

Le moteur actif est retenu s'il convient au profil ; `--engine` en impose un autre parmi `usable_engines`. La factory fixe dans le projet le profil, son empreinte, le moteur, la version de Voice Studio et les réglages. Si le profil change ensuite dans Voice Studio (nouvel enregistrement de référence), la production s'arrête sur `voicestudio_profile_changed_select_again` : refaire le choix avec Lou.

## Identité, direction et traitement

| Couche | Ce qui la règle | Exemple |
| --- | --- | --- |
| Identité vocale | Profil, moteur, langue, graine | Lou, VoxCPM2, français, graine 42 |
| Direction d'interprétation | Le texte lui-même ; la consigne `instruct` seulement si le moteur l'applique | Phrases courtes au présent pour un commentaire de match |
| Traitement audio | `effect_preset`, appliqué après la synthèse | `broadcast`, `podcast`, `cinematic`, `warm`, `bright`, `raw` |

Un traitement audio change le timbre perçu (égalisation, compression, réverbération), jamais la prosodie. Ne pas le présenter comme un réglage d'interprétation.

## Réglages vérifiés dans Voice Studio 0.5.7

L'API annonce les moteurs, pas les champs que chaque moteur applique vraiment. Ces lignes viennent de la lecture du code 0.5.7 et figurent dans `VERIFIED_CONTROLS` de [voicestudio.py](../../../../tools/youtube-growth/src/youtube_growth/factory/voicestudio.py).

| Moteur | `speed` | `instruct` | Remarque |
| --- | --- | --- | --- |
| `voxcpm2` | ignoré | consigne libre placée avant le texte | Avec un profil cloné, une consigne remplace la continuation sur la référence par un clonage contrôlé : la ressemblance peut baisser. Sortie 48 kHz. |
| `omnivoice`, `omnivoice-subprocess` | appliqué | vocabulaire fermé de conception de voix | Les étiquettes décrivent le timbre (genre, âge, hauteur, accent), pas le jeu. |
| `kittentts` | appliqué | ignorée | Anglais, voix préréglées, pas de clonage. |

Le moteur IndexTTS2, seul à accepter des contrôles d'émotion, n'est pas installé. Pour une autre version de Voice Studio, la factory considère ces contrôles comme non vérifiés : elle n'envoie que profil, moteur, langue et traitement, et refuse `speed` ou `instruct`. Une voix fixée sous une version puis produite sous une autre s'arrête sur `voicestudio_version_changed_select_again` : relire le code de la nouvelle version, compléter `VERIFIED_CONTROLS` si les moteurs n'ont pas changé, puis refaire le choix avec Lou.

## Adapter l'interprétation au format

```powershell
& $py -m youtube_growth.factory voicestudio plan --video-type commentary --register dynamic
```

Le plan sépare l'intention, les adaptations du texte, les réglages appliqués, ceux que le moteur ignore et les essais possibles. Avec VoxCPM2, un commentaire sportif ne peut pas être accéléré par `speed` : écrire des phrases très courtes au présent, des relances, et réduire la pause entre phrases (`--sentence-pause 0.15`). Avec OmniVoice, la factory applique `speed` 1,08.

Une consigne libre ne s'adopte qu'après un essai comparé, avec l'accord de Lou, sur une ou deux phrases :

```powershell
& $py -m youtube_growth.factory voicestudio sample --session SESSION --text "Et c'est l'essai !" --output .local/video-onboarding/SESSION/essai-sans-consigne.wav
& $py -m youtube_growth.factory voicestudio sample --session SESSION --text "Et c'est l'essai !" --instruct "energetic live sports commentary" --output .local/video-onboarding/SESSION/essai-consigne.wav
```

Un essai calcule sur le GPU local sans crédit externe ; il n'écrase jamais un fichier existant. Seule l'écoute de Lou décide. Pour adopter la consigne : `video-onboarding voice SESSION --profile ... --instruct "..." --confirmation "..."`.

## Prononciation, respiration et production

- `--pronounce "SANDBOX=sand box"` ajoute une prononciation au profil choisi ; la factory la remplace avant la synthèse, mot entier. Le dictionnaire propre à Voice Studio s'applique aussi.
- La factory génère une prise par phrase et insère après chaque phrase, la dernière comprise, un silence mesuré (`pause_between_sentences_seconds`, 0,3 s par défaut ; 0,35 à 0,45 pour un documentaire posé). Les sous-titres suivent ces durées mesurées.
- `delivery.pause_after_seconds` d'une réplique (0 à 10 s) ajoute un silence après cette réplique dans le montage, quel que soit le fournisseur de voix. Il s'ajoute à la pause de fin de phrase et n'étire jamais la voix ; la prise en cache reste la même.
- Les prises sont conservées dans `.local/factory/storytelling-cache/audio/`. Une réplique inchangée réutilise sa prise ; `regenerate` en demande une nouvelle.
- Erreurs explicites : `voicestudio_unavailable`, `voicestudio_profile_missing`, `voicestudio_profile_changed_select_again`, `voicestudio_version_changed_select_again`, `voicestudio_engine_unavailable`, `voicestudio_engine_cannot_clone`, `voicestudio_speed_not_applied_by_engine`, `voicestudio_instruct_not_supported_by_engine`, `voicestudio_engine_license_required`, `voicestudio_engine_not_ready_retry`, `voicestudio_request_rejected`, `voicestudio_unexpected_response`.

Une transcription automatique ou une durée mesurée ne prouve ni la ressemblance ni la qualité du jeu. L'écoute intégrale reste un contrôle humain distinct.
