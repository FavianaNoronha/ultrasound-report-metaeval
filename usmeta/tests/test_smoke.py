import random, numpy as np, pandas as pd
from usmeta import templates as T, graders as G, meta as M, extract as X

def fake_breast():
    rows = []
    for i in range(30):
        rows.append(dict(CaseID=i, Image_filename=f'c{i}.png', Shape=random.choice(['irregular','oval','round']),
            Margin=random.choice(['circumscribed','not circumscribed - indistinct','not circumscribed - spiculated']),
            Echogenicity=random.choice(['hypoechoic','heterogeneous','anechoic']), Posterior_features=random.choice(['no','shadowing','enhancement']),
            Calcifications=random.choice(['no','in a mass']), Halo=random.choice(['yes','no']), BIRADS=random.choice(['2','3','4a','4b','4c','5']),
            Classification=random.choice(['benign','malignant'])))
    return pd.DataFrame(rows)

def fake_thy():
    return [dict(ds='T', split='x', file=f'{i}.jpg', path=random.choice(['benign','malignant']), count=random.choice([1,2,3]),
                 loc=random.choice(['upper-left','middle-central','lower-right']), ratio=random.random()) for i in range(40)]

def fake_fetal():
    return [dict(file=f'{i}.png', px=0.1+random.random()*0.05, hc=50+random.random()*250) for i in range(40)]

def test_extractors_roundtrip():
    random.seed(1)
    items = T.build_breast(fake_breast()) + T.build_thyroid(fake_thy()) + T.build_fetal(fake_fetal())
    # every harmless rewording must extract the same facts as the reference
    bad = [i for i in items if i['kind'] in ('harmless', 'identical') and
           X.EXTRACT[i['organ']](i['reference']) != X.EXTRACT[i['organ']](i['candidate'])]
    assert not bad, bad[:2]
    # every planted error must change at least one extracted fact
    miss = [i for i in items if i['kind'] == 'error' and
            X.EXTRACT[i['organ']](i['reference']) == X.EXTRACT[i['organ']](i['candidate'])]
    assert not miss, miss[:2]

def test_grading_and_meta():
    random.seed(2)
    items = T.build_breast(fake_breast()) + T.build_thyroid(fake_thy()) + T.build_fetal(fake_fetal())
    sc = G.grade(items, ['bleu', 'rougeL', 'chrf', 'fact_checker', 'evidence_check', 'judge_mock'], progress=False)
    df = M.to_frame(items, sc); s = M.summarize(df, list(sc))
    assert s['all']['fact_checker']['discrimination']['auroc'] > 0.95
    assert s['all']['judge_mock']['discrimination']['auroc'] > 0.95
    assert s['all']['bleu']['discrimination']['auroc'] < 0.5          # the headline finding
    assert abs(s['all']['fact_checker']['robustness']['identical_mean'] - 1) < 1e-9


def test_busbra_tn5000_style():
    import random
    random.seed(3)
    df = pd.DataFrame([dict(ID=f'b{i}', Side=random.choice(['left', 'right']), BIRADS=random.choice([2, 3, 4, 5]),
                            Pathology=(p := random.choice(['benign', 'malignant'])),
                            Histology=random.choice(['fibroadenoma', 'cyst'] if p == 'benign' else ['invasive ductal carcinoma', 'papillary carcinoma']))
                       for i in range(40)])
    items = T.build_busbra(df)
    f = lambda i: X.EXTRACT[i['ftype']]
    assert not [i for i in items if i['kind'] != 'error' and f(i)(i['reference']) != f(i)(i['candidate'])]
    assert not [i for i in items if i['kind'] == 'error' and f(i)(i['reference']) == f(i)(i['candidate'])]
