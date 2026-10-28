# Capacités des plateformes

Vérification documentaire : 28 octobre 2026. Aucun upload, brouillon distant, test d'écriture, programmation ou changement de contenu n'a été effectué. Le contrôle d'un document officiel et le contrôle d'un compte sont deux preuves distinctes. Les adaptateurs de cette livraison simulent les échanges ; ils ne valident pas les accès aux plateformes.

## Comptes et droits observés

| Plateforme | Référence issue du dépôt | Accès API constaté pour cette factory | État |
| --- | --- | --- | --- |
| YouTube | `@SandboxFR`, chaîne `UCuATIBXo5uvNLVm-gCgMenA` | Connecteur historique présent ; nouveau consentement et droits non testés sur le compte pendant cette recette | Implémenté non vérifié |
| TikTok | `@sandbox.talkshow` | Aucun accès Accounts API ni prestataire compatible établi | À configurer ; éligibilité à vérifier |
| Instagram | `@sandbox.talkshow` | Anciennes preuves UI Meta ; aucun jeton ni scope Graph confirmé pour la factory | À configurer |
| X | Profil Sandbox mentionné dans les rapports | Identifiant numérique, droits vidéo et crédits API non confirmés | À configurer |
| LinkedIn | Nom d'affichage Sandbox Podcast demandé dans l'historique | Aucun connecteur de publication requis | Action humaine obligatoire |

Une session de navigateur ouverte ne fournit pas une authentification de worker. Les secrets restent hors Git. La configuration n'autorise un compte qu'après vérification de son identifiant stable et du périmètre accordé.

## YouTube

| Fonction | Surface documentée | État dans le périmètre |
| --- | --- | --- |
| Upload et métadonnées | Data API v3, OAuth ; contrôle du canal attendu dans le code existant | Ancien code conservé, écritures bloquées dans la recette |
| Publication différée et état | `status.publishAt`, visibilité, `processingDetails` ; un upload accepté reste distinct d'une vidéo disponible | À revalider sur le compte après autorisation |
| Miniature et playlist | Data API `thumbnails.set` et `playlistItems.insert` | Aucune mutation effectuée |
| Vidéo associée d'un Short | Studio ; accès aux fonctionnalités avancées et destination publique ou non répertoriée de la même chaîne | Action Studio à préparer ; aucune API publique vérifiée ici |
| Écran de fin interactif | Studio, selon éligibilité | Action humaine ; un élément graphique dans le MP4 ne crée pas de lien natif |
| A/B/C titre, miniature ou combinaison | Studio sur ordinateur, vidéos éligibles ; indisponible sur Shorts | Variantes locales possibles, démarrage et résultat natifs à saisir ; aucune API de test vérifiée |
| Vues et compteurs | Data API | Connecteur historique de lecture, contrôle réel à refaire |
| Temps regardé, rétention et trafic | Analytics API, rapports et dimensions compatibles | Ne pas promettre toutes les ventilations pour chaque vidéo |
| Impressions de miniatures et CTR | Reporting API, rapports de portée `channel_reach_basic_a1` et `channel_reach_combined_a1` | Intégration de collecte non validée sur la chaîne |

