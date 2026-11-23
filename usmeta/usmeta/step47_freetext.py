"""Fresh Mistral-written Set C for the Step 47 audit-and-route evaluator.

Uses the frozen Step 45 fact builder and gold filters, with a case sampler that
excludes prior free-text report sets. The locked test split is logged once at
plan time; later commands consume only the saved plan and generated cache.
"""

import argparse
import collections
import hashlib
import json
import os
import random
import time
import zlib

from . import splits, step45_freetext as base


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "partA", "step47_audit_route", "set_C")
P = lambda filename: os.path.join(OUT, filename)
MODEL = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
SEED = 47
N_TEST_PER_ORGAN = 120

# Step 45 builder, writer prompt, lexicon and gold filters are reused unchanged.
base.OUT = OUT
base.P = P
base.MODEL = MODEL
base.SEED = SEED
base.N_DEVVAL = {"dev": 0, "val": 0}
base.N_TEST = N_TEST_PER_ORGAN


def prior_report_case_ids():
    """Case IDs used by prior free-text/model-report sets, including Set A/B."""
    blocked = set()
    json_paths = (
        os.path.join(ROOT, "results/partA/step11_qwen_real_reports/cases.json"),
        os.path.join(ROOT, "results/partA/step11_qwen_real_reports_rerun2/cases.json"),
        os.path.join(ROOT, "results/partA/step45_improve_scorers/freetext/set_A.json"),
        os.path.join(ROOT, "results/partA/step46_own_scorer/set_B/set_B.json"),
        os.path.join(ROOT, "results/partA/step43_extractor_v4/selected.json"),
    )
    for path in json_paths:
        if not os.path.exists(path):
            continue
        obj = json.load(open(path))
        if isinstance(obj, dict):
            blocked.update(obj.get("cases", obj).keys())
        elif isinstance(obj, list):
            blocked.update(row["case_id"] for row in obj if row.get("case_id"))
    jsonl_paths = (
        os.path.join(ROOT, "results/partA/step14_medgemma/reports_medgemma.jsonl"),
        os.path.join(ROOT, "results/partA/step28_natural_errors/reports.jsonl"),
        os.path.join(ROOT, "results/partA/step32_extractor_v3/reports.jsonl"),
        os.path.join(ROOT, "results/partA/step43_extractor_v4/reports.jsonl"),
        os.path.join(ROOT, "results/partA/step21d_human_sheet/human_bench.jsonl"),
    )
    for path in jsonl_paths:
        if not os.path.exists(path):
            continue
        for line in open(path):
            row = json.loads(line)
            if row.get("case_id"):
                blocked.add(row["case_id"])
    return blocked


def sample_cases(by_split, split, n_per_organ, rng):
    """Select fresh cases evenly across datasets, skipping all prior report IDs."""
    if split != "test" or not n_per_organ:
        return []
    blocked = prior_report_case_ids()
    selected = []
    for organ in base.ORGANS:
        by_dataset = collections.defaultdict(list)
        for case_id, rows in sorted(by_split[split].items()):
            if case_id in blocked or not rows or rows[0].get("organ") != organ:
                continue
            if not any(row.get("kind") == "error" for row in rows):
                continue
            by_dataset[rows[0]["dataset"]].append(case_id)
        datasets = sorted(by_dataset)
        for dataset in datasets:
            rng.shuffle(by_dataset[dataset])
        picked = []
        cursor = 0
        while len(picked) < n_per_organ and any(by_dataset.values()):
            dataset = datasets[cursor % len(datasets)]
            cursor += 1
            if by_dataset[dataset]:
                picked.append(by_dataset[dataset].pop())
        if len(picked) < n_per_organ:
            raise RuntimeError(
                f"Only {len(picked)} fresh {organ} test cases remain; "
                f"Step 47 planned {n_per_organ}."
            )
        selected.extend(picked)
    return selected


base.sample_cases = sample_cases


