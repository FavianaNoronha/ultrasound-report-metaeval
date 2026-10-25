"""HiSBreast Step 2a: translate the Vietnamese clinician conclusions to English with the local Gemma-2-9B (MLX). Unique texts only (325 of 427 exams).
Outputs stay LOCAL (usmeta/local_data/hisbreast/, git-ignored): licence blank, no de-identification statement."""
import json, os, random, sys, time, re, html
from . import hisbreast, graders
def tidy(vi):
    """HTML entities (&nbsp;) and bullet dashes removed; one line per original line is kept as separate sentences joined with ' | '"""
    t = html.unescape(vi).replace('\xa0', ' ')
    parts = [re.sub(r'^[-–•\s]+', '', re.sub(r'\s+', ' ', x)).strip() for x in re.split(r'\s+-\s+|\n', t)]
    return ' | '.join(x for x in parts if x)

PROMPT = """Translate this Vietnamese breast-ultrasound radiologist conclusion into English.
Rules: translate faithfully and completely (every part separated by " | " must appear in the translation, in the same order, separated by " | "); keep BI-RADS terms and categories exactly (for example BI-RADS 4A); keep numbers and units; do not add, remove or interpret anything; do not explain.
Terminology: tuyến vú / vú = breast; phải = right; trái = left; hai bên = both sides; bướu / khối = mass; nang = cyst; hạch nách = axillary lymph node; theo dõi = follow up; chưa ghi nhận bất thường = no abnormality recorded; viêm = inflammation; áp xe = abscess; sau phẫu thuật / mổ = post-surgery; nghi ngờ = suspicious; sinh thiết = biopsy; ung thư = cancer; lành tính = benign; ác tính = malignant; kích thước = size.
Reply with the English translation only, on one line.

VIETNAMESE:
{vi}
"""
if __name__ == '__main__':
    exams = [json.loads(l) for l in open(os.path.join(hisbreast.OUT, 'exams.jsonl'))]; uniq = sorted({tidy(e['vi']) for e in exams})
    cli = graders.LocalLLM('mlx-community/gemma-2-9b-it-4bit', cache_dir=os.path.join(hisbreast.OUT, '.llm_cache'), max_tokens=160); out = os.path.join(hisbreast.OUT, 'translations.jsonl')
    done = {json.loads(l)['vi'] for l in open(out)} if os.path.exists(out) else set(); t0 = time.time(); todo = [u for u in uniq if u not in done]; print(len(uniq), 'unique;', len(todo), 'to translate', flush=True)
    for i, vi in enumerate(todo):
        en = ' '.join((cli.ask(PROMPT.format(vi=vi)) or '').split())
        open(out, 'a').write(json.dumps(dict(vi=vi, en=en), ensure_ascii=False) + '\n')
        if i % 25 == 0: print(i, len(todo), round(time.time() - t0), 's', flush=True)
    print('done', round(time.time() - t0), 's', flush=True)
