# Regroupement des PR 77 et 78

Le 18 octobre 2026, Lou demande de réunir toutes les PR ouvertes du dépôt dans une seule et de tester le lot. La [PR 77](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/77) devient la PR unique ; la [PR 78](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/78) y est intégrée avant sa fermeture.

## Réconciliation

La PR 78 contient 26 fichiers consacrés à l'épisode 003. Ils sont déjà présents dans la PR 77 : 24 fichiers sont identiques. Les deux autres, `content.json` et `shorts.json`, ont reçu dans la PR 77 les révisions éditoriales demandées depuis. Ces versions révisées sont conservées.

Une fusion Git à deux parents intègre le commit `8b92989` de la PR 78 dans la branche `codex/kits-relais-videos-autonomes`. Le code et les contenus du produit restent identiques au commit `25904b7` déjà testé de la PR 77. Seuls ce rapport et ses liens documentaires sont ajoutés au lot.

## Contrôles exécutés sur le lot réuni

Node 24 et pnpm 12.9.1 sont utilisés. Les commandes sont lancées avec `corepack pnpm`.

| Contrôle                                            | Résultat                                                                               |
| --------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `pnpm check`                                        | Formatage, lint, types et 825 tests réussis : 790 site, 7 générique, 4 jingles, 24 BIS |
| `pnpm build`                                        | Réussi ; 204 pages statiques générées                                                  |
| `pnpm audit --audit-level=high`                     | Aucune vulnérabilité connue signalée                                                   |
| `pnpm --filter @podcast/site content:check`         | Zéro erreur, zéro avertissement                                                        |
| `pnpm --filter @podcast/site news:translator:check` | Traduction Argos réelle, fiche complète en EN/ES/DE, 17 097 ms                         |
| `test:og:tracing`                                   | Les 13 routes OpenGraph incluent leurs cinq polices                                    |
| `test:admin:http`                                   | Contrôles HTTP de sécurité réussis, sans accès à la base distante                      |
| `test:public-routes`                                | 333 URL du sitemap valides et 34 contrôles HTTP réussis                                |
| `test:analytics:e2e`                                | 27 contrôles réussis : 9 en mode bloqué et 18 en mode activé                           |
| `test:badges:http`                                  | Contrôles HTTP de production réussis, sans accès à la base distante                    |
| `test:badges:e2e`                                   | 43 contrôles réussis, sans erreur JavaScript du navigateur                             |

Les serveurs de test utilisent des bases PGlite éphémères sur loopback. Les tests de consentement remplacent les services de mesure par des doubles locaux. Aucune migration Neon ni publication de contenu en production n'est effectuée.

## Recette News et épisode 003

Une recette supplémentaire dans un contexte Edge isolé vérifie le parcours suivant : requête cron authentifiée, validation d'une fiche de test, écriture dans la base éphémère, puis affichage dans les quatre langues.

- News fermé : HTTP 404 ; secret absent : HTTP 401 ; première insertion : une fiche ; répétition du lot : zéro doublon. La liste des URL connues retrouve la fiche enregistrée.
- Huit affichages News passent, avec les quatre langues en 1440 × 900 et en 390 × 844. Le titre, les trois phrases, le lien source, le canonical, les liens de langues et l'indexabilité sont contrôlés. La recherche vide, son effacement et le sitemap sont aussi vérifiés.
- Les 21 écrans de l'épisode 003 passent en 1280 × 720, 1920 × 1080, 2560 × 1440 et 3440 × 1440 : 84 contrôles de remplissage et de débordement. Les images se chargent.
- Les choix sauvegardés survivent au rechargement ; l'export JSON est téléchargé. Les notes, le mode image seule, le retour régie et trois formats plus petits sont vérifiés. Aucune erreur JavaScript n'est relevée.

Le script et son rapport local sont dans `apps/site/.local/pr-consolidation/`, hors de Git. Les assertions passent lors des deux exécutions. Lors de la seconde, le navigateur et la base se ferment explicitement ; le processus conserve ensuite des handles de développement Next et est arrêté après la fermeture. Les suites versionnées du tableau quittent toutes avec le code zéro.

## Limites

Le build local émet un avertissement Turbopack sur le motif `.local`, qui contient les modèles installés sur ce poste. Le build réussit. Les dossiers de modèles sont ignorés par Git.

La recette de publication utilise une fiche fictive déjà rédigée dans les quatre langues. Elle ne lance pas l'inférence Qwen ; ses validations et rejets sont couverts par les tests du pipeline. Le premier cycle réel de génération planifiée reste à vérifier lors de la mise en service documentée dans [DD-0057](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0057-automatisation-production-news.md).

La PR 77 a été fusionnée le 18 octobre 2026 à 16:35 UTC. La PR 78 a été fermée sans fusion séparée, son contenu ayant été repris dans la PR 77. L'activation News en production, l'application de la migration 0016, la validation DNS Search Console, la sélection finale du Radar et le cadrage OBS avant le live restent à terminer.
