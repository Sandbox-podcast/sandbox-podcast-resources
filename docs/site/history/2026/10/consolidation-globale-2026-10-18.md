# Regroupement des conversations du 18 octobre 2026

Lou demande de corriger les problèmes restants, de réunir le nouveau code de ses conversations dans une seule PR et de créer une issue de bilan et de suivi.

## Périmètre réuni

| Domaine               | Travail conservé                                                                                                                                                                   |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Classements           | Collecte Models partielle sans fusion d'identités, diagnostic canonique en lecture seule, calcul ISO, sources publiques, isolation OpenSSF par créneau et contrôles de publication |
| News                  | Exécution Linux du traducteur, extraction des articles, états vide et indisponible, liens de l'accueil et recette navigateur en CI                                                 |
| Recherche et langues  | Dernières éditions publiées de quatre familles, identifiants des dépôts et modèles, titres traduits et repli public pendant une panne Postgres                                     |
| Import YouTube        | Date, durée et description depuis la page publique sans clé API, validation des données et protections de la route admin                                                           |
| Kits de relais        | Sous-titres externes déplacés hors des dossiers personnels, ZIP vérifiés et script de montage adapté                                                                               |
| Shorts de l'épisode 2 | Manifestes et journal des corrections de caméra, état des remplacements natifs et sources utiles du montage V2                                                                     |
| Time Machine          | Ouverture sur 2026, onze événements sourcés supplémentaires et onze affiches, corpus revu au 18 octobre                                                                            |

Les PR 84, 85, 86 et 89 sont intégrées avec des commits de fusion à deux parents. Le correctif de semaine ISO conserve aussi l'année ISO correcte. Les protections ajoutées après les PR sur la recherche, les modèles et les pannes Postgres sont conservées lors de la résolution des conflits. La branche inclut également `origin/main`, au commit `a2236f0` lors du regroupement.

Le dossier principal reste celui des autres conversations. La branche de livraison est préparée dans une copie isolée, `codex/lot-global-corrections-2026-10-18`, sans supprimer leurs fichiers ni leurs branches.

## Inventaire des autres copies de travail

Trente worktrees sont recensés ; vingt-huit sont examinés en dehors du dossier principal et de l'intégration. Dix-neuf sont propres, neuf présentent des changements anciens. Aucun nouveau code du 18 octobre n'est trouvé hors du dossier principal et des PR ouvertes. La conversation « Mettre à jour la Time Machine », terminée pendant le regroupement, est également reprise depuis le dossier principal.

Les anciens travaux sur les aperçus sociaux et l'audit de confiance ont déjà été repris ou remplacés par les versions actuelles. Les autres écarts sont des fins de ligne ou des suppressions anciennes de médias. Les anciens prototypes de classements multi-source et de création d'épisodes ne sont pas recopiés : leurs fonctions ont déjà été portées dans le site actuel. L'épisode 003 est déjà dans `main`. Le worktree de l'import YouTube correspond à la PR 89, intégrée ici.

## Vérifications et limites

Le premier contrôle sur la branche regroupée réussit : formatage, lint, types et 918 tests, dont 883 pour le site, sept pour le générique, quatre pour les jingles et vingt-quatre pour le support BIS. Le build produit 204 pages. Gitleaks ne trouve aucune fuite sur les nouveaux commits et l'audit des dépendances ne signale aucune vulnérabilité connue. Les quatre tests Python des kits passent aussi.

Les recettes News passent avec sept groupes de vérification ; le sitemap compte 325 URL valides et les parcours publics passent 49 contrôles HTTP. Les quinze tests du pipeline vidéo passent, dont les comparaisons audio, l'invalidation des preuves et le confinement des sorties ; ses trente compositions sont valides. Le contrôle complet après intégration de la Time Machine passe également : 919 tests, dont 884 pour le site, build de 204 pages, zéro erreur ni avertissement du contrôle de contenu. La recette analytics passe ses 27 contrôles. Le [rapport des corrections du site](remise-en-etat-2026-10-18.md) détaille les parcours testés et les causes corrigées.

La [PR unique 90](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/90) rassemble le lot ; les PR 84, 85, 86 et 89 sont fermées et renvoient vers elle. L'[issue 91](https://github.com/Sandbox-podcast/sandbox-podcast-site/issues/91) contient le bilan et les actions restantes. Les [contrôles Linux de la PR sur le code final](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/39167697218) réussissent, y compris les recettes News et analytics. Le build de l'aperçu Vercel réussit aussi ; sa recette distante reste soumise à l'authentification du projet.

Le suivi social livré est un instantané du 18 octobre à 21:17:26 UTC. Les remplacements natifs poursuivis dans la conversation de diffusion peuvent modifier les états après cet instant : relire sa file courante avant toute action.

Ce regroupement ne fusionne pas la PR dans `main` et n'active aucun contenu en production. Les modèles contradictoires, la mise en service News, les accès Neon/Vercel, les deux rafraîchissements programmés, les Awards réels, les mesures d'audience et les remplacements sociaux encore non confirmés restent des actions distinctes. Aucun historique manquant, classement ou résultat de publication n'est inventé.
