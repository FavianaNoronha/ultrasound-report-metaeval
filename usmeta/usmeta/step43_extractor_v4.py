"""Step 43: stricter free-text fact extractor (v4) and a fresh 30-report check graded by a person. NEW file; step27_extractor.py (model, dev-only few-shot examples, JSON-to-facts mapping, comparer), step27_run.py, step28_natural_errors.py and the Step 32 sampler / agreement code are imported unchanged.
v4 changes ONLY the instruction text (prompt variant 'v4'; same model Qwen2.5-7B-Instruct 4-bit, greedy, same dev-only few-shot examples, same output schema). The v4 text is frozen in results/partA/step43_extractor_v4/PREREG.md (SHA-256 checked below).
v4 calls are cached separately in results/partA/step43_extractor_v4/cache.jsonl (key includes the variant name 'v4'); the Step 27 and Step 32 caches are not touched.
    python3 -m usmeta.step43_extractor_v4 validate | sheet | score | step28"""
import os, sys, json, re, time, random, csv, collections, argparse, hashlib
import numpy as np
from . import splits, schema, step27_extractor as X, step27_run as R27, step28_natural_errors as S28
from .step32_extractor_v3 import sample, agreement                       # imported unchanged (importing it points X.CACHE at the Step 32 folder; reset below)

ROOT = X.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step43_extractor_v4'); os.makedirs(OUT, exist_ok=True)
X.CACHE = os.path.join(OUT, 'cache.jsonl'); X.OUT = OUT; S28.OUT = OUT; R27.OUT = OUT           # separate cache and output folder for this step (module-level paths of the imported code)
V4 = ("You extract facts from an ultrasound report into JSON. Reply with ONE line of JSON only, containing every key listed below, in this order.\n"
      "RULES:\n"
      "1. Fill a key only with a fact that the report itself states. If the report does not state it, the value is null. Never infer, guess or complete.\n"
      "2. Record every stated fact. If the report states a value for a key anywhere (findings, summary, impression or a category line), fill that key. Leaving out a stated fact is an error, exactly as inventing one is.\n"
      "3. Copy the report's own words when it gives a range or a combination (a shape such as 'oval to irregular', a margin described with several words). Do not narrow it to one term and do not pick a value the report does not use. Use a listed allowed value only when the report's words match it.\n"
      "4. BI-RADS and TI-RADS are two different scales. birads (breast) is filled only from a BI-RADS category. tirads (thyroid) is filled only from a category the report itself calls TI-RADS or TIRADS. If a thyroid report gives a BI-RADS category, tirads is null (the thyroid keys have no BI-RADS key).\n"
      "5. echo, composition, margin, shape, foci / calcifications and posterior features describe the nodule or mass itself. Words about the surrounding gland, parenchyma or background tissue (for example a heterogeneous gland) do not belong to the nodule's echo.\n"
      "6. pathology is benign, malignant or normal only if the report states a diagnosis in those terms (including 'most likely benign'). Suspicious, concerning, a BI-RADS or TI-RADS category or a recommendation to biopsy is not a stated pathology: null. histology is a named histologic type only if the report names one.\n"
      "7. Fill halo, calcifications and posterior features only if the report mentions an echogenic halo, calcifications or posterior shadowing / enhancement. A bright area that the report says may be something else is not calcifications.\n"
      "8. count: only a number or number word that is written (a single / one, two, three). 'multiple', 'several' or a plural without a number is null.\n"
      "9. A report that describes a mass, nodule or lesion (also as a hypoechoic or hyperechoic area) has a lesion: fill every key the report states about it, even when the report gives no count and no size. Never return all keys null for a report that describes a nodule. Breast lesion_present is false only if the report says there is no lesion. Thyroid count is 0 only if the report says there is no nodule.\n"
      "10. Copy numbers and units exactly as written (do not convert).\n\nKEYS:\n{keys}")
V4_SHA256 = '868a89255a628fa799ab4ec74a1018d1e6e118405d3e2fbdae904d278462d1ce'
assert hashlib.sha256(V4.encode()).hexdigest() == V4_SHA256, 'the v4 instruction text differs from the one frozen in PREREG.md'
X.INSTR['v4'] = V4

