# Mise en production du site Sandbox — 7 octobre 2026

## État vérifié

- Projet Vercel : [`sandboxpodcastpro-5518/sandbox-podcast`](https://vercel.com/sandboxpodcastpro-5518/sandbox-podcast), domaine `www.sandboxpodcast.fr`.
- Production : toujours sur `main` au commit `9446bf9` (fusion de la PR #2). Le nouveau site n'y est pas encore publié.
- [PR #3](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/3) : ouverte et prête pour revue. Sa branche distante est au commit `292fc22`. La CI GitHub et le déploiement de prévisualisation sont passés après correction du dossier racine.
- Branche locale `codex/site-sync-2026-10-07` : un commit de fusion avec `main` comme second parent résout les conflits avec la PR #2 dans `apps/site`, conserve le code de conduite de `main` et adapte les dépendances et tests Postgres. Format, lint, typecheck et build ont réussi localement. Les tests locaux n'ont pas été lancés ; la CI de la branche distante les a exécutés avant ce commit.
- Vercel : le dossier racine est maintenant `apps/site`. L'intégration Neon fournit `DATABASE_URL` et `POSTGRES_URL` à Production et Preview. `SITE_ADMIN_USERS` et `SITE_ADMIN_SECRET` ont été ajoutés comme **secrets** aux deux environnements. Le [nouveau déploiement Preview](https://vercel.com/sandboxpodcastpro-5518/sandbox-podcast/8bhzZjkrUL85nwc1MW8zx9QCxbRZ) est prêt et son `/admin` affiche le formulaire de connexion.
- `SITE_DATA_MODE=mock` et `noindex` doivent rester actifs tant que les épisodes et classements sont simulés.

## Blocage GitHub

Le compte Git local `louhuss` n'a pas le droit de pousser sur `Sandbox-podcast/sandbox-podcast-site`. Le contrôle automatique a refusé une reconnexion GitHub CLI donnant accès à tous les dépôts privés. Un jeton limité au seul dépôt, avec droits Contents et Pull requests en lecture/écriture pour sept jours, a été demandé. GitHub le marque **Pending** : un administrateur de l'organisation `Sandbox-podcast` doit approuver la demande intitulée « Sandbox podcast site PR3 ». Aucun jeton n'est enregistré dans Git ni dans ce document.

Une fois l'accès approuvé : pousser uniquement `codex/site-sync-2026-10-07`, attendre la CI et la prévisualisation du nouveau commit, puis fusionner la PR #3. Ne pas pousser directement sur `main`. La fusion déclenchera le déploiement de Production.

La [PR #6](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/6), encore ouverte, modifie l'ancienne application à la racine du dépôt. Son dernier déploiement Preview échoue. Elle doit être portée dans `apps/site` après la PR #3, puis sa migration `admin_users` et l'initialisation des comptes doivent être vérifiées avant fusion. La PR #2 est déjà fusionnée ; il n'y a que ces deux PR ouvertes.

## Vérifications restantes

1. Appliquer la migration Postgres par `pnpm --filter @podcast/site db:migrate` avec `DATABASE_URL` du projet, puis vérifier la lecture et l'enregistrement d'un brouillon admin. Ne pas réexécuter un seed sur une publication existante.
2. Après fusion, vérifier `https://www.sandboxpodcast.fr/`, `/episodes`, `/charts` et `/admin`, ainsi que le commit de Production dans Vercel.
3. Révoquer le jeton GitHub temporaire après usage, ou le laisser expirer au plus tard le 14 octobre 2026.
