"""CLI.  python -m usmeta.run build|grade|report|all   (see README)"""
import argparse, json, csv, os, random
import pandas as pd
from . import templates as T, graders as G, meta as M, records as R

def load_hc18(path):
    return [dict(file=r['filename'], px=float(r['pixel size(mm)']), hc=float(r['head circumference (mm)'])) for r in csv.DictReader(open(path))]

def cmd_build(a):
    items = []
    if a.breast: items += T.build_breast(pd.read_excel(a.breast))
    if a.thyroid_records: items += T.build_thyroid(json.load(open(a.thyroid_records)), n=a.n)
    if a.ultrag_thyroid_jsonl: items += T.build_thyroid(R.ultrag_thyroid_records(a.ultrag_thyroid_jsonl), n=a.n)
    if a.busbra: items += T.build_busbra(pd.read_csv(a.busbra), n=a.n)
    if a.tn5000: items += T.build_thyroid(R.tn5000_records(a.tn5000), n=a.n)
    if a.hc18: items += T.build_fetal(load_hc18(a.hc18), n=a.n)
    with open(a.out, 'w') as f:
        for i in items: f.write(json.dumps(i) + '\n')
    print('wrote', len(items), 'items to', a.out)

def read(p): return [json.loads(l) for l in open(p)]

def cmd_grade(a):
    items = read(a.bench); sc = G.grade(items, a.graders.split(','))
    json.dump(sc, open(a.out, 'w'))
    print('scores saved to', a.out)

def cmd_report(a):
    items = read(a.bench); sc = json.load(open(a.scores)); df = M.to_frame(items, sc); gs = list(sc)
    summ = M.summarize(df, gs)
    json.dump(summ, open(a.out + '.json', 'w'), indent=1); open(a.out + '.md', 'w').write(M.to_markdown(summ, gs))
    print(M.to_markdown(summ, gs)); print('saved', a.out + '.json /.md')

def main():
    p = argparse.ArgumentParser(); sp = p.add_subparsers(dest='cmd', required=True)
    b = sp.add_parser('build'); b.add_argument('--breast'); b.add_argument('--thyroid-records'); b.add_argument('--ultrag-thyroid-jsonl'); b.add_argument('--hc18'); b.add_argument('--busbra'); b.add_argument('--tn5000')
    b.add_argument('--n', type=int, default=500, help='max cases per organ (thyroid, fetal)'); b.add_argument('--out', default='bench.jsonl'); b.set_defaults(f=cmd_build)
    g = sp.add_parser('grade'); g.add_argument('--bench', default='bench.jsonl'); g.add_argument('--graders', default='bleu,rougeL,chrf,fact_checker,evidence_check')
    g.add_argument('--out', default='scores.json'); g.set_defaults(f=cmd_grade)
    r = sp.add_parser('report'); r.add_argument('--bench', default='bench.jsonl'); r.add_argument('--scores', default='scores.json'); r.add_argument('--out', default='results'); r.set_defaults(f=cmd_report)
    a = p.parse_args(); a.f(a)

if __name__ == '__main__': main()
