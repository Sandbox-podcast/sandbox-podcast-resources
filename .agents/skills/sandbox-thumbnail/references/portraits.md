# Portraits de référence

Le manifeste [portraits.json](portraits.json) associe sans ambiguïté Lou, Nicolas et Loïc à leurs portraits publiés sur le site Sandbox. Les URL GitHub sont épinglées à une révision ; chaque fichier a une empreinte SHA-256. Ce sont les portraits de présentation du site, pas une attestation de photos brutes sans retouche. L'utilisateur a demandé leur utilisation pour les miniatures de sa chaîne.

## Charger les images ailleurs

1. Si le kit local contient `assets/portraits/`, utiliser ces trois fichiers après vérification de leurs empreintes contre le manifeste.
2. Sinon, depuis le dossier du skill, exécuter :

```sh
python3 scripts/fetch_portraits.py --output /chemin/local/portraits-sandbox
```

Sous Windows, utiliser `python` à la place de `python3`. Python 3 et sa bibliothèque standard suffisent. Le dossier de sortie doit rester hors de Git. Le script réutilise un fichier identique, refuse d'écraser un fichier différent et contrôle les empreintes téléchargées. En cas d'échec, ne pas changer de portrait silencieusement : demander une référence à l'utilisateur.

3. Ouvrir visuellement les trois fichiers avant génération, puis transmettre les images elles-mêmes au générateur, avec leurs noms. Des URL ou des descriptions textuelles seules ne garantissent pas la ressemblance.

Ne pas utiliser une miniature générée comme seule référence d'identité pour les générations suivantes : revenir aux portraits sources évite la dérive des visages. Les images des chaînes étudiées ne représentent pas les membres de Sandbox.

## Kit hors ligne

Copier le dossier complet `sandbox-thumbnail/`, y compris `SKILL.md`, `references/`, `scripts/` et `agents/`. Ajouter localement les trois portraits dans `assets/portraits/`. Les aperçus validés peuvent être joints dans `assets/examples/` pour guider le style, jamais pour remplacer les références d'identité. Ce kit transporte les références, pas le moteur de génération d'image. Aucun secret n'est inclus.

Les images restent exclues du dépôt resources conformément à son AGENTS.md. Le dossier du skill récupéré uniquement depuis GitHub télécharge donc les portraits au premier usage ; le ZIP local peut fonctionner hors ligne pour ses références.
