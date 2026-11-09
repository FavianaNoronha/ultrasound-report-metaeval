"""Step 21e: matched edit-size comparison (SAVED scores only, no model calls). NEW file.
Question: when a planted error and a harmless rewording change the text by the same amount, do the scorers still prefer the rewording?
For each reference: every planted-error candidate and every harmless candidate (small, matched, large, other = secondary variants) of the TEST split.
Edit size = character Levenshtein distance to the reference / max(len(reference), len(candidate)). Bins 0-5, 5-10, 10-20, 20-40, 40+ %.
Within each reference and bin, all error x harmless pairs of that bin (per-case mean, then group bootstrap, 1,000 resamples, seed 0). pref_strict = error < harmless; tie share reported; AUROC = strict + 0.5 tie.
Judge scores exist only for a subset: judge rows use pairs in which both candidates were judged. Bins with fewer than 30 groups: 'too small to compare'.
    python3 -m usmeta.step21_edit_matched OUT_DIR"""
import json, sys, os, collections
import numpy as np
from . import splits, step19_pairs as p
from .step10d_analysis import gboot

BINS = [(0.0, 0.05, '0-5%'), (0.05, 0.10, '5-10%'), (0.10, 0.20, '10-20%'), (0.20, 0.40, '20-40%'), (0.40, 9.0, '40%+')]
HT = ('small', 'matched', 'large', 'other'); MIN_N = 30
SCORERS = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'finding_f1', 'sentence_f1', 'judge_score']
NAMES = {'bleu': 'BLEU', 'rougeL': 'ROUGE-L', 'chrf': 'chrF', 'bertscore[roberta-large]': 'BERTScore', 'ratescore': 'RaTEScore', 'finding_f1': 'finding_f1 (upper bound)', 'sentence_f1': 'judge sentence_f1', 'judge_score': 'judge_score'}
ORGANS = ('breast', 'thyroid', 'fetal head')

def lev(a, b):
    """exact Levenshtein distance, bit-parallel (Hyyrö / Myers); verified against a plain DP in tests"""
    m = len(a)
    if m == 0: return len(b)
    peq = collections.defaultdict(int)
    for i, ch in enumerate(a): peq[ch] |= 1 << i
    full = (1 << m) - 1; hb = 1 << (m - 1); Pv, Mv, score = full, 0, m
    for ch in b:
        Eq = peq.get(ch, 0); Xv = Eq | Mv; Xh = (((Eq & Pv) + Pv) ^ Pv) | Eq; Ph = Mv | (~(Xh | Pv) & full); Mh = Pv & Xh
        if Ph & hb: score += 1
        elif Mh & hb: score -= 1
        Ph = ((Ph << 1) | 1) & full; Mh = (Mh << 1) & full; Pv = Mh | (~(Xv | Ph) & full); Mv = Ph & Xv
    return score

def edit_size(ref, cand):
    d = max(len(ref), len(cand)); return lev(ref, cand) / d if d else 0.0

def load_test():
    rows = [json.loads(l) for l in open('bench_test_v2d.jsonl')]; ids = {r['case_id'] for r in splits.load('test', script='usmeta.step21_edit_matched')}
    assert all(r['case_id'] in ids for r in rows), 'bench rows outside the test split'
    sc = {**p.scores_of('scores_test_layer0.json'), 'finding_f1': p.scores_of('scores_test_layer1.json')['finding_f1']}; sc.update(p.judge_lookup(['judge_test_v2.jsonl', 'judge_big_v2.jsonl'])); return rows, sc

def build_cases(rows):
    C = {}; cache = {}
    for r in rows:
        if not (r['kind'] == 'error' or (r['kind'] == 'harmless' and r['harmless_type'] in HT)): continue
        k = (r['reference'], r['candidate'])
        if k not in cache: cache[k] = edit_size(*k)
        c = C.setdefault(r['case_id'], dict(ds=r['dataset'], organ=p.ORGAN[r['dataset']], group=f"{r['dataset']}:{r['group_id']}", E=[], H=[]))
        c['E' if r['kind'] == 'error' else 'H'].append((r, cache[k]))
    return C

def bin_of(x):
    for lo, hi, nm in BINS:
        if lo <= x < hi: return nm
    return BINS[-1][2]

