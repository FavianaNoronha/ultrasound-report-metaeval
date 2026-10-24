"""Step 8b: borrowed evaluation ideas, with thresholds fixed on VAL (or dev+val for the judge) and numbers reported on TEST.
  D (discrimination, ReEvalMed idea)  = % of planted errors a scorer flags;  R (robustness) = % of harmless_small / matched / harmless_large candidates NOT flagged
  false-alarm rate (breast-US auditing idea) = % of error-free candidates (identical + harmless) flagged at the threshold that gives 90% error recall (frozen threshold rule)
  report-level vs error-level sensitivity for sentence_check (cases with 2 planted errors: any caught vs each caught)
Flag = score BELOW the threshold. Threshold = the largest cut-off t such that at least 90% of VAL errors have score < t... computed as the 90th percentile of val error scores (flag if score <= it).
Frozen scorers are not modified; this file only reads their scores."""
import json, collections
import numpy as np

def threshold(err_scores, recall=0.9):
    """cut-off so that >= `recall` of the validation errors are flagged (score <= cut-off)"""
    return float(np.quantile(np.asarray(err_scores), recall))

def dr(rows, S, thr_by, names):
    """rows: bench rows with kind/harmless_type; S: {'pairs','scores'}; thr_by[(dataset, scorer)] -> cut-off. returns per dataset/scorer dict"""
    idx = {tuple(p): i for i, p in enumerate(S['pairs'])}; out = {}
    for n in names:
        arr = S['scores'][n]
        for ds in sorted({r['dataset'] for r in rows}):
            t = thr_by.get((ds, n))
            if t is None: continue
            f = lambda sel: [arr[idx[(r['reference'], r['candidate'])]] <= t for r in rows if r['dataset'] == ds and sel(r)]
            e = f(lambda r: r['kind'] == 'error'); small = f(lambda r: r['kind'] == 'harmless' and r['harmless_type'] == 'small'); matched = f(lambda r: r['kind'] == 'harmless' and r['harmless_type'] == 'matched')
            large = f(lambda r: r['kind'] == 'harmless' and r['harmless_type'] == 'large'); free = f(lambda r: r['kind'] in ('identical', 'harmless') and r['harmless_type'] != 'other')
            m = lambda x: float(np.mean(x)) if x else None
            out.setdefault(ds, {})[n] = dict(threshold=t, D=m(e), R_small=1 - m(small) if small else None, R_matched=1 - m(matched) if matched else None, R_large=1 - m(large) if large else None, false_alarm=m(free), n_err=len(e))
    return out
