"""Human-readable and structured reports share the same evidence."""
from __future__ import annotations

import json
from .core import write_json


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown(report):
    lines = ["| Rang | Sujet | Score | Tendance | Concurrence FR | Production |", "| --- | --- | ---: | --- | --- | --- |"]
    for row in report["opportunities"]:
        lines.append("| "+" | ".join(cell(x) for x in (row["rank"], row["subject"], str(row["score"])+"/100", row["trend"], row["competition_fr"], row["production"]))+" |")
    lines += ["", "# Veille YouTube SANDBOX", "", "DÉMONSTRATION SYNTHÉTIQUE." if report["synthetic"] else "Collecte réelle ; aucune statistique simulée.", "",
              "Collecte : "+report["collected_at"]+". Mode : "+report["mode"]+".", "",
              f"{len(report['opportunities'])} opportunité(s) retenue(s) sur {report['requested_count']} demandées. Les sujets insuffisamment documentés restent écartés.", "",
              "Scores heuristiques arrondis, sans prédiction de vues. Critères absents : contribution nulle, sans redistribution de poids. Concurrence : échantillon limité, jamais un recensement.", "",
              "Couverture : "+report["coverage_notice"], "", "Sources et quotas :", ""]
    for name, result in report["source_status"].items():
        lines.append(f"- {name} : {result['status']}, {result.get('count', 0)} observation(s). "+" ; ".join(result.get("errors", [])))
    lines += ["", "Quotas locaux du jour Pacifique : "+json.dumps(report["quota_usage"], ensure_ascii=False)+". Les autres outils du même projet Google ne sont pas comptabilisés ici.", ""]
    for row in report["opportunities"]:
        lines += [f"## {row['rank']}. {row['subject']}", "", "Sujet à expliquer : "+row["subject"]+".", "",
                  f"Pourquoi l'examiner : {len(row['support_origins'])} origines de signaux ; fenêtres 24h/48h/7j : "+json.dumps(row["windows_hours"])+". Ces nombres comptent des éléments, pas des recherches Google.", "",
                  f"Score : {row['score']}/100. Confiance : {row['confidence']}. Couverture des critères : {row['data_coverage_percent']} %.", "",
                  "Contributions : "+json.dumps(row["contributions"], ensure_ascii=False)+". Critères absents : "+", ".join(row["missing_criteria"])+".", "", "Preuves :", ""]
        for evidence in row["evidence"]:
            lines.append(f"- [{cell(evidence['title'])}]({evidence['url']}) ; {evidence['source']}, publication {evidence['published_at'] or 'inconnue'}, collecte {evidence['observed_at']} ; mesures : "+json.dumps(evidence["metrics"], ensure_ascii=False))
        if row["video_metrics"]:
            lines += ["", "Performances des vidéos (moyenne depuis publication, vitesse par intervalle et accélération restent distinctes) :", "", "```json", json.dumps(row["video_metrics"], ensure_ascii=False, indent=2), "```"]
        lines += ["", "Titres de travail à réviser après lecture des sources :", "", *["- "+t for t in row["titles"]], "",
                  "Accroche proposée : "+row["hook"], "", "Concept : "+row["concept"], "", "Miniature : "+row["thumbnail"], "",
                  f"Production estimée : {row['duration_seconds_estimate']} secondes, {row['scene_count_estimate']} séquences. Schémas originaux, titres animés et fondus locaux. "+row["production_basis"]+".", "",
                  "Droits : "+row["rights"], "", row["recommendation"], ""]
    if report["rejected"]:
        lines += ["## Pistes à documenter", "", "Ces pistes ne sont pas des recommandations de production. Leurs preuves restent insuffisantes pour le classement.", ""]
        blocked = {"category_filtered", "outside_ai_tech", "production_too_complex", "recently_recommended_without_material_change"}
        watchlist = sorted((r for r in report["rejected"] if not blocked.intersection(r["reasons"])), key=lambda r: -r["score"])[:5]
        for row in watchlist:
            lines += ["### "+row["subject"], "", "Réserves : "+", ".join(row["reasons"])+".", ""]
            lines += [f"- [{cell(e['title'])}]({e['url']}) ; relevé {e['observed_at']}." for e in row.get("evidence", [])[:5]]
            lines.append("")
        lines += ["## Sujets écartés", "", *["- "+r["subject"]+" : "+", ".join(r["reasons"]) for r in report["rejected"]], ""]
    return "\n".join(lines)


def save_report(store, report):
    directory = store.directory / "reports" / report["run_id"]
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory / "report.json", report)
    (directory / "report.md").write_text(markdown(report), encoding="utf-8")
    store.save_run(report)
    return directory
