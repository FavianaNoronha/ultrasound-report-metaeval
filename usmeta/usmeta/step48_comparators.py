"""Step 48 comparators (amendment 1 item 3, DEVIATIONS.md 3): GREEN, CRIMSON and a VERT-style prompt,
run locally with MLX on the fixed 300-report Set D2 subset (same subset as the H4 Llama check).

  GREEN   : StanfordAIMI/GREEN-RadLlama2-7b, converted to MLX 4-bit; GREEN prompt and parser copied from
            github.com/Stanford-AIMI/GREEN (green_score/utils.py, green.py). Route if >= 1 clinically significant error.
  CRIMSON : rajpurkarlab/medgemma-4b-it-crimson, converted to MLX 4-bit; prompt, JSON repair and score from the
            vendored crimson-score 0.2.0 (third_party/crimson). No patient context. Route if any false or missing
            finding is urgent/actionable, or any attribute error is significant.
  VERT    : the GREEN prompt plus VERT's overall-accuracy-score line (Bologna et al. 2026, Appendix C), run on the
            S2 judge model (Gemma-2-9B-it 4-bit). Route if score < t, t fixed on a 300-report Set C subset as the
            largest cut-off with harmless routed <= 30% (VERT was not run on Set C during Stage 1; DEVIATIONS 3).

Commands: convert --model green|crimson ; run --model green|crimson|vert --which setd2|setc
"""
import argparse, hashlib, json, os, re, time

from . import step47_audit_route as s47
from . import step48 as s48
from .third_party.crimson.prompt_parts import build_prompt as crimson_prompt
from .third_party.crimson.utils import parse_json_response as crimson_parse
from .third_party.crimson.generate_score import CRIMSONScore

P = s48.P
MLX_DIR = os.path.expanduser("~/mlx_models")
MODELS = {
    "green": dict(hf="StanfordAIMI/GREEN-RadLlama2-7b", mlx=os.path.join(MLX_DIR, "GREEN-RadLlama2-7b-4bit"), max_tokens=1200),
    "crimson": dict(hf="rajpurkarlab/medgemma-4b-it-crimson", mlx=os.path.join(MLX_DIR, "medgemma-4b-it-crimson-4bit"), max_tokens=2048),
    "vert": dict(hf=s47.AUDIT_MODEL, mlx=None, max_tokens=1200),
}

# ---------------- GREEN prompt and parser (copied from Stanford-AIMI/GREEN) ----------------
GREEN_CATS = ["Clinically Significant Errors", "Clinically Insignificant Errors", "Matched Findings"]
GREEN_SUB = ["(a) False report of a finding in the candidate", "(b) Missing a finding present in the reference",
             "(c) Misidentification of a finding's anatomic location/position", "(d) Misassessment of the severity of a finding",
             "(e) Mentioning a comparison that isn't in the reference", "(f) Omitting a comparison detailing a change from a prior study"]


