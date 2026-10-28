# PD-0003 — Délégation des décisions à l'agent

- Statut : acceptée
- Date : 2026-10-05

## Contexte

Le prompt maître (§0) impose de poser un QCM pour toute décision structurante. Après les premières décisions et le POC 3, le propriétaire a demandé de continuer sans s'arrêter jusqu'à la fin, de prendre les décisions soi-même et de se faire confiance.

## Décision

L'agent tranche lui-même les décisions structurantes restantes, sans poser de QCM. Chacune est consignée dans un ADR, une PD ou une DD, avec la mention « décidée par l'agent sur délégation (PD-0003) », les options considérées et les motifs. Le propriétaire peut les relire et les renverser à tout moment.

## Ce qui reste soumis à validation du propriétaire

La délégation couvre les choix de conception et d'outillage. Elle ne couvre pas :

- les dépenses, abonnements, comptes ou services payants ;
- la publication, l'envoi de messages ou toute action visible à l'extérieur ;
- la suppression de données qui ne sont pas des artefacts de test ;
- les engagements juridiques (consentement, cadre légal, conditions d'utilisation) ;
- les commits et pushes git ;
- les changements des réglages système de la machine.

Ces points restent à demander ou à signaler comme non faits.

## Conséquences

- Le §0 du prompt maître est suspendu pour les décisions de conception tant que cette délégation est active.
- Les décisions prises sans QCM doivent rester faciles à renverser : isolées derrière une interface ou une configuration quand c'est possible.
- Un résultat de POC qui contredit une décision déléguée la remet en cause, comme avant.
- `docs/open-questions.md` reste la liste des sujets réservés au propriétaire.
