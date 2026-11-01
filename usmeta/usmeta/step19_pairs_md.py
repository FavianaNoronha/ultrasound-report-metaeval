"""Step 19a: markdown tables from cells.json / cutoffs_val.json / transfer.csv (written by step19_pairs)."""
import json, csv, sys, collections
import numpy as np
from .step19_pairs import ALL, TEXT, JUDGE, ORGAN, MIN_N, fm
D = sys.argv[1]; cells = json.load(open(f'{D}/cells.json')); cuts = json.load(open(f'{D}/cutoffs_val.json')); tr = list(csv.DictReader(open(f'{D}/transfer.csv')))
dss = sorted(ORGAN, key=lambda d: (ORGAN[d], d)); md = []
def cell(n, ds, f='all'): return cells.get(f'{n}|{ds}|{f}')
md += ['## 1. Per dataset (test): paired preference, ties, sensitivity and false-alarm rate at the val cut-off', '',
       'pref_strict = share of (error, harmless) pairs where the error scores LOWER; tie = equal scores; pref_half = strict + ½ tie (= AUROC). Sensitivity / false-alarm rate use each dataset\'s cut-off tuned on VAL (flags 90% of val errors; values in section 5). Judge rows: test judge sample only (Steps 10d + 12), cut-off pooled over val datasets. † = fewer than 30 groups: too small to compare.', '']
for org in ('breast', 'thyroid', 'fetal head'):
    md += [f'### {org.upper()} (organs are not pooled across: breast, thyroid, fetal head)', '']
    for ds in [d for d in dss if ORGAN[d] == org]:
        md += [f'**{ds}**', '', '| scorer | cases (groups) | pref_strict | ties | pref_half (AUROC) | sensitivity (errors flagged) | false-alarm rate (harmless flagged) |', '|---|---|---|---|---|---|---|']
        for n in ALL:
            d = cell(n, ds)
            if d: md.append(f"| {n}{' †' if d['n_groups'] < MIN_N else ''} | {d['n_cases']} ({d['n_groups']}) | {fm(d['pref_strict'])} | {fm(d['tie'])} | {fm(d['pref_half'])} | {fm(d['sensitivity'])} | {fm(d['fpr'])} |")
        md.append('')
md += ['## 2. Pooled within one organ only (each dataset keeps its own cut-off; group = dataset:patient)', '', '| organ | scorer | cases (groups) | pref_strict | ties | pref_half (AUROC) | sensitivity | false-alarm rate |', '|---|---|---|---|---|---|---|---|']
for org in ('breast', 'thyroid', 'fetal head'):
    for n in ALL:
        d = cell(n, f'ORGAN:{org}')
        if d: md.append(f"| {org} | {n}{' †' if d['n_groups'] < MIN_N else ''} | {d['n_cases']} ({d['n_groups']}) | {fm(d['pref_strict'])} | {fm(d['tie'])} | {fm(d['pref_half'])} | {fm(d['sensitivity'])} | {fm(d['fpr'])} |")
md += ['', '## 3. By error type (test; pref_half = AUROC for that type, n cases in brackets; sensitivity in `cells.csv`)', '', 'Error fields are those of `bench_v2d` (side, birads, tirads, path, hist, lesion, count, pos, orient, size_mm, size_pct, hc_mm, plane, shape, margin, echo, post, halo, calc, comp, foci). Cells with < 30 groups carry † (too small to compare). Judge columns use the judged subset.', '']
for org in ('breast', 'thyroid', 'fetal head'):
    for ds in [d for d in dss if ORGAN[d] == org]:
        fields = sorted({k.split('|')[2] for k in cells if k.split('|')[1] == ds and k.split('|')[2] != 'all' and cells[k]})
        md += [f'**{ds}**', '', '| error type | ' + ' | '.join(ALL) + ' |', '|---|' + '---|' * len(ALL)]
        for f in fields:
            row = []
            for n in ALL:
                d = cell(n, ds, f); row.append('—' if not d else f"{d['pref_half'][0]:.2f} (n={d['n_cases']}){' †' if d['n_groups'] < MIN_N else ''}")
            md.append(f'| {f} | ' + ' | '.join(row) + ' |')
        md.append('')
md += ['## 4. Held-out cut-off transfer (cut-off tuned on dataset A\'s VAL, applied to dataset B\'s TEST, same organ; text scorers)', '',
       'False-alarm change = (harmless flagged with A\'s cut-off) − (harmless flagged with B\'s own val cut-off), mean over all ordered pairs A→B of the organ (min–max over pairs in brackets); sensitivity change likewise. Per-pair rows with CIs: `transfer.csv`. Judge not included (no per-dataset val judge scores).', '',
       '| organ | scorer | pairs | mean Δ false-alarm rate (min–max) | mean Δ sensitivity (min–max) | false-alarm rate with own cut-off (mean) |', '|---|---|---|---|---|---|']
g = collections.defaultdict(list)
for t in tr: g[(t['organ'], t['scorer'])].append(t)
for org in ('breast', 'thyroid', 'fetal head'):
    for n in TEXT:
        ts = g.get((org, n))
        if ts:
            df, ds_ = [float(t['delta_fpr']) for t in ts], [float(t['delta_sens']) for t in ts]
            md.append(f"| {org} | {n} | {len(ts)} | {np.mean(df):+.3f} ({min(df):+.3f} to {max(df):+.3f}) | {np.mean(ds_):+.3f} ({min(ds_):+.3f} to {max(ds_):+.3f}) | {np.mean([float(t['fpr_own']) for t in ts]):.3f} |")
md += ['', '## 5. Cut-off values (tuned on VAL: 90th percentile of the planted-error scores; flag = score ≤ cut-off)', '', '| scorer | ' + ' | '.join(dss) + ' |', '|---|' + '---|' * len(dss)]
for n in ALL:
    md.append(f'| {n}{" (pooled over val datasets)" if n in JUDGE else ""} | ' + ' | '.join('—' if cuts[f'{n}|{ds}']['cutoff'] is None else f"{cuts[f'{n}|{ds}']['cutoff']:.3f}" for ds in dss) + ' |')
open(f'{D}/tables.md', 'w').write('\n'.join(md)); print('\n'.join(md[:14]))
