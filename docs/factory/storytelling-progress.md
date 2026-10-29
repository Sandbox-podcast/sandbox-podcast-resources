# Avancement de StoryTelling Generator

Suivi de l'exécution gauntlet dans l'[issue #14](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/14), en prolongement des demandes #12 et #13.

| Domaine | État | Preuve attendue |
| --- | --- | --- |
| Sources et scénario | Intégré ; 14 tests éditoriaux réussis | Imports figés, scénario validé, critique éditoriale distincte |
| ElevenLabs et voix locales | Intégré ; 14 tests audio et 11 tests navigateur réussis | Cache par réplique, ledger atomique, attribution stable des voix et contrôle de couverture |
| Timeline et montage | Recette réelle locale réussie | H.264/AAC, sous-titres mov_text/SRT/VTT, mix voix/musique/effet et frontières globales de plans |
| Interface et reprise | Sept étapes vérifiées dans le navigateur | Brief enregistré, travail mis en file, requête agent téléchargeable et reprise/validation en file |
| Sauvegarde portable | Restauration indépendante réussie | Ressources et cache réutilisés après disparition du stockage d'origine, aucune nouvelle synthèse |
| Critique indépendante | Aucun défaut bloquant connu sur les contrôles terminés | Budget musical, couverture TTS, concurrence, dérive d'images et verrous transitifs corrigés |

Lou a choisi ElevenLabs dans le navigateur intégré. La session est connectée ; aucun crédit n'a été dépensé. Les demandes sont exportées et suivies dans SQLite, puis les fichiers téléchargés sont importés par empreinte. Ce parcours exige une session Codex active pour piloter le navigateur. Le worker monte ensuite les ressources locales.

L'exemple de récit reste uniquement une fixture technique. Le travail porte sur le générateur et sur ses entrées réelles ; aucune vidéo d'EGO n'est produite.

## Vérifications exécutées

La recette initiale dans le dépôt partagé a exécuté 341 tests avec succès. La branche isolée de StoryTelling Generator a ensuite exécuté 329 tests en 113,6 secondes : résultat réussi, sept tests ignorés. Elle exclut les travaux de veille YouTube menés en parallèle. Les tests spécialisés ont aussi vérifié les dernières attributions de voix navigateur et la restauration portable. La recette média explicite du pipeline a passé ses treize tests, avec vraie voix Windows ; celle du renderer a passé avec des pistes synthétiques identifiées, un MP4 lisible, des sous-titres intégrés, une crête inférieure à 0 dB et 37 images sur trois plans dont les bornes ne tombent pas sur des images entières.

Les contrôles du dépôt, des espaces du diff, de la syntaxe JavaScript et du skill de factory ont réussi. Les ressources de recette restent sous `.local/`.

## Limites de cette validation

Aucune génération ElevenLabs réelle n'a été effectuée après le recentrage demandé par Lou. Les tests de fournisseur utilisent des transports factices ; les tests de navigateur vérifient le suivi et l'import de fichiers, avec du PCM synthétique. Ils ne prouvent pas la qualité d'une voix produite par le compte connecté.

La rédaction sans modèle local demande une session Codex pour traiter la requête structurée. Le parcours ElevenLabs navigateur demande également une session Codex active. Le worker seul peut attendre et reprendre les fichiers locaux, mais ne contrôle pas le navigateur intégré. Les documents scannés nécessitent un OCR ; les médias audio et vidéo ne sont pas transcrits automatiquement par l'importeur. Le rendu de secours utilise schémas, images, vidéos importées et fondus ; les intentions de mouvement plus complexes demandent une ressource ou un moteur supplémentaire. Les validations humaines d'écoute et de fidélité restent à effectuer sur chaque production réelle.
