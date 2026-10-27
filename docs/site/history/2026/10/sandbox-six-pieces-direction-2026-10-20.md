# Sandbox : direction des six pièces

20 octobre 2026. Direction de conception décidée par l'agent sur délégation (PD-0003), à partir de la demande de Lou. Ce document décrit la cible et ses critères de revue ; il ne constitue pas une preuve de réalisation ou de performance.

La dernière consigne de Lou donne accès au portail sur toute l'illustration : les commandes contextuelles choisissent la destination, l'ouverture suit le curseur et le clic dans le décor déclenche le passage. Elle remplace les points d'activation initialement prévus dans les murs. La priorité va à l'ordinateur ; le travail mobile est reporté.

Sources : [vision.md](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/vision.md), [textes publics alignés sur la vision](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0068-wording-aligne-sur-la-vision.md), [plateau photographique](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0064-accueil-impact-ia-et-plateau-au-scroll.md), [vidéoclub existant](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/site/video-club.md) et [limites du premier portail](portail-videoclub-2026-10-20.md). Les captures fournies par Lou montrent l'écart entre le cercle du prototype et une ouverture située dans un espace. L'analyse temporelle de la vidéo source relève de la recette du lot ; cette note ne prétend pas l'avoir visionnée.

## Intention et ligne artistique

Le visiteur entre dans les locaux de Sandbox. Les six pièces prolongent le travail de l'émission : discuter, construire, comparer, remettre en contexte, regarder et suivre les annonces. La promesse « Ce que l'IA change pour ceux qui construisent » reste lisible dès l'arrivée, avec le repère « Le talk-show IA, engineering et produit ». Lou, Loïc et Nico restent identifiables comme les animateurs ; le décor ne doit pas repousser leur présentation après une visite obligatoire.

Nous reprenons le noyer, les panneaux acoustiques bleu nuit, le métal noir et les lumières ambrées du plateau actuel. Chaque pièce possède ses propres volumes et son éclairage d'usage. Un même sol foncé, les mêmes huisseries et une signalétique ivoire relient l'ensemble. Les accents cyan servent aux écrans et aux portes actives. Le rouge appartient au cinéma et à l'enseigne du vidéoclub ; le vert appartient au radar. Les panneaux de contenu utilisent Archivo et les polices déjà chargées par le site.

La référence rétro vient du matériel de studio, des VHS et des appareils de mesure. Les interfaces présentent des projets et des faits actuels. Le décor reste suffisamment calme pour qu'un CTO ou un PM trouve une émission ou une source sans devoir apprendre les commandes d'un jeu.

## Plan des pièces

Le plateau constitue le point de départ. Le premier écran occupe 100 svh, avec l'accroche et la scène. Les six cartes sous le hero sont retirées à la demande de Lou. Les commandes de visite apparaissent au survol et restent accessibles au clavier ; elles permettent de choisir la pièce à révéler depuis n'importe quelle salle. Le visiteur place ensuite le passage avec le curseur dans l'illustration. Aucun ordre de visite n'est imposé.

Les blocs situés plus bas dans la page reprennent les photographies des pièces correspondantes. Time Machine, classements et Radar utilisent chacun le même décor dans la scène et dans leur carte. Les images propres aux projets et aux replays gardent leur rôle de contenu.

| Pièce             | Volume et composition                                                                                                                                                                   | Contenu vivant                                                                                                                 | Action principale                                            |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| 01 · Plateau      | Grande table en noyer, trois places, portique de lumière, panneaux acoustiques. La porte du vidéoclub est visible sur le mur latéral. Un écran indique la dernière émission.            | Titre de l'émission, trois animateurs et épisode disponible issus des contenus existants.                                      | Ouvrir l'émission ou explorer une pièce.                     |
| 02 · Vidéoclub    | Allée centrale praticable, étagères de VHS sur les murs, comptoir bas, enseigne rouge mesurée.                                                                                          | Tous les projets existants dans les rayons, classés par créateur, avec les mêmes pochettes, titres et fiches que le catalogue. | Prendre une VHS puis ouvrir sa fiche.                        |
| 03 · Classements  | Salle de régie avec une console en premier plan et plusieurs moniteurs au fond. Des cadres techniques et tiroirs bas donnent une échelle humaine.                                       | Familles de classements disponibles, dates des éditions et premiers rangs réels.                                               | Choisir un écran pour consulter le classement correspondant. |
| 04 · Time Machine | Salle d'archives avec vitrines, rails lumineux au plafond et frise chronologique sur les murs. L'objet rétrofuturiste déjà présent sur le plateau peut devenir une pièce de collection. | Jalons sourcés de la chronologie existante ; année et titre en texte accessible.                                               | Choisir une période puis ouvrir un événement.                |
| 05 · Cinéma       | Petit cinéma de projection : fauteuils bleu nuit en premier plan, allée dégagée, écran central et affiches intégrées aux cadres des murs.                                               | Replays réels, du plus récent au plus ancien. Une affiche par vidéo disponible, sans doublons de remplissage.                  | Sélectionner une affiche puis ouvrir sa fiche d'épisode.     |
| 06 · Radar        | Bureau de veille relié à une régie : instrument radar vert, dossiers et lampe de travail chaude. Un seul moniteur interactif reçoit le contenu.                                         | Accès au fil existant ; les actualités, dates, sources et statuts restent consultables dans la rubrique.                       | Ouvrir le fil News.                                          |

