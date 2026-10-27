# Intégration de l'audit du 15 octobre 2026

Le travail reprend les corrections encore isolées dans `audit-confiance-parcours` et les rapproche de `main` après la livraison #67. Suivi : [issue #68](https://github.com/Sandbox-podcast/sandbox-podcast-site/issues/68). Décision : [DD-0029](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/DD-0029-integration-audit-methodes-et-mesure.md).

## Changements

- Dates et version propres à chaque édition, méthode conservée dans les liens, rejet des routes invalides et vue qualité-prix absente pour les anciens scores sans prix.
- Confidentialité, accord et refus datés, retrait, expiration et synchronisation des onglets. GA4 reste bloqué par défaut ; Vercel et les événements de badges relisent le consentement.
- Polices locales avec repli ajusté, présentation du pilote et liens Sillage/épisode/chapitres, sans écraser une rédaction éditoriale différente.
- Lecture bornée des corps JSON administratifs, avec interruption du flux et réponse 413 avant analyse si la limite est dépassée.
- Contrôles HTTP du sitemap et parcours Playwright de consentement intégrés à la CI. Chaque serveur utilise une base éphémère et son propre contenu de test.

Les fichiers Time Machine, les styles du catalogue et les travaux vidéo qui évoluent pendant cette intervention sont conservés. Les anciennes migrations de la copie d'audit ne sont pas reprises.

## Vérification

Contrôles exécutés sur le lot intégré le 15 octobre, avec Node 24.12.0 et pnpm 12.9.1 :

| Contrôle                        | Résultat                                                                                                                                                     |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `pnpm check`                    | Format, lint, types et tests réussis ; 593 tests du site dans 93 fichiers, sept tests du générique et quatre des jingles.                                    |
| `pnpm build`                    | Réussi ; 203 pages statiques générées.                                                                                                                       |
| `test:public-routes`            | 82/82 URL du sitemap local et 29 parcours HTTP complémentaires valides.                                                                                      |
| `test:analytics:e2e`            | 19 contrôles réussis sur Edge, dont tag bloqué, refus, retrait entre onglets, expiration et chargement tardif du tag. Aucun service réel de mesure contacté. |
| `test:badges:e2e`               | 43 contrôles réussis, huit familles, copies, sources, retraits, pagination, clavier et responsive ; aucune erreur JavaScript.                                |
| `test:badges:http`              | Contrôles réussis sur le build de production sans accès à la base distante.                                                                                  |
| `pnpm audit --audit-level=high` | Aucune vulnérabilité connue signalée.                                                                                                                        |
| Gitleaks 8.30.1                 | Aucun secret détecté dans les sources du lot, avec résultats expurgés.                                                                                       |
| Migrations historiques          | Aucun diff SQL dans `apps/site/drizzle`.                                                                                                                     |

Le premier contrôle global révèle des fins de ligne CRLF de checkout. `.gitattributes` impose LF aux textes, avec exemption des migrations historiques et de l'archive. Seules les fins de ligne sont normalisées sur les autres fichiers. Le texte original de la licence de police reste hors formatage.

Deux démarrages PGlite dépassent cinq secondes lors d'un essai avec navigateur concurrent ; la suite complète repasse seule sans changer les délais ni désactiver de test. Le parcours des Awards détecte également une fixture Models sans dimension de qualité : la mesure fictive est rendue explicite dans le jeu local, sans changer les données de production.

Les rapports navigateur sont dans `apps/site/.local/analytics-e2e/` et `apps/site/.local/badges-e2e-56560/`. Les images inspectées contiennent uniquement des fixtures. Le build signale toujours la convention Next `middleware` dépréciée ; ce message ne bloque pas sa compilation.

Commandes depuis la racine :

```powershell
pnpm check
pnpm build
pnpm --filter @podcast/site test:public-routes
pnpm --filter @podcast/site test:analytics:e2e
pnpm --filter @podcast/site test:badges:http
```

Sur Windows, `SANDBOX_BROWSER_CHANNEL=msedge` utilise le navigateur installé. En CI, `playwright install --with-deps chromium` prépare Chromium. Les rapports des nouveaux parcours sont dans `apps/site/.local/analytics-e2e/`. Les services tiers sont simulés ; aucune statistique réelle n'est produite.

## Actions nécessitant l'exploitation

Le flux GA4, sa mesure améliorée et sa conservation de 14 mois restent à vérifier dans le compte avant activation. La réception Vercel/GA4 ne peut pas être déduite des tests locaux. Les migrations Neon, les profils de classement autorisés, le secret du planificateur et les premières attributions réelles restent dans l'issue #68.

Le limiteur des tentatives d'administration reste en mémoire par processus. Une protection distribuée et une CSP sans scripts inline demandent un lot d'architecture et des contrôles de déploiement spécifiques ; les limites actuelles sont explicites. La revue native des traductions et l'accord de diffusion des Shorts restent nécessaires.
