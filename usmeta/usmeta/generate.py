"""Free-text report writers (vision-language models). One image at a time; appends to reports_<model>.jsonl after every
image so a run can be resumed. Same prompt for every model.
    python -m usmeta.generate --model qwen --per-dataset 10 --out reports_qwen.jsonl
"""
import argparse, json, os, random, time
from PIL import Image

DL = os.path.expanduser('~/Downloads')
IMG_DIRS = {'BUS-BRA': (DL + '/archive-5/BUSBRA/BUSBRA/Images', '.png'), 'TN5000': (DL + '/TN5000_forReview/JPEGImages', ''),
            'TN3K': (DL + '/archive-6/trainval-image', ''), 'HC18': (DL + '/archive-7/training_set', '')}
ORGAN_WORD = {'breast': 'breast', 'thyroid': 'thyroid', 'fetal': 'fetal head'}
PROMPT = ("You are a sonographer. Write a short report for this {organ} ultrasound image: list the main findings, "
          "a BI-RADS category if it is a breast image, and an overall impression.")
MODELS = {'qwen': 'Qwen/Qwen2.5-VL-3B-Instruct', 'medgemma': 'google/medgemma-4b-it'}

def image_path(item):
    d, ext = IMG_DIRS[item['dataset']]; p = os.path.join(d, item['image'])
    if not os.path.exists(p) and os.path.exists(p + ext): p += ext
    return p

class Writer:
    def __init__(self, key, device=None):
        import torch
        self.key, self.torch = key, torch
        self.device = device or ('mps' if torch.backends.mps.is_available() else 'cpu')
        from transformers import AutoProcessor
        mid = MODELS[key]; self.proc = AutoProcessor.from_pretrained(mid)
        if key == 'qwen':
            from transformers import Qwen2_5_VLForConditionalGeneration as M
        else:
            from transformers import AutoModelForImageTextToText as M
        self.model = M.from_pretrained(mid, torch_dtype=torch.bfloat16 if key == 'medgemma' else torch.float16).to(self.device).eval()
    def report(self, img, organ, max_new_tokens=220):
        msgs = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': PROMPT.format(organ=ORGAN_WORD[organ])}]}]
        text = self.proc.apply_chat_template(msgs, add_generation_prompt=True)
        inp = self.proc(text=[text], images=[img], return_tensors='pt').to(self.device)
        with self.torch.no_grad():
            out = self.model.generate(**inp, max_new_tokens=max_new_tokens, do_sample=False)
        return self.proc.batch_decode(out[:, inp['input_ids'].shape[1]:], skip_special_tokens=True)[0].strip()

def pick_cases(bench, per_dataset, seed=0):
    items = [json.loads(l) for l in open(bench)]; rng = random.Random(seed); cases = {}
    for i in items:
        if i['dataset'] in IMG_DIRS and i['kind'] == 'identical': cases.setdefault(i['dataset'], []).append(i)
    out = []
    for ds, v in cases.items():
        v = [x for x in v if os.path.exists(image_path(x))]; rng.shuffle(v); out += v[:per_dataset]
    return out

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--model', default='qwen'); ap.add_argument('--bench', default='bench_v1.jsonl')
    ap.add_argument('--per-dataset', type=int, default=50); ap.add_argument('--out'); ap.add_argument('--flip', action='store_true')
    a = ap.parse_args(); out = a.out or f'reports_{a.model}.jsonl'
    done = {json.loads(l)['case_id'] for l in open(out)} if os.path.exists(out) else set()
    todo = [c for c in pick_cases(a.bench, a.per_dataset) if c['case_id'] not in done]
    print(len(todo), 'to do'); w = Writer(a.model)
    for c in todo:
        t = time.time(); img = Image.open(image_path(c)).convert('RGB')
        if a.flip: img = img.transpose(Image.FLIP_LEFT_RIGHT)
        r = w.report(img, c['organ'])
        open(out, 'a').write(json.dumps(dict(case_id=c['case_id'], dataset=c['dataset'], organ=c['organ'], model=MODELS[a.model],
                                              flipped=a.flip, seconds=round(time.time() - t, 1), report=r)) + '\n')
        print(c['case_id'], round(time.time() - t, 1), 's', flush=True)
