# Time Machine : 151 affiches distinctes

Date : 2026-10-16. Conception décidée par l'agent sur délégation (PD-0003), après la demande de Lou de ne plus répéter les mêmes images.

## Collection finale

Chaque événement du corpus possède son propre fichier SVG, sous `apps/site/public/images/time-machine/events/`. La collection contient 151 affiches, 151 chemins distincts et 151 compositions géométriques distinctes, y compris lorsque les textes sont retirés du calcul de comparaison. Elle remplace les 19 images de concept partagées de la première version.

Les modèles utilisent des identifiants courts et des versions réelles du corpus : par exemple 4o, 6.1 SOL, SONNET 5.5 ou LARGE 4. Les inventions et travaux scientifiques emploient des illustrations de concept liées à leur sujet : mécanisme de mémoire, attention, protéines, matrices, fluide, cristal, échiquier ou robotique. Les cartes gardent leur date, leur titre complet et leurs sources dans l'interface.

Les illustrations sont vectorielles. Elles ne sont ni des photographies historiques ni des copies de figures scientifiques. Les formes des modèles représentent un concept graphique, pas leur architecture réelle ni leurs performances. Aucun fait, nombre ou événement du corpus n'est modifié.

Les 120 événements dont l'éditeur est couvert utilisent un logo provenant d'une source officielle. Les autres affichent le nom de l'organisation du corpus. Onze logos sont disponibles. Les marques servent à identifier leur éditeur, sans suggérer de partenariat. Ce sont les identités publiées par leurs propriétaires lors de cette vérification, sans prétendre reproduire leur apparence à chaque date historique.

Les identifiants des modèles tiennent dans une zone centrale de 490 pixels du SVG de 1000 x 1000 pixels. Les logos sont centrés dans une zone de 300 pixels, sous l'emplacement de la date ajoutée par l'interface. Les modèles voisins conservent des motifs distincts : prisme pour Gemini 1.0, orbites pour Gemini 4 Argon, quatre éléments pour GPT-4, soleil pour 6.1 Sol. Le champ vectoriel de Navier-Stokes se distingue des ondes de Mistral.

## Sources des logos

Les chemins vectoriels et les couleurs explicites sont conservés. Les attributs de mise en page du site, titres techniques et classes CSS sont retirés. Les logos monochromes héritent de la couleur du support comme dans leur SVG d'origine. Le clip rectangulaire du logo DeepSeek est remplacé par un viewport SVG aux mêmes coordonnées ; ses chemins restent identiques.

| Marque              | Source primaire                                                                                                                                |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| OpenAI              | [Documentation officielle](https://developers.openai.com)                                                                                      |
| Claude              | [Site officiel](https://claude.com)                                                                                                            |
| Google              | [Page Gemini de Google DeepMind](https://deepmind.google/models/gemini/)                                                                       |
| Meta                | [Ressources de marque](https://about.meta.com/brand/resources/meta/company-brand/)                                                             |
| Mistral AI          | [Kit de marque](https://mistral.ai/brand/)                                                                                                     |
| NVIDIA              | [Site officiel](https://www.nvidia.com)                                                                                                        |
| Qwen                | [Fichier du dépôt officiel](https://github.com/QwenLM/Qwen-MM-Plugins/blob/main/src/capabilities/video-edit/skill/assets/images/qwen-icon.svg) |
| DeepSeek            | [Site officiel](https://deepseek.com)                                                                                                          |
| PyTorch             | [Logo du site officiel](https://pytorch.org/wp-content/uploads/2024/10/logo.svg)                                                               |
| SpaceXSI / Grok     | [Documentation officielle](https://docs.x.ai/overview)                                                                                         |
| Artificial Analysis | [Site officiel](https://artificialanalysis.ai)                                                                                                 |

Le manifeste `apps/site/scripts/time-machine-artwork/brand-sources.json` conserve l'URL de chaque source, la date de récupération et l'empreinte du fichier local. Les logos actifs, complexes ou dépendants d'une ressource distante sont refusés ; aucun logo manquant n'est inventé.

## Production reproductible

Le générateur versionné `apps/site/scripts/generate-time-machine-artwork.mjs` lit le corpus validé par Zod et les logos locaux figés. Il produit les affiches et `apps/site/scripts/time-machine-artwork/artwork-manifest.json`, sans appel réseau.

Depuis `apps/site` :

```text
node scripts/generate-time-machine-artwork.mjs
node scripts/generate-time-machine-artwork.mjs --check
```

Le second mode vérifie la reproduction exacte sans modifier les fichiers. Toute modification d'un logo, affiche ou manifeste incohérent provoque une erreur. Un nouvel événement nécessite la génération de sa propre affiche ; il ne reçoit plus une image partagée de repli.

La livraison pèse 1 518 604 octets pour les 151 affiches, après normalisation de l'indentation du logo NVIDIA. Le plus gros fichier pèse 32 863 octets. Les SVG sont servis directement par le composant Image, sans optimisation bitmap. L'illustration principale se charge immédiatement ; les archives restent différées.

## Vérification

Les 32 tests ciblés de la Time Machine passent dans six fichiers, dont les cinq tests d'illustration. Ils couvrent la présence de chaque fichier, la différence réelle des géométries, le budget global de 3 Mo, l'absence de script, de police ou de ressource externe, le chargement accessible et la reproduction du générateur. ESLint et le formatage des fichiers du lot passent.

Sharp décode les 151 SVG en 1000 x 1000 pixels. Des planches de contrôle de modèles et inventions ont été inspectées ; les comparaisons de recadrage et de date sur mobile sont réalisées dans le parcours navigateur final du lot. Les fichiers SVG n'incluent ni script, gestionnaire d'événement, iframe, foreignObject, image distante, href, url(), DTD ou entité externe.

Les images bitmap de la première passe sont conservées comme médias sources, mais ne sont plus utilisées par la Time Machine. Leur provenance reste dans [le rapport de la première collection](time-machine-illustrations-2026-10-16.md).

Aucun compte, publication, commit, push ou nouvelle PR n'est inclus.
