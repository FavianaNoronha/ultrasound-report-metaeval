"""Step 10b: grouped, locked dev / val / test splits (40 / 20 / 40) + the guarded loader.
Group id per case = patient / exam / case id when the dataset has one, else the image id (patient overlap then possible: recorded in group_source);
near-duplicate clusters inside a dataset (dHash <= 4 bits, Step 10a) are merged into ONE group so a cluster is never split.
Assignment is at GROUP level, stratified by dataset and class, seed 0.   Use usmeta.splits.load(split): every access to 'test' is logged."""
import os, sys, json, hashlib, random, subprocess, datetime, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); RES = os.path.join(ROOT, 'results', 'partA')
SPLITS = os.path.join(ROOT, 'splits.jsonl'); LOG = os.path.join(RES, 'test_access.log')
TARGET = dict(dev=0.4, val=0.2, test=0.4)
NO_GROUP = {'BUSI', 'UDIAT', 'TN3K', 'TN5000', 'HC18'}      # no patient / exam id in the records

def _git():
    try: return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True, cwd=ROOT).strip()
    except Exception: return None

def build(seed=0, duplicates=os.path.join(ROOT, 'duplicates.jsonl')):
    from . import unified
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for l in open(duplicates):
        r = json.loads(l)
        if r['dist'] <= 4 and r['ds_a'] == r['ds_b'] and not r['ds_a'].startswith('Diverse'): par[find(r['a'])] = find(r['b'])
    recs = []
    for ds in ['BrEaST', 'BUSBRA', 'BUSI', 'UDIAT', 'BUSUCLM', 'TN3K', 'TN5000', 'DDTI', 'HC18', 'FetalHead']:
        recs += unified.load(ds)
    # base group
    base = {}
    for c in recs:
        base[c['case_id']] = (f"{c['dataset']}:{c['group_id']}" if c['group_id'] else c['case_id'], 'record' if c['group_id'] else 'image id (stand-in)')
    # merge groups of near-duplicate cases
    g = {}
    def gfind(x):
        g.setdefault(x, x)
        while g[x] != x: g[x] = g[g[x]]; x = g[x]
        return x
    for c in recs: gfind(base[c['case_id']][0])
    members = collections.defaultdict(list)
    for x in list(par): members[find(x)].append(x)
    merged = set()
    for m in members.values():
        for a in m[1:]:
            if a in base and m[0] in base: g[gfind(base[a][0])] = gfind(base[m[0]][0]); merged.add(a); merged.add(m[0])
    out = []; by = collections.defaultdict(lambda: collections.defaultdict(list))
    for c in recs:
        gid = gfind(base[c['case_id']][0]); src = base[c['case_id']][1] + (' + near-duplicate cluster' if c['case_id'] in merged else '')
        lab = c['labels'].get('cls') or c['labels'].get('cls_raw') or c['labels'].get('plane') or 'none'
        by[c['dataset']][gid].append((c['case_id'], src, lab))
    rng = random.Random(seed)
    for ds, groups in by.items():
        strata = collections.defaultdict(list)
        for gid, cs in groups.items(): strata[collections.Counter(l for _, _, l in cs).most_common(1)[0][0]].append(gid)
        for lab, gids in sorted(strata.items()):
            gids.sort(); rng.shuffle(gids); total = sum(len(groups[x]) for x in gids); cum = 0
            for gid in gids:
                frac = (cum + len(groups[gid]) / 2) / total; split = 'dev' if frac < TARGET['dev'] else 'val' if frac < TARGET['dev'] + TARGET['val'] else 'test'; cum += len(groups[gid])
                for cid, src, l in groups[gid]: out.append(dict(case_id=cid, dataset=ds, group_id=gid, group_source=src, stratum=lab, split=split))
    out.sort(key=lambda r: (r['dataset'], r['case_id'])); return out

def write(rows):
    open(SPLITS, 'w').write(''.join(json.dumps(r) + '\n' for r in rows))

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def manifest(extra=()):
    files = {'splits.jsonl': SPLITS, 'bench_v2d.jsonl': os.path.join(ROOT, 'bench_v2d.jsonl'), 'true_reports_v2d.jsonl': os.path.join(ROOT, 'true_reports_v2d.jsonl')}
    files.update({os.path.basename(p): p for p in extra})
    return dict(sha256={k: sha(p) for k, p in files.items()}, git_commit=_git(), written=datetime.datetime.now().isoformat(timespec='seconds'))

def load(split=None, script=None):
    """rows of splits.jsonl for one split ('dev' | 'val' | 'test') or all. Access to 'test' (or to all) is logged in results/partA/test_access.log."""
    rows = [json.loads(l) for l in open(SPLITS)]
    if split in (None, 'test'):
        os.makedirs(RES, exist_ok=True)
        open(LOG, 'a').write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{script or os.path.basename(sys.argv[0]) or 'interactive'}\tgit={_git()}\tsplit={split or 'ALL'}\trows={sum(r['split'] == 'test' for r in rows) if split == 'test' else len(rows)}\n")
    return rows if split is None else [r for r in rows if r['split'] == split]

def case_ids(split, script=None): return {r['case_id'] for r in load(split, script)}

if __name__ == '__main__':
    rows = build(); write(rows); c = collections.Counter((r['dataset'], r['split']) for r in rows); print(len(rows), 'cases'); print(dict(c))
