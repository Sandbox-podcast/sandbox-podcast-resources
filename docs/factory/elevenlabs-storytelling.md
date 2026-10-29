# Son de StoryTelling Generator

Le module produit des WAV mono PCM à 48 kHz pour le montage. Il conserve les répliques, les musiques et les effets dans des fichiers séparés et mesure leurs durées. Les descriptions d'émotion ou de montage restent des métadonnées ; seule la propriété `text` de la réplique est prononcée. La vitesse numérique est transmise lorsque le modèle la prend en charge. Les autres intentions de jeu restent à contrôler à l'écoute.

## Voix locales et enregistrements

`voice.provider=system` utilise une voix Windows `System.Speech` nommée, avec une déclaration `authorization`. Le texte est mis en cache par réplique et par paramètres de voix. Une correction recalcule ses bornes et la timeline ; les ressources indépendantes restent réutilisables.

`voice.provider=recordings` utilise les fichiers audio importés avec leur empreinte. L'orchestrateur résout les identifiants de sources vers les chemins locaux autorisés. L'import conserve le fichier source et crée sa copie de travail normalisée. Les bornes de réplique sont mesurées ; elles ne sont pas présentées comme un alignement mot à mot.

## Préparer ElevenLabs

La clé est lue côté serveur dans `ELEVENLABS_API_KEY`. `storytelling.elevenlabs.api_key_env` peut désigner une autre variable d'environnement. Ni la clé ni les réponses d'erreur brutes ne sont inscrites dans les exports ou le journal de la factory.

Le client lit les voix du compte, les modèles disponibles et les informations utiles de l'abonnement. Le modèle TTS est explicite dans `voice.model_id`. Le programme vérifie son support de la parole et ses limites de texte avant génération. Le format demandé est explicitement `mp3_44100_128`, puis FFmpeg produit le WAV de montage. Les formats plus coûteux ou réservés à certains abonnements ne sont pas choisis implicitement. Voir les références officielles des [modèles](https://elevenlabs.io/docs/api-reference/models/list), [voix](https://elevenlabs.io/docs/api-reference/voices/search) et [abonnements](https://elevenlabs.io/docs/api-reference/user/subscription/get).

Les appels payants exigent simultanément `storytelling.paid_calls_enabled=true`, `storytelling.elevenlabs.enabled=true` et un budget explicite de projet. La configuration livrée les garde désactivés. Activer un fournisseur ne constitue pas une validation de son compte réel.

Les paramètres suivants doivent venir de tarifs et de marges autorisés pour le compte :

- `currency` : même devise que le budget du projet ;
- `cost_per_character_upper_bound` : borne de coût par caractère parlé ;
- `cost_per_music_second_upper_bound` et `cost_per_effect_second_upper_bound` : bornes par seconde pour les capacités utilisées ;
- `music_enabled` et `effects_enabled` : autorisations explicites des deux capacités.

L'estimation affichable vient de ces bornes configurées. Elle reste distincte d'une facture ElevenLabs. Les champs d'abonnement ne permettent pas de déduire à eux seuls l'accès à tous les modèles musicaux et sonores ; leur disponibilité réelle est établie par les réponses des endpoints concernés.

## Parole, musique et effets

La production principale synthétise chaque réplique séparément. Les textes trop longs sont découpés sous la limite du modèle. Les segments d'une même réplique utilisent le contexte textuel précédent et suivant pour la continuité. Les dictionnaires de prononciation et les alias parlés sont conservés avec la voix. Les sous-titres gardent le texte original. Les [horodatages de parole](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps) sont conservés quand ils sont renvoyés et contrôlés ; à défaut, seules les bornes audio mesurées sont disponibles.

Le client expose aussi l'[endpoint de dialogue](https://elevenlabs.io/docs/api-reference/text-to-dialogue/convert-with-timestamps). Sa sortie reste un mix avec les segments de voix reçus. Elle ne fournit pas de pistes isolées par personnage. Le parcours par réplique facilite les corrections sans régénérer un dialogue entier.

La [composition musicale détaillée](https://elevenlabs.io/docs/api-reference/music/compose-detailed) utilise soit un prompt, soit un plan de composition. Les paramètres réservés au prompt ne sont pas envoyés avec un plan. La réponse MIME contenant audio et métadonnées est enregistrée avant son traitement. La musique générée par prompt est demandée instrumentale. Les [effets sonores](https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert) ont une durée explicite comprise entre 0,5 et 30 secondes et peuvent demander une boucle. Les placements, niveaux et fondus restent associés aux scènes et aux durées réelles.

## Budget, interruption et reprise

SQLite réserve la borne de coût avant chaque génération, sous transaction immédiate. Les opérations concurrentes utilisent le même plafond de projet. Une réservation engagée, un résultat reçu et une tentative incertaine continuent à consommer leur borne tant qu'un montant confirmé ne les remplace pas. Une réponse réussie ne constitue pas une facture confirmée. Un verrou local limite les générations ElevenLabs à une à la fois sur ce poste.

Les fichiers de réponse et leurs métadonnées sont sauvegardés immédiatement et liés à leurs empreintes. Une reprise réutilise ces fichiers seulement si leurs empreintes correspondent au reçu. Une altération bloque la réutilisation. Une coupure après un appel potentiellement facturé laisse une tentative `unknown`, sans nouvel appel automatique.

L'[historique ElevenLabs](https://elevenlabs.io/docs/api-reference/history/list) permet de rechercher une génération de parole lorsqu'un identifiant de requête fiable est disponible. Il ne permet pas actuellement de récupérer les générations musicales ou les effets sonores. Sans résultat local vérifiable ni identifiant récupérable, le programme garde la tentative bloquée. Il ne déduit pas une réussite d'un texte similaire et ne supprime pas sa réservation pour forcer un nouvel envoi.

Les contrôles locaux utilisent des réponses de test identifiées. Ils couvrent le plafond concurrent, les reprises, les limites de texte et les formats de réponse. Ils ne valident pas une connexion réelle ni la qualité d'une voix ElevenLabs.
