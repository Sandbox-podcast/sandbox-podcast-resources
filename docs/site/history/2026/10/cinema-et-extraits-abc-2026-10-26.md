# Cinéma et tests de miniatures du 26 octobre 2026

Lou signale l’absence de l’épisode 1 dans le cinéma, le recadrage et le titre illisible de l’épisode 3, puis demande un test A/B/C sur les cinq extraits publiés du 21 au 25 octobre.

## YouTube

Les cinq tests natifs sont lancés sur Sandbox TalkShow (`UCuATIBXo5uvNLVm-gCgMenA`). Le tableau Studio confirme « Test A/B en cours » pour chacun. La demande de Lou autorise leur lancement. Les tests des émissions complètes, déjà actifs, sont conservés.

| Extrait                      | Identifiant | Vues au lancement |
| ---------------------------- | ----------- | ----------------: |
| Sillage                      | RijXj9iSR94 |                 5 |
| Codex, Claude Code, OpenCode | OQxyNKJblfI |                47 |
| Réécrire le code legacy      | dDKvDcYLaz4 |                13 |
| Artisans et commerçants      | QbhrC25L3sU |                 6 |
| Lire les tickets             | MT1VIi7P3P4 |                19 |

Pour chaque vidéo, A est la miniature actuelle, B une composition sombre avec un portrait agrandi et C une composition claire avec une autre accroche. Les portraits viennent des fichiers existants du site. Le script Pillow compose les images en 1280 × 720 ; aucun visage n’a été généré. Les titres des vidéos restent identiques : le test porte uniquement sur les miniatures. Le test compare des compositions complètes ; il ne permet pas d’attribuer un éventuel écart à la seule couleur ou au seul texte.

Les exports, le script, le manifeste et les captures Studio sont dans `exports/reseaux-sociaux/extraits-abc-2026-10-26/`. Les fichiers A locaux reproduisent les sources du pipeline ; le témoin réellement testé est la miniature déjà présente dans Studio, conservée sans réimportation. Studio annonce jusqu’à deux semaines pour les résultats. Aucun gagnant n’est encore établi. Les impressions et le CTR des extraits n’ont pas été relevés ; les vues seules ne démontrent pas une faiblesse des miniatures.

## Cinéma local

La pagination limitait le mur à deux replays. Elle utilise maintenant les six cadres existants, du plus récent au plus ancien. Avec trois épisodes, tous apparaissent sur la première page et la pagination est masquée. Le parcours mobile conserve des liens dans le flux, avec retour à la ligne des affiches.

L’épisode 3 reçoit le titre court « Vibe coding en production », traduit en anglais, espagnol et allemand. En l’absence d’affiche cinéma dédiée, le composant affiche la miniature entière dans la partie haute et le titre HTML dessous. Les épisodes disposant d’une affiche dédiée conservent leur composition.

Choix local réversible, décidé par l’agent sur délégation (PD-0003). Aucun commit, push ni déploiement du site n’est effectué.

## Vérification

- Les 68 tests ciblés passent : pagination, présence des trois épisodes, titre court, repli de miniature, localisation et intégration des salles.
- Le contrôle TypeScript du dépôt passe, ainsi que le lint ciblé des fichiers TypeScript modifiés.
- `pnpm test` passe, dont les 153 fichiers et 1 260 tests du site, les tests vidéo et les 24 tests du conducteur expérimental.
- La recette navigateur à 1855 × 1234 et 375 × 812 confirme les trois liens d’épisode, trois images chargées et aucun débordement horizontal sur mobile. Elle utilise une route temporaire avec trois épisodes de test, retirée après contrôle. Les captures sont dans `.local/cinema-fixed-2026-10-26.png` et `.local/cinema-mobile-fixed-2026-10-26.png`. Le contenu local ordinaire ne contient que le pilote ; les données publiées ne sont pas modifiées.
- Le serveur Turbopack a rencontré une erreur de compilation CJS asynchrone pendant le rechargement. La recette visuelle a abouti avec Webpack.
- `pnpm check` échoue au formatage sur 100 fichiers du lot déjà présent, notamment les exports de l’épisode 3. Le lint global signale 7 140 erreurs, notamment dans les copies de GSAP minifié de ces exports. Ces fichiers n’ont pas été modifiés pour contourner les contrôles.

Les résultats des tests YouTube restent à consulter dans Studio à l’issue des expériences. La correction du site reste locale.

À la demande de Lou, l’aperçu des trois épisodes est rouvert sur `http://localhost:3011/cinema-local-qa#room-cinema`. La route est réservée au développement, exclue de l’indexation et renvoie 404 en production. Elle utilise des données de présentation locales sans modifier les épisodes publiés.
