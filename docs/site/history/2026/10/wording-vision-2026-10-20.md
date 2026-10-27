# Réécriture des textes publics du site

20 octobre 2026. Implémentation locale du [positionnement SANDBOX](pitch-vision-2026-10-20.md), aligné sur [vision.md](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/vision.md). Décision et compatibilité des anciens réglages : [DD-0068](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0068-wording-aligne-sur-la-vision.md).

## Résultat

L'accueil présente une seule promesse : "Ce que l'IA change pour ceux qui construisent." Le format et les métiers sont visibles dès le premier écran : un talk-show IA, engineering et produit, avec deux développeurs et un Product Manager. L'introduction relie leurs expériences au code, aux choix produit et au travail des équipes. Les boutons ouvrent l'émission disponible et les projets.

La page Émission explique la discussion et ses quatre séquences sans imposer rétrospectivement un format idéal à chaque replay. À propos présente les animateurs et le public visé. Les projets servent de preuves de pratique, sans affirmer que chaque application a été construite avec l'IA.

News présente les annonces résumées et leurs sources, avec la mention de génération automatique. Charts donne des repères pour choisir quoi tester à partir des mesures et des critères publiés. Time Machine explique ce que ses dates et ses sources apportent à la compréhension de l'IA actuelle. Les titres descriptifs utiles au référencement, les liens, les dates de mise à jour et les comportements restent en place.

Le pied de page et les métadonnées reprennent la même présentation. Les traductions anglaises, espagnoles et allemandes couvrent les nouveaux textes publics. Les clés historiques nécessaires aux anciens contenus sont conservées.

## Réglages publiés

Les anciens réglages admin ne doivent pas masquer le changement. La lecture publique remplace uniquement les valeurs historiques exactes connues dans neuf champs de présentation. Les autres textes, les noms et les liens restent ceux du propriétaire. Le stockage conserve les valeurs originales ; aucune publication ou écriture admin n'est lancée.

Le fichier local de publication contient encore l'ancien titre "Un Talk Show pour y voir plus clair." La recette du serveur local permet donc de vérifier le changement avec une publication existante. Le test Postgres couvre le même parcours de chargement public et confirme l'absence d'appel à l'API d'écriture. Les variantes publiques à apostrophes courbes sont traitées séparément, car elles ont été observées et retrouvées dans l'historique Git.

## Périmètre technique

- Réglages et compatibilité : `content/site.json`, `src/config/site.ts`, `src/domain/site-marketing.ts`.
- Présentations : `studio-landing`, `discovery-story`, `shell`, `news-screen`, `charts-experience`, `time-machine`, pages publiques et métadonnées associées.
- Traductions : dictionnaires EN, ES et DE, catalogue et collecte des trois champs À propos auparavant absents du catalogue.
- Tests : compatibilité des réglages, lecture éditoriale publiée, accueil, bibliothèque podcast, traductions, News, Charts et Time Machine.

## Vérification

Les tests ciblés vérifient le changement de texte, les liens et les cas personnalisés. La recette navigateur indépendante à 320, 390, 1280 et 1440 pixels a révélé un chevauchement du repère avec le nouveau titre sur ordinateur. Le regroupement du repère et du titre dans un même bloc l'a corrigé. Les captures de contrôle sont conservées dans `apps/site/.local/vision-qa/`, dont `1440-home-corrected.png`, `1280-home-corrected.png`, `390-home-corrected.png` et `320-home-corrected.png`.

La passe ciblée couvre 10 suites et 121 tests, tous réussis. ESLint sur les sources et tests concernés et TypeScript sans émission sont également réussis. La vérification rédactionnelle des deux documents et des réglages JSON ne relève aucun caractère interdit.

Le contrôle global a ensuite relevé quatre attentes obsolètes dans les tests de métadonnées localisées et de catalogue Projets. Les suffixes des trois titres ont été actualisés. Le test Projets utilise désormais les vrais dictionnaires EN, ES et DE au lieu d'un dictionnaire minimal contenant uniquement l'ancien titre. Il vérifie les nouveaux H1, les champs de recherche et les liens des 34 projets. Cette passe complémentaire réussit ses 28 tests sur deux suites ; format et lint ciblés réussissent également.

La recette HTTP de l'ancienne publication réelle retourne les nouveaux H1 et métadonnées sur `/` et `/about`, avec un statut 200. Le SHA256 du fichier publié reste identique avant et après : `617d9f4d7c6fd749f911884fefdefd8af096d3518604bcc52555a309e5f801e7`. La preuve structurée est conservée dans `apps/site/.local/vision-qa/legacy-readonly.json`.

Le rapport de recette de l'équipe et le résultat du contrôle global complètent ces vérifications après stabilisation des dictionnaires. Les fichiers de preuve sous `.local` restent locaux. Aucune mise en production, modification de profil social, création de PR, commit ou push n'est inclus dans ce travail.
