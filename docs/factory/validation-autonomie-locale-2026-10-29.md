# Validation de la chaîne locale — 29 octobre 2026

Demande suivie dans l'[issue #8](https://github.com/Sandbox-podcast/sandbox-podcast-resources/issues/8). Le [guide d'exploitation](autonomie-locale.md) donne les commandes reproductibles. Ce lot est local, sans commit, push ou PR.

## Résultat observé

Une commande `prepare`, sur une base vide et sans transcription fournie, a terminé les six étapes avec les vrais moteurs installés : faster-whisper small, qwen3.5:9b et gemma3:12b. La vidéo d'entrée contient une voix française de synthèse et une affiche de test. Ce n'est pas une émission réelle.

```powershell
$env:PYTHONPATH = 'tools/youtube-growth/src'
& ./.local/autonomy-venv/Scripts/python.exe -m youtube_growth.factory `
  --state-dir .local/autonomy-acceptance-v10 prepare `
  .local/autonomy-recette-20261029/master-synthetique.mp4 `
  --episode-id recette-locale `
  --title 'Comment contrôler les sources et le contexte des extraits' `
  --publication-at '2026-10-30T09:00:00+01:00' `
  --next-filming-at '2026-11-05T18:00:00+01:00' --synthetic
```

La commande a retourné `0`. Résultat : un extrait horizontal sous-titré de **20,36 secondes**, trois JPEG de miniature, leurs aperçus 320/160, une planche de comparaison, un pack YouTube local et une proposition pour le 30 octobre à 10 h, heure de Paris. Le nombre de contenus vient de la sélection de ce passage ; il ne constitue pas un quota.

Les fichiers sont exclus de Git. Sur le poste de recette :

- Base : `.local/autonomy-acceptance-v10/`.
- Journal de commande : `.local/autonomy-acceptance-v10-run.txt`.
- Extrait et sous-titres : `.local/autonomy-acceptance-v10/episodes/recette-locale/renders/5d2cc85cb50314723705/`.
- Miniatures, brief et planche : `.local/autonomy-acceptance-v10/episodes/recette-locale/autonomy/586f6f63e0c85176e45fbbae/thumbnails/6287f43a4d2212d4a3700ffb/`.
- Calendrier et bilan lisible : `.local/autonomy-acceptance-v10/reports/recette-locale-local-fedb5211593cd5ff24cff8d6.json` et `.md`.

L'empreinte du master après traitement est identique à celle importée : `586f6f63e0c85176e45fbbae1de3dea0e4d8a0d9998faebdf8f6069083639fb0`. L'extrait a l'empreinte `ab853015b78a25e20fc25843e9771f55fe9cd145f86dd632813cd4925e25ec49`.

## Contrôles effectivement réalisés

Les contrôles du décodage, des dimensions, de la durée et des sous-titres ont réussi. La comparaison du son, après décodage PCM complet, donne des corrélations de **0,9964**, **0,9969** et **0,9960**, avec un décalage mesuré de **0 ms** sur les trois fenêtres examinées. Cela ne démontre pas une écoute intégrale.

L'ASR brut est conservé. Dans cette recette finale, small a correctement reconnu notamment « aux paroles réellement conservées ». La relecture orthographique n'a proposé aucune correction : `changes=[]`. L'application d'une correction bornée est couverte par les tests, pas démontrée par ce cas réel de moteur.

Chaque concept possède sa propre citation. Une vérification distincte associe le concept « Réserve » à « Une coupe ne doit pas supprimer une réserve qui change le sens », à **17,14–20,34 s**, plutôt qu'à la phrase sur l'intégrité du fichier. Les textes viennent des paroles, puis les images du master sont intégrées et les aperçus réellement transmis au modèle de revue visuelle.

Une seconde lecture par un autre agent a inspecté les trois JPEG, les trois aperçus 160, la planche, le brief, les citations, le SRT et deux images du rendu. Aucun problème bloquant relevé dans ce périmètre. Les textes sont complets et lisibles ; les preuves correspondent désormais aux trois angles. Les formules « Master, montage, vérification » et « Coupe, sens, réserve » restent mécaniques. Les concepts sur l'empreinte et l'intégrité sont proches, même si leurs questions et preuves sont distinctes. Cette revue n'a comporté ni écoute ni visionnage continu.

