"""Step 47 audit-and-route report evaluator.

The three fixed quote-audit prompts live in results/partA/step47_audit_route/
prompts.json. Calls are resumable and cached. This module uses only saved Set B
dev-val data for calibration and saved Set C artifacts for the fresh test.
"""

import collections
import csv
import hashlib
import json
import os
import statistics
import time

import numpy as np
from sklearn.metrics import roc_auc_score

from . import graders, judge2, step46_eval as s46
from . import step47_freetext as set_c


ROOT = set_c.ROOT
OUT = os.path.dirname(set_c.OUT)
P = lambda filename: os.path.join(OUT, filename)
PROMPT_PATH = P("prompts.json")
PROMPTS = json.load(open(PROMPT_PATH))
AUDIT_MODEL = PROMPTS["model"]
PROMPT_KEYS = (
    "prompt_a_reference_first",
    "prompt_a_candidate_first",
    "prompt_b_reference_first",
)
PROMPT_SHA256 = hashlib.sha256(
    json.dumps(PROMPTS, sort_keys=True).encode()
).hexdigest()


def parse_audit(raw):
    if not raw:
        return None
    try:
        text = raw[raw.index("{") : raw.rindex("}") + 1]
        result = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        return None
    verdict = str(result.get("verdict", "")).lower().strip()
    if verdict not in {"clean", "major", "minor", "unsure"}:
        return None
    issues = result.get("issues")
    if not isinstance(issues, list):
        return None
    normalized = []
    for issue in issues:
        if not isinstance(issue, dict):
            return None
        kind = str(issue.get("type", "")).lower().strip()
        severity = str(issue.get("severity", "")).lower().strip()
        if kind not in {"contradicted", "unsupported", "omitted"}:
            return None
        if severity not in {"major", "minor", "unsure"}:
            return None
        normalized.append(
            {
                "candidate_quote": str(issue.get("candidate_quote", "")),
                "reference_quote": str(issue.get("reference_quote", "")),
                "type": kind,
                "severity": severity,
                "reason": str(issue.get("reason", "")),
            }
        )
    if verdict == "clean" and normalized:
        return None
    if verdict == "major" and not any(issue["severity"] == "major" for issue in normalized):
        return None
    if verdict == "minor" and not any(issue["severity"] == "minor" for issue in normalized):
        return None
    return {"verdict": verdict, "issues": normalized}


def quote_audit(parsed, reference, candidate):
    """Return exact-quote validity and issue indexes that fail validation."""
    invalid = []
    if parsed is None:
        return False, ["unparsed"]
    for index, issue in enumerate(parsed["issues"]):
        candidate_quote = issue["candidate_quote"]
        reference_quote = issue["reference_quote"]
        if issue["type"] == "omitted":
            if candidate_quote or not reference_quote or reference_quote not in reference:
                invalid.append(index)
        elif issue["type"] == "unsupported":
            if not candidate_quote or candidate_quote not in candidate or reference_quote:
                invalid.append(index)
        elif (
            not candidate_quote
            or candidate_quote not in candidate
            or not reference_quote
            or reference_quote not in reference
        ):
            invalid.append(index)
    return not invalid, invalid


def signature(parsed):
    if parsed is None:
        return None
    return (
        parsed["verdict"],
        tuple(sorted((issue["type"], issue["severity"]) for issue in parsed["issues"])),
    )


def prompt_for(key, reference, candidate):
    return PROMPTS[key].replace("{ref}", reference).replace("{cand}", candidate)


JUDGES = {
    "gemma": dict(model=AUDIT_MODEL, suffix="", cache=".llm_cache"),
    "llama": dict(
        model="mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
        suffix="_llama",
        cache=".llm_cache_llama",
    ),
}


class Runner:
    def __init__(self, judge="gemma"):
        cache_dir = os.path.join(OUT, JUDGES[judge]["cache"])
        self.llm = graders.LocalLLM(JUDGES[judge]["model"], cache_dir=cache_dir, max_tokens=700)
        self.holistic = judge2.SentenceCheck(cli=self.llm)

    def audit(self, key, reference, candidate):
        prompt = prompt_for(key, reference, candidate)
        raw = self.llm.ask(prompt, valid=lambda text: parse_audit(text) is not None)
        return raw, parse_audit(raw)

    def old_holistic(self, reference, candidate):
        result = self.holistic.run(reference, candidate)
        if result is None:
            return None
        return {
            "judge": result["judge"],
            "f1": result["f1"],
            "n_err": result["n_err"],
            "cats": result["cats"],
        }


def set_b_candidates(which):
    return s46.candidates(which)


def set_c_candidates(include_lod=False):
    source = json.load(open(set_c.P("set_C.json")))
    rows = []
    for case_id, case in source["cases"].items():
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
    if include_lod:
        for item in source.get("lod", []):
            case = source["cases"][item["case_id"]]
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


def load_extraction(which):
    if which == "devval":
        return json.load(open(s46.P("extraction_v5.json")))
    if which == "setr":
        path = P("extraction_v5_setr.json")
        if not os.path.exists(path):
            raise RuntimeError("Run extract-setr before scoring Set R.")
        return json.load(open(path))
    return json.load(open(set_c.P("extraction_v5.json")))


def current_judge_rows(which, judge="gemma"):
    path = P(f"audit_calls_{which}{JUDGES[judge]['suffix']}.jsonl")
    calls = collections.defaultdict(dict)
    if os.path.exists(path):
        for line in open(path):
            row = json.loads(line)
            calls[row["id"]][row["variant"]] = row
    return calls


def current_holistic_rows(which):
    path = P(f"holistic_{which}.jsonl")
    rows = {}
    if os.path.exists(path):
        for line in open(path):
            row = json.loads(line)
            rows[row["id"]] = row["result"]
    return rows


CONCEPT = {
    "size_mm": "size",
    "size_pct": "size",
    "size": "size",
    "hc_mm": "hc",
    "hc_abs_mm": "hc",
}
KEY_FIELDS = {
    "breast": ("path", "birads", "size_mm", "size_pct"),
    "thyroid": ("tirads", "size_mm", "size_pct", "comp"),
    "fetal": ("hc_mm", "plane"),
}


def blind(row):
    """Amendment 2 item 1: scorers never see the planted severity label."""
    return dict(row, severity=None)


def field_penalties(row, differences):
    return {
        field: s46.PENALTY[s46.severity_for(row["organ"], field, blind(row))]
        for field in differences
    }


