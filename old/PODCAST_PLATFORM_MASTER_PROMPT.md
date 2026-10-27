# PROMPT MAÎTRE — PLATEFORME WEB AI-NATIVE DE PRODUCTION DE PODCASTS VIDÉO

> **Document unique à fournir à l’agent de développement dans Codex, Claude Code, Cursor ou tout autre harnais de développement agentique.**  
> Ce document décrit la vision produit, les règles de décision, les exigences fonctionnelles, l’architecture attendue, la Podcast Factory, les critères d’acceptation, la stratégie de tests, la sécurité, les performances, la CI/CD et les livrables.

---

## Sommaire

1. Règle absolue de clarification par QCM  
2. Mission et vision produit  
3. Rôle attendu de l’agent  
4. Principes directeurs  
5. Utilisateurs, rôles et permissions  
6. Architecture UX : PREP, STUDIO et POST  
7. Studio virtuel commun  
8. Scene Engine et composition vidéo  
9. Normalisation des caméras et auto-framing  
10. Audio  
11. Active Speaker et Auto Director  
12. Régie live  
13. Collaboration temps réel  
14. Présentations HTML collaboratives  
15. Podcast Factory, Episode Factory et Asset Factory  
16. Product Design System et Broadcast Design System  
17. Enregistrement local multipiste et synchronisation  
18. Résilience et reprise après incident  
19. Transcription, post-production et Clip Factory  
20. Architecture technique générale  
21. Media Plane, Control Plane, WebRTC et SFU  
22. Modèle d’état temps réel et commandes critiques  
23. API, événements, jobs et workers  
24. Stockage, fichiers, versions et cycle de vie  
25. Modèle de données  
26. IA, MCP et gouvernance des modèles  
27. Sécurité, confidentialité et conformité  
28. Observabilité et diagnostic  
29. Performances, scalabilité et coûts  
30. Accessibilité, compatibilité et résilience UX  
31. Environnements, infrastructure et déploiement  
32. Stratégie de tests automatisés  
33. Critères d’acceptation testables  
34. Golden Path E2E  
35. CI/CD et Quality Gates à chaque push  
36. Documentation, ADR et instructions pour agents IA  
37. Workflow obligatoire de développement  
38. Proofs of Concept prioritaires  
39. Roadmap MVP, V2 et V3  
40. Definition of Done globale  
41. Livrables attendus avant le premier développement  
42. Instruction de démarrage de l’agent

---

# 0. RÈGLE ABSOLUE — TOUTE INFORMATION MANQUANTE DOIT ÊTRE DEMANDÉE SOUS FORME DE QCM

Cette règle est **prioritaire sur toutes les autres instructions de ce document**.

Tu ne dois jamais inventer silencieusement une décision lorsqu’une information manque, qu’une exigence est ambiguë ou que plusieurs options raisonnables peuvent produire des conséquences significativement différentes.

Cette règle s’applique notamment aux décisions qui ont un impact sur :

- le produit ;
- le périmètre fonctionnel ;
- les parcours utilisateurs ;
- l’UX/UI ;
- le design ;
- le modèle économique ;
- l’architecture ;
- la sécurité ;
- la confidentialité ;
- les performances ;
- les coûts ;
- l’infrastructure ;
- l’hébergement ;
- les données ;
- les médias ;
- les fournisseurs externes ;
- l’IA ;
- le MCP ;
- le stockage ;
- la rétention ;
- les rôles et permissions ;
- le live ;
- l’enregistrement ;
- la publication ;
- les navigateurs supportés ;
- la roadmap ;
- les critères de qualité.

## 0.1 Utiliser directement le mécanisme de question du harnais

Lorsque le harnais possède une fonction native permettant de poser une question à l’utilisateur, utilise-la en priorité :

- question interactive de Codex ;
- `AskUserQuestion` ou mécanisme équivalent dans Claude Code ;
- prompt interactif de Cursor ;
- question bloquante dans l’IDE ou l’agent utilisé ;
- tout autre mécanisme natif du harnais.

Ne cache jamais la question dans un fichier de logs, un commentaire de code ou une note que l’utilisateur ne verra pas.

Si le harnais ne possède aucun mécanisme interactif, affiche le QCM dans la conversation principale et arrête uniquement la partie du travail qui dépend de la réponse.

## 0.2 Format obligatoire du QCM

Ne pose pas une question ouverte et vague comme :

> Quel fournisseur souhaitez-vous utiliser ?

Présente un QCM décisionnel court, compréhensible et actionnable.

Format attendu :

```text
DÉCISION REQUISE 1/3 — Stockage des médias

Pourquoi cette décision est nécessaire :
Le choix influence les coûts, la stratégie d’upload, la reprise après coupure
et le niveau de dépendance à un fournisseur.

A — Stockage objet S3-compatible
Avantages : standard, portable, nombreux fournisseurs, facile à tester.
Inconvénients : pipeline vidéo et CDN à construire séparément.
Impacts : architecture modulaire, contrôle plus important, davantage d’intégration.

B — Plateforme vidéo managée
Avantages : traitement et diffusion intégrés, mise sur le marché plus rapide.
Inconvénients : coût supérieur, dépendance fournisseur, personnalisation limitée.
Impacts : moins d’infrastructure interne mais davantage de lock-in.

C — Stockage local pour le POC uniquement
Avantages : très simple pour valider les premiers flux.
Inconvénients : non adapté à la production ou au travail distribué.
Impacts : solution temporaire à remplacer après le POC.

RECOMMANDATION : A pour le produit cible, C seulement pour un POC jetable.

Répondre : A / B / C / AUTRE
```

## 0.3 Contenu obligatoire de chaque question

Chaque QCM doit contenir :

1. un identifiant ou numéro de question ;
2. le sujet précis ;
3. la raison pour laquelle la décision est nécessaire ;
4. deux à quatre options réalistes ;
5. les avantages de chaque option ;
6. les inconvénients de chaque option ;
7. les impacts structurants ;
8. ta recommandation argumentée ;
9. une réponse simple de type `A / B / C / AUTRE`.

## 0.4 Questions groupées

Lorsque plusieurs décisions indépendantes sont nécessaires, regroupe-les dans une série courte :

```text
QUESTION 1/4 — Hébergement
QUESTION 2/4 — Authentification
QUESTION 3/4 — Fournisseur SFU
QUESTION 4/4 — Politique de rétention
```

Ne présente pas vingt questions à la fois. Pose d’abord les questions qui bloquent l’architecture ou la prochaine étape de développement.

## 0.5 Questions bloquantes et non bloquantes

Classe les questions en deux catégories :

### BLOQUANTE

La réponse est nécessaire avant d’implémenter correctement la partie concernée.

Dans ce cas :

- pose le QCM ;
- n’implémente pas la décision à la place de l’utilisateur ;
- continue uniquement les travaux indépendants ;
- reprends la partie bloquée après la réponse.

### NON BLOQUANTE MAIS STRUCTURANTE

Une solution provisoire et réversible est possible.

Dans ce cas :

- pose le QCM au prochain point de décision ;
- indique éventuellement l’hypothèse temporaire ;
- isole cette hypothèse derrière une interface, une configuration ou un feature flag ;
- ne présente jamais l’hypothèse comme une décision validée.

## 0.6 Ne pas questionner inutilement

Ne pose pas de question lorsque :

- la réponse existe déjà dans le dépôt ;
- la réponse figure dans ce document ;
- une décision antérieure documentée répond au sujet ;
- une convention explicite existe ;
- la décision est purement interne, locale, facilement réversible et sans impact produit ;
- une bonne pratique incontestable peut être appliquée sans conséquence structurante.

Le principe est :

> **Autonomie maximale sur les décisions réversibles. Validation humaine obligatoire sur les décisions structurantes, coûteuses, ambiguës ou difficiles à inverser.**

## 0.7 Registre des décisions

Toute réponse structurante doit être enregistrée afin de ne pas reposer la même question.

Décisions d’architecture :

```text
/docs/adr/ADR-XXXX-titre.md
```

Décisions produit :

```text
/docs/product-decisions/PD-XXXX-titre.md
```

Décisions de design :

```text
/docs/design-decisions/DD-XXXX-titre.md
```

Chaque décision contient au minimum :

```text
Contexte
Question posée
Options présentées
Réponse retenue
Motifs
Conséquences
Date
Statut
```

---

# 1. MISSION

Conçois puis développe une **plateforme web professionnelle, collaborative, temps réel et AI-native de production de podcasts vidéo**.

L’objectif n’est pas de créer une simple application de visioconférence.

Nous voulons construire un **studio audiovisuel collaboratif complet**, accessible depuis un navigateur, qui permet à plusieurs personnes distantes de donner l’impression d’être physiquement présentes côte à côte dans un même studio.

La plateforme doit réunir dans un même produit :

- visioconférence ;
- studio virtuel commun ;
- suppression d’arrière-plan sans fond vert ;
- harmonisation des différentes webcams ;
- auto-framing ;
- régie live ;
- réalisation automatique ;
- enregistrement multipiste ;
- présentations HTML interactives ;
- partage de documents et d’assets ;
- collaboration temps réel ;
- préparation des épisodes ;
- design system produit ;
- broadcast design system ;
- Podcast Factory ;
- Episode Factory ;
- Asset Factory ;
- IA ;
- MCP ;
- transcription ;
- post-production ;
- génération et suggestion de clips ;
- automatisation ;
- industrialisation de la création des épisodes ;
- tests automatisés ;
- sécurité ;
- observabilité ;
- CI/CD ;
- suivi des performances ;
- documentation pour les humains et les agents IA.

Le cycle produit cible est :

```text
IDÉE
↓
RECHERCHE
↓
PRÉPARATION
↓
CRÉATION DE L’ÉPISODE
↓
GÉNÉRATION DE LA TRAME
↓
CRÉATION ET VALIDATION DES ASSETS
↓
RÉPÉTITION / DEVICE CHECK
↓
STUDIO
↓
ENREGISTREMENT
↓
RÉGIE LIVE
↓
POST-PRODUCTION
↓
CLIPS
↓
EXPORT
↓
PUBLICATION
↓
ARCHIVAGE
↓
RÉUTILISATION
```

Le produit sera généralement utilisé par **trois participants**, mais l’architecture ne doit pas être limitée artificiellement à trois personnes.

Le MVP doit viser au moins **cinq participants simultanés**, sous réserve de validation technique par benchmark.

---

# 2. OBJECTIFS PRODUIT

Le produit doit permettre de :

1. préparer un épisode de manière structurée ;
2. générer automatiquement son workspace à partir d’un template ;
3. collaborer en temps réel sur les notes, scènes, présentations et assets ;
4. rejoindre un studio vidéo depuis un navigateur ;
5. placer les participants dans un décor partagé ;
6. harmoniser visuellement les webcams ;
7. enregistrer chaque source séparément ;
8. piloter une régie manuelle ou automatique ;
9. afficher des présentations, images, vidéos et documents pendant la discussion ;
10. préserver le travail et les enregistrements malgré les problèmes réseau ;
11. reconstruire un replay exploitable ;
12. générer une transcription ;
13. suggérer et produire des clips ;
14. conserver tous les assets et livrables dans le workspace de l’épisode ;
15. permettre à une IA d’interagir avec la plateforme via MCP ;
16. industrialiser la création des futurs épisodes sans reconstruire manuellement la structure.

---

# 3. TON RÔLE

Agis comme une équipe pluridisciplinaire senior réunissant :

- CTO ;
- Software Architect ;
- Product Manager ;
- Product Designer ;
- UX/UI Designer ;
- Design System Lead ;
- Senior Full-Stack Engineer ;
- WebRTC Engineer ;
- Real-Time Systems Engineer ;
- Video Processing Engineer ;
- Audio Engineer ;
- Broadcast Engineer ;
- AI Engineer ;
- MCP / Agentic Systems Engineer ;
- DevOps Engineer ;
- Platform Engineer ;
- Cloud Architect ;
- Security Engineer ;
- QA Automation Engineer ;
- Performance Engineer ;
- SRE ;
- Data Engineer ;
- Video Editor ;
- Motion Designer ;
- Content Creator.

Tu ne dois pas simplement exécuter les idées littéralement.

Tu dois systématiquement :

1. analyser la demande ;
2. inspecter le dépôt et la documentation existante ;
3. identifier les informations manquantes ;
4. poser les QCM nécessaires ;
5. identifier les fonctionnalités implicites ;
6. challenger les hypothèses ;
7. comparer les solutions ;
8. identifier les risques ;
9. éviter la sur-ingénierie ;
10. éviter de réinventer des infrastructures complexes lorsqu’une brique fiable existe ;
11. concevoir pour la maintenabilité ;
12. concevoir pour la testabilité ;
13. concevoir pour la sécurité ;
14. concevoir pour la résilience ;
15. mesurer les performances ;
16. considérer les coûts ;
17. documenter les décisions ;
18. mettre à jour les tests et la documentation avec chaque modification.

Ne transforme jamais directement :

```text
IDÉE → CODE
```

Le workflow obligatoire est :

```text
BESOIN
↓
ANALYSE
↓
INSPECTION DE L’EXISTANT
↓
QUESTIONS BLOQUANTES EN QCM
↓
USER STORY
↓
CRITÈRES D’ACCEPTATION
↓
ARCHITECTURE
↓
RISQUES
↓
STRATÉGIE DE TEST
↓
IMPLÉMENTATION
↓
VALIDATION
↓
DOCUMENTATION
```

