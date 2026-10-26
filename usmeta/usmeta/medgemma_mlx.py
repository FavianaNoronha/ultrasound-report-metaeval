"""MedGemma-1.5-4B-it, 4-bit MLX conversion (made locally from the official google/medgemma-1.5-4b-it weights with `mlx_vlm convert -q --q-bits 4 --q-group-size 64`).
Runs under ~/venvs/mlx312/bin/python (Python 3.12 + mlx-vlm); does NOT import usmeta. Reads a job file written by usmeta.medgemma, writes jsonl.
    ~/venvs/mlx312/bin/python usmeta/medgemma_mlx.py JOBS.json OUT.jsonl
job = {"key":..., "kind": "report"|"box"|"text"|"image_q", "image": path or null, "flip": bool, "prompt": str, "max_tokens": int}"""
import json, sys, os, time, tempfile
from PIL import Image
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

PATH = os.path.expanduser('~/.cache/usmeta/medgemma-1.5-4b-it-4bit')

def main(jobs_path, out):
    jobs = json.load(open(jobs_path)); done = {json.loads(l)['id'] for l in open(out)} if os.path.exists(out) else set()
    model, processor = load(PATH); config = load_config(PATH); t0 = time.time()
    for i, j in enumerate([x for x in jobs if x['id'] not in done]):
        t = time.time(); img = None; size = None
        if j.get('image'):
            im = Image.open(j['image']).convert('RGB'); size = list(im.size)
            if j.get('flip'): im = im.transpose(Image.FLIP_LEFT_RIGHT)
            img = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name; im.save(img)
        prompt = apply_chat_template(processor, config, j['prompt'], num_images=1 if img else 0)
        res = generate(model, processor, prompt, [img] if img else None, max_tokens=j.get('max_tokens', 220), temperature=0.0, verbose=False)
        text = res.text if hasattr(res, 'text') else str(res)
        open(out, 'a').write(json.dumps(dict(id=j['id'], key=j.get('key'), kind=j['kind'], size=size, seconds=round(time.time() - t, 1), text=text.strip())) + '\n')
        if img: os.remove(img)
        if i % 10 == 0: print(i, round(time.time() - t0), 's', flush=True)

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
