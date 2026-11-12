---
name: sandbox-bilan-youtube
description: Relever dans YouTube Studio les chiffres d'une vidéo SANDBOX à J+2 et J+7 (taux de clics, durée moyenne, abonnés, sources), les comparer aux objectifs et en tirer une décision pour la suivante. À utiliser chaque lundi ou quand l'équipe demande "ça a marché ?".
---

# Bilan SANDBOX

## Relever

Dans YouTube Studio, en lecture seule, onglet Statistiques de la vidéo :

- Impressions et taux de clics sur la miniature.
- Durée moyenne de visionnage et pourcentage regardé.
- Rétention à 30 secondes.
- Vues, abonnés gagnés, sources de trafic.
- Résultat de Tester et comparer s'il est terminé.

Ne rien modifier sur la chaîne pendant le relevé.

## Comparer

Point de départ mesuré sur les vidéos longues, 28 jours au 11 novembre 2026 : taux de clics 2,1 %, durée moyenne 5 min 10, 0 % de spectateurs réguliers.

Objectifs fixés par la ligne éditoriale (ce ne sont pas des moyennes YouTube) :

| Indicateur | 15 décembre 2026 | 15 février 2027 |
|---|---:|---:|
| Taux de clics, vidéos longues | 4 % | 6 % |
| Durée moyenne de visionnage | 7 min | 10 min |
| Vues d'une vidéo longue à 7 jours (médiane) | 300 | 1 500 |
| Spectateurs réguliers | 3 % | 8 % |
| Abonnés | 500 | 2 000 |

## Décider

- Taux de clics sous 3 % après 48 heures : changer la miniature ou le titre (gagnant du test, sinon nouvelle variante).
- Bonne rétention mais peu de clics : le contenu est bon, le packaging ne vend pas. Retravailler titre et miniature, pas le format.
- Beaucoup de clics, départ avant 30 secondes : l'accroche ne tient pas la promesse du titre.
- Un sujet à plus de 3 fois notre médiane : le noter dans le backlog comme thème à décliner.

## Livrer

Ajouter une ligne par vidéo dans `projects/ligne-editoriale/data/bilans.csv` (date, vidéo, format, impressions, taux de clics, durée moyenne, vues J+7, abonnés) et trois lignes de conclusion dans le message à l'équipe. Si un palier n'est pas atteint à sa date, proposer un changement de sujets ou de format plutôt que des réglages.