def plan(args):
    os.makedirs(OUT, exist_ok=True)
    plan_path = P("plan.json")
    flag = P("test_read_logged.flag")
    if os.path.exists(plan_path):
        print("Set C plan already saved; reusing the single logged plan.", flush=True)
        return
    if os.path.exists(flag):
        raise RuntimeError("A test read was logged but its plan file is missing; do not reread the test split.")
    thresholds_path = os.path.join(os.path.dirname(OUT), "thresholds.json")
    if not os.path.exists(thresholds_path):
        raise RuntimeError(
            "Freeze development-only routes and comparator cutoffs before planning Set C."
        )
    threshold_info = json.load(open(thresholds_path))
    threshold_sha = threshold_info.pop("sha256", None)
    if threshold_sha != hashlib.sha256(
        json.dumps(threshold_info, sort_keys=True).encode()
    ).hexdigest():
        raise RuntimeError("Frozen development thresholds failed their SHA-256 check.")
    threshold_info["sha256"] = threshold_sha
    if threshold_info.get("prompt_sha256") != hashlib.sha256(
        json.dumps(json.load(open(os.path.join(os.path.dirname(OUT), "prompts.json"))), sort_keys=True).encode()
    ).hexdigest():
        raise RuntimeError("Frozen thresholds do not match the committed audit prompts.")
    if not threshold_info.get("sha256"):
        raise RuntimeError("Frozen thresholds are missing their content hash.")

    model_root = os.path.expanduser(
        "~/.cache/huggingface/hub/models--mlx-community--Mistral-7B-Instruct-v0.3-4bit"
    )
    refs_main = os.path.join(model_root, "refs", "main")
    if not os.path.exists(refs_main):
        raise RuntimeError(f"Writer model must be downloaded before Set C planning: {MODEL}")
    revision = open(refs_main).read().strip()
    snapshot = os.path.join(model_root, "snapshots", revision)
    weight_files = [
        os.path.join(root, name)
        for root, _, names in os.walk(snapshot)
        for name in names
        if name.endswith((".safetensors", ".gguf", ".bin"))
    ]
    if not weight_files:
        raise RuntimeError(f"No local weight file found for pinned writer revision {revision}.")
    model_hashes = {}
    for path in sorted(weight_files):
        digest = hashlib.sha256()
        with open(path, "rb") as weight:
            for block in iter(lambda: weight.read(1024 * 1024), b""):
                digest.update(block)
        model_hashes[os.path.relpath(path, snapshot)] = digest.hexdigest()

    if not os.path.exists(flag):
        splits.load("test", script="usmeta.step47_freetext.plan")
        open(flag, "w").write("locked Step 47 test plan created\n")
    base.cmd_plan(args)
    cases = json.load(open(P("cases.json")))
    plan_data = json.load(open(P("plan.json")))
    blocked = prior_report_case_ids()
    prompt_payload = {
        "system": base.SYS,
        "styles": base.STYLE_TXT,
        "writer_model": MODEL,
        "temperature": base.TEMP,
        "seed": SEED,
        "max_tokens": base.MAX_TOK,
    }
    info = {
        "step": 47,
        "set": "C",
        "writer_model": MODEL,
        "writer_revision": revision,
        "writer_snapshot": snapshot,
        "writer_weight_sha256": model_hashes,
        "seed": SEED,
        "temperature": base.TEMP,
        "max_tokens": base.MAX_TOK,
        "mlx_lm_version": __import__("importlib.metadata", fromlist=["version"]).version("mlx-lm"),
        "planned_cases": len(cases),
        "planned_by_organ": dict(collections.Counter(c["organ"] for c in cases.values())),
        "prior_report_case_ids_blocked": len(blocked),
        "overlap_with_prior_report_case_ids": len(set(cases) & blocked),
        "test_read_script": "usmeta.step47_freetext.plan",
        "test_core_complete": False,
        "writer_prompt_sha256": hashlib.sha256(
            json.dumps(prompt_payload, sort_keys=True).encode()
        ).hexdigest(),
    }
    json.dump(info, open(P("run_info.json"), "w"), indent=1)


