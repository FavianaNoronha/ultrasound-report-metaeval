"""Helper: save a step's results in results/partA/stepN_<name>/ (data, results.md, run_info.json, run.log) + INDEX.md + summaries/."""
import json, os, platform, shutil, subprocess, sys, datetime
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'partA')

def _git(*a):
    try: return subprocess.check_output(['git', *a], text=True, cwd=ROOT if os.path.isdir(ROOT) else None).strip()
    except Exception: return None

def pkg_versions(names=('numpy', 'scipy', 'sacrebleu', 'torch', 'transformers', 'bert_score', 'RaTEScore', 'pytest')):
    out = {}
    for n in names:
        try:
            import importlib.metadata as m; out[n] = m.version(n.replace('_', '-') if n == 'bert_score' else n)
        except Exception: out[n] = None
    return out

def save_step(step, name, results_md, files=(), counts=None, seeds=None, models=None, command=None, log=None, headline=''):
    d = os.path.join(ROOT, f'{step}_{name}'); os.makedirs(d, exist_ok=False)   # never overwrite a previous step
    for f in files: shutil.copy(f, d)
    open(os.path.join(d, 'results.md'), 'w').write(results_md)
    if log is not None: open(os.path.join(d, 'run.log'), 'w').write(log)
    json.dump(dict(date=datetime.datetime.now().isoformat(timespec='seconds'), git_commit=_git('rev-parse', '--short', 'HEAD'),
                   dataset_record_counts=counts, seeds=seeds, packages=pkg_versions(), python=platform.python_version(),
                   models=models, command=command), open(os.path.join(d, 'run_info.json'), 'w'), indent=2)
    os.makedirs(os.path.join(ROOT, 'summaries'), exist_ok=True); import re as _re
    m = _re.search(r'_rerun\d+$', name); sname = f'{step}{m.group(0)}.md' if m else f'{step}.md'   # a re-run never overwrites the original summary
    shutil.copy(os.path.join(d, 'results.md'), os.path.join(ROOT, 'summaries', sname))
    idx = os.path.join(ROOT, 'INDEX.md')
    if not os.path.exists(idx): open(idx, 'w').write('# Part A results index\n\n| step | date | commit | folder | headline |\n|---|---|---|---|---|\n')
    open(idx, 'a').write(f"| {step} | {datetime.date.today()} | {_git('rev-parse', '--short', 'HEAD')} | [{step}_{name}]({step}_{name}/) | {headline} |\n")
    return d