La référence [`videos.insert`](https://developers.google.com/youtube/data/reference/rest/v3/videos/insert) précise OAuth et les restrictions des projets non audités. Le [schéma vidéo](https://developers.google.com/youtube/data/reference/rest/v3/videos) distingue programmation, traitement et visibilité. La disponibilité de chaque action dépend des droits de l'application et de la chaîne.

Le dépôt conserve [cinq tests A/B/C observés en cours dans Studio le 26 octobre](../../.local/legacy/exports/reseaux-sociaux/extraits-abc-2026-10-26/manifest.json), sur Sillage, Harnais, Legacy, Artisans et Tickets. Cela atteste un usage natif historique, sans prouver une API de test ni l'état actuel de ces expériences. Aucun de ces tests n'a été arrêté ou modifié pendant cette recette. Les fichiers OAuth locaux usuels sont absents aux emplacements contrôlés et aucune connexion n'a été renouvelée.

Les [métriques Analytics](https://developers.google.com/youtube/analytics/metrics) conservent des définitions propres, dont `engagedViews`, temps regardé et abonnements. Les [rapports Reporting](https://developers.google.com/youtube/reporting/v1/reports/channel_reports) exposent aussi des rapports de portée avec impressions et CTR. L'ancienne documentation du dépôt qui renvoie systématiquement ces deux mesures à Studio doit donc être lue comme une limite de l'ancien collecteur.

Le [lien de vidéo associée](https://support.google.com/youtube/answer/14075157?hl=en) apparaît dans le lecteur Shorts sous les conditions indiquées par YouTube. Une URL dans une description ne remplace pas ce lien. Les [tests natifs](https://support.google.com/youtube/answer/16391400?hl=en) comparent jusqu'à trois titres, miniatures ou combinaisons, avec le temps regardé comme critère de résultat. Changer le titre ou la miniature pendant le test l'arrête. La factory doit donc préserver le verrou de packaging d'une expérience active, y compris après fermeture du cycle de nouvelles publications.

Pour les [écrans de fin](https://support.google.com/youtube/answer/6388789?hl=en), garder la distinction entre fichier vidéo et éléments ajoutés dans Studio. Ni les écrans de fin ni les tests natifs ne sont déclarés automatisés dans cette livraison.

## TikTok

| Voie | Authentification et prérequis | Conclusion pour Sandbox |
| --- | --- | --- |
| Content Posting API / Direct Post | Application et scope `video.publish`, autorisation du créateur, audit pour lever les restrictions, consentements et interface imposés | L'utilitaire interne pour les comptes de son équipe est exclu des usages acceptés ; ne pas en faire le connecteur interne |
| Content Posting API / Upload | Envoi vers la boîte de réception, puis action du créateur | Action humaine ; constitue déjà un upload distant, interdit pendant cette recette |
| Accounts API dans API for Business v1.3 | Demande d'accès, autorisation du compte organique, droits accordés pour Insights / Moderation / Publishing | Voie à examiner pour les comptes détenus ; aucun accès obtenu ou testé ici |
| Prestataire | Compatibilité du cas d'usage, comptes et fonctions à prouver contractuellement et par accès | Aucun prestataire choisi, aucune souscription |

Les [règles Direct Post](https://developers.tiktok.com/docs/en/content-sharing-guidelines) excluent les outils internes destinés à téléverser sur les comptes gérés par son équipe. Elles imposent aussi un aperçu, des choix du créateur et son consentement avant l'envoi. Leur audit ne transforme pas un usage exclu en usage autorisé. Le [guide Direct Post](https://developers.tiktok.com/docs/en/content-posting-api-get-started) demande notamment le scope et les informations actuelles du créateur ; une durée d'exemple n'est pas un plafond universel.

L'[Accounts API](https://business-api.tiktok.com/portal/docs/accounts-api-overview/v1.3) décrit la gestion organique des comptes détenus, dont publication et mesures, sous demande d'accès. C'est une offre distincte. Son éligibilité pour Sandbox reste à établir, sans supposer qu'un token autorise le fonctionnement autonome souhaité.

Titres, image de couverture, statut de traitement, quotas et mesures restent liés à la voie retenue et aux droits réellement accordés. Tant que cette voie est inconnue, exporter les fichiers et textes, conserver les actions humaines et bloquer la diffusion automatique. Aucun contournement par navigateur n'est prévu.

## Instagram

| Voie | Prérequis et permissions | État |
| --- | --- | --- |
| Instagram Login | Compte professionnel Business ou Creator ; famille `instagram_business_*`, dont publication ; cette voie ne requiert pas de Page Facebook liée | À configurer et à revalider sur le compte |
| Facebook Login | Compte professionnel lié à une Page ; permissions Instagram et Page correspondantes | À configurer ; les anciennes preuves Meta UI ne suffisent pas |
| Meta Business Suite | Fonctionnalités de l'interface native, distinctes de Graph API | Anciennes réservations conservées comme historique ; état actuel non contrôlé |

La [collection officielle Meta](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api?entity=request-23987686-3fe78620-2258-44b6-893f-42d76c7200d7) distingue ces deux familles de permissions. La [documentation Instagram Login](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/) et celle de [Facebook Login](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/) restent les références de prérequis. Leur lecture directe a renvoyé des erreurs d'accès ou HTTP 429 pendant ce relevé ; la collection Meta indexée a été consultée. Revalider les détails de version avant intégration.

La publication Graph passe par la préparation du média, son traitement et sa publication. Ne pas confondre identifiant de conteneur et publication visible. Les champs de couverture, les limites de fréquence et la liste de métriques doivent être vérifiés pour la version Graph et la voie d'authentification retenues. Aucun maximum de durée, quota, tarif ou renouvellement de token n'est figé par souvenir. Les fonctions UI de programmation ne prouvent pas l'existence d'un champ API équivalent.

## X

| Fonction | Documentation consultée | État du compte Sandbox |
| --- | --- | --- |
| Upload vidéo | API média v2, transfert par blocs, finalisation et lecture du statut | Non vérifié |
| Création de post | API v2, avec droits de l'utilisateur ; durée et taille revérifiées à la création du post | Non vérifié ; simulation uniquement |
| Durée et taille | Le guide API indique des droits différents de l'aide de l'interface web | Droits inconnus ; aucun plafond unique appliqué au compte |
| Couverture ou miniature | À distinguer d'une première image et de l'aperçu natif | Fonction d'import non validée pour l'intégration retenue |
| Mesures et coût | Accès dépendant des endpoints et du compte ; crédits à l'usage annoncés par X | Crédits, tarif exact et droits non contrôlés ; aucun achat |

Le [guide d'upload API](https://docs.x.com/x-api/media/quickstart/media-upload-chunked) annonce pour les vidéos de posts des limites typiques de 20 minutes / 8 Go, ou 125 minutes / 16 Go pour Premium, et impose le contrôle de l'état après finalisation. L'[aide web](https://help.x.com/en/using-x/x-videos) indique 140 secondes / 512 Mo sans abonnement et d'autres plafonds pour les abonnés. Ces documents décrivent des surfaces différentes et ne suffisent pas à établir les droits du compte Sandbox. Conserver cette différence dans le diagnostic et vérifier les capacités effectives avant tout extrait long.

La [plateforme développeur X](https://developer.x.com/) présente une facturation par crédits à l'usage. Les montants, les reads de ses propres contenus et les coûts des posts avec liens doivent être relevés dans la console du compte avant activation. Le budget réel reste nul pour cette recette, qui ne fait aucun appel payant.

## LinkedIn et attribution

LinkedIn reçoit exclusivement un pack local : vidéo définitive, couverture éventuelle, texte prêt à copier, URL de destination, date conseillée, embargo et fin de validité. Le statut `manual_ready` signifie que le pack est prêt. La confirmation d'une publication exige une saisie séparée de son URL et de sa date. Aucun adaptateur LinkedIn ne doit envoyer, programmer ou créer de brouillon distant.

Pour chaque réseau, conserver les métriques absentes comme absentes. Séparer clic observé, arrivée agrégée sur YouTube, visionnage long et abonnement attribuable. Un lien suivi ne prouve pas le parcours individuel, et la source Shorts agrégée ne désigne pas forcément le Short d'origine. Une somme de vues multiréseau ne constitue pas une audience unique.
