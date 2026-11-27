"""Set C-F (Step 48 development, amendment 1 item 8): off-schema errors on 150 Set C cases (50 per organ),
written by the Set C writer (Mistral-7B-Instruct-v0.3-4bit, seed 4801), so Stage 1 can measure whether a
variant catches errors the rules cannot see. Per case: '<id>#f' = fabricated major finding (twin, severity 2);
'<id>#n' = the paired normal statement (harmless). These cases are excluded from Set D's off-schema items.

Commands: plan -> generate -> gold -> extract -> calls --judge gemma|llama
"""
import argparse, collections, hashlib, json, os, time, zlib

from . import step45_freetext as base
from . import step47_freetext as s47f
from . import step48_fab as fab

ROOT = s47f.ROOT
OUT = os.path.join(ROOT, "results", "partA", "step48_confirm", "set_CF")
P = lambda name: os.path.join(OUT, name)
SEED = 4801
N_PER_ORGAN = 50
SETC = os.path.join(ROOT, "results/partA/step47_audit_route/set_C")


def _patch():
    base.OUT, base.P, base.SEED = OUT, P, SEED
    s47f.OUT, s47f.P, s47f.SEED = OUT, P, SEED


def cf_case_ids():
    src = json.load(open(os.path.join(SETC, "set_C.json")))["cases"]
    by = collections.defaultdict(list)
    for cid, c in src.items():
        if c["true_reports"]:
            by[c["organ"]].append(cid)
    out = []
    for organ in base.ORGANS:
        ids = sorted(by[organ], key=lambda k: hashlib.sha256(f"{SEED}|{k}".encode()).hexdigest())
        out += ids[:N_PER_ORGAN]
    return out, src


def build_plan():
    ids, src = cf_case_ids()
    cases, items = {}, []
    for cid in ids:
        c = src[cid]
        pair = fab.pick_pair(SEED, cid, c["organ"])
        common = {k: c[k] for k in ("organ", "dataset", "group", "reference", "gold")}
        style_f = base.STYLES[zlib.crc32(f"{SEED}|{cid}|f".encode()) % 3]
        style_n = base.STYLES[zlib.crc32(f"{SEED}|{cid}|n".encode()) % 3]
        facts_f = dict(c["gold"], _extra=fab.extra(pair, "fab"))
        facts_n = dict(c["gold"], _extra=fab.extra(pair, "norm"))
        cases[cid + "#f"] = dict(common, case_id=cid + "#f", source_case=cid, split="test", set="test", variant="fabrication",
                                 twin_field="_extra:" + pair["key"], twin_category="fabricated finding", twin_severity=2,
                                 twin_candidate_templated=None, twin=facts_f, twin_style=style_f)
        cases[cid + "#n"] = dict(common, case_id=cid + "#n", source_case=cid, split="test", set="test", variant="normal_addition",
                                 twin_field=None, twin_category=None, twin_severity=None, twin_candidate_templated=None,
                                 twin=None, twin_style=style_f, true_style=style_n, extra_norm=fab.extra(pair, "norm"))
        items.append(dict(id=f"{cid}#f|twin|{style_f}", case_id=cid + "#f", set="test", kind="twin", style=style_f, facts=facts_f))
        items.append(dict(id=f"{cid}#n|true|{style_n}", case_id=cid + "#n", set="test", kind="true", style=style_n, facts=facts_n))
    for it in items:
        it["organ"] = cases[it["case_id"]]["organ"]
        it["messages"] = base.messages(it["organ"], it["facts"], it["style"])
    return cases, items


def plan(args):
    _patch()
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(P("plan.json")):
        print("Set C-F plan exists; reusing.", flush=True)
        return
    cases, items = build_plan()
    json.dump(cases, open(P("cases.json"), "w"), indent=0)
    json.dump(dict(items=items, system=base.SYS, styles=base.STYLE_TXT, model=s47f.MODEL, temperature=base.TEMP,
                   seed=SEED, max_tokens=base.MAX_TOK), open(P("plan.json"), "w"))
    json.dump([], open(P("lod_plan.json"), "w"))  # no limit-of-detection items in Set C-F
    setc_info = json.load(open(os.path.join(SETC, "run_info.json")))
    info = dict(step=48, set="C-F", writer_model=s47f.MODEL, writer_revision=setc_info["writer_revision"],
                writer_snapshot=setc_info["writer_snapshot"], seed=SEED, planned_cases=len(cases),
                planned_items=dict(collections.Counter(i["kind"] for i in items)),
                by_organ=dict(collections.Counter(c["organ"] for c in cases.values())), test_core_complete=False)
    json.dump(info, open(P("run_info.json"), "w"), indent=1)
    print(json.dumps(info["planned_items"]), info["by_organ"], flush=True)


def generate(args):
    _patch()
    s47f.generate(args)


def gold(args):
    _patch()
    s47f.gold(args)


def extract(args):
    _patch()
    s47f.extract(args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("plan", "generate", "gold", "extract"))
    ap.add_argument("--max-hours", type=float, default=4.0)
    ap.add_argument("--only", default=None)
    ap.add_argument("--refresh-lod", action="store_true")
    a = ap.parse_args()
    {"plan": plan, "generate": generate, "gold": gold, "extract": extract}[a.command](a)


if __name__ == "__main__":
    main()
