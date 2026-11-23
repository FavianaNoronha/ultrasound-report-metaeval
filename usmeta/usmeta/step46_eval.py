"""Step 46 evaluation on the held-out Llama-written set B."""

import collections
import json
import os
import time

import numpy as np
from sklearn.metrics import roc_auc_score

from . import extract, graders, schema, step45_extractor_v5 as v5, step45_numchecker as nc
from . import step45_gemma as gemma
from . import step45_partE as part_e
from . import step45_freetext as set_a
from . import step46_freetext as set_b


OUT = set_b.OUT
P = lambda filename: os.path.join(OUT, filename)
MAX_HARMLESS = 0.056
PENALTY = {"critical": 0.6, "major": 0.3, "minor": 0.1}


def candidates(split="test"):
    data = json.load(open(P("set_B.json")))
    rows = []
    for case_id, case in data["cases"].items():
        if case.get("set") != split:
            continue
        for report in case["true_reports"]:
            rows.append(
                dict(
                    id=f"{case_id}|true|{report['style']}",
                    case=case_id,
                    group=case["group"],
                    organ=case["organ"],
                    dataset=case["dataset"],
                    kind="harmless",
                    severity=None,
                    ref=case["reference"],
                    gold=case["gold"],
                    cand=report["text"],
                )
            )
        if case["twin_report"]:
            report = case["twin_report"]
            rows.append(
                dict(
                    id=f"{case_id}|twin|{report['style']}",
                    case=case_id,
                    group=case["group"],
                    organ=case["organ"],
                    dataset=case["dataset"],
                    kind="error",
                    severity=case["twin_severity"],
                    ref=case["reference"],
                    gold=case["gold"],
                    cand=report["text"],
                )
            )
    for item in data.get("lod", []):
        case = data["cases"][item["case_id"]]
        if case.get("set") != split:
            continue
        rows.append(
            dict(
                id=item["id"],
                case=item["case_id"],
                group=case["group"],
                organ=case["organ"],
                dataset=case["dataset"],
                kind="lod",
                severity=None,
                ref=case["reference"],
                gold=case["gold"],
                cand=item["text"],
                field=item.get("field"),
                level=item.get("level"),
                old=item.get("old"),
                new=item.get("new"),
            )
        )
    return rows


def stress_candidates():
    path = P("stress_reports.json")
    if not os.path.exists(path):
        return []
    cases = json.load(open(P("cases.json")))
    rows = []
    for report in json.load(open(path)):
        if report.get("set") != "test":
            continue
        case = cases[report["case_id"]]
        rows.append(
            dict(
                id=f"stress|{report['id']}",
                case=report["case_id"],
                group=case["group"],
                organ=report["organ"],
                dataset=case["dataset"],
                kind="error" if report["kind"] in ("twin", "lod") else "harmless",
                severity=case.get("twin_severity") if report["kind"] == "twin" else None,
                ref=case["reference"],
                gold=case["gold"],
                cand=report["text"],
            )
        )
    return rows


def human_candidates():
    path = os.path.join(
        set_a.ROOT, "results", "partA", "step21d_human_sheet", "human_bench.jsonl"
    )
    rows = []
    for line in open(path):
        report = json.loads(line)
        if report.get("kind") != "human":
            continue
        organ = "fetal" if report["organ"] == "fetal head" else report["organ"]
        rows.append(
            dict(
                id=f"human|{report['item']}|{report['case_id']}",
                case=report["case_id"],
                group=report["case_id"],
                organ=organ,
                dataset=report["dataset"],
                kind="human",
                severity=None,
                ref=report["reference"],
                gold=schema.extract_rule(report["reference"], organ),
                cand=report["candidate"],
            )
        )
    return rows


