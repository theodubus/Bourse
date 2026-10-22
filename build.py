#!/usr/bin/env python3
"""Génère les pages HTML du site à partir des fichiers Markdown de src/.

Utilisation :

    python3 build.py

Aucune dépendance : seule la bibliothèque standard de Python (3.8 ou plus) est
utilisée. La syntaxe Markdown acceptée est décrite dans le README.
"""

from __future__ import annotations

import csv
import html
import json
import math
import re
import struct
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
SRC = RACINE / "src"

NOM_DU_SITE = "Le guide de l'épargne"
MISE_A_JOUR = "octobre 2026"

AVERTISSEMENT = (
    "Ce guide a une vocation pédagogique : il ne constitue pas un conseil en "
    "investissement personnalisé. Investir en bourse comporte un risque de perte "
    "en capital et les performances passées ne préjugent pas des performances "
    "futures. Les chiffres, règles fiscales et produits cités ont été vérifiés en "
    f"{MISE_A_JOUR} ; ils évoluent, pensez à les vérifier avant d'agir."
)

FEUILLES_DE_STYLE = [
    "lib/styles/obsidian-styles.css",
    "lib/styles/theme.css",
    "lib/styles/plugin-styles.css",
    "lib/styles/snippets.css",
    "lib/styles/generated-styles.css",
    "lib/styles/site.css",
]

NBSP = " "  # espace insécable
NNBSP = " "  # espace fine insécable


class ErreurSource(Exception):
    """Erreur dans un fichier Markdown (lien cassé, image absente, etc.)."""


# --------------------------------------------------------------------------
# Icônes (Lucide, licence ISC)
# --------------------------------------------------------------------------

def svg_icone(contenu: str, taille: int = 16, classe: str = "svg-icon") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="{classe}" width="{taille}" '
        f'height="{taille}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{contenu}</svg>'
    )


ICONES_CALLOUT = {
    "note": '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "todo": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "tip": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "success": '<path d="M20 6 9 17l-5-5"/>',
    "question": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "warning": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "fail": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "danger": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "example": '<line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/>',
    "quote": '<path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"/>',
    "abstract": '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
}

# Alias reconnus par Obsidian -> icône utilisée.
ALIAS_CALLOUT = {
    "summary": "abstract", "tldr": "abstract", "hint": "tip", "important": "tip",
    "check": "success", "done": "success", "help": "question", "faq": "question",
    "caution": "warning", "attention": "warning", "failure": "fail",
    "missing": "fail", "error": "danger", "bug": "danger", "cite": "quote",
}

TITRES_CALLOUT = {
    "note": "Note", "info": "Info", "todo": "À faire", "tip": "Astuce",
    "success": "À retenir", "question": "Question", "warning": "Attention",
    "fail": "À éviter", "danger": "Danger", "example": "Exemple",
    "quote": "Citation", "abstract": "Résumé",
}

ICONE_REPLI = svg_icone('<path d="m6 9 6 6 6-6"/>', 24, "svg-icon lucide-chevron-down")
ICONE_TITRE = svg_icone('<path d="M3 8L12 17L21 8"/>', 24, "svg-icon right-triangle")
ICONE_PANNEAU = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="svg-icon" width="100%" height="100%" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M21 3H3C1.89543 3 1 3.89543 1 5V19C1 20.1046 1.89543 21 3 21H21C22.1046 21 23 '
    '20.1046 23 19V5C23 3.89543 22.1046 3 21 3Z"/><path d="M10 4V20"/><path d="M4 7H7"/>'
    '<path d="M4 10H7"/><path d="M4 13H7"/></svg>'
)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def ancre(titre: str) -> str:
    """Identifiant d'un titre, au format de l'export Obsidian d'origine.

    Les points sont retirés : webpage.js déduit le type d'un lien de ce qui suit
    le dernier point, et prendrait « page.html#1._Titre » pour un fichier à télécharger.
    """
    return titre.strip().replace(" ", "_").replace(".", "")