---

# 4. PRINCIPES DIRECTEURS

## 4.1 Simple pendant le live

Pendant l’enregistrement, les utilisateurs doivent se concentrer sur la conversation. Les actions critiques doivent être immédiatement accessibles et l’interface ne doit pas exposer une complexité technique inutile.

## 4.2 Puissant avant et après

Les espaces PREP et POST peuvent proposer davantage de fonctions, de réglages et d’outils avancés.

## 4.3 Non destructif

Toujours préserver les médias sources. Les corrections, crops, montages, suppressions, effets et exports doivent être représentés sous forme de décisions éditoriales ou de rendus dérivés.

## 4.4 Local-first pour les enregistrements lorsque pertinent

Une mauvaise connexion ne doit pas détruire un enregistrement local de qualité.

## 4.5 Collaborative-first

Les utilisateurs autorisés doivent partager un état cohérent et récupérer cet état après reconnexion.

## 4.6 AI-native

L’IA doit être intégrée à l’architecture, aux permissions, aux audits, aux tests et aux workflows.

## 4.7 Factory-driven

Les épisodes doivent être générés depuis des templates, manifests, composants, scènes et assets réutilisables.

## 4.8 Observable

Un problème média, réseau, sécurité ou backend doit pouvoir être diagnostiqué à partir de logs, métriques, traces et événements corrélés.

## 4.9 Recoverable

Toute opération critique doit avoir une stratégie explicite de récupération.

## 4.10 Secure by design

Les autorisations doivent être validées côté serveur. Le frontend ne constitue jamais une frontière de sécurité.

## 4.11 Idempotent lorsque pertinent

Une commande rejouée, un retry réseau ou un job relancé ne doit pas créer silencieusement des doublons ou corrompre l’état.

## 4.12 Mesurer plutôt que supposer

Les affirmations comme « rapide », « scalable », « stable », « sécurisé » ou « synchronisé » doivent être accompagnées d’une méthode de mesure et de critères testables.

---

# 5. UTILISATEURS, RÔLES ET PERMISSIONS

Prévoir au minimum les rôles suivants :

## ADMIN

- configuration du podcast ;
- gestion des membres ;
- gestion de la marque ;
- accès aux paramètres de sécurité ;
- gestion des intégrations ;
- droits complets.

## PRODUCER

- préparation du studio ;
- gestion du rundown ;
- contrôle de la régie ;
- lancement et arrêt de l’enregistrement ;
- gestion de Program et Preview.

## HOST

- animation du podcast ;
- accès aux notes et séquences ;
- possibilité de contrôler certaines scènes si autorisé.

## EDITOR

- préparation du contenu ;
- édition des présentations ;
- gestion des assets ;
- post-production ;
- clips et exports.

## GUEST

- accès par invitation ;
- device check ;
- participation au studio ;
- accès limité aux contenus nécessaires.

Une personne peut cumuler plusieurs rôles.

Implémenter un RBAC clair et prévoir une extension vers des permissions plus fines si nécessaire.

Toute permission ambiguë doit déclencher un QCM.

---

# 6. ARCHITECTURE UX : PREP, STUDIO ET POST

Séparer clairement l’application en trois espaces.

## 6.1 PREP

Fonctions principales :

- création d’un épisode ;
- choix du template ;
- brief ;
- recherche ;
- notes ;
- rundown ;
- quatre séquences ;
- scènes ;
- présentations ;
- assets ;
- jingles ;
- préparation des invités ;
- répétition ;
- device check ;
- validation avant live.

## 6.2 STUDIO

Fonctions principales :

- participants ;
- Program ;
- Preview ;
- scènes ;
- rundown ;
- régie ;
- active speaker ;
- Auto Director ;
- recording state ;
- niveaux audio ;
- état réseau ;
- état des uploads ;
- backchannel ou chat de production si validé par QCM.

## 6.3 POST

Fonctions principales :

- médias sources ;
- replay ;
- transcription ;
- montage multicam ;
- édition basée sur le texte ;
- chapitres ;
- clips ;
- sous-titres ;
- miniatures ;
- exports ;
- publication ;
- archivage.

Navigation conceptuelle :

```text
Podcast
├── Episodes
├── Templates
├── Assets
├── Brand
├── Studio
├── Clips
├── Exports
└── Settings
```

L’interface STUDIO doit être plus simple, plus stable et moins dense que PREP et POST.

---

# 7. STUDIO VIRTUEL COMMUN

Chaque participant active sa webcam.

L’application doit détourer automatiquement chaque personne afin de supprimer son arrière-plan sans fond vert physique.

Étudier notamment :

- segmentation humaine ;
- MediaPipe ou solution équivalente ;
- WebGPU ;
- WebAssembly ;
- modèles spécialisés ;
- accélération GPU ;
- fallback CPU ;
- traitement local ;
- degradation graceful sur machine faible.

Les personnes détourées doivent être intégrées dans une scène commune.

```text
┌──────────────────────────────────────────────┐
│                                              │
│               PODCAST STUDIO                 │
│                                              │
│      👤               👤              👤      │
│     HOST           SPEAKER 2       SPEAKER 3 │
│                                              │
│          overlays / logo / décor             │
└──────────────────────────────────────────────┘
```

Le résultat ne doit pas ressembler à trois rectangles de visioconférence accolés. Il doit donner l’impression d’une mise en scène cohérente.

Prévoir :

- layouts prédéfinis ;
- positions personnalisables ;
- safe zones ;
- contrôle du crop ;
- contrôle du scale ;
- ombres ou traitements légers si utiles ;
- désactivation du détourage ;
- fallback vers une vignette classique.

---

# 8. SCENE ENGINE ET COMPOSITION VIDÉO

Construire un moteur de scènes générique.

## 8.1 Types de layers

- `ParticipantLayer` ;
- `ImageLayer` ;
- `VideoLayer` ;
- `AudioLayer` ;
- `TextLayer` ;
- `ShapeLayer` ;
- `HTMLLayer` ;
- `PresentationLayer` ;
- `ScreenShareLayer` ;
- `BrowserLayer` ;
- `OverlayLayer` ;
- `CaptionLayer` ;
- `TimerLayer` si validé.

## 8.2 Propriétés communes

```text
id
type
name
x
y
width
height
scale
crop
rotation
opacity
zIndex
visible
locked
source
animation
transition
safeAreaBehavior
```

## 8.3 Capacités

Les scènes doivent être :

- créables ;
- sauvegardables ;
- prévisualisables ;
- duplicables ;
- ordonnables ;
- versionnables ;
- templatisables ;
- exportables/importables ;
- réutilisables entre épisodes ;
- associables à une séquence du rundown.

## 8.4 Séparation définition / rendu

Séparer :

```text
SCENE DEFINITION
```

de :

```text
SCENE RENDERER
```

La définition d’une scène doit rester indépendante du renderer afin de permettre :

- rendu dans le navigateur ;
- rendu serveur ;
- rendu d’un replay ;
- rendu d’un clip vertical ;
- migrations futures.

## 8.5 Modes de composition à comparer

Comparer au minimum :

- composition client-side ;
- composition serveur ;
- composition hybride ;
- enregistrement isolé des sources avec reconstruction ultérieure.

Cette décision est structurante et doit déclencher un QCM avant implémentation définitive.

---

# 9. NORMALISATION DES CAMÉRAS ET AUTO-FRAMING

## 9.1 Camera Matching

Les participants utiliseront des webcams, smartphones, ordinateurs et éclairages différents.

Créer une pipeline capable d’analyser et de corriger de manière raisonnable :

- exposition ;
- luminosité ;
- température de couleur ;
- balance des blancs ;
- contraste ;
- saturation ;
- gamma ;
- netteté ;
- réduction de bruit ;
- tonalité générale.

Créer éventuellement un profil :

```text
PODCAST LOOK
```

Les corrections doivent être :

- configurables ;
- désactivables ;
- non destructives ;
- évaluables par un protocole reproductible.

Ne pas appliquer de filtre beauté excessif.

## 9.2 Calibration avant session

Créer une étape de calibration :

```text
CAMÉRA LOU
✓ cadrage
✓ exposition
✓ lumière
✓ résolution

CAMÉRA 2
⚠ image trop sombre
→ correction automatique proposée
```

## 9.3 Auto-framing

Détecter :

- visage ;
- yeux ;
- épaules ;
- bounding box ;
- position du sujet.

Le système doit pouvoir compenser une personne trop proche, trop éloignée ou décentrée.

Le mouvement doit être interpolé et stable.

Une perte temporaire de détection ne doit pas produire de zoom erratique.

---

# 10. AUDIO

L’audio est prioritaire.

## 10.1 Fonctions

Prévoir :

- sélection du microphone ;
- monitoring ;
- vumètre ;
- test micro ;
- détection du clipping ;
- echo cancellation ;
- noise suppression ;
- automatic gain control configurable ;
- noise gate léger ;
- loudness analysis ;
- loudness normalization pour les rendus ;
- détection d’absence de signal ;
- avertissement en cas de mauvais périphérique.

## 10.2 Pipeline live et pipeline source

Séparer lorsque possible :

```text
MICROPHONE
↓
TRAITEMENT LIVE
↓
WEBRTC
```

et :

```text
MICROPHONE
↓
ENREGISTREMENT HAUTE QUALITÉ
↓
BUFFER LOCAL
↓
UPLOAD
```

Le traitement live ne doit pas empêcher de préserver une source utile à la post-production.

## 10.3 Device check

Afficher un état simple :

```text
MICROPHONE
████████████░░
GOOD
```

Prévenir avant l’entrée en studio si :

- le micro est silencieux ;
- le niveau est trop faible ;
- le niveau sature ;
- le navigateur n’a pas la permission ;
- le périphérique attendu a disparu.

---

# 11. ACTIVE SPEAKER ET AUTO DIRECTOR

## 11.1 Active Speaker Engine

Détecter le participant qui parle sans déclencher de changement à chaque bruit.

Prendre en compte :

- niveau audio ;
- durée de parole ;
- silence ;
- interruptions ;
- conversation croisée ;
- toux ;
- clic ;
- choc micro ;
- latence ;
- réactions ;
- plusieurs personnes parlant simultanément.

Utiliser notamment :

- seuils ;
- hysteresis ;
- durée minimale de parole ;
- cooldown ;
- durée minimale d’un plan ;
- règles éditoriales.

## 11.2 Auto Director

Modes envisagés :

```text
GROUP
SPEAKER_FOCUS
DUO
PRESENTATION
REACTION
MANUAL
```

Prévoir :

```text
AUTO DIRECTOR ON / OFF
```

La réalisation manuelle doit pouvoir reprendre la main immédiatement.

Le moteur doit conserver un journal des décisions de mise en scène :

```text
timestamp
decision
source
speakerId
sceneId
reason
confidence
```

Ces événements peuvent servir à reconstruire ou modifier le montage.

---

# 12. RÉGIE LIVE

Créer une régie inspirée du broadcasting professionnel, mais simplifiée.

Concept :

```text
PROGRAM
[ce que voit le spectateur ou ce qui est enregistré comme programme]

PREVIEW
[prochaine scène préparée]
```

Commandes :

```text
TAKE
CUT
TRANSITION
```

La régie doit permettre de lancer :

- scène ;
- image ;
- vidéo ;
- présentation ;
- document ;
- page web sécurisée ;
- graphique ;
- citation ;
- lower third ;
- jingle ;
- screen share ;
- overlay ;
- intro ;
- outro.

Une erreur en Preview ne doit jamais casser Program.

Prévoir :

- hotkeys si validées ;
- confirmations pour les actions dangereuses ;
- état de chargement d’un asset ;
- preloading ;
- fallback ;
- audit des commandes critiques ;
- permissions Producer.

---

# 13. COLLABORATION TEMPS RÉEL

Tous les participants autorisés doivent partager le même workspace.

Une modification effectuée par une personne doit apparaître chez les autres sans refresh.

Étudier :

- WebSockets ;
- CRDT ;
- Yjs ;
- optimistic updates ;
- event sourcing seulement lorsque justifié.

Prévoir :

- présence ;
- reconnexion ;
- modifications simultanées ;
- résolution de conflits ;
- autosave ;
- historique ;
- restauration de l’état courant ;
- indication des utilisateurs présents ;
- verrouillage optimiste ou explicite selon la ressource.

Ne pas utiliser un CRDT pour toutes les données par défaut. L’utiliser uniquement lorsque l’édition concurrente apporte une valeur réelle.

---

# 14. PRÉSENTATIONS HTML COLLABORATIVES

Les présentations peuvent être générées par une IA en HTML, CSS et JavaScript.

Créer une interface :

```text
CODE | PREVIEW
```

Les présentations doivent être :

- créables ;
- importables ;
- éditables ;
- prévisualisables ;
- versionnées ;
- collaboratives ;
- restaurables ;
- utilisables directement dans une scène ;
- modifiables via MCP ;
- synchronisées en temps réel.

Prévoir :

- autosave ;
- versions ;
- diff ;
- rollback ;
- sandbox ;
- validation ;
- preview isolée ;
- mode lecture seule ;
- statut brouillon/publié.

## 14.1 Isolation de sécurité

Étudier :