def v5_v6_scores(row, differences):
    penalties = field_penalties(row, differences)
    merged = {}
    for field, value in penalties.items():
        concept = CONCEPT.get(field, field)
        merged[concept] = max(merged.get(concept, 0.0), value)
    v5 = max(0.0, 1.0 - sum(merged.values()))
    v6 = 1.0 / (1.0 + sum(penalties.values()))
    return v5, v6


def crqs_paper_exact(row, flat):
    """CRQS per arXiv 2607.18448 Eq. (2)-(5), signed weights of Appendix A.7, /0.7."""
    reference = {k: v for k, v in row["gold"].items() if v is not None and str(v).strip()}
    candidate = {k: v for k, v in flat.items() if v is not None and str(v).strip()}
    matches = {
        key: key in reference and key in candidate and s46.v5.vmatch(key, candidate[key], reference[key])
        for key in set(reference) | set(candidate)
    }
    cfc = sum(matches[k] for k in reference) / len(reference) if reference else 0.0
    key_reference = [k for k in KEY_FIELDS[row["organ"]] if k in reference]
    kir = sum(matches[k] for k in key_reference) / len(key_reference) if key_reference else 0.0
    hr = (
        sum(1 for k in candidate if k not in reference or not matches[k]) / len(candidate)
        if candidate
        else 0.0
    )
    common = [k for k in candidate if k in reference]
    cds = sum(not matches[k] for k in common) / len(common) if common else 0.0
    raw = 0.3 * cfc + 0.4 * kir - 0.2 * hr - 0.4 * cds
    normalized = raw / 0.7
    return {"CFC": cfc, "KIR": kir, "HR": hr, "CDS": cds, "raw": raw,
            "normalized": normalized, "clipped": min(1.0, max(0.0, normalized))}


def s1_route(parsed, differences, major_fields):
    """Stage 1 winner (trial T12, dev/val only; amendment 3).

    Route when: a rule finds a major difference or any difference; any judge
    reply could not be parsed; the three prompt presentations disagree on
    whether there is a major issue; any reply says unsure; or any reply makes a
    major claim (quote validity no longer gates a major claim).
    """
    reasons = []
    if major_fields:
        reasons.extend(f"rule_major:{field}" for field in major_fields)
    if differences:
        reasons.append("rule_difference")
    replies = [parsed.get(key) for key in PROMPT_KEYS]
    if any(reply is None for reply in replies):
        reasons.append("unparsed_judge_reply")
    else:
        majors = [any(i["severity"] == "major" for i in reply["issues"]) for reply in replies]
        if majors[0] != majors[1]:
            reasons.append("order_swap_disagreement")
        if majors[0] != majors[2]:
            reasons.append("prompt_reword_disagreement")
    if any(
        reply is not None
        and (reply["verdict"] == "unsure" or any(i["severity"] == "unsure" for i in reply["issues"]))
        for reply in replies
    ):
        reasons.append("judge_unsure")
    if any(reply is not None and any(i["severity"] == "major" for i in reply["issues"]) for reply in replies):
        reasons.append("judge_major_claim")
    return bool(reasons), reasons


LLAMA_SUBSET = 300


def llama_subset(rows):
    """Amendment 3: the second judge runs on a fixed 300-report subset (stable SHA-256 order of report IDs)."""
    core = [row for row in rows if row["kind"] in ("error", "harmless")]
    ordered = sorted(core, key=lambda row: hashlib.sha256(row["id"].encode()).hexdigest())
    return {row["id"] for row in ordered[:LLAMA_SUBSET]}


def audits_needed(row, extraction):
    return not is_rule_major(row, extraction[row["id"]])[1]


def is_rule_major(row, extraction):
    diffs = s46.rule_result(row, extraction["flat"])
    major_fields = []
    for field in diffs:
        severity = s46.severity_for(row["organ"], field, blind(row))
        if severity in {"major", "critical"}:
            major_fields.append(field)
    return diffs, major_fields


def append_jsonl(path, row):
    with open(path, "a") as output:
        output.write(json.dumps(row, ensure_ascii=False) + "\n")
        output.flush()


def run_calls(which="devval", args=None):
    """Cache 3 quote audits and the Step 46 holistic judge on rule-clear rows."""
    if which == "devval":
        rows = set_b_candidates("devval")
    elif which == "test":
        rows = set_c_candidates()
    elif which == "setr":
        rows = set_r_rows()
    else:
        raise ValueError(which)
    if which in ("devval", "test"):
        rows = [row for row in rows if row["kind"] in ("error", "harmless")]
    extraction = load_extraction(which)
    judge = getattr(args, "judge", "gemma") if args is not None else "gemma"
    if judge == "llama" and which == "test":
        keep = llama_subset(rows)
        rows = [row for row in rows if row["id"] in keep]
    audits = current_judge_rows(which, judge)
    holistic = current_holistic_rows(which)
    audit_path = P(f"audit_calls_{which}{JUDGES[judge]['suffix']}.jsonl")
    holistic_path = P(f"holistic_{which}.jsonl")
    runner = Runner(judge)
    deadline = time.time() + (getattr(args, "max_hours", 8.0) * 3600)
    new_calls = 0
    for index, row in enumerate(rows, 1):
        if row["id"] not in extraction:
            continue
        differences, major_fields = is_rule_major(row, extraction[row["id"]])
        if not major_fields:
            for key in PROMPT_KEYS:
                if key in audits[row["id"]]:
                    continue
                if time.time() >= deadline:
                    print("audit time cap reached at", index, "of", len(rows), flush=True)
                    return
                raw, parsed = runner.audit(key, row["ref"], row["cand"])
                append_jsonl(
                    audit_path,
                    {"id": row["id"], "variant": key, "raw": raw, "parsed": parsed},
                )
                audits[row["id"]][key] = {"parsed": parsed, "raw": raw}
                new_calls += 1
        if judge == "gemma" and which != "setr" and not differences and row["id"] not in holistic:
            if time.time() >= deadline:
                print("holistic time cap reached at", index, "of", len(rows), flush=True)
                return
            result = runner.old_holistic(row["ref"], row["cand"])
            append_jsonl(holistic_path, {"id": row["id"], "result": result})
            holistic[row["id"]] = result
            new_calls += 1
        if index % 25 == 0:
            print(which, "audit rows", index, "of", len(rows), "new calls", new_calls, flush=True)
    print(which, "calls complete", "rows", len(rows), "new calls", new_calls, flush=True)


