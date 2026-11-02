---
name: sandbox-thumbnail
description: "Créer les miniatures YouTube de la chaîne Sandbox à partir des photos de ses membres et du sujet de l’épisode. Style sobre : vrais visages reconnaissables, vêtements et expressions variés, fond simple et accroche courte en français."
---

# Miniatures Sandbox

## Direction

Une photo éditoriale simple : **nos visages + une attitude qui raconte le sujet + une phrase courte**. La personnalité des personnes fait l’image. « Sans AI slop » décrit le rendu demandé ; cela n’interdit pas de générer des changements de vêtements ou de posture à partir de leurs références.

Exigences de l’utilisateur : texte sans fioritures, aucun effet inutile, aucun fond spatial, visages des membres de Sandbox, vêtements/postures/émotions différents à chaque miniature. Ne pas substituer des visages génériques ou ceux des chaînes de référence.

## Intégration au dépôt

Ce skill porte la direction visuelle des miniatures. Le skill [sandbox-packaging](../sandbox-packaging/SKILL.md) garde le titre, les preuves de contenu et le parcours de la factory. Pour un extrait YouTube développé, appliquer aussi [la procédure des miniatures](../../../docs/factory/miniatures.md) : trois concepts titre/image réellement distincts, créations `finished_artwork`, provenance des portraits et transformations, aperçus à 320 et 160 pixels et revue par un second lecteur. Une variation de vêtements ou de couleur ne suffit pas à distinguer trois hypothèses éditoriales.

Pour une demande autonome, produire une miniature sauf demande de variantes. Les dimensions ci-dessous sont celles de la création ; le parcours factory conserve son export configuré. Les portraits, rendus et planches restent locaux, sous `.local/` ; seuls le skill et ses références textuelles sont versionnés. Distinguer une expression mise en scène d'une réaction réellement filmée. Ne jamais présenter une transformation générée comme une preuve de ce qui s'est passé dans l'épisode.

## Entrées

Chercher dans le contexte et les fichiers fournis : sujet et angle réel de l’épisode, personnes à représenter, photos de référence identifiées, dernières miniatures si disponibles. Ne pas lire au hasard des dossiers personnels pour trouver des portraits.

Si le sujet manque, le demander. Si les photos manquent, préparer l’accroche et la composition puis demander les portraits avant de générer les personnes. Ne jamais prétendre reproduire un visage sans référence. Une photo nette par personne est le minimum ; plusieurs angles facilitent les changements de posture. Sans historique, signaler que la variation par rapport aux épisodes précédents n’a pas pu être contrôlée.

## Composition par défaut

Ces réglages sont des valeurs de départ réversibles, pas une charte déjà validée :

- Canevas 16:9, cible 1280 × 720 ou 1920 × 1080.
- Fond uni mat : crème, gris clair ou anthracite selon le contraste. Pas de texture décorative, de halo, de dégradé spectaculaire ni de décor spatial.
- Personne cadrée au buste, assez grande pour reconnaître son expression en miniature. Texte dans l’espace libre opposé. Pour un duo, garder les deux visages lisibles et une interaction naturelle. N’ajouter aucune personne absente du brief ; si l’équipe est trop nombreuse pour rester lisible, faire préciser les participants à mettre en avant.
- Une seule famille sans empattement, droite et grasse (par exemple Inter Bold), sans contour, relief, déformation ni ombre décorative. Une ou deux lignes, 2 à 5 mots de préférence, 6 au maximum. Accents conservés. Casse adaptée à la lisibilité ; majuscules facultatives.
- Texte noir ou blanc selon le fond. Une éventuelle couleur d’accent discrète, sans en inventer une comme couleur officielle de Sandbox.
- Marges généreuses, aucun texte sur les yeux ou la bouche. Garder le coin inférieur droit libre des informations importantes pour la durée affichée par YouTube.
- Par défaut, aucun objet, logo d’outil, écran, flèche, badge, emoji ou autre élément ajouté. Le sujet doit tenir dans le visage et les mots.

## Accroche

