# Écarts entre l'accueil local et la production

Le 16 octobre 2026, Lou signale un rendu différent sur `www.sandboxpodcast.fr`. La comparaison dans le navigateur avec le serveur local `127.0.0.1:3219`, à 1440 x 900 pixels, confirme les écarts suivants.

## Portrait du plateau

La production affiche pour Nicolas une photo rectangulaire avec fond bleu et microphone, chargée depuis `/api/host-photos/`. Le local utilise `/images/home/nicolas-body-no-mic-v2.webp`.

Dans `discovery-home.tsx`, le détourage était choisi seulement si l'adresse de la photo éditoriale correspondait exactement au chemin source du dépôt. Une photo importée dans l'administration faisait donc perdre le détourage, malgré la présence du bon asset dans le code.

La correction locale utilise le portrait de composition associé au slug de chaque animateur. Elle conserve la condition de présence d'une photo et ne modifie aucune photo éditoriale. C'est une correction de l'intention existante de DD-0038. Les proportions et repères de placement continuent ainsi de correspondre aux assets prévus pour le plateau.

Un test de rendu simule les trois photos servies par `/api/host-photos/` et vérifie que le plateau utilise toujours les trois détourages.

## Données et accès différents

- Spotify : le local pointe vers la chaîne configurée dans `content/site.json`. La production affiche un bouton désactivé et un lien de pied de page vers l'accueil Spotify. Le contenu publié est chargé depuis Postgres en production et depuis le stockage local en développement. Un déploiement du code seul ne synchronise pas ces réglages.
- Vidéoclub : le lien et la page sont réservés à `NODE_ENV === 'development'`. Cette restriction est explicite dans la page d'accueil et la route du vidéoclub, conformément au périmètre local documenté dans DD-0039. Son ouverture publique reste à décider et à valider.
- Des liens sociaux diffèrent aussi entre les deux jeux de contenu. Ne pas remplacer globalement les données publiées par les données locales.

## Vérification et limites

Le contrôle visuel à dimensions identiques confirme le décor et les positions des deux autres animateurs. Le portrait local corrigé est détouré, sans fond rectangulaire ni micro. Les 25 tests du fichier `discovery-refonte.test.ts` passent, dont le nouveau cas avec des photos importées.

`pnpm check` réussit : formatage, lint, TypeScript, 657 tests du site, 11 tests média et 21 tests BIS. Aucun test ni contrôle n'est désactivé.

Le connecteur Vercel ne donne pas accès au déploiement indiqué dans le rapport de mise en service. Le commit servi n'est donc pas recertifié par cette inspection. Les constats sur le rendu viennent directement du navigateur public.

Aucune donnée distante, publication, PR, commit ou push n'est effectué pendant ce diagnostic.

## Correction complète demandée ensuite

Lou demande de tout corriger, puis de vérifier les routes, URL et images. [DD-0047](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0047-parite-accueil-production.md) fixe le comportement corrigé : détourages indépendants des imports de photos, compatibilité des anciennes URL Spotify génériques, vidéoclub accessible en production et routes dans les quatre langues. Le pied de page utilise le même lien Spotify que l'accueil. Les autres données éditoriales restent inchangées.

Les 46 tests ciblés passent hors du bac à sable Windows. Deux essais dans le bac à sable ont échoué avant les assertions, faute de fichiers temporaires de transformation Vitest. Aucun test n'a été désactivé.

## Images de partage découvertes pendant la recette étendue

Le parcours HTTP de la production contrôle 624 URL et 1 386 ressources. Il constate les huit variantes indisponibles du vidéoclub, huit images de partage de classements en erreur 500 et l'image Skills en 404. Les autres réponses sont valides ; aucune ancre cassée n'est détectée dans le HTML parcouru.