def evaluate_row(row, flat, audit_rows, holistic_result):
    differences = s46.rule_result(row, flat)
    rule_score, _ = s46.primary_score(blind(row), flat)
    v1_score = 1.0 if rule_score is None else rule_score
    v5_score, v6_score = v5_v6_scores(row, differences)
    v0_score, _ = s46.primary_score(
        blind(row),
        flat,
        holistic_result.get("judge") if holistic_result else None,
    )
    v0_score = 1.0 if v0_score is None else v0_score
    if differences:
        v2_score = v1_score
        v2_flag = v1_score < 0.8
    elif holistic_result and holistic_result.get("judge") is not None:
        v2_score = max(0.8, min(1.0, float(holistic_result["judge"])))
        v2_flag = float(holistic_result["judge"]) < 0.8
    else:
        v2_score, v2_flag = 1.0, False

    parsed = {key: audit_rows.get(key, {}).get("parsed") for key in PROMPT_KEYS}
    valid = {}
    invalid_quotes = {}
    for key in PROMPT_KEYS:
        valid[key], invalid_quotes[key] = quote_audit(
            parsed[key], row["ref"], row["cand"]
        )

    prompt_a = parsed[PROMPT_KEYS[0]]
    order_variant = parsed[PROMPT_KEYS[1]]
    reword_variant = parsed[PROMPT_KEYS[2]]
    reasons = []
    major_fields = []
    for field in differences:
        severity = s46.severity_for(row["organ"], field, blind(row))
        if severity in {"major", "critical"}:
            major_fields.append(field)
    rule_major = bool(major_fields)
    if rule_major:
        reasons.extend(f"rule_major:{field}" for field in major_fields)

    signatures = [signature(parsed[key]) for key in PROMPT_KEYS]
    order_disagreement = (
        signatures[0] is None
        or signatures[1] is None
        or signatures[0] != signatures[1]
    )
    reword_disagreement = (
        signatures[0] is None
        or signatures[2] is None
        or signatures[0] != signatures[2]
    )
    if any(parsed[key] is None for key in PROMPT_KEYS):
        reasons.append("invalid_json")
    if any(not valid[key] for key in PROMPT_KEYS):
        reasons.append("invalid_quote")
    if order_disagreement:
        reasons.append("order_swap_disagreement")
    if reword_disagreement:
        reasons.append("prompt_reword_disagreement")

    judge_issue = any(
        parsed[key] is not None and parsed[key]["verdict"] != "clean"
        for key in PROMPT_KEYS
    )
    if differences and prompt_a is not None and prompt_a["verdict"] == "clean":
        reasons.append("rule_judge_disagreement")
    if not differences and judge_issue:
        reasons.append("rule_judge_disagreement")
    if any(
        parsed[key] is not None
        and (
            parsed[key]["verdict"] == "unsure"
            or any(issue["severity"] == "unsure" for issue in parsed[key]["issues"])
        )
        for key in PROMPT_KEYS
    ):
        reasons.append("judge_unsure")

    judge_major = False
    if prompt_a is not None and valid[PROMPT_KEYS[0]]:
        judge_major = any(issue["severity"] == "major" for issue in prompt_a["issues"])
    if judge_major:
        reasons.append("judge_major_valid_quote")
    reasons = list(dict.fromkeys(reasons))
    uncertain_reasons = {
        "invalid_json",
        "invalid_quote",
        "order_swap_disagreement",
        "prompt_reword_disagreement",
        "rule_judge_disagreement",
        "judge_unsure",
    }
    v3_route = bool(rule_major or judge_major or any(r in uncertain_reasons for r in reasons))
    v4_route = bool(rule_major or judge_major)
    s1, s1_reasons = s1_route(parsed, differences, major_fields)
    if v3_route and not reasons:
        reasons = ["unspecified_route_reason"]
    return {
        "differences": differences,
        "rule_major_fields": major_fields,
        "v0_score": v0_score,
        "v1_score": v1_score,
        "v5_score": v5_score,
        "v6_score": v6_score,
        "v2_score": v2_score,
        "v2_flag": v2_flag,
        "audit": parsed,
        "quote_valid": valid,
        "invalid_quote_issue_indexes": invalid_quotes,
        "v3_route": v3_route,
        "s1_route": s1,
        "s1_route_reason": s1_reasons,
        "v3_route_reason": reasons if v3_route else [],
        "v4_route": v4_route,
        "v4_route_reason": [r for r in reasons if r.startswith("rule_major:") or r == "judge_major_valid_quote"] if v4_route else [],
    }


def score_rows(which="devval", judge="gemma"):
    if which == "devval":
        rows = set_b_candidates("devval")
    elif which == "setr":
        rows = set_r_rows()
    else:
        rows = set_c_candidates()
    if which in ("devval", "test"):
        rows = [row for row in rows if row["kind"] in ("error", "harmless")]
    extraction = load_extraction(which)
    audits = current_judge_rows(which, judge)
    holistic = current_holistic_rows(which)
    scored = []
    for row in rows:
        if row["id"] not in extraction:
            continue
        result = evaluate_row(
            row,
            extraction[row["id"]]["flat"],
            audits.get(row["id"], {}),
            holistic.get(row["id"]),
        )
        scored.append(dict(row, **result))
    return scored


