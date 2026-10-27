# SANDBOX News : médias, synthèses et SEO local

Le 18 octobre 2026. Aperçu : <http://localhost:3328/news>. Décision : [DD-0053](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0053-news-liste-minitel-et-radar-local.md). Ce rapport remplace l'état d'interface et de collecte du rapport V1.

## Résultat

Le fil affiche 28 actualités relues, issues de neuf médias accessibles parmi les dix demandés. Il couvre les entreprises, les usages, la recherche, le développement, les modèles et la société. Le tri par défaut alterne les médias ; les tris chronologique et par média restent disponibles.

Chaque ligne présente un titre français original et sa date de publication. Le volet natif s'ouvre au clic, avec Entrée ou Espace, et contient trois phrases puis le lien vers le média. Le nom du média ne précède plus le titre. Les synthèses reposent sur le contenu public des pages ; les aperçus payants restent limités à leur partie publique.

Le bleu nuit, le blanc et le cyan remplacent le vert. Les titres mesurent 18 pixels, les dates 14 pixels et les synthèses 16 pixels. Recherche, catégories, média, état vide et réinitialisation fonctionnent ensemble. Les filtres sont fermés à l'arrivée.

## Collecte et limites

Le registre contient There's An AI For That, The Rundown AI, Superhuman AI, TLDR AI, Techpresso, The Deep View, The Neuron, The AI Report, AlphaSignal et Futurepedia. Au relevé du 18 octobre à 15 h 53 à Paris, les neuf derniers médias sont accessibles. There's An AI For That reste indisponible ; aucun autre accès n'est essayé pour contourner le refus observé.

Chaque actualisation examine jusqu'à trois articles récents par média accessible. Le cache conserve les articles depuis quatorze jours, jusqu'à 200 entrées. Les URL identiques sont dédupliquées ; deux médias qui traitent le même événement peuvent encore apparaître séparément. Le réseau est limité à quatre requêtes simultanées, les délais et tailles sont bornés et les redirections refusées. Une panne préserve les articles déjà reçus.

La date provient des métadonnées de publication ou d'une date visible associée à l'article. Une date de modification ne la remplace pas. Si seule la journée est connue, la page indique "heure non publiée". Les dates futures sont exclues.

Les 28 titres et synthèses sont préparés pour ce corpus dans `src/pipeline/news-editorial.ts`. Une nouvelle fiche avec son titre et ses trois phrases françaises reçoit automatiquement ses traductions EN/ES/DE au prochain rafraîchissement. Le chemin local utilise Argos Translate sur CPU, conserve les résultats dans le cache avec l'empreinte de la source et recommence si le texte change. Le modèle français-anglais sert de pivot vers l'espagnol et l'allemand. L'installation ponctuelle du moteur et des modèles se fait avec `pnpm --filter @podcast/site news:translator:setup` ; le contrôle local s'exécute avec `pnpm --filter @podcast/site news:translator:check`. Aucun service ni API de traduction distant n'est appelé. Le collecteur ne rédige pas les nouvelles synthèses : un article brut sans texte éditorial reste masqué. La qualité de traduction doit être mesurée avant l'ouverture publique. La collecte programmée reste à mettre en service et la couverture n'est pas exhaustive. Voir [DD-0056](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0056-traduction-automatique-news.md).

## Référencement

Le HTML initial contient les 28 titres, les 28 synthèses et les 28 liens externes, même volets fermés. Les métadonnées comprennent un titre descriptif, une description, une URL canonique et les cartes de partage existantes.

Les données structurées décrivent une `CollectionPage`, une `ItemList` et un fil d'Ariane. Les publications extérieures gardent leur éditeur et leur date. Aucun balisage `NewsArticle` ne présente SANDBOX comme leur auteur. Le relevé technique ne prétend pas être une modification éditoriale.

Le corpus reste en français ; les interfaces localisées marquent ces textes avec leur langue. Les variantes non traduites ne sont pas annoncées comme des pages indexables équivalentes. L'aperçu conserve `noindex` et la route reste fermée en production. Le chargement progressif au-delà de 30 entrées reste une interaction client, à remplacer par une pagination HTML et des archives avant publication.

Avant ouverture publique : terminer rédaction des nouveaux candidats, traductions, programmation et reprises ; créer les archives et la pagination ; activer indexation et sitemap pour les seules routes publiées ; contrôler Search Console et les performances de production. Aucun résultat Google ni affichage enrichi n'est garanti par le balisage.