def green_prompt(text1, text2, max_len=300, vert=False):
    text1 = " ".join(text1.split()[:max_len])
    text2 = " ".join(text2.split()[:max_len])
    crit_extra = ("\n    The overall accuracy score to assign to the candidate report given the count of clinically significant and "
                  "clinically insignificant errors. The score must be a continuous number in [0.00, 1.00] with two decimals.") if vert else ""
    out_extra = ("\n\n    [Overall Accuracy Score]:\n    <Overall accuracy score between 0 and 1 given the total number of clinically "
                 "significant and insignificant errors in the candidate reports>") if vert else ""
    return (f"Objective: Evaluate the accuracy of a candidate radiology report in comparison to a reference radiology report composed by expert radiologists.\n\n    Process Overview: You will be presented with:\n\n    1. The criteria for making a judgment.\n    2. The reference radiology report.\n    3. The candidate radiology report.\n    4. The desired format for your assessment.\n\n    1. Criteria for Judgment:\n\n    For each candidate report, determine:\n\n    The count of clinically significant errors.\n    The count of clinically insignificant errors.{crit_extra}\n\n    Errors can fall into one of these categories:\n\n    a) False report of a finding in the candidate.\n    b) Missing a finding present in the reference.\n    c) Misidentification of a finding's anatomic location/position.\n    d) Misassessment of the severity of a finding.\n    e) Mentioning a comparison that isn't in the reference.\n    f) Omitting a comparison detailing a change from a prior study.\n    Note: Concentrate on the clinical findings rather than the report's writing style. Evaluate only the findings that appear in both reports.\n\n    2. Reference Report:\n    {text1}\n\n    3. Candidate Report:\n    {text2}\n\n    4. Reporting Your Assessment:\n\n    Follow this specific format for your output, even if no errors are found:\n    ```\n    [Explanation]:\n    <Explanation>\n\n    [Clinically Significant Errors]:\n    (a) <Error Type>: <The number of errors>. <Error 1>; <Error 2>; ...; <Error n>\n    ....\n    (f) <Error Type>: <The number of errors>. <Error 1>; <Error 2>; ...; <Error n>\n\n    [Clinically Insignificant Errors]:\n    (a) <Error Type>: <The number of errors>. <Error 1>; <Error 2>; ...; <Error n>\n    ....\n    (f) <Error Type>: <The number of errors>. <Error 1>; <Error 2>; ...; <Error n>\n\n    [Matched Findings]:\n    <The number of matched findings>. <Finding 1>; <Finding 2>; ...; <Finding n>{out_extra}\n    ```\n")


def green_clean(response):
    if "[Explanation]:" in response:
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1]
        response = response.split("[Explanation]:")[1] if "[Explanation]:" in response else response
    if "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1]
    return response.replace("</s>", "").replace("<unk>", "")


def green_counts(text, category):
    m = re.search(rf"\[{category}\]:\s*(.*?)(?:\n\s*\n|\Z)", text, re.DOTALL)
    sub = [0] * 6
    if not m or m.group(1).startswith("No"):
        return 0, sub, bool(m)
    if category == "Matched Findings":
        c = re.findall(r"^\b\d+\b(?=\.)", m.group(1))
        return (int(c[0]) if c else 0), sub, True
    subcats = [s.split(" ", 1)[0] + " " for s in GREEN_SUB]
    matches = sorted(re.findall(r"\([a-f]\) .*", m.group(1)))
    if not matches:
        matches = sorted(re.findall(r"\([1-6]\) .*", m.group(1)))
        subcats = [f"({i}) " for i in range(1, 7)]
    for pos, sc in enumerate(subcats):
        for mm in matches:
            if mm.startswith(sc):
                c = re.findall(r"(?<=: )\b\d+\b(?=\.)", mm)
                if c:
                    sub[pos] = int(c[0])
    return sum(sub), sub, True


def green_parse(raw):
    text = green_clean(raw or "")
    sig, sub, found = green_counts(text, GREEN_CATS[0])
    matched, _, mfound = green_counts(text, GREEN_CATS[2])
    score = 0.0 if matched == 0 else matched / (matched + sig)
    return {"green": score, "sig_errors": sig, "sig_by_type": sub, "matched": matched, "parsed": bool(found and mfound)}


def vert_parse(raw):
    m = re.search(r"\[Overall Accuracy Score\]:\s*\**\s*([01](?:\.\d+)?)", raw or "")
    g = green_parse(raw)
    return {"vert": float(m.group(1)) if m else None, "sig_errors": g["sig_errors"], "parsed": m is not None}


def crimson_score(raw):
    try:
        ev = crimson_parse(raw)
    except Exception:
        ev = None
    if not isinstance(ev, dict):
        return {"crimson": None, "parsed": False}
    try:
        res = CRIMSONScore._calculate_crimson(None, ev)
    except Exception as e:
        return {"crimson": None, "parsed": False, "error": str(e)[:200]}
    sig_w = {"urgent": 1.0, "actionable_not_urgent": 0.5}
    refs = {r.get("id"): r.get("clinical_significance") for r in ev.get("reference_findings", [])}
    preds = {p.get("id"): p.get("clinical_significance") for p in ev.get("predicted_findings", [])}
    errs = ev.get("errors", {})
    serious = (any(preds.get(i) in sig_w for i in errs.get("false_findings", []))
               or any(refs.get(i) in sig_w for i in errs.get("missing_findings", []))
               or any(e.get("severity") == "significant" for e in errs.get("attribute_errors", [])))
    return {"crimson": res["crimson_score"], "serious_error": bool(serious), "error_counts": res["error_counts"], "parsed": True}


