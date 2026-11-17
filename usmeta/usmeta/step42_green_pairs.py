"""Step 42: choose and export the pairs for GREEN (4-bit) on a Colab T4. NEW file. Templated text only (Step 33 factorial blocks and Step 35 limit-of-detection candidates, both saved earlier; no HiSBreast text, no new test-split read).
Design (fixed in results/partA/step42_green/PREREG.md before any GREEN score): an ORDERED list of units, seed 0, stratified round-robin, so that any prefix is balanced:
  F units (factorial): a case of one of the 7 breast / thyroid datasets (20 per dataset) with 2 'a' rewordings (small / matched), the 2 large rewordings 'b' (terse, long), 3 planted errors 'c', and the 3 x 2 'd' texts (the same errors in the large styles) = 13 pairs.
  L units (limit of detection): a case of one of the 4 Step 35 cells (breast size_mm, breast size_pct, thyroid size_pct, fetal-head HC; 40 per cell) with up to 2 matched synonyms and ALL its Step 35 error candidates (both directions, every level) = up to 16 pairs.
  Order: F and L units alternate; inside F the 7 datasets round-robin, inside L the 4 cells round-robin; inside a stratum a seeded shuffle.
Outputs (local_data/step42, git-ignored): green_pairs.jsonl (id, reference, candidate: the ONLY file uploaded for the test pairs), dev_timing_pairs.jsonl (20 dev pairs, same format), pair_key.json (id -> role / unit / case, stays local).
    python3 -m usmeta.step42_green_pairs"""
import os, json, random, collections
from . import step33_factorial as F, step35_lod as L, splits

ROOT = F.ROOT; LOCAL = os.path.join(ROOT, 'local_data', 'step42'); F_PER_DS = 20; L_PER_CELL = 40; SEED = 0
FDS = ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM', 'TN3K', 'TN5000', 'DDTI']; CELLS = [('breast', 'size_mm'), ('breast', 'size_pct'), ('thyroid', 'size_pct'), ('fetal head', 'hc_mm')]

def f_units(rng):
    blocks = json.load(open(os.path.join(F.OUT, 'test_blocks.json')))['blocks']; cases = collections.defaultdict(list)
    for b in blocks: cases[b['case']].append(b)
    by_ds = collections.defaultdict(list)
    for cid in sorted(cases):
        bl = cases[cid]; styles = {b['style'] for b in bl}; a = bl[0]['a_texts']
        if len(a) < 2 or styles != {'terse', 'long'}: continue
        errs = collections.defaultdict(dict)
        for b in bl: errs[b['c_text']][b['style']] = b
        ok = sorted(c for c, d in errs.items() if set(d) == {'terse', 'long'})
        if len(ok) < 3: continue
        by_ds[bl[0]['dataset']].append((cid, bl, errs, ok))
    out = {}
    for ds in FDS:
        lst = by_ds[ds]; rng.shuffle(lst); units = []
        for cid, bl, errs, ok in lst[:F_PER_DS]:
            ch = rng.sample(ok, 3); ref = bl[0]['ref']; pairs = []
            for k, t in enumerate(bl[0]['a_texts'][:2]): pairs.append(('a', k, t))
            for st in ('terse', 'long'): pairs.append(('b', st, next(b['b_text'] for b in bl if b['style'] == st)))
            for k, c in enumerate(ch):
                pairs.append(('c', k, c))
                for st in ('terse', 'long'): pairs.append(('d', f'{k}|{st}', errs[c][st]['d_text']))
            units.append(dict(type='F', case=cid, dataset=ds, organ=bl[0]['organ'], group=bl[0]['group'], ref=ref, pairs=pairs, fields=[errs[c]['terse']['field'] for c in ch]))
        out[ds] = units
    return out

def l_units(rng):
    rows = L.all_rows(); by = collections.defaultdict(list)
    for r in rows: by[r['case_id']].append(r)
    cells = {c: [] for c in CELLS}
    for cid in sorted(by):
        rs = by[cid]; m = [r for r in rs if r['kind'] == 'matched']; e = [r for r in rs if r['kind'] == 'error']
        if not m or not e: continue
        cell = (rs[0]['organ'], e[0]['field'])
        if cell in cells: cells[cell].append((cid, rs[0], m, e))
    out = {}
    for cell in CELLS:
        lst = cells[cell]; rng.shuffle(lst); units = []
        for cid, r0, m, e in lst[:L_PER_CELL]:
            pairs = [('m', k, x['candidate']) for k, x in enumerate(m[:2])] + [('e', f"{x['level']}|{x.get('factor') if x.get('factor') is not None else x.get('shift_mm')}", x['candidate']) for x in e]
            units.append(dict(type='L', case=cid, dataset=r0['dataset'], organ=r0['organ'], group=f"{r0['dataset']}:{r0['group_id']}", ref=r0['reference'], pairs=pairs, cell=f'{cell[0]}|{cell[1]}'))
        out[cell] = units
    return out

def roundrobin(strata):
    keys = list(strata); out = []; i = 0
    while any(i < len(strata[k]) for k in keys):
        for k in keys:
            if i < len(strata[k]): out.append(strata[k][i])
        i += 1
    return out

def main():
    os.makedirs(LOCAL, exist_ok=True); rng = random.Random(SEED); Fu = roundrobin(f_units(rng)); Lu = roundrobin(l_units(rng)); order = []
    for i in range(max(len(Fu), len(Lu))):
        if i < len(Fu): order.append(Fu[i])
        if i < len(Lu): order.append(Lu[i])
    key = {}; lines = []
    for u, unit in enumerate(order, 1):
        uid = f'u{u:04d}'
        for p, (role, k, text) in enumerate(unit['pairs'], 1):
            pid = f'{uid}_p{p:02d}'; lines.append(dict(id=pid, reference=unit['ref'], candidate=text)); key[pid] = dict(unit=uid, type=unit['type'], role=role, k=str(k), case=unit['case'], dataset=unit['dataset'], organ=unit['organ'], group=unit['group'], cell=unit.get('cell'))
    open(os.path.join(LOCAL, 'green_pairs.jsonl'), 'w').write(''.join(json.dumps(l) + '\n' for l in lines)); json.dump(key, open(os.path.join(LOCAL, 'pair_key.json'), 'w'))
    # dev timing pairs: 20 templated breast / thyroid pairs from the dev split (identical, planted error, harmless), seed 0
    dev = {r['case_id'] for r in splits.load('dev')}; rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_v2d.jsonl'))]; pool = [r for r in rows if r['case_id'] in dev and r['organ'] in ('breast', 'thyroid') and r['kind'] in ('identical', 'error', 'harmless')]
    rng2 = random.Random(1); pick = rng2.sample(pool, 20); open(os.path.join(LOCAL, 'dev_timing_pairs.jsonl'), 'w').write(''.join(json.dumps(dict(id=f'dev{i:02d}', reference=r['reference'], candidate=r['candidate'])) + '\n' for i, r in enumerate(pick)))
    ups = collections.Counter(k['unit'] for k in key.values())
    print(len(order), 'units;', len(lines), 'pairs; F', len(Fu), 'L', len(Lu), '; mean pairs per unit', round(len(lines) / len(order), 2), '; first 10 units:', [(o['type'], o['dataset'] if o['type'] == 'F' else o['cell']) for o in order[:10]])
    return order

if __name__ == '__main__': main()