Les affiches, classements et actualités doivent rester des données actualisables. Aucun titre éditorial, score, date ou faux article n'est peint dans une image de décor. Les scènes peuvent contenir des moniteurs éteints lorsqu'aucune donnée n'est disponible ; l'interface explique cet état et garde les autres pièces accessibles.

### Hiérarchie dans chaque pièce

Un repère discret donne le numéro et le nom de la pièce. Le visiteur distingue ensuite un objet principal, quelques objets secondaires et les passages. Le contenu détaillé s'ouvre dans un panneau lisible ou dans sa page existante. Les textes longs ne sont pas plaqués en perspective au fond d'une pièce.

Les liens « Lire le classement », « Ouvrir le projet », « Voir le replay » et « Lire la source » restent explicites. Les personnes venues pour un contenu précis peuvent les utiliser immédiatement. Le radar ne promet pas une actualité en direct lorsque la collecte est ancienne ; la salle des classements n'attribue aucun avis de l'équipe aux mesures automatiques.

## Passages et mouvement

Lou demande de retirer le système de scroll qui transforme le décor. La séquence épinglée de 440 svh, l'allumage progressif et le retournement déclenché par le défilement quittent ce parcours. Le scroll garde son usage habituel pour les textes et les panneaux de contenu.

Toute l'illustration constitue la surface du portail. Les commandes contextuelles choisissent la destination ; lorsque le visiteur déplace le curseur dans le décor, une ouverture organique suit sa position et révèle la pièce choisie. Aucun objet ni zone ponctuelle ne conditionne l'apparition. La lumière du contour reste assez mesurée pour préserver la vue située derrière. Les liens de contenu gardent leurs actions propres.

Au clic dans le décor ou avec la commande clavier équivalente, la caméra avance vers l'ouverture, franchit le seuil et s'arrête dans la pièce. La position du passage est conservée pendant la traversée. La destination conserve son cadrage, son sol et son éclairage. Le contour s'efface une fois traversé ; les commandes contextuelles permettent de choisir la pièce de retour.

Le réglage actuel prévoit une traversée de 1,8 seconde, avec une accélération puis un ralentissement. La revue sur ordinateur doit vérifier le rythme et le raccord de perspective. Le déplacement latéral au repos reste limité ; aucun balancement permanent ni rotation automatique n'est nécessaire. La commande de pause et la préférence de réduction des mouvements donnent accès au parcours fixe.

### Ce qui produit l'impression d'entrer

La vue de destination doit dépendre de la même caméra que la vue d'origine. Une ouverture vue en biais montre son épaisseur. Un objet proche se déplace davantage à l'écran qu'un objet lointain. Le seuil grandit lorsque la caméra avance, puis quitte le cadre. Le contenu aperçu avant le passage correspond à celui que le visiteur retrouve après.

Lou demande que l'ouverture suive la souris. La correction doit conserver ce geste tout en donnant une vue en profondeur de la pièce choisie. Une petite photographie entière contenue dans un cercle garderait l'apparence de loupe du premier prototype. Le déplacement de caméra et la continuité de la destination doivent donc être perceptibles, au-delà du contour et de ses particules.

## Réalisation praticable

La cible demande une géométrie légère : murs, sol, plafond, portes, étagères, fauteuils, console et surfaces d'affichage. Des textures et les médias existants fournissent les détails. Les ouvertures peuvent relier des chambres d'une même scène, ou rendre une seconde scène avec une caméra raccordée. L'équipe technique choisit selon les contraintes du rendu ; la continuité visuelle reste le critère d'acceptation.

