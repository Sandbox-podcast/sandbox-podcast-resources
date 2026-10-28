# POC 5 — Auto Director

Résultat : **PASS** pour la logique, sur des traces audio synthétiques. Non calibré sur de vraies prises. Code produit : `packages/auto-director` (25 tests).

## Ce qui est construit

- `ActiveSpeakerEngine` : détecte qui parle et qui est le locuteur dominant, à partir de niveaux audio en dBFS par participant (une trame toutes les 50 ms par exemple).
- `AutoDirector` : transforme ces niveaux en décisions de plan (`GROUP`, `SPEAKER_FOCUS`, `DUO`, `PRESENTATION`) et tient le journal demandé par le §11.2 du prompt maître (horodatage, décision, source, locuteur, scène, raison, confiance).
- Fonctions pures et déterministes : le temps vient des trames, jamais de l'horloge. Mêmes trames, mêmes décisions.

## Règles

Par ordre de priorité :

1. Présentation en cours : plan `PRESENTATION`, les changements de locuteur ne changent rien.
2. Réalisation manuelle : aucune décision automatique tant que le Producer n'a pas rendu la main. Au retour de l'automatique, le plan courant garde sa durée minimale.
3. Conversation croisée (plusieurs personnes parlent en même temps depuis 1,2 s) : plan de groupe.
4. Duo (au moins 3 alternances entre deux personnes en 8 s) : plan à deux.
5. Locuteur actif stable depuis 0,9 s : plan serré sur lui.
6. Silence de 4 s : retour au plan de groupe.

Un plan dure au moins 2,5 s avant le prochain changement automatique.

Mécanismes contre les faux changements : lissage du niveau, seuil de début de parole à -42 dBFS et seuil de fin à -48 (hystérésis), durée minimale de parole de 300 ms (rejette clics et chocs), maintien de 500 ms (garde les respirations), marge de 4 dB tenue 350 ms pour remplacer le locuteur dominant, durée de parole stable avant le plan serré (rejette toux et interjections).

Le mode `REACTION` existe dans les types pour une prise manuelle, mais aucune règle automatique ne le produit : il faudrait un signal d'expression qu'on n'a pas.

## Critères d'acceptation

| Critère                         | Vérifié par                                                                                                                                  |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| AC-SPK-001 locuteur actif       | participant seul identifié, personne si silence                                                                                              |
| AC-SPK-002 bruit court          | clic de 40 ms, toux de 350 ms pendant que quelqu'un parle, toux isolée, souffle de 250 ms, interjection de 600 ms : aucun changement de plan |
| AC-SPK-003 temporisation        | plan serré pas avant 2,5 s, écart d'au moins 2,5 s entre deux changements, retour en groupe après un silence                                 |
| AC-SPK-004 conversation croisée | passage en plan de groupe sans osciller ; détection d'un duo                                                                                 |
| AC-SPK-005 reprise manuelle     | arrêt immédiat des décisions, prise manuelle journalisée, reprise avec durée minimale                                                        |
| AC-SPK-006 audit                | tous les champs présents pour chaque décision, locuteur associé                                                                              |

Robustesse : un niveau qui frôle les seuils ne fait pas osciller la détection (au plus 2 transitions en 20 s), une heure de trames à 50 ms (72 000 trames, 3 participants) est traitée en moins de 3 s.

## Comment les tests ont été validés

Les tests passent, mais un test qui passe ne prouve pas qu'il détecte une régression. J'ai donc affaibli un à un huit réglages (durée minimale du plan, durée de focus, durée minimale de parole, maintien, durée de croisement, durée et marge de bascule, délai de silence) et vérifié que chaque affaiblissement fait échouer au moins un test. Quatre réglages survivaient la première fois : des tests ont été corrigés ou ajoutés (par exemple, une assertion qui relisait la valeur mutée ne pouvait jamais échouer).

## Limites

- Traces synthétiques : niveaux fixes avec un petit bruit reproductible. Les seuils (-42 et -48 dBFS, durées) sont des valeurs de départ plausibles, pas des valeurs calibrées sur de vrais micros, de vraies voix et de vraies pièces.
- Le niveau en dBFS vient d'un calcul à faire côté client ou serveur (RMS court sur le flux audio) : non construit. Les niveaux audio de LiveKit (`audioLevel`) pourraient servir de source, à vérifier.
- Pas de détection de vraie voix (VAD) : un bruit continu fort (ventilateur, musique) serait pris pour de la parole. Un VAD est à envisager.
- Le choix des scènes (`SceneCatalog`) est fourni par l'appelant. L'intégration avec la régie (POC 6) reste à faire.

## Suite

Calibrer avec des enregistrements réels de 3 participants, ajouter un VAD, intégrer au Control plane avec la régie (POC 6).