def rule_result(row, flat):
    differences = {}
    numeric = nc.compare(row["ref"], row["cand"], row["organ"])
    for key, value in numeric.items():
        if value is None or value is False:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0:
            continue
        field = key.removesuffix("_rel").removesuffix("_mismatch")
        if field == "hc_abs_mm":
            field = "hc_mm"
        differences[field] = "number_checker"
    fields = v5.match_report(row["organ"], row["gold"], flat, row["cand"])
    for field, matched in fields.items():
        if not matched:
            differences.setdefault(field, "extractor_v5")
    expected = (
        row["gold"]
        if row["gold"].get("lesion") != "absent"
        else {key: value for key, value in row["gold"].items() if key in ("lesion", "birads", "path")}
    )
    for field in v5.FIELDS[row["organ"]]:
        if expected.get(field) is not None or flat.get(field) is None:
            continue
        try:
            stated = set_a.check_field(row["organ"], field, flat[field], row["cand"])
        except Exception:
            stated = False
        if stated:
            differences.setdefault(field, "extractor_v5_extra")
    return differences


def severity_for(organ, field, row):
    if row.get("severity") in (1, 2, 3):
        return {1: "minor", 2: "major", 3: "critical"}[row["severity"]]
    field = {"hc_mm": "hc", "size_mm": "size", "size_pct": "size", "lesion": "path"}.get(field, field)
    weight = extract.WEIGHTS.get(organ, {}).get(field, 1)
    return "critical" if weight >= 3 else "major" if weight == 2 else "minor"


def primary_score(row, flat, judge_score=None):
    differences = rule_result(row, flat)
    if not differences:
        return judge_score, differences
    penalty = sum(PENALTY[severity_for(row["organ"], field, row)] for field in differences)
    return max(0.0, 1.0 - penalty), differences


def crqs_score(row, flat):
    reference = {
        key: value
        for key, value in row["gold"].items()
        if value is not None and str(value).strip()
    }
    candidate = {
        key: value
        for key, value in flat.items()
        if value is not None and str(value).strip()
    }
    keys = set(reference) | set(candidate)
    matches = {
        key: key in reference
        and key in candidate
        and v5.vmatch(key, candidate[key], reference[key])
        for key in keys
    }
    clinical_coverage = sum(matches[key] for key in reference) / len(reference) if reference else 0.0
    key_fields = {
        "breast": ("path", "birads", "size_mm", "size_pct"),
        "thyroid": ("tirads", "size_mm", "size_pct", "comp"),
        "fetal": ("hc_mm", "plane"),
    }[row["organ"]]
    key_reference = [key for key in key_fields if key in reference]
    key_recall = sum(matches[key] for key in key_reference) / len(key_reference) if key_reference else 0.0
    unsupported = sum(key not in reference for key in candidate)
    hallucination = unsupported / len(candidate) if candidate else 0.0
    comparable_key_fields = set(key_reference) & set(candidate)
    discordance = float(any(not matches[key] for key in comparable_key_fields))
    raw = 0.3 * clinical_coverage + 0.4 * key_recall - 0.2 * hallucination - 0.4 * discordance
    normalized = raw / 0.7
    return {
        "CFC": clinical_coverage,
        "KIR": key_recall,
        "HR": hallucination,
        "CDS": discordance,
        "raw": raw,
        "normalized": normalized,
        "clipped": min(1.0, max(0.0, normalized)),
    }


def grouped_auc(rows, score_name, score_key="score", seed=0, draws=1000):
    complete = [row for row in rows if row.get(score_key) is not None and row["kind"] in ("error", "harmless")]
    groups = sorted({row["group"] for row in complete})
    if len(groups) < 30:
        return {"n": len(complete), "groups": len(groups), "too_small_to_compare": True}
    if len({row["kind"] for row in complete}) < 2:
        return {
            "n": len(complete),
            "groups": len(groups),
            "too_small_to_compare": True,
            "reason": "only one label class has a score",
        }
    rng = np.random.default_rng(seed)
    point = roc_auc_score(
        [row["kind"] == "error" for row in complete],
        [-row[score_key] for row in complete],
    )
    by_group = {group: [row for row in complete if row["group"] == group] for group in groups}
    samples = []
    for _ in range(draws):
        selected = rng.choice(groups, size=len(groups), replace=True)
        boot = [row for group in selected for row in by_group[group]]
        if len({row["kind"] for row in boot}) == 2:
            samples.append(
                roc_auc_score(
                    [row["kind"] == "error" for row in boot],
                    [-row[score_key] for row in boot],
                )
            )
    return {
        "n": len(complete),
        "groups": len(groups),
        "auroc": float(point),
        "ci": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
        "seed": seed,
        "draws": draws,
        "too_small_to_compare": False,
    }


