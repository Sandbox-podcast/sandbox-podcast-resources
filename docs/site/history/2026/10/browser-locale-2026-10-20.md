# Langue à l'arrivée sur le site

20 octobre 2026. À la demande de Lou, l'entrée par `/` choisit une langue à partir du navigateur. Une préférence enregistrée dans le sélecteur de langue reste prioritaire. Le périmètre de la redirection est limité à l'accueil, décision locale et réversible décidée par l'agent sur délégation (PD-0003).

Le proxy examine les requêtes GET et HEAD vers `/`, hors du sous-domaine des présentations. Il valide d'abord le cookie fonctionnel `sandbox-locale`. En son absence, ou si sa valeur est invalide, il classe les langues de `Accept-Language` par leur poids `q`, puis retient la première langue disponible. Les variantes régionales françaises, anglaises, espagnoles et allemandes correspondent respectivement à `fr-FR`, `en`, `es-ES` et `de-DE`. Le français sert de repli.

Le sélecteur écrit la langue choisie dans un cookie valable un an, avec `Path=/`, `SameSite=Lax` et `Secure` en HTTPS. Le choix du français est enregistré comme les autres. Une redirection temporaire 307 conserve les paramètres de recherche ; sa réponse est privée, non stockable, et varie selon `Accept-Language` et `Cookie`.

Un chemin explicite reste inchangé : `/en`, `/es-es`, `/de-de`, mais aussi une page française telle que `/about`. Les routes d'administration, les API, les fichiers, les présentations et `/time-machine` ne sont pas concernés. La langue d'une URL partagée est donc respectée, même si elle diffère de la préférence enregistrée.

## Vérification exécutée

- 32 tests ciblés réussis : préférence navigateur, poids, langue inconnue, cookie invalide, choix manuel, URL explicite, absence de boucle, administration, présentations et route d'épisode.
- Navigateur Edge local : arrivée anglaise vers `/en`, espagnole vers `/es-es`, allemande vers `/de-de`, japonaise vers `/`.
- Clic réel dans le sélecteur : choix français conservé après retour à `/` avec navigateur anglais ; choix allemand conservé ensuite ; ouverture explicite de `/en` respectée malgré le cookie allemand.
- Rapport local : `apps/site/.local/browser-locale/report.json`.

Les recettes qui attendent le français doivent fixer `locale: 'fr-FR'` dans le contexte Playwright, ou envoyer `Accept-Language: fr-FR` pour les requêtes HTTP directes. Ce contrôle ciblé ne remplace pas les gates globaux du dépôt.
