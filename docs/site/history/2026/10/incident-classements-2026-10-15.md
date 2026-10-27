# Classements : incident du 15 octobre 2026

## État vérifié

L'investigation part de `origin/main` au commit `e29f09cd21656fb7fbf2f929c30f1a26b32e8bf4`, dans un worktree séparé pour préserver les travaux locaux.

| Contrôle       | Résultat                                                                               |
| -------------- | -------------------------------------------------------------------------------------- |
| GitHub public  | Édition du 10 octobre, ancien score `github-momentum-v1+stars`                         |
| Skills public  | Édition du 10 octobre, ancien score `skills-installs-v1`                               |
| Models public  | Édition du 12 octobre, ancien score `models-cross-source-v1`                           |
| Rising         | Pas d'édition publique                                                                 |
| GitHub Actions | Origine et secret absents ; échecs avant appel des collecteurs                         |
| Vercel         | `vercel.json` sans cron ; CLI et connecteur sur un compte différent de celui du projet |

Depuis l'administration connectée par Lou, une collecte GitHub du 15 octobre a enregistré 616 relevés sur 620 traitements ; quatre dépôts ont échoué. Le tableau affiche 1 210 dépôts suivis et 10 963 candidats. La collecte externe a enregistré 1 134 skills et 1 017 entités Models ; le catalogue OpenRouter a échoué.

La simulation externe suivant ces collectes annonce 34 identités Models contradictoires, 1 225 skills hors pool éligible, zéro skill et six modèles disposant des preuves requises. Elle n'écrit aucune édition. Ces résultats ne justifient pas de publier un Top 20.

La réparation OpenRouter a été vérifiée sur son API publique avec le client corrigé : 576 modèles validés, dont 84 sans contexte textuel applicable. Les résultats dépendent du catalogue au moment de l'appel.

## Corrections déployées

La [PR #65](https://github.com/Sandbox-podcast/sandbox-podcast-site/pull/65) a été fusionnée et déployée le 15 octobre au commit `1599f99d947a26d6c0acbe7c6e457867af5fdd32`. `pnpm check` a réussi avec 429 tests du site et 11 tests vidéo. Le build Turbopack, la CI, l'audit des dépendances et le scan de secrets ont réussi. L'essai complémentaire Webpack a échoué sur des contrats de pages ; ce n'est pas la commande de build du projet.

Après déploiement, les reprises GitHub ont ajouté 620 puis 403 relevés, portant le total du jour à 1 639. Les dépôts suivis ont été collectés ; quatre candidats restent inaccessibles. Models a enregistré 1 592 entités sans erreur de collecte, Skills 1 134 avec un dépôt inaccessible.

Les simulations finales donnent zéro projet GitHub éligible, zéro skill et six modèles admissibles. Elles signalent 36 identités Models contradictoires. Aucune nouvelle édition n'a été publiée. Le [test du workflow](https://github.com/Sandbox-podcast/sandbox-podcast-site/actions/runs/38715345103) échoue explicitement sur le secret GitHub Actions absent.

Voir [ADR-0030](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/adr/ADR-0030-reprise-et-controle-des-classements.md). Les changements couvrent le workflow, le pilote de reprise, les routes cron isolées, la priorité aux dépôts suivis, la lecture des collectes historiques, OpenRouter, l'invalidation des pages et l'affichage d'un retard. Aucun changement de migration ou suppression de données.

Tests de régression : collecte suivie prioritaire malgré un grand nombre de candidats, reprise bornée après panne, indépendance des sources, refus d'un faux succès avec édition ancienne, authentification de chaque nouvelle route, gel isolé, invalidation des pages, collecte historique non masquée et catalogue comprenant des modèles non textuels.

## Mise en service à terminer

Lou a demandé une prise en charge par le tech lead, via une PR laissée ouverte pour revue, faute d'accès GitHub et Vercel. La [fiche d'intervention du tech lead](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/site/reprise-classements-techlead.md) précise les réglages, les contrôles et les critères de clôture.

1. Vérifier le déploiement existant de la PR #65. Cette étape est réalisée ; les blocages restants concernent la configuration et les données.
2. Dans `Sandbox-podcast/sandbox-podcast-site`, configurer le secret Actions `SANDBOX_CHARTS_CRON_SECRET` avec la valeur existante de `CRON_SECRET` du projet Vercel `sandboxpodcastpro-5518/sandbox-podcast`. Ne pas l'écrire dans Git ou dans le chat. `SANDBOX_CHARTS_ORIGIN` est désormais facultatif ; sa valeur éventuelle est `https://www.sandboxpodcast.fr`.
3. Déclencher manuellement `SANDBOX CHARTS refresh`. Examiner les trois lignes du résumé et les journaux administrateur. Une collecte enregistrée ne suffit pas : les trois éditions publiques doivent correspondre au créneau attendu.
4. Corriger les rapprochements Models à partir des identités exactes des fournisseurs ; conserver séparés les modèles ambigus. Vérifier les baselines GitHub et Skills et les preuves OpenSSF. Ne pas utiliser les compteurs actuels comme observations des jours passés.
5. Faire la revue des profils conformément à [la procédure v3](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/site/reference-ranking-operations.md), puis autoriser uniquement les versions effectivement relues. Aucun profil n'a été activé pendant cette intervention.
6. Vérifier les deux prochaines exécutions programmées et le contrôle horaire. Confirmer les notifications d'échec dans les réglages GitHub du responsable.

Contrôle public sans secret, depuis la racine :

```bash
node apps/site/scripts/charts-refresh.ts --check
```

Le 15 octobre, ce contrôle échoue correctement et identifie les trois éditions en retard. Tant que ce contrôle échoue, la remise en service n'est pas validée.

## Historique manquant

L'administration ne permet pas d'inventer des observations pour les jours omis. Un rejeu est admissible uniquement pour les créneaux disposant de relevés conservés et des preuves exigées. Le correctif de recherche historique rend ce rejeu possible sans qu'un job plus récent masque l'ancien ; il ne garantit pas que tous les jours du 10 au 15 soient calculables. Les éditions déjà publiées restent intactes.
