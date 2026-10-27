# Contrôle des workflows du 21 octobre 2026

Lou demande de corriger les échecs visibles dans GitHub Actions. Le contrôle porte sur le traitement News, les traductions, la CI et les classements. Corrections locales décidées par l’agent sur délégation (PD-0003), dans la suite de la publication autorisée.

## Constats reproduits

- News, passage 39598198838 : sept arrêts natifs du modèle. Les erreurs du parseur de grammaire montrent des guillemets issus des citations injectées en constantes dans le schéma. L’isolation des processus a préservé les publications valides, sans résoudre la cause native.
- Traductions : quatre articles restent incomplets. Deux contiennent des milliers avec espaces ; les traductions changent ce format et échouent au contrôle des valeurs. Deux titres dépassent leur borne de longueur après traduction.
- CI 39599756063 : le test des tentatives de connexion expire pendant le démarrage de PGlite, avant les assertions de concurrence. La base est désormais préparée dans un hook borné ; les assertions restent identiques et gardent leur délai.
- Recette HTTP : Next.js peut servir un statut 200 pour une page introuvable en flux HTML. Le test vérifie la page introuvable et le noindex du flux HTML, l’absence de données de classement et le vrai statut 404 de l’API JSON non diffusée en flux. Les métadonnées des archives inexistantes lèvent aussi notFound.
- Classements : Skills reste au créneau du 20 octobre à midi. Les reprises échouent à fournir l’historique requis. Rising répond explicitement pending et attend deux périodes mesurées ; aucune donnée n’est inventée.

## Corrections News

Les preuves restent des citations exactes du texte source, une par phrase. Le modèle désigne les passages utiles par des indices numériques bornés et distincts. Le programme vérifie une preuve par phrase, joint les citations exactes après génération et ne les injecte plus dans la grammaire native. Une seule phrase reste possible quand les autres passages sont du remplissage. Le modèle ne les choisissait déjà pas : la grammaire les imposait en constantes. Le changement retire la copie de ces constantes dans la sortie générée.

Les nombres sont protégés pendant la traduction puis restitués avec leur valeur d’origine. Leur perte ou duplication reste une erreur. Les titres traduits acceptent jusqu’à 400 caractères, pour éviter de couper une traduction allemande ou espagnole ; le titre français reste borné à 200. Le résumé garde ses contrôles de phrases, chiffres et caractères.

Les contrôles de sécurité, de publication et de fraîcheur restent actifs. Les vérifications distantes après livraison doivent confirmer la disparition des arrêts natifs, la reprise des quatre traductions et le résultat de la CI complète.

## Attente de Rising

L’API courante de Rising répond 202 avec un état pending, une liste vide et un message explicite sur les deux fenêtres de sept jours. Le contrôle rend cet état comme une attente, avec ok=false et pending=true pour la ligne Rising. L’agrégat de santé accepte cette seule attente connue si les autres éditions sont valides. Une absence de réponse, un échec, une liste incohérente ou un classement Skills périmé restent bloquants. Cette distinction corrige le signal d’exploitation ; elle ne publie aucune édition ni ne valide un historique manquant.

Les journaux de reprise conservent désormais les détails des collecteurs et des gels, pour distinguer manque d’historique, accès source et panne réseau.

## Échec Analytics révélé après les premiers contrôles

La CI suivante franchit les anciens échecs et s’arrête sur le clic YouTube de l’accueil mobile. La reproduction locale confirme que le bouton « Nos vidéos » utilise data-analytics-location, alors que le schéma des événements exige data-analytics-placement. L’événement est donc rejeté avant envoi. Le bouton transmet désormais placement=home. Un test lit les attributs du lien rendu et les soumet au validateur d’événements ; la recette navigateur garde les contrôles du consentement et des services simulés.

Le passage Charts 39606417107 réussit : les éditions GitHub, Skills et Models du créneau du 21 octobre à midi UTC sont publiées. Rising reste explicitement en attente d’historique, sans édition publiée.

## Reprise finale des traductions

Le passage de rédaction corrigé traite quinze candidats et publie sept fiches sans erreur d’exécution ni SIGSEGV. La CI complète a4b6d13 est réussie. La première reprise des traductions complète plusieurs fiches mais révèle deux derniers cas : des marqueurs contenant les mots anglais NUMBER et END sont altérés sur le trajet vers l’allemand ; une ancienne fiche possède une empreinte différente de son texte français et ses traductions calculées ne sont pas enregistrées.

Les nombres utilisent des marqueurs opaques, toujours vérifiés avant restitution. Un suffixe numérique isolé après une virgule est conservé hors du moteur, puis restitué en fin de texte. Il ne dépend ainsi pas de la décision du moteur de supprimer un renvoi. La reprise traduit le français effectivement stocké et conserve le jeton de concurrence initial pour l’écriture. Les langues déjà enregistrées restent conservées. La garde de l’API compare toujours l’empreinte et le français sous verrou avant toute écriture. Le job relit aussi les fiches encore incomplètes en base avant d’annoncer sa réussite.

Le mode manuel translate reprend les langues des fiches publiées sans relancer la collecte ni le modèle de résumé. Il utilise le même verrou que les cycles complets et conserve le contrôle de fraîcheur. Les cycles horaires gardent leur fonctionnement complet.

La reprise 39657451749 complète cinq des six fiches restantes. La dernière révèle la perte d’un marqueur sur le trajet anglais vers espagnol. Le worker vérifie désormais les marqueurs après chaque étape et réessaie avec des repères entre crochets si nécessaire. Chaque valeur doit rester présente exactement autant de fois ; une reprise incomplète ou un conflit avec des crochets existants reste rejeté. Le cas Luma est reproduit et traduit avec les modèles locaux, et quatre tests Python couvrent cette reprise.
