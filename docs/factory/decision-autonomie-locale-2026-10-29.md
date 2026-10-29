# Décision : chaîne autonome locale, 29 octobre 2026

Décidée par l'agent sur délégation (PD-0003), à la demande de Lou : préparer automatiquement l'analyse du master, les extraits, les miniatures et le calendrier, avec contrôles et tests, sans publier sur les réseaux.

## Périmètre

Étendre le worker et SQLite existants. Une entrée explicitement marquée `local_autonomy` déclenche des étapes persistantes : transcription, analyse et sélection, rendu, revue automatique, miniatures, revue du packaging et calendrier local. Les anciens parcours restent compatibles.

Les modèles s'exécutent sur le poste : faster-whisper avec des poids déjà présents, et Ollama sur une adresse de boucle locale. Les noms de modèles et leurs paramètres sont configurables. Le poste inspecté possède notamment qwen3.5:9b et gemma3:12b avec vision. La première recette avec faster-whisper tiny a révélé des erreurs lexicales ; les poids publics de small ont été installés explicitement pour améliorer cette base. Aucun téléchargement de poids, compte cloud ou appel payant n'est déclenché par le worker. Un modèle absent bloque l'étape avec son motif.

## Nature des preuves

Les revues automatiques portent sur des entrées identifiées : transcription, extraits audio comparés, images échantillonnées, rendus et aperçus de miniatures. Leurs empreintes, modèles, prompts, périmètres et conclusions sont conservés. L'échantillonnage visuel n'est jamais présenté comme un visionnage continu ; l'ASR n'est pas une écoute humaine. Aucun nom ni aucune attestation de personne ne sont inventés.

Le statut local des médias contrôlés est distinct d'une validation opérateur autorisant la diffusion. Les revues humaines existantes et les barrières sociales restent intactes. Une revue négative ou incomplète bloque le contenu concerné ; un autre contenu peut continuer. Les réponses des modèles sont des données validées, sans outils ni autorité sur le système.

## Calendrier

Produire une prévision dans un enregistrement séparé, sans créer de job `dispatch`, même simulé. Avant disponibilité réelle confirmée de l'émission, la prévision est explicitement conditionnelle à la date de sortie prévue. La borne du prochain tournage reste nécessaire et n'est pas devinée. Une URL absente ne bloque ni le montage ni les miniatures ; elle reste un préalable de diffusion.

## Réutilisation et limites

Les étapes conservent des clés liées à la source, au modèle, au prompt et aux paramètres. Une correction de titre réutilise la transcription ; une modification du média invalide ses contrôles. Une reprise ne marque pas artificiellement une erreur comme réussie.

Le premier niveau de montage conserve l'image entière pour protéger les démonstrations. Le suivi de locuteur et le recadrage dynamique restent une amélioration séparée ; une lisibilité insuffisante doit être signalée par la revue locale.

La recette synthétique et les tests de transport simulé prouvent l'enchaînement et ses protections. Les appels à de vrais modèles locaux constituent une preuve distincte. La fidélité sur des émissions inédites complètes devra encore être mesurée avec leurs masters autorisés.

## Ajustements issus du master réel

Décidés par l'agent sur délégation (PD-0003), dans le périmètre local demandé :

- Utiliser une transcription large-v3-turbo liée au master et conserver les incertitudes de reconnaissance. La probabilité de non-parole ne supprime plus seule du dialogue. Les corrections orthographiques restent des opérations silencieuses mot par mot, avec veto indépendant et conservation du brut.
- Distinguer les paroles conservées du contexte extérieur aux coupes et confronter le titre aux seuls mots conservés. Un titre de discussion peut annoncer une question ouverte ; le contrôle ne doit pas exiger un cours exhaustif ou une réponse définitive non promis.
- Appliquer les réparations éditoriales par plans immuables liés au master et à la transcription, après suspension de la file. Les médias et preuves précédents restent conservés ; les nouvelles bornes refont les revues et le rendu concerné.
- Pour les miniatures, recadrer un participant authentique dans une vraie image du passage. Le cadre vidéo complet reste celui des extraits ; sa réduction dans les miniatures rendait visages et diapositives trop petits. Le critique reçoit uniquement le couple et sa preuve, puis compare séparément les trois concepts. Les instructions de génération ne peuvent tenir lieu de question du public ou de promesse de contenu.
- Rédiger et contrôler le packaging en français naturel pour le public SANDBOX, tout en conservant les noms d'outils et les termes techniques utiles. Une variante fidèle mais en anglais ou en franglais reste refusée. Une demande de trois angles ne justifie aucune réserve inventée.
- Confronter aussi les angles et hypothèses du brief aux citations. Ces champs ne sont pas des preuves ; un titre interrogatif ne rend pas fidèle une explication causale absente des propos. Fournir la réserve essentielle au plan et garder les champs de rédaction strictement nécessaires à chaque tâche.
- Après échec réel du contrôle textuel sur deux cas fautifs, limiter la génération aux choix d'unités de parole, de mots d'ancrage dans leur propre citation, de titres/phrases d'image et du choix initial. Construire les questions complètes depuis les mots retenus, et les autres textes depuis ces questions, le titre de passage contrôlé et des citations littérales entières (`source_bound_v1`). Préférer omettre une citation trop longue plutôt que couper une condition. Cette décision locale est réversible ; elle réduit les diagnostics inventés sans revendiquer une compréhension générale certifiée.
- Autoriser une unique atténuation de sortie par version de politique lorsque le seul défaut technique est le niveau de crête. La première politique utilisait −1,5 dB ; la version corrigée mesure les pics flottants AAC et calcule la baisse nécessaire pour viser −1,5 dB. Une reprise d'ancien échec repart de l'export d'origine. Copier les images encodées et refaire les contrôles sur les nouveaux fichiers. Ne jamais assimiler cette correction à une restauration d'un son source écrêté.
- Réserver une bande aux sous-titres du rendu horizontal local pour conserver les noms du master visibles. Regrouper les fragments d'affichage fugitifs avec leurs voisins sans changer les mots ni inventer d'horaires au mot. Cette évolution versionne les paramètres du rendu, préserve les fichiers précédents et réutilise l'analyse compatible.
- Vérifier les bords sur le seul texte intégral conservé, sans titre ni contexte extérieur. Une amorce orale ou le nom donné à une notion déjà expliquée n'est pas, à elle seule, une phrase coupée. Les fausses interprétations des premiers contrôles et leur calibration sur les cas réels restent dans les reçus.
- Conserver le dépassement de capacité du calendrier sans accélérer la cadence. La date de tournage du 1er novembre, fournie sans heure, donne une borne prudente à 00:00 Europe/Paris pour cette recette, explicitement enregistrée comme hypothèse.

La [recette du master de l'épisode 3](validation-master-episode-003-2026-10-29.md) porte les observations réelles, les résultats et leurs limites. Aucune de ces décisions n'autorise de diffusion sociale.


Décision locale complémentaire sur délégation (PD-0003) : accepter une revue indépendante explicite d'images et de textes lorsqu'elle satisfait les six critères et leurs preuves liées aux fichiers courants. Conserver l'avis automatique, ne modifier aucune revue audio et ne créer aucune intention sociale. Une telle revue n'est pas produite automatiquement par le worker à partir d'un refus. Les essais de miniatures du présent master sont ensuite arrêtés à la demande de Lou ; les fichiers et les constats restent conservés.
