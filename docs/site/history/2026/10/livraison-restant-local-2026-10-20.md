# Livraison du travail local restant du 20 octobre 2026

Lou demande une PR unique avec tout le travail encore local. La branche part de `origin/main` au commit `fe23ed7`, après fusion de la PR 101. La copie de travail partagée était encore positionnée sur la branche de la PR 77 ; ses nombreux fichiers modifiés ou non suivis ne représentaient donc pas tous des nouveautés à publier.

## Périmètre

Le rapprochement du contenu avec main révèle 43 différences réelles, après exclusion des seuls changements de fins de ligne. La livraison reprend les évolutions non encore publiées : cartes d’exploration à onglet, quatre destinations conditionnelles, marges de 16 pixels, survol de 8 pixels, ordre repères puis équipe puis projets, accroche courte et aide à la visite traduites, panneau News aligné sur son moniteur et recettes navigateur associées.

Les variantes locales anciennes des workflows Charts, du client GitHub, des diagnostics News et des tests ne remplacent pas leurs corrections déjà fusionnées. Les documents qui décrivent les déploiements réels restent à jour. La frontière de chargement Charts locale n’est pas réintroduite : la PR 101 l’avait écartée pour conserver les statuts 404 des archives absentes. Les corrections du retour de préférence et du contexte WebGL sont conservées. Les médias lourds, fichiers ignorés, archives et migrations déjà publiées ne sont pas réimportés.

La section « Nos expérimentations », déjà présente dans main, est conservée après l’équipe avec ses styles et sa sélection de projets. Son paramètre `projects` reste transmis par `DiscoveryHome`. Ce rapprochement résout les trois erreurs de types et l’échec de test observés dans la copie partagée avant consolidation. Les anciens textes publiés restent reconnus ; les nouvelles variantes d’accroche rejoignent cette compatibilité sans supprimer les précédentes.

## Contrôles

- Les 72 tests ciblés de l’accueil, des textes de marque, du contenu public et des salles passent.
- Le build de production réussit. Les traces de 13 routes OpenGraph contiennent leurs cinq polices.
- L’audit des dépendances ne relève aucune vulnérabilité connue.
- Gitleaks 8.30.1 termine le contrôle du répertoire avec code 0, en masquant les valeurs éventuelles.
- Les recettes précédentes des cartes couvrent dix configurations de 320 à 1440 pixels et les quatre langues ; le Radar dispose de sa recette dédiée. Ces contrôles utilisent Edge headless, sans téléphone physique.

`pnpm check` réussit : formatage, lint, TypeScript, 1 229 tests du site, 7 tests du générique, 4 tests des assets vidéo et 24 tests BIS, soit 1 264 tests. La PR est préparée sans fusion ni déploiement manuel. La copie partagée initiale est conservée ; la branche de livraison se trouve dans le worktree attaché à ce chat.