class Page:
    def __init__(self, chemin: Path):
        self.chemin = chemin
        self.slug = chemin.stem
        self.fichier = self.slug + ".html"
        meta, self.corps = lire_entete(chemin)
        for cle in ("titre", "description", "ordre"):
            if cle not in meta:
                raise ErreurSource(f"{chemin.name} : champ « {cle} » manquant dans l'en-tête")
        self.titre = meta["titre"]
        self.description = meta["description"]
        self.ordre = int(meta["ordre"])
        self.titres = {}  # texte du titre -> identifiant
        for ligne in self.corps.splitlines():
            m = RE_TITRE.match(ligne)
            if m:
                self.titres[m.group(2)] = ancre(m.group(2))


def lire_entete(chemin: Path):
    """Sépare l'en-tête (entre deux lignes « --- ») du corps du fichier."""
    texte = chemin.read_text(encoding="utf-8").replace("\r\n", "\n")
    lignes = texte.split("\n")
    if not lignes or lignes[0].strip() != "---":
        raise ErreurSource(f"{chemin.name} : l'en-tête « --- » est absent")
    meta = {}
    for i, ligne in enumerate(lignes[1:], start=1):
        if ligne.strip() == "---":
            return meta, "\n".join(lignes[i + 1:])
        cle, sep, valeur = ligne.partition(":")
        if sep:
            meta[cle.strip()] = valeur.strip()
    raise ErreurSource(f"{chemin.name} : l'en-tête n'est pas refermé par « --- »")


class Contexte:
    def __init__(self, page: Page, pages: dict):
        self.page = page
        self.pages = pages


# --------------------------------------------------------------------------
# Éléments en ligne
# --------------------------------------------------------------------------

RE_EN_LIGNE = re.compile(
    r"""
      (?P<wiki>\[\[(?P<wiki_corps>[^\]]+)\]\])
    | (?P<img>!\[(?P<img_alt>[^\]]*)\]\((?P<img_src>[^)\s]+)\))
    | (?P<lien>\[(?P<lien_texte>(?:[^\[\]]|\[[^\]]*\])+)\]\((?P<lien_url>[^)\s]+)\))
    | (?P<code>`(?P<code_corps>[^`]+)`)
    | (?P<gras>\*\*(?P<gras_corps>.+?)\*\*)
    | (?P<ital>(?<![\w*])\*(?P<ital_corps>[^\s*](?:.*?[^\s*])?)\*(?![\w*]))
    | (?P<balise></?[a-zA-Z][^<>]*>)
    """,
    re.VERBOSE,
)


def typo(texte: str) -> str:
    """Espaces insécables de la typographie française."""
    texte = re.sub(r"(?<=\d) (?=\d{3}(?!\d))", NNBSP, texte)
    texte = re.sub(r"(?<=\d) (?=[€%])", NBSP, texte)
    texte = re.sub(r" (?=[?!:;»])", NNBSP, texte)
    return texte.replace("« ", "«" + NNBSP)


def texte_brut(texte: str) -> str:
    return typo(html.escape(texte, quote=False))


def en_ligne(texte: str, ctx: Contexte) -> str:
    morceaux = []
    position = 0
    for m in RE_EN_LIGNE.finditer(texte):
        morceaux.append(texte_brut(texte[position:m.start()]))
        position = m.end()
        if m.group("wiki"):
            morceaux.append(lien_wiki(m.group("wiki_corps"), ctx))
        elif m.group("img"):
            morceaux.append(
                f'<img src="{html.escape(m.group("img_src"))}" '
                f'alt="{html.escape(m.group("img_alt"))}">'
            )
        elif m.group("lien"):
            morceaux.append(lien(m.group("lien_texte"), m.group("lien_url"), ctx))
        elif m.group("code"):
            morceaux.append(f"<code>{html.escape(m.group('code_corps'))}</code>")
        elif m.group("gras"):
            morceaux.append(f"<strong>{en_ligne(m.group('gras_corps'), ctx)}</strong>")
        elif m.group("ital"):
            morceaux.append(f"<em>{en_ligne(m.group('ital_corps'), ctx)}</em>")
        else:
            morceaux.append(m.group("balise"))
    morceaux.append(texte_brut(texte[position:]))
    return "".join(morceaux)


