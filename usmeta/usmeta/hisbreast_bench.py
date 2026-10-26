"""HiSBreast planted-error benchmark on the KEPT exams (passed the three automatic translation checks). Local only (git-ignored): the English texts are machine translations of
licence-blank patient data. True report = the validated English conclusion. Cases = exams (group = exam id); splits from local_data/hisbreast/hisbreast_splits.jsonl.
    python3 -m usmeta.hisbreast_bench paraphrase | pjudge | build"""
import json, os, re, sys, random, time, collections
from . import hisbreast, hisbreast_validate as V, hisbreast_parse as P, graders, judge2

D = hisbreast.OUT
GEMMA = 'mlx-community/gemma-2-9b-it-4bit'
PROMPT_PARA = """Reword this breast-ultrasound radiologist conclusion using different words, keeping exactly the same medical facts.
Rules: keep every BI-RADS code, number and unit, every side (right / left / both) and every negation exactly; do not add, remove or interpret anything; keep the parts separated by " | " in the same order.
Reply with the reworded conclusion only, on one line.

CONCLUSION:
{t}
"""
PROMPT_MEAN = """Do these two breast-ultrasound conclusions have the SAME clinical meaning (same findings, same side, same BI-RADS category, same numbers, same negations, same recommendation)?
Wording and order may differ. Answer with one word: YES or NO.

A: {a}
B: {b}
"""

def kept(strict=True):
    ex = V.exams(); val = json.load(open(os.path.join(D, 'validation.json')))['texts']; sp = {json.loads(l)['exam']: json.loads(l)['split'] for l in open(os.path.join(D, 'hisbreast_splits.jsonl'))}; out = []
    for e in ex:
        r = val[e['vi_clean']]; ok = r['passes'] if strict else (r['1']['ok'] and (r['2']['ok'] or r['3']['ok']))
        if ok: out.append(dict(exam=e['exam'], split=sp[e['exam']], vi=e['vi_clean'], en=V.strip_prefix(e['en']), strict=r['passes']))
    return out

def paraphrase():
    cli = graders.LocalLLM(GEMMA, cache_dir=os.path.join(D, '.llm_cache_g'), max_tokens=160); out = os.path.join(D, 'paraphrases.jsonl'); done = {json.loads(l)['en'] for l in open(out)} if os.path.exists(out) else set()
    texts = sorted({k['en'] for k in kept(strict=False)}); t0 = time.time()
    for i, t in enumerate([x for x in texts if x not in done]):
        p = V.strip_prefix(cli.ask(PROMPT_PARA.format(t=t), valid=lambda x: bool(x.strip()))); open(out, 'a').write(json.dumps(dict(en=t, para=p), ensure_ascii=False) + '\n')
        if i % 25 == 0: print(i, len(texts), round(time.time() - t0), 's', flush=True)

def pjudge():
    """non-Gemma 'same clinical meaning' judgement of every paraphrase (Qwen2.5-7B)"""
    cli = graders.LocalLLM(V.JUDGE, cache_dir=os.path.join(D, '.llm_cache_q'), max_tokens=8); out = os.path.join(D, 'paraphrase_judged.jsonl'); done = {json.loads(l)['en'] for l in open(out)} if os.path.exists(out) else set(); t0 = time.time()
    P_ = [json.loads(l) for l in open(os.path.join(D, 'paraphrases.jsonl'))]
    for i, r in enumerate([x for x in P_ if x['en'] not in done]):
        a = cli.ask(PROMPT_MEAN.format(a=r['en'], b=r['para']), valid=lambda x: bool(x.strip())).strip().upper()
        fa, fb = V.facts(r['en'], 'en'), V.facts(r['para'], 'en'); h, s = V.compare(fa, fb)
        open(out, 'a').write(json.dumps(dict(r, judge=a[:12], same_meaning=a.startswith('YES'), facts_preserved=not h, hard_diff=h, differs=r['en'].strip().lower() != r['para'].strip().lower()), ensure_ascii=False) + '\n')
        if i % 25 == 0: print(i, round(time.time() - t0), 's', flush=True)