Les photographies actuelles du plateau, du vidéoclub et du mur des replays servent de références de matériaux et de composition. Une photographie plate seule ne permet pas de reconstruire correctement les faces cachées d'un meuble ou de se déplacer librement autour d'une table. Le dépôt ne fournit pas ici de capture volumétrique de ces locaux. Un rendu Gaussian splatting équivalent à la référence demanderait des scènes préparées pour cette technique ; il ne doit pas être annoncé sur la seule base de ces images.

Pour ce lot, l'équipe technique projette les photographies sur un volume à cinq faces et ajoute des objets en relief. La position du curseur détermine le passage ; une seconde pièce située derrière son plan est rendue depuis la caméra courante. Au clic, ce point devient le seuil du trajet. La revue devra contrôler les raccords entre sol et murs, le cadrage des meubles photographiés et les amplitudes latérales : une table incluse dans la photographie reste aplatie si elle ne reçoit pas sa propre géométrie.

Une première réalisation peut proposer six chambres stylisées en 3D avec navigation entre points de vue définis. Elle donne déjà de vrais volumes, des passages et une destination cohérente avec l'aperçu. Il faut nommer cette limite dans la livraison si la marche libre n'est pas proposée.

Les textes et actions restent en HTML accessible, associés aux objets rendus. Le catalogue, les classements, la chronologie, les replays et News conservent leurs routes existantes et leurs sources de données. Chaque salle propose un accès direct à sa rubrique. Les contenus distants ne sont pas chargés automatiquement pour fabriquer de l'ambiance.

## Priorité ordinateur, clavier et chargement

Lou a explicitement reporté le travail mobile. La correction actuelle se juge sur ordinateur, avec le portail disponible dans toute l'illustration. Le parcours fixe et les liens existants restent disponibles sur les autres configurations ; leur présence ne constitue pas une validation de l'expérience tactile. Le cadrage mobile, les cibles et la place des commandes seront repris ultérieurement.

Au clavier, Tab atteint les commandes de visite, la commande de passage et les objets. Le focus indique la destination ; Entrée déclenche l'action, Échap annule l'aperçu ou le trajet, et le retour navigateur restaure la pièce précédente. Les pièces masquées ne proposent aucune cible fantôme. La recette doit vérifier ces commandes après le retrait des anciens points d'accès.

Le plateau apparaît en premier, puis les pièces voisines se préparent en arrière-plan. Si le rendu 3D ne fonctionne pas, un aperçu fixe et la liste des six destinations donnent accès aux contenus. Si une salle charge, le visiteur peut revenir au plateau. Le son reste désactivé tant que le visiteur ne l'a pas demandé.

## Critères de revue visuelle et fonctionnelle

- Les six pièces possèdent un volume, un objet principal et une silhouette reconnaissables avant lecture de leur nom.
- Le noyer, le bleu nuit et les mêmes huisseries se retrouvent dans les six pièces. Chaque accent coloré correspond à un usage précis.
- Dès l'arrivée, le visiteur comprend que Sandbox est une émission sur l'IA, l'engineering et le produit, et peut accéder à un replay.
- Aucun défilement n'allume le plateau, ne retourne la scène ou ne force une progression entre les pièces.
- Le portail apparaît au curseur sur toute l'illustration, y compris hors des anciens points d'accès. Les commandes contextuelles déterminent la pièce révélée.
- Le clic dans le décor déclenche la traversée ; les liens des affiches, projets et rubriques gardent leurs actions.
- Pendant la traversée, le sol et les objets de destination restent continus. Une capture avant, au seuil et après permet de vérifier ce raccord.
- Au moins un objet de contenu est utilisable dans chaque pièce ; ses données viennent du catalogue ou de la rubrique existante.
- Les classements conservent leurs dates ; les actualités conservent leurs sources et leur statut de synthèse ; les affiches correspondent à de vrais replays.
- Chaque pièce reste accessible sur ordinateur au clavier et avec les mouvements réduits. La recette mobile reste reportée.
- Un chargement interrompu ou un rendu 3D indisponible ne bloque pas l'accès aux contenus.

La recette devra distinguer les captures visuelles, les tests de navigation et les mesures de performance réellement effectuées. Aucune fluidité sur téléphone physique, consommation GPU ou équivalence avec la vidéo source n'est établie par cette note.
