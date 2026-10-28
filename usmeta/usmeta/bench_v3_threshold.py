"""Step 18: bench_v3_threshold, matched threshold-crossing size errors. NEW file; bench_v2d and the frozen builders are not touched.
MAIN experiment = DDTI cases with a REAL TI-RADS level (TR3-TR5), nodule size in mm is SYNTHETIC (DDTI has no size in mm):
every row is labelled 'synthetic size, real TI-RADS level'. No TI-RADS level is invented; DDTI 4a/4b/4c are mapped to ACR TR4 ('to confirm').
Thresholds (ACR TI-RADS 2017, 'to confirm against Tessler 2017'; apply to the nodule's maximum dimension; 'crosses' = (size >= t) changes):
  TR3: follow-up 15, FNA 25   TR4: follow-up 10, FNA 15   TR5: follow-up 5, FNA 10   (TR1/TR2: none; dropped)
Per case (sizes drawn from a RNG seeded by crc32(case_id), independent of any score):
  role 'pair'    (70%): size = cutoff +- margin, margin in {1,2,3,5} mm, cutoff and side random, size >= 4 mm
  role 'control' (30%): size >= 6 mm from every cutoff of its level (no +-5 mm change crosses a cutoff), 4..40 mm
Candidates per case: identical; size errors +-1,2,3,5 mm and +-5,10,20,30,50 % (each tagged crossing yes/no, thresholds crossed, distance to the
nearest cutoff, digit counts, token / character edit fractions); matched one-word synonyms (harmless_type 'matched', the Step 5 rerun2 group).
    python3 -m usmeta.bench_v3_threshold build  -> bench_v3_threshold.jsonl"""
import json, os, re, sys, zlib, random, collections
from . import templates_v2 as T, splits

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'bench_v3_threshold.jsonl')
LEVEL = {'3': 'TR3', '4a': 'TR4', '4b': 'TR4', '4c': 'TR4', '5': 'TR5'}
THR = {'TR3': (15, 25), 'TR4': (10, 15), 'TR5': (5, 10)}
MM = (1, 2, 3, 5); PCT = (5, 10, 20, 30, 50); MARGINS = (1, 2, 3, 5); MIN_SIZE = 4
LABEL = 'synthetic size, real TI-RADS level'
SEV_NOTE = 'provisional, guideline-derived: crossing a TI-RADS cutoff = 3, otherwise 1; not clinician-confirmed'

def crossed(s, s2, thr): return [t for t in thr if (s >= t) != (s2 >= t)]
def dist_to_cutoff(s, thr): return min(abs(s - t) for t in thr)
def digits(n): return len(str(int(n)))

REPS = 4      # independent synthetic sizes per real case (replicas); groups (patients) are resampled together in every analysis

def synth_size(case_id, level, rep=0):
    rng = random.Random(zlib.crc32((f'step18|{case_id}|{rep}').encode())); thr = THR[level]
    role = 'pair' if rng.random() < 0.7 else 'control'
    if role == 'pair':
        while True:
            t, side, m = rng.choice(thr), rng.choice((-1, 1)), rng.choice(MARGINS); s = t + side * m
            if s >= MIN_SIZE: return role, s, t
    ok = [s for s in range(MIN_SIZE, 41) if dist_to_cutoff(s, thr) >= 6]
    return role, rng.choice(ok), None

def tok(t): return re.findall(r'\S+', t)
def edit_dist(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1): prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return d[-1]

ONE = [('nodule', 'lesion'), ('Assessment:', 'Impression:'), ('is seen', 'is demonstrated')]

def errors_for(s):
    out = []
    for d in MM:
        for sign in (1, -1): out.append(('mm', d, sign, s + sign * d))
    for p in PCT:
        for sign in (1, -1): out.append(('pct', p, sign, int(s * (1 + sign * p / 100) + 0.5)))
    seen, res = set(), []
    for ty, nom, sign, new in out:
        if new < 1 or new == s: continue
        res.append((ty, nom, sign, new))
    return res

def build():
    ids = {}
    for sp in ('dev', 'val'): ids.update({r['case_id']: (r['group_id'], sp, r['group_source']) for r in splits.load(sp)})
    ids.update({r['case_id']: (r['group_id'], 'test', r['group_source']) for r in splits.load('test', script='usmeta.bench_v3_threshold')})
    rows, counts = [], collections.Counter()
    for rec in T.load('DDTI'):
        tr = str(rec['labels'].get('tirads')).lower() if rec['labels'].get('tirads') is not None else None
        if tr not in LEVEL: continue
        level = LEVEL[tr]; thr = THR[level]; cid = rec['case_id']; gid, split, gsrc = ids[cid]
        for rep in range(REPS):
            role, s, anchor = synth_size(cid, level, rep)
            f = T.facts(rec); f.pop('size_pct', None); f['size_mm'] = (s, 'measured')
            ref = T.render(f, 'thyroid', 'standard'); counts[(split, level, role)] += 1
            base = dict(case_id=cid, rep=rep, unit=f'{cid}~r{rep}', dataset='DDTI', organ='thyroid', group_id=gid, group_source=gsrc, split=split, reference=ref, level=level, tirads_label=tr,
                        role=role, size_mm=s, anchor_cutoff=anchor, dist_to_cutoff=dist_to_cutoff(s, thr), data_label=LABEL, size_source='synthetic', level_source='real (DDTI label)')
            n = 0
            def emit(**kw):
                nonlocal n; rows.append(dict(base, id=f'{cid}~r{rep}#{n}', **kw)); n += 1
            emit(kind='identical', category=None, field=None, group='identical', primary=True, magnitude=None, severity=0, candidate=ref, harmless_type=None)
            for ty, nom, sign, new in errors_for(s):
                g = dict(f); g['size_mm'] = (new, 'measured'); txt = T.render(g, 'thyroid', 'standard')
                cr = crossed(s, new, thr); rt, ct = tok(ref), tok(txt)
                emit(kind='error', category='wrong measurement', field='size_mm', group='error', primary=True, magnitude=new / s, severity=3 if cr else 1, severity_note=SEV_NOTE,
                     old=s, new=new, delta_type=ty, nominal=nom, direction='up' if sign > 0 else 'down', delta_mm=new - s, rel_change=(new - s) / s,
                     crossing=bool(cr), crossed=cr, digits_ref=digits(s), digits_new=digits(new), token_edit_frac=edit_dist(rt, ct) / len(rt),
                     char_edit_frac=edit_dist(ref, txt) / len(ref), candidate=txt, harmless_type=None)
            for a, b in ONE:
                if a in ref:
                    emit(kind='harmless', category=None, field=None, group='synonym1', primary=False, magnitude=None, severity=0, candidate=ref.replace(a, b, 1), harmless_type='matched')
    return rows, counts

if __name__ == '__main__':
    if sys.argv[1] == 'build':
        rows, counts = build(); open(OUT, 'w').write(''.join(json.dumps(r) + '\n' for r in rows))
        print(len(rows), 'rows'); c = collections.Counter((r['split'], r['level'], r['role']) for r in rows if r['kind'] == 'identical')
        for k in sorted(c): print(k, c[k])
