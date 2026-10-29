---
name: sandbox-resultats
description: Collecter ou importer les performances SANDBOX, comparer des contenus ou expériences et préparer le bilan ou le brief suivant. Utiliser pour Analytics, rétention, tests de titres ou révision de stratégie ; distinguer relevés réels, simulations et causalité non établie.
---

# Analyser les résultats

Partir des publications confirmées ou simulées, des observations sourcées, des coûts et du registre d'expériences. Fixer épisode, plateforme, compte, fenêtre et âge de publication. Utiliser `collect`, `report` et les imports selon [l'exploitation](../../../docs/factory/exploitation.md).

Pour importer un audit YouTube avec `import-analytics` ou comparer via `learn`, lire [le contrat Analytics](../../../docs/factory/production-editoriale.md#réutiliser-les-observations-analytics). Conserver rétention et sources de trafic ; fournir durée, format, publication, sujet, accroche, style et provenance. Exiger les impressions de la même période pour comparer l'exposition.

1. Pour chaque mesure, conserver définition native et version, unité, dénominateur utile, portée compte/post/média/destination, période, collecte et fuseau d'agrégation. Garder les valeurs absentes comme absentes. Ne pas additionner relevés cumulés, fenêtres recouvrantes ou posts partageant un média ; séparer fixtures et performances réelles.
2. Comparer des contenus d'âge et contexte compatibles ; expliciter les différences de durée, sujet, public et plateforme. Garder les médianes descriptives. Distinguer clic, arrivée YouTube, visionnage long et abonnement attribuable ; les données agrégées ne retracent pas un parcours individuel. Les commentaires suggèrent des hypothèses sans représenter toute l'audience.
3. Pour une expérience, garder hypothèse, facteur, variantes, population observable, fenêtre, métrique, arrêt et décision. Distinguer test natif simultané, contrôlé et observationnel. Accepter `inconclusive` sans seuil statistique universel ni gagnant inventé. Une expérience en cours peut continuer après la fermeture des nouveaux posts.

Pour le cycle suivant, commencer par `brief`, éventuellement avec `--episode-id`, et consulter [l'optimisation](../../../docs/factory/optimisation.md). Garder séparés faits de l'épisode et décisions globales ; vérifier les références signalées périmées. Temps et CPU Python ne mesurent ni coût financier ni énergie.

Livrer données disponibles et manquantes, constats, hypothèses, coûts constatés/estimés et décisions proposées. Toute modification de configuration conserve justification, valeurs avant/après, réévaluation et retour possible ; ne pas ajuster automatiquement le scoring. Une fixture peut justifier un test, jamais appliquer une stratégie. Un budget atteint bloque les dépenses dépendantes et préserve les résultats calculés.
