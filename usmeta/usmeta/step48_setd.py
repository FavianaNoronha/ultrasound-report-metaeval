"""Step 48 Set D: fresh text on the test-split scans of Set B and Set C, written by Phi-3.5-mini (seed 48).

Design (PREREG.md + PREREG_AMENDMENT_1.md item 7): per case, one harmless rewording (style rotated by case)
and two planted-error twins (two different bench errors where possible; the second twin is stored as case
'<id>#b' in the same group, so all downstream Step 47 code works unchanged). Gold filter, LOD and
extraction are the Step 47 code with only the paths, writer and seed changed.

Commands: plan -> generate -> gold -> generate (LOD) -> gold -> extract
"""
import argparse, collections, hashlib, json, os, random, time, zlib

from . import step45_freetext as base
from . import step47_freetext as s47f
from . import schema
from . import step48_fab as fab
from . import step48_devfab as devfab

ROOT = s47f.ROOT
# DEVIATIONS.md 2: the Phi-3.5 Set D (folder set_D) kept too few reports; Set D2 (folder set_D2) is written by
# Llama-3.1-8B-Instruct with the same plan, seed and filter. Choose with env STEP48_WRITER=phi|llama (default llama).
WRITER = os.environ.get("STEP48_WRITER", "llama")
OUT = os.path.join(ROOT, "results", "partA", "step48_confirm", "set_D" if WRITER == "phi" else "set_D2")
P = lambda name: os.path.join(OUT, name)
MODEL = {"phi": "mlx-community/Phi-3.5-mini-instruct-4bit", "llama": "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"}[WRITER]
SEED = 48

# reuse Step 47 generate / gold / extract with new paths, writer and seed
base.OUT, base.P, base.MODEL, base.SEED = OUT, P, MODEL, SEED
s47f.OUT, s47f.P, s47f.MODEL, s47f.SEED = OUT, P, MODEL, SEED

# DEVIATIONS.md 1: Phi-3.5 does not stop at its <|end|> turn marker in mlx-lm, so replies continue with a
# repeated '<|assistant|>' turn. Every reply is cut at the first '<|end|>' (or '<|assistant|>') before the gold filter.
_load_cache = base.load_cache


def _clean(text):
    for marker in ("<|end|>", "<|assistant|>", "<|endoftext|>"):
        text = text.split(marker)[0]
    return text.strip()


def load_cache():
    cache = _load_cache()
    for rec in cache.values():
        rec["reply"] = _clean(rec["reply"])
    return cache


base.load_cache = load_cache


def setd_case_ids():
    b = json.load(open(os.path.join(ROOT, "results/partA/step46_own_scorer/set_B/set_B.json")))["cases"]
    c = json.load(open(os.path.join(ROOT, "results/partA/step47_audit_route/set_C/set_C.json")))["cases"]
    ids = sorted({k for k, v in b.items() if v.get("set") == "test"} | set(c))
    return ids, sum(v.get("set") == "test" for v in b.values()), len(c)


def build_plan():
    by = base.load_bench()
    ids, n_b, n_c = setd_case_ids()
    cases, items, skipped = {}, [], []
    for cid in ids:
        rows = by["test"].get(cid)
        if not rows:
            skipped.append(cid)
            continue
        organ, ref = rows[0]["organ"], rows[0]["reference"]
        gold = schema.extract_rule(ref, organ)
        errs = [r for r in rows if r["kind"] == "error"]
        if not errs:
            skipped.append(cid)
            continue
        rr = random.Random(zlib.crc32(f"{SEED}|{cid}".encode()))
        first = rr.choice(errs)
        other = [e for e in errs if e["field"] != first["field"]] or [e for e in errs if e is not first]
        second = rr.choice(other) if other else None
        true_style = base.STYLES[zlib.crc32(f"{SEED}|{cid}|true".encode()) % 3]
        common = dict(split="test", set="test", organ=organ, dataset=rows[0]["dataset"],
                      group=f"{rows[0]['dataset']}:{rows[0]['group_id']}", reference=ref, gold=gold)
        for suffix, e in (("", first), ("#b", second)):
            if e is None:
                continue
            k = cid + suffix
            tw_style = base.STYLES[zlib.crc32(f"{SEED}|{k}|tw".encode()) % 3]
            cases[k] = dict(common, case_id=k, source_case=cid, twin_field=e["field"], twin_category=e["category"],
                            twin_severity=e["severity"], twin_candidate_templated=e["candidate"],
                            twin=schema.extract_rule(e["candidate"], organ), twin_style=tw_style,
                            true_style=true_style if suffix == "" else None)
    # amendment 1 item 8: off-schema pairs on ~400 cases (133-134 per organ), excluding the Set C-F development cases
    cf_ids = set(devfab.cf_case_ids()[0])
    by_organ = collections.defaultdict(list)
    for k, c in cases.items():
        if not k.endswith("#b") and c["source_case"] not in cf_ids:
            by_organ[c["organ"]].append(k)
    n_fab = {"breast": 134, "thyroid": 133, "fetal": 133}
    for organ, ks in by_organ.items():
        ks = sorted(ks, key=lambda k: hashlib.sha256(f"{SEED}|{k}|fab".encode()).hexdigest())[:n_fab[organ]]
        for k in ks:
            c = cases[k]
            pair = fab.pick_pair(SEED, k, organ)
            st_f = base.STYLES[zlib.crc32(f"{SEED}|{k}|f".encode()) % 3]
            st_n = base.STYLES[zlib.crc32(f"{SEED}|{k}|n".encode()) % 3]
            common = {x: c[x] for x in ("split", "set", "organ", "dataset", "group", "reference", "gold", "source_case")}
            cases[k + "#f"] = dict(common, case_id=k + "#f", variant="fabrication", twin_field="_extra:" + pair["key"],
                                   twin_category="fabricated finding", twin_severity=2, twin_candidate_templated=None,
                                   twin=dict(c["gold"], _extra=fab.extra(pair, "fab")), twin_style=st_f, true_style=None)
            cases[k + "#n"] = dict(common, case_id=k + "#n", variant="normal_addition", twin_field=None, twin_category=None,
                                   twin_severity=None, twin_candidate_templated=None, twin=None, twin_style=st_f,
                                   true_style=st_n, true_facts=dict(c["gold"], _extra=fab.extra(pair, "norm")))
    for k, c in cases.items():
        if c.get("variant") == "fabrication":
            items.append(dict(id=f"{k}|twin|{c['twin_style']}", case_id=k, set="test", kind="twin", style=c["twin_style"], facts=c["twin"]))
            continue
        if c.get("variant") == "normal_addition":
            items.append(dict(id=f"{k}|true|{c['true_style']}", case_id=k, set="test", kind="true", style=c["true_style"], facts=c["true_facts"]))
            continue
        if c["true_style"]:
            items.append(dict(id=f"{k}|true|{c['true_style']}", case_id=k, set="test", kind="true", style=c["true_style"], facts=c["gold"]))
        items.append(dict(id=f"{k}|twin|{c['twin_style']}", case_id=k, set="test", kind="twin", style=c["twin_style"], facts=c["twin"]))
    for it in items:
        it["organ"] = cases[it["case_id"]]["organ"]
        it["messages"] = base.messages(it["organ"], it["facts"], it["style"])
    return cases, items, dict(set_b_test_cases=n_b, set_c_cases=n_c, union=len(ids), skipped=len(skipped))