- `iframe sandbox` ;
- CSP restrictive ;
- origin séparée ;
- communication contrôlée via `postMessage` ;
- allowlist d’APIs ;
- blocage du réseau par défaut si nécessaire.

Le contenu utilisateur ne doit pas accéder librement :

- aux cookies ;
- aux tokens ;
- au DOM parent ;
- aux secrets ;
- aux APIs privées ;
- au stockage sensible ;
- au réseau interne.

---

# 15. PODCAST FACTORY, EPISODE FACTORY ET ASSET FACTORY

L’industrialisation de la création des épisodes est une brique centrale du produit.

## 15.1 Podcast Factory

La factory doit transformer :

```text
DEMANDE D’ÉPISODE
+
VERSION DU TEMPLATE
+
VERSION DE LA MARQUE
+
BIBLIOTHÈQUE D’ASSETS
+
PARAMÈTRES DE L’ÉPISODE
```

En :

```text
WORKSPACE D’ÉPISODE PRÊT À ÊTRE PRÉPARÉ
```

## 15.2 Structure canonique d’un épisode

```text
Episode
├── Brief
├── Rundown
├── Segments
├── Research
├── Script / Notes
├── Guests
├── Presentations
├── Scenes
├── Assets
├── Music
├── Jingles
├── Recordings
├── Audio Tracks
├── Video Tracks
├── Program Output
├── Transcript
├── Chapters
├── Clips
├── Thumbnails
├── Social
├── Exports
└── Audit / Diagnostics
```

## 15.3 Les quatre séquences

Template par défaut :

```text
01 INTRO
02 SÉQUENCE A
03 SÉQUENCE B
04 CONCLUSION
```

Les noms sont configurables.

Chaque séquence possède :

```text
id
title
objective
targetDuration
notes
questions
speakers
scenes
assets
presentation
transition
jingle
CTA
status
```

## 15.4 Génération automatique

La création d’un épisode doit pouvoir générer :

```text
✓ structure
✓ rundown
✓ quatre séquences
✓ scènes de base
✓ intro
✓ outro
✓ lower thirds
✓ transitions
✓ présentation modèle
✓ clip templates
✓ thumbnail template
✓ export presets
✓ checklists
✓ permissions initiales
```

## 15.5 Manifests et schémas

Prévoir des schémas versionnés, par exemple :

```text
podcast.config.yaml
episode-template.json
broadcast-theme.json
scene-template.json
asset-manifest.json
export-presets.json
```

Valider ces fichiers par JSON Schema, Zod ou mécanisme équivalent.

## 15.6 Générateur d’épisode

Prévoir une commande ou capacité équivalente :

```text
pnpm episode:create --template standard --title "Titre" --date 2026-10-05
```

ou une action UI/MCP reposant sur le même service métier.

La génération doit être :

- idempotente lorsque possible ;
- traçable ;
- testable ;
- versionnée ;
- indépendante du frontend.

## 15.7 Réutilisation sans duplication inutile

Les assets globaux doivent être référencés plutôt que copiés lorsque pertinent.

Un épisode doit pouvoir figer une version d’asset pour empêcher une modification globale de changer rétroactivement le rendu d’un ancien épisode.

---

# 16. PRODUCT DESIGN SYSTEM ET BROADCAST DESIGN SYSTEM

## 16.1 Product Design System

Créer un design system de l’application documentant :

- couleurs ;
- typographie ;
- espacements ;
- grilles ;
- bordures ;
- radius ;
- ombres ;
- icônes ;
- motion ;
- transitions ;
- layouts ;
- états ;
- accessibilité ;
- responsive behavior ;
- composants ;
- patterns d’interaction.

Créer des design tokens :

```text
color.brand.primary
color.surface.studio
color.text.primary
spacing.sm
spacing.md
spacing.lg
radius.panel
radius.button
motion.fast
motion.sceneTransition
```

Éviter les valeurs arbitraires dispersées.

Documenter les composants et leurs variantes, idéalement dans Storybook ou une solution équivalente après validation.

## 16.2 Broadcast Design System

Créer un système spécifique au rendu vidéo :

- backgrounds ;
- logos ;
- lower thirds ;
- noms des speakers ;
- intro ;
- outro ;
- transitions ;
- cadres de présentation ;
- graphiques ;
- citations ;
- alert boxes ;
- clip layouts ;
- sous-titres ;
- speaker focus ;
- split screens ;
- safe zones ;
- règles de lisibilité vidéo.

## 16.3 Asset Factory

Catégories :

```text
BRAND
BACKGROUNDS
OVERLAYS
LOWER_THIRDS
TRANSITIONS
INTROS
OUTROS
JINGLES
MUSIC
ICONS
ILLUSTRATIONS
PRESENTATIONS
THUMBNAILS
CLIP_TEMPLATES
SUBTITLE_STYLES
```

Chaque asset doit posséder au minimum :

```text
id
type
name
version
status
tags
width
height
duration
format
checksum
usage
createdAt
updatedAt
createdBy
```

Créer des instructions précises permettant à un humain ou une IA de générer un nouvel asset conforme.

## 16.4 Versioning

Exemple :

```text
Podcast Template v3
Broadcast Theme v2
Intro v4
Lower Third v6
```

Un ancien épisode doit continuer à utiliser la version avec laquelle il a été créé.

---

# 17. ENREGISTREMENT LOCAL MULTIPISTE ET SYNCHRONISATION

Ne jamais dépendre uniquement de l’enregistrement du Program Output.

Chaque participant doit idéalement produire :

```text
participant_video_original
participant_audio_original
```

Conserver également :

```text
program_output
```

## 17.1 Double pipeline

Pipeline live :

```text
CAMÉRA / MICRO
↓
CAPTURE
↓
TRAITEMENT LIVE OPTIONNEL
↓
ENCODAGE BASSE LATENCE
↓
WEBRTC
```

Pipeline d’enregistrement :

```text
CAMÉRA / MICRO
↓
ENREGISTREMENT LOCAL HAUTE QUALITÉ
↓
CHUNKS
↓
BUFFER LOCAL
↓
UPLOAD PROGRESSIF
↓
STOCKAGE OBJET
↓
VÉRIFICATION
↓
RECONSTRUCTION
```

## 17.2 Chunks

Chaque chunk doit disposer de métadonnées :

```text
recordingSessionId
participantId
trackId
sequenceNumber
startTimestamp
endTimestamp
duration
codec
container
size
checksum
uploadStatus
```

## 17.3 Reprise d’upload

Prévoir :

- upload multipart ou équivalent ;
- retries ;
- reprise après coupure ;
- déduplication ;
- checksum ;
- confirmation serveur ;
- état local persistant si autorisé par le navigateur ;
- nettoyage contrôlé après confirmation.

## 17.4 Synchronisation

Toutes les pistes doivent être synchronisables à l’aide de :

- timestamps ;
- timecodes ;
- horloge de session ;
- métadonnées ;
- événements start/stop ;
- points de resynchronisation ;
- correction de drift si nécessaire.

Après reconstruction, les pistes doivent être exploitables pour un montage multicam.

La stratégie d’horloge et de synchronisation doit être documentée et testée.

---

# 18. RÉSILIENCE ET REPRISE APRÈS INCIDENT

Prévoir explicitement :

- browser crash ;
- network loss ;
- reconnexion ;
- ICE restart ;
- server restart ;
- WebSocket loss ;
- SFU disconnect ;
- upload interrompu ;
- participant qui quitte ;
- participant qui revient ;
- refresh accidentel ;
- fermeture d’onglet ;
- changement de périphérique ;
- worker qui échoue ;
- export interrompu.

Afficher des états honnêtes :

```text
● RECORDING
● LOCAL RECORDING SAFE
● CLOUD SYNC IN PROGRESS
● 3 PARTICIPANTS CONNECTED
```

Ne jamais afficher `SAFE` si le système ne peut pas le démontrer.

Définir les états possibles :

```text
SAFE
UPLOADING
RECOVERABLE
AT_RISK
MISSING
FAILED
```

Créer des procédures de récupération et des tests automatisés ou semi-automatisés pour chaque incident critique.

---

# 19. TRANSCRIPTION, POST-PRODUCTION ET CLIP FACTORY

## 19.1 Transcription

Chaque segment doit contenir :

```text
speakerId
speakerLabel
startTime
endTime
text
confidence
language
```

Exemple :

```text
00:12:42 LOU
Les agents IA vont probablement…

00:12:48 SPEAKER 2
Justement, je ne suis pas totalement…
```

La transcription doit permettre :

- recherche ;
- navigation ;
- chapitrage ;
- résumé ;
- correction manuelle ;
- réassignation du speaker ;
- clipping ;
- montage textuel.

## 19.2 Post-production

Prévoir progressivement :

- cuts multicam ;
- suppression de silences ;
- détection d’hésitations ;
- normalisation audio ;
- chapitres ;
- transitions ;
- intro ;
- outro ;
- jingles ;
- sous-titres ;
- correction colorimétrique ;
- exports.

Toutes les décisions doivent rester non destructives.

## 19.3 Text-based editing

Une suppression dans le transcript doit créer une décision de montage proposée, pas détruire la source.

## 19.4 Clip Factory

Analyser l’épisode pour identifier :

- punchlines ;
- débats ;
- désaccords ;
- révélations ;
- explications ;
- moments humoristiques ;
- hooks ;
- moments pédagogiques ;
- citations fortes.

Chaque suggestion contient :

```text
startTime
endTime
title
hook
reason
score
speakerIds
platformHints
```

Le score constitue une aide éditoriale, jamais une garantie de viralité.

## 19.5 Auto-reframing

Créer des rendus :

```text
16:9
9:16
1:1
```

Prévoir :

- face tracking ;
- dynamic crop ;
- gestion de plusieurs visages ;
- sous-titres ;
- titre ;
- branding ;
- speaker name ;
- safe zones ;
- preview ;
- correction manuelle.

---
# 20. ARCHITECTURE TECHNIQUE GÉNÉRALE

Concevoir une architecture moderne, mais éviter la complexité distribuée prématurée.

Comparer un monolithe modulaire bien structuré à une architecture de services. Ne créer des services séparés que lorsqu’une frontière technique, de sécurité, de charge ou de cycle de vie le justifie.

Architecture conceptuelle :

```text
WEB APPLICATION
├── PREP UI
├── STUDIO UI
├── POST UI
└── ADMIN UI

APPLICATION BACKEND
├── Authentication / Authorization
├── Podcast / Episode Domain
├── Factory Services
├── Scene / Rundown Domain
├── Collaboration Gateway
├── Recording Control
├── Asset Service
├── Export Service
├── AI Orchestration
└── MCP Server

MEDIA INFRASTRUCTURE
├── SFU / WebRTC
├── STUN / TURN
├── Local Recording Upload
├── Media Workers
├── FFmpeg Pipeline
└── CDN / Delivery

DATA INFRASTRUCTURE
├── Relational Database
├── Realtime / Cache if justified
├── Object Storage
├── Job Queue
├── Search if justified
└── Observability
```

## 20.1 Stack à évaluer

Frontend :

- Next.js ;
- React ;
- TypeScript ;
- gestion d’état adaptée ;
- composants accessibles ;
- Web Workers lorsque pertinent.

Backend :

- Node.js / TypeScript ou autre choix justifié ;
- PostgreSQL ;
- Redis seulement si nécessaire ;
- stockage objet S3-compatible ;
- workers ;
- queue de jobs ;
- FFmpeg.

Realtime et médias :

- WebRTC ;
- SFU ;
- WebSocket ;
- WebTransport lorsque pertinent ;
- Yjs ou CRDT seulement pour les documents collaboratifs ;
- Canvas, WebGL ou WebGPU pour le rendu local si pertinent.

Infrastructure :

- Docker ;
- Infrastructure as Code ;
- CDN ;
- observabilité ;
- CI/CD ;
- preview environments.

Chaque choix structurant doit être justifié et, s’il n’est pas déjà décidé, faire l’objet d’un QCM.

## 20.2 Build vs Buy

Pour chaque brique complexe, comparer :

```text
BUILD
vs
OPEN SOURCE
vs
MANAGED SERVICE
```

Au minimum pour :

- SFU ;
- TURN ;
- authentification ;
- stockage ;
- transcription ;
- background removal ;
- vidéo processing ;
- observabilité ;
- CDN ;
- envoi d’emails ;
- modération éventuelle.

Comparer :

- coût ;
- time-to-market ;
- lock-in ;
- maturité ;
- sécurité ;
- performances ;
- scalabilité ;
- maintenabilité ;
- capacité à tester localement.

---

# 21. MEDIA PLANE, CONTROL PLANE, WEBRTC ET SFU

Séparer strictement :

```text
MEDIA PLANE
```

et :

```text
CONTROL PLANE
```

## 21.1 Media Plane

Responsable de :

- audio ;
- vidéo ;
- screen share ;
- track publication ;
- track subscription ;
- bitrate adaptation ;
- éventuellement Program Output live.

## 21.2 Control Plane

Responsable de :

- authentification ;
- autorisation ;
- présence ;
- scène active ;
- Preview ;
- Program ;
- rundown ;
- collaboration ;
- recording state ;
- commandes ;
- statuts ;
- synchronisation de l’UI ;
- audit.

Une panne du control plane ne doit pas détruire les médias déjà enregistrés localement.

## 21.3 Mesh, SFU et MCU

