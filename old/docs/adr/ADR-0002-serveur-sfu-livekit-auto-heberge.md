# ADR-0002 — Serveur média (SFU) : LiveKit auto-hébergé

- Statut : acceptée sous réserve du POC 1
- Date : 2026-10-05

## Contexte

Le SFU est le socle du Media Plane. Il détermine les coûts, l'adaptation de débit, la reconnexion et la possibilité de tester en local. Le prompt maître exclut un SFU développé en interne.

## Question posée

Quel SFU utiliser pour le MVP ?

## Facteurs de décision

Tests locaux reproductibles, maîtrise des coûts, simulcast et adaptation de débit, SDK JavaScript, possibilité de passer à une offre managée sans changer de protocole.

## Options considérées

- A. LiveKit auto-hébergé : open source, exécutable dans Docker, SDK JS. SFU et TURN à exploiter soi-même.
- B. LiveKit Cloud : mise en route la plus rapide, coût récurrent, dépendance fournisseur.
- C. mediasoup : contrôle fin, mais signaling, reconnexion, simulcast et enregistrement à construire.
- D. Autre service managé : intégration rapide, enregistrement multipiste souvent limité.

## Décision

Option A (recommandée), retenue.

## Conséquences

- L'infrastructure du SFU et de TURN est décrite en Infrastructure as Code et exploitée par l'équipe.
- Le POC 1 s'exécute d'abord en local avec Docker Compose.
- Le contrôle de la couche média reste derrière une interface mince côté Control Plane, pour garder la possibilité de passer à LiveKit Cloud.
- La question de l'hébergement et de la région reste ouverte et doit être tranchée avant la mise en production.

## Risques

- Sous Docker Windows, le trafic UDP WebRTC dans un conteneur demande une configuration de ports. À valider dans le POC 1. Docker Desktop n'était pas démarré lors de l'audit du 2026-10-05.
- Exploitation de TURN (IP publique, ports UDP, supervision) à la charge de l'équipe.
- Charge réelle à 5 participants inconnue tant que le POC 1 n'a pas mesuré.

## Plan de validation

POC 1 : 3 clients, puis 5, stats WebRTC collectées, réseau dégradé, reconnexion, TURN forcé. Si le POC échoue sur la stabilité ou le coût d'exploitation, rouvrir la question avec l'option B.
