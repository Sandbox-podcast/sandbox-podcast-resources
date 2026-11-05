# Corpus reproductible

Le premier relevé se trouve dans `assets/corpus/2026-11-01/`.

Pour une actualisation seulement, installer les dépendances avec `python -m pip install -r requirements-corpus.txt`. Le relevé inclus fonctionne sans réseau. L'extraction ne télécharge aucune vidéo ni aucun son. Commandes depuis la racine du skill :

```powershell
python scripts/corpus.py --config references/channels.json --root assets/corpus/NOUVELLE-DATE
```

Sans `--refresh`, le script reprend les inventaires et les images déjà présents. `--channel SLUG` réduit une reprise à une chaîne ; il ne faut pas l'utiliser pour annoncer ensuite une couverture des sept. `--refresh` relit le catalogue distant ; préférer un nouveau dossier de relevé pour conserver les anciennes preuves.

Chaque chaîne possède `raw.json`, `manifest.json`, `images/` et `boards/`. L'ordre est celui de l'extracteur, généralement les vidéos récentes en tête ; il ne suffit pas à prouver une date de publication. Le manifeste conserve identifiant vidéo, URL, titre renvoyé, vues éventuellement disponibles, URL image et empreinte. Un titre peut être localisé par YouTube ; ne pas le présenter comme la transcription exacte du texte de la miniature.

`coverage.json` donne le résultat de chaque chaîne et les échecs. Un extracteur qui termine sans erreur n'est pas une preuve indépendante que YouTube n'a rien omis. Les planches contiennent toutes les entrées retournées, par groupes de 40, avec leurs indices et identifiants.

Après examen réel, consigner dans un `review.json` séparé les planches ouvertes et leur niveau d'examen. Indiquer les miniatures ouvertes individuellement en plus. Le script initialise `visually_reviewed` à faux : le téléchargement ne prouve pas une analyse. La revue initiale est dans `review.json`, qui fait autorité pour l'examen, sans modifier les données brutes.

Périmètre initial : les sept URLs `/videos` fournies. Les onglets Shorts et directs ne sont pas collectés. Les vidéos privées, supprimées, cachées et les anciennes variantes d'une miniature remplacée restent hors d'accès. Pour une nouvelle demande qui inclut ces onglets, les traiter explicitement et conserver des couvertures séparées.

La galerie locale `atlas.html` permet de filtrer le corpus et d'ouvrir la miniature téléchargée ou la vidéo. Les images des autres créateurs servent de références d'analyse. Elles n'entrent pas telles quelles dans les livrables de Lou. Respecter les échecs d'accès et les limitations ; ne pas utiliser de session privée ou payante pour les contourner.