Comparer :

- WebRTC Mesh ;
- SFU ;
- MCU.

Pour chaque option, analyser :

- latence ;
- upload participant ;
- download participant ;
- coût serveur ;
- complexité ;
- scalabilité ;
- qualité ;
- enregistrement ;
- observabilité ;
- compatibilité mobile future.

Pour trois à cinq participants avec une ambition d’évolution, considérer sérieusement une architecture SFU.

Ne pas construire un SFU maison sans justification exceptionnelle.

## 21.4 Signaling

Définir explicitement le protocole de signaling et les événements :

- join ;
- leave ;
- reconnect ;
- heartbeat ;
- ICE restart ;
- publish track ;
- unpublish track ;
- subscribe ;
- unsubscribe ;
- mute ;
- unmute ;
- camera state ;
- screen share ;
- permission changed ;
- device changed ;
- quality warning.

Utiliser des identifiants stables :

```text
sessionId
participantId
connectionId
trackId
recordingSessionId
```

`participantId` doit survivre à une reconnexion lorsque l’identité du participant est la même.

## 21.5 NAT traversal

Prévoir :

- STUN ;
- TURN ;
- ICE ;
- TURN fallback ;
- ICE restart ;
- collecte des candidats et métriques utiles.

Tester :

- réseau d’entreprise ;
- Wi-Fi public ;
- CGNAT ;
- firewall restrictif ;
- réseau mobile si supporté.

## 21.6 Simulcast, SVC et adaptation

Évaluer :

- simulcast ;
- SVC ;
- adaptive bitrate ;
- selective subscription ;
- dynacast ou mécanisme équivalent ;
- pause des tracks invisibles ;
- choix de la résolution selon le layout.

## 21.7 Codecs et compatibilité

Le choix des codecs audio/vidéo et containers est structurant.

Avant de le figer :

- analyser les navigateurs cibles ;
- analyser les besoins d’enregistrement ;
- analyser les coûts de transcodage ;
- poser un QCM si les cibles ne sont pas définies ;
- documenter la matrice de compatibilité.

## 21.8 WebRTC stats

Collecter au minimum lorsque disponible :

- bitrate ;
- packets sent/received ;
- packets lost ;
- jitter ;
- RTT ;
- frame rate ;
- resolution ;
- frames dropped ;
- freeze count ;
- codec ;
- candidate pair ;
- relay usage ;
- quality limitation reason.

---

# 22. MODÈLE D’ÉTAT TEMPS RÉEL ET COMMANDES CRITIQUES

## 22.1 Classer chaque donnée

Toute donnée doit être classée :

```text
LOCAL
EPHEMERAL
PERSISTENT
COLLABORATIVE
AUTHORITATIVE
DERIVED
```

Exemples :

```text
survol d’un bouton → LOCAL
présence participant → EPHEMERAL COLLABORATIVE
nom épisode → PERSISTENT COLLABORATIVE
scène Program → AUTHORITATIVE REALTIME
buffer d’enregistrement → LOCAL CRITICAL
niveau audio instantané → EPHEMERAL DERIVED
```

Ne pas synchroniser l’intégralité de l’état frontend.

## 22.2 Autorité de l’état

Définir une source de vérité pour :

- présence ;
- Program ;
- Preview ;
- recording state ;
- rundown courant ;
- versions ;
- permissions ;
- état des uploads ;
- état des jobs.

Les commandes critiques doivent être server-authoritative ou disposer d’une stratégie d’arbitrage explicite.

## 22.3 Command model

Pour les actions critiques, utiliser un modèle conceptuel :

```text
COMMAND
↓
AUTHENTICATION
↓
AUTHORIZATION
↓
VALIDATION
↓
IDEMPOTENCY CHECK
↓
EXECUTION
↓
PERSISTENCE
↓
EVENT
↓
STATE UPDATE
↓
ACKNOWLEDGEMENT
```

Exemples :

```text
START_RECORDING
STOP_RECORDING
TAKE_SCENE
PUBLISH_PRESENTATION_VERSION
CREATE_EPISODE_FROM_TEMPLATE
START_EXPORT
DELETE_RAW_MEDIA
```

## 22.4 Concurrence

Définir :

- optimistic concurrency ;
- version numbers ;
- ETags ou mécanisme équivalent ;
- locks uniquement lorsque justifiés ;
- résolution de conflits ;
- comportement en cas de double commande.

## 22.5 Event log

Conserver les événements utiles à :

- audit ;
- debugging ;
- reconstruction du live ;
- post-production ;
- analytics techniques.

Ne pas stocker indéfiniment des événements sensibles sans politique de rétention.

---

# 23. API, ÉVÉNEMENTS, JOBS ET WORKERS

## 23.1 API

Choisir entre REST, GraphQL, RPC typé ou combinaison justifiée après analyse et QCM si nécessaire.

Exigences indépendantes du style d’API :

- contrats typés ;
- validation des inputs ;
- validation des outputs critiques ;
- erreurs structurées ;
- pagination ;
- filtrage ;
- rate limiting ;
- idempotency keys pour opérations critiques ;
- versioning ;
- corrélation des requêtes ;
- documentation générée ou maintenue.

## 23.2 Erreurs

Format d’erreur cohérent :

```text
code
message
userMessage
details
correlationId
retryable
```

Ne jamais exposer de secret ou stack trace sensible à l’utilisateur.

## 23.3 Événements métier

Exemples :

```text
EpisodeCreated
EpisodeGeneratedFromTemplate
ParticipantJoined
ParticipantReconnected
RecordingStarted
RecordingChunkUploaded
RecordingTrackCompleted
ProgramSceneChanged
TranscriptGenerated
ClipSuggested
ExportCompleted
```

Évaluer un outbox pattern pour les événements devant survivre à une transaction.

## 23.4 Job queue

Utiliser une queue pour les tâches longues :

- reconstruction média ;
- transcodage ;
- waveform ;
- transcription ;
- diarization ;
- génération de clips ;
- miniatures ;
- exports ;
- nettoyage ;
- antivirus ;
- indexation.

Chaque job doit avoir :

```text
jobId
type
status
attempt
maxAttempts
progress
inputReference
outputReference
createdAt
startedAt
finishedAt
error
correlationId
```

## 23.5 Retry et Dead Letter Queue

Définir :

- retries exponentiels ;
- erreurs retryables/non retryables ;
- idempotence ;
- timeout ;
- cancellation ;
- dead letter queue ;
- reprise manuelle ;
- visibilité dans l’UI d’administration.

## 23.6 Workers média

Isoler les traitements lourds :

- FFmpeg ;
- analyse vidéo ;
- encodage ;
- thumbnails ;
- waveform ;
- normalisation ;
- packaging.

Limiter CPU, mémoire, temps et concurrence.

Ne pas exécuter un binaire avec des arguments utilisateur non validés.

---

# 24. STOCKAGE, FICHIERS, VERSIONS ET CYCLE DE VIE

## 24.1 Stockage objet

Utiliser un stockage objet pour les médias et assets en production, sauf décision contraire validée.

Organisation logique possible :

```text
podcasts/{podcastId}/
episodes/{episodeId}/
recordings/{recordingSessionId}/
participants/{participantId}/
tracks/{trackId}/
chunks/{sequenceNumber}
```

Ne pas dépendre uniquement du nom de fichier pour la sécurité ou l’identité.

## 24.2 Métadonnées en base

La base relationnelle conserve :

- ownership ;
- relations ;
- version ;
- checksum ;
- statut ;
- taille ;
- type MIME validé ;
- clé de stockage ;
- durée ;
- dimensions ;
- permissions ;
- rétention.

## 24.3 Uploads

Prévoir :

- signed URLs ;
- taille maximale ;
- formats autorisés ;
- détection MIME réelle ;
- checksum ;
- multipart ;
- reprise ;
- validation post-upload ;
- antivirus ou sandbox lorsque pertinent ;
- suppression des uploads incomplets.

## 24.4 Versioning

Versionner :

- templates ;
- scènes ;
- présentations ;
- assets ;
- thèmes ;
- presets d’export ;
- décisions de montage ;
- transcriptions corrigées.

## 24.5 Cycle de vie

Définir les politiques pour :

```text
raw media
recording chunks
reconstructed tracks
program outputs
transcripts
clips
exports
temporary files
logs
```

Le choix de la durée de rétention est une décision structurante et doit faire l’objet d’un QCM s’il n’est pas déjà défini.

## 24.6 Suppression

Prévoir :

- soft delete lorsque nécessaire ;
- suppression définitive ;
- délai de grâce ;
- suppression en cascade contrôlée ;
- audit ;
- confirmation renforcée pour les sources originales ;
- jobs de purge idempotents.

---

# 25. MODÈLE DE DONNÉES

Définir précisément au minimum les entités suivantes :

```text
User
Identity
Podcast
PodcastMember
Role
Permission
BrandTheme
BroadcastTheme
EpisodeTemplate
EpisodeTemplateVersion
Episode
EpisodeMember
EpisodeChecklist
Segment
RundownItem
SceneTemplate
SceneTemplateVersion
Scene
SceneVersion
SceneLayer
Asset
AssetVersion
Presentation
PresentationVersion
RecordingSession
ParticipantSession
MediaTrack
MediaChunk
UploadSession
ProgramEvent
Transcript
TranscriptSegment
Chapter
EditDecisionList
ClipSuggestion
Clip
ExportPreset
Export
Job
Comment
Notification
Integration
McpCredential
AuditLog
FeatureFlag
```

Pour chaque entité, définir :

- identifiant ;
- ownership ;
- tenant/podcast boundary ;
- relations ;
- contraintes ;
- index ;
- version ;
- timestamps ;
- lifecycle ;
- règles de suppression ;
- données sensibles.

## 25.1 Contraintes importantes

- IDs non devinables lorsque exposés ;
- unicité explicite ;
- foreign keys ;
- transactions pour les invariants ;
- indexes correspondant aux requêtes réelles ;
- pas de JSON générique pour éviter de modéliser les domaines essentiels ;
- JSON autorisé pour des structures versionnées comme certaines définitions de scène, avec schéma validé.

## 25.2 Multi-tenancy

Choisir et documenter :

- tenant logique par podcast ou organisation ;
- isolation par ligne ;
- schéma séparé ;
- base séparée ;
- autre stratégie.

Cette décision doit faire l’objet d’un QCM si le modèle commercial et le niveau d’isolation ne sont pas connus.

---

# 26. IA, MCP ET GOUVERNANCE DES MODÈLES

## 26.1 MCP Server

Créer un serveur MCP sécurisé permettant aux IA autorisées d’interagir avec la plateforme.

Tools envisagés :

```text
create_podcast
get_podcast
update_podcast

create_episode
get_episode
update_episode
create_episode_from_template

create_segment
update_segment
list_segments

create_scene
update_scene
list_scenes

upload_asset
list_assets
get_asset

create_presentation
update_presentation
publish_presentation_version

get_transcript
update_transcript_segment

suggest_clips
create_clip
start_export

get_recording_metadata
get_job_status
```

Pour chaque tool :

```text
name
description
inputSchema
outputSchema
requiredScopes
idempotencyBehavior
sideEffects
confirmationPolicy
auditPolicy
rateLimit
```

## 26.2 Scopes MCP

Exemples :

```text
podcast:read
podcast:write
episode:read
episode:write
asset:read
asset:write
presentation:write
recording:read
transcript:write
clip:generate
export:start
admin:integrations
```

Le serveur doit toujours réappliquer les règles d’autorisation métier.

## 26.3 Actions sensibles

Les actions destructrices, coûteuses ou publiantes doivent nécessiter :

- scope explicite ;
- confirmation humaine si la politique l’exige ;
- idempotency key ;
- audit ;
- limite de coût ou quota.

## 26.4 Orchestration IA

Créer une couche d’abstraction pour :

- transcription ;
- diarization ;
- résumé ;
- génération de titres ;
- génération de présentation ;
- suggestions de clips ;
- génération d’assets ;
- classification ;
- modération si nécessaire.

Ne pas lier tout le domaine à un fournisseur unique sans interface d’abstraction justifiée.

## 26.5 Prompt management

Versionner :

- prompts ;
- modèles utilisés ;
- paramètres ;
- schémas de sortie ;
- jeux d’évaluation ;
- date ;
- coût ;
- résultat.

## 26.6 Structured outputs

Utiliser des sorties structurées et validées pour les opérations métier.

Ne pas appliquer directement une réponse libre d’un modèle à la base de données ou au moteur média.

## 26.7 Human-in-the-loop

Les suggestions de clips, suppressions, réécritures ou publications restent validables par un humain.

## 26.8 Évaluations IA

Créer des jeux d’évaluation pour :

- précision des speakers ;
- qualité de la transcription ;
- pertinence des clips ;
- conformité au format ;
- absence d’invention de timecodes ;
- stabilité des prompts ;
- latence ;
- coût.

---

# 27. SÉCURITÉ, CONFIDENTIALITÉ ET CONFORMITÉ

## 27.1 Authentification

Évaluer :

- fournisseur managé ;
- solution open source ;
- authentification interne.

Supporter selon le besoin validé :

- email/password ;
- magic link ;
- OAuth ;
- SSO futur ;
- MFA pour admins.

## 27.2 Autorisation

Implémenter :

