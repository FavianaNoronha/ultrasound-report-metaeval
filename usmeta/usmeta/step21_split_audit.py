"""Step 21f: split-leakage audit (no model calls). NEW file. For every dataset: images per split, near-duplicate clusters (dHash distance <= 4 bits, within a dataset; also <= 8 as a looser check)
that span more than one of dev / val / test, and patient / exam groups that span splits. Reads splits.jsonl (no test labels are used; counts only) and duplicates.jsonl (Step 10a).
    python3 -m usmeta.step21_split_audit OUT_DIR"""
import json, sys, os, collections

def main(out):
    sp = {}
    for l in open('splits.jsonl'):
        r = json.loads(l); sp[r['case_id']] = r
    D = [json.loads(l) for l in open('duplicates.jsonl')]; res = {}
    def clusters(maxd):
        par = {}
        def find(x):
            par.setdefault(x, x)
            while par[x] != x: par[x] = par[par[x]]; x = par[x]
            return x
        for r in D:
            if r['dist'] <= maxd and r['ds_a'] == r['ds_b'] and not r['ds_a'].startswith('Diverse') and r['a'] in sp and r['b'] in sp: par[find(r['a'])] = find(r['b'])
        cl = collections.defaultdict(set)
        for x in list(par): cl[find(x)].add(x)
        return list(cl.values())
    C4, C8 = clusters(4), clusters(8)
    cross = [r for r in D if r['dist'] <= 4 and r['ds_a'] != r['ds_b'] and not r['ds_a'].startswith('Diverse') and not r['ds_b'].startswith('Diverse')]
    by_ds = collections.defaultdict(list)
    for c in sp.values(): by_ds[c['dataset']].append(c)
    rows = []
    for ds, cs in sorted(by_ds.items()):
        n = collections.Counter(c['split'] for c in cs); g = collections.defaultdict(set)
        for c in cs: g[c['group_id']].add(c['split'])
        span_groups = sum(len(v) > 1 for v in g.values())
        row = dict(dataset=ds, images=len(cs), dev=n['dev'], val=n['val'], test=n['test'], groups=len(g), groups_spanning_splits=span_groups)
        for tag, CL in (('le4', C4), ('le8', C8)):
            mine = [c for c in CL if next(iter(c)) in sp and sp[next(iter(c))]['dataset'] == ds]
            row[f'clusters_{tag}'] = len(mine); row[f'clusters_{tag}_images'] = sum(len(c) for c in mine); row[f'clusters_{tag}_spanning'] = sum(len({sp[x]['split'] for x in c}) > 1 for c in mine)
        rows.append(row)
    res = dict(rows=rows, cross_dataset_pairs_le4=len(cross), total_spanning_le4=sum(r['clusters_le4_spanning'] for r in rows), total_spanning_le8=sum(r['clusters_le8_spanning'] for r in rows), total_groups_spanning=sum(r['groups_spanning_splits'] for r in rows))
    json.dump(res, open(os.path.join(out, 'split_audit.json'), 'w'), indent=1)
    md = ['| dataset | images | dev | val | test | groups | groups spanning splits | near-dup clusters (≤ 4 bits) | clusters spanning splits | clusters (≤ 8 bits) | clusters spanning splits |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows: md.append(f"| {r['dataset']} | {r['images']} | {r['dev']} | {r['val']} | {r['test']} | {r['groups']} | {r['groups_spanning_splits']} | {r['clusters_le4']} ({r['clusters_le4_images']} images) | {r['clusters_le4_spanning']} | {r['clusters_le8']} ({r['clusters_le8_images']} images) | {r['clusters_le8_spanning']} |")
    open(os.path.join(out, 'table.md'), 'w').write('\n'.join(md)); print('\n'.join(md)); print({k: v for k, v in res.items() if k != 'rows'})
    return res

if __name__ == '__main__': main(sys.argv[1])