if __name__ == '__main__' and sys.argv[1] in ('paraphrase', 'pjudge'): {'paraphrase': paraphrase, 'pjudge': pjudge}[sys.argv[1]]()

# ---------------------------------------------------------------- planted errors and harmless rewordings on the real (translated) conclusions
ORDER = ['1', '2', '3', '4a', '4b', '4c', '5', '6']
BRX = re.compile(r'(bi\s*-?\s*rads?\s*[:\-]?\s*(?:category\s*)?)(\d)\s*([abc])?\b', re.I)
def code_index(d, l): c = d + (l or '').lower(); return ORDER.index(c if c in ORDER else (d + 'a' if d == '4' else d)) if (c in ORDER or d == '4' or d in ORDER) else None
def birads_sev(i, j): return 3 if (i <= 2) != (j <= 2) else (2 if abs(i - j) >= 2 else 1)
def swap_case(m, new): w = m.group(0); return new.upper() if w.isupper() else (new.capitalize() if w[0].isupper() else new)
def parts_of(t): return [p.strip() for p in t.split('|') if p.strip()]

def errors_for(t):
    out = []   # (error type, category, severity, magnitude, new text)
    m = BRX.search(t)
    if m:
        i = code_index(m.group(2), m.group(3))
        if i is not None:
            for d in (1, -1):
                j = i + d
                if 0 <= j < len(ORDER):
                    c = ORDER[j].upper(); new = t[:m.start()] + m.group(1) + c + t[m.end():]; out.append(('birads', 'wrong severity/category', birads_sev(i, j), abs(d), new))
    tl = t.lower(); sides = ('right' in tl, 'left' in tl)
    if sides[0] != sides[1]:
        new = re.sub(r'\b(right|left)\b', lambda m: swap_case(m, 'left' if m.group(0).lower() == 'right' else 'right'), t, flags=re.I); out.append(('side_swap', 'wrong location', 3, None, new))
    noabn = re.search(r'no\s+abnormalit\w*(\s+(recorded|noted|seen|detected))?', t, re.I); mass = re.search(r'\b(mass(es)?|nodules?|lesions?|tumou?rs?)\b', t, re.I)
    if noabn and not mass: out.append(('negation_flip', 'false finding', 3, None, t[:noabn.start()] + 'Mass seen' + t[noabn.end():]))
    if mass and not noabn:
        ps = parts_of(t); idx = [k for k, p in enumerate(ps) if re.search(r'\b(mass(es)?|nodules?|lesions?|tumou?rs?)\b', p, re.I)]
        if idx: ps2 = list(ps); ps2[idx[0]] = 'No abnormality recorded'; out.append(('negation_flip', 'missed finding', 3, None, ' | '.join(ps2)))
    ps = parts_of(t); ax = [k for k, p in enumerate(ps) if re.search(r'axill', p, re.I)]
    if ax and len(ps) > 1: out.append(('missed_axillary', 'missed finding', 2, None, ' | '.join(p for k, p in enumerate(ps) if k not in ax)))
    if not ax: out.append(('invented_axillary', 'false finding', 2, None, t.rstrip(' .|') + ' | Axillary lymph node enlarged'))
    if re.search(r'\bbenign\b', t, re.I): out.append(('benign_to_suspicious', 'wrong severity/category', 3, None, re.sub(r'\bbenign\b', 'suspicious for malignancy', t, flags=re.I)))
    elif re.search(r'suspicious|malignan|cancer', t, re.I): out.append(('suspicious_to_benign', 'wrong severity/category', 3, None, re.sub(r'suspicious( for malignancy)?|malignan\w*|cancer', 'benign', t, count=1, flags=re.I)))
    if re.search(r'follow[\s-]?up', t, re.I): out.append(('recommendation', 'wrong severity/category', 2, None, re.sub(r'follow[\s-]?up', 'biopsy recommended', t, count=1, flags=re.I)))
    elif re.search(r'biops', t, re.I): out.append(('recommendation', 'wrong severity/category', 2, None, re.sub(r'biops\w*( recommended)?', 'follow up', t, count=1, flags=re.I)))
    n = re.search(r'(\d+(?:[.,]\d+)?)\s*(mm|cm)\b', t, re.I)
    if n:
        v = float(n.group(1).replace(',', '.')); out.append(('size_x2', 'wrong measurement', 2, 2.0, t[:n.start(1)] + f'{v * 2:g}' + t[n.end(1):]))
    return [o for o in out if o[4].strip() and o[4].strip().lower() != t.strip().lower()]