def extractor(shots=None): return X.Extractor('v4', shots=shots)

def run_validate(a):
    ex = extractor(); dl = time.time() + a.max_hours * 3600; res = {}
    for split in ('dev', 'val'):
        items = sample(split); flats, bad = R27.run_texts(ex, items, dl, f'v4-{split}')
        if flats is None: return
        per, pooled = agreement(items, flats); res[split] = dict(per_organ=per, pooled_field_agreement=pooled, parse_failures=bad, n=len(items))
        res[split]['wrong_examples'] = [dict(organ=it['organ'], text=it['text'][:200], diffs={fk: [R27.known(it['organ'], it['text']).get(fk), f.get(fk)] for fk in R27.FLAT_FIELDS[it['organ']] if not R27.same(fk, f.get(fk), R27.known(it['organ'], it['text']).get(fk))}) for it, f in zip(items, flats) if any(not R27.same(fk, f.get(fk), R27.known(it['organ'], it['text']).get(fk)) for fk in R27.FLAT_FIELDS[it['organ']])][:25]
    v3 = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step32_extractor_v3', 'validation.json')))
    res['v3_for_reference'] = {s: dict(pooled_field_agreement=v3[s]['pooled_field_agreement'], per_organ={o: v['field_agreement'] for o, v in v3[s]['per_organ'].items()}) for s in ('dev', 'val')}
    res['criterion'] = dict(threshold=0.98, passed=all(res[s]['pooled_field_agreement'] >= 0.98 for s in ('dev', 'val')) and all(v['field_agreement'] >= 0.98 for s in ('dev', 'val') for v in res[s]['per_organ'].values()), v4_sha256=hashlib.sha256(V4.encode()).hexdigest())
    json.dump(res, open(os.path.join(OUT, 'validation.json'), 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k not in ('dev', 'val')}, indent=1)); print({s: (round(res[s]['pooled_field_agreement'], 4), {o: round(v['field_agreement'], 4) for o, v in res[s]['per_organ'].items()}) for s in ('dev', 'val')})

# ---------------------------------------------------------------- fresh check sheet
def excluded():
    """case ids and report texts of every report already in the Step 32 check (docs/step32_check.csv via its key file and texts) and, stricter than the brief, in the Step 28 check (docs/step28_check.csv)"""
    ids = {k['case_id'] for k in json.load(open(os.path.join(ROOT, 'results', 'partA', 'step32_extractor_v3', 'check_sheet_key.json')))}
    t32 = {r[3] for r in list(csv.reader(open(os.path.join(ROOT, 'docs', 'step32_check.csv'), encoding='utf-8')))[2:] if r and r[0].startswith('C')}
    t28 = {r['report_text'] for r in csv.DictReader(open(os.path.join(ROOT, 'docs', 'step28_check.csv'), encoding='utf-8'))}
    return ids, t32, t28