def scalar_scores(which, rows):
    """Saved CRQS, word-metric, and Step 45 learned scores for equal-budget routing."""
    core = [row for row in rows if row["kind"] in ("error", "harmless")]
    path = P(f"comparators_{which}.json")
    saved = {}
    if os.path.exists(path):
        saved = json.load(open(path))
    score_keys = ("bleu", "rougeL", "chrf", "bertscore", "ratescore", "step45_learned")
    missing = [row for row in core if row["id"] not in saved or any(k not in saved[row["id"]] for k in score_keys)]
    if missing:
        specs = {
            "bleu": "bleu",
            "rougeL": "rougeL",
            "chrf": "chrf",
            "bertscore": "bertscore:roberta-large",
            "ratescore": "ratescore",
        }
        refs = [row["ref"] for row in missing]
        candidates_text = [row["cand"] for row in missing]
        new_values = {row["id"]: {} for row in missing}
        for key, spec in specs.items():
            metric = graders.make(spec)
            values = (
                metric.batch(refs, candidates_text)
                if hasattr(metric, "batch")
                else [metric.score(ref, cand) for ref, cand in zip(refs, candidates_text)]
            )
            for row, value in zip(missing, values):
                new_values[row["id"]][key] = float(value)
            for row in missing:
                saved.setdefault(row["id"], {}).update(new_values[row["id"]])
            json.dump(saved, open(path, "w"), ensure_ascii=False)
            print(which, "comparator", key, len(values), flush=True)

        model_path = os.path.join(
            s46.set_a.ROOT,
            "results",
            "partA",
            "step45_improve_scorers",
            "partE",
            "models.pkl",
        )
        if not os.path.exists(model_path):
            raise RuntimeError("Frozen Step 45 learned scorer is missing.")
        import pickle

        learned = pickle.load(open(model_path, "rb"))["logreg"]
        vectors = []
        for row in missing:
            feature_scores = {
                "bleu": new_values[row["id"]]["bleu"],
                "rougeL": new_values[row["id"]]["rougeL"],
                "chrf": new_values[row["id"]]["chrf"],
                "bertscore[roberta-large]": new_values[row["id"]]["bertscore"],
                "ratescore": new_values[row["id"]]["ratescore"],
            }
            vectors.append(s46.part_e.vec(feature_scores, row["ref"], row["cand"], row["organ"]))
        learned_values = 1.0 - learned.predict_proba(np.asarray(vectors, dtype=float))[:, 1]
        for row, value in zip(missing, learned_values):
            saved[row["id"]]["step45_learned"] = float(value)
        json.dump(saved, open(path, "w"), ensure_ascii=False)

    extraction = load_extraction(which)
    for row in core:
        flat = extraction[row["id"]]["flat"]
        row.update(saved[row["id"]])
        row["crqs_normalized"] = s46.crqs_score(row, flat)["normalized"]
        row["crqs_clipped"] = s46.crqs_score(row, flat)["clipped"]
        paper = crqs_paper_exact(row, flat)
        row["crqs_paper_normalized"] = paper["normalized"]
        row["crqs_paper_clipped"] = paper["clipped"]
    json.dump({row["id"]: {key: row[key] for key in (*score_keys, "crqs_normalized", "crqs_clipped", "crqs_paper_normalized", "crqs_paper_clipped")} for row in core}, open(path, "w"), ensure_ascii=False)
    return core


def stable_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def calibrate_route_cutoff(rows, score_key, target_share):
    """Choose a label-blind cutoff and stable hash tie-break for an exact dev share."""
    values = sorted((float(row[score_key]), row["id"]) for row in rows)
    if not values:
        raise RuntimeError(f"No dev-val values for {score_key}")
    n_route = int(round(target_share * len(values)))
    if n_route <= 0:
        threshold = values[0][0]
        tie_hash_max = None
    elif n_route >= len(values):
        threshold = values[-1][0]
        tie_hash_max = "f" * 64
    else:
        threshold = values[n_route - 1][0]
        lower = sum(value < threshold for value, _ in values)
        tied = sorted(stable_hash(row_id) for value, row_id in values if value == threshold)
        need = n_route - lower
        tie_hash_max = tied[need - 1] if need else None
    calibration = {"threshold": threshold, "tie_hash_max": tie_hash_max}
    flagged = sum(route_by_scalar(row, score_key, calibration) for row in rows)
    return {
        **calibration,
        "devval_routes": flagged,
        "devval_route_share": flagged / len(rows),
        "target_route_share": float(target_share),
        "n_devval": len(rows),
    }


def route_by_scalar(row, score_key, calibration):
    value = float(row[score_key])
    threshold = float(calibration["threshold"])
    if value < threshold:
        return True
    if value > threshold:
        return False
    tie_hash_max = calibration.get("tie_hash_max")
    return bool(tie_hash_max and stable_hash(row["id"]) <= tie_hash_max)


def freeze_devval(args=None):
    """Freeze V3's dev-val route budget and same-budget scalar comparators."""
    source_rows = [
        row for row in set_b_candidates("devval") if row["kind"] in ("error", "harmless")
    ]
    extraction = load_extraction("devval")
    audits = current_judge_rows("devval")
    holistic = current_holistic_rows("devval")
    missing = []
    for row in source_rows:
        if row["id"] not in extraction:
            missing.append(row["id"] + "|extraction")
            continue
        if audits_needed(row, extraction) and any(key not in audits.get(row["id"], {}) for key in PROMPT_KEYS):
            missing.append(row["id"])
        if not s46.rule_result(row, extraction[row["id"]]["flat"]) and row["id"] not in holistic:
            missing.append(row["id"])
    if missing:
        raise RuntimeError(
            f"Set B dev-val calls are incomplete for {len(set(missing))} report IDs; finish calls before freezing."
        )

    scored = score_rows("devval")
    comparator_rows = scalar_scores("devval", scored)
    core_scored = [row for row in scored if row["kind"] in ("error", "harmless")]
    route_share = float(np.mean([row["v3_route"] for row in core_scored])) if core_scored else None
    comparator_keys = (
        "crqs_normalized",
        "crqs_paper_normalized",
        "bleu",
        "rougeL",
        "chrf",
        "bertscore",
        "ratescore",
        "step45_learned",
    )
    cutoffs = {
        key: calibrate_route_cutoff(comparator_rows, key, route_share)
        for key in comparator_keys
    }
    thresholds = {
        "source": "Step 46 Set B dev-val only",
        "n_rows": len(core_scored),
        "groups": len({row["group"] for row in core_scored}),
        "v3_route_budget": route_share,
        "v3_routes": sum(row["v3_route"] for row in core_scored),
        "v3_quote_valid_share": float(np.mean([all(row["quote_valid"].values()) for row in core_scored])) if core_scored else None,
        "comparator_cutoffs": cutoffs,
        "prompt_sha256": PROMPT_SHA256,
        "audit_model": AUDIT_MODEL,
        "calibration_rows_sha256": hashlib.sha256(
            "\n".join(sorted(row["id"] for row in core_scored)).encode()
        ).hexdigest(),
    }
    json.dump(scored, open(P("devval_scores.json"), "w"), ensure_ascii=False)
    json.dump(thresholds, open(P("thresholds.json"), "w"), indent=1)
    thresholds["sha256"] = hashlib.sha256(
        json.dumps(thresholds, sort_keys=True).encode()
    ).hexdigest()
    json.dump(thresholds, open(P("thresholds.json"), "w"), indent=1)
    print(json.dumps(thresholds, indent=1))


