"""Step 46 free-text set B, using the frozen Step 45 builder and checks."""

import argparse
import collections
import json
import os
import random
import time
import zlib
import hashlib

from . import step45_freetext as base


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "partA", "step46_own_scorer", "set_B")
MODEL = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"
SEED = 46

base.OUT = OUT
base.P = lambda filename: os.path.join(OUT, filename)
base.MODEL = MODEL
base.SEED = SEED
base.N_DEVVAL = {"dev": 20, "val": 10}
base.N_TEST = 90

_sample_cases = base.sample_cases
_set_a_path = os.path.join(ROOT, "results", "partA", "step45_improve_scorers", "freetext", "set_A.json")
with open(_set_a_path) as _file:
    _set_a_ids = set(json.load(_file)["cases"])


def sample_cases(by_split, split, n_per_organ, rng):
    selected = []
    blocked = set(_set_a_ids)
    for attempt in range(100):
        attempt_rng = random.Random(SEED * 1000 + attempt * 31 + (0 if split == "dev" else 1 if split == "val" else 2))
        candidates = _sample_cases(by_split, split, n_per_organ, attempt_rng)
        for case_id in candidates:
            if case_id not in blocked:
                selected.append(case_id)
                blocked.add(case_id)
        counts = collections.Counter(by_split[split][case_id][0]["organ"] for case_id in selected)
        if all(counts[organ] >= n_per_organ for organ in base.ORGANS):
            return [
                case_id
                for organ in base.ORGANS
                for case_id in [
                    value
                    for value in selected
                    if by_split[split][value][0]["organ"] == organ
                ][:n_per_organ]
            ]
    counts = collections.Counter(by_split[split][case_id][0]["organ"] for case_id in selected)
    raise RuntimeError(f"Could not sample the target without Set A overlap for {split}: {dict(counts)}")


base.sample_cases = sample_cases


def plan(args):
    from . import splits

    os.makedirs(OUT, exist_ok=True)
    splits.load("test", script="usmeta.step46_freetext.plan")
    open(base.P("test_read_logged.flag"), "w").write("locked Step 46 test plan created\n")
    base.cmd_plan(args)
    with open(base.P("plan.json")) as source:
        plan_data = json.load(source)
    with open(os.path.expanduser("~/.cache/huggingface/hub/models--mlx-community--Meta-Llama-3.1-8B-Instruct-4bit/refs/main")) as source:
        model_revision = source.read().strip()
    set_a_ids = _set_a_ids
    plan_data["model_revision"] = model_revision
    with open(base.P("plan.json"), "w") as target:
        json.dump(plan_data, target)
    json.dump(
        {
            "model": MODEL,
            "model_revision": model_revision,
            "seed": SEED,
            "temperature": base.TEMP,
            "max_tokens": base.MAX_TOK,
            "cases": len(json.load(open(base.P("cases.json")))),
            "set_A_overlap": len(set_a_ids & {item["case_id"] for item in plan_data["items"]}),
            "mlx_lm_version": __import__("importlib.metadata", fromlist=["version"]).version("mlx-lm"),
        },
        open(base.P("run_info.json"), "w"),
        indent=1,
    )


def generate(args):
    import mlx.core as mx
    from mlx_lm import generate as mlx_generate, load
    from mlx_lm.sample_utils import make_sampler

    plan = json.load(open(base.P("plan.json")))
    items = plan["items"]
    if os.path.exists(base.P("lod_plan.json")):
        items += json.load(open(base.P("lod_plan.json")))
    cache = base.load_cache()
    deadline = time.time() + args.max_hours * 3600
    order = {"test": 0, "devval": 1}
    items = sorted(items, key=lambda item: (order[item["set"]], item["case_id"], item["id"]))
    todo = [
        item
        for item in items
        if item["id"] not in cache
        and (args.only is None or item["set"] == args.only or item["kind"] == args.only)
    ]
    print("to generate", len(todo), "cached", len(cache), flush=True)
    model, tokenizer = load(MODEL)
    started = time.time()
    count = 0
    with open(base.P("gen_cache.jsonl"), "a") as output:
        for item in todo:
            if time.time() > deadline:
                print("time cap reached after", count, "items", flush=True)
                break
            prompt = tokenizer.apply_chat_template(
                item["messages"], add_generation_prompt=True, tokenize=False
            )
            mx.random.seed(zlib.crc32(f"{SEED}|{item['id']}".encode()) & 0x7FFFFFFF)
            item_started = time.time()
            generated = mlx_generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=base.MAX_TOK,
                sampler=make_sampler(temp=base.TEMP),
            )
            record = {
                "id": item["id"],
                "reply": generated.strip(),
                "seconds": round(time.time() - item_started, 2),
                "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest(),
                "prompt": prompt,
            }
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
            count += 1
            if count % 25 == 0:
                print(count, len(todo), round(time.time() - started), "s", flush=True)
    print("done", count, round(time.time() - started), "s", flush=True)


