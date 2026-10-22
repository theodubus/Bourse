// Comportements propres au site : infobulle des graphiques et encadrés au clavier.
// Les écouteurs sont posés sur le document, car webpage.js remplace le contenu
// de la page à chaque navigation.
// webpage.js appelle setupScroll(), qui était définie dans un fichier absent de
// l'export : sans cette fonction vide, l'initialisation s'interrompt sur une erreur.
if (typeof window.setupScroll !== "function") window.setupScroll = function () {};

(function () {
  "use strict";

  function points(svg) {
    if (!svg._points) svg._points = JSON.parse(svg.dataset.points);
    return svg._points;
  }

  function afficher(svg, index) {
    var liste = points(svg);
    index = Math.max(0, Math.min(liste.length - 1, index));
    svg._index = index;
    var p = liste[index];

    var repere = svg.querySelector(".chart-crosshair");
    repere.setAttribute("x1", p[0]);
    repere.setAttribute("x2", p[0]);
    repere.style.visibility = "visible";
    var point = svg.querySelector(".chart-focus");
    point.setAttribute("cx", p[0]);
    point.setAttribute("cy", p[1]);
    point.style.visibility = "visible";

    var figure = svg.closest(".chart");
    var bulle = figure.querySelector(".chart-tooltip");
    bulle.querySelector(".chart-tooltip-valeur").textContent = p[3];
    bulle.querySelector(".chart-tooltip-libelle").textContent = p[2];
    bulle.hidden = false;

    var matrice = svg.getScreenCTM();
    var cadre = figure.getBoundingClientRect();
    var demiLargeur = bulle.offsetWidth / 2;
    var x = matrice.a * p[0] + matrice.e - cadre.left;
    x = Math.max(demiLargeur, Math.min(cadre.width - demiLargeur, x));
    bulle.style.left = x + "px";
    bulle.style.top = matrice.d * p[1] + matrice.f - cadre.top + "px";
  }

  function masquer(svg) {
    svg.querySelector(".chart-crosshair").style.visibility = "";
    svg.querySelector(".chart-focus").style.visibility = "";
    svg.closest(".chart").querySelector(".chart-tooltip").hidden = true;
  }

  function indexLePlusProche(svg, clientX) {
    var matrice = svg.getScreenCTM();
    var x = (clientX - matrice.e) / matrice.a;
    var liste = points(svg);
    var meilleur = 0;
    for (var i = 1; i < liste.length; i++) {
      if (Math.abs(liste[i][0] - x) < Math.abs(liste[meilleur][0] - x)) meilleur = i;
    }
    return meilleur;
  }

  function graphique(cible) {
    return cible && cible.closest ? cible.closest(".chart svg") : null;
  }

  document.addEventListener("pointermove", function (e) {
    var svg = graphique(e.target);
    if (svg) afficher(svg, indexLePlusProche(svg, e.clientX));
  });

  document.addEventListener("pointerout", function (e) {
    var svg = graphique(e.target);
    if (svg && !svg.contains(e.relatedTarget) && document.activeElement !== svg) masquer(svg);
  });

  document.addEventListener("focusin", function (e) {
    var svg = graphique(e.target);
    if (svg) afficher(svg, svg._index == null ? points(svg).length - 1 : svg._index);
  });

  document.addEventListener("focusout", function (e) {
    var svg = graphique(e.target);
    if (svg) masquer(svg);
  });

  document.addEventListener("keydown", function (e) {
    var svg = graphique(e.target);
    if (svg && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
      e.preventDefault();
      var courant = svg._index == null ? points(svg).length - 1 : svg._index;
      afficher(svg, courant + (e.key === "ArrowRight" ? 1 : -1));
      return;
    }
    var titre = e.target.closest && e.target.closest('.callout-title[role="button"]');
    if (titre && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      titre.click();
    }
  });

  // webpage.js replie/déplie l'encadré ; on tient aria-expanded à jour.
  document.addEventListener("click", function (e) {
    var titre = e.target.closest && e.target.closest('.callout-title[role="button"]');
    if (titre) {
      var replie = titre.parentElement.classList.contains("is-collapsed");
      titre.setAttribute("aria-expanded", replie ? "false" : "true");
    }
  });
})();