def model_info():
    root = os.path.expanduser("~/.cache/huggingface/hub/models--" + MODEL.replace("/", "--"))
    ref = os.path.join(root, "refs", "main")
    if not os.path.exists(ref):
        from huggingface_hub import snapshot_download
        snapshot_download(MODEL)
    rev = open(ref).read().strip()
    snap = os.path.join(root, "snapshots", rev)
    hashes = {}
    for dirpath, _, names in os.walk(snap):
        for n in names:
            if n.endswith((".safetensors", ".bin", ".gguf")):
                h = hashlib.sha256()
                with open(os.path.join(dirpath, n), "rb") as f:
                    for blk in iter(lambda: f.read(1 << 20), b""):
                        h.update(blk)
                hashes[n] = h.hexdigest()
    return rev, snap, hashes


def plan(args):
    frozen = os.path.join(os.path.dirname(OUT), "frozen_s2.json")
    if not os.path.exists(frozen):
        raise RuntimeError("Freeze S2 (step48 freeze) and commit it before planning Set D.")
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(P("plan.json")):
        print("Set D plan already saved; reusing it.", flush=True)
        return
    cases, items, src = build_plan()
    rev, snap, hashes = model_info()
    json.dump(cases, open(P("cases.json"), "w"), indent=0)
    json.dump(dict(items=items, system=base.SYS, styles=base.STYLE_TXT, model=MODEL, temperature=base.TEMP,
                   seed=SEED, max_tokens=base.MAX_TOK), open(P("plan.json"), "w"))
    info = dict(step=48, set="D", writer_model=MODEL, writer_revision=rev, writer_snapshot=snap,
                writer_weight_sha256=hashes, seed=SEED, temperature=base.TEMP, max_tokens=base.MAX_TOK,
                frozen_s2_sha256=json.load(open(frozen))["sha256"], sources=src, planned_cases=len(cases),
                planned_by_organ=dict(collections.Counter(c["organ"] for c in cases.values())),
                planned_items=dict(collections.Counter(i["kind"] for i in items)), test_core_complete=False)
    json.dump(info, open(P("run_info.json"), "w"), indent=1)
    print(json.dumps({k: info[k] for k in ("sources", "planned_cases", "planned_by_organ", "planned_items")}), flush=True)


def gold(args):
    s47f.gold(args)
    json.dump(json.load(open(P("set_C.json"))), open(P("set_D.json"), "w"), ensure_ascii=False)
    sd = json.load(open(P("set_D.json")))
    major = sum(1 for c in sd["cases"].values() if c["twin_report"] and c["twin_severity"] in (2, 3))
    groups = {o: len({c["group"] for c in sd["cases"].values() if c["organ"] == o and (c["twin_report"] or c["true_reports"])}) for o in base.ORGANS}
    print("ELIGIBILITY major/critical errors kept:", major, "(need >= 400); groups by organ:", groups, flush=True)


def pilot(args):
    plan_items = {i["id"]: i for i in json.load(open(P("plan.json")))["items"]}
    cache = base.load_cache()
    kept = 0
    for k, r in cache.items():
        it = plan_items.get(k)
        if it is None:
            continue
        ok, _ = base.gold_check(it["organ"], it["facts"], r["reply"])
        kept += ok and not base.extras(it["organ"], it["facts"], r["reply"])
    print("PILOT", WRITER, "generated", len(cache), "kept", kept, "rate", round(kept / max(len(cache), 1), 2), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("plan", "generate", "gold", "extract", "pilot"))
    ap.add_argument("--max-hours", type=float, default=6.0)
    ap.add_argument("--only", default=None)
    ap.add_argument("--refresh-lod", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    {"plan": plan, "generate": s47f.generate, "gold": gold, "extract": s47f.extract, "pilot": pilot}[a.command](a)


if __name__ == "__main__":
    main()
