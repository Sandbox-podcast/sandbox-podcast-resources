# Navigation, logo et pied de page sur mobile

Date : 20 octobre 2026. Correction locale demandée par Lou, dans le lot de reprise du compte précédent. Périmètre : en-tête, navigation, logo et pied de page partagés. Les textes et vignettes des épisodes font l'objet d'un travail parallèle.

## Constats et corrections

L'accueil masquait son menu mobile avec une règle CSS dédiée au décor du plateau. Le menu est désormais accessible jusqu'à 1 024 pixels, avec le logo et le choix de langue sur une seule ligne. Ces trois commandes gardent des zones tactiles d'au moins 44 pixels. Les liens du menu mesurent au moins 48 pixels de haut. Un appui extérieur, Échap ou la navigation ferment le menu.

Le fichier du logo chargeait correctement lors de l'audit. Le logo du footer ne portait toutefois aucun lien. Sur l'accueil déjà affiché, un lien Next.js vers la même URL ne ramenait pas non plus systématiquement en haut. Les deux logos conduisent maintenant à l'accueil de la langue courante ; depuis l'accueil, un clic ordinaire ramène directement en haut. Les clics avec une touche modificatrice conservent le comportement du navigateur. Le nom accessible "Accueil Sandbox" utilise la traduction existante, au lieu d'une concaténation française absente des dictionnaires.

Le pied de page déployait tous ses liens et ses six boutons de réseaux sur plusieurs lignes. Sur mobile, les réseaux utilisent maintenant six icônes avec leurs noms accessibles et des zones tactiles de 44 pixels. Les groupes Explorer et Sandbox sont repliables. Le contact par email reste dans le groupe Sandbox ; les liens relatifs aux données personnelles et au flux RSS restent directement visibles. La phrase de présentation reste affichée sur ordinateur. Le rappel des préférences de mesure est conservé.

Les groupes repliables utilisent des éléments `details` natifs : ils fonctionnent aussi sans JavaScript. Les variantes mobiles et bureau sont masquées par CSS selon la largeur ; elles ne présentent pas deux jeux de liens simultanément aux utilisateurs. Les adaptations sont locales et réversibles, dans le cadre de DD-0005, DD-0008 et DD-0028. Aucun compte, contenu publié, image source ou service distant n'a été modifié.

## Mesures et captures

Mesures réelles sur Edge sans interface, avec une fenêtre de 812 pixels de haut, sur `http://127.0.0.1:3100` :

| Largeur | Footer avant, français | Footer final, FR / EN / ES / DE |
| ------- | ---------------------: | ------------------------------: |
| 320 px  |               753,5 px |                        254,5 px |
| 375 px  |               753,5 px |                        254,5 px |
| 390 px  |                 699 px |                        254,5 px |

Le footer replié occupe donc environ 31 % de la hauteur de cette fenêtre. Ces mesures excluent le panneau initial de consentement, indépendant du footer ; la recette refuse la mesure d'audience avant d'interagir avec le pied de page. Les liens gardent une police de 13 pixels et des cibles tactiles de 44 pixels ; seul le copyright utilise 12 pixels.

Preuves locales, dans `apps/site/.local/` :

- `mobile-shell-before/` : captures et mesures initiales des trois largeurs.
- `mobile-shell/final-measurements.json` : les douze mesures finales et le retour en haut par le logo, vérifiés dans les quatre langues.
- `mobile-shell/*-home-final.png` et `*-footer-final.png` : captures finales des douze configurations.
- `mobile-shell/report.json` : recette complète des pages accueil, podcast, News, Charts et À propos dans les quatre langues aux trois largeurs.
- `mobile-shell/supplemental.json` : contrôles sans JavaScript à 320 et 390 pixels, et contrôle bureau à 1 440 pixels. Le menu natif et le contact replié fonctionnent sans JavaScript ; la navigation et le footer bureau restent visibles.

## Vérifications

Le script `apps/site/scripts/test-mobile-shell.mjs` contrôle les liens et le chargement du logo, la navigation tactile, Échap, l'appui extérieur, les quatre choix de langue, les groupes repliables du footer, les liens légaux, le retour en haut et l'absence de débordement horizontal. Il utilise uniquement un serveur local. Les filtres `SANDBOX_MOBILE_WIDTHS`, `SANDBOX_MOBILE_LOCALES` et `SANDBOX_MOBILE_PATHS` permettent de reproduire un cas ; les résultats ciblés vont dans `mobile-shell-targeted/`.

La recette finale réussit les **60 parcours** : cinq pages, quatre langues et trois largeurs, sans route absente, erreur JavaScript ni débordement horizontal. Le footer mesure 254,5 pixels dans chacun de ces parcours.

Les premiers essais pendant les modifications ont rencontré des délais de navigation liés au serveur de développement. Un essai démarré dès `DOMContentLoaded` interagissait aussi avant l'hydratation des gestionnaires React et avant l'apparition du panneau de consentement. La recette attend désormais explicitement l'hydratation du menu, refuse le panneau initial puis attend sa fermeture. Aucun contrôle produit n'a été retiré pour faire passer le test.

Les cinq suites unitaires de navigation, réseaux du footer, réglages du site, confidentialité et accueil passent : **52 tests**. Le contrôle TypeScript sans émission et ESLint sur les fichiers de ce périmètre passent également. Le contrôle global du dépôt et le build sont réalisés par l'agent principal sur le lot consolidé.

## Limites de livraison

Les captures prouvent le comportement local de ce lot. Elles ne décrivent pas encore la version publique, car aucune publication, PR, création de commit ou poussée Git n'a été effectuée dans ce travail. Les autres langues du contenu éditorial et les vignettes relèvent du chantier parallèle ; ce rapport couvre les commandes et liens partagés.
