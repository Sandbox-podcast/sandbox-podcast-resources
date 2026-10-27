# Reprise locale du 20 octobre 2026

Lou a demandé de reprendre les travaux interrompus sur un autre compte Codex, puis de vérifier News, Charts, le mobile et les traductions. Le lot conserve les modifications déjà présentes dans cette copie de travail. Aucun commit, push, PR ou déploiement n'a été effectué pendant cette reprise.

## Travaux intégrés

- News distingue la dernière collecte des sources et la dernière publication sur le site. Un lot ancien ne remplace plus un relevé récent et une interruption de traduction ne classe plus les candidats restants comme refusés pendant vingt-quatre heures.
- Charts affiche la date réelle de publication de l'édition. Le contrôle horaire peut reprendre les chaînes dont le créneau dû manque, avec relecture après acquisition du verrou et arrêt des nouveaux appels lors du changement de créneau.
- Le menu mobile de l'accueil fonctionne. Les logos du header et du footer reviennent à l'accueil de la langue courante et ramènent en haut lorsqu'on y est déjà. Le footer mesure 254,5 pixels aux largeurs contrôlées, contre 699 à 754 pixels auparavant.
- Les textes de l'épisode 2, ses ressources et les miniatures sont localisés en anglais, espagnol et allemand. Les textes des miniatures sont en HTML. La langue française de la vidéo est annoncée ; le lecteur YouTube et sa piste audio ne sont pas traduits par ce lot.
- Les dictionnaires comportent chacun les 2 504 clés du catalogue. La recette de l'accueil au scroll et celle de la Time Machine ont été reprises avec le reste des changements locaux.
- Soixante-sept fichiers sources manquants du pipeline `camera-unique-v2` ont été restaurés depuis `origin/main`, sans écraser de fichier existant. Le pipeline valide ses trente compositions. Les médias sources restent intacts.

Le fonctionnement et les limites des traitements sont détaillés dans [le guide d'automatisation](automatisation-news-charts-2026-10-20.md), [l'audit backend](audit-automatisation-2026-10-20.md) et [ADR-0038](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0038-reprise-horaire-des-classements.md). Les fichiers UI et leurs contrôles figurent dans [le rapport mobile](responsive-mobile-2026-10-20.md) et [le rapport vidéo/i18n](mobile-i18n-video-2026-10-20.md).

## Recettes exécutées

`pnpm check` réussit : format, lint, TypeScript et **1 040 tests** (1 005 pour le site, 35 pour les autres suites du dépôt). L'audit des dépendances ne signale aucune vulnérabilité connue. Le cycle de publication d'un épisode réussit ses quatre groupes de contrôle avec une base éphémère. Le scan de secrets CI n'a pas été exécuté localement ; aucun push n'a été fait.

La dernière correction de métadonnées applique la ponctuation des titres de projets selon la langue. Les tests vérifient les titres HTML, OpenGraph et Twitter des fiches dans les trois langues secondaires.

| Contrôle local                                                | Résultat                                                   |
| ------------------------------------------------------------- | ---------------------------------------------------------- |
| Build Next.js de production                                   | Réussi, 204 pages générées                                 |
| Parcours mobile FR/EN/ES/DE, cinq pages, trois largeurs       | 60 parcours réussis, sans débordement ni erreur JavaScript |
| Vidéos localisées, trois langues, trois pages, trois largeurs | 27 contrôles réussis                                       |
| Time Machine sur build de production, quatre largeurs         | 41 contrôles réussis                                       |
| Accueil au scroll, six configurations                         | 20 contrôles réussis                                       |
| Routes HTTP publiques et métadonnées                          | 49 contrôles réussis                                       |
| News avec PostgreSQL simulé                                   | 11 groupes réussis                                         |
| Consentement, refus, retrait et nouvel accord                 | 27 contrôles réussis, services tiers simulés               |
| Administration HTTP en mode production                        | Réussi sans base réelle                                    |
| Polices des images OpenGraph                                  | 13 routes vérifiées                                        |
| Tests Python News, montage et compositions                    | 3 + 4 + 15 tests réussis                                   |
| Sources du pipeline de compositions                           | 30 sources valides                                         |

Les journaux de reprise sont conservés dans `apps/site/.local/reprise-*.log`. Le rapport final du gate global est `reprise-final-check.log`. Les captures et rapports navigateur sont dans les sous-dossiers `mobile-shell`, `video-localization`, `time-machine-experience` et `home-studio` du même dossier local.

Les premiers essais Time Machine sur le serveur de développement avaient échoué pendant les recompilations et les changements de fichiers. Les 41 contrôles finaux passent sur le build stable. La recette du consentement a été adaptée pour ouvrir le nouveau groupe repliable du footer avant de suivre son lien ; elle conserve les contrôles de retrait et de renouvellement de l'accord.

## Profils et points restants

Les changements de profils autorisés dans la conversation précédente ont été repris : Instagram, X, Spotify et LinkedIn sont vérifiés. L'accès au seul profil Instagram dans le Centre Meta a reçu une autorisation explicite supplémentaire. YouTube ne confirme pas la sauvegarde et son brouillon reste conservé ; TikTok interdit le renommage avant le 24 octobre. Voir [l'état des profils et les textes approuvés](social-profile-copy-2026-10-20.md).

Les correctifs applicatifs et les workflows restent locaux. Après une livraison autorisée, vérifier plusieurs événements GitHub `schedule` successifs, les éditions publiques et l'évolution de la file News. Les journaux observés montrent des lancements irréguliers, sans en établir toutes les causes. Une reprise horaire dépend elle-même du lancement de son contrôle ; ce mécanisme n'apporte pas de garantie de délai lorsque GitHub omet les événements. Rising attend toujours les données requises par sa méthode. Aucune donnée simulée ne lui a été substituée.

Les recettes navigateur utilisent Edge/Chromium local. Elles ne certifient pas Safari ni le comportement sur un téléphone physique. Les nouvelles publications vidéo suivent encore le lot de traduction d'ADR-0022.
