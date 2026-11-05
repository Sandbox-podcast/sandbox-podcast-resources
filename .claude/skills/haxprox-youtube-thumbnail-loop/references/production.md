# Contrat de production et de revue

Tous les chemins de ressources indiqués ici partent de la racine du skill. Enregistrer les livrables dans le projet choisi pour la vidéo.

## Brief pour chaque vidéo

Écrire `brief.json` avec `video_id`, `subject`, `audience`, `verified_result`, `evidence_paths`, `title` et `variants` contenant exactement A, B et C. Chaque variante conserve `intent`, `literal_text`, `reference_ids`, `composition`, `identity_sources`, `portrait_source`, `portrait_selection_reason`, `pose`, `assets`, `prompt` et `comparison_hypothesis`. Une référence s'écrit `chaîne/identifiant-vidéo`. Le résultat vérifié doit être rattaché au scénario, au montage, à une capture réelle ou au brief explicite de Lou.

Un prompt utile précise : miniature YouTube 16:9 ; sujet réel de la vidéo ; image 1 comme identité de Lou ; image 2 comme preuve ou résultat ; autres images comme références de composition ; placement et taille relative du visage et du sujet ; lumière ; texte littéral entre guillemets ; éléments à préserver. Demander l'absence de texte supplémentaire. Répéter les invariants d'identité dans chaque correction.

Utiliser 2 à 5 mots lorsque le sujet le permet. Cette plage est une préférence de conception dérivée du corpus, pas une mesure générale. Un nom de produit plus long reste possible. Mettre le texte dans une zone calme ; préserver une marge d'environ 4 % et éviter le coin inférieur droit occupé par la durée. Ces marges sont des conventions internes, à contrôler dans l'aperçu.

Ne pas inventer de capture, facture, notification, résultat financier, chronomètre ou témoignage pour soutenir une promesse. Un objet illustratif peut représenter un mécanisme ; s'il ressemble à une preuve réelle, le remplacer par la preuve fournie ou simplifier le concept. Les noms et logos doivent correspondre au sujet vérifié, même si un concurrent utilise un autre nom dans sa miniature.

## Revue

`review.json` conserve les chemins et, pour chaque version, `identity`, `anatomy`, `literal_text`, `mobile_readability`, `truthfulness`, `hierarchy`, `reference_fit`, `distinctness`, `observed_defects`, `correction`, `status`. Les champs de contrôle contiennent des observations, pas seulement une case cochée. `status` vaut `ready` ou `provisional`. Garder l'historique des corrections et les prompts, sans écraser un master antérieur.

Une auto-revue visuelle vérifie les images, pas la performance marketing. Si le visage dérive, repartir des originaux et corriger le portrait. Si le texte est faux, demander une correction ciblée à imagegen. Si le texte est trop long, réduire en gardant la promesse vérifiée. Si les variantes se ressemblent, changer la composition ou la preuve mise en avant.

Préparer les fichiers et les aperçus :

```powershell
python scripts/prepare_delivery.py --images A.png B.png C.png --out exports
```

Le script refuse un ratio incorrect et trois images identiques. Il ne recadre pas une composition défectueuse. Il conserve les sources et crée trois JPG 1280 x 720 sous 2 Mo, les aperçus à 320 et 160 pixels de large, `comparison.jpg` et `technical-checks.json`. Il signale l'agrandissement éventuel ; agrandir un fichier n'ajoute pas de détail. Ouvrir les trois exports et leurs aperçus avant de les dire prêts. Les fichiers générés par l'outil natif doivent être copiés dans le projet depuis le dossier renvoyé par l'outil.

## Contraintes YouTube vérifiées le 1 novembre 2026

L'[aide YouTube sur les miniatures](https://support.google.com/youtube/answer/72431?hl=en) recommande désormais 3840 x 2160 pour les vidéos, au ratio 16:9, JPG ou PNG. Les limites indiquées sont 2 Mo sur mobile et 50 Mo sur ordinateur. Le projet livre un export de compatibilité à 1280 x 720 sous 2 Mo et garde le plus grand master natif ; ne pas le qualifier de master 4K s'il ne l'est pas. Reconsulter la documentation avant de fixer une nouvelle règle technique.

L'[aide YouTube sur les tests A/B](https://support.google.com/youtube/answer/16391400?hl=en) permet jusqu'à trois variantes et décide selon le temps de visionnage. Elle recommande une haute résolution et indique un abaissement à 480p si une variante est sous 720p. Vérifier l'éligibilité réelle de la chaîne et de la vidéo lorsqu'un test est demandé. La disponibilité générale ne prouve pas que Lou y a accès.

## Retours et performance

Dans `assets/preferences.json`, enregistrer les corrections textuelles de Lou et leur portée, en citant la proposition. Une variante choisie n'est pas automatiquement gagnante en performance.

Pour un résultat YouTube fourni par Lou, créer un fichier de mesure lié au run : date, vidéo, variantes exactes et empreintes, titre, période, impressions, CTR si disponible, temps de visionnage ou part de temps, trafic et conclusion affichée. Mentionner les données absentes. Conserver un résultat non concluant. Ne pas isoler l'effet du design si titre, distribution ou période ont aussi changé.

Une préférence répétée ou un résultat documenté peut conduire à modifier une règle de `patterns.md`. Conserver la source du changement et distinguer préférence esthétique, observation et résultat mesuré. Sans données, proposer une hypothèse à tester.
