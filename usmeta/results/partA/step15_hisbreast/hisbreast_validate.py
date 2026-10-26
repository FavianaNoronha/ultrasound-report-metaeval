"""HiSBreast: automatic validation of the machine translations (nobody on the team reads Vietnamese). ALL outputs stay in usmeta/local_data/hisbreast/ (git-ignored).
  check 1  key facts of the Vietnamese original vs the English translation (Gemma-2-9B)
  check 2  key facts of the English translation vs a SECOND translation by a different, non-Gemma model (Qwen2.5-7B-Instruct 4-bit)
  check 3  key facts of the original vs a back-translation (Gemma's English -> Vietnamese, by Qwen2.5-7B)
Key facts: numbers (+units), BI-RADS codes, side words (phai / trai / hai ben), negation, 'no abnormality' phrases, axillary-node mention, plus soft concept flags.
The Vietnamese dictionary is hand-written by the assistant (not a bilingual human): a missing word makes a check fail (cases are dropped), it never makes one pass.
    python3 -m usmeta.hisbreast_validate translate2 | backtranslate | checks"""
import json, os, re, sys, time, unicodedata, collections
from . import hisbreast, graders

D = hisbreast.OUT; JUDGE = 'mlx-community/Qwen2.5-7B-Instruct-4bit'
def nfc(t): return unicodedata.normalize('NFC', t or '').casefold()

BIRADS = re.compile(r'bi\s*-?\s*rads?\s*[:\-]?\s*(?:category\s*|loại\s*|độ\s*)?(\d)\s*([abc])?\b')
NUM = re.compile(r'(\d+(?:[.,]\d+)?)\s*(mm|cm|%)?')
NEG_VI = re.compile(r'\b(không|chưa|ko|khong|no|not|without|unclear)\b'); NEG_EN = re.compile(r'\b(no|not|without|absent|none|neither|nor|cannot|unremarkable|unclear|undetermined|unknown|uncertain|unspecified|non-?specific)\b')
NOABN_VI = re.compile(r'(chưa|không)\s+(?:\w+\s+){0,2}?(bất thường|tổn thương|dấu hiệu bất thường)|bình thường|no abnormal|normal'); NOABN_EN = re.compile(r'no\s+(?:\w+\s+){0,2}?(abnormal|lesion|finding)|within normal|normal|unremarkable|nothing abnormal')
CONCEPTS = {  # name -> (vietnamese regex, english regex)
 'axillary': (r'hạch nách|nách|axill', r'axill'), 'abscess': (r'áp[\s-]?xe|abscess', r'abscess'), 'inflammation': (r'viêm', r'inflam|mastitis'),
 'cyst': (r'nang', r'cyst'), 'mass': (r'bướu|khối|u\b|tumor|nodule', r'mass|tumou?r|nodule|lump|lesion'), 'followup': (r'theo dõi', r'follow|monitor|surveil'),
 'biopsy': (r'sinh thiết|chọc hút|fna', r'biops|fna|aspirat'), 'cancer': (r'ung thư|\bk\b|ác tính', r'cancer|carcinoma|malignan|\bk\b'), 'benign': (r'lành tính', r'benign'),
 'postsurgery': (r'sau mổ|phẫu thuật|đã mổ', r'post-?op|surgery|surgical|operat|mastectomy|resect'), 'fibro': (r'u xơ|xơ tuyến|xơ', r'fibro')}

def side_vi(t):
    s = set()
    if re.search(r'hai bên|2 bên|both|bilateral', t): s.add('B')
    if re.search(r'phải|\bright\b', t): s.add('R')            # an English word left untranslated by the back-translation still names the side
    if re.search(r'trái|\bleft\b', t): s.add('L')
    return s
def side_en(t):
    s = set()
    if re.search(r'both|bilateral|two sides', t): s.add('B')
    if re.search(r'\bright\b', t): s.add('R')
    if re.search(r'\bleft\b', t): s.add('L')
    return s
def facts(text, lang):
    t = nfc(text); b = sorted(m[1] + (m[2] or '') for m in BIRADS.finditer(t)); rest = BIRADS.sub(' ', t)
    nums = collections.Counter()
    for m in NUM.finditer(rest):
        v = float(m[1].replace(',', '.')); u = m[2]
        if u == 'cm': v *= 10
        nums[round(v, 1)] += 1
    f = dict(birads=b, side=sorted(side_vi(t) if lang == 'vi' else side_en(t)), numbers=dict(sorted(nums.items())), neg=bool((NEG_VI if lang == 'vi' else NEG_EN).search(t)),
             noabn=bool((NOABN_VI if lang == 'vi' else NOABN_EN).search(t)))
    for k, (a, e) in CONCEPTS.items(): f['c_' + k] = bool(re.search(a if lang == 'vi' else e, t))
    return f
