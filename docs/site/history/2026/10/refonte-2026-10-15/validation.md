# Validation locale de la refonte SANDBOX

15 octobre 2026. La version courante suit [DD-0033](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0033-accueil-cinematique-et-trio-sur-plateau-tv.md) : trio sur un plateau télé, message court et cadrage au défilement. Les contrôles de la version précédente selon DD-0032 sont conservés plus bas.

## Itération du plateau télé (V3)

Le décor vide est remplacé par `public/images/home/sandbox-trio-tv-v3.png` (1 931 330 octets avant optimisation Next). La [fiche de provenance](plateau-provisoire.md) documente les portraits de référence, les corrections de cadrage et le prompt. Le texte devient " L'IA, en pratique. " et précise les essais d'outils et les projets. La courte progression de caméra est implémentée dans `cinematic-stage.tsx`, `stage-motion.ts` et `discovery-home.module.css`. Les styles d'en-tête, les dictionnaires et les tests de l'accueil sont adaptés. Le rappel des préférences de mesure reste accessible en fin de homepage, sans recouvrir l'action principale.

Revue réelle dans le navigateur à 320 × 780, 390 × 844, 768 × 1024 et 1440 × 1000 : trio visible, proportions conservées, texte lisible, aucun débordement horizontal. Le recadrage initial trop serré sur téléphone a été corrigé. Le mode statique s'applique jusqu'à 1000 pixels. Sur ordinateur, le retour en haut retrouve exactement le cadrage initial ; le bouton de réduction passe en mode statique, puis la touche Entrée réactive le mouvement. Le lien " La suite " rejoint le dernier replay. Le rappel de mesure ouvre bien son panneau et le refus le referme.

Captures locales : `.local/refonte-captures/home-v3-tv-desktop.jpg`, `home-v3-tv-mobile.jpg`, `home-v3-tv-replay.jpg`. Ce sont des captures de la page exécutée en localhost, pas des maquettes dessinées. Les tests ciblés d'accueil et de navigation réussissent : 15 tests dans deux fichiers (`.local/refonte-v3-targeted.log`).

Le premier contrôle complet a détecté une expression de callback refusée par ESLint ; elle a été corrigée. La relance dans le bac à sable a ensuite échoué sur des modules temporaires Vitest introuvables. Cette trace est conservée dans `.local/refonte-v3-check-sandbox-failure.log`. La relance hors du bac à sable a réussi, sans désactiver de test.

Contrôles finaux : `pnpm check` réussi avec format, ESLint, TypeScript, 603 tests du site, 7 tests de l'intro et 4 tests des jingles, soit 614 tests (`.local/refonte-v3-check.log`). Build de production réussi, 203 pages statiques (`.local/refonte-v3-build.log`). L'avertissement déjà présent sur la convention `middleware` reste à traiter séparément. `git diff --check` ne signale aucune erreur. Le bouton principal a également ouvert `/episodes/1` au clavier dans le navigateur.

Le mouvement reste un zoom de l'image, pas un déplacement dans un maillage 3D. Aucun benchmark de fluidité, score Lighthouse ou gain de conversion n'est revendiqué. La ressemblance et la direction artistique restent à apprécier avec Lou avant le remplacement par le plateau définitif.

## Historique : accueil avec plateau vide (V2)

## Résultat

La version locale est disponible sur `http://127.0.0.1:3340/`. Le premier écran présente le sujet du podcast, sa proposition, le plateau provisoire et le bouton du dernier épisode. Le pilote réel apparaît une seule fois sous ce premier écran. Les rubriques d'acquisition restent dans leurs pages.

La base de classements du serveur local est éphémère et explicitement marquée FIXTURE. Le contenu du pilote vient de la fixture de référence publique du dépôt, recopiée dans le stockage local de développement. Aucun contenu distant n'a été publié ou modifié. Aucun commit, push ou PR n'a été créé.

## Contrôles exécutés

| Contrôle                                                                                | Résultat                                                                                                            | Trace locale                                                           |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `pnpm check`                                                                            | Réussi : format, ESLint, TypeScript, 601 tests du site dans 94 fichiers, 7 tests de l'intro et 4 tests des jingles. | `.local/refonte-v2-check.log`                                          |
| `pnpm --filter @podcast/site build`                                                     | Réussi : compilation, types et génération de 203 pages statiques.                                                   | `.local/refonte-v2-build.log`                                          |
| `SANDBOX_BROWSER_CHANNEL=msedge node scripts/test-analytics-e2e.mjs` depuis `apps/site` | Réussi : 7 contrôles GA4 bloqué et 15 contrôles GA4 prêt, avec doubles locaux de Google et Vercel.                  | `.local/refonte-v2-analytics.log` et `apps/site/.local/analytics-e2e/` |
| Vérificateur `fasst-human-quality`                                                      | Réussi pour l'audit, la stratégie, la roadmap et DD-0032.                                                           | `.local/refonte-v2-writing.log`                                        |
| `git diff --check`                                                                      | Réussi. Un avertissement de normalisation CRLF existant sur `.prettierignore`, sans erreur de diff.                 | Sortie terminal                                                        |