Exprimer une idée vérifiable dans l’épisode. Compléter le titre au lieu de le recopier. Écrire comme les membres parleraient : « On garde quoi ? », « Ça tourne chez nous », « On a tout refait », « Qui contrôle quoi ? » — seulement si le contenu le justifie.

Éviter les promesses de revenus, les chiffres inventés et les superlatifs automatiques (« INCROYABLE », « RÉVOLUTION », « GAME CHANGER »). Une tension honnête convient ; ne pas fabriquer une peur ou un scandale.

## Faire varier les personnes

Comparer avec les dernières miniatures disponibles. Changer les trois dimensions demandées à chaque épisode, avec des variations naturelles :

| Dimension | Exemples |
|---|---|
| Vêtements | T-shirt uni, chemise simple, surchemise, pull ; varier coupe et couleur sans marque inventée |
| Posture | De face, trois quarts, légèrement penché, bras croisés, regard vers un autre membre ; mains uniquement si anatomiquement crédibles |
| Émotion | Curiosité, doute léger, satisfaction, concentration, amusement, désaccord calme |

Relier l’expression à l’angle de l’épisode. Éviter la bouche béante de surprise répétée, les yeux exagérés et les costumes gadgets. Conserver identité, âge apparent, morphologie, coiffure et signes distinctifs ; pas de peau plastique, de blanchiment excessif des dents ou d’embellissement automatique. Pour un duo, éviter deux expressions identiques copiées.

## Production

1. Définir l’accroche, la composition et les variations de tenue/posture/émotion. Pour une demande autonome, choisir une proposition cohérente sans demander une validation intermédiaire systématique ; pour la factory, préparer les trois concepts requis.
2. Utiliser l’outil de génération/édition d’image disponible, en respectant ses instructions et en lui transmettant les portraits réels. Examiner les références avant édition. Si aucun outil adapté n’est disponible, livrer le brief et le prompt en indiquant que l’image n’a pas été produite.
3. Produire l’image selon le brief ci-dessous. Si l’outil reproduit mal les lettres, préférer une image sans texte avec un espace réservé, puis poser le texte avec un outil de composition autorisé. Respecter les restrictions de l’outil ; ne pas basculer silencieusement vers une retouche interdite. Ne pas livrer une faute de texte comme résultat final.
4. Examiner le résultat à pleine taille et en aperçu d’environ 320 × 180, puis à 160 pixels de largeur pour la factory. Contrôler identité, anatomie, texte exact, contraste et absence d’effets décoratifs. Corriger les défauts observés, sans boucle de génération illimitée ; après deux corrections infructueuses, expliquer la limite et fournir le meilleur résultat clairement marqué comme brouillon.
5. Exporter sans écraser les portraits, en PNG ou JPEG au ratio prévu. Afficher l’image et fournir son fichier. Ajouter un bref récapitulatif de l’accroche, tenue, posture et émotion pour permettre la variation suivante. Ne rien publier sur YouTube sans instruction explicite.

### Brief à adapter

> Miniature YouTube 16:9 pour Sandbox. À partir des portraits joints de [personnes], préserver fidèlement leur identité et leurs traits. Photographie naturelle, peau avec sa texture, lumière douce neutre. [Cadrage et position]. [Tenue différente de la précédente]. [Posture]. [Émotion contenue liée au sujet]. Fond uni mat [couleur]. Espace libre [position] pour le texte exact « [accroche] », en sans-serif grasse simple, [noir/blanc], une ou deux lignes. Aucun autre texte. Aucun objet ou logo ajouté. Aucun cosmos, néon, halo, particules, feu, éclair, contour lumineux, effet 3D ou peau lissée. Ensemble sobre, crédible et lisible en petit.

## Ce qui constitue un résultat réussi

Visages reconnaissables ; phrase comprise en un coup d’œil et fidèle au contenu ; vêtements, posture et émotion variés ; aucun ajout décoratif ; texte exact ; image effectivement inspectée. Ne pas promettre un meilleur taux de clic sans mesure comparative.

Pour comprendre les inspirations et leurs limites, lire [references/analyse.md](references/analyse.md). Ces chaînes sont des références de composition, jamais des banques de visages à réutiliser.