def lien(texte: str, url: str, ctx: Contexte) -> str:
    if re.match(r"^(https?:|mailto:)", url):
        return (
            f'<a class="external-link" href="{html.escape(url)}" target="_blank" '
            f'rel="noopener">{en_ligne(texte, ctx)}</a>'
        )
    return f'<a class="internal-link" href="{html.escape(url)}">{en_ligne(texte, ctx)}</a>'


def lien_wiki(corps: str, ctx: Contexte) -> str:
    """[[page]], [[page|texte]], [[page#Titre|texte]] ou [[#Titre|texte]]."""
    cible, _, alias = corps.partition("|")
    slug, _, titre = cible.partition("#")
    slug, titre = slug.strip(), titre.strip()
    page = ctx.pages.get(slug) if slug else ctx.page
    if page is None:
        raise ErreurSource(f"{ctx.page.chemin.name} : lien vers une page inconnue « {slug} »")
    href = page.fichier if slug else ""
    if titre:
        if titre not in page.titres:
            raise ErreurSource(
                f"{ctx.page.chemin.name} : la page « {page.slug} » n'a pas de titre « {titre} »"
            )
        href += "#" + page.titres[titre]
    texte = alias.strip() or titre or page.titre
    return f'<a class="internal-link" href="{html.escape(href)}">{en_ligne(texte, ctx)}</a>'


# --------------------------------------------------------------------------
# Blocs
# --------------------------------------------------------------------------

RE_TITRE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
RE_PUCE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
RE_CALLOUT = re.compile(r"^\[!([\w-]+)\]([+-]?)\s*(.*)$")
RE_FIGURE = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)$')
RE_FILET = re.compile(r"^(-{3,}|\*{3,})$")


def indentation(ligne: str) -> int:
    ligne = ligne.expandtabs(4)
    return len(ligne) - len(ligne.lstrip(" "))


def debut_de_bloc(ligne: str) -> bool:
    brut = ligne.strip()
    return bool(
        RE_TITRE.match(ligne)
        or brut.startswith((">", "|"))
        or (RE_PUCE.match(ligne) and indentation(ligne) == 0)
        or RE_FIGURE.match(brut)
        or RE_FILET.match(brut)
    )


def analyser_blocs(lignes: list, ctx: Contexte) -> list:
    """Découpe des lignes en blocs : ("titre", niveau, texte) ou ("html", code)."""
    blocs = []
    i, n = 0, len(lignes)
    while i < n:
        ligne = lignes[i]
        brut = ligne.strip()
        if not brut:
            i += 1
            continue
        m = RE_TITRE.match(ligne)
        if m:
            blocs.append(("titre", len(m.group(1)), m.group(2)))
            i += 1
            continue
        if brut.startswith(">"):
            bloc = []
            while i < n and lignes[i].strip().startswith(">"):
                bloc.append(re.sub(r"^\s*> ?", "", lignes[i]))
                i += 1
            blocs.append(("html", rendre_citation(bloc, ctx)))
            continue
        if brut.startswith("|"):
            bloc = []
            while i < n and lignes[i].strip().startswith("|"):
                bloc.append(lignes[i].strip())
                i += 1
            blocs.append(("html", rendre_tableau(bloc, ctx)))
            continue
        if RE_PUCE.match(ligne):
            bloc = []
            while i < n and lignes[i].strip() and (
                RE_PUCE.match(lignes[i]) or indentation(lignes[i]) > 0
            ):
                bloc.append(lignes[i])
                i += 1
            blocs.append(("html", rendre_liste(bloc, ctx)))
            continue
        m = RE_FIGURE.match(brut)
        if m:
            blocs.append(("html", rendre_figure(m.group(1), m.group(2), m.group(3), ctx)))
            i += 1
            continue
        if RE_FILET.match(brut):
            blocs.append(("html", "<hr>"))
            i += 1
            continue
        bloc = []
        while i < n and lignes[i].strip() and not (bloc and debut_de_bloc(lignes[i])):
            bloc.append(lignes[i].strip())
            i += 1
        blocs.append(("html", "<p>" + "<br>\n".join(en_ligne(l, ctx) for l in bloc) + "</p>"))
    return blocs


