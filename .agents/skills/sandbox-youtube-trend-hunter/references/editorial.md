# Contrat de préparation éditoriale

Le moteur collecte des signaux et contrôle des références. Codex ou Claude Code rédige le scénario dans la conversation, avec l'abonnement existant. Aucun modèle facturé par API ne sert de solution de repli.

La préparation accepte un fichier JSON :

```json
{
  "research_dossier": "research-dossier.json",
  "angle": "Angle précis justifié par les sources",
  "titles": ["Titre A", "Titre B", "Titre C"],
  "description": "Description factuelle avec les sources primaires",
  "thumbnail": "Nom du produit, schéma original et texte court",
  "scenes": [
    {
      "role": "hook",
      "heading": "Titre de séquence",
      "narration": "Narration française sourcée",
      "on_screen": "Texte affiché",
      "visual": "Schéma original à produire localement",
      "statement_kind": "fact",
      "claim_ids": ["c1"]
    }
  ]
}
```

L'exemple montre une seule séquence pour expliquer les champs ; le fichier complet en contient 4 à 10. La première a le rôle `hook`, la dernière `conclusion`. Le script représente 120 à 300 secondes à 150 mots/minute, ou moins si la durée maximale configurée l'impose. Cette durée est une estimation avant la voix.

Chaque séquence relie ses faits à des affirmations confirmées. Les analyses et hypothèses portent leur nature ; aucune citation ne les transforme en faits. Les textes écran restent sous 140 caractères, les titres de séquence sous 70 et les titres YouTube sous 101. Les schémas générés reprennent le titre et le texte écran ; `visual` décrit l'intention à examiner et n'entraîne pas de génération d'images par IA.

Le dossier de recherche utilise le contrat existant de `youtube_growth.factory.research.verify` :

```json
{
  "version": 1,
  "sources": [
    {
      "source_id": "s1",
      "title": "Document primaire",
      "url": "https://example.org/document",
      "kind": "primary",
      "rights": "Texte archivé pour vérification ; aucune illustration réutilisée",
      "retrieved_at": "2026-10-29T10:00:00+00:00",
      "snapshot": "source.txt",
      "sha256": "empreinte SHA-256 du fichier source.txt"
    }
  ],
  "claims": [
    {
      "claim_id": "c1",
      "text": "Affirmation précise",
      "kind": "fact",
      "references": [{"source_id": "s1", "quote": "Extrait exact du texte archivé"}],
      "verification": {
        "status": "confirmed",
        "reviewer": "Codex, contrôle documentaire",
        "reason": "Ce que le document confirme et les limites de la vérification",
        "checked_at": "2026-10-29T10:05:00+00:00"
      }
    }
  ]
}
```

Remplace les valeurs d'exemple par la source effectivement lue. Utilise `fetch_sources` du module de recherche pour archiver une URL fournie, ou enregistre le texte obtenu par un outil de lecture autorisé et calcule son empreinte. Le contrôle vérifie la présence de la citation et la traçabilité du jugement, sans automatiser la vérité de l'affirmation. Identifie le réviseur réel ; une revue par agent ne constitue pas une approbation humaine.

Le pack conserve la copie des sources et leurs empreintes. Il produit `research.md`, `script.md`, `storyboard.json`, `titles.md`, `thumbnail.md`, `description.md`, `assets/`, `attributions.md`, `audio/` et `render/`. Une préparation sans scénario validé garde `research_required` et n'autorise ni voix ni rendu.