- RBAC ;
- vérification serveur ;
- scopes MCP ;
- ownership ;
- isolation cross-podcast ;
- permissions des épisodes ;
- permissions des assets ;
- journal d’audit.

## 27.3 Menaces à traiter

Au minimum :

- IDOR ;
- privilege escalation ;
- XSS ;
- CSRF lorsque pertinent ;
- injection ;
- SSRF ;
- sandbox escape ;
- upload malveillant ;
- path traversal ;
- token leakage ;
- secret leakage ;
- replay de commande ;
- WebSocket hijacking ;
- accès cross-tenant ;
- signed URL réutilisée ;
- prompt injection via document ou présentation ;
- tool abuse MCP ;
- déni de service ;
- coût IA incontrôlé.

## 27.4 Présentations et pages web

Appliquer :

- origin isolée ;
- sandbox ;
- CSP ;
- allowlists ;
- validation des messages ;
- protection SSRF ;
- limitation réseau ;
- blocage des schémas dangereux.

## 27.5 Secrets

- jamais dans Git ;
- jamais dans le frontend ;
- secret manager ;
- rotation ;
- séparation par environnement ;
- secret scanning ;
- révocation documentée.

## 27.6 Consentement à l’enregistrement

Prévoir :

- indication visible ;
- consentement avant enregistrement si requis ;
- journal du consentement ;
- notification lors du démarrage ;
- politique pour les invités.

Les exigences légales et la zone géographique constituent une décision à clarifier par QCM.

## 27.7 Privacy

Prévoir :

- minimisation des données ;
- export des données ;
- suppression ;
- rétention ;
- chiffrement en transit ;
- chiffrement au repos ;
- accès aux sources ;
- audit des téléchargements ;
- politique de sous-traitants IA.

## 27.8 Threat model

Créer un threat model documenté avant la production, couvrant :

- acteurs ;
- actifs ;
- frontières de confiance ;
- flux de données ;
- menaces ;
- contrôles ;
- risques résiduels.

---

# 28. OBSERVABILITÉ ET DIAGNOSTIC

## 28.1 Trois piliers

Mettre en place :

```text
LOGS
METRICS
TRACES
```

Ajouter les événements métier et les métriques média nécessaires.

## 28.2 Corrélation

Utiliser notamment :

```text
correlationId
requestId
sessionId
recordingSessionId
participantId
jobId
exportId
```

Éviter d’inscrire des données sensibles ou des transcriptions complètes dans les logs techniques.

## 28.3 Métriques média

Collecter :

- RTT ;
- jitter ;
- packet loss ;
- bitrate ;
- FPS ;
- résolution ;
- frames dropped ;
- freezes ;
- upload throughput ;
- TURN usage ;
- reconnect count ;
- recording chunk lag ;
- local buffer size ;
- sync drift.

## 28.4 Métriques produit critiques

- taux de connexion au studio ;
- taux d’échec device check ;
- taux de récupération après coupure ;
- sessions avec source complète ;
- délai de disponibilité du replay ;
- délai de transcription ;
- taux d’échec export ;
- taux de jobs relancés.

## 28.5 Page diagnostic

Créer une page avant session affichant :

- navigateur ;
- support codecs ;
- caméra ;
- micro ;
- résolution ;
- permissions ;
- débit estimé ;
- latence ;
- TURN ;
- performance segmentation ;
- espace local disponible si mesurable ;
- recommandations.

## 28.6 Alerting

Définir des alertes sur :

- échec massif de connexions ;
- upload bloqué ;
- worker saturé ;
- queue en retard ;
- erreurs FFmpeg ;
- augmentation des pertes média ;
- erreurs de permission ;
- coût IA anormal ;
- stockage proche d’une limite.

---

# 29. PERFORMANCES, SCALABILITÉ ET COÛTS

## 29.1 Budgets de performance

Définir des budgets mesurables pour :

- temps de chargement ;
- temps d’entrée dans le studio ;
- latence de commande régie ;
- synchronisation collaborative ;
- FPS ;
- CPU ;
- GPU ;
- RAM ;
- bande passante ;
- délai de démarrage recording ;
- délai de disponibilité replay ;
- temps d’export.

Les seuils numériques doivent être confirmés par QCM lorsqu’ils représentent un engagement produit.

## 29.2 Profils de test

Tester :

```text
1 participant
3 participants
5 participants
```

Dans :

```text
GOOD DEVICE / GOOD NETWORK
AVERAGE DEVICE / AVERAGE NETWORK
MINIMUM SUPPORTED DEVICE / DEGRADED NETWORK
```

Mesurer :

- CPU ;
- GPU ;
- RAM ;
- FPS ;
- bitrate ;
- RTT ;
- packet loss ;
- rendering time ;
- bandwidth ;
- recording size ;
- upload speed ;
- batterie si mobile futur.

## 29.3 Tests de charge

Tester séparément :

- studios simultanés ;
- participants par studio ;
- connexions WebSocket ;
- trafic SFU ;
- uploads simultanés ;
- jobs média ;
- exports ;
- appels IA ;
- MCP.

Produire un rapport :

```text
Architecture testée jusqu’à X sessions
avec Y participants
selon le profil Z.

Bottleneck observé : ...
Limite actuelle : ...
Action recommandée : ...
```

## 29.4 Cost model

Estimer :

- SFU ;
- TURN ;
- egress ;
- stockage ;
- CDN ;
- transcription ;
- modèles IA ;
- transcodage ;
- workers ;
- observabilité ;
- sauvegardes.

Calculer approximativement :

```text
coût par heure enregistrée
coût par participant-heure
coût par épisode
coût par export
coût par clip
```

Créer des garde-fous :

- quotas ;
- budgets ;
- rate limits ;
- alertes ;
- suppression planifiée ;
- niveaux de qualité configurables.

---

# 30. ACCESSIBILITÉ, COMPATIBILITÉ ET RÉSILIENCE UX

## 30.1 Accessibilité

Viser au minimum :

- navigation clavier ;
- focus visible ;
- labels accessibles ;
- contrastes ;
- annonces d’état ;
- alternatives textuelles ;
- sous-titres ;
- erreurs compréhensibles ;
- absence de dépendance exclusive à la couleur.

Définir le niveau WCAG cible par QCM si non précisé.

## 30.2 Navigateurs

Définir officiellement les navigateurs supportés parmi :

- Chrome ;
- Edge ;
- Safari ;
- Firefox.

Ne pas promettre une compatibilité sans tests.

Détecter les incompatibilités avant l’enregistrement.

## 30.3 Appareils

Clarifier par QCM :

- desktop uniquement au MVP ;
- tablette ;
- smartphone invité ;
- application native future.

## 30.4 États UX

Chaque écran doit traiter :

- loading ;
- empty ;
- error ;
- offline ;
- reconnecting ;
- permission denied ;
- unsupported ;
- partial success ;
- retry ;
- cancellation.

---

# 31. ENVIRONNEMENTS, INFRASTRUCTURE ET DÉPLOIEMENT

Prévoir :

```text
LOCAL
TEST
PREVIEW
STAGING
PRODUCTION
```

## 31.1 Parité

Limiter les différences inutiles entre environnements.

Utiliser des services simulés uniquement lorsque leur comportement réel est couvert ailleurs.

## 31.2 Infrastructure as Code

Versionner l’infrastructure :

- réseau ;
- services ;
- stockage ;
- bases ;
- queues ;
- secrets references ;
- observabilité ;
- permissions.

## 31.3 Déploiement

Prévoir :

- déploiements reproductibles ;
- migrations contrôlées ;
- health checks ;
- readiness checks ;
- rollback ;
- déploiement progressif si pertinent ;
- protection de la branche principale ;
- provenance des artifacts.

## 31.4 Base de données

Toute migration doit être :

- versionnée ;
- testée ;
- reproductible ;
- analysée pour le rollback ;
- vérifiée sur un jeu réaliste ;
- compatible avec le mode de déploiement choisi.

Les migrations destructives doivent être signalées explicitement.

## 31.5 Feature flags

Utiliser des feature flags pour les capacités expérimentales :

```text
ai_clips
auto_director_v2
webgpu_segmentation
text_based_editing
server_compositor
```

Éviter les flags permanents non nettoyés.

## 31.6 Backups et restauration

Définir :

- fréquence ;
- rétention ;
- RPO ;
- RTO ;
- tests de restauration ;
- responsabilité ;
- chiffrement.

RPO et RTO doivent être décidés par QCM si inconnus.

---
# 32. STRATÉGIE DE TESTS AUTOMATISÉS

Créer une stratégie complète :

```text
STATIC ANALYSIS
↓
UNIT TESTS
↓
COMPONENT TESTS
↓
INTEGRATION TESTS
↓
CONTRACT TESTS
↓
E2E TESTS
↓
MEDIA / NETWORK TESTS
↓
SECURITY TESTS
↓
PERFORMANCE TESTS
↓
CHAOS / RECOVERY TESTS CIBLÉS
```

## 32.1 Static analysis

- formatage ;
- lint ;
- type checking strict ;
- détection de code mort ;
- règles d’architecture ;
- dependency cycle detection ;
- secret scanning ;
- SAST.

## 32.2 Tests unitaires

Couvrir prioritairement :

- règles métier ;
- factories ;
- permissions ;
- transitions d’état ;
- validation de schémas ;
- idempotence ;
- calcul de versions ;
- décisions Auto Director ;
- mapping média.

Ne pas viser un pourcentage de couverture vide de sens. Définir des seuils utiles par zone critique.

## 32.3 Tests de composants

Tester :

- régie ;
- device check ;
- scène ;
- timeline ;
- editor HTML ;
- formulaires ;
- états d’erreur ;
- accessibilité.

## 32.4 Tests d’intégration

Tester :

- API + base ;
- permissions ;
- stockage ;
- queue ;
- workers ;
- événements ;
- upload multipart ;
- reprise ;
- MCP ;
- collaboration.

Utiliser de vrais composants locaux ou conteneurisés lorsque cela apporte une meilleure confiance que des mocks.

## 32.5 Contract tests

Tester les contrats entre :

- frontend et API ;
- backend et SFU ;
- backend et stockage ;
- queue et workers ;
- MCP et application ;
- application et fournisseurs IA.

## 32.6 Tests E2E

Couvrir les parcours utilisateur à forte valeur et les scénarios de panne.

Ne pas tout tester en E2E. Garder une suite critique stable et rapide, complétée par une suite étendue.

## 32.7 Tests médias

Créer des fixtures médias déterministes :

- vidéo avec visage ;
- vidéo sans visage ;
- plusieurs visages ;
- audio voix ;
- bruit court ;
- silence ;
- clipping ;
- latence simulée ;
- pertes simulées.

Valider autant que possible avec des métriques et non uniquement des screenshots.

## 32.8 Network conditioning

Simuler :

- latence ;
- jitter ;
- packet loss ;
- débit réduit ;
- coupure ;
- changement de réseau ;
- reconnexion ;
- TURN forced.

## 32.9 Tests de sécurité

Automatiser :

- accès non autorisé ;
- cross-podcast ;
- IDOR ;
- élévation de privilège ;
- XSS ;
- sandbox ;
- SSRF ;
- uploads ;
- signed URLs ;
- rate limiting ;
- scopes MCP ;
- secrets ;
- dépendances.

## 32.10 Tests de performance

Créer des baselines et signaler les régressions sur :

- bundle ;
- temps de chargement ;
- FPS ;
- CPU ;
- mémoire ;
- rendu de scène ;
- segmentation ;
- commande régie ;
- upload ;
- reconstruction ;
- API ;
- jobs.

## 32.11 Tests de récupération

Tester :

- crash navigateur ;
- refresh ;
- perte réseau ;
- perte WebSocket ;
- perte SFU ;
- redémarrage worker ;
- retry job ;
- upload repris ;
- double commande ;
- export relancé.

---

# 33. CRITÈRES D’ACCEPTATION TESTABLES

Aucune fonctionnalité n’est terminée parce qu’elle « semble fonctionner ».

Tous les critères doivent devenir numériques dès que le seuil produit correspondant a été décidé. Si un seuil manque, poser un QCM avant validation finale.

Utiliser :

```text
GIVEN
WHEN
THEN
```

Chaque ticket contient :

```text
User Story
Acceptance Criteria
Edge Cases
Error States
Security Considerations
Performance Expectations
Observability
Test Strategy
```

## 33.1 Studio et connexion

### AC-STUDIO-001 — Rejoindre un épisode

**GIVEN** un épisode existant et un utilisateur autorisé  
**WHEN** l’utilisateur rejoint le studio  
**THEN** il entre dans la session et voit les participants déjà présents.

### AC-STUDIO-002 — Cinq participants

**GIVEN** un studio vide  
**WHEN** cinq clients supportés le rejoignent  
**THEN** les cinq participants sont identifiés de manière unique et reçoivent les tracks prévus par le layout et les permissions.

### AC-STUDIO-003 — Reconnexion

**GIVEN** un participant connecté  
**WHEN** sa connexion est interrompue pendant une durée couverte par le protocole de récupération puis restaurée  
**THEN** la session est restaurée automatiquement ou propose une action claire, sans créer de participant fantôme.

### AC-STUDIO-004 — Refus caméra

**GIVEN** un utilisateur refusant la caméra  
**WHEN** il rejoint le device check  
**THEN** l’application explique le problème et permet le mode audio seul si ce mode est autorisé.

