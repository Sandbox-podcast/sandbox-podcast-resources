# Génération des formats des prochains épisodes

Lou demande le 24 octobre 2026 un système utilisable par Nico et Loïc sur les prochaines émissions, avec des Shorts adaptés à chaque réseau et des vidéos thématiques de 5 à 15 minutes. Les trente compositions E02 restent une référence ; leurs timecodes ne définissent pas les prochains lots.

## Décision de réalisation

Décidée par l'agent sur délégation (PD-0003) : réutiliser le moteur vertical existant dans `youtube_growth.social`, avec un plan éditorial explicite par épisode et par réseau. Chaque variante choisit son intervalle continu, son titre, sa légende et son cadrage. Le mode par défaut simule sans écriture ; `--execute` rend localement. La reprise lie le plan, la source, la transcription et les sorties à leurs empreintes. Le programme refuse les sorties modifiées ou les changements de plan dans un dossier déjà utilisé.

La sélection et l'adaptation restent éditoriales. Le programme ne prétend pas trouver automatiquement le meilleur angle TikTok ou Instagram, ni prédire la rétention. Une nouvelle émission exige ses propres passages et une inspection des images.

Le module `youtube_growth.thematic`, ses contrôles et ses tests sont intégrés dans le même lot. Il accepte des émissions différentes, produit au plus cinq sujets autonomes de 300 à 900 secondes et peut ne retenir aucun candidat. Son analyse locale utilise un vocabulaire limité ; l'analyse sémantique payante est explicitement optionnelle. Voir ADR-0040 pour les choix du moteur horizontal.

## Livrables

- Le [guide de génération](../../../../../tools/social-network-manager/GENERER.md) contient l'installation, les entrées, les commandes et le plan social illustratif à remplacer.
- Les variantes courtes ont des sorties séparées par réseau et passage, avec sous-titres, légende et manifeste.
- Les formats thématiques comprennent vidéo, sous-titres, proposition de miniature, titre, description et carte des coupes.
- Le workflow de tests installe FFmpeg, Pillow et NumPy pour exercer les recettes média sur sources synthétiques.

Les sources, rendus, sessions et accès restent locaux. Aucun appel de publication ni routine automatique n'est ajouté. Les rendus sont à relire avant toute diffusion autorisée. L'objectif de 10 000 abonnés ne constitue pas une performance prédite par ces outils.

## Vérification

Les tests du module social couvrent des bornes et textes différents par réseau, trente passages et quatre-vingt-dix variantes, la simulation sans écriture, les plans invalides, les reprises et les empreintes modifiées. Une recette FFmpeg génère deux exports verticaux distincts depuis une source synthétique puis vérifie leur réutilisation sans nouveau rendu.

Les tests thématiques couvrent les preuves de sélection, la durée, les sous-titres, l'alignement image et son, le cache et les modifications de fichiers. Leur recette FFmpeg rend une vidéo synthétique de 310 secondes avec sous-titres sélectionnables puis incrustés. Ces recettes ne constituent pas une revue éditoriale d'une prochaine émission réelle.
