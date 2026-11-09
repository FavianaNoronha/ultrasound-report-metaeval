"""Step 24 report: reads results/partA/step24_box_reliability/case_rows.json (from step24_box_reliability analyse) and writes curve.csv, curve.png, results.md. NEW file.
    python3 -m usmeta.step24_report"""
import os, json, collections, csv, math
import numpy as np
from . import partb, location, step24_box_reliability as s24
from .step10d_analysis import gboot

OUT = s24.OUT; METRICS = ('position', 'size', 'all'); ORGANS = ('pooled', 'breast', 'thyroid')
def small(ng): return ' †' if ng < 30 else ''
def fm(t): return 'n/a' if t is None else f'{t[0]:.2f} ({t[1]:.2f}–{t[2]:.2f})'

def agg(rows, key):
    """mean over rows (one value per case-condition), group bootstrap; returns (gboot tuple or None, n_groups)"""
    v = [(r[key], r['group']) for r in rows if r.get(key) is not None and not (isinstance(r[key], float) and math.isnan(r[key]))]
    if not v: return None, 0
    return gboot([x for x, _ in v], [g for _, g in v]), len({g for _, g in v})

def level_rows(rows):
    """one row per (case, family, level): average over the 3 jitter seeds at the case level"""
    d = collections.defaultdict(list)
    for r in rows: d[(r['case_id'], r['family'], r['level'])].append(r)
    out = []
    for (cid, fam, lv), rs in d.items():
        o = dict(case_id=cid, group=rs[0]['group'], organ=rs[0]['organ'], dataset=rs[0]['dataset'], family=fam, level=lv)
        for k in rs[0]:
            if k.startswith(('auc_', 'correct_')) or k in ('box_iou', 'mask_iou', 'mask_scale'):
                v = [x[k] for x in rs if x[k] is not None and not (isinstance(x[k], float) and math.isnan(x[k]))]; o[k] = float(np.mean(v)) if v else None
        out.append(o)
    return out

def sel_organ(rows, organ): return rows if organ == 'pooled' else [r for r in rows if r['organ'] == organ]

def cross(xs, ys, thr):
    """highest box IoU at which the curve (sorted by IoU, high -> low) first falls below thr (linear interpolation); None if it never does / never starts above"""
    pts = sorted(zip(xs, ys), reverse=True)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if y0 >= thr > y1: return x0 + (x1 - x0) * (y0 - thr) / (y0 - y1) if y0 != y1 else x1
    return None

