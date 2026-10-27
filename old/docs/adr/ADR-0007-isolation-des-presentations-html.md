# ADR-0007 — Isolation des présentations HTML

- Statut : acceptée
- Date : 2026-10-05
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

Les présentations HTML, CSS et JavaScript sont générées par une IA ou écrites par un utilisateur, puis affichées dans le studio. C'est du code non fiable, qui ne doit accéder ni aux cookies, ni aux jetons, ni au DOM de l'application, ni au réseau interne (§14.1 et §27.4 du prompt maître).

## Options considérées

- A. Rendre le HTML directement dans l'application après nettoyage : une faille de nettoyage donne un accès complet. Écartée.
- B. Iframe avec `sandbox` seulement : protège peu contre l'exfiltration réseau, et dépend d'un attribut que le code de l'application peut mal régler.
- C. Origine dédiée, iframe en `sandbox="allow-scripts"` sans `allow-same-origin`, en-tête CSP strict, messages validés : trois couches indépendantes.
- D. Exécution sur un serveur (rendu en images) : perd l'interactivité.

## Décision

Option C, avec ces règles :

1. Les présentations sont servies par une origine différente de celle de l'application (autre site), avec `presentationHeaders` (CSP, `nosniff`, `no-referrer`, permissions désactivées).
2. L'iframe porte `sandbox="allow-scripts"` seul. `allow-same-origin`, les popups, les formulaires, la navigation de la page principale, les téléchargements et les modales sont interdits.
3. La CSP coupe tout réseau et toute ressource externe, interdit `eval` et inclut la directive `sandbox`, qui s'applique aussi si la page est ouverte directement.
4. La présentation ne parle à l'application que par trois messages `postMessage` validés par un schéma strict, et seulement s'ils viennent de la fenêtre de l'iframe.
5. `frameAncestors` est un paramètre obligatoire : l'origine de l'application, jamais `'self'`.
6. Les assets d'une présentation sont embarqués (`data:` ou `blob:`) : aucune ressource réseau.

## Conséquences

- Aucun accès aux secrets de l'application, démontré par 24 attaques et 2 messages forgés dans Chrome et par le comptage des requêtes reçues.
- Une boucle infinie dans une présentation ne gèle pas l'application (iframe dans un autre processus), mais elle consomme un cœur : un chien de garde reste à écrire.
- Pas de polices ni d'API externes dans les présentations. Une IA qui génère des présentations doit le savoir : `validatePresentationHtml` lui signale ces cas.
- Les couches se doublent : il faut en affaiblir deux pour ouvrir une brèche.

## Risques

- Une mauvaise configuration du serveur de production (CSP absente, même origine que l'application) annule la protection. Le contrôle négatif du banc montre l'ampleur des dégâts. À vérifier à chaque déploiement.
- Navigateurs autres que Chrome : non testés.

## Plan de validation

`pnpm test` lance le banc dans Chrome. En production : vérifier les en-têtes de la route des présentations, et le domaine.