def set_r_rows():
    """Load Step 43 Qwen-VL reports plus extraction-fidelity labels, not image truth."""
    selected = {
        row["case_id"]: row
        for row in json.load(open(os.path.join(OUT, "..", "step43_extractor_v4", "selected.json")))
    }
    reports = {
        row["case_id"]: row
        for row in (
            json.loads(line)
            for line in open(os.path.join(OUT, "..", "step43_extractor_v4", "reports.jsonl"))
        )
    }
    labels = {}
    with open(os.path.join(ROOT, "docs", "step43_check_filled.csv"), newline="") as source:
        for row in csv.DictReader(source):
            labels[row["id"]] = row
    key = json.load(open(os.path.join(OUT, "..", "step43_extractor_v4", "check_sheet_key.json")))
    rows = []
    for item in key["key"]:
        selected_case = selected[item["case_id"]]
        report = reports[item["case_id"]]["report"]
        label = labels[item["id"]]
        rows.append(
            dict(
                id=f"setR|{item['id']}",
                case=item["case_id"],
                group=item["case_id"],
                organ="fetal" if item["organ"] == "fetal" else item["organ"],
                dataset=item["dataset"],
                kind="human",
                severity=None,
                ref=selected_case["reference"],
                gold=selected_case["ref_facts"],
                cand=report,
                human_extraction_fidelity=label["all_fields_right"],
                human_wrong_fields=label["wrong_fields"],
            )
        )
    return rows


def extract_set_r():
    """Run the frozen v5 extractor on the 30 descriptive Set R reports."""
    from . import step27_extractor as extractor
    from .step45_extractor_v5 import facts_v5

    extractor.CACHE = P("cache_v5_setr.jsonl")
    extractor.OUT = OUT
    instance = extractor.Extractor("v5")
    results = {}
    rows = set_r_rows()
    for index, row in enumerate(rows, 1):
        raw = instance.raw(row["organ"], row["cand"])
        flat, ok, strict = facts_v5(row["organ"], raw, row["cand"])
        results[row["id"]] = {"flat": flat, "ok": ok, "strict": strict, "raw": raw}
        if index % 10 == 0:
            print("Set R extract", index, len(rows), flush=True)
    json.dump(results, open(P("extraction_v5_setr.json"), "w"), ensure_ascii=False)
    print("saved Set R extraction", len(results), flush=True)


def clopper_pearson_upper(misses, n, level=0.95):
    from scipy.stats import beta
    if n == 0:
        return None
    if misses >= n:
        return 1.0
    return float(beta.ppf(level, misses + 1, n - misses))


def miss_rate_h1(rows):
    """Amendment 2 item 2: unrouted planted major/critical errors / all of them."""
    major = [row for row in rows if row["kind"] == "error" and row.get("severity") in (2, 3)]
    misses = sum(not row["v3_route"] for row in major)
    upper = clopper_pearson_upper(misses, len(major))
    return {
        "n_major_or_critical": len(major),
        "misses": misses,
        "miss_rate": (misses / len(major)) if major else None,
        "upper_95_clopper_pearson": upper,
        "groups_with_major_or_critical": len({row["group"] for row in major}),
    }


def bootstrap_h1(rows, draws=1000, seed=0):
    major_errors = [row for row in rows if row["kind"] == "error" and row.get("severity") in (2, 3)]
    groups = sorted({row["group"] for row in rows})
    if len(groups) < 30:
        return {"n_major_or_critical": len(major_errors), "groups": len(groups), "too_small_to_compare": True}
    by_group = {group: [row for row in rows if row["group"] == group] for group in groups}

    def auto_pass_major_share(sample):
        auto_pass = [row for row in sample if not row["v3_route"]]
        if not auto_pass:
            return None
        return float(
            sum(row["kind"] == "error" and row.get("severity") in (2, 3) for row in auto_pass)
            / len(auto_pass)
        )

    point = auto_pass_major_share(rows)
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(draws):
        selected = rng.choice(groups, size=len(groups), replace=True)
        boot = [row for group in selected for row in by_group[group]]
        value = auto_pass_major_share(boot)
        if value is not None:
            samples.append(value)
    return {
        "n_major_or_critical": len(major_errors),
        "groups": len(groups),
        "n_auto_passed": sum(not row["v3_route"] for row in rows),
        "auto_pass_major_critical_share": point,
        "major_critical_error_miss_share": float(np.mean([not row["v3_route"] for row in major_errors])) if major_errors else None,
        "ci": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))] if samples else None,
        "seed": seed,
        "draws": draws,
        "too_small_to_compare": False,
    }


def grouped_catch_difference(rows, comparator_key, v3_key="v3_route", seed=0, draws=1000):
    errors = [row for row in rows if row["kind"] == "error" and row.get(comparator_key) is not None]
    groups = sorted({row["group"] for row in errors})
    if len(groups) < 30:
        return {"n_errors": len(errors), "groups": len(groups), "too_small_to_compare": True}
    by_group = {group: [row for row in errors if row["group"] == group] for group in groups}

    def difference(sample):
        return float(
            np.mean([bool(row[v3_key]) for row in sample])
            - np.mean([bool(row[comparator_key]) for row in sample])
        )

    point = difference(errors)
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(draws):
        selected = rng.choice(groups, size=len(groups), replace=True)
        boot = [row for group in selected for row in by_group[group]]
        if boot:
            samples.append(difference(boot))
    return {
        "n_errors": len(errors),
        "groups": len(groups),
        "difference_v3_minus_comparator": point,
        "ci": [float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))],
        "seed": seed,
        "draws": draws,
        "too_small_to_compare": False,
    }


def require_complete_calls(which, rows):
    extraction = load_extraction(which)
    audits = current_judge_rows(which)
    holistic = current_holistic_rows(which)
    missing = []
    for row in rows:
        if row["id"] not in extraction:
            missing.append(row["id"] + "|extraction")
            continue
        if audits_needed(row, extraction) and any(key not in audits.get(row["id"], {}) for key in PROMPT_KEYS):
            missing.append(row["id"] + "|audit")
        if which != "setr" and not s46.rule_result(row, extraction[row["id"]]["flat"]) and row["id"] not in holistic:
            missing.append(row["id"] + "|holistic")
    if missing:
        raise RuntimeError(f"{which} artifacts incomplete: {len(missing)} missing report outputs; resume calls/extraction.")


def load_frozen_thresholds():
    thresholds = json.load(open(P("thresholds.json")))
    saved_hash = thresholds.pop("sha256", None)
    computed_hash = hashlib.sha256(json.dumps(thresholds, sort_keys=True).encode()).hexdigest()
    if saved_hash != computed_hash:
        raise RuntimeError("Frozen development thresholds failed their SHA-256 check.")
    thresholds["sha256"] = saved_hash
    if thresholds.get("prompt_sha256") != PROMPT_SHA256:
        raise RuntimeError("Frozen development thresholds do not match the current prompts.")
    return thresholds


