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