def pair_stats(C, sc, name, organ=None, binname=None, harmless_sel=lambda r: True, err_sel=lambda r: True):
    """per case: strict / tie / half over error x harmless pairs in the bin (None = no bin, all pairs); returns dict"""
    s, t, h, g = [], [], [], []; npairs = 0
    for c in C.values():
        if organ and c['organ'] != organ: continue
        e = [p.score_of(sc, name, r) for r, x in c['E'] if (binname is None or bin_of(x) == binname) and err_sel(r)]; hh = [p.score_of(sc, name, r) for r, x in c['H'] if (binname is None or bin_of(x) == binname) and harmless_sel(r)]
        e = [v for v in e if v is not None]; hh = [v for v in hh if v is not None]
        if not e or not hh: continue
        E, H = np.array(e)[:, None], np.array(hh)[None, :]; lt, eq = float((E < H).mean()), float((E == H).mean()); s.append(lt); t.append(eq); h.append(lt + 0.5 * eq); g.append(c['group']); npairs += len(e) * len(hh)
    n_groups = len(set(g)); out = dict(n_cases=len(s), n_groups=n_groups, n_pairs=npairs)
    if len(s) and n_groups >= MIN_N: out.update(strict=gboot(s, g), tie=float(np.mean(t)), auroc=gboot(h, g))
    elif len(s): out.update(small=True, strict_pt=float(np.mean(s)), tie=float(np.mean(t)), auroc_pt=float(np.mean(h)))
    return out

def cell(d, key):
    if d is None or d['n_cases'] == 0: return '—'
    if d.get('small'): return f"too small to compare ({d['n_groups']} groups)"
    v = d[key]; return f'{v[0]:.2f} ({v[1]:.2f}–{v[2]:.2f})'