Les traces du build initial ne contiennent aucun des cinq fichiers WOFF lus par `og.tsx`. Le rendu local dispose de `node_modules` complet, alors que les fonctions déployées dépendent des fichiers tracés. Le correctif ajoute explicitement ces cinq polices à `outputFileTracingIncludes`, selon la [documentation Next.js](https://nextjs.org/docs/app/api-reference/config/next-config-js/output). Le nouveau test `test:og:tracing` échoue sur l'ancien build et réussit après correction pour 13 routes OpenGraph. Sans accès aux logs distants, cela démontre le défaut d'emballage et sa correction locale, mais la disparition des erreurs 500 doit être confirmée après livraison.

Pour Skills, `/charts/skills/[platform]` intercepte l'adresse de l'image issue de `/charts/[slug]`. Une page Skills explicite et son image dédiée retirent cette ambiguïté. Le test HTTP lit l'adresse réellement annoncée dans les métadonnées, puis demande le PNG, au lieu de reconstruire une adresse supposée.

## Couverture des contrôles

- Les 328 fichiers PNG, JPEG, WebP et SVG de `public/` se décodent intégralement avec Sharp.
- Le parcours du premier build corrigé valide 228 URL et 1 321 ressources locales, y compris les images optimisées, les images de partage, les fichiers publics, les styles, scripts et polices. Le scanner normalise les URL canoniques locales vers le port du serveur de recette. Une référence interne à un filtre SVG avait d'abord été prise pour un fichier ; le scanner est corrigé et le parcours relancé.
- Les 310 destinations externes uniques des deux parcours sont demandées en lecture seule : 280 réponses 200, 28 refus 403, une réponse 202 d'IEEE et une connexion fermée par `travail-emploi.gouv.fr`. Aucun 404 externe n'est observé. Les 30 derniers cas ne sont pas certifiés accessibles ; aucun lien source n'est supprimé sur la seule base d'un refus automatisé.
- Le parcours navigateur du build de production vérifie la porte, la sélection de Sillage, l'ouverture de la boîte, la vidéo (lecture à plus de 33 secondes, sans erreur), la fermeture, la recherche sans résultat, sa remise à zéro et le retour au plateau. Aucun débordement horizontal ni image chargée en erreur sur la fiche inspectée. L'accueil mobile affiche Spotify et la vignette du vidéoclub.

Les rapports détaillés restent dans `apps/site/.local/` : `audit-live.json`, `audit-local-production.json`, `audit-external-all.json` et `images-report.json`. La recette n'écrit aucune donnée en production. Les routes privées et API de mutation sont couvertes par les tests dédiés, pas par des soumissions du robot sur le site public. Les URL arbitraires et combinaisons infinies de paramètres ne peuvent pas être garanties par ce parcours des liens publiés.

## Lot regroupé pour la PR

Lou autorise ensuite le regroupement dans une PR, puis demande explicitement d'y inclure les [cartes holographiques compactes](cartes-holo-compactes-2026-10-16.md) de l'autre conversation. Les PR 69 et 70 étant déjà fusionnées, la branche `codex/parite-production-cartes` repart de `main` au commit `3ae8653`. Elle conserve ainsi la publication du lecteur BIS et ajoute ce lot de corrections.

Validation du lot regroupé :

- `pnpm check` réussit : formatage, lint, types, 662 tests du site, 11 tests médias et 22 tests BIS.
- `pnpm build` réussit : 203 pages statiques générées.
- `test:public-routes` réussit avec sa base de données jetable : 84 URL du sitemap et 34 contrôles HTTP, dont les adresses OpenGraph extraites des pages.
- `test:og:tracing` confirme les cinq polices dans les 13 fonctions OpenGraph du build final.
- `test:admin:http` et `test:badges:http` réussissent avec la base désactivée, y compris les refus et indisponibilités attendus.
- Le nouveau parcours du build de production valide 228 URL et 1 346 ressources, sans réponse cassée ni ancre manquante. Il inclut les fichiers du lecteur BIS désormais présent sur `main`.
- Les 344 images publiques du lot regroupé se décodent intégralement.
- L'audit des dépendances ne signale aucune vulnérabilité connue.
- La navigation anglaise entre l'accueil et le vidéoclub conserve `/en`, y compris au retour. Les liens vers le catalogue et les fiches complètes conservent aussi la langue choisie. Le parcours mobile Okodukai ouvre la fiche et revient au plateau sans débordement ni image cassée.
- Les cartes compactes sont mesurées à 320, 390, 768 et 1440 pixels : légende entre 15,2 % et 21,5 % de la hauteur, prénom de 30 à 32 pixels, aucun débordement horizontal.

La confirmation des corrections sur le domaine public reste à effectuer après fusion et déploiement. Les 30 liens externes non certifiés lors du parcours initial restent signalés plus haut.
