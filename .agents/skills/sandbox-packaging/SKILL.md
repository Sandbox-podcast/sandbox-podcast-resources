---
name: sandbox-packaging
description: Préparer titres, miniatures et textes SANDBOX avec références visuelles, concepts argumentés et revue croisée, puis pack LinkedIn manuel. Utiliser sur des passages sourcés, sans modifier les contenus distants.
---

# Préparer le packaging

Entrées : rendu et provenance, propos vérifiés, audience principale, épisode et destination accessible. Paramètres : plateforme, version et hypothèse de variante. Outils : factory, assets Sandbox, recherche web et inspection d'images. Lis la [procédure des miniatures](../../../docs/factory/miniatures.md) pour tout extrait YouTube développé et consulte [les capacités](../../../docs/factory/capacites.md) avant d'annoncer une fonction de couverture, de lien ou de test.

Rédige un texte direct avec les mots du contenu. Conserve les faits, noms propres et termes techniques utiles. Utilise les apostrophes simples et guillemets droits. L'angle doit servir les développeurs, équipes produit ou organisations selon le passage. L'humour et le désaccord doivent venir de l'émission. Les skills de rédaction imposés par AGENTS.md restent applicables.

Chaque déclinaison conserve titre si pertinent, texte, couverture disponible, CTA et destination précise. L'extrait doit apporter une idée avant son invitation vers le long. Réutilise une playlist seulement avec son identifiant connu.

Pour un extrait YouTube développé :

1. Analyse le passage, le public et la nuance à préserver. Relève citations exactes et secondes source à l'intérieur du montage livré.
2. Examine visuellement au moins six miniatures sur trois chaînes pertinentes, dont deux avec des formats comparables. Le [relevé initial](../../../docs/factory/references-miniatures-2026-10-28.md) et son [JSON](../../../docs/factory/references-miniatures-2026-10-28.json) fournissent un corpus daté. Adapte-le au sujet et actualise les références périmées. Des vues publiques ne prouvent ni CTR, ni rétention, ni effet causal de la miniature.
3. Conçois trois couples titre/image avec trois hypothèses distinctes. Justifie l'angle, les mots, la complémentarité du titre et de la phrase, le sujet visible et son cadrage. Le texte peut être absent si l'image et le titre suffisent ; motive ce choix. Ne transforme pas une même proposition recolorée en trois concepts.
4. Écris le brief versionné selon le contrat de `factory/thumbnails.py`. Utilise des images du passage ou des photos autorisées ; aucune personne inventée, fausse réaction ou capture trompeuse. Appelle `thumbnails PUBLICATION_ID --brief CHEMIN` sur la bonne base. Les gabarits historiques ne constituent pas une validation éditoriale.
5. Ouvre les trois exports, les aperçus à 320 et 160 pixels et la planche avec les titres. Vérifie les faits, mots, coupes, premier point d'attention, lisibilité, zones occupées par les interfaces et droits.
6. Confie une revue à un autre lecteur ou agent avec les sources, le brief et les images. Il inspecte réellement les fichiers, formule les objections et contrôle les six critères de la procédure. Corrige les propositions insuffisantes. Enregistre ensuite `review-thumbnails` avec responsable et preuves ; la seule présence d'une attestation ne prouve pas un examen visuel. Si l'inspection est impossible, laisse la revue en attente.

La revue média et celle du packaging restent distinctes. Un changement de titre, de texte, de concept ou de fichier invalide le contrôle concerné. Préserver l'historique et une expérience active avant toute écriture. Le choix initial reste éditorial ; ne déclarer aucun gagnant de performance avant des résultats accessibles.

Prépare l'action Studio pour vidéo associée, écran de fin ou test natif quand elle reste manuelle. Distingue miniature importée, couverture choisie, première image et lien interactif natif. Un remplacement séquentiel ne constitue pas un test randomisé. Ne modifie pas le packaging verrouillé par une expérience active.

Sorties : variantes locales liées au rendu et aux preuves, actions humaines explicites. Pour LinkedIn : vidéo, texte à copier, lien, date conseillée, embargo et fin de validité. `manual_ready` n'est pas une publication confirmée. Si le lien ou une affirmation manque de preuve, bloque le packaging concerné et conserve le média.
