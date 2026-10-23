"""Step 10f: memorisation probe for a report-writing VLM (Qwen2.5-VL-3B here). A PROBE, not proof either way.
 (a) text-only: name a dataset file (no image) and ask for its label (pathology, or head circumference for HC18); compare with the truth against the majority-class / median baseline.
 (b) image: show the scan and ask which public dataset it comes from; log exact matches.
20 scans per dataset, seed 0, drawn from the DEV split only (no test access).
    python3 -m usmeta.memprobe qwen out.jsonl"""
import sys, json, random, os, time, collections
from PIL import Image
from . import generate, splits, unified

NAMES = {'BUS-BRA': ['BUS-BRA'], 'BUSI': ['BUSI', 'Breast Ultrasound Images'], 'BrEaST': ['BrEaST'], 'TN3K': ['TN3K'], 'TN5000': ['TN5000'], 'HC18': ['HC18', 'Head Circumference']}

def chat(w, text, img=None, max_new_tokens=24):
    content = ([{'type': 'image'}] if img is not None else []) + [{'type': 'text', 'text': text}]
    t = w.proc.apply_chat_template([{'role': 'user', 'content': content}], add_generation_prompt=True)
    inp = (w.proc(text=[t], images=[img], return_tensors='pt') if img is not None else w.proc(text=[t], return_tensors='pt')).to(w.device)
    with w.torch.no_grad(): out = w.model.generate(**inp, max_new_tokens=max_new_tokens, do_sample=False)
    return w.proc.batch_decode(out[:, inp['input_ids'].shape[1]:], skip_special_tokens=True)[0].strip()

def run(model='qwen', out='memprobe.jsonl', n=20):
    dev = {r['case_id'] for r in splits.load('dev', script='usmeta.memprobe')}; w = generate.Writer(model); rng = random.Random(0); rows = []
    for ds, key in (('BUSBRA', 'BUS-BRA'), ('BUSI', 'BUSI'), ('BrEaST', 'BrEaST'), ('TN3K', 'TN3K'), ('TN5000', 'TN5000'), ('HC18', 'HC18')):
        recs = [c for c in unified.load(ds) if c['case_id'] in dev and c['has']['image']]; rng.shuffle(recs)
        for c in recs[:n]:
            img = Image.open(c['image'].replace(c['image'].split('/mnt/Downloads')[0] + '/mnt/Downloads', os.path.expanduser('~/Downloads'))).convert('RGB') if '/mnt/Downloads' in c['image'] else Image.open(c['image']).convert('RGB')
            fname = os.path.basename(c['image'])
            if key == 'HC18': q = f"The HC18 fetal ultrasound dataset contains the file {fname}. What is the head circumference in mm recorded for it? Answer with a number only."; truth = c['labels'].get('hc_mm')
            elif key in ('BUS-BRA', 'BUSI', 'BrEaST'): q = f"The {key} breast ultrasound dataset contains the file {fname}. Is the lesion in this image benign or malignant? Answer with one word."; truth = c['labels'].get('cls')
            else: q = None; truth = c['labels'].get('cls_raw')
            a = chat(w, q) if q else None; b = chat(w, 'Which public ultrasound dataset does this image come from? Answer with the dataset name only.', img)
            rows.append(dict(dataset=key, case_id=c['case_id'], file=fname, text_probe_q=q, text_probe_answer=a, truth=truth, dataset_answer=b, dataset_match=any(x.lower() in b.lower() for x in NAMES[key])))
            open(out, 'a').write(json.dumps(rows[-1]) + '\n')
    return rows

if __name__ == '__main__': run(sys.argv[1], sys.argv[2])
