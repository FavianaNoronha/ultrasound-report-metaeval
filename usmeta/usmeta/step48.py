"""Step 48 machine steps on Set C (development data now).

retry-raw : re-ask every Gemma audit call on Set C that returned no readable reply,
            saving the raw text (Step 47 discarded it), for the parser fix (candidate P).
llama-setc: run the Llama audit prompts on all Set C core reports that need an audit
            (Step 47 ran Llama on a 300-report subset only), for candidate L.
"""
import json, os, re, time

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


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("retry-raw", "llama-setc"))
    p.add_argument("--max-hours", type=float, default=8.0)
    a = p.parse_args()
    {"retry-raw": retry_raw, "llama-setc": llama_setc}[a.command](a)


if __name__ == "__main__":
    main()
