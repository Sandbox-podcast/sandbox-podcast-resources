# Modèle de coût

Date : 2026-10-06. Code : `packages/cost-model` (15 tests, mutations vérifiées). Statut : **quantités, pas prix**.

## Ce que ce document donne, et ce qu'il ne donne pas

Il donne les **quantités** consommées par un épisode (gigaoctets, heures-cœur, minutes à transcrire), mesurées quand c'est possible, estimées sinon, avec la source de chaque valeur. Il ne donne **aucun prix** : l'hébergeur, le stockage, le trafic, les fournisseurs de transcription et de modèles de langage sont des décisions du propriétaire, et un tarif écrit de mémoire serait périmé ou faux. Le calculateur chiffre un poste seulement si un prix unitaire lui est fourni, et signale ceux qui manquent.

## Valeurs retenues

| Quantité                           | Valeur par défaut             | Origine                                                                                                                                                                                       |
| ---------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Débit audio par participant        | 24 kb/s                       | **Mesuré** : 22 kb/s (POC 4, 3 fichiers de 20 min).                                                                                                                                           |
| Débit vidéo publié (couche haute)  | 4 Mb/s                        | **Hypothèse**. Mesuré 4,9 à 6,8 Mb/s sur un contenu animé bruité (pire cas, POC 1) et 35 kb/s sur un fond noir fixe ; un visage parlant est entre les deux. À mesurer avec de vraies caméras. |
| Couche basse reçue par les invités | 0,6 Mb/s                      | **Hypothèse** (360p).                                                                                                                                                                         |
| Replay exporté                     | 8 Mb/s                        | **Hypothèse**.                                                                                                                                                                                |
| Clips                              | 5 de 60 s à 6 Mb/s            | **Hypothèse**.                                                                                                                                                                                |
| Conservation                       | 12 mois (brut et exports)     | **Hypothèse** : la durée est une décision du propriétaire.                                                                                                                                    |
| CPU d'Egress                       | 3 % d'un cœur par piste       | **Mesuré** : 12 à 13 % pour 4 pistes (POC 3), 18 % pour 6 pistes (POC 4), sur un poste de 24 cœurs. Dépend du contenu.                                                                        |
| CPU du SFU                         | 4 % d'un cœur par participant | **Mesuré 2 %** (5 à 7 % pour 2 à 3 publieurs, **sans abonnés réels**) ; on retient le double par précaution, valeur non mesurée.                                                              |
| Trafic via TURN                    | 0 %                           | **Non mesuré** : le TURN forcé depuis Chrome a échoué dans Docker Desktop (POC 1).                                                                                                            |
| Transcription                      | chaque piste séparément       | **Choix de conception** : transcrire le mélange seul divise les minutes par le nombre de participants.                                                                                        |

Non mesuré du tout : le CPU du SFU avec de vrais abonnés, le CPU de rendu des exports sur du vrai contenu (un clip de 60 s s'est rendu en 5,6 s de temps réel sur un fond simple, 24 threads), le coût de l'IA (transcription, suggestions), le trafic TURN.

## Modèle

Pour `P` participants, une durée de `H` heures :

- **Stockage brut** = `P × (vidéo + audio) × 3600 × H`. Chaque participant a une piste vidéo et une piste audio.
- **Stockage des exports** = replay + clips. **Go-mois** = brut × mois de conservation + exports × mois de conservation.
- **Trafic sortant du SFU** : le Producer reçoit les `P − 1` autres en couche haute ; chacun des `P − 1` invités reçoit les `P − 1` autres en couche basse. Le trafic vers Egress est interne à la machine et n'est pas compté.
- **Heures-cœur** : Egress `2P × 0,03 × H` ; SFU `P × 0,04 × H`.
- **Minutes de transcription** : `P × 60 × H` (par piste) ou `60 × H` (mélange).

## Exemples (quantités calculées par `episodeQuantities`, avec les valeurs par défaut sauf mention)

| Épisode                                     | Stockage brut | Exports | Go-mois (12 mois) | Trafic sortant SFU | Heures-cœur (Egress + SFU) | Transcription |
| ------------------------------------------- | ------------- | ------- | ----------------- | ------------------ | -------------------------- | ------------- |
| 3 participants, 1 h                         | 5,4 Go        | 3,8 Go  | 111               | 4,7 Go             | 0,18 + 0,12                | 180 min       |
| 4 participants, 1 h                         | 7,2 Go        | 3,8 Go  | 133               | 8,0 Go             | 0,24 + 0,16                | 240 min       |
| 5 participants, 2 h, vidéo 6 Mb/s           | 27,1 Go       | 7,4 Go  | 414               | 30,7 Go            | 0,60 + 0,40                | 600 min       |
| 4 participants, 1 h, mélange seul transcrit | 7,2 Go        | 3,8 Go  | 133               | 8,0 Go             | 0,24 + 0,16                | 60 min        |

Lecture : le **stockage** domine dans la durée (il croît avec les mois de conservation et les pistes brutes sont l'actif à ne jamais perdre), le **trafic sortant** dépend surtout du nombre de participants (il croît à peu près au carré pour les invités) et du débit de la couche haute, le **calcul média** est modeste (moins d'une heure-cœur par épisode aux valeurs mesurées) mais ne comprend ni le rendu des exports, ni le détourage (qui tourne chez le Producer, [ADR-0012](adr/ADR-0012-detourage-chez-le-producer-avec-regulation.md)).

## Prix à fournir par le propriétaire

Pour chiffrer, il faut : le prix du **stockage** par Go et par mois, du **trafic sortant** par Go, de l'**heure de calcul** (ou le prix de la machine hébergeant LiveKit et Egress, à répartir), du trafic **TURN**, de la **transcription** par minute d'audio, et des appels à un modèle de langage par million de jetons (non modélisé : dépend du fournisseur et de l'usage). L'appel est : `price(episodeQuantities({ participants: 4, hours: 1 }), { storagePerGbMonth: …, egressPerGb: …, … })`.

Une alternative auto-hébergée change la forme du coût : la machine est facturée au mois, pas à l'épisode ; il faut alors dimensionner le nombre d'épisodes simultanés. Ce dimensionnement n'est pas fait : sur le poste de développement, 6 pistes enregistrées ont occupé moins d'un cœur, mais le SFU n'a jamais servi de vrais abonnés.

## Contrôles de coût à prévoir (pas encore implémentés)

- **Quotas par podcast** : stockage total, minutes de transcription par mois, nombre de clips et d'exports par épisode.
- **Plafond de dépense IA** par credential MCP et par podcast, avec coupe-circuit et alerte à 80 % ([threat-model.md](threat-model.md) : « coût IA incontrôlé » est un risque non couvert).
- **Politique de conservation** : durée des pistes brutes, des exports, des transcriptions ; suppression programmée après avertissement (décision du propriétaire).
- **Confirmation humaine** avant une action coûteuse lancée par une IA, comme pour la publication ([ADR-0009](adr/ADR-0009-mcp-et-episode-factory.md)).
- **Mesure en production** des débits réels pour remplacer les hypothèses ci-dessus : c'est le premier réglage à faire dès qu'il y a de vrais enregistrements.
