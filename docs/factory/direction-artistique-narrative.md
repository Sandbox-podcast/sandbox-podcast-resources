# Direction artistique des vidéos narratives

La première bibliothèque utilise le fond bleu nuit `#071322`, des panneaux `#10243B`, le cyan `#16D5E8`, un blanc `#F1F6FC` et une couleur de repère `#FFB463`. Elle reprend le logo commun `assets/brand/logo.png`. Elle convient aux explications de processus, aux différences entre étapes et aux protocoles de mesure.

Les paramètres de dessin et d'animation sont dans `factory/narrative_visuals.py`. La version du style entre dans les clés de rendu. Les scènes ont un titre bref, un schéma central, une indication de nature des propos et des sous-titres. Les indications distinguent fait sourcé, analyse Sandbox, hypothèse et témoignage. Les libellés visibles sont en français ; les noms de composants restent des identifiants de code.

| Composant | Usage | Mouvement |
| --- | --- | --- |
| `flow` | Un traitement et ses étapes | Apparition progressive des nœuds et signal sur les liaisons. |
| `comparison` | Deux éléments ou états à comparer | Cartes révélées puis accent successif, sans chiffres inventés. |
| `timeline` | Ordre d'observation ou d'action | Étapes empilées et progression entre elles. |
| `cards` | Points distincts qui n'impliquent pas une causalité | Cartes séparées, sans flèches de cause à effet. |

Le paysage dispose les étapes d'un flux sur une ligne. Le portrait les empile et réserve le bas aux sous-titres. Les titres, libellés et phrases doivent rester courts ; le renderer refuse les dépassements de ses zones de texte. Une composition ne doit pas cacher un écran de démonstration ou transformer une hypothèse en mesure.

Les animations dépendent du temps local de la scène. Un même instant reproduit la même image. L'entrée du titre dure 550 ms ; les nœuds apparaissent avec un décalage de 220 ms et une transition de 420 ms. Le signal mobile et la progression soutiennent la lecture du schéma. Les éléments sont dessinés à chaque image et ne dépendent pas d'une animation lancée une seule fois dans une page Web.

Les sous-titres suivent les fichiers audio de chaque phrase, avec une pause de 180 ms entre phrases. Leur texte conserve l'orthographe de la narration même si la voix utilise un alias de prononciation. La normalisation FFmpeg vise -16 LUFS et une crête à -1,5 dBTP ; le contrôle final conserve les valeurs effectivement observées. Une écoute reste nécessaire pour le débit, l'intonation et les noms propres.

Cette version ne couvre pas encore les personnages animés, les illustrations originales générées, les plans de démonstration, la musique ou les effets sonores. Pour étendre la bibliothèque, ajouter un composant avec un usage précis, une disposition dans les deux ratios, un mouvement déterministe, ses contrôles de texte et une recette visuelle. Toute ressource tierce doit garder sa provenance et ses droits. Aucun visage ou réaction d'animateur ne doit être inventé.

Les miniatures suivent une procédure séparée. Le storyboard et les cartes d'une vidéo peuvent fournir des éléments graphiques ; ils ne valent ni concept de miniature ni preuve de lisibilité à 160 pixels. Voir [la procédure](miniatures.md).