def extract_set(args):
    from . import step27_extractor as base_extractor
    from . import splits
    from .step45_extractor_v5 import facts_v5

    source = json.load(open(base.P("set_B.json")))
    reports = []
    for case_id, case in source["cases"].items():
        for report in case["true_reports"]:
            reports.append((f"{case_id}|true|{report['style']}", case, report["text"]))
        if case["twin_report"]:
            report = case["twin_report"]
            reports.append((f"{case_id}|twin|{report['style']}", case, report["text"]))
    for item in source.get("lod", []):
        case = source["cases"][item["case_id"]]
        reports.append((item["id"], case, item["text"]))
    stress_path = base.P("stress_reports.json")
    if os.path.exists(stress_path):
        for report in json.load(open(stress_path)):
            reports.append(
                (
                    f"stress|{report['id']}",
                    {"organ": report["organ"]},
                    report["text"],
                )
            )
    human_path = os.path.join(
        ROOT, "results", "partA", "step21d_human_sheet", "human_bench.jsonl"
    )
    for line in open(human_path):
        report = json.loads(line)
        if report.get("kind") != "human":
            continue
        organ = "fetal" if report["organ"] == "fetal head" else report["organ"]
        reports.append(
            (
                f"human|{report['item']}|{report['case_id']}",
                {"organ": organ},
                report["candidate"],
            )
        )

    if not os.path.exists(base.P("test_read_logged.flag")):
        splits.load("test", script="usmeta.step46_freetext.extract")
        open(base.P("test_read_logged.flag"), "w").write("locked Step 46 test extraction\n")
    base_extractor.CACHE = base.P("cache_v5.jsonl")
    base_extractor.OUT = OUT
    instance = base_extractor.Extractor("v5")
    results = {}
    started = time.time()
    for index, (report_id, case, text) in enumerate(reports, 1):
        raw = instance.raw(case["organ"], text)
        flat, ok, strict = facts_v5(case["organ"], raw, text)
        results[report_id] = {"flat": flat, "ok": ok, "strict": strict, "raw": raw}
        if index % 50 == 0:
            print("extract", index, len(reports), round(time.time() - started), "s", flush=True)
    json.dump(results, open(base.P("extraction_v5.json"), "w"), ensure_ascii=False)
    print("saved", len(results), "of", len(reports), flush=True)


