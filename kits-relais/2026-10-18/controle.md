# Contrôle du lot

État du 18 octobre 2026. Les mesures ci-dessous portent sur les fichiers locaux, pas sur une publication YouTube ou une performance d'audience.

## Livré

- Trois kits personnels : Lou, Loïc et Nico.
- Pour chacun : deux propositions LinkedIn et une variante avec vidéo, trois publications X indépendantes, un bloc de profil GitHub et son mode d'emploi, deux cartes, un extrait vertical existant d'E1 et un nouvel extrait horizontal d'E2.
- Quatre vidéos autonomes, deux par épisode, avec miniatures, descriptions, chapitres, sous-titres et bornes source.
- Trois archives ZIP personnelles, contenant les textes et les assets du kit concerné.

## Contrôles exécutés

- Trois tests Python : arrondi des horodatages, bornes et accents des sous-titres, protection de la source contre l'écrasement. Réussis.
- Fin commune HyperFrames : vérification complète réussie, aucune erreur ni avertissement, 15 contrôles de contraste réussis.
- Fin commune : rendu HyperFrames de 3 secondes, puis ajout d'une piste silencieuse pour l'assemblage.
- Exports nouveaux : ffprobe et décodage FFmpeg intégral, dimensions 1280 x 720, présence d'audio et durée comparée au montage.
- Neuf textes X sous la limite de 280 caractères avec URL comptée à 23 caractères.
- Cartes et images d'extraits examinées sur une planche de contact.
- Copie retrouvée d'E1 vérifiée sur des images à 37:19, 42:30 et 1:13:20 : les intervenants et les mises en page de l'émission sont présents. Les images des deux montages E1 ont aussi été examinées.

Les empreintes et durées exactes sont dans `assets.json` et les fichiers `montage.json` et `extrait.json`.

## Correction du double affichage des sous-titres, le 18 octobre

Lou signale un doublon à la lecture de son extrait. Les images extraites du MP4 horizontal montrent une seule couche incrustée, et ffprobe ne trouve aucune piste de sous-titres supplémentaire. Le fichier voisin `extrait.srt` peut être chargé automatiquement par le lecteur et ajouter une seconde couche. L'image vérifiée dans l'extrait vertical montre aussi une seule couche de sous-titres.

Les SRT des trois kits personnels sont déplacés à l'identique dans `production/captions/`. Les trois ZIP sont actualisés sans ces SRT ; leurs autres fichiers correspondent aux dossiers personnels. Le script de montage écrit désormais les SRT dans ce dossier de production. Les empreintes des médias restent identiques, sans réencodage.

Les quatre tests Python passent, dont le test qui vérifie que la génération des trois extraits place les SRT hors des kits personnels. Les 26 empreintes et tailles du manifeste, les 41 liens locaux et les trois archives sont vérifiés. Les deux extraits de Lou passent le décodage intégral. La lecture dans le lecteur utilisé par Lou reste à confirmer après fermeture et réouverture du fichier.

La relance de `pnpm check` passe le formatage puis échoue au lint : 7 140 erreurs dans les 30 copies de `gsap.min.js` sous `exports/reseaux-sociaux/episode-02/revisions/camera-unique-v2/projects/`, hors de cette correction. La chaîne n'exécute donc pas les types ni les tests du site. Aucun contrôle n'est désactivé.

## Limites de revue

Les sous-titres proviennent de transcriptions automatiques. Quelques erreurs évidentes sont corrigées, mais la relecture humaine complète à l'écoute reste à faire avant diffusion. Le contrôle de décodage et les images de contrôle ne démontrent pas une validation d'écoute complète.

La copie propriétaire d'E1 indiquée dans les anciens manifestes n'est plus présente. Une copie complète locale préparée pour Spotify a été retrouvée : `sandbox-ep01-pilote-spotify-rec709.mp4`, durée 4701,542 secondes, vidéo 1920 x 1080 à 24 images/s et couleur Rec.709. Les deux montages E1 utilisent cette source. Son empreinte est conservée dans les manifestes ; le fichier complet reste hors de Git. La source E2 est la copie Studio 1280 x 720 à 25 images/s, durée 7523,660 secondes.

`pnpm check` a été lancé dans le checkout partagé. Il s'est arrêté au formatage : le dossier E2 produit dans une autre tâche contient de nombreux fichiers non formatés, et un fichier vidéo temporaire a disparu pendant son inventaire. Les fichiers de ce kit sont formatés séparément. `pnpm lint` a aussi rencontré les copies locales de GSAP minifié de cette autre production. Ces fichiers ne font pas partie de la PR. Le résultat global n'est pas déclaré réussi.

`pnpm typecheck` réussit. `pnpm test` réussit hors du bac à sable : 694 tests du site et 35 tests média et conducteur. Le premier essai dans le bac à sable a échoué sur les dossiers temporaires et sous-processus ; la relance autorisée confirme le résultat. Les validations complémentaires et la CI de la PR sont consignées dans la description de PR.

Aucune action sur les profils personnels, aucun changement du test A/B et aucune programmation sociale dans ce lot.