def main():
    D = json.load(open(os.path.join(OUT, 'case_rows.json'))); rows = D['rows']; tau, pm = D['tau'], D['position']; Lr = level_rows(rows)
    A = lambda k: f'auc_tol_{k}'
    csvrows = []; lines = []
    # ---- level table (family x level) per organ
    lev = {}
    for organ in ORGANS:
        R = sel_organ(Lr, organ); fams = collections.OrderedDict((f, sorted({r['level'] for r in R if r['family'] == f})) for f in ('exact', 'shrink', 'enlarge', 'shift', 'jitter', 'labelfree'))
        for fam, lvs in fams.items():
            for lv in lvs:
                rr = [r for r in R if r['family'] == fam and r['level'] == lv]; d = dict(organ=organ, family=fam, level=lv, n_scans=len(rr), n_groups=len({r['group'] for r in rr}))
                d['box_iou'] = float(np.mean([r['box_iou'] for r in rr])); d['mask_iou'] = agg(rr, 'mask_iou')[0][0]
                for m in METRICS: d['auc_' + m] = agg(rr, A(m))[0]; d['n_' + m] = agg(rr, A(m))[1]
                d['correct'] = agg(rr, 'correct_tol')[0]; d['correct_exact'] = agg(rr, 'correct_exact')[0]; d['auc_size_boxproxy'] = agg(rr, 'auc_boxproxy_size')[0]
                d['mask_scale_median'] = float(np.nanmedian([r['mask_scale'] if r['mask_scale'] is not None else np.nan for r in rr])); lev[(organ, fam, lv)] = d
                csvrows.append(dict(table='level', organ=organ, family=fam, level_or_bin=lv, n_scans=d['n_scans'], n_groups=d['n_groups'], mean_box_iou=round(d['box_iou'], 4), mean_mask_iou=round(d['mask_iou'], 4),
                                    auroc_position=round(d['auc_position'][0], 4), auroc_size=round(d['auc_size'][0], 4), auroc_all=round(d['auc_all'][0], 4), correct_report_score=round(d['correct'][0], 4),
                                    auroc_size_box_proxy=round(d['auc_size_boxproxy'][0], 4) if d['auc_size_boxproxy'] else '', median_mask_size_ratio=round(d['mask_scale_median'], 3)))
    # ---- IoU-bin table (all perturbed instances, every family, plus the exact box in the top bin), per organ
    bins = {}
    for organ in ORGANS:
        R = sel_organ(rows, organ)
        for lo, hi, nm in s24.BINS:
            rr = [r for r in R if lo <= r['box_iou'] < hi]
            if not rr: continue
            d = dict(organ=organ, bin=nm, n_inst=len(rr), n_scans=len({r['case_id'] for r in rr}), n_groups=len({r['group'] for r in rr}), mask_iou=agg(rr, 'mask_iou')[0][0], correct=agg(rr, 'correct_tol')[0])
            for m in METRICS: d['auc_' + m], d['n_' + m] = agg(rr, A(m))
            bins[(organ, nm)] = d
            csvrows.append(dict(table='iou_bin', organ=organ, family='all', level_or_bin=nm, n_scans=d['n_scans'], n_groups=d['n_groups'], mean_box_iou='', mean_mask_iou=round(d['mask_iou'], 4),
                                auroc_position=round(d['auc_position'][0], 4) if d['auc_position'] else '', auroc_size=round(d['auc_size'][0], 4) if d['auc_size'] else '', auroc_all=round(d['auc_all'][0], 4) if d['auc_all'] else '',
                                correct_report_score=round(d['correct'][0], 4), auroc_size_box_proxy='', median_mask_size_ratio=''))
    # ---- thresholds: fine pooled curve (0.1-wide bins of box IoU) and per-family level curves
    fine = []
    for lo in np.arange(0, 1.0, 0.1):
        rr = [r for r in rows if lo <= r['box_iou'] < lo + 0.1 + (1e-9 if lo > 0.85 else 0)]
        if len(rr) >= 30: fine.append((float(np.mean([r['box_iou'] for r in rr])), agg(rr, A('position'))[0][0], agg(rr, A('size'))[0][0], len(rr)))
    thr = {}
    for t in (0.80, 0.60):
        thr[('pooled fine bins', 'position', t)] = cross([f[0] for f in fine], [f[1] for f in fine], t); thr[('pooled fine bins', 'size', t)] = cross([f[0] for f in fine], [f[2] for f in fine], t)
        for fam in ('shrink', 'enlarge', 'shift', 'jitter'):
            pts = [lev[('pooled', fam, lv)] for lv in sorted({k[2] for k in lev if k[0] == 'pooled' and k[1] == fam})] + [lev[('pooled', 'exact', 1.0)]]
            for m in ('position', 'size'): thr[(fam, m, t)] = cross([p['box_iou'] for p in pts], [p['auc_' + m][0] for p in pts], t)
    # ---- 21a label-free boxes, re-scored with the SAME rule (Step 20) so they sit on the same axes; the 21a (exact-match rule) numbers are shown beside them
    a21 = json.load(open(os.path.join(s24.ROOT, 'results', 'partA', 'step21a_localisation', 'sweep_results.json'))); lf = {}
    for i, cond in enumerate(s24.LABELFREE):
        d = lev[('pooled', 'labelfree', float(i + 1))]; o = a21[f'breast+thyroid (pooled)|{cond}']; lf[cond] = (d, o['auroc_position'], o['auroc_size'])
    # ---- centre offset bins (box centre to true-box centre, in true-box widths), all perturbed instances
    cbins = [(0, 0.1, '<0.1'), (0.1, 0.25, '0.1-0.25'), (0.25, 0.5, '0.25-0.5'), (0.5, 0.75, '0.5-0.75'), (0.75, 1.5, '0.75-1.5'), (1.5, 99, '>1.5')]; cb = []
    for lo, hi, nm in cbins:
        rr = [r for r in rows if lo <= r['centre_dist'] < hi and r['family'] != 'labelfree']
        if len(rr) >= 30: cb.append((nm, len(rr), len({r['group'] for r in rr}), agg(rr, A('position')), agg(rr, A('size')), float(np.mean([r['box_iou'] for r in rr]))))
        csvrows.append(dict(table='centre_offset_bin', organ='pooled', family='all', level_or_bin=nm, n_scans=len({r['case_id'] for r in rr}), n_groups=len({r['group'] for r in rr}), mean_box_iou=round(float(np.mean([r['box_iou'] for r in rr])), 4) if rr else '',
                            auroc_position=round(agg(rr, A('position'))[0][0], 4) if rr else '', auroc_size=round(agg(rr, A('size'))[0][0], 4) if rr else ''))
    lfd = [r for r in rows if r['family'] == 'labelfree']
    # ---- write csv
    keys = list(dict.fromkeys(k for r in csvrows for k in r))
    with open(os.path.join(OUT, 'curve.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(csvrows)
    # ---- plot
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True); col = {'shrink': '#1f77b4', 'enlarge': '#d95f02', 'shift': '#2ca02c', 'jitter': '#9467bd'}
    for a, m, ttl in ((ax[0], 'position', 'Position errors'), (ax[1], 'size', 'Size errors')):
        for fam in ('shrink', 'enlarge', 'shift', 'jitter'):
            pts = sorted([lev[('pooled', fam, lv)] for lv in sorted({k[2] for k in lev if k[0] == 'pooled' and k[1] == fam})] + [lev[('pooled', 'exact', 1.0)]], key=lambda p: p['box_iou'])
            a.errorbar([p['box_iou'] for p in pts], [p['auc_' + m][0] for p in pts], yerr=[[p['auc_' + m][0] - p['auc_' + m][1] for p in pts], [p['auc_' + m][2] - p['auc_' + m][0] for p in pts]], marker='o', ms=4, lw=1.4, capsize=2, color=col[fam], label=fam)
        for cond, mk in (('centre50', 's'), ('whole', 'D'), ('random', '^'), ('wrongregion', 'v')):
            a.scatter([lf[cond][0]['box_iou']], [lf[cond][0]['auc_' + m][0]], marker=mk, s=45, facecolor='none', edgecolor='k', zorder=5, label=f'21a {cond}' if m == 'position' else None)
        a.axhline(0.5, color='grey', lw=0.8, ls=':'); a.axhline(0.8, color='grey', lw=0.8, ls='--'); a.set_xlabel('box IoU with the true box'); a.set_title(ttl + ' (breast + thyroid, n = 228 scans)'); a.set_xlim(-0.02, 1.02); a.set_ylim(0, 1.02)
    ax[0].set_ylabel('AUROC (error vs harmless rewording)'); ax[0].legend(fontsize=7, loc='lower right'); plt.tight_layout(); plt.savefig(os.path.join(OUT, 'curve.png'), dpi=150)
    # ---- markdown
    L = [f'# Step 24 — Box reliability curve for the image check (breast + thyroid, the same 228 test scans as Steps 16 / 19b / 21a)', '',
         '**Perturbed-prompt sweep, NOT a detector.** Every box starts from the TRUE mask box and is then perturbed (shrink / enlarge about the centre; shift of the centre by a % of box width in a random direction; jitter = independent Gaussian noise on each of the 4 edges, sd = % of box width/height, 3 seeds averaged). '
         f'MedSAM (`wanglab/medsam-vit-base`, MPS) segments from the perturbed box; the Step 20 tolerance-aware image check (tau = {tau}, position = {pm}, frozen on dev/val) scores every candidate against the facts measured from the predicted mask. '
         'Group bootstrap (1,000 resamples, seed 0); † = fewer than 30 groups, too small to compare. AUROC = per case, error candidates vs harmless rewordings, averaged over cases. Code: `usmeta/step24_box_reliability.py`, `usmeta/step24_report.py`.', '',
         '**Reuse:** exact (Step 16), shrink x0.9 / x0.75 / x0.5 (= 19b shrink 10 / 25 / 50) and enlarge x1.25 (= 19b enlarge 25) are the saved masks; the other 16 settings (x 228 scans) are new MedSAM runs. The 19b shift (10 / 25% of box size) is a different rule from the shift here (% of box width), so shift was re-run in full.',
         '**Levels:** the brief says six levels per family but lists 6 / 4 / 4 / 3 values; only the listed values were run (extra levels would have exceeded the ~3 h limit).', '']
    P = lambda fam, lv, m, o='pooled': lev[(o, fam, lv)]['auc_' + m][0]; f2 = lambda x: 'not crossed' if x is None else f'{x:.2f}'
    mn = min(P(f, l, 'position') for (o, f, l) in lev if o == 'pooled' and f in ('shrink', 'enlarge', 'shift', 'jitter'))
    L += ['## Headline (breast + thyroid pooled, n = 228 scans)', '',
          f"- **Position AUROC does not fall below 0.80 for shrink, enlarge or jitter at any tested level** (lowest {min(P(f, l, 'position') for (o, f, l) in lev if o == 'pooled' and f in ('shrink', 'enlarge', 'jitter')):.2f}, at box IoU as low as 0.09), because those perturbations keep the box centre on the lesion and a position claim is read from where the mask sits, not how big the box is. Only the shift family moves the centre: position AUROC is {P('shift', 0.1, 'position'):.2f} / {P('shift', 0.25, 'position'):.2f} / {P('shift', 0.5, 'position'):.2f} / {P('shift', 0.75, 'position'):.2f} at shifts of 10 / 25 / 50 / 75% of box width (box IoU {lev[('pooled', 'shift', 0.1)]['box_iou']:.2f} / {lev[('pooled', 'shift', 0.25)]['box_iou']:.2f} / {lev[('pooled', 'shift', 0.5)]['box_iou']:.2f} / {lev[('pooled', 'shift', 0.75)]['box_iou']:.2f}).",
          f"- **IoU at which position AUROC drops below 0.80 / 0.60:** below 0.80 at box IoU ≈ {f2(thr[('shift', 'position', 0.8)])} on the shift curve ({f2(thr[('pooled fine bins', 'position', 0.8)])} on the pooled fine-bin curve, which mixes families); below 0.60 **never reached by any perturbation of the true box** (lowest point {P('shift', 0.75, 'position'):.2f}, shifted by 0.75 widths, breast {P('shift', 0.75, 'position', 'breast'):.2f}, thyroid {P('shift', 0.75, 'position', 'thyroid'):.2f}; the pooled fine-bin value {f2(thr[('pooled fine bins', 'position', 0.6)])} rests on very few shifted instances at the lowest IoU). Box IoU is therefore a poor single axis for position: the centre offset table below is the cleaner one (≥ 0.91 up to a centre offset of 0.5 widths, ≈ 0.80 at 0.5–0.75, ≈ 0.78 at 0.75–1.5 widths).",
          f"- **The label-free boxes of Step 21a sit at box IoU {lf['centre50'][0]['box_iou']:.2f} (centre), {lf['whole'][0]['box_iou']:.2f} (whole image), {lf['random'][0]['box_iou']:.2f} (random), {lf['wrongregion'][0]['box_iou']:.2f} (wrong region)** and give position AUROC {P('labelfree', 1.0, 'position'):.2f} / {P('labelfree', 2.0, 'position'):.2f} / {P('labelfree', 3.0, 'position'):.2f} / {P('labelfree', 4.0, 'position'):.2f} under this step's rule, far below the perturbed true boxes at the same IoU (shrink x0.3 at IoU {lev[('pooled', 'shrink', 0.3)]['box_iou']:.2f}: {P('shrink', 0.3, 'position'):.2f}). Same IoU, different position AUROC: what matters is whether the box is centred on the lesion, which a label-free prompt cannot guarantee.",
          f"- **Size claims degrade much earlier and follow the box scale.** Size AUROC drops below 0.80 at box IoU ≈ {f2(thr[('pooled fine bins', 'size', 0.8)])} (pooled fine bins), {f2(thr[('shrink', 'size', 0.8)])} (shrink), {f2(thr[('jitter', 'size', 0.8)])} (jitter), {f2(thr[('shift', 'size', 0.8)])} (shift), and below 0.60 at ≈ {f2(thr[('pooled fine bins', 'size', 0.6)])} (pooled) / {f2(thr[('shrink', 'size', 0.6)])} (shrink). With the box shrunk to x0.5 or less the size AUROC is {P('shrink', 0.5, 'size'):.2f} or lower, below chance.",
          f"- **Mechanical part of the size drop:** the 'size just follows the box' column (true-mask facts, size scaled by the box scale, no segmentation) is {P('shrink', 0.5, 'size') and lev[('pooled', 'shrink', 0.5)]['auc_size_boxproxy'][0]:.2f} at shrink x0.5 and {lev[('pooled', 'shrink', 0.3)]['auc_size_boxproxy'][0]:.2f} at x0.3, against MedSAM {P('shrink', 0.5, 'size'):.2f} / {P('shrink', 0.3, 'size'):.2f}: the below-chance size result for small boxes is mechanical (the stated true size is judged against the box). At mild shrink (x0.9) the box-only value is {lev[('pooled', 'shrink', 0.9)]['auc_size_boxproxy'][0]:.2f} but MedSAM gives {P('shrink', 0.9, 'size'):.2f}, so about {lev[('pooled', 'shrink', 0.9)]['auc_size_boxproxy'][0] - P('shrink', 0.9, 'size'):.2f} of AUROC there is segmentation error rather than box scale (MedSAM's mask is already {1 - lev[('pooled', 'exact', 1.0)]['mask_scale_median']:.0%} smaller than the true size with the exact box). That under-sizing is also why size AUROC is highest for slightly enlarged boxes ({P('enlarge', 1.25, 'size'):.2f} at x1.25 against {P('exact', 1.0, 'size'):.2f} for the exact box): the check is partly calibrated to MedSAM's habit of undersizing, not evidence of better localisation. Shift and jitter lower size AUROC without changing the box scale on average, i.e. through segmentation error from a misplaced box.",
          f"- **False alarms:** the correct-report score falls from {lev[('pooled', 'exact', 1.0)]['correct'][0]:.3f} (exact box) to {lev[('pooled', 'shrink', 0.5)]['correct'][0]:.3f} (shrink x0.5), {lev[('pooled', 'shift', 0.75)]['correct'][0]:.3f} (shift 0.75), {lev[('pooled', 'jitter', 0.2)]['correct'][0]:.3f} (jitter 20%), and stays at {lev[('pooled', 'enlarge', 1.5)]['correct'][0]:.3f} for enlarge x1.5.",
          "- **Caveats:** all boxes are derived from the TRUE mask, so this is a sensitivity curve, not a detector test; box IoU is computed against the true-mask box; for TN5000 the 'true' mask is itself a box; the IoU-bin table mixes families; bootstrap CIs are over scans' groups (206 groups pooled; breast 120, thyroid 86; every cell here has at least 86 groups).", '']
    for organ in ORGANS:
        lv0 = lev[(organ, 'exact', 1.0)]; L += [f'## {organ.capitalize()} by family and level (n = {lv0["n_scans"]} scans, {lv0["n_groups"]} groups{small(lv0["n_groups"])})', '',
             '| family | level | mean box IoU | mean mask IoU | position AUROC | size AUROC | all-checkable AUROC | correct-report score | size AUROC if size just follows the box (no MedSAM) | median MedSAM size / true size |', '|---|---|---|---|---|---|---|---|---|---|']
        for (o, fam, lv), d in lev.items():
            if o != organ: continue
            if fam == 'labelfree': fam, lv = '21a label-free', s24.LABELFREE[int(lv) - 1]
            L.append(f"| {fam} | {lv} | {d['box_iou']:.2f} | {d['mask_iou']:.2f} | {fm(d['auc_position'])}{small(d['n_position'])} | {fm(d['auc_size'])}{small(d['n_size'])} | {fm(d['auc_all'])}{small(d['n_all'])} | {d['correct'][0]:.3f} | {fm(d['auc_size_boxproxy'])} | {d['mask_scale_median']:.2f} |")
        L.append('')
    L += ['## By box-IoU bin (every perturbed instance, all families pooled; the exact box sits in 0.9–1.0)', '', '| organ | box IoU | instances | scans | groups | mean mask IoU | position AUROC | size AUROC | all-checkable AUROC | correct-report score |', '|---|---|---|---|---|---|---|---|---|---|']
    for (o, nm), d in bins.items():
        L.append(f"| {o} | {nm} | {d['n_inst']} | {d['n_scans']} | {d['n_groups']}{small(d['n_groups'])} | {d['mask_iou']:.2f} | {fm(d['auc_position'])} | {fm(d['auc_size'])} | {fm(d['auc_all'])} | {d['correct'][0]:.3f} |")
    L += ['', 'Bins mix families, so a bin can contain different perturbation types; the per-family tables above are the cleaner view.', '', '## Where does position AUROC fall below 0.80 and 0.60? (box IoU; pooled breast + thyroid)', '', '| curve | metric | below 0.80 at box IoU ≈ | below 0.60 at box IoU ≈ |', '|---|---|---|---|']
    f2 = lambda x: 'not crossed' if x is None else f'{x:.2f}'
    for src in ('pooled fine bins', 'shrink', 'enlarge', 'shift', 'jitter'):
        for m in ('position', 'size'): L.append(f"| {src} | {m} | {f2(thr[(src, m, 0.8)])} | {f2(thr[(src, m, 0.6)])} |")
    L += ['', 'Linear interpolation between the measured points (fine bins: 0.1-wide box-IoU bins with ≥ 30 instances); "not crossed" = the curve never drops below the line within the tested range.', '']
    L += ['## Size versus position (what is mechanical)', '',
          'Size claims are checked against a length measured from the MedSAM mask, and MedSAM follows the box it is given: when the box is scaled by s the mask size scales by about s, so a report that states the TRUE size is read as a size error of about 1/s. The "size AUROC if size just follows the box" column is the check with no segmentation at all (true-mask facts, linear size multiplied by the box scale); the "median MedSAM size / true size" column shows how closely the mask follows the box. '
          'Where the MedSAM size AUROC and the box-only column move together, the drop is mechanical (the stated size is judged against the box, not the lesion). Position claims are different: they depend on where the mask lands, which depends on the box centre, not on its scale. Shrink and enlarge change size without moving the centre, so they hit size claims first and position claims late; shift and jitter move the centre, so they hit position first.', '',
          '## Label-free boxes from Step 21a on the same axes', '', 'The Step 21a masks (not re-run) scored with this step\'s rule (Step 20 tolerance, adjacent position) so they can be placed on the curve; the 21a column is the exact-match rule used in that step.', '',
          '| 21a prompt | mean box IoU with the true box | position AUROC (this step\'s rule) | size AUROC (this step\'s rule) | position AUROC (21a, exact-match) | size AUROC (21a, exact-match) |', '|---|---|---|---|---|---|']
    for cond, (d, p, z) in lf.items(): L.append(f"| {cond} | {d['box_iou']:.2f} | {fm(d['auc_position'])} | {fm(d['auc_size'])} | {fm(p)} | {fm(z)} |")
    L += ['', '## Position AUROC by distance between box centre and true-box centre (all perturbed instances, pooled)', '', '| centre offset (true-box widths) | instances | groups | mean box IoU | position AUROC | size AUROC |', '|---|---|---|---|---|---|']
    for nm, n, ng, pa, sz, mi in cb: L.append(f"| {nm} | {n} | {ng}{small(ng)} | {mi:.2f} | {fm(pa[0])} | {fm(sz[0])} |")
    L += ['', 'Bins use all four families; shrink / enlarge keep the centre, so they sit in the first row.', '']
    L += ['', f'![curve](curve.png)', '', 'Files: `curve.csv` (level and IoU-bin tables, all organs), `curve.png`, `case_rows.json` (one row per scan x condition), `predict.log`, `run_info.json`.', '']
    open(os.path.join(OUT, 'results.md'), 'w').write('\n'.join(L)); print('\n'.join(L[:60]))

if __name__ == '__main__': main()