def generate(args):
    import mlx.core as mx
    from mlx_lm import generate as mlx_generate, load
    from mlx_lm.sample_utils import make_sampler

    plan_data = json.load(open(P("plan.json")))
    items = list(plan_data["items"])
    lod_path = P("lod_plan.json")
    if os.path.exists(lod_path):
        items += json.load(open(lod_path))
    cache = base.load_cache()
    todo = [
        item
        for item in items
        if item["id"] not in cache
        and (args.only is None or item["set"] == args.only or item["kind"] == args.only)
    ]
    deadline = time.time() + args.max_hours * 3600
    print("to generate", len(todo), "cached", len(cache), flush=True)
    run_info = json.load(open(P("run_info.json")))
    model, tokenizer = load(run_info["writer_snapshot"])
    started = time.time()
    with open(P("gen_cache.jsonl"), "a") as output:
        for index, item in enumerate(todo, 1):
            if time.time() >= deadline:
                print("time cap reached after", index - 1, "items", flush=True)
                break
            prompt = tokenizer.apply_chat_template(
                item["messages"], add_generation_prompt=True, tokenize=False
            )
            mx.random.seed(zlib.crc32(f"{SEED}|{item['id']}".encode()) & 0x7FFFFFFF)
            item_started = time.time()
            reply = mlx_generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=base.MAX_TOK,
                sampler=make_sampler(temp=base.TEMP),
            )
            output.write(
                json.dumps(
                    {
                        "id": item["id"],
                        "reply": reply.strip(),
                        "seconds": round(time.time() - item_started, 2),
                        "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest(),
                        "prompt": prompt,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            output.flush()
            if index % 25 == 0:
                print(index, len(todo), round(time.time() - started), "s", flush=True)
    print("done", len(todo), round(time.time() - started), "s", flush=True)


def gold(args):
    """Use the frozen Step 45 filter, then save the equivalent named Set C."""
    plan_data = json.load(open(P("plan.json")))
    core_ids = {
        item["id"]
        for item in plan_data["items"]
        if item["set"] == "test" and item["kind"] in ("true", "twin")
    }
    cache = base.load_cache()
    if not core_ids <= set(cache):
        raise RuntimeError(
            f"Set C core generation is incomplete ({len(core_ids & set(cache))}/{len(core_ids)} reports); resume generate before gold."
        )
    base.cmd_gold(args)
    set_a = json.load(open(P("set_A.json")))
    json.dump(set_a, open(P("set_C.json"), "w"), ensure_ascii=False)
    items = list(plan_data["items"])
    if os.path.exists(P("lod_plan.json")):
        items += json.load(open(P("lod_plan.json")))
    cases = json.load(open(P("cases.json")))
    cache = base.load_cache()
    stress = []
    for item in items:
        if item["id"] not in cache:
            continue
        text = cache[item["id"]]["reply"]
        extra = base.extras(item["organ"], item["facts"], text)
        if not extra:
            continue
        case = cases[item["case_id"]]
        stress.append(
            {
                "id": item["id"],
                "case_id": item["case_id"],
                "set": item["set"],
                "organ": item["organ"],
                "kind": item["kind"],
                "severity": case.get("twin_severity") if item["kind"] == "twin" else None,
                "reference": case["reference"],
                "gold": item["facts"],
                "text": text,
                "extras": extra,
            }
        )
    json.dump(stress, open(P("stress_reports.json"), "w"), ensure_ascii=False)
    info = json.load(open(P("run_info.json")))
    info["kept_cases"] = len(set_a["cases"])
    expected_core_ids = {
        item["id"]
        for item in items
        if item["set"] == "test" and item["kind"] in ("true", "twin")
    }
    generated_ids = set(cache)
    info["test_core_expected_reports"] = len(expected_core_ids)
    info["test_core_generated_reports"] = len(expected_core_ids & generated_ids)
    info["test_core_generated_complete"] = expected_core_ids <= generated_ids
    info["test_core_kept_cases"] = sum(
        case.get("set") == "test" and bool(case["true_reports"])
        for case in set_a["cases"].values()
    )
    kept_test = {
        case_id: case
        for case_id, case in set_a["cases"].items()
        if case.get("set") == "test" and case["true_reports"]
    }
    info["test_core_kept_cases_by_organ"] = dict(
        collections.Counter(case["organ"] for case in kept_test.values())
    )
    info["test_core_kept_groups_by_organ"] = {
        organ: len({case["group"] for case in kept_test.values() if case["organ"] == organ})
        for organ in base.ORGANS
    }
    info["test_core_complete"] = bool(info["test_core_generated_complete"])
    current_lod_ids = {item["id"] for item in json.load(open(P("lod_plan.json"))) if item["set"] == "test"} if os.path.exists(P("lod_plan.json")) else set()
    info["test_lod_expected_reports"] = len(current_lod_ids)
    info["test_lod_generated_reports"] = len(current_lod_ids & generated_ids)
    info["test_lod_generated_complete"] = current_lod_ids <= generated_ids
    info["stress_reports"] = len(stress)
    json.dump(info, open(P("run_info.json"), "w"), indent=1)
    print("saved Set C", len(set_a["cases"]), "cases and", len(stress), "stress reports", flush=True)


def extract(args):
    from . import step27_extractor as extractor
    from .step45_extractor_v5 import facts_v5

    info = json.load(open(P("run_info.json")))
    if not info.get("test_core_generated_complete") or not info.get("test_lod_generated_complete"):
        raise RuntimeError("Set C core and LOD generation must be complete before extraction.")
    source = json.load(open(P("set_C.json")))
    reports = []
    for case_id, case in source["cases"].items():
        for report in case["true_reports"]:
            reports.append((f"{case_id}|true|{report['style']}", case, report["text"]))
        if case["twin_report"]:
            report = case["twin_report"]
            reports.append((f"{case_id}|twin|{report['style']}", case, report["text"]))
    for item in source.get("lod", []):
        reports.append((item["id"], source["cases"][item["case_id"]], item["text"]))
    for report in json.load(open(P("stress_reports.json"))):
        reports.append((f"stress|{report['id']}", {"organ": report["organ"]}, report["text"]))
    extractor.CACHE = P("cache_v5.jsonl")
    extractor.OUT = OUT
    instance = extractor.Extractor("v5")
    results = {}
    started = time.time()
    for index, (report_id, case, text) in enumerate(reports, 1):
        raw = instance.raw(case["organ"], text)
        flat, ok, strict = facts_v5(case["organ"], raw, text)
        results[report_id] = {"flat": flat, "ok": ok, "strict": strict, "raw": raw}
        if index % 50 == 0:
            print("extract", index, len(reports), round(time.time() - started), "s", flush=True)
    json.dump(results, open(P("extraction_v5.json"), "w"), ensure_ascii=False)
    info = json.load(open(P("run_info.json")))
    info["extracted_reports"] = len(results)
    json.dump(info, open(P("run_info.json"), "w"), indent=1)
    print("saved", len(results), "of", len(reports), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "generate", "gold", "extract"))
    parser.add_argument("--max-hours", type=float, default=5.5)
    parser.add_argument("--only", default=None)
    parser.add_argument("--refresh-lod", action="store_true")
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    {"plan": plan, "generate": generate, "gold": gold, "extract": extract}[args.command](args)


if __name__ == "__main__":
    main()
