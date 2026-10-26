"""Extractor v2 evaluation on dev/val free-text Qwen reports. Still a PROXY: agreement with independent regex readings (side, BI-RADS, size, lesion phrases), not hand labels.
    python3 -m usmeta.extractor_v2_eval run     (extracts 40 NEW dev/val reports with v2; the first 40 are re-read from the cache)
    python3 -m usmeta.extractor_v2_eval report"""
import json, sys, random, collections, os
from . import qwen_real as Q, schema, schema_v2, graders

def new_keys(n=10, seed=1):
    old = set(json.load(open(f'{Q.OUTD}/check_keys.json'))); rows = [r for r in Q.cases() if r['split'] in ('dev', 'val') and not r['flipped'] and r['key'] not in old]
    by = collections.defaultdict(list)
    for r in rows: by[r['dataset']].append(r)
    rng = random.Random(seed); return [x['key'] for ds in sorted(by) for x in rng.sample(by[ds], n)]

def extract(keys, out, version):
    cases = {c['key']: c for c in Q.cases()}; cli = graders.LocalLLM('mlx-community/gemma-2-9b-it-4bit', max_tokens=800)
    done = {json.loads(l)['key'] for l in open(out)} if os.path.exists(out) else set()
    for k in keys:
        if k in done: continue
        r = cases[k]
        if version == 'v2': f, bad, opts, over = schema_v2.extract_llm_v2(cli, r['report'], r['organ'])
        else: f, bad = schema.extract_llm(cli, r['report'], r['organ']); opts = over = 0
        open(out, 'a').write(json.dumps(dict(key=k, facts=f, unquoted=bad, options_dropped=opts, numeric_overrides=over)) + '\n')

def proxy(keys, path):
    cases = {c['key']: c for c in Q.cases()}; E = {json.loads(l)['key']: json.loads(l) for l in open(path)}; hit = collections.Counter(); tot = collections.Counter(); opt = 0; ov = 0; bad = []
    for k in keys:
        e = E[k]; r = cases[k]; f = e['facts'] or {}; rx = Q.regex_reading(r['report']); fields = set(schema.LLM_FIELDS[r['organ']]); opt += e.get('options_dropped', 0); ov += e.get('numeric_overrides', 0)
        # invalid values: any option list left in a value
        for a, b in f.items():
            if isinstance(b, str) and '|' in b: tot['invalid_option_value'] += 1; bad.append((k, a, b))
        for fld, v in rx.items():
            if fld not in fields and not (fld == 'size_mm' and 'hc_mm' in fields): continue
            g = f.get(fld) if fld != 'size_mm' else (f.get('size_mm') if f.get('size_mm') is not None else f.get('hc_mm'))
            ok = (abs(g - v) <= 0.15 * v) if (fld == 'size_mm' and g is not None) else str(g).lower() == str(v).lower()
            tot[fld] += 1; hit[fld] += ok
    n = sum(tot[k] for k in ('side', 'birads', 'size_mm', 'lesion')); h = sum(hit[k] for k in ('side', 'birads', 'size_mm', 'lesion'))
    return dict(reports=len(keys), agree=h, comparisons=n, rate=h / n if n else None, per_field={k: (hit[k], tot[k]) for k in ('side', 'birads', 'size_mm', 'lesion')}, options_dropped=opt, numeric_overrides=ov, invalid_option_values_left=tot['invalid_option_value'], examples=bad[:3])

if __name__ == '__main__':
    old = json.load(open(f'{Q.OUTD}/check_keys.json')); new = new_keys()
    if sys.argv[1] == 'run':
        extract(old, f'{Q.OUTD}/extract_check_v2.jsonl', 'v2'); extract(new, f'{Q.OUTD}/extract_new40_v2.jsonl', 'v2')
    else:
        res = dict(old40_v1=proxy(old, f'{Q.OUTD}/extract_check.jsonl'), old40_v2=proxy(old, f'{Q.OUTD}/extract_check_v2.jsonl'), new40_v2=proxy(new, f'{Q.OUTD}/extract_new40_v2.jsonl'))
        json.dump(res, open(f'{Q.OUTD}/extractor_v2_eval.json', 'w'), indent=1); print(json.dumps(res, indent=1))