HARD = ('birads', 'side', 'numbers', 'neg', 'noabn', 'c_axillary')
def compare(fa, fb, hard=HARD):
    """-> (hard mismatch names, soft mismatch names)"""
    h = [k for k in hard if fa[k] != fb[k]]; s = [k for k in fa if k.startswith('c_') and k not in hard and fa[k] != fb[k]]; return h, s

PROMPT_T = """Translate this Vietnamese breast-ultrasound radiologist conclusion into English.
Rules: translate faithfully and completely (every part separated by " | " must appear, in the same order, separated by " | "); keep BI-RADS terms and categories exactly (for example BI-RADS 4A); keep numbers and units; do not add, remove or interpret anything; do not explain.
Terminology: tuyến vú / vú = breast; phải = right; trái = left; hai bên = both sides; bướu / khối = mass; nang = cyst; hạch nách = axillary lymph node; theo dõi = follow up; chưa ghi nhận bất thường = no abnormality recorded; viêm = inflammation; áp xe = abscess; sau phẫu thuật / mổ = post-surgery; nghi ngờ = suspicious; sinh thiết = biopsy; ung thư = cancer; lành tính = benign; ác tính = malignant; kích thước = size.
Reply with the English translation only, on one line.

VIETNAMESE:
{vi}
"""
PROMPT_B = """Translate this English breast-ultrasound radiologist conclusion into Vietnamese, as a Vietnamese radiologist would write it.
Rules: translate faithfully and completely (parts separated by " | " stay separated by " | "); keep BI-RADS terms and categories exactly (for example BI-RADS 4A); keep numbers and units; do not add, remove or interpret anything; do not explain.
Reply with the Vietnamese translation only, on one line.

ENGLISH:
{en}
"""
def llm(): return graders.LocalLLM(JUDGE, cache_dir=os.path.join(D, '.llm_cache_q'), max_tokens=200)
def clean(t): return ' '.join((t or '').replace('<end_of_turn>', '').split())

def run_llm(inp_key, prompt, out, src):
    cli = llm(); items = json.load(open(src)); done = {json.loads(l)['k'] for l in open(out)} if os.path.exists(out) else set(); t0 = time.time()
    for i, (k, v) in enumerate([x for x in items if x[0] not in done]):
        o = clean(cli.ask(prompt.format(**{inp_key: v}), valid=lambda x: bool(x.strip()))); open(out, 'a').write(json.dumps(dict(k=k, out=o), ensure_ascii=False) + '\n')
        if i % 25 == 0: print(i, round(time.time() - t0), 's', flush=True)

def exams(): return [json.loads(l) for l in open(os.path.join(D, 'exams_translated.jsonl'))]

def prep_inputs():
    ex = exams(); uniq = {}
    for e in ex: uniq[e['vi_clean']] = e['en']
    json.dump([[k, k] for k in sorted(uniq)], open(os.path.join(D, 'in_translate2.json'), 'w'), ensure_ascii=False)
    json.dump([[k, en] for k, en in sorted(uniq.items())], open(os.path.join(D, 'in_backtranslate.json'), 'w'), ensure_ascii=False)
    return uniq

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'prep': print(len(prep_inputs()), 'unique texts')
    if cmd == 'translate2': run_llm('vi', PROMPT_T, os.path.join(D, 'translations2_qwen.jsonl'), os.path.join(D, 'in_translate2.json'))
    if cmd == 'backtranslate': run_llm('en', PROMPT_B, os.path.join(D, 'backtranslations_qwen.jsonl'), os.path.join(D, 'in_backtranslate.json'))

def strip_prefix(t): return re.sub(r'^(english|vietnamese|translation)\s*:\s*', '', clean(t), flags=re.I)

CJK = re.compile(r'[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]')
def degenerate(src, out): return bool(CJK.search(out)) or len(out.split()) > 3 * max(2, len(src.split()))

PROMPT_T_STRICT = PROMPT_T + "\nThe answer must be plain English written with Latin letters only, no other language or script, no extra items, about as long as the input.\n"
PROMPT_B_STRICT = PROMPT_B + "\nThe answer must be Vietnamese written with Latin letters (Vietnamese diacritics allowed) only; no Chinese or other scripts, no extra items, about as long as the input.\n"

