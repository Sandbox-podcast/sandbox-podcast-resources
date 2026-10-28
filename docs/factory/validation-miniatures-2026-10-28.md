# Validation de la préparation des miniatures

Évolution demandée par Lou le 28 octobre 2026 : expliquer le fonctionnement de la factory dans un README humain, puis préparer les miniatures à partir de références pertinentes, de concepts argumentés et de revues croisées. Les fichiers et données de la première recette sont conservés. La simulation et le blocage des écritures sociales restent actifs.

## Livré

Le [README côté équipe](README.md) décrit les entrées, étapes, rôles, états, blocages, bases et sorties, avec un brief à donner à Codex. Les README du dépôt et de YouTube Growth y renvoient. Les commandes restent dans l'exploitation.

Le [relevé visuel](references-miniatures-2026-10-28.md) examine treize miniatures de six chaînes, avec un [JSON de provenance](references-miniatures-2026-10-28.json). Les observations portent sur les titres, mots, images et compositions. Les compteurs publics ne servent pas à attribuer une performance aux miniatures. Aucun asset concurrent n'a été ajouté aux créations SANDBOX.

`factory/thumbnails.py` vérifie le brief, les références, les citations de transcription, les coupes et les cadrages. Il produit trois JPEG, six aperçus et une planche titre/image. Les images viennent des coupes source ou de photos autorisées. La revue est distincte de la conception et de la QA média. Elle est liée aux empreintes du brief, des images et du packaging. La planification et l'envoi simulé les vérifient à nouveau. Un test actif empêche la préparation de nouveaux packs avant écriture. Les sauvegardes portables conservent les images, les copies de photos et leurs références.

La procédure et les commandes `thumbnails` et `review-thumbnails` figurent dans [miniatures.md](miniatures.md). Le skill `sandbox-packaging` et les consignes du package les rendent obligatoires pour les extraits YouTube développés. Les gabarits historiques restent des outils locaux ; ils ne satisfont pas seuls la revue éditoriale.

## Contrôles exécutés

La suite Python complète a exécuté 186 tests en 123,892 secondes : 183 réussis et trois tests Postgres ignorés faute de base locale. `FACTORY_MEDIA_INTEGRATION=1` était actif. Les nouveaux scénarios vérifient notamment le remplacement d'une image au même chemin, le titre modifié après revue, la QA média insuffisante, le verrou avant écriture, la source hors des coupes, les faux horodatages à l'intérieur d'un segment et la restauration sans les fichiers d'origine. Journal local : `.local/factory-thumbnails-final-tests.txt`.

Les tests HTTP vérifient les PNG de prévisualisation, leurs tailles et leurs empreintes, le refus d'accès hors stockage et le refus d'un aperçu modifié. Le JavaScript de la page passe `node --check`. La compilation Python et `git diff --check` passent. Le skill modifié passe `quick_validate.py` et les textes rédigés passent le vérificateur de ponctuation. Les liens locaux de la documentation ont été contrôlés.

La recette `.local/factory-miniatures-validation-v2` a exécuté ingestion, montage, concepts, revue de contrat, calendrier et collecte simulés. Elle conserve cinq envois simulés et un pack LinkedIn expiré après fermeture. Son bundle `e84f5ab3177d95826993dee7` contient trois JPEG en 3840 x 2160, les aperçus 320/160 et `comparaison.png`. Aucun gagnant de performance n'est déclaré. Les références de cette recette sont synthétiques et ne peuvent pas préparer une miniature réelle.

## Revue visuelle et limites

Un second agent a ouvert le brief, la planche, les trois JPEG et les six aperçus. Les trois phrases principales restent lisibles à 320 et 160 pixels, sans chevauchement ni recadrage gênant observé. La ponctuation finale reste avec son mot après la correction du retour à la ligne.

Le texte interne de la mire, dont sa mention synthétique, devient illisible à 160 pixels. Les titres de la planche, le brief et les états de l'interface signalent la recette ; ces images isolées ne doivent pas servir de propositions d'épisode. Les trois concepts utilisent la même carte technique. Cette vérification ne valide ni un visage réel, ni un écran de démonstration, ni la qualité éditoriale d'un véritable extrait.

La dernière vérification visuelle de la galerie dans l'onglet n'a pas pu être exécutée : l'outil de contrôle du navigateur était indisponible. Les fichiers rendus, le service HTTP et la syntaxe JavaScript ont été contrôlés séparément. Une revue d'un vrai épisode devra porter sur ses propres images et aperçus avant approbation. Aucune écoute, connexion sociale, publication ou performance réelle n'est déduite de cette recette.
