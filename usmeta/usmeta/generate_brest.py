"""Qwen2.5-VL-3B reports for BrEaST (50 scans + 5 mirrored copies), same prompt and settings as usmeta/generate.py (frozen); BrEaST scans were not on the machine for Step 3.
Case ids are the unified ids ('BrEaST:<n>'). Output: reports_qwen_brest.jsonl, reports_qwen_brest_flip.jsonl. Possible training exposure (public archive): unverifiable."""
import json, os, random, time, sys
from PIL import Image
from . import generate, unified, qwen_real as Q

def run(n=50, nflip=5, seed=0):
    recs = [c for c in unified.load('BrEaST') if c['has']['image']]; rng = random.Random(seed); rng.shuffle(recs); sel = recs[:n]; w = generate.Writer('qwen')
    for fn, flip, items in (('reports_qwen_brest.jsonl', False, sel), ('reports_qwen_brest_flip.jsonl', True, sel[:nflip])):
        done = {json.loads(l)['case_id'] for l in open(fn)} if os.path.exists(fn) else set()
        for c in items:
            if c['case_id'] in done: continue
            t = time.time(); img = Image.open(Q.img_path(c)).convert('RGB')
            if flip: img = img.transpose(Image.FLIP_LEFT_RIGHT)
            rep = w.report(img, 'breast'); open(fn, 'a').write(json.dumps(dict(case_id=c['case_id'], dataset='BrEaST', organ='breast', model=generate.MODELS['qwen'], flipped=flip, seconds=round(time.time() - t, 1), report=rep)) + '\n'); print(c['case_id'], round(time.time() - t, 1), 's', flush=True)

if __name__ == '__main__': run()
