# ADR-0011 — Post-production : logique pure, exécuteurs injectés, validation avant application

- Statut : acceptée
- Date : 2026-10-06
- Décidée par l'agent sur délégation (PD-0003)

## Contexte

La post-production (transcription, clips, exports) combine des traitements lourds et faillibles (ffmpeg, fournisseurs IA) avec des règles métier précises (AC-TRANSCRIPT, AC-CLIP, AC-EXPORT). Les sorties d'un modèle ne doivent pas être appliquées sans validation (§26.6). Les sources ne sont jamais modifiées (AC-EXPORT-002).

## Décision

1. **Logique pure, exécution injectée.** `packages/post-production` ne lance rien : il construit les arguments ffmpeg, décide des étapes et des essais, valide. Les exécuteurs (rendu, vérification, empreinte, nettoyage) et le fournisseur de transcription sont des interfaces injectées. Les tests utilisent des faux ; l'essai de bout en bout utilise ffmpeg.
2. **Transcription** : fournisseur derrière une interface `TranscriptionProvider` ; sa sortie est validée (schéma, durée du média, cohérence) avant d'être acceptée, sinon l'essai échoue comme une panne. Quatre essais, délai de 30 s doublé à chaque échec avec plafond de 10 min, échec final explicite, relance manuelle. L'état de la tâche est indépendant de l'accès au média. Le document est **immuable et versionné** : une correction produit une version, le journal garde l'avant, l'après, l'acteur et l'instant.
3. **Suggestions de clips** : jamais appliquées sans passer par `validateSuggestions`. Les points doivent correspondre à des limites de segments existants (tolérance 0,25 s, puis recalage exact), la durée tient de 15 à 90 s, les doublons (recouvrement de plus de la moitié du plus court) sont écartés au profit du mieux noté. Un timecode proposé par un modèle ne devient jamais un timecode du système sans ce recalage. L'utilisateur peut ensuite ajuster IN/OUT librement dans le média (mêmes bornes de durée).
4. **Alignement** : modèle `fichier = (T − départ) × (1 + dérive)` par piste, estimé par moindres carrés sur des repères communs ; la vidéo d'un participant sert de référence ; la dérive audio est corrigée par `atempo`, un fichier qui commence après le départ du clip est retardé par `adelay`. Un minimum de repères est exigé.
5. **Export** : la liste de décisions de montage référence les sources. Un export est une tâche en trois étapes (rendu, vérification, empreinte), reprise sans refaire les étapes réussies. L'annulation supprime **uniquement** le dossier temporaire du job ; l'exécuteur refuse tout chemin hors de la racine des exports. Le fichier est rendu dans le dossier temporaire et la traçabilité (épisode, version du preset, version de la liste de montage, pistes sources, date, auteur, SHA-256) n'est produite qu'après réussite.
6. **ffmpeg** est appelé avec un tableau d'arguments, jamais par une chaîne passée à un shell : un nom de fichier hostile reste un argument.
7. **Loudness** : cible de −16 LUFS par défaut pour les exports audio de podcast, en une passe. Valeur d'usage courant, à valider ; la mesure en deux passes viendra.

## Conséquences

- Le comportement des exports est testable sans ffmpeg ; la conformité du rendu réel se vérifie par un essai de bout en bout, pas encore automatisé.
- Un vrai fournisseur ou un vrai modèle de suggestion s'ajoute sans changer le domaine, mais sa qualité reste à évaluer avec un jeu d'évaluation versionné (§26.5).
- Les tâches ne survivent pas à la mort du processus qui les exécute : une file persistante est à concevoir avec le MVP.

## Risques

- Le recalage des suggestions sur des segments suppose une transcription de qualité : une transcription fausse donne des clips coupés au mauvais endroit, valides en apparence.
- Les zones de sécurité des formats verticaux sont indicatives.
- Le choix de caméra d'un clip est naïf (premier locuteur) ; la régie enregistre le Program, qui sera une meilleure source de décision.
