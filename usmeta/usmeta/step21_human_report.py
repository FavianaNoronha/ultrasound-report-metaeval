"""Step 21d report: writes results.md in results/partA/step21d_human_sheet/ from human_results.json (made by step21_human_score score). NEW file.
    python3 -m usmeta.step21_human_report"""
import json, os, csv
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'partA', 'step21d_human_sheet')
R = json.load(open(os.path.join(D, 'human_results.json')))
NAMES = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('finding_f1', 'finding_f1 (upper bound)'), ('sentence_f1', 'judge sentence_f1'), ('judge_score', 'judge_score')]
KINDS = [('human', 'human rewording'), ('template_small', 'template small'), ('template_matched', 'template matched'), ('template_large', 'template large')]
f = lambda d: '—' if not d or not d['auroc'] else f"{d['auroc'][0]:.2f} ({d['auroc'][1]:.2f}–{d['auroc'][2]:.2f})"
flag = list(csv.DictReader(open(os.path.join(D, 'flagged.csv')))); sheet = list(csv.DictReader(open(os.path.join(D, 'sheet.csv'))))
L = ['# Step 21d — Human rewordings (scored)', '',
     f'30 test references were reworded by hand (sheet filled by the project team; file `reference to human.xlsx` uploaded to the repository, copied into `sheet.csv`; the blank sheet is kept as `sheet_blank.csv`). The rule-based fact extractor flagged 10 rewordings as changing a fact; I read each one against its reference: 9 (H02-H06, H08-H11) preserve every fact (the extractor only misreads free wording such as "wider in shape than in height") and were marked `OK` in the note column; **H01 was left flagged and excluded** (the reword drops "irregular" and changes "Combined posterior features" to "Associated posterior features"). 29 rewordings are scored; none is identical to its reference.', '',
     '**Too small to compare:** 29 items overall (9 breast, 10 thyroid, 10 fetal head) is under 30 groups in every cell; the numbers below are point estimates with group-bootstrap intervals and must not be used for a significance claim. Planted errors are the test-split errors of the same reference (bench_test_v2d); judge = Gemma-2-9B prompt_v2 (greedy), run on the 29 rewordings only; the template columns are the project\'s own rewordings of the SAME references, scored in the same run, for a like-for-like comparison.', '',
     'AUROC = share of error x rewording pairs in which the error scores lower (ties 0.5); 1.00 = every error scores below every rewording of that type.', '']
for org, title in (('ALL', 'All three organs (n = 29 items)'), ('breast', 'Breast (n = 9)'), ('thyroid', 'Thyroid (n = 10)'), ('fetal head', 'Fetal head (n = 10)')):
    L += [f'## {title}', '', '| scorer | ' + ' | '.join(k[1] for k in KINDS) + ' |', '|---|' + '---|' * len(KINDS)]
    for n, nm in NAMES: L.append(f'| {nm} | ' + ' | '.join(f(R.get(f'{n}|{k[0]}|{org}')) + ' †' for k in KINDS) + ' |')
    L.append('')
L += ['† too small to compare (fewer than 30 groups).', '', '## Reading', '']
g = lambda n, k: R[f'{n}|{k}|ALL']['auroc'][0]
L += [f"- Word-overlap scorers rank the human rewordings like the project's own large rewrites, not like small ones: AUROC against human rewordings is {g('bleu', 'human'):.2f} (BLEU), {g('rougeL', 'human'):.2f} (ROUGE-L), {g('chrf', 'human'):.2f} (chrF), {g('bertscore[roberta-large]', 'human'):.2f} (BERTScore), {g('ratescore', 'human'):.2f} (RaTEScore) over all organs, i.e. errors score HIGHER than a correct human rewording most of the time.",
      f"- The judge keeps separating errors from human rewordings: judge_score {g('judge_score', 'human'):.2f}, sentence_f1 {g('sentence_f1', 'human'):.2f}; finding_f1 {g('finding_f1', 'human'):.2f} (upper bound: it reads the same template vocabulary, and a few free rewordings lose facts to its extractor).",
      '- 29 items, one writer per sheet, 30 references only: this is a spot-check that the template rewordings are not unusually easy for the judge, not a replacement for a clinician-written set.', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(L)); print('\n'.join(L[:30]))
