"""Step 6: Layer 1 structured fact check on bench_v2d (rule-based extractor for templated wording).
    python3 -m usmeta.layer1 score --bench bench_v2d.jsonl --out scores_v2d_layer1.json
Scorers: finding_f1 / finding_precision / finding_recall (schema.py) and the OLD fact_checker / fact_f1 (extract.py, written for v1 wording,
kept for comparison: on v2 text its extractor mostly finds nothing)."""
import json, sys, argparse, collections
from . import layer0, schema, graders
NAMES = ['finding_f1', 'finding_precision', 'finding_recall', 'legacy_fact_checker', 'legacy_fact_f1']

def score(bench, out):
    rows = [json.loads(l) for l in open(bench)]; P = layer0.pairs_of(rows); org = {}
    for r in rows: org[r['reference']] = r['organ']
    old = {'legacy_fact_checker': graders.FactChecker(), 'legacy_fact_f1': graders.FactF1()}
    S = {'pairs': [list(p) for p in P], 'scores': {n: [] for n in NAMES}}
    cache = {}
    for ref, hyp in P:
        o = org[ref]
        if ref not in cache: cache[ref] = schema.to_findings(schema.extract_rule(ref, o), o)
        p, r, f1, _ = schema.finding_scores(cache[ref], schema.to_findings(schema.extract_rule(hyp, o), o))
        S['scores']['finding_precision'].append(p); S['scores']['finding_recall'].append(r); S['scores']['finding_f1'].append(f1)
        for n, g in old.items():
            try: S['scores'][n].append(float(g.score(ref, hyp, {'organ': o})))
            except Exception: S['scores'][n].append(0.0)
    json.dump(S, open(out, 'w')); print('scored', len(P), 'pairs')

def attribute_tables(rows):
    """(a) wiring: mean credit per attribute on identical + harmless candidates (should be 1.00); (b) detection: share of planted errors whose
    changed field gets credit < 1 for the field's own attribute"""
    ok, tot = collections.defaultdict(float), collections.Counter(); det, dn = collections.defaultdict(float), collections.Counter()
    ent = schema.FIELD_ENTITY
    for r in rows:
        o = r['organ']; ref = schema.to_findings(schema.extract_rule(r['reference'], o), o); hyp = schema.to_findings(schema.extract_rule(r['candidate'], o), o)
        _, _, _, cr = schema.finding_scores(ref, hyp)
        if r['kind'] in ('identical', 'harmless'):
            for (e, a), c in cr.items(): ok[(r['dataset'], f'{e}.{a}')] += c; tot[(r['dataset'], f'{e}.{a}')] += 1
        else:
            f = r['field']; key = (ent.get(f, f), 'status' if f == 'lesion' else f)
            if f in ('calc', 'halo', 'foci'): key = (ent[f], 'status')
            if key in cr or f == 'count': key = key if key in cr else ('lesion', 'count')
            if key in cr: det[(r['dataset'], f)] += (cr[key] < 1); dn[(r['dataset'], f)] += 1
    return ok, tot, det, dn

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--bench', default='bench_v2d.jsonl'); ap.add_argument('--out', default='scores_v2d_layer1.json'); a = ap.parse_args()
    if a.cmd == 'score': score(a.bench, a.out)
