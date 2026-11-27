"""Step 48 machine steps on Set C (development data now).

retry-raw : re-ask every Gemma audit call on Set C that returned no readable reply,
            saving the raw text (Step 47 discarded it), for the parser fix (candidate P).
llama-setc: run the Llama audit prompts on all Set C core reports that need an audit
            (Step 47 ran Llama on a 300-report subset only), for candidate L.
"""
import collections, hashlib, json, os, re, time

from . import step47_audit_route as s47

OUT = os.path.join(os.path.dirname(s47.OUT), "step48_confirm")
P = lambda name: os.path.join(OUT, name)


def lenient_parse(raw):
    """Candidate P: accept JSON in code fences, single quotes, trailing commas, extra text."""
    if not raw:
        return None
    parsed = s47.parse_audit(raw)
    if parsed is not None:
        return parsed
    text = re.sub(r"```(?:json)?", "", raw)
    start = text.find("{")
    if start < 0:
        return None
    depth, end = 0, None
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    body = text[start:end] if end else text[start:] + "}" * max(depth, 0)
    body = re.sub(r",\s*([}\]])", r"\1", body)
    for candidate in (body, body.replace("'", '"')):
        parsed = s47.parse_audit(candidate)
        if parsed is not None:
            return parsed
    return None


def retry_raw(args):
    os.makedirs(OUT, exist_ok=True)
    path = P("gemma_raw_retry_setc.jsonl")
    done = set()
    if os.path.exists(path):
        done = {(r["id"], r["variant"]) for r in map(json.loads, open(path))}
    rows = [r for r in s47.set_c_candidates() if r["kind"] in ("error", "harmless")]
    extraction = s47.load_extraction("test")
    audits = s47.current_judge_rows("test")
    runner = s47.Runner("gemma")
    deadline = time.time() + args.max_hours * 3600
    todo = [
        (row, key)
        for row in rows
        if row["id"] in extraction and s47.audits_needed(row, extraction)
        for key in s47.PROMPT_KEYS
        if audits.get(row["id"], {}).get(key, {}).get("parsed") is None and (row["id"], key) not in done
    ]
    print("retry-raw todo", len(todo), flush=True)
    with open(path, "a") as out:
        for n, (row, key) in enumerate(todo, 1):
            if time.time() > deadline:
                print("time cap reached", n - 1, flush=True)
                return
            raw = runner.llm._run(s47.prompt_for(key, row["ref"], row["cand"]))
            out.write(json.dumps({"id": row["id"], "variant": key, "raw": raw,
                                  "strict": s47.parse_audit(raw) is not None,
                                  "lenient": lenient_parse(raw) is not None}, ensure_ascii=False) + "\n")
            out.flush()
            if n % 25 == 0:
                print("retry-raw", n, "of", len(todo), flush=True)
    print("retry-raw complete", len(todo), flush=True)


def llama_setc(args):
    s47.llama_subset = lambda rows: {r["id"] for r in rows}
    args.judge = "llama"
    s47.run_calls("test", args)


# ---------------- Set C-F / Set D rows and judge calls (saved raw text always) ----------------
SET_PATHS = {"setcf": ("set_CF", "set_C.json"), "setd": ("set_D", "set_D.json")}


def rows_for(which):
    folder, name = SET_PATHS[which]
    source = json.load(open(P(os.path.join(folder, name))))
    rows = []
    for case_id, case in source["cases"].items():
        variant = case.get("variant") or ("second_twin" if case_id.endswith("#b") else "standard")
        for report in case["true_reports"]:
            rows.append(dict(id=f"{case_id}|true|{report['style']}", case=case_id, group=case["group"], organ=case["organ"],
                             dataset=case["dataset"], kind="harmless", severity=None, ref=case["reference"], gold=case["gold"],
                             cand=report["text"], variant=variant))
        if case["twin_report"]:
            report = case["twin_report"]
            rows.append(dict(id=f"{case_id}|twin|{report['style']}", case=case_id, group=case["group"], organ=case["organ"],
                             dataset=case["dataset"], kind="error", severity=case["twin_severity"], ref=case["reference"],
                             gold=case["gold"], cand=report["text"], variant=variant))
    return rows