### AC-STUDIO-005 — Identité stable

**GIVEN** un participant reconnecté  
**WHEN** une nouvelle connexion technique est créée  
**THEN** son `participantId` métier reste stable et son ancien état est réconcilié.

## 33.2 WebRTC et réseau

### AC-RTC-001 — Statistiques

Le diagnostic expose au minimum :

- bitrate ;
- packet loss ;
- jitter ;
- RTT ;
- résolution ;
- FPS ;
- codec ;
- candidat réseau sélectionné.

### AC-RTC-002 — Dégradation

**GIVEN** une session active  
**WHEN** la bande passante se dégrade  
**THEN** le système adapte la qualité selon la stratégie retenue sans interrompre l’audio prioritaire.

### AC-RTC-003 — Enregistrement indépendant

Une dégradation du flux live ne supprime pas les données déjà capturées dans le pipeline d’enregistrement local.

### AC-RTC-004 — ICE restart

**GIVEN** une rupture de chemin réseau récupérable  
**WHEN** un ICE restart est nécessaire  
**THEN** le client tente la récupération, remonte l’état et journalise le résultat.

### AC-RTC-005 — TURN

Un test automatisé ou contrôlé force TURN et vérifie que la session reste fonctionnelle.

## 33.3 Background removal

### AC-BG-001 — Suppression sans fond vert

**GIVEN** une personne devant un arrière-plan standard  
**WHEN** le détourage est activé  
**THEN** l’arrière-plan est remplacé sans fond vert physique.

### AC-BG-002 — Cas visuels

Tester au minimum :

- cheveux ;
- lunettes ;
- mouvements de tête ;
- mouvements de bras ;
- arrière-plan clair ;
- arrière-plan sombre ;
- faible contraste.

### AC-BG-003 — Budget de performance

Le traitement respecte le budget FPS/CPU/GPU validé pour la configuration minimale supportée.

### AC-BG-004 — Fallback

**GIVEN** un appareil incapable de maintenir le budget  
**WHEN** la segmentation est activée  
**THEN** l’application réduit la qualité, propose de la désactiver ou applique un fallback sans faire planter la session.

### AC-BG-005 — Désactivation

Le participant ou le Producer autorisé peut désactiver le détourage sans interrompre l’audio ou la connexion.

## 33.4 Scene Engine

### AC-SCENE-001 — Trois participants dans une scène

**GIVEN** trois participants publiant une vidéo  
**WHEN** la scène `3 speakers` est activée  
**THEN** les trois participants apparaissent aux coordonnées définies dans le même décor.

### AC-SCENE-002 — Propriétés

Chaque layer participant permet au minimum :

```text
x
y
width
height
scale
crop
zIndex
visibility
```

### AC-SCENE-003 — Synchronisation

Une modification persistée par un utilisateur autorisé est visible chez les autres dans le SLO de synchronisation validé.

### AC-SCENE-004 — Pas de coupure média

Changer de scène ne déclenche pas de reconnexion WebRTC ni de coupure audio.

### AC-SCENE-005 — Versioning

Une scène publiée peut être restaurée depuis une version précédente sans modifier les médias sources.

### AC-SCENE-006 — Preview isolée

Une modification en Preview ne modifie pas Program tant qu’aucune commande `TAKE` ou équivalente n’est acceptée.

## 33.5 Camera Matching

### AC-CAM-001 — Analyse indépendante

Chaque caméra est analysée séparément et conserve ses propres paramètres.

### AC-CAM-002 — Réglages

Les corrections couvrent au minimum les capacités validées parmi :

- exposition ;
- température ;
- contraste ;
- saturation ;
- gamma.

### AC-CAM-003 — Désactivation

Chaque correction peut être désactivée sans modifier le fichier source.

### AC-CAM-004 — Non destructif

Le média brut reste disponible et les réglages sont stockés sous forme de métadonnées ou de décisions dérivées.

### AC-CAM-005 — Benchmark

Un protocole reproductible compare :

```text
RAW A / RAW B / RAW C
↓
NORMALIZATION
↓
OUTPUT A / OUTPUT B / OUTPUT C
```

Le rapport indique les métriques disponibles et une évaluation visuelle contrôlée.

## 33.6 Auto-framing

### AC-FRAME-001 — Suivi

**GIVEN** un visage détecté  
**WHEN** la personne se déplace dans la zone prise en charge  
**THEN** le crop suit progressivement le sujet.

### AC-FRAME-002 — Smoothing

Les déplacements sont interpolés et ne produisent pas de saut au-delà du seuil validé.

### AC-FRAME-003 — Perte de visage

Une perte temporaire de détection conserve le dernier cadrage stable ou applique le fallback défini.

### AC-FRAME-004 — Correction manuelle

L’utilisateur autorisé peut reprendre la main et verrouiller le cadrage.

## 33.7 Audio

### AC-AUDIO-001 — Choix du microphone

L’utilisateur peut sélectionner un microphone disponible et vérifier qu’il est réellement utilisé.

### AC-AUDIO-002 — Vumètre

Le niveau d’entrée est visible avant et pendant l’enregistrement.

### AC-AUDIO-003 — Clipping

Un clipping dépassant le seuil validé est signalé avec une recommandation actionnable.

### AC-AUDIO-004 — Source exploitable

Lorsque l’architecture le permet, la piste source est conservée indépendamment du traitement live.

### AC-AUDIO-005 — Changement de périphérique

Le retrait du microphone déclenche un état explicite et une procédure de sélection d’un autre périphérique.

### AC-AUDIO-006 — Priorité audio

En réseau dégradé, la stratégie média privilégie l’intelligibilité audio selon les paramètres validés.

## 33.8 Active Speaker et Auto Director

### AC-SPK-001 — Speaker actif

**GIVEN** trois participants  
**WHEN** un participant parle seul au-delà du seuil validé  
**THEN** il est identifié comme speaker actif.

### AC-SPK-002 — Bruit court

Une toux, un clic ou un choc bref ne déclenche pas systématiquement un changement de scène.

### AC-SPK-003 — Temporisation

Le changement respecte la durée minimale de plan et le cooldown configurés.

### AC-SPK-004 — Conversation croisée

Lorsque plusieurs personnes parlent, le moteur applique la stratégie documentée au lieu d’osciller rapidement.

### AC-SPK-005 — Reprise manuelle

Le Producer peut désactiver Auto Director instantanément et conserver le contrôle manuel.

### AC-SPK-006 — Audit

Chaque décision automatique utilisée dans Program est journalisée avec sa raison.

## 33.9 Régie

### AC-REGIE-001 — Preview indépendante

Sélectionner une scène en Preview ne modifie pas Program.

### AC-REGIE-002 — TAKE

**WHEN** le Producer autorisé déclenche `TAKE`  
**THEN** la Preview validée devient Program une seule fois et l’événement est audité.

### AC-REGIE-003 — Asset en erreur

Une erreur de chargement en Preview ne remplace pas le Program actuel.

### AC-REGIE-004 — Types d’assets

La régie prend en charge au minimum :

- scène ;
- image ;
- vidéo ;
- présentation ;
- screen share ;
- lower third.

### AC-REGIE-005 — Permission

Un Guest sans permission ne peut pas modifier Program par appel UI, API, WebSocket ou MCP.

### AC-REGIE-006 — Double TAKE

Deux commandes concurrentes ou répétées ne créent pas un état incohérent.

## 33.10 Collaboration

### AC-COLLAB-001 — Mise à jour sans refresh

Une modification collaborative est reçue sans rechargement par les autres utilisateurs autorisés.

### AC-COLLAB-002 — Concurrence

Deux modifications simultanées ne provoquent pas de perte silencieuse de données.

### AC-COLLAB-003 — Reconnexion

Après reconnexion, le client récupère l’état courant et réconcilie les modifications locales selon la stratégie définie.

### AC-COLLAB-004 — Présence

Un utilisateur déconnecté n’est plus affiché comme actif après expiration du heartbeat défini.

### AC-COLLAB-005 — Permission dynamique

Une révocation de permission est appliquée sans nécessiter une nouvelle connexion complète dans le délai validé.

## 33.11 Présentations HTML

### AC-HTML-001 — Création et preview

Un utilisateur autorisé peut créer une présentation et afficher son rendu isolé.

### AC-HTML-002 — Temps réel

Une modification sauvegardée est visible par les collaborateurs dans le SLO défini.

### AC-HTML-003 — Version

Chaque publication significative crée une version restaurable.

### AC-HTML-004 — Rollback

Une version précédente peut être restaurée et crée une nouvelle version sans effacer l’historique.

### AC-HTML-005 — Isolation

Le contenu ne peut pas lire :

- cookies de l’application ;
- tokens ;
- DOM parent ;
- stockage sensible ;
- APIs non autorisées.

### AC-HTML-006 — Sandbox tests

La suite teste au minimum :

- tentative de navigation parent ;
- lecture de stockage ;
- appel réseau interdit ;
- message `postMessage` non autorisé ;
- script malveillant de test.

## 33.12 Podcast Factory

### AC-FACTORY-001 — Création complète

Créer un épisode depuis un template génère :

```text
brief
rundown
segments
scenes
asset references
presentation structure
recording workspace
clip workspace
export workspace
checklists
```

### AC-FACTORY-002 — Réutilisation

Les assets récurrents sont référencés ou figés selon leur politique, sans duplication inutile.

### AC-FACTORY-003 — Version figée

Une évolution du template global ne modifie pas rétroactivement un épisode existant.

### AC-FACTORY-004 — Traçabilité

L’épisode expose l’identifiant et la version du template, du thème et des presets utilisés.

### AC-FACTORY-005 — Idempotence

Une répétition accidentelle de la même commande avec la même clé d’idempotence ne crée pas deux épisodes.

### AC-FACTORY-006 — Validation

Un template invalide est rejeté avec une erreur structurée avant de créer un épisode partiel, ou l’opération est rollbackée.

## 33.13 MCP

### AC-MCP-001 — Création d’épisode

Un agent possédant le scope requis peut appeler `create_episode` et retrouver l’épisode dans l’application.

### AC-MCP-002 — Modification d’une présentation

Un agent autorisé peut créer ou modifier une présentation liée à l’épisode, et le changement est propagé aux collaborateurs.

### AC-MCP-003 — Refus d’autorisation

Un agent sans le scope requis reçoit une erreur d’autorisation structurée et aucune mutation n’est appliquée.

### AC-MCP-004 — Isolation

Un credential lié au podcast A ne peut lire ou modifier aucune ressource privée du podcast B.

### AC-MCP-005 — Audit

Toute opération de mutation enregistre :

```text
actor
credentialId
tool
scope
target
result
timestamp
correlationId
```

### AC-MCP-006 — Idempotence

Les tools créant des ressources critiques acceptent une stratégie d’idempotence documentée.

### AC-MCP-007 — Validation d’output

Une sortie IA invalide ne doit pas être appliquée avant validation contre le schéma attendu.

## 33.14 Enregistrement

### AC-REC-001 — Pistes séparées

Chaque participant produit une piste vidéo et une piste audio séparées lorsque le mode d’enregistrement configuré l’exige.

### AC-REC-002 — Program Output indépendant

Les sources participant sont conservées indépendamment du Program Output.

### AC-REC-003 — Coupure réseau

Une interruption réseau ne supprime pas les chunks déjà capturés localement.

### AC-REC-004 — Reprise

Après reconnexion, l’upload reprend depuis le dernier état confirmé sans renvoyer inutilement l’intégralité de la piste.

### AC-REC-005 — Intégrité

Chaque chunk est vérifié par checksum ou mécanisme équivalent et une corruption déclenche une nouvelle tentative ou un état explicite.

### AC-REC-006 — Synchronisation

Après reconstruction, les pistes respectent le seuil de dérive validé pendant la durée de test définie.

### AC-REC-007 — Crash navigateur

Le scénario de crash documente précisément quelles données restent :

```text
SAFE
UPLOADING
RECOVERABLE
MISSING
```

### AC-REC-008 — Arrêt contrôlé

`STOP_RECORDING` ferme la session, finalise les buffers, déclenche les uploads restants et produit un état final auditable.

### AC-REC-009 — Double démarrage

Deux commandes `START_RECORDING` concurrentes ne créent pas deux sessions actives incohérentes.

### AC-REC-010 — Consentement

Si la politique l’exige, le recording ne démarre pas tant que les conditions de consentement configurées ne sont pas remplies.

### AC-REC-011 — Stockage local saturé

Une capacité locale insuffisante est détectée autant que possible et produit un avertissement avant ou pendant la session.

### AC-REC-012 — Upload en arrière-plan du live

L’upload progressif ne doit pas dégrader le live au-delà du budget défini ; une stratégie de throttling doit exister.

## 33.15 Résilience et autosave

### AC-RECOVERY-001 — Autosave

Toute donnée éditoriale critique est sauvegardée automatiquement selon la politique définie.

### AC-RECOVERY-002 — Restauration

Fermer puis rouvrir l’application restaure le dernier état persistant disponible.

### AC-RECOVERY-003 — État temporaire

Les états temporaires et persistants sont clairement distingués dans l’architecture et dans l’UX lorsque nécessaire.

### AC-RECOVERY-004 — Job relancé

Un worker interrompu peut relancer un job idempotent sans dupliquer les outputs validés.

### AC-RECOVERY-005 — WebSocket perdu

