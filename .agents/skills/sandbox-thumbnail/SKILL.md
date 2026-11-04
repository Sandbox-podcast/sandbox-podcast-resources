---
name: sandbox-thumbnail
description: "Créer les miniatures YouTube de la chaîne Sandbox à partir des photos de ses membres et du sujet de l’épisode. Style sobre : vrais visages reconnaissables, vêtements et expressions variés, fond simple et accroche courte en français."
---

# Miniatures Sandbox

## Direction

Une photo éditoriale simple : **nos visages + une attitude qui raconte le sujet + une phrase courte**. La personnalité des personnes fait l’image. « Sans AI slop » décrit le rendu demandé ; cela n’interdit pas de générer des changements de vêtements ou de posture à partir de leurs références.

Exigences de l’utilisateur : texte sans fioritures, aucun effet inutile, aucun fond spatial, visages des membres de Sandbox, vêtements/postures/émotions différents à chaque miniature. Ne pas substituer des visages génériques ou ceux des chaînes de référence.

## Style validé le 4 novembre 2026

Privilégier les trois visages de Lou, Nicolas et Loïc ensemble lorsqu'ils participent à l'épisode. Têtes grandes, de taille comparable, toutes visibles ; texte sur une ou deux lignes dans le tiers supérieur. Une personne peut être légèrement en avant. Faire varier leur ordre, leurs vêtements, leurs postures et leurs émotions sans fusionner les identités. Un extrait centré sur une autre personne doit respecter ses vrais participants.

L'accroche nomme le sujet même sans lire le titre de la vidéo. Exemples validés : « IA : le modèle ne suffit pas », « L'IA pour ton commerce », « Du code IA en production ? ». Écarter les questions génériques seules comme « On commence par quoi ? ». Viser 2 à 6 mots, accepter 7 si nécessaires à la clarté.

Intégrer discrètement la charte : bleu nuit `#071A29`, cyan `#1CB5ED`, blanc cassé `#F4F7FA`. Sur fond clair, préférer un bleu pétrole plus foncé `#08799E` pour les mots accentués. Un ou deux mots en couleur, et un petit triangle creux cyan en haut à gauche, pointe vers le haut, avec une marge ; il ne doit pas concurrencer le titre. Ce rappel de l'icône n'est pas un logo de partenaire ni un grand bandeau de marque.

Trois déclinaisons validées : fond crème avec texte bleu nuit et « IA » bleu pétrole ; fond bleu glacier `#DDEFF4` avec « commerce » bleu pétrole ; fond bleu nuit avec texte blanc cassé et « code IA » cyan. Garder des couleurs de peau naturelles. La préférence personnelle de l'agent pour le fond sombre n'impose pas ce fond à tous les épisodes.

## Utilisation autonome ou dans la factory

Le dossier de ce skill est autonome : ses références et son script utilisent des chemins relatifs. Lire [references/portraits.md](references/portraits.md) pour charger les trois visages et [references/style-valide.md](references/style-valide.md) pour les compositions validées. Aucun accès au serveur marldev ni clé API n'est nécessaire pour récupérer les portraits publics ; la génération exige séparément un outil d'image capable de recevoir les photos.

Dans le dépôt resources, `sandbox-packaging` gère le titre, les preuves et la factory. Pour ce parcours uniquement, lire `docs/factory/miniatures.md` depuis la racine du dépôt : trois concepts titre/image distincts, créations `finished_artwork`, provenance, aperçus à 320 et 160 pixels, puis revue par un second lecteur. Une variation de tenue ne suffit pas à différencier trois hypothèses éditoriales. Hors du dépôt, ne pas exiger ces fichiers absents : produire une miniature autonome, sauf demande de variantes.

Les portraits, rendus et planches restent locaux, sous `.local/` ; seuls le skill et ses références textuelles sont versionnés. Distinguer une expression mise en scène d'une réaction filmée. Ne jamais présenter une transformation générée comme une preuve de ce qui s'est passé dans l'épisode.

## Entrées

Chercher dans le contexte et les fichiers fournis : sujet et angle réel de l’épisode, personnes à représenter, photos de référence identifiées, dernières miniatures si disponibles. Ne pas lire au hasard des dossiers personnels pour trouver des portraits.

Charger d’abord les portraits identifiés selon [references/portraits.md](references/portraits.md). Si le sujet manque, le demander. Si les photos restent introuvables, préparer l’accroche et la composition puis demander les portraits avant de générer les personnes. Ne jamais prétendre reproduire un visage sans référence. Une photo nette par personne est le minimum ; plusieurs angles facilitent les changements de posture. Sans historique, signaler que la variation par rapport aux épisodes précédents n’a pas pu être contrôlée.

## Composition par défaut

Appliquer le style validé ci-dessus ; adapter le cadrage au sujet :

