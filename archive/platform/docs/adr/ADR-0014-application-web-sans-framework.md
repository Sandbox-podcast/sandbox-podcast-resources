# ADR-0014 — Application web : TypeScript sans framework, gabarits échappés, même origine que l'API

- Statut : acceptée (à réévaluer si l'interface grossit)
- Date : 2026-10-06
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

L'[ADR-0001](ADR-0001-stack-applicative-et-monorepo.md) cite Next.js. Le noyau serveur ([ADR-0013](ADR-0013-noyau-serveur-api.md)) existe, avec des cookies de session `SameSite=Strict`. Il faut une première interface : connexion, podcasts, épisodes et conducteur, invitations, page de studio du Producer (jeton de salle, régie, enregistrement, consentement), page d'invité (device check, consentement, entrée). Contraintes : sécurité du contenu rendu (AC-SEC-003), pas de jeton lisible par le JavaScript, testabilité sans navigateur, faible empreinte mémoire du poste de développement.

## Décision

1. **TypeScript sans framework d'interface** (`apps/web`), empaqueté par esbuild en un seul `app.js`. Next.js n'apporte rien à cette étape : pas de rendu serveur nécessaire, pas de routage de fichiers, une dépendance et un outillage lourds de plus. L'ADR-0001 n'est pas annulé : on repassera à un framework quand l'interface le justifiera, la logique (`Controller`, `ApiClient`) est indépendante du DOM.
2. **Rendu par gabarits échappés par construction** : le gabarit `html` échappe toute valeur interpolée ; seul un fragment produit par un autre gabarit ou par `raw()` (littéraux du code) passe tel quel. Un titre, un nom ou une note venant du serveur ne peut pas devenir du balisage. Aucun attribut d'événement, aucun script ni style en ligne : les interactions passent par des attributs `data-action` et `data-form` gérés par délégation d'événements.
3. **Même origine que l'API** : l'API sert les pages (`WEB_DIR`) avec la politique de contenu `default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self' ws: wss:; frame-ancestors 'none'…`. Le cookie de session part tout seul, le JavaScript n'en lit jamais la valeur, aucun jeton n'est stocké dans la page ni dans le stockage du navigateur. Le service des fichiers n'accepte qu'une liste d'extensions, refuse les segments cachés, `..`, antislash, octet nul et la sortie du dossier racine.
4. **Une seule action modifiante à la fois** dans l'interface, **clé d'idempotence conservée** par demande de création d'épisode (un double clic ou un rejeu après erreur réseau ne crée qu'un épisode), révision envoyée à chaque modification de séquence (conflit signalé, jamais écrasé), version d'état de la régie rechargée après un refus pour version périmée, session expirée détectée par le code `UNAUTHENTICATED` (et non par un simple 401 : une mauvaise connexion est une erreur, pas une expiration).
5. **Salle LiveKit** : réglages de l'ADR-0006 (H.264, simulcast à deux couches 1080p et 360p, 6 Mb/s, abonnement adaptatif, dynacast). La connexion est derrière une interface injectée : les tests utilisent une fausse salle.
6. **Device check** minimal : test d'accès à la caméra et au micro (relâchés aussitôt), messages d'erreur explicites par type d'échec, bilan des appareils détectés.
7. **États** : chargement, vide, erreur (avec la référence de corrélation du serveur) traités sur chaque page ; libellés d'erreur et de statut annoncés (`role="alert"`, `role="status"`, `aria-live`) ; formulaires avec étiquettes ; thème clair/sombre selon le système.

## Conséquences

- La logique est testée sans navigateur (47 tests : gabarits, routes, vues, contrôleur contre une fausse API). **Le rendu réel dans Chrome, la connexion LiveKit réelle et l'accessibilité au clavier n'ont pas été vérifiés** : le poste de développement manquait de mémoire et le propriétaire a demandé de ne pas lancer de navigateur. Une vérification manuelle ou un test Playwright reste à faire.
- Redessiner toute la page à chaque changement est simple mais coûteux si l'interface grossit ; les valeurs saisies sont conservées d'un rendu à l'autre (sauf mots de passe), pas la position de défilement ni la sélection du texte.
- Pas encore : édition collaborative des présentations dans l'interface, Scene Engine et Preview/Program visuels (la page de studio expose les commandes de régie sous forme de boutons, pas la composition vidéo), post-production.

## Risques

- Le jeton d'invitation est dans le fragment de l'URL (`#/join/…`) : il n'est pas envoyé au serveur dans les journaux d'accès, mais reste dans l'historique du navigateur de l'invité.
- Les liens d'invitation ne s'affichent qu'une fois ; si le Producer ne les copie pas, il doit en recréer.
- La conservation des saisies à l'identifiant d'élément suppose des identifiants uniques et stables dans chaque vue.
