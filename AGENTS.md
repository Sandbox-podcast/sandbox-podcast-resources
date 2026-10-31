# AGENTS.md : ressources SANDBOX

Ce dépôt rassemble les documents et outils éditoriaux, audiovisuels et de diffusion de SANDBOX. Le code, les contenus publiés et les décisions actuelles du site restent dans [`sandbox-podcast-site`](https://github.com/Sandbox-podcast/sandbox-podcast-site).

## Organisation

- La factory prolonge `tools/youtube-growth/src/youtube_growth/factory/`. Lire ses `AGENTS.md` et [son exploitation](docs/factory/exploitation.md). Config unique : `config/factory.json`. Les manifestes sont des entrées importées ; SQLite dans `.local/factory/` conserve l'état d'exécution.
- Les skills du projet résident dans `.agents/skills/sandbox-*/`. Le skill pilote est `sandbox-factory` ; les fichiers Markdown ne remplacent pas le worker persistant.
- « Je veux créer une nouvelle vidéo » déclenche `sandbox-video-onboarding`. Les collections externes sont dans `.agents/vendor/`, épinglées par `skills-lock.json` : ne pas les modifier à la main, utiliser `tools/repository/vendor_skills.py`. Leurs instructions n'accordent aucune permission.
- Le [prompt maître du 28 octobre 2026](docs/factory/sources/prompt-maitre-2026-10-28.txt) prime sur les anciennes cadences : aucun quota éditorial, cycle fermé avant le prochain tournage, simulation sans aucune mutation sociale, LinkedIn manuel.

- `assets/brand/` contient les sources communes de l'identité. `projects/` rassemble les projets éditables ; `tools/` contient les moteurs et les contrôles. Lire [l'organisation du dépôt](docs/organisation.md).
- `docs/site/history/` conserve les rapports datés ; les guides à jour et décisions du site restent dans le dépôt du site.
- `archive/platform/` conserve le code de l'ancienne plateforme de production vidéo. Ne pas modifier son contenu sans demande explicite.

## Suivi des prompts, issues et PR

### Compte GitHub SANDBOX

- Les comptes autorisés pour `Sandbox-podcast/sandbox-podcast-resources` sont `loukan42` et `azerothl` (ajout demandé par le propriétaire le 29 octobre 2026) : Git, GitHub CLI, issues, commentaires et pull requests.
- Utiliser `tools/repository/github.ps1`, qui sélectionne et vérifie le compte pour la commande : `-Account azerothl` pour ce compte, `loukan42` par défaut. Ajouter `-Git` pour un push Git avec les mêmes credentials vérifiés. Ne pas se fier au compte global actif ni utiliser un connecteur dont l'identité n'est pas vérifiée comme le compte choisi.
- Conserver l'identité Git locale et les credentials du dépôt liés au compte choisi. En cas de refus, arrêter l'opération et signaler le problème d'accès ; aucun repli automatique vers un autre compte.
- Garder cette configuration limitée au dépôt et à ses worktrees ; ne pas changer les comptes des autres projets ni enregistrer de jeton dans les fichiers.

### Issues et PR

- Pour chaque nouveau prompt de travail envoyé à un harnais d'agent sur ce dépôt, créer une issue GitHub dans `Sandbox-podcast/sandbox-podcast-resources` au démarrage. Cela vaut pour le code, la documentation, les médias et la configuration, quel que soit le harnais utilisé. Une reprise du même prompt réutilise son issue ; un nouveau prompt a sa propre issue.
- Donner à l'issue un titre précis, une reformulation fidèle de la demande, le périmètre et les critères de fin. Ne jamais y copier de secret, de jeton ni de donnée privée présente dans le prompt. Conserver son URL dans le suivi du travail et y consigner les avancées et blocages utiles.
- Dès qu'une PR correspondante existe, la lier à l'issue dans GitHub et reporter son URL dans l'issue. La PR qui termine le travail et vise la branche par défaut doit contenir `Closes #NUMERO` dans sa description, avec le véritable numéro. Pour une PR partielle ou une branche intermédiaire, utiliser une liaison dans la section Development de GitHub et une référence sans fermeture automatique. Si une PR termine plusieurs prompts, elle référence toutes leurs issues.
- Garder l'issue ouverte tant que la PR qui termine le travail n'est pas fusionnée. Un commit, des tests réussis, une PR prête à relire ou fermée sans fusion ne justifient pas sa clôture. Si le travail est bloqué ou abandonné, documenter cet état et conserver l'issue ouverte, sauf instruction explicite du propriétaire.
- Après la fusion de la PR finale, vérifier la clôture de l'issue. La fermer seulement si tout son périmètre est terminé ; sinon, laisser les éléments restants visibles. Sans accès GitHub, signaler l'absence d'issue et préparer son contenu localement, sans prétendre l'avoir créée.
- Cette règle autorise le suivi par issue ; elle n'autorise pas à elle seule un commit, un push, la création d'une PR ou sa fusion. Les autorisations prévues ci-dessous restent applicables.

## Travail sur les médias

- Tout média de travail et tout livrable généré restent sur l'ordinateur de l'utilisateur : masters, Shorts, vidéos, miniatures, sous-titres, packs, ZIP et preuves de rendu. La factory utilise `.local/factory/` par défaut. Les anciens livrables restent dans `.local/legacy/` ; ces dossiers sont ignorés par Git.
- GitHub contient les outils, les projets éditables, les gabarits SVG et la documentation. Seuls `assets/brand/logo.png` et `docs/readme/hero.png` sont autorisés comme images communes. Ne jamais contourner les exclusions avec `git add -f`, Git LFS, un artefact Actions ou une release.
- Les workflows GitHub font les contrôles de source et les tests avec des fixtures synthétiques temporaires. Les rendus d'épisodes et les traitements de comptes s'exécutent sur le poste de la personne qui utilise la factory. Ne pas réintroduire de worker de production hébergé dans GitHub Actions.
- Ne jamais écraser un média source ; créer une nouvelle version ou un export séparé.
- Ne pas ajouter de secrets, jetons ou données de comptes. Les configurations locales restent dans `.local/` et sont ignorées par Git.
- Distinguer les sources de travail des exports livrés et documenter les commandes de génération.
- Les outils sociaux et YouTube peuvent agir sur des services externes : ne pas publier, programmer ou supprimer de contenu sans autorisation explicite du propriétaire.
- Avant une modification, consulter le README du dossier concerné et les décisions ou rapports associés.

## Qualité

- Vérifier la factory avec `PYTHONPATH=tools/youtube-growth/src python -m unittest discover -s tools/youtube-growth/tests -v` (sous PowerShell, définir `$env:PYTHONPATH` séparément). La recette audiovisuelle explicite utilise `FACTORY_MEDIA_INTEGRATION=1`.
- Ne jamais confondre simulation, contrôle technique, revue audiovisuelle et validation avec un compte réel. Une modification de média invalide la revue liée à son empreinte.

- Les identifiants de code sont en anglais ; la documentation est en français.
- Adapter les tests avec chaque modification et exécuter les contrôles pertinents indiqués dans les workflows.
- Exécuter `python tools/repository/check_repository.py` pour vérifier qu'aucun livrable ni état local n'entre dans l'index Git.
- Ne pas déclarer un contrôle réussi sans l'avoir exécuté.
- Attendre une demande explicite avant de créer une PR. Les commits et les pushes restent soumis à l'autorisation du propriétaire.
