# ADR-0012 — Détourage dans le navigateur du Producer, avec régulation de qualité

- Statut : acceptée (à confirmer sur une machine modeste et avec des séquences réelles)
- Date : 2026-10-06
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

Le studio virtuel place les participants détourés dans un décor commun. Le détourage est un calcul continu (30 images/s par participant). Où l'exécuter ? Le propriétaire a demandé que les PC des participants ne soient pas saturés pendant les lives ([ADR-0004](ADR-0004-enregistrement-serveur-par-piste.md)), et la composition du Program se fait déjà dans le navigateur du Producer ([ADR-0003](ADR-0003-composition-du-program-cote-producer.md)).

## Options considérées

- A. **Chez chaque participant**, avant publication. Le détourage ne coûte rien au Producer, mais WebRTC ne transporte pas de canal alpha : il faudrait un fond uni à retirer ou un second flux de masque, et surtout cela charge le PC de chaque invité, ce que le propriétaire veut éviter.
- B. **Chez le Producer**, sur les flux reçus. Une seule machine à dimensionner, aucune exigence pour les invités, les pistes enregistrées restent brutes.
- C. **Sur un serveur GPU.** Cohérent avec l'enregistrement serveur, mais ajoute une infrastructure coûteuse et de la latence.

## Décision

Option B, avec régulation de qualité automatique.

- Le détourage tourne dans le navigateur du Producer sur chaque flux reçu, pour la composition du Program uniquement. **Les pistes enregistrées par le serveur ne sont jamais détourées** : elles restent brutes, et la post-production peut détourer à nouveau, hors ligne, avec un meilleur modèle.
- Le Producer exécute un **contrôleur de qualité** (`packages/scene-quality`) : escalier de 5 niveaux (détourage à chaque image → une image sur 2 → une sur 3 à 360 p → aucun modèle avec cadre adouci → 15 images/s), dégradation d'un niveau après 1,5 s de surcharge, remontée d'un niveau après 15 s de marge, repos de 3 s, interdiction d'un niveau qui vient d'échouer. Le **détourage est dégradé avant la fluidité** : la composition garde 30 images/s tant que possible.
- Le Producer voit le niveau en vigueur et peut le **verrouiller** (par exemple « sans détourage » pour un direct important sur une machine fragile).
- Le modèle est **préchauffé** au chargement du studio (le premier appel coûte 1,3 à 1,8 s).
- Premier modèle : MediaPipe Selfie Segmentation (Apache-2.0, modèle inclus dans le paquet npm), choisi pour pouvoir mesurer ; **pas un choix de qualité**. Le modèle doit rester remplaçable derrière une interface.

## Conséquences

- Les invités n'ont besoin que d'une caméra et d'un navigateur : la contrainte de machine porte sur le Producer.
- Une **configuration minimale du Producer** doit être établie par mesure (non faite). Sur le poste de développement (RTX 4090), 5 flux détourés tiennent 29 images/s ; le CPU de Chrome est mesuré avec une grande dispersion (de 19 à 116 % d'un cœur pour 5 flux, voir le POC).
- Le Producer cumule : réception de N flux, détourage, composition, encodage du Program, publication de sa propre caméra. Le banc ne couvre qu'une partie.
- Le niveau « sans détourage » doit rester présentable : cadre elliptique aux bords adoucis, aucun trou ni clignotement.

## Risques

- La **qualité visuelle** du masque n'est pas évaluée ; le modèle retenu pour mesurer n'est peut-être pas assez bon pour une diffusion.
- Un Producer sur machine trop faible dégrade tout le studio : prévoir un test de capacité avant l'antenne.
- Le contrôleur n'a été vérifié dans un navigateur qu'avec un surcoût simulé.