Le navigateur a chargé les vrais fichiers du cycle : six vues vérifiées à **375, 768 et 1440 pixels**, sans débordement, erreur JavaScript, requête de mutation ou requête externe. Le compteur des dates proposées correspond au calendrier. Captures locales : `.local/autonomy-thumbnails-desktop.png` et `.local/autonomy-calendar-mobile.png`.

La vérification du calendrier a été rejouée avec le dernier code de contrôle des reçus : résultat `completed`, aucun contenu bloqué. Il reste conditionnel à la disponibilité de l'émission, avec `valid_for_publication=false`. Aucun job `dispatch`, aucun identifiant distant et aucune date de programmation distante. La configuration conserve `mode=simulation`, `live_enabled=false` et les dépenses externes désactivées.

## Défauts rencontrés et protections conservées

Les itérations précédentes ont révélé des problèmes réels, corrigés avant cette recette :

- Incompatibilité faster-whisper/PyAV et résolution incomplète d'un cache de poids ; dépendances et résolution hors réseau corrigées.
- Décalage audio AAC d'environ 46,5 ms ; correction de l'origine temporelle du rééchantillonnage et tests au début ainsi qu'après une coupe non entière.
- Erreurs lexicales avec le modèle tiny ; recours explicite à small, sans téléchargement par le worker.
- Phrases de miniature tronquées ; validation des formulations et de leur encombrement réel.
- Mélange entre preuve technique et sens du propos ; plan, rédaction par concept, ancrage lexical et association sémantique distincte.
- Reprise du texte de l'affiche comme sujet ; rédaction textuelle depuis les paroles, puis revue des images réelles séparée.
- Reçu de génération modifié non détecté par le suivi léger des fichiers ; suivi des reçus imbriqués ajouté, avec retrait du calendrier testé.

Des réponses et des miniatures refusées ont bien bloqué leurs étapes. Les refus restent conservés sous `.local/` ; ils n'ont pas été transformés en validations. Les tests distinguent explicitement doubles d'inférence, vrais exports FFmpeg, vrais appels aux modèles et inspection indépendante des fichiers.

## Tests et contrôles du lot final

- Suite Python du package, avec `FACTORY_MEDIA_INTEGRATION=1` : **270 tests exécutés en 66,163 s, 267 réussis et 3 ignorés** faute de PostgreSQL local configuré. Les tests PostgreSQL sont prévus par le service de CI ; ils ne sont pas déclarés validés sur ce poste.
- Parmi eux, **27 tests** couvrent la nouvelle autonomie et ses contrats : reprise, idempotence, panne partielle, source ou preuve modifiée, dates manquantes, absence de sélection, modèle absent, réponses invalides, cache, corrections orthographiques bornées et correspondance audio réelle.
- Politique de rangement du dépôt : contrôle réussi et **6 tests réussis**.
- Compilation Python, syntaxe du script navigateur et `git diff --check` : réussis.
- Recette navigateur sur les vrais résultats : réussie, périmètre décrit ci-dessus.

Le test de verrou de processus utilise désormais l'interpréteur de base sous Windows : tuer uniquement le lanceur d'un environnement virtuel laissait auparavant son interpréteur enfant actif. Le test reste exécuté. Aucun gate n'a été désactivé pour faire réussir le lot. L'index Git est resté vide ; les sources modifiées et les nouveaux fichiers n'ont été ni commités ni poussés.

## Limites et prochaine validation

Le worker persiste et reprend les étapes ; il peut continuer sans conversation Codex ouverte. Aucune tâche Windows ni aucun réglage système n'ont été installés par ce lot. Le fonctionnement après fermeture de session dépend donc du mode de lancement du worker.

Les contrôles automatiques ne prouvent ni l'exactitude parfaite d'une transcription, ni un visionnage continu, ni des droits absents des entrées. Le cadre entier est conservé ; le suivi des intervenants et le recadrage dynamique d'une démonstration restent à développer. Une revue peut refuser une image ou un texte insuffisamment lisible.

La prochaine recette doit porter sur un master réel complet de 60 à 120 minutes, avec plusieurs intervenants et démonstrations, pour mesurer les erreurs ASR, les passages retenus/manqués, la conservation des réserves, la lisibilité et le temps de traitement. Cette recette synthétique ne prouve pas ces propriétés ni l'efficacité publique des miniatures. La diffusion sociale reste hors du périmètre autorisé.