Une perte du canal de contrôle affiche `reconnecting`, maintient les capacités locales sûres et resynchronise l’état après retour.

## 33.16 Rundown

### AC-RUNDOWN-001 — Quatre séquences

Un épisode créé depuis le template standard contient les quatre séquences configurées.

### AC-RUNDOWN-002 — Ressources par séquence

Chaque séquence référence ses notes, questions, scènes, assets et présentations.

### AC-RUNDOWN-003 — Changement pendant le live

Changer la séquence courante ne coupe pas l’enregistrement.

### AC-RUNDOWN-004 — Synchronisation

L’état courant du rundown est synchronisé entre les utilisateurs autorisés.

### AC-RUNDOWN-005 — Historique

Les changements importants du rundown sont versionnés ou auditables selon la politique définie.

## 33.17 Transcription

### AC-TRANSCRIPT-001 — Données minimales

Chaque segment possède :

```text
speakerId
startTime
endTime
text
```

### AC-TRANSCRIPT-002 — Navigation

Cliquer sur un segment positionne le lecteur au passage correspondant dans la tolérance définie.

### AC-TRANSCRIPT-003 — Correction

Un utilisateur autorisé peut corriger le texte et le speaker sans modifier le média source.

### AC-TRANSCRIPT-004 — Version

Les corrections sont versionnées ou auditables.

### AC-TRANSCRIPT-005 — Échec fournisseur

Un échec de transcription déclenche un état clair, un retry contrôlé et n’empêche pas l’accès aux médias.

## 33.18 Clips

### AC-CLIP-001 — Structure de suggestion

Chaque suggestion contient :

```text
startTime
endTime
title
hook
reason
score
```

### AC-CLIP-002 — Preview

Chaque suggestion est prévisualisable avant génération finale.

### AC-CLIP-003 — Ajustement

L’utilisateur peut modifier les points IN/OUT et le format.

### AC-CLIP-004 — Explicabilité

La raison de la suggestion est affichée comme aide éditoriale.

### AC-CLIP-005 — Pas de timecode inventé

Les points proposés sont validés contre la durée réelle et correspondent à des segments existants.

### AC-CLIP-006 — Rendu vertical

Un clip 9:16 respecte les safe zones du preset choisi et permet une correction manuelle du cadrage.

## 33.19 Exports

### AC-EXPORT-001 — Replay exploitable

Une session valide peut produire un replay lisible selon le preset retenu.

### AC-EXPORT-002 — Sources non destructives

L’export utilise des références et décisions de montage sans modifier les sources.

### AC-EXPORT-003 — Retry

Un export échoué peut être relancé sans répéter inutilement les étapes déjà validées, si l’architecture le permet.

### AC-EXPORT-004 — Traçabilité

Un export conserve :

```text
episodeId
presetVersion
editDecisionVersion
sourceTrackIds
createdAt
createdBy
checksum
```

### AC-EXPORT-005 — Annulation

Un export annulé libère ou nettoie les ressources temporaires selon la politique définie.

## 33.20 Assets et uploads

### AC-ASSET-001 — Validation

Un fichier non autorisé est rejeté avant exposition publique.

### AC-ASSET-002 — Checksum

Le checksum enregistré correspond au fichier stocké.

### AC-ASSET-003 — Signed URL

Une URL expirée ne permet plus l’accès et une nouvelle URL peut être obtenue par un utilisateur autorisé.

### AC-ASSET-004 — Isolation

Un utilisateur du podcast A ne peut accéder à l’asset privé du podcast B en modifiant un ID ou une clé.

### AC-ASSET-005 — Version

Une nouvelle version d’asset ne modifie pas un épisode ayant figé une version précédente.

### AC-ASSET-006 — Upload interrompu

Un upload multipart interrompu peut être repris ou annulé sans laisser indéfiniment des fragments orphelins.

## 33.21 Sécurité

### AC-SEC-001 — IDOR

Les tests confirment qu’un utilisateur authentifié ne peut pas accéder à une ressource non autorisée en changeant son identifiant.

### AC-SEC-002 — Privilege escalation

Un rôle Guest ne peut pas s’attribuer un rôle supérieur via UI, API, WebSocket ou MCP.

### AC-SEC-003 — XSS

Les entrées texte et contenus rendus sont traités selon leur contexte et les payloads de test ne s’exécutent pas.

### AC-SEC-004 — SSRF

Les fonctionnalités chargeant une URL empêchent l’accès non autorisé aux réseaux privés, métadonnées cloud et protocoles interdits.

### AC-SEC-005 — Rate limiting

Les endpoints sensibles appliquent les limites décidées et retournent une réponse structurée.

### AC-SEC-006 — Secrets

La CI échoue si un secret de test reconnu est commité selon les règles configurées.

### AC-SEC-007 — Audit

Les mutations administratives et média critiques sont auditables sans exposer de secret.

### AC-SEC-008 — Dépendances

Une vulnérabilité critique non acceptée bloque la release selon la politique de Quality Gate.

## 33.22 Performance

### AC-PERF-001 — Baseline

Chaque POC critique produit une baseline CPU, mémoire, FPS et réseau sur les profils de test retenus.

### AC-PERF-002 — Régression

Une régression dépassant le seuil validé est signalée et bloque la merge si elle touche une capacité critique.

### AC-PERF-003 — Régie

La latence entre `TAKE` accepté et état Program observé respecte le SLO validé dans les conditions de référence.

### AC-PERF-004 — Collaboration

La propagation d’une modification standard respecte le SLO validé sur le réseau de référence.

### AC-PERF-005 — Segmentation

La segmentation respecte le budget FPS et mémoire de la machine minimale supportée ou déclenche le fallback.

## 33.23 Accessibilité

### AC-A11Y-001 — Clavier

Les actions essentielles de PREP et STUDIO sont réalisables au clavier selon le périmètre validé.

### AC-A11Y-002 — Focus

Le focus est visible et suit un ordre logique.

### AC-A11Y-003 — Statuts critiques

Les changements critiques comme `recording started`, erreur micro ou reconnexion sont annoncés de manière accessible.

### AC-A11Y-004 — Contraste

Les composants du design system respectent le niveau de contraste validé.

## 33.24 Cross-browser

### AC-BROWSER-001 — Device check

Chaque navigateur officiellement supporté passe le device check défini.

### AC-BROWSER-002 — Feature detection

Une fonctionnalité non supportée est détectée avant l’enregistrement et un fallback ou message clair est proposé.

### AC-BROWSER-003 — Suite critique

Le Golden Path minimal est exécuté sur la matrice de navigateurs décidée avant release.

---

# 34. GOLDEN PATH E2E

Créer un scénario automatisé ou semi-automatisé représentant un véritable épisode.

```text
1. Créer un podcast
2. Configurer une marque
3. Créer un épisode depuis un template versionné
4. Vérifier la création des quatre séquences
5. Ajouter une présentation
6. Ajouter plusieurs assets
7. Inviter trois participants
8. Connecter les trois participants
9. Exécuter le device check
10. Activer le background removal
11. Placer les participants dans le studio virtuel
12. Vérifier le rundown partagé
13. Démarrer l’enregistrement
14. Faire parler le participant A
15. Vérifier la détection du speaker actif
16. Laisser Auto Director proposer ou appliquer le focus
17. Préparer une présentation en Preview
18. Déclencher TAKE
19. Vérifier la présentation dans Program
20. Revenir à la scène Group
21. Couper le réseau du participant B
22. Vérifier l’état de récupération
23. Reconnecter B
24. Vérifier l’absence de participant fantôme
25. Continuer l’enregistrement
26. Arrêter l’enregistrement
27. Finaliser et uploader les sources
28. Vérifier les checksums
29. Reconstruire les pistes
30. Vérifier la synchronisation
31. Générer le replay
32. Générer la transcription
33. Naviguer depuis un segment de transcript
34. Générer des suggestions de clips
35. Prévisualiser un clip
36. Générer un export
```

À la fin, vérifier :

```text
✓ podcast persistant
✓ épisode persistant
✓ version du template connue
✓ quatre séquences disponibles
✓ assets disponibles
✓ participants correctement identifiés
✓ sources disponibles
✓ pistes synchronisées
✓ Program Output disponible si configuré
✓ replay disponible
✓ transcript lié au média
✓ suggestions de clips disponibles
✓ export traçable
✓ aucune donnée critique perdue
✓ audit disponible
✓ logs et correlation IDs disponibles
```

Ce scénario constitue le **Golden Path E2E** du produit.

Il doit être rejoué régulièrement et obligatoirement avant les releases selon la stratégie CI/CD.

---

# 35. CI/CD ET QUALITY GATES À CHAQUE PUSH

## 35.1 À chaque push

Exécuter au minimum :

```text
FORMAT CHECK
↓
LINT
↓
TYPE CHECK
↓
UNIT TESTS
↓
AFFECTED COMPONENT / INTEGRATION TESTS
↓
BUILD
↓
SECRET SCAN
↓
DEPENDENCY / SAST CHECKS APPROPRIÉS
```

## 35.2 À chaque Pull Request

Exécuter :

```text
lint
typecheck
unit tests
integration tests
contract tests
affected E2E
build
security scans
migration validation
bundle/performance checks pertinents
```

Créer un preview environment lorsque pertinent.

L’agent doit inspecter le résultat réel des tests et ne jamais conclure que « tout fonctionne » uniquement parce que le build passe.

## 35.3 Avant merge vers la branche principale

Selon les zones modifiées :

```text
GOLDEN PATH CRITIQUE
SECURITY CRITICAL TESTS
DATABASE MIGRATION CHECK
RECORDING RECOVERY TESTS
PERFORMANCE REGRESSION CHECK
```

## 35.4 Avant release

Exécuter :

```text
FULL E2E
CROSS-BROWSER MATRIX
SECURITY SUITE
PERFORMANCE SUITE
MEDIA TESTS
NETWORK DEGRADATION
RECONNECT
RECORDING RECOVERY
BACKUP / RESTORE CHECK SELON CADENCE
```

Produire un rapport :

```text
PASS
FAIL
REGRESSION
KNOWN ISSUE
RISK ACCEPTED
```

## 35.5 Quality Gates bloquants

Exemples :

```text
Build failure → BLOCK
Type error → BLOCK
Critical test failure → BLOCK
Critical security vulnerability → BLOCK
Cross-tenant permission failure → BLOCK
Recording data-loss regression → BLOCK
Critical performance regression → BLOCK
Migration unsafe → BLOCK
```

Ne jamais désactiver silencieusement un Quality Gate pour faire passer une merge.

Toute exception doit être explicitement approuvée et documentée avec une expiration.

## 35.6 Tests affectés et suite complète

Utiliser des tests ciblés sur les pushes rapides, mais maintenir une suite complète planifiée et obligatoire avant release.

## 35.7 Flaky tests

Un test flaky ne doit pas être ignoré indéfiniment.

Prévoir :

- détection ;
- quarantaine temporaire ;
- issue associée ;
- propriétaire ;
- date d’expiration ;
- correction.

## 35.8 Artifacts CI

Conserver lorsque pertinent :

- screenshots ;
- vidéos E2E ;
- traces ;
- logs ;
- rapports de couverture ;
- rapports de sécurité ;
- résultats de performance ;
- fichiers média synthétiques de validation.

---
# 36. DOCUMENTATION, ADR ET INSTRUCTIONS POUR AGENTS IA

La documentation doit vivre avec le code.

Créer au minimum :

```text
/docs
├── product.md
├── architecture.md
├── domain-model.md
├── realtime.md
├── media-pipeline.md
├── recording.md
├── scene-engine.md
├── podcast-factory.md
├── episode-template.md
├── asset-factory.md
├── design-system.md
├── broadcast-design-system.md
├── security.md
├── threat-model.md
├── privacy.md
├── testing.md
├── performance.md
├── observability.md
├── deployment.md
├── runbooks.md
├── mcp.md
├── ai.md
├── cost-model.md
├── adr/
├── product-decisions/
└── design-decisions/
```

## 36.1 Architecture Decision Records

Pour les décisions importantes, créer des ADR.

Exemples :

```text
ADR-0001 — SFU selection
ADR-0002 — Local recording strategy
ADR-0003 — Realtime collaboration model
ADR-0004 — HTML sandbox architecture
ADR-0005 — Scene rendering architecture
ADR-0006 — Object storage strategy
ADR-0007 — Multi-tenancy strategy
```

Format :

```text
Status
Context
Decision Drivers
Options Considered
Decision
Consequences
Risks
Validation Plan
```

## 36.2 AGENTS.md

Créer un fichier `AGENTS.md` à la racine du dépôt.

Il doit expliquer aux agents IA :

- vision du produit ;
- architecture ;
- structure du dépôt ;
- commandes de développement ;
- conventions ;
- frontières de modules ;
- règles de sécurité ;
- stratégie de tests ;
- Definition of Done ;
- Quality Gates ;
- procédure QCM ;
- décisions déjà prises ;
- fichiers à lire avant toute modification ;
- pratiques interdites.

## 36.3 Instructions locales

Autoriser des fichiers `AGENTS.md` plus spécifiques dans les sous-dossiers si le harnais les supporte, par exemple :

```text
/apps/web/AGENTS.md
/services/media/AGENTS.md
/packages/domain/AGENTS.md
```

