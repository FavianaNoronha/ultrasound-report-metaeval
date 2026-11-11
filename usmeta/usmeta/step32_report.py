"""Step 32 report: results/partA/step32_extractor_v3/results.md (no model calls)."""
import os, json, random, csv, sys, platform, time, subprocess
import numpy as np
from . import step32_extractor_v3 as V, step28_natural_errors as S28, step27_extractor as X
D = V.OUT; ROOT = V.ROOT
val = json.load(open(os.path.join(D, 'validation.json'))); R3 = json.load(open(os.path.join(D, 'results.json'))); R2 = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors', 'results.json')))
E3 = json.load(open(os.path.join(D, 'extraction.json'))); E2 = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors', 'extraction.json')))
S28.OUT = D; S = S28.load_all(); sample = random.Random(0).sample(S, 30)           # the 30 reports of the owner's Step 28 hand check, C01..C30
hand = {r['id']: r for r in csv.DictReader(open(os.path.join(ROOT, 'docs', 'step28_check.csv'), encoding='utf-8'))}
FLAG = {'C07': ['lesion', 'count'], 'C08': ['count', 'comp'], 'C14': ['path'], 'C15': ['lesion'], 'C23': ['count', 'comp'], 'C24': ['halo'], 'C25': ['path', 'halo', 'margin'], 'C30': ['comp']}
def f(v, k=2):
    if not v: return '—'
    return f'{v[0]:.{k}f}' if v[1] is None else f'{v[0]:.{k}f} ({v[1]:.{k}f}–{v[2]:.{k}f})'
NAMES = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('llm_finding_f1', 'llm_finding_f1'), ('sentence_f1', 'judge sentence_f1'), ('judge_score', 'judge_score')]
pooled = lambda R, n: R['by_organ']['ALL']['metrics'][n].get('auroc_wrong_vs_correct')
md = ['# Step 32: stricter free-text extractor (extractor v3) and the Step 28 metrics re-run', '',
      '**PROVISIONAL until the owner fills `docs/step32_check.csv`** (30 reports, hand check of the v3 extractions). Nothing in this file is hand-verified for v3. Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step32_extractor_v3.py`, `step32_report.py` (new files; `step27_extractor.py`, `step28_natural_errors.py` imported unchanged; the v3 calls are cached separately). Prompt version **v3** is logged in `CHANGELOG.md`.', '',
      '## What changed (extractor v3)', '',
      'Only the instruction text. Same model (Qwen2.5-7B-Instruct, 4-bit, greedy), same dev-only few-shot examples, same JSON schema and the same JSON-to-facts mapping and comparer as Step 27. New instruction (full text in `usmeta/step32_extractor_v3.py`): fill a key only with a fact **explicitly stated**, null otherwise; never infer pathology (a BI-RADS / TI-RADS category, "suspicious", "biopsy recommended" are not a stated pathology), halo, calcifications, posterior features, count ("multiple" is null) or composition (echogenicity words are echo, never composition); presence rules for breast (`lesion_present` true / false / null) and thyroid (count 0 only if "no nodule" is stated).', '',
      '## Re-validation on the templated dev and val sets (criterion: field agreement >= 0.98)', '',
      '| set | reports | field agreement pooled | breast | thyroid | fetal head | all fields right per report (breast / thyroid / fetal head) | parse failures |', '|---|---|---|---|---|---|---|---|']
for s in ('dev', 'val'):
    v = val[s]; po = v['per_organ']; md.append(f"| {s} | {v['n']} | {v['pooled_field_agreement']:.4f} | {po['breast']['field_agreement']:.4f} | {po['thyroid']['field_agreement']:.4f} | {po['fetal']['field_agreement']:.4f} | {po['breast']['all_fields_correct']:.2f} / {po['thyroid']['all_fields_correct']:.2f} / {po['fetal']['all_fields_correct']:.2f} | {v['parse_failures']} |")
md += ['', f"**Criterion {'PASSED' if val['criterion']['passed'] else 'FAILED'}** (every organ x set >= 0.98). For reference, v2 on the same 300-report dev sample: mean per-field agreement breast {val['v2_dev_for_reference']['per_field_agreement_mean']['breast']:.4f}, thyroid {val['v2_dev_for_reference']['per_field_agreement_mean']['thyroid']:.4f}, fetal head {val['v2_dev_for_reference']['per_field_agreement_mean']['fetal']:.4f}; all fields right per report 0.96 / 0.99 / 1.00. Known facts = the rule extractor on the templated text; the val set is a fresh draw of 100 reports per organ (seed 0, val split). The remaining dev/val misses are listed in `validation.json` (for example thyroid \"echogenic foci\" read as an echo pattern, and a side read from \"upper left part of the image\").", '',
      '## The owner\'s Step 28 hand check, replayed with v3 (diagnostic only; not a v3 hand check)', '',
      'For each of the 8 extractions the owner marked wrong for v2, the field(s) named in the owner\'s note, with the v2 value, the v3 value, and what the owner said. "Fixed" means the v3 value is the one the note implies is correct (null for an invented field); this is read from the note, not re-verified.', '', '| id | organ | field | v2 value | v3 value | owner note (v2) |', '|---|---|---|---|---|---|']
fixed = tot = 0
for k, s in enumerate(sample):
    cid = f'C{k + 1:02d}'
    if cid in FLAG:
        for fl in FLAG[cid]:
            a, b = E2[s['case_id']]['flat'].get(fl), E3[s['case_id']]['flat'].get(fl); tot += 1
            md.append(f"| {cid} | {s['organ']} | {fl} | {a} | {b} | {hand[cid]['note'][:110]} |")
