"""Step 18: markdown tables from the test report (usmeta.step18 report test ...) and the H3 summary. Numbers only; the narrative is written by hand in results.md."""
import json, sys

ORDER = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'finding_f1', 'sentence_f1', 'judge_score']
LV = ('TR3', 'TR4', 'TR5'); MIN_N = 30
def ci(a, d=3): return f'[{a[0]:+.{d}f}, {a[1]:+.{d}f}]'
def small(p): return ' †' if p is None or min(p['n_pairs'], p['n_groups']) < MIN_N else ''

def primary(R, delta=3, mode='digit-matched', lv='ALL'):
    out = ['| scorer | pairs (groups) | controls | mean d = non-crossing − crossing | DiD | crossing penalised more / tie / less | verdict |', '|---|---|---|---|---|---|---|']
    for n in ORDER:
        d = R['scorers'].get(n)
        if not d: continue
        p = d['pairs'].get(f'delta{delta}|{mode}|{lv}')
        if not p: out.append(f'| {n} | — | | | | | no pairs |'); continue
        verdict = 'penalises crossing MORE (CI above 0)' if p['did_ci'][0] > 0 else ('penalises crossing LESS (CI below 0)' if p['did_ci'][1] < 0 else 'no difference (CI includes 0)')
        out.append(f"| {n}{small(p)} | {p['n_pairs']} ({p['n_groups']}) | {p['n_controls']} | {p['mean_d']:+.4f} {ci(p['mean_d_ci'], 4)} | {p['did']:+.4f} {ci(p['did_ci'], 4)} | {p['share_crossing_penalised_more']:.2f} / {p['share_tie']:.2f} / {p['share_less']:.2f} | {verdict} |")
    return out

def by_level(R, delta=3, mode='digit-matched'):
    out = ['| scorer | ' + ' | '.join(f'{l} pairs (groups): DiD [CI]' for l in LV) + ' |', '|---|' + '---|' * len(LV)]
    for n in ORDER:
        d = R['scorers'].get(n)
        if not d: continue
        cells = []
        for l in LV:
            p = d['pairs'].get(f'delta{delta}|{mode}|{l}')
            cells.append('—' if not p else f"{p['n_pairs']} ({p['n_groups']}){small(p)}: {p['did']:+.4f} {ci(p['did_ci'], 4)}")
        out.append(f'| {n} | ' + ' | '.join(cells) + ' |')
    return out

def sensitivity(R):
    keys = [('delta2|digit-matched|ALL', 'δ=2 mm, digit-matched'), ('delta3|digit-matched|ALL', 'δ=3 mm, digit-matched (primary)'), ('delta5|digit-matched|ALL', 'δ=5 mm, digit-matched'), ('delta3|all-valid|ALL', 'δ=3 mm, all valid pairs')]
    out = ['| scorer | ' + ' | '.join(k[1] for k in keys) + ' |', '|---|' + '---|' * len(keys)]
    for n in ORDER:
        d = R['scorers'].get(n)
        if not d: continue
        cells = []
        for k, _ in keys:
            p = d['pairs'].get(k); cells.append('—' if not p else f"n={p['n_pairs']}{small(p)}: {p['did']:+.4f} {ci(p['did_ci'], 4)}")
        out.append(f'| {n} | ' + ' | '.join(cells) + ' |')
    return out

def dose(R, scorers, ty):
    nominals = (1, 2, 3, 5) if ty == 'mm' else (5, 10, 20, 30, 50)
    out = ['| scorer | ' + ' | '.join(f'±{n} {ty}' for n in nominals) + ' | smallest bin with CI above 0.5 |', '|---|' + '---|' * len(nominals) + '---|']
    for n in scorers:
        d = R['scorers'].get(n)
        if not d: continue
        cells = []; first = None
        for nom in nominals:
            c = d['dose'].get(f'{ty}|{nom}|all')
            if not c: cells.append('—'); continue
            sm = ' †' if min(c['n_units'], c['n_groups']) < MIN_N else ''
            cells.append(f"{c['auroc']:.2f} ({c['ci'][0]:.2f}–{c['ci'][1]:.2f}) n={c['n_units']}{sm}")
            if first is None and c['ci'][0] > 0.5 and not sm: first = f'±{nom} {ty}'
        out.append(f'| {n} | ' + ' | '.join(cells) + f" | {first or 'none (or too small)'} |")
    return out

def gates(R):
    return ['| scorer | identical copies | mean | min |', '|---|---|---|---|'] + [f"| {n} | {R['scorers'][n]['identical']['n']} | {R['scorers'][n]['identical']['mean']:.4f} | {R['scorers'][n]['identical']['min']:.4f} |" for n in ORDER if n in R['scorers']]

if __name__ == '__main__':
    R = json.load(open(sys.argv[1])); print('\n'.join(['PRIMARY'] + primary(R) + ['', 'LEVEL'] + by_level(R) + ['', 'SENS'] + sensitivity(R) + ['', 'DOSE mm'] + dose(R, ORDER, 'mm') + ['', 'DOSE pct'] + dose(R, ORDER, 'pct') + ['', 'GATES'] + gates(R)))