def imbriquer(blocs: list) -> str:
    """Regroupe chaque titre avec son contenu, comme le faisait l'export Obsidian."""
    sortie = []
    i = 0
    while i < len(blocs):
        bloc = blocs[i]
        if bloc[0] == "html":
            sortie.append(f"<div>{bloc[1]}</div>")
            i += 1
            continue
        _, niveau, texte = bloc
        fin = i + 1
        while fin < len(blocs) and not (blocs[fin][0] == "titre" and blocs[fin][1] <= niveau):
            fin += 1
        identifiant = html.escape(ancre(texte))
        sortie.append(
            f'<div class="heading-wrapper">'
            f'<h{niveau} class="heading" data-heading="{html.escape(texte)}" id="{identifiant}">'
            f'<div class="heading-before"></div>'
            f'<div class="heading-collapse-indicator collapse-indicator collapse-icon">{ICONE_TITRE}</div>'
            f"{texte_brut(texte)}"
            f'<div class="heading-after">…</div></h{niveau}>\n'
            f'<div class="heading-children">\n{imbriquer(blocs[i + 1:fin])}\n</div></div>'
        )
        i = fin
    return "\n".join(sortie)


def rendre_liste(lignes: list, ctx: Contexte) -> str:
    premiere = RE_PUCE.match(lignes[0])
    base = indentation(lignes[0])
    numero = premiere.group(2)[:-1] if premiere.group(2)[0].isdigit() else None
    elements = []  # [lignes de texte, lignes de la sous-liste]
    for ligne in lignes:
        m = RE_PUCE.match(ligne)
        if m and indentation(ligne) <= base:
            elements.append([[m.group(3)], []])
        elif indentation(ligne) > base and (m or elements[-1][1]):
            elements[-1][1].append(ligne)
        else:
            elements[-1][0].append(ligne.strip())
    balise = "ol" if numero else "ul"
    debut = f' start="{numero}"' if numero and numero != "1" else ""
    sortie = [f"<{balise}{debut}>"]
    for texte, sous_liste in elements:
        contenu = "<br>\n".join(en_ligne(t, ctx) for t in texte)
        if sous_liste:
            retrait = min(indentation(l) for l in sous_liste)
            contenu += "\n" + rendre_liste([l.expandtabs(4)[retrait:] for l in sous_liste], ctx)
        sortie.append(f"<li>{contenu}</li>")
    sortie.append(f"</{balise}>")
    return "\n".join(sortie)


def rendre_citation(lignes: list, ctx: Contexte) -> str:
    m = RE_CALLOUT.match(lignes[0].strip())
    if not m:
        return f"<blockquote>\n{imbriquer(analyser_blocs(lignes, ctx))}\n</blockquote>"
    genre, pli, titre = m.group(1).lower(), m.group(2), m.group(3).strip()
    icone = ALIAS_CALLOUT.get(genre, genre)
    if icone not in ICONES_CALLOUT:
        icone = "note"
    titre_html = en_ligne(titre, ctx) if titre else TITRES_CALLOUT[icone]
    corps = imbriquer(analyser_blocs(lignes[1:], ctx))
    classes = ["callout"]
    attributs_titre = ""
    pliage = ""
    style_contenu = ""
    if pli:
        replie = pli == "-"
        classes.append("is-collapsible")
        if replie:
            classes.append("is-collapsed")
            style_contenu = ' style="display:none"'
        attributs_titre = (
            f' role="button" tabindex="0" aria-expanded="{"false" if replie else "true"}"'
        )
        pliage = f'<div class="callout-fold{" is-collapsed" if replie else ""}">{ICONE_REPLI}</div>'
    return (
        f'<div class="{" ".join(classes)}" data-callout="{html.escape(genre)}" '
        f'data-callout-fold="{pli}" data-callout-metadata="">\n'
        f'<div class="callout-title"{attributs_titre}>'
        f'<div class="callout-icon">{svg_icone(ICONES_CALLOUT[icone])}</div>'
        f'<div class="callout-title-inner">{titre_html}</div>{pliage}</div>\n'
        f'<div class="callout-content"{style_contenu}>\n{corps}\n</div>\n</div>'
    )