def paired_auc_difference(rows, comparison_key, primary_key="score", seed=0, draws=1000):
    paired = [
        row
        for row in rows
        if row.get(primary_key) is not None
        and row.get(comparison_key) is not None
        and row["kind"] in ("error", "harmless")
    ]
    groups = sorted({row["group"] for row in paired})
    if len(groups) < 30:
        return {"n": len(paired), "groups": len(groups), "too_small_to_compare": True}
    if len({row["kind"] for row in paired}) < 2:
        return {
            "n": len(paired),
            "groups": len(groups),
            "too_small_to_compare": True,
            "reason": "only one label class has a paired score",
        }
    rng = np.random.default_rng(seed)
    by_group = {group: [row for row in paired if row["group"] == group] for group in groups}

    def difference(sample):
        labels = [row["kind"] == "error" for row in sample]
        primary_auc = roc_auc_score(labels, [-row[primary_key] for row in sample])
        comparison_auc = roc_auc_score(labels, [-row[comparison_key] for row in sample])
        return primary_auc - comparison_auc

    point = difference(paired)
    samples = []
    for _ in range(draws):
        selected = rng.choice(groups, size=len(groups), replace=True)
        boot = [row for group in selected for row in by_group[group]]
        if len({row["kind"] for row in boot}) == 2:
            samples.append(difference(boot))
    return {
        "n": len(paired),
        "groups": len(groups),
        "difference_primary_minus_comparison": float(point),
        "ci": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
        "seed": seed,
        "draws": draws,
        "too_small_to_compare": False,
    }


def h4_ceiling():
    path = os.path.join(set_a.ROOT, "results", "partA", "step33_factorial", "test_blocks.json")
    blocks = json.load(open(path))["blocks"]
    cell_values = []
    for block in blocks:
        ref_facts = schema.extract_rule(block["ref"], block["organ"])
        row = dict(
            ref=block["ref"],
            gold=ref_facts,
            organ=block["organ"],
            severity=block["severity"],
        )
        a_values = []
        for text in block["a_texts"]:
            row["cand"] = text
            value, _ = primary_score(row, schema.extract_rule(text, block["organ"]))
            a_values.append(1.0 if value is None else value)
        row["cand"] = block["b_text"]
        b_value, _ = primary_score(row, schema.extract_rule(block["b_text"], block["organ"]))
        row["cand"] = block["c_text"]
        c_value, _ = primary_score(row, schema.extract_rule(block["c_text"], block["organ"]))
        row["cand"] = block["d_text"]
        d_value, _ = primary_score(row, schema.extract_rule(block["d_text"], block["organ"]))
        cell_values.append(
            dict(
                group=block["group"],
                a=float(np.mean(a_values)),
                b=1.0 if b_value is None else b_value,
                c=1.0 if c_value is None else c_value,
                d=1.0 if d_value is None else d_value,
            )
        )

    def decomposition(rows, weights=None):
        values = {key: np.asarray([row[key] for row in rows], dtype=float) for key in ("a", "b", "c", "d")}
        weights = np.ones(len(rows)) if weights is None else np.asarray(weights, dtype=float)
        total_weight = weights.sum()
        means = {key: float(np.average(value, weights=weights)) for key, value in values.items()}
        grand = sum(means.values()) / 4
        fact_yes = (means["c"] + means["d"]) / 2
        fact_no = (means["a"] + means["b"]) / 2
        wording_yes = (means["b"] + means["d"]) / 2
        wording_no = (means["a"] + means["c"]) / 2
        total = sum(float((weights * (value - grand) ** 2).sum()) for value in values.values())
        if total == 0 or not total_weight:
            return None
        fact_ss = 2 * total_weight * ((fact_yes - grand) ** 2 + (fact_no - grand) ** 2)
        wording_ss = 2 * total_weight * ((wording_yes - grand) ** 2 + (wording_no - grand) ** 2)
        interaction_ss = total_weight * sum(
            (means[cell] - fact - wording + grand) ** 2
            for cell, fact, wording in (
                ("a", fact_no, wording_no),
                ("b", fact_no, wording_yes),
                ("c", fact_yes, wording_no),
                ("d", fact_yes, wording_yes),
            )
        )
        return {
            "fact": fact_ss / total,
            "wording": wording_ss / total,
            "interaction": interaction_ss / total,
            "residual": max(0.0, 1.0 - (fact_ss + wording_ss + interaction_ss) / total),
        }

    estimate = decomposition(cell_values)
    groups = sorted({row["group"] for row in cell_values})
    rng = np.random.default_rng(0)
    boot = []
    for _ in range(1000):
        chosen = rng.choice(groups, size=len(groups), replace=True)
        counts = collections.Counter(chosen)
        weights = [counts[row["group"]] for row in cell_values]
        result = decomposition(cell_values, weights)
        if result:
            boot.append(result)
    intervals = {
        key: [float(np.quantile([row[key] for row in boot], 0.025)), float(np.quantile([row[key] for row in boot], 0.975))]
        for key in ("fact", "wording")
    }
    return {
        "n_blocks": len(cell_values),
        "groups": len(groups),
        "eta2": estimate,
        "ci": intervals,
        "fact_share_ge_0_60": bool(estimate and estimate["fact"] >= 0.60),
        "wording_share_le_0_05": bool(estimate and estimate["wording"] <= 0.05),
        "pass": bool(estimate and estimate["fact"] >= 0.60 and estimate["wording"] <= 0.05),
        "interpretation": "template-only ceiling using the project's deterministic fact extractor; not free-text evidence",
    }


