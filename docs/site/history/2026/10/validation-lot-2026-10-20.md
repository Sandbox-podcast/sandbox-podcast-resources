# Validation du lot local et des descriptions publiques

Ce document conserve le contrôle local effectué avant la livraison. Le lot a ensuite été fusionné dans la PR 99 ; [le relevé de production](verification-production-2026-10-20.md) consigne le déploiement et les résultats réellement observés.

20 octobre 2026. Ce relevé complète les rapports détaillés de reprise, de responsive, d'automatisation et de wording. Il distingue les changements locaux des opérations distantes réellement vérifiées.

## Textes et affichage

La promesse d'accueil est " Ce que l'IA change pour ceux qui construisent. ". L'introduction relie les expériences des deux développeurs et du Product Manager au code, aux choix produit et au travail des équipes. Les nouvelles présentations et métadonnées couvrent l'accueil, l'émission, À propos, les projets, News, Charts, Time Machine et le footer. Les nouveaux textes sont traduits en anglais, espagnol et allemand ; les trois dictionnaires couvrent les 2 506 clés du catalogue contrôlé. Time Machine conserve son routage français préexistant.

À la demande de Lou, les nouvelles présentations ne mentionnent plus les années d'expérience. `vision.md` et les faits historiques ne sont pas réécrits. La compatibilité des anciennes publications admin remplace uniquement les valeurs historiques exactes ; les textes personnalisés restent conservés. La lecture réelle de l'ancienne publication locale n'a changé ni son contenu ni son SHA-256.

La recette indépendante du wording a contrôlé les sept vues françaises à quatre tailles, puis les six vues communes EN/ES/DE et leurs titres et métadonnées. Le chevauchement du titre desktop a été corrigé. Les recettes mobile et vidéo précédentes sont détaillées dans `responsive-mobile-2026-10-20.md` et `mobile-i18n-video-2026-10-20.md`. Les captures finales sont dans le dossier local ignoré `.local/vision-qa/` du site.

Les six descriptions sociales sont enregistrées. TikTok, Instagram, X, YouTube et LinkedIn ont été relus sur leurs profils publics ; Spotify conserve le texte final après rechargement de ses réglages. Les liens, compteurs et limites sont consignés dans [le relevé de publication](profils-vision-2026-10-20.md). Spotify utilise 458 caractères sur les 600 réellement autorisés. Les noms, identifiants et médias ne sont pas modifiés dans ce lot de descriptions.

## Vérifications finales exécutées

- `pnpm check` : code de sortie 0, formatage, ESLint et TypeScript réussis. 1 081 tests du site sur 142 fichiers, 7 tests du générique, 4 tests des assets et 24 tests BIS : **1 116 tests réussis**.
- `pnpm --filter @podcast/site exec next build --webpack` : code de sortie 0, compilation et TypeScript réussis, **204 pages générées sur 204**. La voie Webpack est celle de la recette locale ; le build Turbopack standard n'est pas présenté comme revalidé par cette commande.
- Watchdog et précontrôles : **67 tests réussis**, également relus par un autre agent. Recette du moteur officiel `workerd` avec stockage SQLite : **cinq groupes réussis**, dont concurrence et redémarrage. Les transports y sont simulés.

Journaux : `apps/site/.local/watchdog/final-check.log`, `final-build.log` et `worker-test.log`. Les fichiers de slides et du portail ajoutés par les autres chats ont été inclus dans le contrôle global de l'état partagé ; aucune fonctionnalité de ces lots n'a été réécrite par cette validation.

## Contrôle distant de la cadence

Le Worker gratuit `sandbox-automation-watchdog` est déployé en observation avec `ENABLED=true` et `DRY_RUN=true`. Les logs Cloudflare montrent les événements planifiés à 11 h 05, 11 h 10, 11 h 15 et 11 h 20, heure de Paris. Le dernier état de santé relu porte `checkedAt=2026-10-20T09:25:12.286Z`, avec HTTP 202, `schedulerOk=true`, `recent=true` et `dataFresh=null`. Le passage précédent était à `09:20:12.554Z`, soit 4 min 59,732 s d'écart.

L'invocation interne du 20 octobre à 11 h 20 porte `outcome=ok`, HTTP 200, `cpuTimeMs=17` et `wallTimeMs=10027`. Il s'agit d'une mesure isolée du Durable Object. Elle ne démontre ni le coût à long terme ni le temps de publication d'une actualité. La console confirme le plan gratuit pour les événements observés.

Le contrôleur n'a pas encore lancé de workflow : le mode observation empêche les dispatchs. Il faut d'abord livrer les nouveaux modes sur `main`, valider leur CI puis activer `DRY_RUN=false`. Les protections contre les doublons sont locales et testées ; la recette de récupération réellement publiée reste à faire après cette livraison. Le diagnostic et la procédure se trouvent dans [le rapport de planification](fiabilisation-planification-2026-10-20.md) et [le guide du Worker](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/tools/automation-watchdog/README.md).

News utilise Qwen pour le résumé et Argos pour les traductions dans GitHub Actions. Le fonctionnement de ce pipeline ne dépend pas du quota de l'abonnement Codex. Le Worker contrôle les dates et déclenche les workflows ; il ne produit pas les articles.

## Livraison restante

Le dépôt partagé reste sans nouveau commit, push ou PR de cette reprise. La référence distante a été actualisée en lecture : `main` pointe sur `df86504d263fa4f5a9d7a6b5c2bfdad1c32989b4`, qui inclut la correction de timeout de découverte Charts de la PR 98. Une livraison doit conserver cette correction et intégrer les fichiers locaux nécessaires, sans traiter comme supprimés les fichiers non suivis déjà présents sur `main`.

Les règles du dépôt soumettent commits, pushes et PR à l'accord explicite du propriétaire. Après cet accord, le lot pourra être livré, puis le contrôle Cloudflare activé et vérifié sur plusieurs échéances réelles. Une cadence de contrôle régulière ne garantit pas à elle seule la disponibilité des sources, des runners ou la résorption de la file News. Safari sur téléphone physique n'a pas été testé dans cette recette.

Après ce contrôle global, le chat consacré au portail a ajouté Three et ses types au package et au lockfile. Cette évolution reste sous la responsabilité de ce chantier et demande sa propre vérification finale. Les résultats ci-dessus décrivent l'état effectivement testé ; ils ne valident pas par anticipation ces nouvelles dépendances. L'inventaire de livraison distingue les fichiers propres au portail, les slides 003 et les intégrations partagées. Il est conservé dans le fichier ignoré `.local/watchdog/release-inventory.json` à la racine du dépôt.