- Canevas 16:9, cible 1280 × 720 ou 1920 × 1080.
- Fond uni mat : crème, bleu glacier ou bleu nuit selon la déclinaison choisie. Pas de texture décorative, de halo, de dégradé spectaculaire ni de décor spatial.
- Trio cadré aux épaules ou au buste, les trois têtes lisibles sous le titre. Adapter les participants au contenu ; ne pas ajouter une personne absente de l’épisode.
- Une seule famille sans empattement, droite et grasse (par exemple Inter Bold), sans contour, relief, déformation ni ombre décorative. Une ou deux lignes, 2 à 6 mots de préférence, jusqu’à 7 si le sujet le nécessite. Accents conservés. Casse adaptée à la lisibilité ; majuscules facultatives.
- Texte bleu nuit ou blanc cassé selon le fond ; un ou deux mots cyan ou bleu pétrole selon le contraste.
- Marges généreuses, aucun texte sur les yeux ou la bouche. Garder le coin inférieur droit libre des informations importantes pour la durée affichée par YouTube.
- Hors du petit triangle de signature, aucun objet, logo d’outil, écran, flèche, badge ou emoji ajouté par défaut. Le sujet doit tenir dans le visage et les mots.

## Accroche

Exprimer une idée vérifiable dans l’épisode. Compléter le titre tout en nommant le thème concret dans l’image (IA, commerce, code en production…). Utiliser les exemples validés seulement lorsque le contenu les justifie.

Éviter les promesses de revenus, les chiffres inventés et les superlatifs automatiques (« INCROYABLE », « RÉVOLUTION », « GAME CHANGER »). Une tension honnête convient ; ne pas fabriquer une peur ou un scandale.

## Faire varier les personnes

Comparer avec les dernières miniatures disponibles. Changer les trois dimensions demandées à chaque épisode, avec des variations naturelles :

| Dimension | Exemples |
|---|---|
| Vêtements | T-shirt uni, chemise simple, surchemise, pull ; varier coupe et couleur sans marque inventée |
| Posture | De face, trois quarts, légèrement penché, bras croisés, regard vers un autre membre ; mains uniquement si anatomiquement crédibles |
| Émotion | Curiosité, doute léger, satisfaction, concentration, amusement, désaccord calme |

Relier l’expression à l’angle de l’épisode. Éviter la bouche béante de surprise répétée, les yeux exagérés et les costumes gadgets. Conserver identité, âge apparent, morphologie, coiffure et signes distinctifs ; pas de peau plastique, de blanchiment excessif des dents ou d’embellissement automatique. Éviter de copier la même expression sur les trois visages.

## Production

1. Définir l’accroche, la composition et les variations de tenue/posture/émotion. Pour une demande autonome, choisir une proposition cohérente sans demander une validation intermédiaire systématique ; pour la factory, préparer les trois concepts requis.
2. Utiliser l’outil de génération/édition d’image disponible, en respectant ses instructions et en lui transmettant les portraits réels. Examiner les références avant édition. Si aucun outil adapté n’est disponible, livrer le brief et le prompt en indiquant que l’image n’a pas été produite.
3. Produire l’image selon le brief ci-dessous. Si l’outil reproduit mal les lettres, préférer une image sans texte avec un espace réservé, puis poser le texte avec un outil de composition autorisé. Respecter les restrictions de l’outil ; ne pas basculer silencieusement vers une retouche interdite. Ne pas livrer une faute de texte comme résultat final.
4. Examiner le résultat à pleine taille et en aperçu d’environ 320 × 180, puis à 160 pixels de largeur. Contrôler identité, anatomie, texte exact, contraste et absence d’effets décoratifs. Corriger les défauts observés, sans boucle de génération illimitée ; après deux corrections infructueuses, expliquer la limite et fournir le meilleur résultat clairement marqué comme brouillon.
5. Exporter sans écraser les portraits, en PNG ou JPEG au ratio prévu. Afficher l’image et fournir son fichier. Ajouter un bref récapitulatif de l’accroche, tenue, posture et émotion pour permettre la variation suivante. Ne rien publier sur YouTube sans instruction explicite.

### Brief à adapter

> Miniature YouTube 16:9 pour Sandbox. Références jointes identifiées : [Lou, Nicolas, Loïc]. Représenter ces trois personnes distinctes, une fois chacune, avec des traits fidèles. [Ordre et attitudes], cadrage épaules/buste ; trois têtes de taille comparable, aucune masquée. [Tenues et émotions différentes de l'épisode précédent]. Peau naturelle, lumière douce neutre. Fond uni mat [crème/bleu glacier/bleu nuit]. Dans le tiers supérieur, texte exact « [accroche qui nomme le sujet] », sans-serif grasse simple, [bleu nuit/blanc cassé], [mot précis] en [cyan/bleu pétrole]. Petit triangle creux cyan discret en haut à gauche. Aucun autre texte, objet, logo d'outil, halo, néon, contour lumineux, effet 3D ou lissage de peau. Aucun filtre bleu sur les personnes.


## Ce qui constitue un résultat réussi

Visages reconnaissables ; phrase comprise en un coup d’œil et fidèle au contenu ; vêtements, posture et émotion variés ; signature discrète sans effet décoratif ; texte exact ; image effectivement inspectée. Ne pas promettre un meilleur taux de clic sans mesure comparative.

Pour comprendre les inspirations et leurs limites, lire [references/analyse.md](references/analyse.md). Ces chaînes sont des références de composition, jamais des banques de visages à réutiliser.