def prepare():
    for f in ('selected.json', 'reports.jsonl'):          # the Step 28 selection and writer reports (read-only copies; no report is regenerated)
        dst = os.path.join(OUT, f)
        if not os.path.exists(dst): open(dst, 'w').write(open(os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors', f)).read())

def fresh_pool():
    prepare(); ids, t32, t28 = excluded(); S = S28.load_all()
    return [s for s in S if s['case_id'] not in ids and s['report'] not in t32 and s['report'] not in t28]

def run_sheet(a):
    pool = fresh_pool(); rng = random.Random(43); pick = []; cnt = {}
    for organ in ('breast', 'thyroid', 'fetal'):
        p = sorted([s for s in pool if s['organ'] == organ], key=lambda s: s['case_id']); cnt[organ] = len(p); rng.shuffle(p); pick += p[:10]
    rng.shuffle(pick); ex = extractor(); rows = []; key = []
    for k, s in enumerate(pick):
        raw = ex.raw(s['organ'], s['report']); js = S28.raw_json(s['organ'], raw); flat, ok = X.to_flat(s['organ'], raw); rid = f'D{k + 1:02d}'
        rows.append([rid, s['organ'], s['report'], json.dumps(js, ensure_ascii=False), '', '', '']); key.append(dict(id=rid, case_id=s['case_id'], organ=s['organ'], dataset=s['dataset'], parse_ok=ok, flat=flat))
    with open(os.path.join(ROOT, 'docs', 'step43_check.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['id', 'organ', 'report_text', 'extracted_json', 'all_fields_right', 'wrong_fields', 'note']); w.writerows(rows)
    json.dump(dict(seed=43, pool_per_organ=cnt, picked=collections.Counter(s['organ'] for s in pick), key=key, v4_sha256=hashlib.sha256(V4.encode()).hexdigest()), open(os.path.join(OUT, 'check_sheet_key.json'), 'w'), indent=1)
    print('wrote docs/step43_check.csv', dict(collections.Counter(s['organ'] for s in pick)), 'pool', cnt)

# ---------------------------------------------------------------- tally of the graded sheet (after the grader has filled docs/step43_check.csv)
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5; return round((c - h) / d, 2), round((c + h) / d, 2)

# author's manual reading of the grader's wrong_fields and notes (wrong rows only; a row can have several types). Not machine-classified.
MANUAL = {
 'BI-RADS category written into tirads on a thyroid report': ['D03', 'D04', 'D07', 'D09', 'D11', 'D17', 'D18', 'D21'],
 'key outside the organ schema added (birads on fetal head / thyroid)': ['D05', 'D12', 'D16'],
 'thyroid nodule echo omitted': ['D03', 'D07', 'D09', 'D11', 'D17', 'D18'],
 'thyroid composition wrong (hypoechoic written as composition) or omitted': ['D04', 'D07', 'D11', 'D16', 'D18'],
 "count 'multiple' written as a number or as the word": ['D04', 'D07'],
 'stated TI-RADS left null (D16: "TIRADS 4C" in the impression)': ['D16'],
 'breast shape narrowed or changed ("somewhat irregular ... lobulated" -> irregular)': ['D01', 'D08', 'D15', 'D28'],
 'breast margin word not as written (mapped to circumscribed / not circumscribed)': ['D01', 'D08', 'D10', 'D15', 'D19', 'D28'],
 'pathology benign filled from suggestive wording ("suggesting", "consistent with", "likely")': ['D02', 'D10', 'D19', 'D26'],
 'halo invented': ['D10', 'D19', 'D29'],
 'echo heterogeneous written for a mass first described as hypoechoic': ['D15', 'D29'],
 'stated "no calcifications" left null': ['D02'],
}

def run_score(a):
    path = a.sheet or os.path.join(ROOT, 'docs', 'step43_check_filled.csv'); rows = [r for r in csv.DictReader(open(path, encoding='utf-8')) if r.get('id', '').startswith('D')]; assert len(rows) == 30, f'{len(rows)} rows'
    V = {r['id']: r['all_fields_right'].strip().lower() for r in rows}; assert set(V.values()) <= {'yes', 'no'}, 'all_fields_right must be yes or no on every row'
    org = {r['id']: r['organ'] for r in rows}; by = {o: dict(right=sum(V[i] == 'yes' for i in V if org[i] == o), n=sum(org[i] == o for i in V)) for o in ('breast', 'thyroid', 'fetal')}
    for o, d in by.items(): d['ci95'] = wilson(d['right'], d['n'])
    bt = dict(right=by['breast']['right'] + by['thyroid']['right'], n=by['breast']['n'] + by['thyroid']['n']); bt['ci95'] = wilson(bt['right'], bt['n']); passed = bt['right'] >= 17
    wf = collections.defaultdict(collections.Counter)
    for r in rows:
        if V[r['id']] == 'no':
            for k in [x.strip().lower() for x in re.split(r'[,;/]', r.get('wrong_fields') or '') if x.strip()]: wf[r['organ']][k] += 1
    res = dict(n=30, by_organ=by, wrong_fields_by_organ={o: dict(c) for o, c in wf.items()}, notes={r['id']: r.get('note', '') for r in rows if V[r['id']] == 'no'}, breast_thyroid=bt, pass_rule='at least 17 of the 20 breast + thyroid reports fully right', passed=passed, wrong_ids=sorted(i for i in V if V[i] == 'no'), v4_sha256=hashlib.sha256(V4.encode()).hexdigest(),
               caveats=['one grader, not blinded to the project, not a clinician', 'rubric differs from Step 32 (BI-RADS on thyroid; see PREREG)', '30 reports, 20 for the rule'])
    wrong_ids = set(res['wrong_ids']); assert all(i in wrong_ids for ids in MANUAL.values() for i in ids), 'manual map names a row that was graded right'
    res['manual_error_types'] = {k: dict(rows=v, n=len(v)) for k, v in MANUAL.items()}; res['manual_error_types_note'] = "author's reading of the grader's wrong_fields and notes; a row can have several types"
    res['sensitivity'] = dict(note='breast + thyroid fully right if the two rows with a single wrong field that is arguably a judgement call (D21 tirads from BI-RADS, D26 pathology from suggestive wording) were counted right', right=bt['right'] + sum(1 for i in ('D21', 'D26') if V.get(i) == 'no'), n=bt['n'])
    json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
    md = ['# Step 43: extractor v4 on 30 fresh free-text reports graded by a person', '', f"**{'PASSES' if passed else 'DOES NOT PASS'} the pre-registered rule: {bt['right']} of {bt['n']} breast + thyroid reports fully right (rule: at least 17 of 20; 95% Wilson CI {bt['ci95'][0]}-{bt['ci95'][1]}).** " + ('Step 28 (natural errors) is to be re-run with v4 (`step43_extractor_v4 step28`).' if passed else 'Step 28 stays inconclusive; v4 labels are not validated on free text.'), '',
          '| organ | fully right / n | 95% CI |', '|---|---|---|'] + [f"| {o} | {d['right']} / {d['n']} | {d['ci95'][0]}-{d['ci95'][1]} |" for o, d in by.items()] + ['', f"Wrong rows: {', '.join(res['wrong_ids']) or 'none'}. Wrong fields (grader's `wrong_fields`, by organ): " + (', '.join(o + ' ' + ', '.join(f'{k} x{n}' for k, n in c.most_common()) for o, c in wf.items()) or 'none listed') + ". Pre-registration: [PREREG.md](PREREG.md). One grader, not blinded to the project, not a clinician; rubric differs from Step 32 (BI-RADS on thyroid), so the numbers are not strictly comparable to Step 32's 13 of 30.", '']
    md += ['## Wrong rows by error type (author reading of the grader notes; a row can have several types)', '', '| error type | rows | n |', '|---|---|---|'] + [f"| {k} | {', '.join(v)} | {len(v)} |" for k, v in MANUAL.items()] + ['', f"Sensitivity: counting the two single-judgement-call rows (D21, D26) as right would give {res['sensitivity']['right']} of {res['sensitivity']['n']} breast + thyroid, still far under 17.", '',
          '## Reading', '',
          "- **Instruction rule 4 was not followed on thyroid:** on 8 of the 10 thyroid reports that state a BI-RADS category, v4 still wrote it into `tirads` (and added a `birads` key on a ninth); the model (Qwen2.5-7B-Instruct, 4-bit, greedy) did not obey the rule although templated dev / val agreement stayed at 0.9989 / 0.9986. The thyroid nodule's echo was left null on 6 reports whose text says hypoechoic nodules or areas.",
          '- **Breast:** 9 of 10 reports have at least one wrong field; the most frequent are the margin word not as written (6), shape narrowed or changed (4), pathology benign taken from suggestive wording (4) and a halo the report does not state (3).',
          "- **Fetal head 8 of 10:** both wrong rows (D05, D12) are wrong only because the JSON added a `birads` key that is not in the fetal schema (BI-RADS 0 is in the report text); the other eight are all-null on reports that state no plane or head circumference.",
          '- Step 32 (v3, a different grader rubric and different reports) had breast 7 of 12, thyroid 0 of 12, fetal head 6 of 6; v4 breast 1 of 10, thyroid 1 of 10, fetal head 8 of 10. The two checks are not strictly comparable (rubric, reports, one grader), so this is not evidence that v4 is worse than v3 on breast, but it shows no improvement on thyroid and no pass.', '',
          '## Caveats', '',
          '- **One grader, not blinded to the project, not a clinician; AI use by the grader cannot be verified.** Several wrong rows rest on judgement calls: on four breast rows (D02, D10, D19, D26) the grader treated "most consistent with / suggesting a benign lesion" as not a stated pathology, which is stricter than the grading guide (rule 7 accepts "most likely benign"); counting those pathology calls as right still leaves each of D02, D10 and D19 wrong on other fields, and D26 would become right (see the sensitivity line). The margin and shape rows follow guide rule 3 (copy the report\'s words).',
          '- 30 reports (20 for the rule); the rule is fixed in the PREREG and the verdict does not depend on any single row (the sensitivity count is 4 of 20).',
          '- Same Qwen2.5-VL-3B reports and writer as Steps 28 / 32; the thyroid and fetal-head reports state BI-RADS (a breast scale), a writer failure (LIMITATIONS 36).',
          '- v4 changed instruction text only (same model, schema and dev-only few-shot examples); prompt rules alone did not change the 4-bit 7B model\'s behaviour on the thyroid BI-RADS case. **Step 28 (natural errors) was not re-run and stays inconclusive.**', '']
    open(os.path.join(OUT, 'results.md'), 'w').write('\n'.join(md)); print('\n'.join(md))
    import subprocess, platform
    def g(*c):
        try: return subprocess.check_output(c, text=True, cwd=ROOT).strip()
        except Exception: return None
    json.dump(dict(step='43', model=X.MODEL, decoding='greedy', variant='v4', v4_sha256=hashlib.sha256(V4.encode()).hexdigest(), sheet_seed=43, git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), prereg_commit=g('git', 'log', '--format=%h', '-1', '--', 'results/partA/step43_extractor_v4/PREREG.md'), python=platform.python_version(), platform=platform.platform(), date=time.strftime('%Y-%m-%d'), graded_file='docs/step43_check_filled.csv (untracked)', passed=passed, step28_rerun=False), open(os.path.join(OUT, 'run_info.json'), 'w'), indent=1)

def run_step28(a):
    r = json.load(open(os.path.join(OUT, 'results.json')))
    if not r.get('passed'): print('v4 did not pass the pre-registered rule: Step 28 is not re-run (it stays inconclusive).'); return
    for f in ('selected.json', 'reports.jsonl'):
        dst = os.path.join(OUT, f)
        if not os.path.exists(dst): open(dst, 'w').write(open(os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors', f)).read())
    S = S28.load_all(); ex = extractor(); out = {}; t0 = time.time()
    for i, s in enumerate(S):
        if time.time() - t0 > a.max_hours * 3600: print('time limit'); return
        flat, ok = ex.facts(s['organ'], s['report']); js = S28.raw_json(s['organ'], ex.raw(s['organ'], s['report'])); rf, rok = ex.facts(s['organ'], s['reference'])
        out[s['case_id']] = dict(flat=flat, ok=ok, raw=js, ref_extracted=rf, ref_ok=rok, regex=S28.qwen_real.regex_reading(s['report']))
        if i % 20 == 0: print('extract v4', i, len(S), round(time.time() - t0), 's', flush=True)
    json.dump(out, open(os.path.join(OUT, 'extraction.json'), 'w')); print('parse failures', sum(not v['ok'] for v in out.values()))
    sc = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors', 'scores.json'))); assert sc['case_ids'] == [s['case_id'] for s in S]
    sc['llm_finding_f1'] = [X.llm_finding_f1(out[s['case_id']]['ref_extracted'], out[s['case_id']]['flat'], s['organ']) for s in S]; json.dump(sc, open(os.path.join(OUT, 'scores.json'), 'w')); S28.analyse(a)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=3.0); ap.add_argument('--sheet', default=None); a = ap.parse_args()
    {'validate': run_validate, 'sheet': run_sheet, 'score': run_score, 'step28': run_step28}[a.cmd](a)
