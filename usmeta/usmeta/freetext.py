"""LLM extractor: pulls the extract.py fields out of FREE-TEXT reports. null = the report does not say.
Backend is any object with .ask(prompt, valid) (ClaudeCLI or LocalLLM). Must be validated against the rule-based
extractor on templated reports before use (see tests / run check_extractor)."""
import json, re
from . import extract

FIELD_HELP = {
 'breast': dict(path='benign|malignant', birads='BI-RADS category as written, e.g. 2, 3, 4a, 4b, 4c, 5', margin='margin description as written',
                calc='"no" if no calcifications, else "yes:<type>"', shape='mass shape (oval, round, irregular)',
                echo='echogenicity (anechoic, hypoechoic, hyperechoic, isoechoic, heterogeneous, complex cystic/solid)',
                post='shadowing|enhancement|combined|no', halo='yes|no'),
 'busbra': dict(path='benign|malignant', birads='BI-RADS category', side='left|right', hist='histological type'),
 'thyroid': dict(path='benign|malignant', count='a single nodule|two nodules|three or more nodules',
                 loc='location such as "right-lobe"', size='small|medium|large'),
 'fetal': dict(hc='head circumference in millimetres (number)'),
}
PROMPT = """Extract facts from this ultrasound report. Reply with JSON only, with exactly these keys:
{keys}
Use null for any key the report does not state. Do not guess or infer beyond the text.

REPORT:
{report}
"""

def _parse(t, organ):
    m = re.search(r'\{.*\}', t or '', re.S)
    try: js = json.loads(m.group(0))
    except Exception: return None
    return js if isinstance(js, dict) and set(FIELD_HELP[organ]) <= set(js) else None

def extract_llm(cli, report, organ):
    keys = '\n'.join(f'  "{k}": {v}' for k, v in FIELD_HELP[organ].items())
    t = cli.ask(PROMPT.replace('{keys}', keys).replace('{report}', report), valid=lambda x: _parse(x, organ) is not None)
    js = _parse(t, organ)
    if js is None: return None
    out = {k: (None if js[k] in (None, 'null', '') else js[k]) for k in FIELD_HELP[organ]}
    if organ == 'fetal' and out['hc'] is not None:
        try: out['hc'] = float(out['hc'])
        except Exception: out['hc'] = None
    if isinstance(out.get('path'), str): out['path'] = out['path'].lower()
    return out

def agreement(cli, items):
    """share of (item, field) pairs where LLM extraction == rule-based extraction on templated text"""
    hit = tot = 0
    for i in items:
        o = i.get('ftype', i['organ']); a = extract.EXTRACT[o](i['candidate']); b = extract_llm(cli, i['candidate'], o)
        for k in FIELD_HELP[o]:
            tot += 1; x, y = a.get(k), (b or {}).get(k)
            hit += (str(x).lower() == str(y).lower()) if x is not None else (y is None)
    return hit / tot