def gold_set(args):
    base.cmd_gold(args)
    plan = json.load(open(base.P("plan.json")))
    cases = json.load(open(base.P("cases.json")))
    cache = base.load_cache()
    planned_items = list(plan["items"])
    if os.path.exists(base.P("lod_plan.json")):
        planned_items += json.load(open(base.P("lod_plan.json")))
    dropped = []
    stress_reports = []
    kept_reports = collections.defaultdict(lambda: {"true": [], "twin": None})
    kept_lod = []
    reasons = collections.Counter()
    filter_stats = collections.defaultdict(lambda: collections.Counter())
    for item in planned_items:
        if item["id"] not in cache:
            continue
        reply = cache[item["id"]]["reply"]
        gold_ok, missing = base.gold_check(item["organ"], item["facts"], reply)
        extras = base.extras(item["organ"], item["facts"], reply)
        if gold_ok and not extras:
            report = {"style": item["style"], "text": reply}
            if item["kind"] == "true":
                kept_reports[item["case_id"]]["true"].append(report)
            elif item["kind"] == "twin":
                kept_reports[item["case_id"]]["twin"] = report
            elif item["kind"] == "lod":
                kept_lod.append(
                    {
                        "id": item["id"],
                        "case_id": item["case_id"],
                        "organ": item["organ"],
                        "group": cases[item["case_id"]]["group"],
                        "text": reply,
                        **{key: item[key] for key in ("field", "level", "old", "new")},
                    }
                )
        filter_key = (item["set"], item["organ"])
        filter_stats[filter_key]["generated"] += 1
        filter_stats[filter_key]["missing_gold_dropped"] += int(not gold_ok)
        filter_stats[filter_key]["extras_filter_dropped"] += int(bool(extras))
        filter_stats[filter_key]["kept"] += int(gold_ok and not extras)
        if gold_ok and not extras:
            continue
        reason = "missing_gold" if not gold_ok else "extras_only"
        reasons[(item["set"], item["organ"], reason)] += 1
        dropped_report = {
                "id": item["id"],
                "case_id": item["case_id"],
                "set": item["set"],
                "organ": item["organ"],
                "kind": item["kind"],
                "style": item["style"],
                "text": reply,
                "missing_gold": missing,
                "extras": extras,
                "reference": cases[item["case_id"]]["reference"],
                "facts": item["facts"],
            }
        dropped.append(dropped_report)
        if extras:
            stress_reports.append(dropped_report)
    json.dump(dropped, open(base.P("filter_dropped_reports.json"), "w"), ensure_ascii=False)
    json.dump(stress_reports, open(base.P("stress_reports.json"), "w"), ensure_ascii=False)
    set_b_cases = {}
    for case_id, case in cases.items():
        kept = kept_reports.get(case_id, {"true": [], "twin": None})
        if not kept["true"] and kept["twin"] is None:
            continue
        set_b_cases[case_id] = {
            **case,
            "true_reports": kept["true"],
            "twin_report": kept["twin"],
        }
    json.dump(
        {"cases": set_b_cases, "lod": kept_lod},
        open(base.P("set_B.json"), "w"),
        ensure_ascii=False,
    )
    info_path = base.P("run_info.json")
    info = json.load(open(info_path)) if os.path.exists(info_path) else {}
    try:
        with open(os.path.expanduser("~/.cache/huggingface/hub/models--mlx-community--Meta-Llama-3.1-8B-Instruct-4bit/refs/main")) as source:
            model_revision = source.read().strip()
    except OSError:
        model_revision = None
    info.update(
        {
            "model": MODEL,
            "model_revision": model_revision,
            "seed": SEED,
            "temperature": base.TEMP,
            "max_tokens": base.MAX_TOK,
            "planned_cases": len(cases),
            "set_A_overlap": len(_set_a_ids & set(cases)),
            "generated_reports": len(cache),
            "mlx_lm_version": __import__("importlib.metadata", fromlist=["version"]).version("mlx-lm"),
        }
    )
    info["planned_by_set_kind"] = {
        f"{split}|{kind}": sum(
            planned["set"] == split and planned["kind"] == kind
            for planned in planned_items
        )
        for split in ("devval", "test")
        for kind in ("true", "twin")
    }
    info["generated_by_set_kind"] = {
        key: sum(
            planned["id"] in cache
            and f"{planned['set']}|{planned['kind']}" == key
            for planned in planned_items
        )
        for key in info["planned_by_set_kind"]
    }
    info["test_core_complete"] = (
        info["generated_by_set_kind"].get("test|true", 0)
        + info["generated_by_set_kind"].get("test|twin", 0)
        == info["planned_by_set_kind"].get("test|true", 0)
        + info["planned_by_set_kind"].get("test|twin", 0)
    )
    json.dump(info, open(info_path, "w"), indent=1)
    filter_summary = {}
    for (split, organ), counts in filter_stats.items():
        total = counts["generated"]
        filter_summary[f"{split}|{organ}"] = {
            **counts,
            "missing_gold_drop_share": counts["missing_gold_dropped"] / total if total else None,
            "extras_filter_drop_share": counts["extras_filter_dropped"] / total if total else None,
            "kept_share": counts["kept"] / total if total else None,
        }
    json.dump(
        {"by_set_organ": filter_summary, "all_filter_dropped": len(dropped), "stress_reports": len(stress_reports)},
        open(base.P("filter_summary.json"), "w"),
        indent=1,
    )
    print("saved stress reports", len(stress_reports), "all dropped", len(dropped), "drop reasons", dict(reasons), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "generate", "gold", "extract"))
    parser.add_argument("--max-hours", type=float, default=5.5)
    parser.add_argument("--only", default=None)
    parser.add_argument("--refresh-lod", action="store_true")
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    {"plan": plan, "generate": generate, "gold": gold_set, "extract": extract_set}[args.command](args)


if __name__ == "__main__":
    main()