def limit_of_detection_metrics():
    rows = set_c_candidates(include_lod=True)
    extraction = load_extraction("test")
    core_rows = set_c_candidates()
    base_scores = collections.defaultdict(list)
    for row in core_rows:
        if row["kind"] != "harmless" or row["id"] not in extraction:
            continue
        score, _ = s46.primary_score(blind(row), extraction[row["id"]]["flat"])
        base_scores[row["case"]].append(1.0 if score is None else float(score))
    lod_rows = []
    for row in rows:
        if row["kind"] != "lod" or row["id"] not in extraction or row["case"] not in base_scores:
            continue
        score, _ = s46.primary_score(blind(row), extraction[row["id"]]["flat"])
        lod_rows.append(dict(row, v1_score=1.0 if score is None else float(score)))
    output = {}
    for name, matches in (
        ("5_percent_size", lambda row: row.get("field") in ("size_mm", "size_pct") and row.get("level") == 0.05),
        ("1_mm_head_circumference", lambda row: row.get("field") == "hc_mm" and row.get("level") == 1),
    ):
        paired = []
        for row in lod_rows:
            if not matches(row):
                continue
            paired.extend(
                (
                    dict(row, kind="error", score=row["v1_score"]),
                    dict(row, id=row["id"] + "|reference", kind="harmless", score=float(np.mean(base_scores[row["case"]]))),
                )
            )
        output[name] = s46.grouped_auc(paired, name, "score")
    output["pass"] = all(
        isinstance(output[name], dict)
        and output[name].get("auroc", -1) >= 0.80
        and not output[name].get("too_small_to_compare", False)
        for name in ("5_percent_size", "1_mm_head_circumference")
    )
    return output


def evaluate_set_r():
    if not os.path.exists(P("extraction_v5_setr.json")):
        extract_set_r()
    rows = set_r_rows()
    require_complete_calls("setr", rows)
    scored = score_rows("setr")
    parsed = []
    for row in scored:
        value = str(row["human_extraction_fidelity"]).strip().lower()
        human_right = value in {"yes", "y", "true", "1", "all right", "correct"}
        human_wrong = value in {"no", "n", "false", "0", "wrong"}
        parsed.append((row, human_right if human_right or human_wrong else None))
    known = [(row, right) for row, right in parsed if right is not None]
    result = {
        "n": len(scored),
        "labels_known": len(known),
        "human_extraction_fidelity_yes": sum(right for _, right in known),
        "v3_routes": sum(row["v3_route"] for row in scored),
        "v3_route_share": float(np.mean([row["v3_route"] for row in scored])) if scored else None,
        "counts": {
            "route_and_human_wrong": sum(row["v3_route"] and not right for row, right in known),
            "route_and_human_right": sum(row["v3_route"] and right for row, right in known),
            "auto_pass_and_human_wrong": sum(not row["v3_route"] and not right for row, right in known),
            "auto_pass_and_human_right": sum(not row["v3_route"] and right for row, right in known),
        },
        "label_scope": "single-reviewer extractor-v4 text-faithfulness labels; not image correctness",
    }
    json.dump(scored, open(P("scored_setr.json"), "w"), ensure_ascii=False)
    return result


