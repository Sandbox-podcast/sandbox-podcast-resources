---
name: sandbox-veille-chaines
description: Lancer la veille YouTube de SANDBOX (46 chaînes IA US et FR), lire les vidéos qui surperforment et proposer les sujets de la semaine ou une alerte Radar. À utiliser le lundi matin, quand un gros modèle sort, ou quand Lou, Nicolas ou Loïc demandent "qu'est-ce qui marche en ce moment".
---

# Veille SANDBOX

## Lancer

Depuis la racine du dépôt :

```sh
python -I projects/ligne-editoriale/scripts/veille.py --n 40
python -I projects/ligne-editoriale/scripts/analyse.py
```

Le script lit les 40 dernières vidéos de chaque chaîne de `projects/ligne-editoriale/scripts/watchlist.json` avec yt-dlp (pas de clé d'API), puis écrit `projects/ligne-editoriale/rapports/veille-AAAA-MM-JJ.md`. Un relevé du jour déjà présent dans `projects/ligne-editoriale/data/veille/AAAA-MM-JJ/raw/` est réutilisé ; le supprimer pour relire une chaîne.

Le score d'une vidéo est ses vues divisées par la médiane de sa chaîne. Un score de 3 veut dire "3 fois mieux que d'habitude sur cette chaîne". Les âges au-delà de 4 semaines sont approximatifs (YouTube affiche "il y a 1 mois").

## Lire le rapport

1. Sujets à score 2 ou plus des 30 derniers jours. Garder ceux qui passent le filtre ci-dessous.
2. Vidéos de moins de 5 jours à score 1,5 ou plus : c'est la vague en cours.
3. Taux de réussite par thème : sert à choisir entre deux sujets équivalents.

Filtre SANDBOX, un sujet passe s'il a au moins 3 oui :

- Un dev, un PM ou un CTO a une raison concrète de regarder.
- Au moins l'un de nous trois a un avis tranché ou une expérience dessus.
- On peut le montrer à l'écran (démo, test, chiffre).
- Il y a un désaccord possible entre nous.
- Aucune chaîne française de la watchlist ne l'a encore traité avec un score de 2 ou plus.

## Alerte Radar

Déclencher une alerte quand, sur 72 heures, au moins deux chaînes US publient sur le même produit ou le même événement avec un score de 1,5 ou plus. Écrire à l'équipe : le sujet, les deux vidéos (lien, score, âge), l'angle SANDBOX proposé en une phrase et la date limite de publication (48 heures après l'alerte).

Exemples relevés le 12 novembre 2026 : la vague Fable 5.2 (Nick Saraev x3,6 et Matthew Berman x2,0 en 2 jours) ; deux sujets US repris en France quelques semaines plus tard par Shubham SHARMA (le dépôt GitHub qui copie n'importe quelle app, x14,4 chez Nick Saraev puis x3,4 en France ; la même app à chaque niveau d'effort, x4,4 chez Nate Herk puis x2,5 en France). Le délai entre la vidéo US et sa reprise française est la fenêtre où SANDBOX peut arriver premier.

## Livrer

Un message court ou `projects/ligne-editoriale/rapports/sujets-AAAA-MM-JJ.md` avec :

- 3 sujets pour la semaine, un par format (Clash, Build, Radar), chacun avec le signal (vidéo, chaîne, score), l'angle SANDBOX et un titre provisoire.
- L'alerte Radar s'il y en a une.
- Les sujets écartés en une ligne chacun, avec la raison.

Ne jamais recopier un titre US. Reprendre la tension du sujet, pas sa formulation. Ne pas présenter un score comme une promesse de vues.

## Ajouter une chaîne

Ajouter une ligne dans `projects/ligne-editoriale/scripts/watchlist.json` (handle sans @, nom, groupe, langue). Vérifier le handle en ouvrant `https://www.youtube.com/@handle/videos`.
