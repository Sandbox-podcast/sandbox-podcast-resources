# SANDBOX : diffusion intensive et objectif à six mois

Décision du 18 octobre 2026, à la demande de Lou. Décidée par l'agent sur délégation (PD-0003). Objectif de travail : 10 000 abonnés sur chacun des comptes YouTube, TikTok, Instagram et X au 18 avril 2027, conformément à l'ambition exprimée précédemment par réseau. C'est une cible, pas une prévision garantie. Budget publicitaire : zéro.

## Sommaire

- [Ce que montre Silicon Carne](#ce-que-montre-silicon-carne)
- [Cadence retenue](#cadence-retenue)
- [Découpage de l'épisode 2](#découpage-de-lépisode-2)
- [Distribution et acquisition](#distribution-et-acquisition)
- [Mesure et décisions](#mesure-et-décisions)
- [Exécution et dépendances](#exécution-et-dépendances)

## Ce que montre Silicon Carne

Audit public du 18 octobre 2026. Échantillon limité : page des vidéos YouTube, grille Shorts, 12 premières publications Instagram et trois pages de Reels, profil et un extrait TikTok, cinq publications X visibles. Les métriques privées, la conversion en abonnés et les résultats d'expériences ne sont pas accessibles. Une concomitance entre format et vues ne prouve pas une causalité.

| Réseau    | Observation vérifiée                                                                                                                                                                                                                                                                                       | Application SANDBOX                                                                                                                                                          |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| YouTube   | La chaîne affiche environ 99,9 k abonnés. Les cinq vidéos les plus récentes portent les âges relatifs de 1 à 5 jours; quatre sujets de 34 à 40 minutes et un Afterwork de 1 h 45. L'annonce du 1er septembre prévoit un sujet par vidéo, quotidien en semaine, et conserve les entretiens longs.           | Garder l'émission hebdomadaire et proposer ensuite 2 à 3 chapitres autonomes de 8 à 20 minutes si le contenu le justifie. Ne pas lancer une nouvelle production quotidienne. |
| Shorts    | La grille reprend des séries de trois angles autour de l'école, du SaaS et des mathématiques. Les dates ne sont pas affichées dans cette grille : fréquence quotidienne non mesurée.                                                                                                                       | Plusieurs angles par séquence, chacun compréhensible isolément.                                                                                                              |
| Instagram | Environ 81 074 abonnés et 1 014 publications. Trois Reels sur l'école datés du 16 octobre à 06:02, 08:01 et 10:03 UTC, soit 08:02, 10:01 et 12:03 à Paris. L'échantillon prouve au moins trois Reels ce jour-là, pas trois tous les jours. Les légendes développent l'idée et renvoient à YouTube/podcast. | Trois Reels/jour au démarrage, légendes utiles et série identifiable.                                                                                                        |
| TikTok    | Environ 51,9 k abonnés. Les trois premiers angles sur l'école correspondent à ceux d'Instagram, avec des textes plus courts. Un extrait dure 39 secondes. Dates relatives seulement : cadence exacte non établie.                                                                                          | Adapter les premières lignes au réseau et ouvrir directement sur le problème du métier.                                                                                      |
| X         | Environ 11,9 k abonnés. Cinq posts visibles datés du 16 octobre : une longue vidéo épinglée, deux extraits de 39/40 secondes, une citation commentée et un texte court. C'est un minimum journalier observé, pas une moyenne.                                                                              | Combiner extraits et discussion; ne pas réduire X à des liens YouTube.                                                                                                       |

Sources primaires : [annonce éditoriale](https://siliconcarne.substack.com/p/silicon-carne-cest-maintenant-tous), [vidéos YouTube](https://www.youtube.com/@siliconcarnepod/videos), [Shorts](https://www.youtube.com/@siliconcarnepod/shorts), [Instagram](https://www.instagram.com/siliconcarne_/), Reels [06:02 UTC](https://www.instagram.com/siliconcarne_/reel/Dei1zBxitOf/), [08:01 UTC](https://www.instagram.com/siliconcarne_/reel/DejDkiVClr-/), [10:03 UTC](https://www.instagram.com/siliconcarne_/reel/DejRYbHAtd4/), [TikTok](https://www.tiktok.com/@siliconcarne_), [extrait de 39 secondes](https://www.tiktok.com/@siliconcarne_/video/7697203684249177376), [X](https://x.com/siliconcarnesf), [émission épinglée](https://x.com/siliconcarnesf/status/2111126901121028138), [extrait](https://x.com/siliconcarnesf/status/2111034712634400911).

Le mécanisme à reprendre : sujet précis, plusieurs entrées éditoriales, adaptation des légendes, émission de référence, identité constante et rendez-vous récurrent. Les accroches du concurrent restent des affirmations du concurrent; elles ne deviennent pas des faits validés ni des scripts SANDBOX.

## Cadence retenue

Mise à jour après production de l'épisode 2 : le premier lot comprend 30 extraits réels. Le 18 octobre, Lou précise que le prochain épisode devrait sortir le 25 octobre : tous les Shorts d'E02 doivent donc être diffusés au plus tard le 24, puis les nouveaux Shorts d'E03 commencent entre le 25 octobre et le 1er novembre. Comme la file E02 contient 30 sorties par réseau, la proposition de rattrapage répartit chaque série sur six jours, soit cinq sorties par jour et par réseau du 19 au 24 octobre. Les créneaux précis sont dans `exports/reseaux-sociaux/episode-02/replanification-proposee.json`.

Cette proposition n'a pas encore remplacé les réservations natives : l'état enregistré dans `publication-queue.json` dépasse encore le 24 octobre, et certaines lignes sont en cours de traitement ou à vérifier. Il faut réconcilier chaque état natif avant de déplacer les publications pour éviter les doublons. Une publication par agent local est distinguée d'une programmation native. Ce test de fréquence ne constitue pas une recommandation chiffrée officielle : [Meta propose des conseils personnalisés dans Best Practices](https://about.fb.com/news/2024/10/best-practices-education-hub-creators-instagram/).

La proposition à cinq sorties par jour concerne uniquement le lot E02 et sa fenêtre raccourcie. Pour E03, la fenêtre de diffusion commence le 25 octobre et se termine le 1er novembre; le nombre de clips et la cadence par réseau dépendront des extraits validés. Le tableau ci-dessous reste l'hypothèse générale de départ pour les contenus suivants, pas le calendrier natif confirmé d'E02. Essai de 14 jours à partir du premier lot validé. Les heures sont des hypothèses de test en Europe/Paris, pas des horaires prétendument optimisés. Calculer les dates avec ce fuseau, notamment lors du changement d'heure du 25 octobre.

| Réseau          | Volume de départ                  | Créneaux locaux            | Total hebdomadaire   |
| --------------- | --------------------------------- | -------------------------- | -------------------- |
| YouTube Shorts  | 4/jour                            | 09:00, 12:30, 17:30, 20:30 | 28                   |
| TikTok          | 4/jour                            | 09:30, 13:00, 18:00, 21:00 | 28                   |
| Instagram Reels | 3/jour                            | 10:00, 14:00, 19:00        | 21                   |
| X               | 2 extraits + 1 post original/jour | 10:30, 15:00, 19:30        | 14 vidéos + 7 textes |

Un même extrait peut servir plusieurs plateformes; il ne compte qu'une fois dans la production. Trente extraits validés alimentent 28 sorties hebdomadaires sur YouTube/TikTok et deux réserves. Instagram sélectionne 21 de ces extraits; X en sélectionne 14. Ne pas ajouter la cadence prévue aux posts déjà programmés : vérifier la file et remplacer un créneau disponible dans le plan. Ne jamais republier un fichier identique sur le même compte pour remplir un trou.

Alterner métiers, actualité et débat. Publier les actualités encore pertinentes dans les 72 premières heures; les cas d'usage durables peuvent attendre. Les deux réserves couvrent les contrôles échoués ou l'épisode suivant en retard. À chaque nouvel épisode, réévaluer les invendus; ne pas empiler neuf Reels de plus par semaine dans une file sans fin.

## Découpage de l'épisode 2

Lou annonce deux heures de vidéo, des cas d'usage par métier dont la restauration, une séquence de clash et de l'actualité. Upload en cours : aucun timecode ni extrait produit n'est confirmé.

Objectif de sélection : environ 40 candidats pour retenir jusqu'à 30 bons extraits. Répartition initiale indicative : 15 cas d'usage, 8 débats, 7 actualités. Réallouer selon la matière réelle. Trente est une cible de production, jamais une obligation de découper artificiellement.

- **Métiers** : un problème concret, le cas présenté, ce que fait l'IA et ce que la personne doit vérifier. Un métier ne devient plusieurs clips que si les usages sont distincts. Nommer le métier dans le titre et les premiers mots. Ne pas transformer une proposition en résultat client mesuré.
- **Clash** : conserver la thèse, l'objection et assez de réponse pour comprendre le désaccord. Une réaction isolée n'est pas un argument. Pas de fausse citation, de montage inversant une position ou de titre accusatoire ajouté.
- **Actualités** : un fait, sa date, sa source et une conséquence. Vérifier si l'information a évolué avant diffusion; distinguer commentaire, hypothèse et annonce confirmée.

Durée indicative 25 à 65 secondes; prolonger si la nuance l'exige. Entrée directe, pas de générique en ouverture. Cadrage vertical contrôlé sur les visages et les démos : si une capture devient illisible, conserver son contexte dans une composition adaptée. Sous-titres corrigés à l'écoute, noms et chiffres vérifiés, logo officiel discret. Un seul appel à l'action, lié à la série : prochain métier, réponse au débat ou épisode complet.

Chaque candidat reçoit : identifiant stable `E02-001`, URL source, début/fin, verbatim, catégorie, métier éventuel, accroche, contexte à préserver, sources factuelles, fichier, contrôle audio/visuel, statut par plateforme, date proposée puis date confirmée et URL publique. Avant réception du média, les champs source/timecode restent vides et le statut `waiting_source`.

## Distribution et acquisition

1. Relier chaque Short YouTube à l'épisode réel par la vidéo associée quand l'option est disponible. Organiser les séries métiers, débats et actualités; titres autonomes plutôt que « extrait numéro 12 ».
2. Adapter les couvertures et textes à chaque réseau, sans watermark d'une plateforme concurrente. Sur Instagram, compléter le lien externe via l'application mobile, puis sélectionner trois publications d'accueil à partir des résultats.
3. Répondre aux vrais commentaires avec une information utile; transformer les questions récurrentes en prochain extrait ou démonstration. Pas de quota de commentaires ni de lien collé partout.
4. Préparer chaque semaine cinq propositions de collaboration pertinentes : professionnels des métiers traités, créateurs IA appliquée, intervenants et communautés. Fournir un angle et un extrait précis. L'envoi de messages privés reste une action séparée nécessitant une instruction explicite; la carte blanche de croissance ne déclenche pas une campagne de messages.
5. Préparer pour Lou, Nico et Loïc un kit hebdomadaire : trois extraits adaptés à leurs audiences, texte personnel à ajuster et lien de l'épisode. Ne pas écrire sur leurs comptes personnels sans accès et autorisation dédiés.
6. Produire deux carrousels pratiques par semaine à partir de cas réellement présentés, et des stories de question/réponse quand une matière existe. Leur création ne doit pas empêcher la validation des vidéos prioritaires.
7. Au mois 2, transformer les séries qui convertissent en abonnés en rendez-vous fixes. Aux mois 3 à 6, privilégier ces séries et les collaborations réellement réalisées; poursuivre les expériences sur une minorité du volume.

## Mesure et décisions

Depuis zéro, 10 000 abonnés en environ 26 semaines demandent environ 385 abonnés nets/semaine, ou 55/jour, **par compte**. Recalculer avec le point de départ réel. Ne pas additionner les quatre audiences pour déclarer l'objectif atteint.

À titre de scénarios arithmétiques, et non de benchmarks : avec 0,1 %, 0,3 % ou 1 % de conversion vues → abonnements, obtenir 10 000 abonnements bruts demanderait respectivement 10 millions, 3,33 millions ou 1 million de vues par compte. Désabonnements et vues répétées peuvent modifier le besoin réel. N'attribuer les abonnements à une vidéo que si les statistiques natives le permettent.

Relever à 48 h et 7 jours : vues/portée, durée moyenne, complétion ou rétention disponible, partages, sauvegardes, visites de profil, abonnements attribués, abonnés nets du compte. Sources et fenêtres obligatoires; valeur absente = indisponible. Comparer séparément les réseaux et catégories.

À J7, corriger les problèmes de distribution, sous-titres et compréhension. À J14, comparer les cohortes à âge égal : abonnés nets hebdomadaires, médiane des abonnements pour 1 000 vues lorsque disponible, portée totale et temps de production. Si les données sont trop rares, prolonger le test sans décréter une fréquence gagnante. Une baisse du nombre de vues par clip ne suffit pas, à elle seule, à réduire la cadence.

Maintenir 4/4/3 si la qualité et le volume d'abonnements progressent. Tester Instagram à 4/jour seulement avec stock validé et signal encourageant. Si les contrôles prennent du retard ou si deux cohortes comparables se dégradent à la fois en acquisition totale et conversion, réduire d'un créneau sur le réseau concerné et tester l'accroche ou l'angle. Ces règles guident une décision, elles ne prouvent pas un effet causal.

## Exécution et dépendances

Le présent document et le README changent la consigne éditoriale de l'agent. Ils ne programment pas des vidéos dans les plateformes. Les quatre programmations X d'E1 restent celles vérifiées le 18 octobre; ne pas les effacer.

Dès le signal de Lou : vérifier l'URL E2, le traitement YouTube, l'accès au fichier source ou à une copie officielle du propriétaire, et la transcription. La disponibilité sur YouTube ne fournit pas automatiquement un master exploitable par l'API. Réutiliser le pipeline existant et son journal; ne pas créer une nouvelle base SQLite ou un second ordonnanceur.

Ensuite : sélectionner les passages réels, rendre par lots, écouter et regarder les rendus, préparer les métadonnées propres à chaque réseau, programmer les créneaux futurs disponibles, puis enregistrer les identifiants et preuves. En cas de résultat ambigu, vérifier l'existence du post avant tout nouvel envoi. Les droits, l'audio, le cadrage ou une donnée factuelle non vérifiés bloquent uniquement les clips concernés.

Les routines Codex existantes restent des contrôles locaux à 09:00 et le lundi à 09:30; aucune publication autonome permanente n'est activée par cette note. Pour les prochaines reprises, lire ce plan avant l'ancien calendrier. Le passage à une exécution distante durable exige les connexions officielles et une reprise vérifiée. Aucune dépense, nouveau compte, commit ou push réalisé dans ce lot.