SYN = [('mass', 'lesion'), ('lesion', 'mass'), ('recorded', 'noted'), ('follow up', 'follow-up'), ('both sides', 'bilateral'), ('suspicious', 'suspect')]
def harmless_for(t):
    out = []; ps = parts_of(t)
    if len(ps) > 1: out.append(('reorder', 'small', ' | '.join(ps[::-1])))
    out.append(('form_sentence', 'small', '. '.join(ps) + '.')); out.append(('form_bullet', 'small', '\n'.join('- ' + p for p in ps)))
    for a, b in SYN:
        m = re.search(r'\b' + re.escape(a) + r'\b', t, re.I)
        if m: out.append(('synonym1', 'matched', t[:m.start()] + swap_case(m, b) + t[m.end():])); break
    return [o for o in out if o[2].strip().lower() != t.strip().lower()]

def build(strict_only=False):
    K = kept(strict=False); PJ = {json.loads(l)['en']: json.loads(l) for l in open(os.path.join(D, 'paraphrase_judged.jsonl'))}; rows = []; stats = collections.Counter()
    for e in K:
        if strict_only and not e['strict']: continue
        t = e['en']; base = dict(case_id=e['exam'], dataset='HiSBreast', split=e['split'], group_id=e['exam'], strict=e['strict'], reference=t); n = [0]
        def emit(kind, group, cand, **kw): rows.append(dict(base, id=f"{e['exam']}#{n[0]}", kind=kind, group=group, candidate=cand, **kw)); n[0] += 1
        emit('identical', 'identical', t, harmless_type=None, category=None, field=None, severity=0, magnitude=None)
        for g, ty, c in harmless_for(t): emit('harmless', g, c, harmless_type=ty, category=None, field=None, severity=0, magnitude=None)
        pj = PJ.get(t); stats['paraphrases_generated'] += bool(pj)
        if pj:
            ok_diff = pj['differs']; ok_f = pj['facts_preserved']; ok_m = pj['same_meaning']; stats['para_identical_to_original'] += not ok_diff; stats['para_failed_fact_preservation'] += ok_diff and not ok_f; stats['para_failed_meaning_judge'] += ok_diff and ok_f and not ok_m
            if ok_diff and ok_f and ok_m: emit('harmless', 'paraphrase_llm', pj['para'], harmless_type='paraphrase', category=None, field=None, severity=0, magnitude=None); stats['para_kept'] += 1
        for ty, cat, sev, mag, c in errors_for(t): emit('error', 'error', c, harmless_type=None, category=cat, field=ty, severity=sev, magnitude=mag)
    return rows, stats

if __name__ == '__main__' and sys.argv[1] == 'build':
    rows, stats = build(); open(os.path.join(D, 'bench_his.jsonl'), 'w').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    ec = collections.Counter(r['field'] for r in rows if r['kind'] == 'error'); hc = collections.Counter(r['group'] for r in rows if r['kind'] == 'harmless')
    print(len(rows), 'rows;', dict(stats)); print('error types', dict(ec)); print('harmless groups', dict(hc))