def extraction_for(which):
    folder, _ = SET_PATHS[which]
    return json.load(open(P(os.path.join(folder, "extraction_v5.json"))))


def calls_path(which, judge):
    return P(f"audit_calls_{which}{s47.JUDGES[judge]['suffix']}.jsonl")


def judge_calls_for(which, judge):
    out = collections.defaultdict(dict)
    path = calls_path(which, judge)
    if os.path.exists(path):
        for r in map(json.loads, open(path)):
            out[r["id"]][r["variant"]] = r
    return out


def subset_300(rows):
    core = sorted(rows, key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())
    return {r["id"] for r in core[:300]}


def run_set_calls(args):
    which, judge = args.which, args.judge
    rows = rows_for(which)
    extraction = extraction_for(which)
    if which == "setd" and judge != "gemma":
        keep = subset_300(rows)
        rows = [r for r in rows if r["id"] in keep]
    done = judge_calls_for(which, judge)
    runner = s47.Runner(judge)
    deadline = time.time() + args.max_hours * 3600
    new = 0
    hpath = P(f"holistic_{which}.jsonl")
    holistic = {json.loads(l)["id"] for l in open(hpath)} if os.path.exists(hpath) else set()
    with open(calls_path(which, judge), "a") as out, open(hpath, "a") as hout:
        for n, row in enumerate(rows, 1):
            if row["id"] not in extraction:
                continue
            if s47.is_rule_major(row, extraction[row["id"]])[1]:
                continue
            for key in s47.PROMPT_KEYS:
                if key in done.get(row["id"], {}):
                    continue
                if time.time() > deadline:
                    print("time cap reached at row", n, "of", len(rows), flush=True)
                    return
                raw = runner.llm._run(s47.prompt_for(key, row["ref"], row["cand"]))
                out.write(json.dumps({"id": row["id"], "variant": key, "raw": raw, "parsed": s47.parse_audit(raw)},
                                     ensure_ascii=False) + "\n")
                out.flush()
                new += 1
            # single-call holistic judge (Step 46), Gemma only, rows with no rule difference: simple-judge baseline (amendment 1 item 4b)
            if judge == "gemma" and not s47.is_rule_major(row, extraction[row["id"]])[0] and row["id"] not in holistic:
                if time.time() > deadline:
                    print("time cap reached at row", n, "of", len(rows), flush=True)
                    return
                res = runner.old_holistic(row["ref"], row["cand"])
                hout.write(json.dumps({"id": row["id"], "result": res}) + "\n")
                hout.flush()
                holistic.add(row["id"])
                new += 1
            if n % 25 == 0:
                print(which, judge, "rows", n, "of", len(rows), "new calls", new, flush=True)
    print(which, judge, "CALLS COMPLETE rows", len(rows), "new calls", new, flush=True)


# ---------------- Stage 1 (Set C, saved replies only, no model calls) ----------------
P2_TYPE = {"contradicted": "contradicted", "unsupported": "unsupported", "omitted": "omitted",
           "added": "unsupported", "added unsupported": "unsupported"}
P2_DROP = {"none", "supported"}
SEV_RANK = {"major": 3, "minor": 2, "unsure": 1}


