# Descriptions des profils : vérification de publication

20 octobre 2026. Lou a validé les six descriptions du document `descriptions-reseaux-vision-2026-10-20.md`, puis demandé de supprimer la mention des années d'expérience et de synthétiser Spotify pour respecter sa limite.

## Résultat distant

| Profil                           | Résultat vérifié                                                 | Contrôle                                                                                                                                                                      |
| -------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TikTok `@sandbox.talkshow`       | Bio de 65 caractères publiée avec `sandboxpodcast.fr`            | Le profil rechargé affiche les deux lignes. Le premier enregistrement avait échoué ; le formulaire a été rouvert puis la sauvegarde a été vérifiée après rechargement.        |
| Instagram `@sandbox.talkshow`    | Bio de 110 caractères publiée avec `sandboxpodcast.fr`           | Le formulaire rechargé puis le profil public affichent le texte final.                                                                                                        |
| X `@SandboxTalkShow`             | Bio de 155 caractères publiée, quatre liens conservés            | Le profil affiche la nouvelle première phrase et les quatre destinations.                                                                                                     |
| YouTube `@SandboxFR`             | Description de 902 caractères publiée                            | La description complète est visible dans la fenêtre publique de présentation de la chaîne. La sauvegarde de la description seule a fonctionné depuis une nouvelle vue Studio. |
| Spotify `2Wp6S4qgRqQaV01AjkDcMH` | Description de 458 caractères enregistrée, cinq liens conservés  | Le champ conserve le texte final après rechargement. L'interface impose effectivement `maxlength=600`. La propagation aux applications d'écoute n'a pas été mesurée.          |
| LinkedIn `sandbox-podcast-fr`    | Slogan de 70 caractères et description de 984 caractères publiés | Les deux textes sont visibles sur la page À propos en vue membre. Un conflit d'édition a été résolu en annulant notre brouillon, rechargeant le formulaire puis enregistrant. |

Les identifiants et les médias n'ont pas été modifiés dans ce lot. Aucun post ni épisode n'a été publié. Le nom YouTube reste `Sandbox TalkShow` ; la description présente bien `Sandbox Podcast`. Le surnom TikTok reste verrouillé par la plateforme jusqu'au 24 octobre 2026.

## Preuves locales

Captures conservées dans le répertoire ignoré `apps/site/.local/pitch-profils/` :

- `tiktok-published.png` : bio visible sur le profil rechargé.
- `instagram-published.png` : profil public.
- `x-published.png` : profil public.
- `youtube-published.png` : fenêtre publique avec description complète.
- `spotify-published.png` : champ de description après rechargement.
- `linkedin-published.png` : slogan en vue membre.

Les textes finaux et leurs compteurs sont conservés dans `descriptions-reseaux-vision-2026-10-20.md`. Les rapports antérieurs décrivent leur propre état de publication ; ils ne remplacent pas cette vérification.