def cellules(ligne: str) -> list:
    """Découpe une ligne de tableau sans couper les liens [[page|texte]]."""
    ligne = ligne.strip()
    if ligne.startswith("|"):
        ligne = ligne[1:]
    if ligne.endswith("|") and not ligne.endswith("\\|"):
        ligne = ligne[:-1]
    resultat, courant, profondeur, i = [], "", 0, 0
    while i < len(ligne):
        if ligne.startswith("[[", i):
            profondeur += 1
            courant += "[["
            i += 2
            continue
        if ligne.startswith("]]", i) and profondeur:
            profondeur -= 1
            courant += "]]"
            i += 2
            continue
        c = ligne[i]
        if c == "\\" and ligne.startswith("\\|", i):
            courant += "|"
            i += 2
            continue
        if c == "|" and not profondeur:
            resultat.append(courant.strip())
            courant = ""
        else:
            courant += c
        i += 1
    resultat.append(courant.strip())
    return resultat


def rendre_tableau(lignes: list, ctx: Contexte) -> str:
    rangees = [cellules(l) for l in lignes]
    alignements = []
    entete = None
    if len(rangees) > 1 and all(re.match(r"^:?-{3,}:?$", c) for c in rangees[1]):
        for c in rangees[1]:
            if c.startswith(":") and c.endswith(":"):
                alignements.append("center")
            elif c.endswith(":"):
                alignements.append("right")
            else:
                alignements.append("")
        entete, rangees = rangees[0], rangees[2:]

    def cellule(balise, texte, colonne):
        style = ""
        if colonne < len(alignements) and alignements[colonne]:
            style = f' style="text-align:{alignements[colonne]}"'
        return f"<{balise}{style}>{en_ligne(texte, ctx)}</{balise}>"

    sortie = ['<div class="table-scroll"><table>']
    if entete:
        sortie.append(
            "<thead><tr>" + "".join(cellule("th", t, k) for k, t in enumerate(entete)) + "</tr></thead>"
        )
    sortie.append("<tbody>")
    for rangee in rangees:
        sortie.append("<tr>" + "".join(cellule("td", t, k) for k, t in enumerate(rangee)) + "</tr>")
    sortie.append("</tbody></table></div>")
    return "\n".join(sortie)


