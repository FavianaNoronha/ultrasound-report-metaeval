"""Extractor v2 (new file; schema.py stays frozen as v1). Same prompt, so cached model replies are reused; v2 changes only the post-processing:
  1. numbers are re-read from the model's own QUOTE (deterministic): the model once returned 106 for "10.6 mm" (dropped decimal). If the quote contains a number with a unit
     (mm / cm / %), that reading replaces the model's value; cm -> mm; size_mm rounded to the nearest mm (hc_mm to 0.1 mm), as in v1.
  2. a value that is an option list copied from the prompt ("solid|cystic", "yes|no") or contains '|' is dropped (the field is left unstated), counted in the second return value.
  3. lesion = true / false (JSON booleans) map to present / absent.
Returns (facts, n_unquoted_dropped, n_option_lists_dropped, n_numeric_overrides)."""
import re
from . import schema

NUM = re.compile(r'(\d+(?:[.,]\d+)?)\s*(mm|cm|%)', re.I)

def number_from_quote(quote, field):
    """first number+unit in the quote -> value in the field's unit, or None"""
    for m in NUM.finditer(quote or ''):
        x = float(m[1].replace(',', '.')); u = m[2].lower()
        if field in ('size_mm', 'hc_mm') and u in ('mm', 'cm'): return x * (10 if u == 'cm' else 1)
        if field == 'size_pct' and u == '%': return x
    return None

def _quote_ok(q, rl, mode):
    """exact: the quote is a substring of the report (default, the frozen rule). tokens80: at least 80% of the quote's words occur in the report, in order-free fashion (for extractors that paraphrase or shorten quotes)"""
    qn = re.sub(r'\s+', ' ', str(q).lower())
    if qn in rl: return True
    if mode != 'tokens80': return False
    toks = re.findall(r'[a-z0-9.%]+', qn); words = set(re.findall(r'[a-z0-9.%]+', rl))
    return bool(toks) and sum(t in words for t in toks) / len(toks) >= 0.8

def extract_llm_v2(cli, report, organ, prompt=None, quote_match='exact'):
    fields = '\n'.join(f'- {k}: {v}' for k, v in schema.LLM_FIELDS[organ].items())
    t = cli.ask((prompt or schema.LLM_PROMPT).format(fields=fields, report=report), valid=lambda x: schema._parse_llm(x, organ) is not None)
    js = schema._parse_llm(t, organ)
    if js is None: return None, 0, 0, 0
    f, bad, opts, over = {}, 0, 0, 0; rl = re.sub(r'\s+', ' ', report.lower())
    for k in schema.LLM_FIELDS[organ]:
        d = js.get(k) or {}; v, q = d.get('value'), d.get('quote')
        if v in (None, '', 'null') or q in (None, ''): continue
        if not _quote_ok(q, rl, quote_match): bad += 1; continue
        if k == 'lesion' and isinstance(v, bool): v = 'present' if v else 'absent'
        if isinstance(v, str) and ('|' in v): opts += 1; continue
        if not isinstance(v, (int, float)): v = str(v).strip().lower()
        if k in ('size_mm', 'size_pct', 'hc_mm', 'count'):
            n = number_from_quote(q, k) if k != 'count' else None
            try: val = float(v)
            except Exception:
                if n is None: continue
                val = n
            if n is not None and abs(n - val) > 1e-9: over += 1; val = n
            v = int(round(val)) if k != 'hc_mm' else round(val, 1)
        if k == 'lesion' and v not in ('present', 'absent'): continue
        if k == 'pos' and isinstance(v, str): v = v.replace(' ', '-')
        if k == 'birads' and isinstance(v, str): v = re.sub(r'^bi-?rads\s*', '', v)
        f[k] = schema._norm_llm(k, v, organ)
    if 'lesion' not in f: f['lesion'] = 'present' if any(schema.FIELD_ENTITY[k] == 'lesion' for k in f) else 'absent'
    return f, bad, opts, over