def fix_degenerate():
    """one retry with a stricter prompt for degenerate generations (CJK characters or runaway length); still-degenerate outputs are marked unusable (the check fails, reason logged)"""
    cli = llm(); n = 0
    for name, strict, key in (('translations2_qwen', PROMPT_T_STRICT, 'vi'), ('backtranslations_qwen', PROMPT_B_STRICT, 'en')):
        src = json.load(open(os.path.join(D, 'in_translate2.json' if name.startswith('trans') else 'in_backtranslate.json'))); inp = {k: v for k, v in src}
        out = os.path.join(D, name + '_retry.jsonl'); done = {json.loads(l)['k'] for l in open(out)} if os.path.exists(out) else set()
        for l in open(os.path.join(D, name + '.jsonl')):
            r = json.loads(l); o = strip_prefix(r['out'])
            if degenerate(inp[r['k']], o) and r['k'] not in done:
                o2 = strip_prefix(cli.ask(strict.format(**{key: inp[r['k']]}), valid=lambda x: bool(x.strip()))); open(out, 'a').write(json.dumps(dict(k=r['k'], out=o2), ensure_ascii=False) + '\n'); n += 1
    print('retried', n)

def load_gen(name):
    G = {json.loads(l)['k']: strip_prefix(json.loads(l)['out']) for l in open(os.path.join(D, name + '.jsonl'))}; rp = os.path.join(D, name + '_retry.jsonl')
    if os.path.exists(rp):
        for l in open(rp): r = json.loads(l); G[r['k']] = strip_prefix(r['out'])
    return G

def run_checks():
    ex = exams(); T2 = load_gen('translations2_qwen'); BT = load_gen('backtranslations_qwen')
    uniq = {}
    for e in ex: uniq[e['vi_clean']] = e['en']
    res = {}; ctr = collections.Counter(); per_type = {c: collections.Counter() for c in (1, 2, 3)}
    for vi, en in uniq.items():
        fv, fe = facts(vi, 'vi'), facts(en, 'en'); f2 = facts(T2.get(vi, ''), 'en'); fb = facts(BT.get(vi, ''), 'vi')
        r = {}
        for c, (a, b) in {1: (fv, fe), 2: (fe, f2), 3: (fv, fb)}.items():
            h, s = compare(a, b); unusable = (c == 2 and degenerate(vi, T2.get(vi, ''))) or (c == 3 and degenerate(en, BT.get(vi, ''))); r[c] = dict(hard=h, soft=s, unusable=unusable, ok=not h and not unusable)
            if unusable: ctr[f'check{c}_unusable_generation'] += 1
            for x in h: per_type[c][x] += 1
        r['passes'] = r[1]['ok'] and r[2]['ok'] and r[3]['ok']; r['score'] = sum(2 * len(r[c]['hard']) + len(r[c]['soft']) for c in (1, 2, 3)); res[vi] = r
        for c in (1, 2, 3): ctr[f'check{c}_failed'] += not r[c]['ok']
        ctr['passes_all'] += r['passes']
    # exam level
    per_exam = {e['exam']: res[e['vi_clean']] for e in ex}
    summary = dict(unique_texts=len(uniq), exams=len(ex), texts_failed_check1=ctr['check1_failed'], texts_failed_check2=ctr['check2_failed'], texts_failed_check3=ctr['check3_failed'], texts_passing_all=ctr['passes_all'], texts_check2_unusable_generation=ctr['check2_unusable_generation'], texts_check3_unusable_generation=ctr['check3_unusable_generation'],
                   exams_passing_all=sum(r['passes'] for r in per_exam.values()), exams_failed_any=sum(not r['passes'] for r in per_exam.values()),
                   exams_failed_check1=sum(not r[1]['ok'] for r in per_exam.values()), exams_failed_check2=sum(not r[2]['ok'] for r in per_exam.values()), exams_failed_check3=sum(not r[3]['ok'] for r in per_exam.values()),
                   hard_mismatch_types={f'check{c}': dict(per_type[c]) for c in (1, 2, 3)})
    json.dump(dict(summary=summary, texts={k: v for k, v in res.items()}), open(os.path.join(D, 'validation.json'), 'w'), ensure_ascii=False)
    # 60 most uncertain texts for an optional human look (local, git-ignored)
    import csv
    ranked = sorted(uniq, key=lambda v: (-res[v]['score'], v))[:60]
    with open(os.path.join(D, 'uncertain_cases.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['rank', 'passed_all_checks', 'uncertainty_score', 'check1_hard', 'check2_hard', 'check3_hard', 'soft_mismatches', 'vietnamese_original', 'english_gemma', 'english_qwen', 'back_translation_vi_qwen'])
        for i, v in enumerate(ranked, 1):
            r = res[v]; w.writerow([i, r['passes'], r['score'], ';'.join(r[1]['hard']), ';'.join(r[2]['hard']), ';'.join(r[3]['hard']), ';'.join(sorted(set(r[1]['soft'] + r[2]['soft'] + r[3]['soft']))), v, uniq[v], T2.get(v, ''), BT.get(v, '')])
    return summary

if __name__ == '__main__' and sys.argv[1] == 'fix': fix_degenerate()
if __name__ == '__main__' and sys.argv[1] == 'checks': print(json.dumps(run_checks(), indent=1))