md += ['']
right = [f'C{k + 1:02d}' for k in range(30) if hand[f'C{k + 1:02d}']['extraction_right_or_wrong (fill: right / wrong)'].strip().lower() == 'right' and sample[k]['organ'] != 'fetal']
chg = [(cid, {fl: (E2[sample[int(cid[1:]) - 1]['case_id']]['flat'].get(fl), E3[sample[int(cid[1:]) - 1]['case_id']]['flat'].get(fl)) for fl in set(E2[sample[int(cid[1:]) - 1]['case_id']]['flat']) | set(E3[sample[int(cid[1:]) - 1]['case_id']]['flat']) if E2[sample[int(cid[1:]) - 1]['case_id']]['flat'].get(fl) != E3[sample[int(cid[1:]) - 1]['case_id']]['flat'].get(fl)}) for cid in right]
md += [f"Of the {len(right)} breast / thyroid extractions the owner marked right for v2, {sum(1 for _, d in chg if d)} change under v3 (fields changed: " + '; '.join(f"{cid} {', '.join(f'{k}: {a} -> {b}' for k, (a, b) in d.items())}" for cid, d in chg if d) + '). Any change among these needs the new hand check to say whether v3 lost a stated fact or removed a wrong one.', '',
       '## Step 28 metrics re-run on the same 180 reports (60 per organ), v2 vs v3', '',
       f"Same reports, same word / embedding / judge scores (saved Step 28 scores); only the extractor changes, and with it `llm_finding_f1` **and the labels** (fact F1, stated / wrong key facts), because Step 28 reads the truth comparison through the extractor. AUROC for separating reports with at least one wrong key fact from fully correct ones (95% CI by image bootstrap): v2 pooled {R2['by_organ']['ALL']['n_wrong_reports']} wrong of {R2['by_organ']['ALL']['n_checkable']} checkable, v3 pooled {R3['by_organ']['ALL']['n_wrong_reports']} wrong of {R3['by_organ']['ALL']['n_checkable']} checkable.", '',
       '| scorer | AUROC wrong vs correct, v2 (pooled) | v3 (pooled) | v2 breast | v3 breast | Spearman with fact F1, v2 pooled | v3 pooled |', '|---|---|---|---|---|---|---|']
for n, nm in NAMES:
    m2, m3 = R2['by_organ']['ALL']['metrics'].get(n, {}), R3['by_organ']['ALL']['metrics'].get(n, {}); b2, b3 = R2['by_organ']['breast']['metrics'].get(n, {}), R3['by_organ']['breast']['metrics'].get(n, {})
    md.append(f"| {nm} | {f(m2.get('auroc_wrong_vs_correct'))} | {f(m3.get('auroc_wrong_vs_correct'))} | {f(b2.get('auroc_wrong_vs_correct'))} | {f(b3.get('auroc_wrong_vs_correct'))} | {f(m2.get('spearman'))} | {f(m3.get('spearman'))} |")
md += ['', '| organ | metric | v2 | v3 |', '|---|---|---|---|']
for o in ('breast', 'thyroid', 'fetal', 'ALL'):
    a, b = R2['by_organ'][o], R3['by_organ'][o]
    md.append(f"| {o} | reports with a wrong key fact / stating no key fact | {a['share_with_a_wrong_key_fact']*100:.0f}% / {a['share_stating_no_key_fact']*100:.0f}% | {b['share_with_a_wrong_key_fact']*100:.0f}% / {b['share_stating_no_key_fact']*100:.0f}% |")
    md.append(f"| {o} | mean fact F1 | {a['mean_fact_f1']:.2f} | {b['mean_fact_f1']:.2f} |")
    md.append(f"| {o} | checkable / wrong / fully correct | {a['n_checkable']} / {a['n_wrong_reports']} / {a['n_fully_correct']} | {b['n_checkable']} / {b['n_wrong_reports']} / {b['n_fully_correct']} |")
md += ['', 'Per-field stated / correct counts (v3) are in `results.json`. The Gemma `judge_score` is floored at 0.00 on almost every free-text report (as in Step 28), so its row carries no information.', '',
       '## What can and cannot be concluded', '',
       '- v3 keeps the templated-text agreement (>= 0.98 on dev and val): the stricter prompt did not cost accuracy on the text it was tuned on.',
       '- Whether v3 is **more accurate on free text** is **not known**: the replay above reads the owner\'s v2 notes, not a v3 hand check. `docs/step32_check.csv` (30 fresh reports: 12 breast, 12 thyroid, 6 fetal head; none of the 30 reports of the Step 28 check) is waiting for the right / wrong marks; until then every v3 free-text number here is **provisional**, and a result that moves with the extractor is a statement about the extractor and the labels, not about the scorers.',
       '- The Step 28 decision (scorers track similarity and completeness, not mistakes; inconclusive) is not changed by this file; see the pooled AUROC columns above and judge them only after the hand check.', '',
       '## Caveats', '',
       '- Same 180 reports, same writer, same scorers: only the extractor changed. Labels depend on the extractor, so v2 and v3 AUROCs are not independent estimates of the scorers.',
       '- Thyroid presence cannot be read from a missing field (count null and no attributes maps to "absent"), a mapping unchanged from Step 27; fetal head has no checkable key fact in these reports.',
       '- One extractor model, one prompt change, greedy decoding. Possible training exposure of Qwen is unverifiable.', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=ROOT).strip()
    except Exception: return None
json.dump(dict(step='32', extractor='v3 (instruction text only)', model=X.MODEL, validation_criterion=val['criterion'], provisional_until='docs/step32_check.csv filled', git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d')), open(os.path.join(D, 'run_info.json'), 'w'), indent=1); print('wrote', len(md))