def parse_p2(raw):
    """Candidate P2 (PARSER_FINDING.md): read the issues, derive the verdict from them."""
    if not raw:
        return None
    text = re.sub(r"```(?:json)?", "", raw).replace("<end_of_turn>", "")
    start = text.find("{")
    if start < 0:
        return None
    depth, end = 0, None
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        return None  # cut off: stays unparsed (routed)
    body = re.sub(r",\s*([}\]])", r"\1", text[start:end])
    try:
        obj = json.loads(body)
    except json.JSONDecodeError:
        try:
            obj = json.loads(body.replace("'", '"'))
        except json.JSONDecodeError:
            return None
    issues = obj.get("issues")
    if not isinstance(issues, list):
        return None
    out = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        kind = str(issue.get("type", "")).lower().strip()
        if kind in P2_DROP:
            continue
        sev = str(issue.get("severity", "")).lower().strip()
        sev = "major" if sev in ("major", "critical", "high") else "minor" if sev in ("minor", "low") else "unsure"
        out.append({"candidate_quote": str(issue.get("candidate_quote", "")),
                    "reference_quote": str(issue.get("reference_quote", "")),
                    "type": P2_TYPE.get(kind, "unsupported"), "severity": sev,
                    "reason": str(issue.get("reason", ""))})
    verdict = max((i["severity"] for i in out), key=SEV_RANK.get) if out else "clean"
    if str(obj.get("verdict", "")).lower().strip() == "unsure":
        verdict = "unsure"
    return {"verdict": verdict, "issues": out}


def judge_reasons(parsed, mode="s1"):
    """The judge part of the S1 rule (s47.s1_route without the rule checks).
    mode "majority": a major claim counts only if at least 2 of the 3 readings make it, and
    order/reword disagreement alone does not route (unparsed and unsure still route)."""
    reasons = s47.s1_route(parsed, [], [])[1]
    if mode == "majors":
        return [r for r in reasons if r in ("unparsed_judge_reply", "judge_unsure", "judge_major_claim")]
    if mode != "majority":
        return reasons
    replies = [parsed.get(k) for k in s47.PROMPT_KEYS]
    majors = sum(1 for r in replies if r is not None and any(i["severity"] == "major" for i in r["issues"]))
    keep = [r for r in reasons if r in ("unparsed_judge_reply", "judge_unsure")]
    if majors >= 2:
        keep.append("judge_major_claim_2of3")
    return keep


RETRY_RAW = None


def retry_raw_text(row_id, key):
    """Step 47 did not save raw text for unparsed Gemma replies; use the re-asked raw (same prompt, greedy)."""
    global RETRY_RAW
    if RETRY_RAW is None:
        path = P("gemma_raw_retry_setc.jsonl")
        RETRY_RAW = {(r["id"], r["variant"]): r["raw"] for r in map(json.loads, open(path))} if os.path.exists(path) else {}
    return RETRY_RAW.get((row_id, key))


def _parsed(calls, row_id, parser, judge="gemma"):
    out = {}
    for key in s47.PROMPT_KEYS:
        call = calls.get(row_id, {}).get(key)
        if call is None:
            out[key] = "MISSING"
        elif parser == "strict":
            out[key] = call.get("parsed")
        else:
            raw = call.get("raw") or (retry_raw_text(row_id, key) if judge == "gemma" else None)
            out[key] = parse_p2(raw)
    return out


TRIALS = [
    ("S48-T1", "S1 baseline: Gemma, strict parser (Step 47 rule)", ("gemma",), "strict", "any"),
    ("S48-T2", "S1 rule, Gemma, parser P2", ("gemma",), "p2", "any"),
    ("S48-T3", "S1 rule, Llama, strict parser", ("llama",), "strict", "any"),
    ("S48-T4", "S1 rule, Llama, parser P2", ("llama",), "p2", "any"),
    ("S48-T5", "S1 rule, Gemma P2 OR Llama P2 (route if either judge part routes)", ("gemma", "llama"), "p2", "any"),
    ("S48-T6", "S1 rule, Gemma P2 AND Llama P2 (judge part routes only if both do)", ("gemma", "llama"), "p2", "all"),
    ("S48-T7", "Rules only: route on any rule difference, no judge (baseline, amendment 1 item 8)", (), "none", "any"),
    ("S48-T8", "S1 rule, Gemma P2, judge major claim needs 2 of 3 readings (amendment 1 item 8)", ("gemma",), "p2", "majority"),
    ("S48-T9", "S1 rule, Gemma P2 OR Llama P2, judge part = major claim / unparsed / unsure only (reading disagreement alone does not route)", ("gemma", "llama"), "p2", "majors"),
    ("S48-T10", "S1 rule, Gemma P2, judge part = major claim / unparsed / unsure only (reading disagreement alone does not route)", ("gemma",), "p2", "majors"),
]


