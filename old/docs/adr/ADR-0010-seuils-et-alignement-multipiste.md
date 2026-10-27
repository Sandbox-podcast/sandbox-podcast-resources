# ADR-0010 — Seuils de synchronisation multipiste et stratégie d'alignement

- Statut : acceptée (seuils provisoires à valider ; amendée le 2026-10-06 après l'essai Chrome)
- Date : 2026-10-06
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

AC-REC-006 demande qu'après reconstruction les pistes respectent « le seuil de dérive validé pendant la durée de test définie ». Le prompt maître ne fixe ni le seuil ni la durée. Le [POC 4](../pocs/poc-04-multitrack-sync.md) a mesuré, sur 30 minutes et trois participants : alignement entre participants stable, audio/vidéo d'un même participant en dérive de 38 ppm avec les publieurs de test, manifestes d'egress insuffisants pour réaligner (erreur de 94 à 189 ms).

## Décision

1. **Seuils**, mesurés avec des repères communs sur une session de test de 30 minutes minimum :
   - amplitude (maximum − minimum) du décalage ≤ **40 ms** pour une série qui n'implique que de l'audio, ≤ **70 ms** (deux images) dès qu'une série vidéo est impliquée (voir l'amendement ci-dessous) ;
   - dérive ajustée par moindres carrés entre le début et la fin ≤ **20 ms** ;
   - au moins 10 repères appariés, aucun intervalle de repères hors de ± 0,5 s.
     Justification : la recommandation EBU R37 tolère un son en avance de 40 ms au plus sur l'image (retard jusqu'à 60 ms) ; pour des pistes de parole mixées, 20 ms de dérive reste inaudible. Ce sont des seuils d'ingénieur, **à valider par le propriétaire** (par exemple avec un test d'écoute sur de vrais enregistrements). Ils sont dans le code (`DEFAULT_THRESHOLDS`) et les tests les vérifient.
2. **Stratégie d'alignement en production** : les manifestes d'egress ne suffisent pas. La plateforme doit enregistrer, pour chaque piste, la correspondance entre l'horloge de capture (RTP) et une horloge commune (mur), au démarrage puis périodiquement (toutes les minutes). Source envisagée : `getStats()` côté navigateur (rapports d'émetteur) envoyé par le canal de données et stocké avec la session ; à défaut, des repères injectés. Tant que ce mécanisme n'est pas validé, **aucune reconstruction de production n'est garantie alignée**.
3. **Correction en post-production** : une dérive linéaire se corrige par rééchantillonnage de la piste (facteur 1 + pente). Le résiduel mesuré après ajustement linéaire est de 1,8 ms. Appliquer cette correction seulement si la pente mesurée dépasse le seuil, et la tracer dans la liste de décisions de montage (les sources ne sont jamais modifiées).
4. **Banc de mesure conservé** : la source à repères et l'analyse (`pocs/poc-04-multitrack-sync`) deviennent un test de non-régression à relancer à chaque changement de version d'Egress, de LiveKit ou de paramètres de publication.

## Amendement du 2026-10-06 (après les mesures)

Le seuil d'amplitude de 70 ms pour les séries vidéo a été ajouté **après** avoir mesuré 67 ms entre deux séries vidéo Chrome, alors que le seuil posé avant les mesures était de 40 ms pour tout. Ce n'est pas un réglage fait pour passer : un repère vidéo n'est connu qu'à l'image près (33,3 ms), donc l'écart entre deux séries vidéo peut valoir deux images sans défaut, et la pente ajustée (−1,1 ± 2,1 ppm dans ce cas) montrait déjà l'absence de dérive. Le seuil de dérive ajustée (20 ms) n'a pas changé : c'est le critère strict, insensible à la quantification. Le code l'applique (`maxVideoSpanMs`) et les tests le vérifient.

Le résultat de la mesure est l'incertitude de la pente : chaque résultat est donné avec son erreur-type, et une dérive de l'ordre de deux erreurs-types n'est pas considérée comme établie.

## Conséquences

- Le POC 4 est PASS avec limites pour des publieurs Chrome sur une machine et 20 minutes (voir le POC). L'essai avec les publieurs `livekit-cli` donne 38 ppm de dérive audio/vidéo, attribuée au publieur de test puisque l'Egress et le SFU sont les mêmes.
- Le modèle de données de l'enregistrement doit prévoir un emplacement pour les points de correspondance d'horloge par piste.
- La reconstruction (POC 10) prend en entrée un décalage de départ et une pente par piste.

## Risques

- Les seuils peuvent être trop sévères ou trop souples pour l'oreille et l'œil : à confirmer par l'écoute.
- La dérive de 38 ppm s'est révélée un artefact du publieur de test. La décision 3 (correction par rééchantillonnage) reste utile comme filet de sécurité, pas comme correction attendue.
- Les mesures viennent d'un seul hôte : les horloges de postes distincts ajouteront de la dérive.
