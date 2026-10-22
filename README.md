# Le guide de l'épargne

Site statique pédagogique sur l'épargne et l'investissement (épargne de précaution, bourse, ETF, PEA, assurance vie…).

Le site a été exporté à l'origine depuis Obsidian (extension « Webpage HTML Export »). Le contenu est désormais rédigé en Markdown dans `src/`, et les pages HTML sont générées par `build.py`, avec les styles et le script de l'export d'origine.

## Modifier le site

1. Modifier ou ajouter un fichier Markdown dans `src/`.
2. Régénérer les pages :

   ```sh
   python3 build.py
   ```

   Aucune dépendance n'est nécessaire (Python 3.8 ou plus). Le script s'arrête avec un message clair si un lien interne, un titre ou une image n'existe pas.
3. Vérifier le résultat dans un navigateur, par exemple avec `python3 -m http.server` puis http://localhost:8000.
4. Committer les fichiers `src/` **et** les pages `.html` générées (ce sont elles qui sont publiées).

Ne pas modifier directement les fichiers `.html` : ils sont écrasés à chaque génération (sauf `index.html`, qui redirige vers la page d'accueil).

## Organisation

| Chemin | Rôle |
| --- | --- |
| `src/*.md` | Contenu des pages (une page par fichier, même nom que la page `.html`) |
| `src/donnees/*.csv` | Données des graphiques |
| `build.py` | Générateur du site |
| `lib/styles/site.css`, `lib/scripts/site.js` | Styles et comportements propres au site |
| `lib/styles/*.css` (autres), `lib/scripts/webpage.js` | Fichiers de l'export Obsidian, à ne pas modifier |
| `*.png`, `favicon.svg` | Images |

## Syntaxe des fichiers Markdown

Chaque fichier commence par un en-tête :

```markdown
---
titre: Assurance vie
description: Phrase affichée par les moteurs de recherche.
ordre: 8
---
```

`ordre` fixe la position de la page dans le sommaire et dans les liens « Précédent / Suivant ».

Dans le corps de la page :

- Titres : `## Titre`, `### Sous-titre` (le titre principal vient de l'en-tête).
- Mise en forme : `**gras**`, `*italique*`, listes `- …` ou `1. …`, tableaux `| … |`.
- Liens vers une autre page du guide : `[[assurance-vie]]`, `[[assurance-vie|texte du lien]]`, ou vers un titre précis : `[[assurance-vie#Quel contrat choisir ?|texte]]`. Lien vers un titre de la même page : `[[#Les ETF|texte]]`.
- Liens externes : `[texte](https://…)`.
- Encadrés (comme dans Obsidian) : `> [!info] Titre`, `> [!question]`, `> [!warning]`, `> [!fail]`, `> [!success]`, `> [!tip]`, `> [!example]`, `> [!quote]`… Ajouter `-` après le crochet (`> [!info]- Titre`) pour un encadré replié par défaut.
- Image avec légende, seule sur sa ligne : `![texte alternatif](orange.png "Légende")`.
- Graphique en courbe à partir d'un fichier CSV (colonnes année, valeur) : `![Description](donnees/inflation-france.csv "Légende")`.

La date de dernière mise à jour et l'avertissement affichés en bas de chaque page se règlent en haut de `build.py` (`MISE_A_JOUR`, `AVERTISSEMENT`).