def trial_routes(rows, extraction, calls, judges, parser, combine):
    routes, missing = {}, 0
    for row in rows:
        diffs, major = s47.is_rule_major(row, extraction[row["id"]])
        reasons = [f"rule_major:{f}" for f in major] + (["rule_difference"] if diffs else [])
        if not major:
            per_judge = []
            for j in judges:
                parsed = _parsed(calls[j], row["id"], parser, j)
                if any(v == "MISSING" for v in parsed.values()):
                    missing += 1
                    parsed = {k: (None if v == "MISSING" else v) for k, v in parsed.items()}
                per_judge.append([f"{j}:{r}" for r in judge_reasons(parsed, combine if combine in ("majority", "majors") else "s1")])
            if combine in ("any", "majority", "majors"):
                reasons += [r for jr in per_judge for r in jr]
            elif per_judge and all(per_judge):
                reasons += [r for jr in per_judge for r in jr]
        routes[row["id"]] = (bool(reasons), reasons)
    return routes, missing


def summarize(rows, routes, n_judges):
    major = [r for r in rows if r["kind"] == "error" and r.get("severity") in (2, 3)]
    fabr = [r for r in major if r.get("variant") == "fabrication"]
    norm = [r for r in rows if r.get("variant") == "normal_addition"]
    errors = [r for r in rows if r["kind"] == "error"]
    harmless = [r for r in rows if r["kind"] == "harmless"]
    m = lambda xs: sum(routes[r["id"]][0] for r in xs) / len(xs)
    return {"n_major_critical": len(major), "catch_major_critical": m(major),
            "missed_major_critical": sum(not routes[r["id"]][0] for r in major),
            "catch_all_errors": m(errors), "harmless_routed": m(harmless), "n_harmless": len(harmless),
            "calls_per_audited_report": 3 * n_judges,
            "n_fabrication": len(fabr), "catch_fabrication": (sum(routes[r["id"]][0] for r in fabr) / len(fabr)) if fabr else None,
            "n_normal_addition": len(norm), "normal_addition_routed": (sum(routes[r["id"]][0] for r in norm) / len(norm)) if norm else None}  # 0 for rules only