def main(out):
    os.makedirs(out, exist_ok=True); rows, sc = load_test(); C = build_cases(rows); res = {}; md = []
    # ---- edit-size distributions
    dist = collections.defaultdict(lambda: collections.Counter())
    for c in C.values():
        for r, x in c['E']: dist[(c['organ'], 'error')][bin_of(x)] += 1
        for r, x in c['H']: dist[(c['organ'], 'harmless')][bin_of(x)] += 1; dist[(c['organ'], 'harmless:' + r['harmless_type'])][bin_of(x)] += 1
    md += ['## Candidates per edit-size bin (test split)', '', '| organ | candidates | ' + ' | '.join(b[2] for b in BINS) + ' |', '|---|---|' + '---|' * len(BINS)]
    for organ in ORGANS:
        for kind in ('error', 'harmless', 'harmless:small', 'harmless:matched', 'harmless:large', 'harmless:other'):
            d = dist[(organ, kind)]; md.append(f"| {organ} | {kind.replace('harmless:', 'harmless, ')} | " + ' | '.join(str(d[b[2]]) for b in BINS) + ' |')
    res['distribution'] = {f'{o}|{k}': dict(v) for (o, k), v in dist.items()}
    md += ['', 'Large harmless rewordings and large errors are rare at the two ends, so some bins have no pairs or too few groups; no extra rewordings were generated.', '']
    # ---- pairs and groups per bin
    md += ['## Pairs and groups per bin (error x harmless pairs inside the same reference and bin)', '', '| organ | ' + ' | '.join(b[2] for b in BINS) + ' | all pairs (unmatched) |', '|---|' + '---|' * (len(BINS) + 1)]
    for organ in ORGANS:
        cells = []
        for b in [x[2] for x in BINS] + [None]:
            d = pair_stats(C, sc, 'bleu', organ, b); cells.append(f"{d['n_pairs']} pairs, {d['n_groups']} groups" + (' †' if d['n_groups'] < MIN_N else ''))
        md.append(f'| {organ} | ' + ' | '.join(cells) + ' |')
    md += ['', '† under 30 groups: too small to compare.', '']
    # ---- per scorer x organ x bin
    for key, title in (('strict', 'Paired preference accuracy (share of error x harmless pairs where the error scores LOWER; ties not counted as preferred)'), ('auroc', 'AUROC (= strict preference + 0.5 x tie share)')):
        md += [f'## {title}', '']
        for organ in ORGANS:
            md += [f'### {organ}', '', '| scorer | ' + ' | '.join(b[2] for b in BINS) + ' | all pairs (unmatched) |', '|---|' + '---|' * (len(BINS) + 1)]
            for name in SCORERS:
                cells = []
                for b in [x[2] for x in BINS] + [None]:
                    d = pair_stats(C, sc, name, organ, b); res[f'{organ}|{name}|{b or "all"}'] = {k: v for k, v in d.items()}; cells.append(cell(d, key))
                md.append(f'| {NAMES[name]} | ' + ' | '.join(cells) + ' |')
            md.append('')
    # ---- error-type composition per bin (the bins are confounded with error type)
    md += ['## Which error types fall in each edit-size bin (share of error candidates; test split)', '', '| organ | error category | ' + ' | '.join(b[2] for b in BINS) + ' |', '|---|---|' + '---|' * len(BINS)]
    for organ in ORGANS:
        cnt = collections.defaultdict(collections.Counter); tot = collections.Counter()
        for c in C.values():
            if c['organ'] != organ: continue
            for r, x in c['E']: cnt[r['category'] + (' (field lesion: no focal lesion)' if r['category'] == 'missed finding' and r['field'] == 'lesion' else '')][bin_of(x)] += 1; tot[bin_of(x)] += 1
        for cat in sorted(cnt): md.append(f'| {organ} | {cat} | ' + ' | '.join(f"{cnt[cat][b[2]] / tot[b[2]]:.0%}" if tot[b[2]] else '—' for b in BINS) + ' |')
    md += ['', 'Error edit size is set by the error type, so a bin comparison is also an error-type comparison: the 40%+ bin is almost entirely the "No focal lesion is seen." rewrite.', '']
    md += ['## Same tables without the whole-report "no focal lesion" errors (field = lesion, missed finding): strict preference', '']
    nl = lambda r: not (r['category'] == 'missed finding' and r['field'] == 'lesion')
    for organ in ORGANS:
        md += [f'### {organ} (excluding no-lesion errors)', '', '| scorer | ' + ' | '.join(b[2] for b in BINS) + ' | all pairs |', '|---|' + '---|' * (len(BINS) + 1)]
        for name in SCORERS[:6]:
            cells = []
            for b in [x[2] for x in BINS] + [None]:
                d = pair_stats(C, sc, name, organ, b, err_sel=nl); res[f'{organ}|{name}|{b or "all"}|no_lesion_errors'] = d; cells.append(cell(d, 'strict'))
            md.append(f'| {NAMES[name]} | ' + ' | '.join(cells) + ' |')
        md.append('')
    # ---- human rewordings (Step 21d, scored): paired with the SAME reference's errors that fall in the same edit-size bin
    hd = 'results/partA/step21d_human_sheet'; hb = [json.loads(l) for l in open(os.path.join(hd, 'human_bench.jsonl'))]; hb = [b for b in hb if b['kind'] == 'human']
    HS = {}
    for f, names in (('scores_layer0.json', None), ('scores_layer1.json', ('finding_f1',))):
        S = json.load(open(os.path.join(hd, f))); P = [tuple(q) for q in S['pairs']]
        for n, a in S['scores'].items():
            if names is None or n in names: HS[n] = dict(zip(P, a))
    # judge scores of the human rewordings are only in human_results (aggregated), not saved per pair: judge rows are not available here
    md += ['## Human rewordings (Step 21d) against same-bin errors of the same reference (point estimates; far fewer than 30 groups: too small to compare)', '', '| scorer | ' + ' | '.join(b[2] for b in BINS) + ' |', '|---|' + '---|' * len(BINS)]
    hbins = collections.Counter(); per = {n: collections.defaultdict(list) for n in SCORERS[:6]}
    for b in hb:
        c = C.get(b['case_id']); x = edit_size(b['reference'], b['candidate']); bn = bin_of(x); hbins[bn] += 1
        if not c: continue
        for n in per:
            h = HS[n].get((b['reference'], b['candidate'])); e = [p.score_of(sc, n, r) for r, xx in c['E'] if bin_of(xx) == bn]; e = [v for v in e if v is not None]
            if h is not None and e: per[n][bn].append(float((np.array(e) < h).mean()))
    md.append('| human rewordings in the bin | ' + ' | '.join(str(hbins[b[2]]) for b in BINS) + ' |')
    for n in per: md.append(f'| {NAMES[n]} | ' + ' | '.join((f"{np.mean(per[n][b[2]]):.2f} (n={len(per[n][b[2]])} items)" if per[n][b[2]] else '—') for b in BINS) + ' |')
    md += ['', 'Judge scores of the human rewordings were not saved per pair (Step 21d keeps aggregates only), so there is no judge row here; see the Step 21d results for the aggregate.', '']
    md += ['Judge rows (`sentence_f1`, `judge_score`) use only pairs in which both candidates were judged (Steps 10d + 12 samples); their bins have far fewer groups.', '']
    open(os.path.join(out, 'tables.md'), 'w').write('\n'.join(md)); json.dump(res, open(os.path.join(out, 'edit_matched.json'), 'w'), indent=1, default=float); print('\n'.join(md[:60]))

if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else 'results/partA/step21e_edit_matched')
