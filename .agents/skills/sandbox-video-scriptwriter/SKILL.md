---
name: sandbox-video-scriptwriter
description: Écrire ou réécrire le texte prononcé d'une vidéo SANDBOX, de la fiche de recherche au texte prêt pour la voix, en appelant chaque skill d'écriture installé à son étape. Utiliser depuis l'onboarding vidéo pour les étapes recherche à révision orale, ou quand Lou demande de reprendre un script ; pour la voix, le montage et l'export, utiliser sandbox-storytelling-generator.
---

# Scénariste vidéo SANDBOX

Tu écris le texte que Lou prononcera, ou que sa voix clonée lira. L'onboarding vidéo garde l'état : réponses de cadrage, voix, étapes et contrôles. Travaille dans `.local/video-onboarding/SESSION/`, ignoré par Git, et enregistre chaque étape avec `video-onboarding record` (voir [sandbox-video-onboarding](../sandbox-video-onboarding/SKILL.md)).

## Avant d'écrire

1. Lire les règles apprises : [apprentissage.md](references/apprentissage.md) et `fasst-human-quality/references/apprentissage.md` dans les skills de Lou. Elles l'emportent sur les consignes des skills externes.
2. Lire le profil de voix, dans cet ordre : `references/prose.md` s'il existe, sinon `identity/VOICE.md` du skill `anti-slop-fr` de Lou. Sans aucun des deux, demander à Lou trois extraits où il parle seul et lancer l'étape « Guide de style » ci-dessous.
3. Lire le cadrage de la session (`video-onboarding show SESSION`). Le cadrage dit quoi écrire. Il ne se recopie jamais dans le texte : angle, objectif, budget, public et exclusions restent des consignes.

## L'ordre des skills

Charger chaque skill au moment de son étape, par son chemin dans `.agents/vendor/` (`python tools/repository/vendor_skills.py find NOM`). Les consignes sont en anglais ; le texte produit est en français.

| Étape de l'onboarding | Skill | Ce qu'il produit | Quand le sauter |
| --- | --- | --- | --- |
| Guide de style, une seule fois | `copywriting-prose-creator` | `references/prose.md` : vocabulaire, rythme, humour, tournures de Lou et mots qu'il refuse, tirés de ses transcriptions où il parle seul | Le guide existe déjà |
| Recherche | `content-research-writer` | Fiche préparatoire : faits vérifiés, source de chacun, limites, exemples utilisables. Pour un tuto, seulement des étapes réellement faites et vérifiées | Fiction sans contexte réel |
| Structure | `yt-script` | Cinq accroches d'après les formules de `hooks.json`, les deux meilleures présentées à Lou, puis la progression en séquences | Jamais |
| Texte intégral | `yt-script` | Le script séquence par séquence, chaque séquence avec `[À L'ÉCRAN : ...]`, durée estimée à 150 mots par minute | Jamais |
| Texte intégral, passages explicatifs | `animated-explainer-script` | Un mécanisme expliqué concept par concept, jargon expliqué aussitôt, un visuel par passage | Aucun mécanisme à expliquer |
| Adaptation au narrateur | `narrator-voice-adapter` | Le texte reformulé là où Lou dirait « je ne formulerais jamais ça comme ça », réserves, attributions et degrés de certitude conservés | Le texte sonne déjà comme Lou |
| Révision du français | `humanizer-fr` | Une seule passe de nettoyage des tournures artificielles, avec le profil de voix comme échantillon. Garder apostrophes `'` et guillemets `"` droits : ignorer son paragraphe 21 sur les guillemets français | Jamais |
| Révision du français, contrôle | `no-ai-slop`, `anti-slop-fr`, `writing-unslop` en mode détection, puis `scripts/verifier.py` de `fasst-human-quality` | Liste des motifs restants, corrigés à la main sans seconde réécriture complète | Jamais |
| Révision pour l'oral | `teleprompter-script-writer`, `spoken-check` de la factory, [revision-orale.md](../sandbox-video-onboarding/references/revision-orale.md) | Nombres en toutes lettres, respirations, prononciations, intentions de jeu | Jamais |
| Storyboard | `animated-explainer-script` (indications visuelles), `b-roll-shot-list` | Plans reliés aux répliques, médias et droits | Pas d'image à préparer |

Un seul correcteur réécrit le texte : `humanizer-fr`. Les autres outils anti-IA signalent seulement. `yt-script` prévoit un score d'accroche (`hookscore.py`) : il n'est pas installé et ses motifs sont anglais ; comparer les accroches aux formules à la main.

## Validations de Lou

- Après la structure : montrer les deux meilleures accroches et la progression. Attendre son choix.
- Après la révision orale : montrer le texte complet et finir par la question « Je le garde ou je le change ? ». Le storyboard attend sa réponse.
- Un contrôle humain n'est enregistré qu'avec les mots de Lou.

## Interdits

- Inventer un chiffre, un résultat, une source ou une expérience de Lou. Un fait absent de la fiche donne une question à Lou.
- Faire dire au narrateur les consignes de cadrage.
- Un plan annoncé ou des étapes numérotées à voix haute : la progression passe par ce qu'on montre.
- Une phrase sans fait ni image.
- Publier, générer une voix ou une image : cet agent écrit, la production passe par `sandbox-storytelling-generator`.