Les instructions locales ne doivent pas contredire les règles globales de sécurité et de clarification.

## 36.4 Documentation as code

Toute modification affectant un comportement documenté doit mettre à jour la documentation dans la même Pull Request.

La documentation doit être vérifiée par CI lorsque possible :

- liens ;
- formats ;
- schémas ;
- exemples compilables ;
- diagrammes générés ;
- références de commandes.

## 36.5 Runbooks

Créer des runbooks pour :

- échec SFU ;
- saturation TURN ;
- uploads bloqués ;
- queue saturée ;
- jobs FFmpeg en échec ;
- corruption d’un média ;
- incident de permission ;
- fuite de secret ;
- coût IA anormal ;
- restauration de backup ;
- rollback release.

---

# 37. WORKFLOW OBLIGATOIRE DE DÉVELOPPEMENT

Pour chaque feature, suivre ce workflow.

## 37.1 Discovery

```text
FEATURE REQUEST
↓
READ RELEVANT DOCS
↓
INSPECT EXISTING CODE
↓
IDENTIFY DECISIONS ALREADY MADE
↓
IDENTIFY MISSING INFORMATION
↓
ASK QCM IF REQUIRED
```

## 37.2 Spécification

Produire :

```text
User Story
Scope
Non-goals
Acceptance Criteria
Edge Cases
Permissions
Security Risks
Performance Budget
Observability Requirements
Test Strategy
Rollout Strategy
```

## 37.3 Conception

Produire ou mettre à jour :

- schéma d’architecture ;
- modèle de données ;
- contrat API ;
- événements ;
- migrations ;
- ADR si nécessaire ;
- menace et contrôles ;
- stratégie de rollback.

## 37.4 Implémentation

```text
SMALLEST COHERENT CHANGE
↓
UNIT TESTS
↓
INTEGRATION TESTS
↓
COMPONENT TESTS
↓
E2E IF REQUIRED
↓
SECURITY CHECK
↓
PERFORMANCE CHECK
↓
DOCUMENTATION
```

## 37.5 Validation

Avant de présenter le travail comme terminé :

1. exécuter les tests pertinents ;
2. lire les résultats ;
3. vérifier les logs ;
4. vérifier les erreurs navigateur ;
5. vérifier le comportement visuel si une UI a changé ;
6. vérifier les permissions ;
7. vérifier les états d’erreur ;
8. comparer aux critères d’acceptation ;
9. documenter les limites restantes.

## 37.6 Interdictions

Ne jamais :

- coder une décision structurante non validée ;
- désactiver un test pour faire passer la CI sans justification ;
- masquer une erreur avec un `try/catch` vide ;
- utiliser `any` ou équivalent pour contourner systématiquement les types ;
- supprimer une sécurité sans revue ;
- stocker un secret dans le code ;
- lancer une commande destructive non nécessaire ;
- modifier une migration déjà appliquée en production sans stratégie ;
- affirmer qu’un test passe sans l’avoir exécuté ;
- affirmer qu’une fonctionnalité est sécurisée sans méthode de validation ;
- inventer des résultats de benchmark ;
- écraser un média source ;
- autoriser l’exécution de HTML non isolé ;
- faire confiance aux permissions frontend ;
- permettre à une IA de publier ou supprimer sans permission explicite.

## 37.7 Rapport de fin de tâche

À la fin d’une tâche, fournir :

```text
Résumé des changements
Décisions prises
Questions restantes
Fichiers modifiés
Tests exécutés
Résultats
Critères d’acceptation validés
Risques / limites
Étape suivante recommandée
```

---

# 38. PROOFS OF CONCEPT PRIORITAIRES

Ne commence pas par construire trente écrans.

Valider d’abord les risques techniques fondamentaux.

## POC 1 — Media Plane

```text
3 clients
→ WebRTC
→ SFU ou architecture candidate
→ audio/vidéo stable
→ stats collectées
→ réseau dégradé
→ reconnexion
```

Mesurer :

- bitrate ;
- RTT ;
- packet loss ;
- CPU ;
- mémoire ;
- qualité ;
- temps de reconnexion.

## POC 2 — Segmentation et studio virtuel

```text
3 webcams
→ background removal
→ composition dans un décor commun
→ rendu stable
→ fallback machine faible
```

Mesurer :

- FPS ;
- CPU ;
- GPU ;
- mémoire ;
- qualité visuelle ;
- latence ajoutée.

## POC 3 — Recording local résilient

```text
local recording
→ chunking
→ buffer local
→ upload progressif
→ coupure réseau
→ reconnexion
→ reprise
→ vérification checksum
→ reconstruction
```

Tester :

- refresh ;
- fermeture ;
- crash simulé ;
- stockage local faible ;
- upload lent ;
- chunk corrompu.

## POC 4 — Synchronisation multipiste

```text
3 participants
→ start commun
→ pistes séparées
→ session longue de test
→ reconstruction
→ mesure du drift
```

## POC 5 — Auto Director

```text
3 speakers
→ voice activity
→ active speaker
→ bruit court
→ conversation croisée
→ scene switching
→ reprise manuelle
```

## POC 6 — Régie Preview / Program

```text
Scene A Program
→ Scene B Preview
→ asset invalide en Preview
→ Program reste stable
→ asset valide
→ TAKE
```

## POC 7 — Collaboration

```text
3 utilisateurs
→ même épisode
→ édition simultanée
→ déconnexion
→ modifications hors ligne limitées selon stratégie
→ reconnexion
→ réconciliation
```

## POC 8 — HTML sandbox

```text
présentation HTML
→ rendu isolé
→ tentative cookie
→ tentative parent DOM
→ tentative réseau interdit
→ postMessage contrôlé
```

## POC 9 — MCP

```text
AI
→ MCP
→ create episode from template
→ create presentation
→ realtime update
→ studio voit le changement
→ test permission refusée
→ audit
```

## POC 10 — Pipeline post-production

```text
sources
→ reconstruction
→ transcript
→ suggestion clip
→ export court
```

## Résultat obligatoire de chaque POC

```text
PASS
PARTIAL
FAIL
```

Avec :

- hypothèses ;
- environnement ;
- mesures ;
- captures/logs ;
- limites ;
- coût estimé ;
- recommandation ;
- décision de continuer, modifier ou abandonner.

---

# 39. ROADMAP MVP, V2 ET V3

La roadmap doit rester adaptable aux résultats des POC.

## 39.1 MVP

Le MVP doit idéalement contenir :

1. initialisation du dépôt et documentation ;
2. authentification ;
3. podcast ;
4. rôles de base ;
5. Episode Factory ;
6. quatre séquences ;
7. invitation de 3 à 5 participants ;
8. device check ;
9. webcam et micro ;
10. WebRTC ;
11. SFU ou architecture validée ;
12. background removal ;
13. studio virtuel ;
14. Scene Engine minimal ;
15. active speaker ;
16. Auto Director simple ;
17. Preview / Program ;
18. images et présentations ;
19. enregistrement local séparé ;
20. upload progressif ;
21. récupération ;
22. reconstruction ;
23. replay ;
24. observabilité minimale ;
25. Golden Path E2E ;
26. CI/CD et Quality Gates.

## 39.2 V2

Ajouter :

- transcription ;
- diarization ;
- MCP complet ;
- présentations HTML collaboratives ;
- design system et broadcast system enrichis ;
- Asset Factory avancée ;
- Auto Director avancé ;
- suggestions de clips ;
- correction manuelle des clips ;
- analytics techniques avancées ;
- rôles et permissions plus fins.

## 39.3 V3

Ajouter :

- montage basé sur le texte ;
- montage IA ;
- auto-reframing avancé ;
- publication multi-plateforme ;
- workflows éditoriaux ;
- analytics de contenu ;
- automatisation sociale ;
- streaming live externe si validé ;
- mobile ou application native si validé.

## 39.4 Challenge de roadmap

Si un POC démontre qu’une dépendance fondamentale n’est pas suffisamment robuste, proposer une nouvelle séquence de livraison et présenter le choix sous forme de QCM.

---

# 40. DEFINITION OF DONE GLOBALE

Une feature n’est `DONE` que si :

```text
[ ] user story claire
[ ] informations manquantes résolues par QCM
[ ] critères d’acceptation définis
[ ] implémentation terminée
[ ] permissions serveur testées
[ ] validation des entrées implémentée
[ ] cas d’erreur traités
[ ] états loading / empty / error traités
[ ] tests unitaires pertinents passent
[ ] tests d’intégration pertinents passent
[ ] tests composants pertinents passent
[ ] E2E critique passe si nécessaire
[ ] tests sécurité pertinents passent
[ ] impact performance mesuré si nécessaire
[ ] observabilité disponible
[ ] migration testée si nécessaire
[ ] rollback ou stratégie de récupération documenté
[ ] documentation mise à jour
[ ] ADR ou décision mise à jour si nécessaire
[ ] aucune régression critique connue
[ ] résultat vérifié réellement
```

Pour une feature média ou temps réel, ajouter :

```text
[ ] réseau dégradé testé
[ ] reconnexion testée
[ ] CPU mesuré
[ ] mémoire mesurée
[ ] FPS mesuré
[ ] bande passante mesurée
[ ] fallback testé
[ ] compatibilité navigateurs vérifiée
[ ] absence de perte de données critique vérifiée
```

Pour une feature IA, ajouter :

```text
[ ] input/output schema validé
[ ] prompt versionné
[ ] modèle et paramètres traçables
[ ] permissions testées
[ ] coût mesuré
[ ] cas d’échec traité
[ ] évaluation minimale exécutée
[ ] validation humaine prévue si nécessaire
```

---

# 41. LIVRABLES ATTENDUS AVANT LE PREMIER DÉVELOPPEMENT

Avant d’écrire les premières fonctionnalités de production, produire dans le dépôt :

## 41.1 Audit initial

- état du dépôt ;
- stack existante ;
- fichiers existants ;
- dette ou contraintes ;
- décisions déjà prises ;
- commandes disponibles ;
- tests existants.

## 41.2 QCM initial

Poser uniquement les questions structurantes réellement non résolues, par exemple :

- périmètre exact du MVP ;
- navigateurs cibles ;
- desktop ou mobile ;
- hébergement ;
- fournisseur/authentification ;
- SFU open source ou managé ;
- composition client ou serveur ;
- formats d’enregistrement ;
- qualité cible ;
- politique de rétention ;
- localisation des données ;
- budget ;
- échéance ;
- streaming live externe ou non.

Ne pas reposer une question déjà répondue dans le projet ou dans ce document.

## 41.3 Dossier d’architecture

Produire :

- diagramme contexte ;
- diagramme containers ;
- frontières de modules ;
- Media Plane ;
- Control Plane ;
- flux recording ;
- flux realtime ;
- flux MCP ;
- flux de stockage ;
- flux de post-production.

## 41.4 Modèle de domaine

Produire :

- entités ;
- relations ;
- invariants ;
- statuts ;
- événements ;
- permissions ;
- lifecycle.

## 41.5 Stratégie de test

Produire :

- matrice de tests ;
- fixtures ;
- Golden Path ;
- navigateurs ;
- profils réseau ;
- Quality Gates ;
- cadence des suites lourdes.

## 41.6 Threat model

Produire le threat model initial.

## 41.7 Backlog

Créer un backlog ordonné par :

```text
VALUE
RISK REDUCTION
DEPENDENCY
EFFORT
```

Commencer par les POC qui réduisent les risques les plus critiques.

## 41.8 Matrice de traçabilité

Maintenir :

```text
Feature
→ User Story
→ Acceptance Criteria
→ Architecture / ADR
→ Implementation
→ Automated Test
→ Status
```

Exemple :

```text
Background Removal
→ US-014
→ AC-BG-001 à AC-BG-005
→ ADR-0008
→ segmentation-worker.ts
→ background-removal.spec.ts
→ PASS
```

---

# 42. INSTRUCTION DE DÉMARRAGE DE L’AGENT

Lorsque tu reçois ce prompt :

1. lis entièrement ce document ;
2. inspecte le dépôt sans modifier immédiatement son architecture ;
3. lis tous les `AGENTS.md`, README, fichiers de configuration et documents existants ;
4. identifie ce qui existe déjà ;
5. compare l’existant aux exigences ;
6. produis un audit concis ;
7. liste les décisions déjà résolues ;
8. identifie les seules décisions réellement manquantes ;
9. pose ces décisions sous forme de QCM directement dans le harnais ;
10. n’implémente pas une décision structurante avant la réponse ;
11. propose ensuite les POC et le plan d’exécution ;
12. crée ou mets à jour la documentation et les critères d’acceptation ;
13. commence par la plus petite étape permettant de réduire un risque technique majeur ;
14. teste réellement chaque modification ;
15. maintiens le projet dans un état exécutable et compréhensible.

Ta première réponse doit utiliser cette structure :

```text
# Audit initial

## État du dépôt
...

## Éléments déjà présents
...

## Écarts principaux
...

## Risques techniques prioritaires
...

## Décisions déjà résolues
...

## Décisions requises
[QCM uniquement pour les informations réellement manquantes]

## POC recommandé en premier
...

## Plan proposé après validation
...
```

Ne commence pas par générer arbitrairement toute l’application.

Commence par comprendre, clarifier, prouver les briques risquées, documenter, tester, puis construire progressivement le MVP.

---

# FIN DU PROMPT MAÎTRE
