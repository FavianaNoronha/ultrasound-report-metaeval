"""Step 10c: write FROZEN.md = the exact versions (file SHA-256) of everything the headline numbers depend on."""
import hashlib, os, subprocess, datetime, json, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FILES = [
 ('templates', 'usmeta/templates_v2.py', 'true-report templates v2 (3 styles, provenance)'),
 ('schema + extractors', 'usmeta/schema.py', 'finding schema, rule extractor, local-LLM extractor, finding_f1'),
 ('benchmark builders', 'usmeta/bench_v2.py', 'planted errors + severity rules (provisional)'),
 ('benchmark builders', 'usmeta/bench_v2b.py', 'harmless split + matched one-word synonym group'),
 ('benchmark builders', 'usmeta/bench_loc.py', 'box / location extension'),
 ('scorers', 'usmeta/graders.py', 'bleu, rougeL, chrf, bertscore (roberta-large), ratescore (use_gpu=False -> mps), local judge classes'),
 ('scorers', 'usmeta/layer0.py', 'AUROC / bootstrap machinery'), ('scorers', 'usmeta/layer0b.py', 'analysis with small / matched / large harmless'),
 ('scorers', 'usmeta/layer1.py', 'finding_f1 scoring'), ('scorers', 'usmeta/judge2.py', 'sentence_check; PROMPT_V1 and PROMPT_V2 (stricter) live here'),
 ('scorers', 'usmeta/judge2_report.py', 'judge analysis'), ('scorers', 'usmeta/location.py', 'IoU, Dice, Hungarian, mask loaders'), ('scorers', 'usmeta/layer3.py', 'location_check, grounded_check, mask_verified_facts, semacc, box_support'),
 ('splits', 'usmeta/splits.py', 'grouped dev/val/test + guarded loader'), ('data', 'splits.jsonl', 'case -> group -> split'), ('data', 'bench_v2d.jsonl', 'benchmark (dev-era sample, 150 cases per dataset)'),
 ('data', 'true_reports_v2d.jsonl', 'true reports'), ('data', 'bench_loc.jsonl', 'location benchmark'), ('data', 'duplicates.jsonl', 'near-duplicate pairs'),
]
def sha(p): return hashlib.sha256(open(os.path.join(ROOT, p), 'rb').read()).hexdigest()
def prompt_hashes():
    sys.path.insert(0, ROOT); from usmeta import judge2
    return {'prompt_v1 (first Step 7 run)': hashlib.sha256(judge2.PROMPT_V1.encode()).hexdigest(), 'prompt_v2 (stricter, identical copies must get 1.0)': hashlib.sha256(judge2.PROMPT_V2.encode()).hexdigest()}
def write(path='FROZEN.md'):
    git = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True, cwd=ROOT).strip()
    L = ['# FROZEN (freeze-v1)', '', f'Frozen {datetime.date.today()} at git {git} (the tag `freeze-v1` is placed on the commit that adds this file). Anything below that changes after this point must be a NEW version (v2, ...) with a note in `CHANGELOG.md` saying what changed and why; the old version and its results are kept. Tuning of any kind uses dev and val only; final numbers come from the locked test split via `usmeta.splits.load("test")`.', '',
         '| group | file | SHA-256 | what |', '|---|---|---|---|']
    L += [f'| {g} | `{p}` | `{sha(p)[:16]}...` | {w} |' for g, p, w in FILES]
    L += ['', '## Judge prompts (Gemma-2-9B-it 4-bit via MLX, greedy, max 500 new tokens)', ''] + [f'- **{k}**: SHA-256 `{v[:16]}...`' for k, v in prompt_hashes().items()]
    L += ['', '## Settings that are part of the freeze',
          '- Layer 0: sacrebleu defaults (BLEU effective order, chrF), own ROUGE-L, BERTScore roberta-large (layer default, MPS), RaTEScore 0.6.0 (Angelakeke/RaTE-NER-Deberta, FremyCompany/BioLORD-2023-C, MPS).',
          '- Layer 1: finding_f1 credit rules (size: linear to 0 at 50% relative error; head circumference: linear to 0 at 20 mm; categories exact). LLM extractor: gemma-2-9b-it-4bit, quoted evidence required, normalisation map in `schema._norm_llm`.',
          '- Layer 2: judge penalties critical 0.6 / major 0.3 / minor 0.1 (`graders.PENALTY`); sentence_check precision/recall from true/false lists.',
          '- Layer 3: location_check = Hungarian best-match box IoU; grounded_check = finding_f1 x location_check; mask_verified credit >= 0.5 counts as backed; support rule >= 50% of the box inside the true region.',
          '- Bootstrap: 1,000 resamples, seed 0; to be resampled at GROUP level on the test split (Step 10d).',
          '- **Threshold rule (for detection / robustness and flag rates, Step 8b):** the threshold of a scorer is the score cut-off that flags 90% of planted errors on the VAL split (flag = score below the cut-off); it is then applied unchanged to test. Calibration (if any) is fitted on val.',
          '', 'Rebuild this file with `python3 -m usmeta.frozen`.']
    open(os.path.join(ROOT, path), 'w').write('\n'.join(L) + '\n')
if __name__ == '__main__': write()