def set_a_tuning_rows():
    set_a_cases_path = os.path.join(
        set_a.ROOT,
        "results",
        "partA",
        "step45_improve_scorers",
        "freetext",
        "set_A.json",
    )
    cases = json.load(open(set_a_cases_path))["cases"]
    extraction = json.load(
        open(
            os.path.join(
                set_a.ROOT,
                "results",
                "partA",
                "step45_improve_scorers",
                "extractor",
                "extraction_v5_devval.json",
            )
        )
    )
    judge_rows = []
    judge_path = os.path.join(
        set_a.ROOT,
        "results",
        "partA",
        "step45_improve_scorers",
        "gemma",
        "f_holistic.jsonl",
    )
    for line in open(judge_path):
        item = json.loads(line)
        if item["set"] != "devval" or item["result"] is None:
            continue
        case_id = item["id"].split("|")[0]
        case = cases.get(case_id)
        if not case:
            continue
        texts = {
            f"{case_id}|true|{report['style']}": report["text"]
            for report in case["true_reports"]
        }
        if case["twin_report"]:
            texts[
                f"{case_id}|twin|{case['twin_report']['style']}"
            ] = case["twin_report"]["text"]
        if item["id"] not in texts or item["id"] not in extraction:
            continue
        judge_rows.append(
            dict(
                set="devval",
                id=item["id"],
                case=case_id,
                group=case["group"],
                organ=case["organ"],
                kind=item["kind"],
                ref=case["reference"],
                cand=texts[item["id"]],
                gold=case["gold"],
                flat=extraction[item["id"]]["flat"],
                judge=item["result"]["judge"],
            )
        )
    return judge_rows


def tune_threshold():
    rows = set_a_tuning_rows()
    scored = []
    for row in rows:
        score, _ = primary_score(row, row["flat"], row["judge"])
        scored.append((row, score))
    harmless = [score for row, score in scored if row["kind"] == "harmless"]
    errors = [score for row, score in scored if row["kind"] == "error"]
    if not harmless or not errors:
        raise RuntimeError("Set A dev/val tuning pairs are unavailable")
    thresholds = sorted(set(harmless + errors)) + [max(harmless + errors) + 1e-9]
    eligible = [
        threshold
        for threshold in thresholds
        if np.mean([score < threshold for score in harmless]) <= MAX_HARMLESS
    ]
    threshold = max(
        eligible,
        key=lambda value: (
            np.mean([score < value for score in errors]),
            value,
        ),
    )
    return {
        "threshold": threshold,
        "n_harmless": len(harmless),
        "n_errors": len(errors),
        "harmless_flagged": float(np.mean([score < threshold for score in harmless])),
        "error_catch": float(np.mean([score < threshold for score in errors])),
        "source": "Step 45 Set A dev/val only",
    }