def taille_png(chemin: Path):
    with chemin.open("rb") as f:
        entete = f.read(24)
    if entete[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", entete[16:24])


def rendre_figure(alt: str, src: str, legende, ctx: Contexte) -> str:
    if src.endswith(".csv"):
        return rendre_graphique(alt, src, legende, ctx)
    chemin = RACINE / src
    if not chemin.is_file():
        raise ErreurSource(f"{ctx.page.chemin.name} : image introuvable « {src} »")
    taille = taille_png(chemin) if chemin.suffix.lower() == ".png" else None
    dimensions = f' width="{taille[0]}" height="{taille[1]}"' if taille else ""
    sortie = (
        f'<figure class="figure"><img src="{html.escape(src)}" alt="{html.escape(alt)}"'
        f'{dimensions} loading="lazy">'
    )
    if legende:
        sortie += f"<figcaption>{en_ligne(legende, ctx)}</figcaption>"
    return sortie + "</figure>"


# --------------------------------------------------------------------------
# Graphique en courbe à partir d'un fichier CSV (2 colonnes : année, valeur)
# --------------------------------------------------------------------------

def nombre_fr(valeur: float, decimales: int = 1) -> str:
    return f"{valeur:.{decimales}f}".replace(".", ",").replace("-", "−")


def rendre_graphique(alt: str, src: str, legende, ctx: Contexte) -> str:
    chemin = SRC / src
    if not chemin.is_file():
        raise ErreurSource(f"{ctx.page.chemin.name} : données introuvables « src/{src} »")
    with chemin.open(encoding="utf-8", newline="") as f:
        lignes = [l for l in csv.reader(f) if l]
    entetes = lignes[0]
    donnees = [(int(annee), float(valeur)) for annee, valeur in lignes[1:]]
    annees = [a for a, _ in donnees]
    valeurs = [v for _, v in donnees]

    largeur, hauteur = 640, 340
    gauche, droite, haut, bas = 56, 60, 30, 42
    y_max = math.ceil(max(valeurs))
    y_min = min(0, math.floor(min(valeurs)))
    pas_y = 1 if y_max - y_min <= 8 else 2

    def px(annee):
        return gauche + (annee - annees[0]) / (annees[-1] - annees[0]) * (largeur - gauche - droite)

    def py(valeur):
        return haut + (y_max - valeur) / (y_max - y_min) * (hauteur - haut - bas)

    def coord(x):
        return f"{x:.1f}"

    grille, axe_y, axe_x = [], [], []
    for v in range(y_min, y_max + 1, pas_y):
        y = coord(py(v))
        grille.append(f'<line x1="{gauche}" x2="{largeur - droite}" y1="{y}" y2="{y}"/>')
        axe_y.append(
            f'<text x="{gauche - 10}" y="{y}" text-anchor="end" dominant-baseline="middle">'
            f"{v}{NNBSP}%</text>"
        )
    reperes = [annees[0]] + [a for a in annees if a % 5 == 0 and a - annees[0] >= 3]
    for a in reperes:
        # Le premier repère, trop proche du suivant, est masqué sur les petits écrans.
        classe = ' class="chart-tick-debut"' if a == annees[0] and a % 5 else ""
        axe_x.append(
            f'<text{classe} x="{coord(px(a))}" y="{hauteur - bas + 26}" text-anchor="middle">{a}</text>'
        )

    points = [(px(a), py(v)) for a, v in donnees]
    trace = " ".join(f"{'M' if k == 0 else 'L'}{coord(x)},{coord(y)}" for k, (x, y) in enumerate(points))
    aire = f"{trace} L{coord(points[-1][0])},{coord(py(0))} L{coord(points[0][0])},{coord(py(0))} Z"

    # Étiquettes directes : la valeur maximale (au-dessus du point) et la
    # dernière valeur (au bout de la courbe).
    k_max = valeurs.index(max(valeurs))
    k_fin = len(donnees) - 1
    etiquettes = []
    for k in sorted({k_max, k_fin}):
        x, y = points[k]
        if k == k_fin:
            texte = (
                f'<text class="chart-label" x="{coord(x + 9)}" y="{coord(y)}" '
                f'dominant-baseline="middle">{nombre_fr(valeurs[k])}{NBSP}%</text>'
            )
        else:
            texte = (
                f'<text class="chart-label" x="{coord(x)}" y="{coord(y - 12)}" text-anchor="middle">'
                f"{annees[k]}{NNBSP}: {nombre_fr(valeurs[k])}{NBSP}%</text>"
            )
        etiquettes.append(f'<circle class="chart-dot" cx="{coord(x)}" cy="{coord(y)}" r="4"/>{texte}')

    donnees_js = json.dumps(
        [
            [round(x, 1), round(y, 1), str(a), f"{nombre_fr(v)}{NBSP}%"]
            for (x, y), (a, v) in zip(points, donnees)
        ],
        ensure_ascii=False,
    )
    svg = (
        f'<svg viewBox="0 0 {largeur} {hauteur}" role="img" tabindex="0" '
        f'aria-label="{html.escape(alt)}" data-points="{html.escape(donnees_js)}">'
        f"<title>{html.escape(alt)}</title>"
        f'<g class="chart-grid">{"".join(grille)}</g>'
        f'<path class="chart-area" d="{aire}"/>'
        f'<path class="chart-line" d="{trace}"/>'
        f'<g class="chart-axis">{"".join(axe_y)}{"".join(axe_x)}</g>'
        f"{''.join(etiquettes)}"
        f'<line class="chart-crosshair" x1="0" x2="0" y1="{haut}" y2="{hauteur - bas}"/>'
        f'<circle class="chart-focus" cx="0" cy="0" r="5"/>'
        f'<rect class="chart-hit" x="{gauche}" y="{haut}" width="{largeur - gauche - droite}" '
        f'height="{hauteur - haut - bas}"/>'
        "</svg>"
    )
    tableau = (
        '<details class="chart-table"><summary>Voir les données</summary><table>'
        f"<thead><tr><th>{html.escape(entetes[0])}</th>"
        f'<th style="text-align:right">{html.escape(entetes[1])}</th></tr></thead><tbody>'
        + "".join(
            f'<tr><td>{a}</td><td style="text-align:right">{nombre_fr(v)}</td></tr>'
            for a, v in donnees
        )
        + "</tbody></table></details>"
    )
    bulle = (
        '<div class="chart-tooltip" hidden><span class="chart-tooltip-valeur"></span>'
        '<span class="chart-tooltip-libelle"></span></div>'
    )
    legende_html = f"<figcaption>{en_ligne(legende, ctx)}</figcaption>" if legende else ""
    return f'<figure class="figure chart">{svg}{bulle}{legende_html}{tableau}</figure>'


# --------------------------------------------------------------------------
# Gabarit de page
# --------------------------------------------------------------------------

def element_arbre(href: str, titre: str, profondeur: int, actif: bool = False, enfants: str = "") -> str:
    classes = "tree-item" + (" mod-tree-file" if profondeur == 1 and not href.startswith("#") else "")
    if actif:
        classes += " mod-active"
    return (
        f'<div class="{classes}" data-depth="{profondeur}"><div class="tree-item-contents">'
        f'<a class="internal-link tree-item-link" href="{html.escape(href)}">'
        f'<span class="tree-item-title">{texte_brut(titre)}</span></a></div>'
        f'<div class="tree-item-children">{enfants}</div></div>'
    )


def bouton_repli(replie: bool) -> str:
    return (
        f'<button class="clickable-icon collapse-tree-button{" is-collapsed" if replie else ""}" '
        'aria-label="Replier ou déplier"><svg xmlns="http://www.w3.org/2000/svg" width="24" '
        'height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"></svg></button>'
    )


def rendre_page(page: Page, pages: list, index: int, contenu: str) -> str:
    sommaire = "".join(
        element_arbre(p.fichier, p.titre, 1, actif=p is page) for p in pages
    )
    plan = "".join(
        element_arbre("#" + identifiant, texte, int(niveau))
        for niveau, texte, identifiant in titres_de(page)
    )
    plan = element_arbre("#" + ancre(page.titre), page.titre, 1, enfants=plan)

    navigation = []
    if index > 0:
        precedente = pages[index - 1]
        navigation.append(
            f'<a class="internal-link page-nav-prev" href="{html.escape(precedente.fichier)}">'
            f'<span class="page-nav-label">← Précédent</span>'
            f'<span class="page-nav-title">{texte_brut(precedente.titre)}</span></a>'
        )
    if index < len(pages) - 1:
        suivante = pages[index + 1]
        navigation.append(
            f'<a class="internal-link page-nav-next" href="{html.escape(suivante.fichier)}">'
            f'<span class="page-nav-label">Suivant →</span>'
            f'<span class="page-nav-title">{texte_brut(suivante.titre)}</span></a>'
        )

    titre_onglet = page.titre if page.titre == NOM_DU_SITE else f"{page.titre} · {NOM_DU_SITE}"
    styles = "\n".join(f'<link rel="stylesheet" href="{f}">' for f in FEUILLES_DE_STYLE)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{texte_brut(titre_onglet)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{html.escape(page.description)}">
<base href="./">
<meta id="root-path" root-path="./">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
{styles}
<script src="lib/scripts/webpage.js"></script>
<script src="lib/scripts/site.js" defer></script>
</head>
<body class="theme-light show-inline-title loading">
<script>try{{if(localStorage.getItem("theme_toggle")===null&&matchMedia("(prefers-color-scheme: dark)").matches)document.body.classList.replace("theme-light","theme-dark")}}catch(e){{}}</script>
<div class="webpage-container">
<div class="sidebar-left sidebar">
<div class="sidebar-container"><div class="sidebar-sizer"><div class="sidebar-content-positioner"><div class="sidebar-content">
<div><label class="theme-toggle-container" for="theme_toggle" title="Thème clair ou sombre"><input class="theme-toggle-input" type="checkbox" id="theme_toggle"><div class="toggle-background"></div></label></div>
<nav class="tree-container file-tree mod-nav-indicator" data-depth="0" aria-label="Sommaire">
<div class="tree-header"><span class="sidebar-section-header">Sommaire</span>{bouton_repli(True)}</div>
<div class="tree-scroll-area">
{sommaire}
</div>
</nav>
</div></div></div></div>
<div class="sidebar-gutter"><div class="clickable-icon sidebar-collapse-icon" title="Afficher ou masquer le sommaire">{ICONE_PANNEAU}</div></div>
</div>
<div class="document-container show">
<main class="markdown-preview-view markdown-rendered node-insert-event is-readable-line-width allow-fold-headings show-indentation-guide allow-fold-lists show-properties" style="tab-size:4" tabindex="-1">
<div class="markdown-preview-sizer markdown-preview-section">
<div class="markdown-preview-pusher" style="width:1px;height:.1px;margin-bottom:0"></div>
<div class="mod-header"><h1 class="inline-title" data-heading="{html.escape(page.titre)}" id="{html.escape(ancre(page.titre))}">{texte_brut(page.titre)}</h1></div>
{contenu}
<div class="mod-footer">
<nav class="page-nav" aria-label="Page précédente et page suivante">{"".join(navigation)}</nav>
<p class="avertissement"><strong>Avertissement.</strong> {texte_brut(AVERTISSEMENT)}<br>Dernière mise à jour : {MISE_A_JOUR}.</p>
</div>
</div>
</main>
</div>
<div class="sidebar-right sidebar">
<div class="sidebar-gutter"><div class="clickable-icon sidebar-collapse-icon" title="Afficher ou masquer le plan de la page">{ICONE_PANNEAU}</div></div>
<div class="sidebar-container"><div class="sidebar-sizer"><div class="sidebar-content-positioner"><div class="sidebar-content">
<nav class="tree-container outline-tree" data-depth="0" aria-label="Sur cette page">
<div class="tree-header"><span class="sidebar-section-header">Sur cette page</span>{bouton_repli(False)}</div>
<div class="tree-scroll-area">
{plan}
</div>
</nav>
</div></div></div></div>
</div>
</div>
</body>
</html>
"""


def titres_de(page: Page):
    for ligne in page.corps.splitlines():
        m = RE_TITRE.match(ligne)
        if m:
            yield len(m.group(1)), m.group(2), ancre(m.group(2))


# --------------------------------------------------------------------------

def construire() -> int:
    pages = sorted((Page(c) for c in SRC.glob("*.md")), key=lambda p: (p.ordre, p.slug))
    ordres = [p.ordre for p in pages]
    if len(set(ordres)) != len(ordres):
        raise ErreurSource("deux pages ont le même « ordre » dans leur en-tête")
    index_pages = {p.slug: p for p in pages}
    for index, page in enumerate(pages):
        ctx = Contexte(page, index_pages)
        contenu = imbriquer(analyser_blocs(page.corps.split("\n"), ctx))
        sortie = RACINE / page.fichier
        sortie.write_text(rendre_page(page, pages, index, contenu), encoding="utf-8")
        print(f"  {page.fichier}")
    print(f"{len(pages)} pages générées.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(construire())
    except ErreurSource as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        sys.exit(1)