La première commande destinée aux tests ciblés a lancé toute la suite à cause du séparateur d'arguments. Deux tests PGlite d'import de médias ont dépassé leur délai de 5 secondes. Le contrôle complet suivant a réussi avec les mêmes tests et les mêmes délais, sans modification de gate. Le premier essai E2E n'a pas trouvé le navigateur Chromium de Playwright ; la relance avec Edge déjà installé a réussi, sans installation.

Les journaux E2E contiennent un 404 pour l'avatar fictif `sandbox-e2e` et des recommandations de priorité d'images sur d'autres pages. Le build signale la convention Next `middleware` à migrer vers `proxy`, déjà présente avant ce lot. Ces avertissements n'ont pas été masqués.

## Revue dans le navigateur

| Parcours ou état                       | Observation                                                                                                                                                        |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Accueil à 320, 390, 768 et 1440 pixels | Aucun défilement horizontal. Le texte, le bouton de 48 pixels de haut et le plateau restent visibles. Les trois places du décor sont reconnaissables sur mobile.   |
| Menu mobile                            | Le podcast apparaît en premier. Classements, Time Machine, Nos projets et recherche restent accessibles.                                                           |
| Bouton principal                       | Ouvre `/episodes/1` avec le titre réel du pilote, sa vidéo à la demande, 17 chapitres et 14 ressources.                                                            |
| Accueil anglais                        | Message, légende provisoire, action, pied de page et titre du pilote traduits. Liens d'épisode préfixés `/en`.                                                     |
| Image et scripts                       | Plateau et miniature chargés. Aucun lecteur tiers ni canvas sur l'accueil. Aucune erreur JavaScript dans le journal de l'onglet de revue.                          |
| Absence d'épisode                      | Test de rendu réussi : aucun faux replay, bouton vers `/podcast`. L'état sans base a également été contrôlé dans le build de la première itération.                |
| Consentement                           | Aucun script avant accord ou après refus ; retrait propagé entre onglets ; expiration, administration exclue, tag retardé et paramètres nettoyés vérifiés par E2E. |

Les améliorations annexes ont été vérifiées pendant la première itération : filtres et état vide des classements, retour aux résultats, changement de famille ; recherche sans résultat et réinitialisation de Time Machine ; sélection d'un événement par ancre ; récapitulatif 2022 et téléchargement JSON ; lecture volontaire du pilote. La nouvelle itération n'a modifié que l'accueil, l'ordre et le style du menu, le texte du pied de page et leurs traductions.

Captures enregistrées dans `.local/refonte-captures/` : `home-v2-stage-first-screen.jpg`, `home-v2-stage-desktop.jpg`, `home-v2-stage-mobile.jpg`, `home-v2-stage-320.jpg` et `home-v2-stage-tablet.jpg`. Les captures précédentes restent disponibles pour comparaison visuelle, avec leurs différences de contenu et de largeur ; ce ne sont pas des mesures de performance.

## Principaux fichiers du lot

| Partie            | Fichiers                                                                                                                                        |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Stratégie         | `docs/SANDBOX_AUDIT.md`, `docs/SANDBOX_UX_STRATEGY.md`, `docs/SANDBOX_ROADMAP.md`, DD-0031 et DD-0032, index documentaires                      |
| Accueil           | `src/app/(fr)/page.tsx`, `src/components/discovery-home.tsx`, son CSS module et `src/domain/home-discovery.ts`                                  |
| Plateau           | `public/images/home/sandbox-stage-placeholder-v1.png`, [provenance et prompt](plateau-provisoire.md)                                            |
| Navigation        | `src/components/nav.tsx`, `shell.tsx`, `src/app/site-polish.css`                                                                                |
| Classements       | `charts-experience.tsx`, `charts-ranking.tsx`, `charts-compact.module.css`, métadonnées de `/charts`                                            |
| Contenus annexes  | Page et styles podcast, page épisode, catalogue Nos projets, `time-machine.tsx`, son CSS module, `history-sharing.ts`, `search-screen.tsx`      |
| Guides préparés   | `content/guides.json` vide, `domain/guides.ts`, `lib/guides.ts`, `guide-article.tsx`, `docs/site/guides.md`                                     |
| Langues et mesure | Dictionnaires, catalogue de chaînes, `shared-pages.tsx`, `analytics-actions.ts`, `analytics-consent.tsx`, `sitemap-index.ts`, documentation GA4 |
| Tests             | `discovery-refonte.test.ts`, tests de navigation, localisation, route d'épisode et événements, `scripts/test-analytics-e2e.mjs`                 |

Les chemins `src/`, `public/`, `content/` et `test/` du tableau sont relatifs à `apps/site`. Le dépôt comportait déjà de nombreuses modifications locales avant ce travail ; ce rapport décrit le lot fonctionnel, pas l'ensemble du diff Git.

## Limites et suite

Le visuel est une image d'attente générée avec `image_gen`, pas le plateau définitif. Aucun mouvement 3D n'est livré. Les tests de rendu ne prouvent ni que le pitch est compris par le public, ni que la page convertit mieux. Aucun score Lighthouse ou gain de Core Web Vitals n'est revendiqué.

La prochaine revue avec Lou porte sur le message, la place du plateau et le rythme de la page. Quand la scène définitive est prête, remplacer l'image et tester le cadrage avant de choisir une vidéo ou un maillage. Les classements distants, GA4, Search Console et le déploiement restent des vérifications séparées, à effectuer dans leurs environnements autorisés.
