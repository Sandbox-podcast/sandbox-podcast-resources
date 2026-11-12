---
name: sandbox-titres-youtube
description: Écrire les titres, le texte de miniature, la description, les chapitres et le commentaire épinglé d'une vidéo SANDBOX selon les règles mesurées sur 1 729 vidéos IA, puis préparer le test A/B dans YouTube Studio. À utiliser avant le tournage (titres provisoires) et après le montage (pack final).
---

# Titres et packaging YouTube SANDBOX

Pour un pack LinkedIn à publier à la main ou une revue croisée du rendu, utiliser `sandbox-packaging`. Cette skill couvre le titre YouTube, la description et le test A/B.

## Règles de titre

Chiffres de la veille du 12 novembre 2026 : part des vidéos qui font au moins 2 fois la médiane de leur chaîne, sur 1 729 vidéos longues de 45 chaînes IA. La base est 15 %.

| Règle | Avec | Sans |
|---|---:|---:|
| Pas de point d'interrogation | 5,9 % avec "?" | 16,2 % sans |
| Récit à la première personne ("J'ai", "On a") | 18,2 % | 14,8 % |
| Un chiffre | 17,3 % | 13,8 % |
| Pas de "tu" ou "vous" | 10,6 % avec | 15,8 % sans |
| Pas de "|" ni de deux-points | 12,9 % avec | 16,2 % sans |
| Moins de 40 caractères | 17,1 % | 10,3 % au-delà de 90 |

Ce sont des corrélations, pas des lois. Elles suffisent pour trancher entre deux titres.

1. Affirmer un fait ou un résultat. Pas de "Faut-il... ?", pas de "X : Y ?".
2. Moins de 55 caractères. Le nom connu (Claude, ChatGPT, Fable, Codex) ou le chiffre dans les 30 premiers.
3. Raconter ce qu'on a fait ou ce qui est arrivé à quelqu'un : "Il a laissé un agent IA gérer l'achat de son appartement".
4. Le numéro d'épisode et "SANDBOX" vont dans la description et la playlist, pas dans le titre.
5. Fort mais vrai. Chaque titre renvoie à un moment précis de la vidéo, avec son timecode. Pas de gain, de chiffre ou de verdict absent de l'épisode (vision SANDBOX : pas de titres trompeurs).

Formules qui marchent, avec leur source :

- Le récit : "Il a laissé l'IA gérer sa vie pendant 6 mois" (Underscore_, 836 k vues).
- L'expérience : "J'ai fait créer la même app à GPT-6 Astra et Fable 5.1" (Shubham SHARMA, x7,5).
- Le verdict : "Le vibecoding, c'est (déjà) fini." (Benjamin Code, x3).
- L'expérience poussée trop loin : "I Told Claude to "Make it better" 100 Times (It Went Too Far)" (Nate Herk, x5,7).

## Texte de miniature

Trois mots au plus. Il complète le titre et ne le répète pas. Exemple : titre "Il a laissé un agent IA acheter son appartement", miniature "Signé par l'IA".

## Livrer

Fichier `packaging.md` dans le dossier de l'épisode :

- 3 titres, chacun avec son angle et le timecode qui le prouve. Le premier est la recommandation.
- 3 textes de miniature, un par titre.
- Description : deux phrases qui reprennent la promesse du titre, puis les liens vérifiés, puis "SANDBOX #N" et les noms de Lou, Nicolas et Loïc. Chapitres mesurés sur le montage final.
- Commentaire épinglé : une question à laquelle on répond par une expérience ("Quel projet confierais-tu à un agent pendant une semaine ?").
- Plan du test : les 3 miniatures dans Tester et comparer de YouTube Studio, les titres en variantes si le test de titres est disponible.

## Relecture obligatoire

Passer chaque texte par la skill `humanizer`, puis `fasst-human-quality` : guillemets droits, aucun tiret cadratin, pas de points de suspension typographiques. Lancer son `projects/ligne-editoriale/scripts/verifier.py` sur `packaging.md` jusqu'à `OK`. Ne pas toucher aux noms de produits, liens et timecodes.

Ne pas publier ni programmer sans demande explicite.