Références : [contenu utile selon Google](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), [JavaScript et exploration](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics), [CollectionPage](https://schema.org/CollectionPage), [ItemList](https://schema.org/ItemList).

## Skills de rédaction

Les skills demandés sont installés dans le profil Codex de Lou : [no-ai-slop](https://github.com/petergyang/no-ai-slop), [anti-slop-fr](https://github.com/captain-marketing/anti-slop-fr) et [writing:unslop](https://github.com/ceyddrick/skills/tree/main/writing%3Aunslop). Ce dernier utilise le dossier local `writing-unslop` et un champ `name` pour la compatibilité Windows/Codex.

La règle est enregistrée dans `C:/Users/Lou/.codex/AGENTS.md` : conserver faits, noms propres, termes techniques et mots-clés SEO, puis retirer les formules creuses. Le profil de voix vierge du skill français reste inchangé. Le [skill UI/UX demandé](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) est conservé dans le dossier local ignoré `.local/skills/ui-ux-pro-max`.

## Vérification

La recette navigateur confirme l'ouverture au clic, la fermeture avec Entrée et l'ouverture avec Espace. Recherche LayerFS, filtre The Deep View, état vide et réinitialisation ramènent les 28 lignes. Aux largeurs demandées de 375, 768, 1024 et 1440 pixels, le document ne déborde pas horizontalement. Les tailles de texte calculées correspondent aux valeurs annoncées et le bouton Actualiser mesure 44 pixels de haut.

Le contrôle HTTP sans JavaScript constate un seul H1, 28 volets fermés, 28 paragraphes de synthèse, 28 liens externes et 28 éléments dans le JSON-LD. Il vérifie aussi les métadonnées et le `noindex`.

Les 35 tests News couvrent les trois phrases, les titres non relus, les corrections du cache, le rendu natif, les dates, les erreurs par source, les URL et le balisage. Après la dernière relecture, `corepack pnpm check` termine avec le code 0 : formatage, lint, TypeScript et 804 tests réussis (769 du site, 7 de timeline, 4 de médias et 24 BIS). `git diff --check` et le vérificateur rédactionnel des deux nouveaux états documentaires ne signalent pas d'erreur. Le build de production n'est pas lancé pour cette route réservée au développement.

Preuves locales ignorées par Git : `apps/site/.local/news-preview/qa/news-v3-responsive.json`, `news-v3-ssr.json`, `news-v3-mobile.jpg` et `news-v3-desktop.jpg`. Aucun benchmark de production ni audit Lighthouse n'est annoncé pour cet aperçu.

## Fichiers et suite

Fichiers du lot : domaines `news-media.ts`, `news-preview.ts`, `news-seo.ts` ; pipeline `news-media-preview.ts` et `news-editorial.ts` ; stockage `news-preview-store.ts` ; métadonnées `news-metadata.ts` ; composant `news-screen.tsx` et CSS ; page News et entrée de `shared-pages.tsx` ; tests `news-media-preview.test.ts` et `news-preview.test.ts` ; DD-0053 et documentation News. Les accès radar et carte de V1 restent dans le lot local. Le collecteur GitHub de V1 reste présent avec ses tests, sans être appelé par le stockage actif.

Aucun commit, push ou déploiement dans cette reprise. Les changements des autres chats sont conservés. Le contrôle global a aussi demandé une correction de formatage uniquement dans `exports/reseaux-sociaux/episode-02/replanification-proposee.json`.

## Automatisation des nouvelles fiches

Le lot de la PR ajoute ensuite un workflow GitHub Actions horaire. Il consulte les mêmes médias, lit les passages publics disponibles et évite les URL déjà enregistrées. Qwen3 1.7B rédige localement le titre et les trois phrases françaises ; le système refuse un résumé si ses trois citations ne figurent pas dans l'extrait. Argos traduit la fiche en anglais, espagnol et allemand. Le stockage Neon n'accepte que les fiches fraîches, complètes, rattachées au domaine exact d'une source autorisée et absentes de la base.

La page et les écritures de production restent désactivées. L'activation demande la migration 0016, la variable Vercel `SANDBOX_NEWS_PUBLIC=1`, la variable GitHub `SANDBOX_NEWS_PUBLIC=true` et le secret cron existant. La marche à suivre et les limites sont dans [DD-0057](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/docs/design-decisions/dd-0057-automatisation-production-news.md) et le [README du dépôt](https://github.com/Sandbox-podcast/sandbox-podcast-site/blob/main/README.md#sandbox-news). La citation d'un extrait ne garantit pas à elle seule la fidélité sémantique de chaque phrase ; le premier lot public devra être relu.