def run_judge(args):
    extraction = json.load(open(P("extraction_v5.json")))
    done = {}
    if os.path.exists(P("judge.jsonl")):
        for line in open(P("judge.jsonl")):
            item = json.loads(line)
            done[item["id"]] = item
    rows = candidates("test") + candidates("devval") + stress_candidates() + human_candidates()
    runner = gemma.Runner()
    deadline = time.time() + args.max_hours * 3600
    with open(P("judge.jsonl"), "a") as output:
        for index, row in enumerate(rows, 1):
            if row["id"] in done or row["id"] not in extraction:
                continue
            flat = extraction[row["id"]]["flat"]
            differences = rule_result(row, flat)
            if differences:
                continue
            if time.time() >= deadline:
                print("judge cap reached", index, "of", len(rows), flush=True)
                break
            result = runner.holistic(row["ref"], row["cand"])
            output.write(json.dumps({"id": row["id"], "result": result}) + "\n")
            output.flush()
            done[row["id"]] = {"id": row["id"], "result": result}
            if index % 25 == 0:
                print("judge", index, len(rows), flush=True)


def run_score(args):
    extraction = json.load(open(P("extraction_v5.json")))
    judge = {}
    if os.path.exists(P("judge.jsonl")):
        for line in open(P("judge.jsonl")):
            item = json.loads(line)
            judge[item["id"]] = item["result"]
    threshold = tune_threshold()
    rows = candidates("test")
    scores = []
    for row in rows:
        if row["id"] not in extraction:
            continue
        flat = extraction[row["id"]]["flat"]
        result = judge.get(row["id"])
        judge_value = result.get("judge") if result else None
        score, differences = primary_score(row, flat, judge_value)
        if score is None:
            continue
        scores.append(
            dict(
                row,
                score=score,
                differences=differences,
                judge=judge_value,
                flagged=score < threshold["threshold"],
                crqs=crqs_score(row, flat),
            )
        )
    if args.metrics:
        specs = {
            "bleu": "bleu",
            "rougeL": "rougeL",
            "chrf": "chrf",
            "bertscore": "bertscore:roberta-large",
            "ratescore": "ratescore",
        }
        references = [row["ref"] for row in scores]
        candidates_text = [row["cand"] for row in scores]
        for key, spec in specs.items():
            metric = graders.make(spec)
            values = (
                metric.batch(references, candidates_text)
                if hasattr(metric, "batch")
                else [metric.score(ref, cand) for ref, cand in zip(references, candidates_text)]
            )
            for row, value in zip(scores, values):
                row[key] = float(value)
            print("scored", key, len(values), flush=True)
        for row in scores:
            row["crqs_normalized"] = row["crqs"]["normalized"]
            row["crqs_clipped"] = row["crqs"]["clipped"]
        metric_scores = {
            key: grouped_auc(scores, key, key)
            for key in (*specs.keys(), "score", "crqs_normalized", "crqs_clipped")
        }
        exploratory_rows = [
            dict(
                row,
                exploratory_score=1.0 if not row["differences"] else row["score"],
            )
            for row in scores
        ]
        metric_scores["exploratory_rule_only_no_diff_as_perfect"] = grouped_auc(
            exploratory_rows, "exploratory_score", "exploratory_score"
        )
        set_a_models = os.path.join(
            set_a.ROOT,
            "results",
            "partA",
            "step45_improve_scorers",
            "partE",
            "models.pkl",
        )
        if os.path.exists(set_a_models):
            import pickle

            learned = pickle.load(open(set_a_models, "rb"))["logreg"]
            vectors = []
            for row in scores:
                feature_scores = {
                    "bleu": row["bleu"],
                    "rougeL": row["rougeL"],
                    "chrf": row["chrf"],
                    "bertscore[roberta-large]": row["bertscore"],
                    "ratescore": row["ratescore"],
                }
                vectors.append(part_e.vec(feature_scores, row["ref"], row["cand"], row["organ"]))
            score_values = 1.0 - learned.predict_proba(np.asarray(vectors, dtype=float))[:, 1]
            for row, value in zip(scores, score_values):
                row["step45_learned"] = float(value)
            metric_scores["step45_learned"] = grouped_auc(scores, "step45_learned", "step45_learned")
        else:
            metric_scores["step45_learned"] = {"status": "missing frozen Step 45 E model"}
        judge_rows = [row for row in scores if row.get("judge") is not None]
        if judge_rows:
            metric_scores["judge_on_rule_clear_subset"] = grouped_auc(judge_rows, "judge", "judge")
        comparisons = {
            "bleu": "bleu",
            "rougeL": "rougeL",
            "chrf": "chrf",
            "bertscore": "bertscore",
            "ratescore": "ratescore",
            "crqs_normalized": "crqs_normalized",
            "step45_learned": "step45_learned",
        }
        for name, key in comparisons.items():
            metric_scores["paired_difference_vs_" + name] = paired_auc_difference(scores, key)
        if judge_rows:
            metric_scores["paired_difference_vs_judge"] = paired_auc_difference(judge_rows, "judge")
        threshold_flags = [row for row in scores if row["kind"] in ("error", "harmless")]
        metric_scores["monitor"] = {
            "error_catch": float(np.mean([row["flagged"] for row in threshold_flags if row["kind"] == "error"])) if any(row["kind"] == "error" for row in threshold_flags) else None,
            "harmless_flagged": float(np.mean([row["flagged"] for row in threshold_flags if row["kind"] == "harmless"])) if any(row["kind"] == "harmless" for row in threshold_flags) else None,
        }
        metric_scores["H1_pass"] = bool(
            metric_scores["score"].get("auroc", -1.0) >= 0.90
            and all(
                metric_scores.get("paired_difference_vs_" + name, {}).get("ci", [0, 0])[0] > 0
                for name in (*comparisons.keys(), "judge")
            )
        )
        metric_scores["H2_pass"] = bool(
            metric_scores["monitor"]["error_catch"] is not None
            and metric_scores["monitor"]["error_catch"] >= 0.80
            and metric_scores["monitor"]["harmless_flagged"] is not None
            and metric_scores["monitor"]["harmless_flagged"] <= MAX_HARMLESS
        )
        stress_scores = []
        for row in stress_candidates():
            if row["id"] not in extraction:
                continue
            flat = extraction[row["id"]]["flat"]
            result = judge.get(row["id"])
            value, differences = primary_score(
                row, flat, result.get("judge") if result else None
            )
            if value is not None:
                stress_scores.append(
                    dict(row, score=value, flagged=value < threshold["threshold"], differences=differences)
                )
        metric_scores["stress_subset"] = {
            "n": len(stress_scores),
            "error_catch": float(
                np.mean([row["flagged"] for row in stress_scores if row["kind"] == "error"])
            ) if any(row["kind"] == "error" for row in stress_scores) else None,
            "harmless_flagged": float(
                np.mean([row["flagged"] for row in stress_scores if row["kind"] == "harmless"])
            ) if any(row["kind"] == "harmless" for row in stress_scores) else None,
        }
        lod_rows = [row for row in scores if row["kind"] == "lod"]
        base_scores = collections.defaultdict(list)
        for row in scores:
            if row["kind"] == "harmless":
                base_scores[row["case"]].append(row["score"])
        lod_checks = {}
        for name, matches in (
            ("5_percent_size", lambda row: row.get("field") in ("size_mm", "size_pct") and row.get("level") == 0.05),
            ("1_mm_head_circumference", lambda row: row.get("field") == "hc_mm" and row.get("level") == 1),
        ):
            samples = []
            for row in lod_rows:
                if not matches(row) or row["case"] not in base_scores:
                    continue
                reference_score = float(np.mean(base_scores[row["case"]]))
                samples.append(
                    dict(
                        id=row["id"],
                        case=row["case"],
                        group=row["group"],
                        kind="error",
                        score=row["score"],
                    )
                )
                samples.append(
                    dict(
                        id=row["id"] + "|reference",
                        case=row["case"],
                        group=row["group"],
                        kind="harmless",
                        score=reference_score,
                    )
                )
            lod_checks[name] = grouped_auc(samples, "score", "score")
        metric_scores["H5_limit_of_detection"] = lod_checks
        severity_rows = [
            row
            for row in scores
            if row["kind"] == "error" and row.get("severity") in (1, 2, 3)
        ]
        if len(severity_rows) >= 3:
            from scipy.stats import spearmanr

            severity_rho, severity_p = spearmanr(
                [row["severity"] for row in severity_rows],
                [row["score"] - 1.0 for row in severity_rows],
            )
            metric_scores["H7_severity"] = {
                "n": len(severity_rows),
                "groups": len({row["group"] for row in severity_rows}),
                "spearman_rho_severity_vs_signed_score_drop": float(severity_rho),
                "p_value_descriptive": float(severity_p),
                "pass": bool(severity_rho <= -0.3),
            }
        else:
            metric_scores["H7_severity"] = {"n": len(severity_rows), "too_few": True}
        human_scored = []
        for row in human_candidates():
            if row["id"] not in extraction:
                continue
            flat = extraction[row["id"]]["flat"]
            result = judge.get(row["id"])
            value, differences = primary_score(
                row, flat, result.get("judge") if result else None
            )
            if value is not None:
                human_scored.append(
                    dict(row, score=value, flagged=value < threshold["threshold"], differences=differences)
                )
        human_auc_rows = [
            dict(row, group="human:" + row["group"], kind="harmless")
            for row in human_scored
        ] + [row for row in scores if row["kind"] == "error"]
        metric_scores["H6_human_rewordings"] = {
            "n_human_items": len(human_scored),
            "n_error_items": sum(row["kind"] == "error" for row in human_auc_rows),
            "human_flagged_share": float(np.mean([row["flagged"] for row in human_scored])) if human_scored else None,
            "descriptive_auroc": grouped_auc(human_auc_rows, "score", "score") if human_auc_rows else None,
            "status": "descriptive; 29 human items, too small for comparison",
        }
        metric_scores["H4_template_ceiling"] = h4_ceiling()
        transfer_scores = []
        for row in candidates("devval"):
            if row["id"] not in extraction:
                continue
            flat = extraction[row["id"]]["flat"]
            result = judge.get(row["id"])
            value, differences = primary_score(
                row, flat, result.get("judge") if result else None
            )
            if value is not None:
                transfer_scores.append(
                    dict(
                        row,
                        score=value,
                        crqs_normalized=crqs_score(row, flat)["normalized"],
                        flagged=value < threshold["threshold"],
                        differences=differences,
                    )
                )
        metric_scores["set_B_devval_transfer"] = {
            "n_scored": len(transfer_scores),
            "test_read_for_tuning": False,
            "uScore_auroc": grouped_auc(transfer_scores, "score", "score"),
            "crqs_auroc": grouped_auc(transfer_scores, "crqs", "crqs_normalized"),
            "monitor": {
                "error_catch": float(
                    np.mean([row["flagged"] for row in transfer_scores if row["kind"] == "error"])
                ) if any(row["kind"] == "error" for row in transfer_scores) else None,
                "harmless_flagged": float(
                    np.mean([row["flagged"] for row in transfer_scores if row["kind"] == "harmless"])
                ) if any(row["kind"] == "harmless" for row in transfer_scores) else None,
            },
            "status": "transfer description only; tuning remains Set A dev/val",
        }
        json.dump(metric_scores, open(P("metrics.json"), "w"), indent=1)
    json.dump({"tuning": threshold, "scores": scores}, open(P("scored.json"), "w"), indent=1)
    print("scored", len(scores), "of", len(rows), "threshold", threshold["threshold"], flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("judge", "score"))
    parser.add_argument("--max-hours", type=float, default=3.0)
    parser.add_argument("--metrics", action="store_true")
    options = parser.parse_args()
    {"judge": run_judge, "score": run_score}[options.command](options)
