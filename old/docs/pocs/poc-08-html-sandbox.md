# POC 8 — Bac à sable des présentations HTML

Résultat : **PASS** dans Chrome 154. Code produit : `packages/presentation-sandbox` (36 tests). Banc d'essai : `pocs/poc-08-html-sandbox` (25 tests dans un vrai Chrome).

Les présentations sont écrites par une IA ou par un utilisateur : c'est du code non fiable. Décision : [ADR-0007](../adr/ADR-0007-isolation-des-presentations-html.md).

## Ce qui est construit

- `presentationCsp` / `presentationHeaders` : en-têtes de l'origine dédiée aux présentations. Aucun réseau (`connect-src 'none'`), seulement des images, polices et médias en `data:` ou `blob:`, scripts et styles inline, aucune frame, aucun formulaire, aucun `eval`, et une directive `sandbox allow-scripts` qui isole aussi la page ouverte seule.
- `iframeAttributes` : `sandbox="allow-scripts"` sans `allow-same-origin`, `allow=""`, `referrerpolicy="no-referrer"`. `isSafeSandboxAttribute` refuse les réglages qui annulent l'isolation.
- `parseSandboxMessage` / `isTrustedMessage` : seuls trois messages `postMessage` sont admis (`presentation:ready`, `presentation:slide`, `presentation:resize`), validés par un schéma strict, et seulement s'ils viennent de la fenêtre de l'iframe.
- `validatePresentationHtml` : contrôle statique avant enregistrement (ressources externes, redirections, `<base>`, frames, formulaires, objets, `eval`, taille maximale de 2 Mo). Aide l'auteur, ne remplace pas l'isolation.

## Le banc d'essai

Trois origines locales : l'application (`localhost`), les présentations (`127.0.0.1`, autre site) et un serveur « attaquant ». Une présentation malveillante tente 24 attaques et envoie 2 messages forgés ; l'application détient des secrets (cookie, `localStorage`, route d'API). Le banc compte aussi les requêtes qui arrivent réellement aux serveurs, ce qui prouve l'absence de fuite mieux que le résultat déclaré par l'attaque.

Attaques bloquées (résultat déclaré et aucune requête reçue) : lecture et modification du DOM de l'application, lecture de ses cookies et de son `localStorage`, lecture de ses propres cookies et stockage, navigation de la fenêtre principale, `fetch` vers l'application avec cookies, `fetch` externe, image, script, média, police, feuille de style, objet et worker externes, WebSocket, ouverture de fenêtre, envoi de formulaire, caméra, service worker, cadre imbriqué, `eval`, `new Function`.

Autres vérifications :

- Contrôle positif : la présentation s'exécute et envoie ses messages autorisés.
- Messages : seuls les deux messages valides sont acceptés, les deux forgés (type inconnu, index invalide) sont rejetés.
- Origine opaque : `window.origin` vaut `null`.
- Une boucle infinie dans la présentation ne gèle pas l'application (au moins 10 relevés en 1,5 s, car l'iframe est dans un autre processus).
- Un titre contenant du HTML s'affiche en texte et ne s'exécute pas.
- Ouverte directement (hors iframe), la page reste isolée : origine `null`, cookies et stockage refusés.
- **Contrôle négatif** : avec `allow-same-origin`, sans CSP et sur l'origine de l'application, au moins 8 attaques réussissent, dont la lecture du cookie secret, la modification de l'application et l'envoi vers le serveur attaquant. Le banc détecte donc bien une configuration dangereuse.

## Ce que le banc a révélé

- Ma première CSP contenait `frame-ancestors 'self'`. Chrome refusait alors d'afficher la présentation dans l'application, qui est une autre origine. `frameAncestors` est maintenant un paramètre obligatoire de la politique.
- Plusieurs attaques étaient mal écrites : une lisait `document.cookie` avant d'émettre sa requête et échouait donc pour une autre raison que la CSP ; le cadre imbriqué déclenche `onload` même quand il est bloqué. Des mutations de la politique les ont fait remonter : une politique affaiblie ne faisait échouer aucun test. Les attaques ont été corrigées et, pour le cadre imbriqué, la preuve est côté serveur.

## Sensibilité des tests

Dix affaiblissements de la politique ont été essayés : `connect-src`, `img-src`, `media-src`, `font-src`, `style-src`, `script-src` ouverts, `eval` autorisé, `frame-src` ouvert, `allow-same-origin` ajouté à la CSP, attribut `sandbox` de l'iframe affaibli. Détectés : tous, sauf trois qui sont de la double protection :

- l'attribut `sandbox` de l'iframe seul : la directive `sandbox` de la CSP l'impose de toute façon ;
- `form-action` ouvert : le bac à sable interdit déjà les formulaires ;
- `object-src` ouvert : le bac à sable interdit déjà les objets.

Il faut donc affaiblir deux couches à la fois pour ouvrir une brèche, ce qui est le but.

## Limites

- Chrome 154 seulement, conformément à PD-0001. Safari et Firefox non testés.
- L'origine dédiée est simulée par un autre site local (autre hôte, autre port). En production : un domaine distinct (pas un sous-domaine de l'application si des cookies de domaine existent), servi en HTTPS, avec les en-têtes de `presentationHeaders`.
- Les présentations qui ont besoin d'un réseau (polices externes, API) sont refusées. C'est un choix : les assets doivent être embarqués ou fournis en `data:`/`blob:`.
- Le temps CPU et la mémoire d'une présentation ne sont pas limités : une boucle infinie ne gèle pas l'application mais consomme un cœur jusqu'à la fermeture de l'iframe. Un chien de garde (fermer l'iframe si le processus ne répond plus) reste à écrire.
- Le test dépend de Chrome : il est ignoré si Chrome n'est pas installé, ce qui masquerait un défaut. En CI, Chrome doit être présent.
- Pas de scénario d'IA qui injecte des instructions dans une présentation pour manipuler un autre agent (prompt injection) : à traiter avec le MCP (POC 9).

## Suite

Servir les présentations depuis un domaine dédié, chien de garde de ressources, éditeur CODE | PREVIEW, versions et rollback (AC-HTML-001 à 004), test sur d'autres navigateurs si PD-0001 évolue.