def stage1(args):
    import collections, subprocess
    rows = [r for r in s47.set_c_candidates() if r["kind"] in ("error", "harmless")]
    extraction = s47.load_extraction("test")
    rows = [r for r in rows if r["id"] in extraction]
    calls = {j: s47.current_judge_rows("test", j) for j in ("gemma", "llama")}
    if os.path.exists(P(os.path.join("set_CF", "extraction_v5.json"))):
        cf_rows = rows_for("setcf")
        cf_ex = extraction_for("setcf")
        cf_rows = [r for r in cf_rows if r["id"] in cf_ex]
        extraction = dict(extraction, **cf_ex)
        for j in ("gemma", "llama"):
            calls[j] = dict(calls[j], **judge_calls_for("setcf", j))
        rows = rows + cf_rows
        print("Set C-F rows added:", len(cf_rows), flush=True)
    elif not args.dry:
        raise RuntimeError("Set C-F (off-schema development errors) must be extracted and judged before Stage 1 (amendment 1 item 8).")
    try:
        git = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        git = ""
    results = []
    for tid, desc, judges, parser, combine in TRIALS:
        routes, missing = trial_routes(rows, extraction, calls, judges, parser, combine)
        s = summarize(rows, routes, len(judges))
        s.update(trial=tid, description=desc, judges=judges, parser=parser, combine=combine, missing_calls=missing)
        reasons = collections.Counter(r.split(":")[-1] if r.startswith(("gemma:", "llama:")) else r.split(":")[0]
                                      for r in rows if r["kind"] == "harmless" for r in routes[r["id"]][1])
        s["harmless_route_reasons"] = dict(reasons.most_common())
        results.append(s)
        if s["n_fabrication"]:
            print(f"   fabrication catch {s['catch_fabrication']:.3f} of {s['n_fabrication']}; normal-statement routed {s['normal_addition_routed']:.3f} of {s['n_normal_addition']}", flush=True)
        print(f"{tid} catch {s['catch_major_critical']:.3f} (missed {s['missed_major_critical']}/{s['n_major_critical']}) "
              f"harmless routed {s['harmless_routed']:.3f} missing calls {missing} | {desc}", flush=True)
        if not args.dry:
            _orig_P = s47.P; s47.P = P
            s47.log_trial(trial_id=tid, date=time.strftime("%Y-%m-%d"), description=desc, code_git_hash=git,
                          judge="+".join(judges), dev_auroc="",
                          catch_major_critical_at_30pct_harmless=(round(s["catch_major_critical"], 4)
                                                                  if s["harmless_routed"] <= 0.30 else "not eligible (harmless > 30%)"),
                          model_calls_per_report=s["calls_per_audited_report"],
                          notes=f"Set C + Set C-F saved replies; harmless routed {s['harmless_routed']:.4f}; fabrication catch {s['catch_fabrication']}; missing calls {missing}")
            s47.P = _orig_P
    eligible = [s for s in results if s["harmless_routed"] <= 0.30 and s["missing_calls"] == 0]
    eligible.sort(key=lambda s: (-s["catch_major_critical"], s["harmless_routed"], s["calls_per_audited_report"]))
    out = {"trials": results, "winner": eligible[0]["trial"] if eligible else None,
           "rule": "max catch of major/critical at harmless routed <= 30%; ties: lower harmless routed, then fewer calls"}
    if not args.dry:
        json.dump(out, open(P("stage1_results.json"), "w"), indent=1)
    print("WINNER", out["winner"], flush=True)


def freeze(args):
    import hashlib
    path = P("frozen_s2.json")
    if os.path.exists(path):
        raise RuntimeError("frozen_s2.json already exists; refusing to overwrite.")
    if os.path.exists(P("set_D")):
        raise RuntimeError("Set D already exists; S2 can no longer be frozen.")
    res = json.load(open(P("stage1_results.json")))
    win = next(t for t in res["trials"] if t["trial"] == res["winner"])
    sha = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
    frozen = {"primary_variant": f"S2 = {win['trial']}: {win['description']}", "trial": win,
              "judges": win["judges"], "parser": win["parser"], "combine": win["combine"],
              "selection_rule": res["rule"], "stage1_trials_logged": len(res["trials"]),
              "step48_code_sha256": sha(__file__), "step47_code_sha256": sha(s47.__file__),
              "prereg_sha256": sha(P("PREREG.md")),
              "amendment1_sha256": sha(P("PREREG_AMENDMENT_1.md")) if os.path.exists(P("PREREG_AMENDMENT_1.md")) else None}
    frozen["sha256"] = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    json.dump(frozen, open(path, "w"), indent=1)
    print("FROZEN", frozen["primary_variant"], frozen["sha256"], flush=True)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("retry-raw", "llama-setc", "stage1", "freeze", "calls"))
    p.add_argument("--which", choices=("setcf", "setd"), default="setcf")
    p.add_argument("--judge", choices=("gemma", "llama"), default="gemma")
    p.add_argument("--max-hours", type=float, default=8.0)
    p.add_argument("--dry", action="store_true", help="stage1: print only, log nothing")
    a = p.parse_args()
    {"retry-raw": retry_raw, "llama-setc": llama_setc, "stage1": stage1, "freeze": freeze, "calls": run_set_calls}[a.command](a)


if __name__ == "__main__":
    main()