def evaluate_test(args=None):
    scored = score_rows("test")
    core = [row for row in scored if row["kind"] in ("error", "harmless")]
    require_complete_calls("test", core)
    frozen = load_frozen_thresholds()
    comparator_rows = scalar_scores("test", core)
    comparator_by_id = {row["id"]: row for row in comparator_rows}
    for row in core:
        comparator = comparator_by_id[row["id"]]
        for key, cutoff in frozen["comparator_cutoffs"].items():
            route_key = key + "_route"
            row[route_key] = route_by_scalar(comparator, key, cutoff)
    h2_comparisons = {
        key: grouped_catch_difference(core, key + "_route")
        for key in frozen["comparator_cutoffs"]
    }
    h2_required = {key: value for key, value in h2_comparisons.items() if key not in ("step45_learned", "crqs_paper_normalized")}
    paired_cases = {
        row["case"] for row in core if row["kind"] == "error"
    } & {row["case"] for row in core if row["kind"] == "harmless"}
    case_counts_by_organ = {
        organ: len({row["case"] for row in core if row["organ"] == organ and row["case"] in paired_cases})
        for organ in sorted({row["organ"] for row in core})
    }
    group_counts_by_organ = {
        organ: len({row["group"] for row in core if row["organ"] == organ and row["case"] in paired_cases})
        for organ in sorted({row["organ"] for row in core})
    }
    n_test_cases = len(paired_cases)
    n_major_critical = sum(1 for row in core if row["kind"] == "error" and row.get("severity") in (2, 3))
    sample_eligible = n_major_critical >= 400 and bool(group_counts_by_organ) and all(
        count >= 30 for count in group_counts_by_organ.values()
    )
    h2_pass = sample_eligible and bool(h2_required) and all(
        not result.get("too_small_to_compare", False)
        and result.get("ci", [0, 0])[0] > 0
        for result in h2_required.values()
    )
    v1_auc = s46.grouped_auc(core, "V1", "v1_score")
    v1_by_organ = {
        organ: s46.grouped_auc([row for row in core if row["organ"] == organ], "V1", "v1_score")
        for organ in sorted({row["organ"] for row in core})
    }
    h4 = limit_of_detection_metrics()
    h4["pass"] = bool(h4.get("pass") and sample_eligible)
    h5 = {
        "all_routed_have_reason": all(bool(row["v3_route_reason"]) for row in core if row["v3_route"]),
        "routed_count": sum(row["v3_route"] for row in core),
        "invalid_quote_count": sum(
            sum(not valid for valid in row["quote_valid"].values())
            for row in core
            if row["v3_route"]
        ),
        "quote_valid_share": float(
            np.mean([all(row["quote_valid"].values()) for row in core if row["v3_route"]])
        ) if any(row["v3_route"] for row in core) else None,
    }
    h5["pass"] = h5["all_routed_have_reason"] and h5["invalid_quote_count"] == 0
    h1 = bootstrap_h1(core)
    harmless_route = float(np.mean([row["v3_route"] for row in core if row["kind"] == "harmless"])) if any(row["kind"] == "harmless" for row in core) else None
    h1["harmless_routed_share"] = harmless_route
    h1["amendment2_miss_rate"] = miss_rate_h1(core)
    h1["pass"] = bool(
        not h1.get("too_small_to_compare", False)
        and h1["amendment2_miss_rate"]["upper_95_clopper_pearson"] is not None
        and h1["amendment2_miss_rate"]["upper_95_clopper_pearson"] <= 0.02
        and harmless_route is not None
        and harmless_route <= 0.30
        and sample_eligible
    )

    h9 = {"status": "second-judge calls not found"}
    if os.path.exists(P("audit_calls_test_llama.jsonl")):
        llama_audits = current_judge_rows("test", "llama")
        extraction_test = load_extraction("test")
        subset_ids = llama_subset(core)
        incomplete = [
            row["id"]
            for row in core
            if row["id"] in subset_ids
            and row["id"] in extraction_test
            and audits_needed(row, extraction_test)
            and any(key not in llama_audits.get(row["id"], {}) for key in PROMPT_KEYS)
        ]
        if incomplete:
            h9 = {"status": "incomplete", "missing_reports": len(incomplete)}
        else:
            llama_rows = {r["id"]: r for r in score_rows("test", "llama") if r["kind"] in ("error", "harmless")}
            both = [row for row in core if row["id"] in llama_rows and row["id"] in subset_ids]
            for row in both:
                row["llama_v3_route"] = llama_rows[row["id"]]["v3_route"]
                row["llama_s1_route"] = llama_rows[row["id"]]["s1_route"]
            llama_view = [dict(row, v3_route=row["llama_v3_route"]) for row in both]
            h9 = {
                "status": "complete",
                "gemma": {
                    "error_catch": float(np.mean([r["v3_route"] for r in both if r["kind"] == "error"])),
                    "harmless_routed_share": float(np.mean([r["v3_route"] for r in both if r["kind"] == "harmless"])),
                    "h1_miss_rate": miss_rate_h1(both),
                },
                "llama": {
                    "error_catch": float(np.mean([r["llama_v3_route"] for r in both if r["kind"] == "error"])),
                    "harmless_routed_share": float(np.mean([r["llama_v3_route"] for r in both if r["kind"] == "harmless"])),
                    "h1_miss_rate": miss_rate_h1(llama_view),
                },
                "routes_differ_share": float(np.mean([r["v3_route"] != r["llama_v3_route"] for r in both])),
                "s1": {
                    "gemma_error_catch": float(np.mean([r["s1_route"] for r in both if r["kind"] == "error"])),
                    "gemma_harmless_routed": float(np.mean([r["s1_route"] for r in both if r["kind"] == "harmless"])),
                    "llama_error_catch": float(np.mean([r["llama_s1_route"] for r in both if r["kind"] == "error"])),
                    "llama_harmless_routed": float(np.mean([r["llama_s1_route"] for r in both if r["kind"] == "harmless"])),
                    "routes_differ_share": float(np.mean([r["s1_route"] != r["llama_s1_route"] for r in both])),
                },
                "subset_size": len(both),
                "note": "descriptive; if the two judges disagree on H1 or H2 both are reported",
            }

    stage1 = load_frozen_stage1()
    for row in core:
        comparator = comparator_by_id[row["id"]]
        for key, cutoff in stage1["comparator_cutoffs"].items():
            row[key + "_s1budget_route"] = route_by_scalar(comparator, key, cutoff)
    s1_h1 = miss_rate_h1([dict(r, v3_route=r["s1_route"]) for r in core])
    s1_harmless = float(np.mean([r["s1_route"] for r in core if r["kind"] == "harmless"]))
    s1_h2 = {
        key: grouped_catch_difference(core, key + "_s1budget_route", v3_key="s1_route")
        for key in stage1["comparator_cutoffs"]
    }
    s1_h2_required = {k: v for k, v in s1_h2.items() if k not in ("step45_learned", "crqs_paper_normalized")}
    primary = {
        "variant": stage1["primary_variant"],
        "frozen_variants_sha256": stage1["sha256"],
        "H1": dict(s1_h1, harmless_routed_share=s1_harmless, pass_=bool(
            sample_eligible
            and s1_h1["upper_95_clopper_pearson"] is not None
            and s1_h1["upper_95_clopper_pearson"] <= 0.02
            and s1_harmless <= 0.30
        )),
        "H2": {"comparators": s1_h2, "pass_": bool(sample_eligible and s1_h2_required and all(
            not v.get("too_small_to_compare", False) and v.get("ci", [0, 0])[0] > 0 for v in s1_h2_required.values()
        ))},
        "error_catch": float(np.mean([r["s1_route"] for r in core if r["kind"] == "error"])),
        "route_reasons": dict(collections.Counter(x for r in core if r["s1_route"] for x in r["s1_route_reason"])),
        "all_routed_have_reason": all(bool(r["s1_route_reason"]) for r in core if r["s1_route"]),
    }

    set_b_metrics = json.load(open(s46.P("metrics.json")))
    crqs_set_b = set_b_metrics.get("crqs_normalized", {}).get("auroc")
    v1_set_b = set_b_metrics.get("exploratory_rule_only_no_diff_as_perfect", {}).get("auroc")
    crqs_set_c = s46.grouped_auc(comparator_rows, "CRQS", "crqs_normalized")
    h7 = {
        "set_B_writer_generated_crqs_auroc": crqs_set_b,
        "set_B_rule_only_auroc": v1_set_b,
        "set_C_crqs_auroc": crqs_set_c.get("auroc"),
        "set_C_v1_auroc": v1_auc.get("auroc"),
        "set_B_crqs_minus_rule_only": crqs_set_b - v1_set_b if crqs_set_b is not None and v1_set_b is not None else None,
        "set_C_crqs_minus_v1": crqs_set_c["auroc"] - v1_auc["auroc"] if crqs_set_c.get("auroc") is not None and v1_auc.get("auroc") is not None else None,
        "change_in_crqs_minus_v1_gap": None,
        "interpretation": "descriptive comparison with Step 46 Set B writer-generated reports, not templated reports",
    }
    if h7["set_B_crqs_minus_rule_only"] is not None and h7["set_C_crqs_minus_v1"] is not None:
        h7["change_in_crqs_minus_v1_gap"] = h7["set_C_crqs_minus_v1"] - h7["set_B_crqs_minus_rule_only"]

    metrics = {
        "n_core_reports": len(core),
        "groups": len({row["group"] for row in core}),
        "sample_size_eligibility": {
            "n_cases": n_test_cases,
            "cases_by_organ": case_counts_by_organ,
            "groups_by_organ": group_counts_by_organ,
            "meets_preregistered_minimum": sample_eligible,
        },
        "variants_tried": ["V0", "V1", "V2", "V3", "V4", "V5", "V6", "S1"],
        "V0": s46.grouped_auc(core, "V0", "v0_score"),
        "V1": v1_auc,
        "V2": s46.grouped_auc(core, "V2", "v2_score"),
        "V5": s46.grouped_auc(core, "V5", "v5_score"),
        "V6": s46.grouped_auc(core, "V6", "v6_score"),
        "H8_V5_minus_V1": s46.paired_auc_difference(core, "v1_score", primary_key="v5_score"),
        "H8_V6_minus_V1": s46.paired_auc_difference(core, "v1_score", primary_key="v6_score"),
        "H1": h1,
        "H2": {
            "same_budget_as_v3_devval": frozen["v3_route_budget"],
            "comparators": h2_comparisons,
            "test_route_shares": {
                key: float(np.mean([row[key + "_route"] for row in core])) if core else None
                for key in frozen["comparator_cutoffs"]
            },
            "pass": h2_pass,
        },
        "H3": {
            "V1_auroc": v1_auc,
            "V1_auroc_by_organ": v1_by_organ,
            "pass": sample_eligible and v1_auc.get("auroc", -1) >= 0.90,
        },
        "H4": h4,
        "V3_harmless_routed_share": float(np.mean([r["v3_route"] for r in core if r["kind"] == "harmless"])) if any(r["kind"] == "harmless" for r in core) else None,
        "V3_error_catch": float(np.mean([r["v3_route"] for r in core if r["kind"] == "error"])) if any(r["kind"] == "error" for r in core) else None,
        "V4_harmless_routed_share": float(np.mean([r["v4_route"] for r in core if r["kind"] == "harmless"])) if any(r["kind"] == "harmless" for r in core) else None,
        "V4_error_catch": float(np.mean([r["v4_route"] for r in core if r["kind"] == "error"])) if any(r["kind"] == "error" for r in core) else None,
        "H5": h5,
        "H6_Set_R": evaluate_set_r(),
        "H7": h7,
        "H9_second_judge": h9,
        "PRIMARY_S1": primary,
        "frozen_thresholds_sha256": frozen["sha256"],
    }
    json.dump(scored, open(P("scored_test.json"), "w"), ensure_ascii=False)
    json.dump(metrics, open(P("metrics.json"), "w"), indent=1)
    print(json.dumps(metrics, indent=1))