# ---------------- running ----------------
def rows_for(which):
    if which == "setc":
        rows = [r for r in s47.set_c_candidates() if r["kind"] in ("error", "harmless")]
    else:
        rows = s48.rows_for(which)
    keep = s48.subset_300(rows)
    return [r for r in rows if r["id"] in keep]


def out_path(model, which):
    return P(f"comp_{model}_{which}.jsonl")


def convert(args):
    from mlx_lm import convert as mlx_convert
    m = MODELS[args.model]
    if os.path.exists(os.path.join(m["mlx"], "config.json")):
        print("already converted:", m["mlx"], flush=True)
        return
    os.makedirs(MLX_DIR, exist_ok=True)
    mlx_convert(hf_path=m["hf"], mlx_path=m["mlx"], quantize=True, q_bits=4, q_group_size=64)
    print("CONVERTED", args.model, "->", m["mlx"], flush=True)


def chat(tokenizer, model, prompt):
    if model == "green":
        try:
            return tokenizer.apply_chat_template([{"from": "human", "value": prompt}, {"from": "gpt", "value": ""}],
                                                 tokenize=False, add_generation_prompt=True)
        except Exception:
            pass
    msgs = [{"role": "user", "content": prompt}]
    if model == "crimson":
        msgs = [{"role": "system", "content": "You are an expert radiology evaluator that assesses the accuracy of radiology reports."}] + msgs
    try:
        return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    except Exception:  # template without a system role: fold it into the user turn
        return tokenizer.apply_chat_template([{"role": "user", "content": "\n\n".join(x["content"] for x in msgs)}],
                                             tokenize=False, add_generation_prompt=True)


def run(args):
    from mlx_lm import load, generate
    m = MODELS[args.model]
    path = m["mlx"] or m["hf"]
    rows = rows_for(args.which)
    out = out_path(args.model, args.which)
    done = {json.loads(l)["id"] for l in open(out)} if os.path.exists(out) else set()
    todo = [r for r in rows if r["id"] not in done]
    print(args.model, args.which, "rows", len(rows), "todo", len(todo), flush=True)
    model, tok = load(path)
    deadline = time.time() + args.max_hours * 3600
    with open(out, "a") as fh:
        for n, r in enumerate(todo, 1):
            if time.time() > deadline:
                print("time cap reached", n - 1, flush=True)
                return
            if args.model == "crimson":
                prompt = crimson_prompt(r["ref"], r["cand"], include_significance_examples=False,
                                        include_attribute_guidelines=False, include_context_guidelines=False)
            else:
                prompt = green_prompt(r["ref"], r["cand"], vert=(args.model == "vert"))
            t0 = time.time()
            raw = generate(model, tok, prompt=chat(tok, args.model, prompt), max_tokens=m["max_tokens"])
            parsed = {"green": green_parse, "vert": vert_parse, "crimson": crimson_score}[args.model](raw)
            fh.write(json.dumps({"id": r["id"], "raw": raw, "result": parsed, "seconds": round(time.time() - t0, 1)}, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 10 == 0:
                print(args.model, args.which, n, "of", len(todo), flush=True)
    print(args.model, args.which, "COMPLETE", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("convert", "run"))
    ap.add_argument("--model", choices=("green", "crimson", "vert"), required=True)
    ap.add_argument("--which", choices=("setd2", "setc"), default="setd2")
    ap.add_argument("--max-hours", type=float, default=6.0)
    a = ap.parse_args()
    {"convert": convert, "run": run}[a.command](a)


if __name__ == "__main__":
    main()
