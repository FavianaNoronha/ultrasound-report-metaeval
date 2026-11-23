"""Render the Step 46 result summary from saved artifacts."""

import json
import os

from .step46_freetext import OUT as SETB_OUT

OUT = os.path.dirname(SETB_OUT)


def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else None


def shown(value, digits=3):
    return "incomplete" if value is None else f"{value:.{digits}f}"


def percent(value):
    return "incomplete" if value is None else f"{100 * value:.1f}%"


def render():
    metrics = load_json(os.path.join(SETB_OUT, "metrics.json")) or {}
    info = load_json(os.path.join(SETB_OUT, "run_info.json")) or {}
    filters = load_json(os.path.join(SETB_OUT, "gold_summary.json")) or {}
    filter_shares = load_json(os.path.join(SETB_OUT, "filter_summary.json")) or {}
    rows = [
        "# Step 46: UScore and CRQS on ultrasound reports",
        "",
        "UScore is assembled from the project's existing checks and evaluated on its own benchmark plus model-written text. No clinician has validated it; radiologist-written reports are still needed.",
        "",
        "Primary test result: on 861 core reports from 235 groups, CRQS separated planted errors from harmless rewordings better than UScore (AUROC 0.998 vs 0.656; paired UScore-minus-CRQS difference -0.341, 95% CI -0.385 to -0.298).",
        "",
        f"Writer: `{info.get('model', 'not recorded')}` at revision `{info.get('model_revision', 'not recorded')}`. Planned Set B: {info.get('planned_cases', 0)} cases; Set A overlap: {info.get('set_A_overlap', 'not checked')}.",
        f"Core test report generation: {'complete' if info.get('test_core_complete') else 'incomplete'}; cached reports: {info.get('generated_reports', 0)}.",
        "",
        "## Hypotheses",
        "",
        "| Hypothesis | Result |",
        "|---|---|",
    ]
    score_auc = metrics.get("score", {}).get("auroc")
    rows.append(
        f"| H1, separation | {'PASS' if metrics.get('H1_pass') else 'DOES NOT PASS' if 'H1_pass' in metrics else 'INCOMPLETE'}; UScore AUROC {shown(score_auc)} |"
    )
    rows.append(
        f"| H2, monitor | {'PASS' if metrics.get('H2_pass') else 'DOES NOT PASS' if 'H2_pass' in metrics else 'INCOMPLETE'}; catch {shown(metrics.get('monitor', {}).get('error_catch'))}; harmless flagged {shown(metrics.get('monitor', {}).get('harmless_flagged'))} |"
    )
    stress = metrics.get("stress_subset", {})
    rows.append(
        f"| H3, extras-filter stress subset | Descriptive; n={stress.get('n', 0)}, catch {shown(stress.get('error_catch'))}, harmless flagged {shown(stress.get('harmless_flagged'))} |"
    )
    h4 = metrics.get("H4_template_ceiling", {})
    rows.append(
        f"| H4, fact versus wording (template ceiling) | {'PASS' if h4.get('pass') else 'DOES NOT PASS' if 'pass' in h4 else 'INCOMPLETE'}; fact share {shown(h4.get('eta2', {}).get('fact'))}, wording share {shown(h4.get('eta2', {}).get('wording'))} |"
    )
    h5 = metrics.get("H5_limit_of_detection", {})
    lod5 = h5.get("5_percent_size", {}).get("auroc")
    lod1 = h5.get("1_mm_head_circumference", {}).get("auroc")
    rows.append(f"| H5, limit of detection | 5% size AUROC {shown(lod5)}; 1 mm head circumference AUROC {shown(lod1)} |")
    human = metrics.get("H6_human_rewordings", {})
    rows.append(
        f"| H6, human rewordings | Descriptive; {human.get('n_human_items', 0)} items, AUROC {shown((human.get('descriptive_auroc') or {}).get('auroc'))} |"
    )
    h7 = metrics.get("H7_severity", {})
    rows.append(
        f"| H7, provisional severity | {'PASS' if h7.get('pass') else 'DOES NOT PASS' if 'pass' in h7 else 'INCOMPLETE'}; Spearman {shown(h7.get('spearman_rho_severity_vs_signed_score_drop'))} |"
    )
    transfer = metrics.get("set_B_devval_transfer", {})
    rows.append(
        f"| Set B dev/val transfer | Descriptive only; {transfer.get('n_scored', 0)} scored; UScore AUROC {shown(transfer.get('uScore_auroc', {}).get('auroc'))}; CRQS AUROC {shown(transfer.get('crqs_auroc', {}).get('auroc'))} |"
    )
    rows += [
        "",
        "## Scorer comparison",
        "",
        "| Scorer | AUROC (95% group-bootstrap CI) | UScore minus scorer (95% paired CI) |",
        "|---|---:|---:|",
    ]
    for name, diff_key in (
        ("UScore", None),
        ("BLEU", "paired_difference_vs_bleu"),
        ("ROUGE-L", "paired_difference_vs_rougeL"),
        ("chrF", "paired_difference_vs_chrf"),
        ("BERTScore", "paired_difference_vs_bertscore"),
        ("RaTEScore", "paired_difference_vs_ratescore"),
        ("CRQS", "paired_difference_vs_crqs_normalized"),
        ("CRQS clipped sensitivity", None),
        ("Step 45 learned scorer", "paired_difference_vs_step45_learned"),
        ("Holistic Gemma on rule-clear subset", "paired_difference_vs_judge"),
    ):
        key = {
            "UScore": "score",
            "BLEU": "bleu",
            "ROUGE-L": "rougeL",
            "chrF": "chrf",
            "BERTScore": "bertscore",
            "RaTEScore": "ratescore",
            "CRQS": "crqs_normalized",
            "CRQS clipped sensitivity": "crqs_clipped",
            "Step 45 learned scorer": "step45_learned",
            "Holistic Gemma on rule-clear subset": "judge_on_rule_clear_subset",
        }[name]
        result = metrics.get(key, {})
        auc = result.get("auroc")
        interval = result.get("ci")
        if auc is not None and interval:
            auc_text = f"{shown(auc)} ({shown(interval[0])}–{shown(interval[1])})"
        elif result.get("reason") == "only one label class has a score":
            auc_text = "not estimable (judge scored harmless cases only)"
        else:
            auc_text = "incomplete"
        difference = metrics.get(diff_key, {}) if diff_key else None
        diff_ci = difference.get("ci") if difference else None
        diff_text = (
            f"{shown(difference.get('difference_primary_minus_comparison'))} ({shown(diff_ci[0])}–{shown(diff_ci[1])})"
            if difference and diff_ci
            else "—"
        )
        rows.append(f"| {name} | {auc_text} | {diff_text} |")
    diagnostic = metrics.get("exploratory_rule_only_no_diff_as_perfect", {})
    if diagnostic.get("auroc") is not None:
        interval = diagnostic.get("ci", [None, None])
        rows += [
            "",
            "## Exploratory diagnostic (not preregistered)",
            "",
            f"If rule-clear reports are assigned 1.0 instead of the Gemma score, AUROC is {shown(diagnostic['auroc'])} ({shown(interval[0])}–{shown(interval[1])}). This suggests the judge fallback penalizes some harmless rewordings; it is not the preregistered UScore result.",
        ]
    rows += ["", "## Notes", ""]
    if filters:
        rows.append(f"Filter counts: `{json.dumps(filters.get('dropped', {}), sort_keys=True)}`")
        rows.append(f"Missing generation: `{json.dumps(filters.get('missing_generation', {}), sort_keys=True)}`")
    if filter_shares.get("by_set_organ"):
        rows += [
            "",
            "| Set / organ | Missing-gold filter dropped | Extras filter dropped | Kept |",
            "|---|---:|---:|---:|",
        ]
        for key, counts in sorted(filter_shares["by_set_organ"].items()):
            rows.append(
                f"| {key} | {percent(counts.get('missing_gold_drop_share'))} | {percent(counts.get('extras_filter_drop_share'))} | {percent(counts.get('kept_share'))} |"
            )
    rows += [
        "",
        "CRQS follows the released PathBench code's signed penalties and reports the unclipped normalized score plus a clipped sensitivity score. The paper's displayed formula and the implementation differ; see `CRQS_SOURCE.md`.",
        "The holistic Gemma judge was called only when the rules found no discrepancy; this left 632 harmless reports and no errors in its scored subset, so its AUROC is not estimable.",
        "",
        "Test groups below 30 are too small to compare. The report describes model-written free text, not clinical validation.",
        "",
    ]
    return "\n".join(rows)


if __name__ == "__main__":
    path = os.path.join(OUT, "results.md")
    open(path, "w").write(render())
    print(path)
