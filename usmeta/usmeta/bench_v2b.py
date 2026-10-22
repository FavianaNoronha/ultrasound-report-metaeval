"""bench_v2b = bench_v2 with the harmless group split by size of edit (bench_v2 is not touched).
  harmless_small : edits INSIDE one style: synonyms, sentence reorder, unit rewrite (mm -> cm)
  harmless_large : style swap (reference is the 'standard' style; candidate is the terse or long-form style) -> whole text rewritten
  harmless_other : secondary groups (negation, hedge, padding), reported separately as before
`kind` stays 'harmless' for all three (the union) so old code still works; the new field `harmless_type` says which."""
import json, os, sys
TYPE = {'synonyms': 'small', 'reorder': 'small', 'unit_cm': 'small', 'style_terse': 'large', 'style_long': 'large'}

def convert(src='bench_v2.jsonl', dst='bench_v2b.jsonl'):
    rows = [json.loads(l) for l in open(src)]
    for r in rows: r['harmless_type'] = TYPE.get(r['group'], 'other') if r['kind'] == 'harmless' else None
    open(dst, 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); return rows

if __name__ == '__main__':
    import collections; rows = convert(); print(len(rows), collections.Counter(r['harmless_type'] for r in rows if r['kind'] == 'harmless'))

# ---------------------------------------------------------------- bench_v2c: + matched-edit-size harmless group (ONE-token synonym)
ONE = {'breast': [('mass', 'lesion'), ('margins', 'borders'), ('echo pattern', 'echogenicity'), ('Assessment:', 'Impression:'), ('is seen', 'is demonstrated'), ('approximately', 'about')],
       'thyroid': [('nodule', 'lesion'), ('Assessment:', 'Impression:'), ('is seen', 'is demonstrated'), ('about', 'approximately')],
       'fetal': [('Head circumference', 'Cranial circumference'), ('head', 'cranium')]}

def add_matched(src='bench_v2b.jsonl', dst='bench_v2c.jsonl'):
    """adds harmless_type='matched' rows (group 'synonym1'): the reference with ONE substitution, about the same share of tokens as a planted single-fact error"""
    rows = [json.loads(l) for l in open(src)]; base = {}
    for r in rows:
        if r['kind'] == 'identical': base[r['case_id']] = r
    out = list(rows)
    for cid, b in base.items():
        n = 0
        for a, c in ONE[b['organ']]:
            if a in b['reference']:
                cand = b['reference'].replace(a, c, 1)
                if cand != b['reference']:
                    r = {k: v for k, v in b.items() if k not in ('id', 'candidate')}
                    r.update(id=f'{cid}#m{n}', kind='harmless', group='synonym1', primary=False, harmless_type='matched', category=None, field=None,
                             magnitude=None, severity=0, candidate=cand); out.append(r); n += 1
    open(dst, 'w').write(''.join(json.dumps(r) + '\n' for r in out)); return out