def freeze_stage1(args=None):
    """Amendment 3: freeze the Stage 1 winner, its dev budget and same-budget comparator cutoffs."""
    path = P("frozen_variants.json")
    if os.path.exists(path):
        raise RuntimeError("frozen_variants.json already exists; refusing to overwrite.")
    if os.path.exists(set_c.P("set_C.json")):
        raise RuntimeError("Set C already exists; Stage 1 can no longer be frozen.")
    frozen_v3 = load_frozen_thresholds()
    scored = score_rows("devval")
    core = [row for row in scored if row["kind"] in ("error", "harmless")]
    comparator_rows = scalar_scores("devval", core)
    budget = float(np.mean([row["s1_route"] for row in core]))
    cutoffs = {key: calibrate_route_cutoff(comparator_rows, key, budget) for key in frozen_v3["comparator_cutoffs"]}
    major = [r for r in core if r["kind"] == "error" and r.get("severity") in (2, 3)]
    frozen = {
        "primary_variant": "S1 (Stage 1 trial T12)",
        "replaces_v3_as_primary": True,
        "stage1_trials_logged": 12,
        "stage1_data": "Step 46 Set B dev-val saved Gemma replies only (no new model calls)",
        "selection_metric": "catch of major/critical errors at harmless routed <= 30%, on dev",
        "dev_s1_major_critical_catch": sum(r["s1_route"] for r in major) / len(major),
        "dev_s1_harmless_routed": float(np.mean([r["s1_route"] for r in core if r["kind"] == "harmless"])),
        "s1_route_budget": budget,
        "comparator_cutoffs": cutoffs,
        "v3_thresholds_sha256": frozen_v3["sha256"],
        "code_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
    }
    frozen["sha256"] = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    json.dump(frozen, open(path, "w"), indent=1)
    print(json.dumps({k: v for k, v in frozen.items() if k != "comparator_cutoffs"}, indent=1))


def load_frozen_stage1():
    data = json.load(open(P("frozen_variants.json")))
    saved = data.pop("sha256")
    if hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest() != saved:
        raise RuntimeError("frozen_variants.json failed its SHA-256 check.")
    data["sha256"] = saved
    return data


TRIAL_COLUMNS = (
    "trial_id", "date", "description", "code_git_hash", "judge",
    "dev_auroc", "catch_major_critical_at_30pct_harmless", "model_calls_per_report", "notes",
)


def log_trial(**fields):
    """Amendment 2 item 6: every Stage 1 trial is appended, none deleted."""
    path = P("trial_log.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIAL_COLUMNS)
        if new:
            writer.writeheader()
        writer.writerow({key: fields.get(key, "") for key in TRIAL_COLUMNS})


def export_handcheck(n=50, seed=0):
    """Amendment 2 item 8: 50 Set C reports, extractor v5 fields beside the text, no scores, no labels."""
    path = P("handcheck_setC.csv")
    if os.path.exists(path):
        raise RuntimeError("handcheck_setC.csv already exists; refusing to overwrite.")
    rows = [r for r in set_c_candidates() if r["kind"] in ("error", "harmless")]
    extraction = load_extraction("test")
    strata = collections.defaultdict(list)
    for row in rows:
        if row["id"] in extraction:
            strata[(row["organ"], row["kind"])].append(row)
    rng = np.random.default_rng(seed)
    for key in strata:
        rng.shuffle(strata[key])
    chosen = []
    keys = sorted(strata)
    while len(chosen) < n and any(strata[k] for k in keys):
        for key in keys:
            if strata[key] and len(chosen) < n:
                chosen.append(strata[key].pop())
    rng.shuffle(chosen)
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["report_id", "organ", "report_text", "field", "extracted_value", "correct_yes_no", "notes"])
        for row in chosen:
            flat = extraction[row["id"]]["flat"]
            for field, value in sorted(flat.items()):
                writer.writerow([row["id"], row["organ"], row["cand"], field, value, "", ""])
    print("wrote", path, "reports", len(chosen))


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("calls", "freeze-devval", "freeze-stage1", "extract-setr", "score-test", "export-handcheck"))
    parser.add_argument("--judge", choices=tuple(JUDGES), default="gemma")
    parser.add_argument("--set", choices=("devval", "test", "setr"), default="devval")
    parser.add_argument("--max-hours", type=float, default=8.0)
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if args.command == "calls":
        run_calls(args.set, args)
    elif args.command == "freeze-devval":
        freeze_devval(args)
    elif args.command == "export-handcheck":
        export_handcheck()
    elif args.command == "freeze-stage1":
        freeze_stage1(args)
    elif args.command == "extract-setr":
        extract_set_r()
    else:
        evaluate_test(args)


if __name__ == "__main__":
    main()
