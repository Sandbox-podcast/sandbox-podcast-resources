# Modèle de domaine

Date : 2026-10-06. Ce document décrit les entités du noyau serveur (`apps/api`) et leurs relations. Le schéma SQL fait foi : `apps/api/src/db/migrations/`.

## Entités

| Entité                                        | Rôle                                                                                                                                               | Clés et contraintes principales                            |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `users`                                       | Compte d'une personne. E-mail en minuscules, mot de passe haché (scrypt).                                                                          | e-mail unique ; jamais de mot de passe en clair            |
| `sessions`                                    | Session ouverte. On ne stocke que l'empreinte du jeton.                                                                                            | expiration, révocation ; jeton aléatoire de 256 bits       |
| `login_failures`                              | Compteur d'échecs de connexion par e-mail, avec verrouillage temporaire.                                                                           |                                                            |
| `podcasts`                                    | Espace d'un podcast : tout ce qui suit lui appartient (isolation entre podcasts).                                                                  |                                                            |
| `memberships`                                 | Rôle d'un utilisateur dans un podcast : `ADMIN`, `PRODUCER`, `HOST`, `EDITOR`, `VIEWER`.                                                           | clé (podcast, utilisateur)                                 |
| `templates`, `assets`, `themes`               | Catalogues versionnés d'un podcast (versions jamais modifiées, seulement ajoutées).                                                                | clé (podcast, id, version)                                 |
| `episodes`                                    | Espace de travail d'un épisode (document structuré de `packages/episode-factory`) et sa révision.                                                  | `podcast_id` obligatoire ; révision optimiste              |
| `episode_idempotency`                         | Clés d'idempotence de création d'épisode et empreinte de la demande.                                                                               | clé (podcast, clé)                                         |
| `studios`, `studio_events`, `studio_commands` | État de régie d'un épisode (`packages/studio-control`), journal des événements, résultats de commandes pour l'idempotence.                         | version optimiste ; clé (épisode, identifiant de commande) |
| `invitations`                                 | Invitation d'un invité à un épisode. On ne stocke que l'empreinte du jeton.                                                                        | usage unique, expiration, révocable                        |
| `participants`                                | Personne présente dans un épisode (membre ou invité). Son **identifiant est l'identité LiveKit** : attribuée par le serveur, jamais choisie.       |                                                            |
| `audit_log`                                   | Journal des actions sensibles : qui, quoi, cible, résultat, corrélation. **Ajout seul** : un déclencheur refuse toute modification ou suppression. | immuable                                                   |
| `schema_migrations`                           | Migrations appliquées avec leur empreinte : modifier un fichier déjà appliqué fait échouer le démarrage.                                           |                                                            |

## Rôles et droits (par podcast)

| Action                                        | ADMIN | PRODUCER | HOST | EDITOR | VIEWER |
| --------------------------------------------- | :---: | :------: | :--: | :----: | :----: |
| Voir le podcast, ses épisodes                 |  oui  |   oui    | oui  |  oui   |  oui   |
| Créer un épisode, inviter, régie, enregistrer |  oui  |   oui    | non  |  non   |  non   |
| Modifier le conducteur (séquences)            |  oui  |   oui    | oui  |  oui   |  non   |
| Gérer les membres                             |  oui  |   non    | non  |  non   |  non   |
| Publier dans le studio (audio, vidéo)         |  oui  |   oui    | oui  |  non   |  non   |

Les invités (`GUEST`) n'ont pas de compte : ils entrent par invitation, avec les droits minimaux d'un épisode (publier leur audio et leur vidéo, voir le studio). Les droits sont vérifiés par le serveur à chaque requête, par la fonction pure `can()` (`apps/api/src/rbac.ts`), testée sans base de données.

## Principes

- Tout accès passe par (podcast, id) : un identifiant d'un autre podcast répond « introuvable ».
- Les identités LiveKit sont des identifiants de `participants`, générés par le serveur : aucun texte libre n'entre dans un chemin de fichier d'enregistrement (voir [threat-model.md](threat-model.md)).
- Aucun secret en base en clair : mots de passe en scrypt avec sel, jetons de session et d'invitation en empreinte SHA-256.
- Une écriture sensible est inscrite dans `audit_log` dans la même transaction que la modification.
