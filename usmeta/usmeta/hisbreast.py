"""HiSBreast loader (Step 1 of TASK_hisbreast). Reads ~/Downloads/HiSBreast.zip IN PLACE. Vietnamese clinician-written conclusions.
Licence blank, no de-identification statement: derived text stays LOCAL (usmeta/local_data/hisbreast/, git-ignored); patient/exam codes are hashed
(salted SHA-256, first 12 hex) in every output file. Split key = exam id."""
import os, re, json, zipfile, hashlib, collections, glob
SALT = 'usmeta-hisbreast-v1'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'local_data', 'hisbreast')

def hid(x): return hashlib.sha256((SALT + str(x)).encode()).hexdigest()[:12]

def clean(t): return re.sub(r'\s+', ' ', re.sub(r'<br\s*/?>', ' ', t or '')).strip()

def load_exams(zip_path=os.path.expanduser('~/Downloads/HiSBreast.zip')):
    z = zipfile.ZipFile(zip_path); exams = collections.OrderedDict(); n_img = 0
    for jn in sorted(n for n in z.namelist() if n.startswith('json/') and n.endswith('.json')):
        recs = json.loads(z.read(jn))['RECORDS']
        for k, r in enumerate(recs):
            if 'tuyến vú' not in (r.get('TEN_CDHA') or '').lower(): continue      # the JSON also holds abdomen, thyroid, endoscopy, ... records; breast ultrasound only
            n_img += 1; eid = r.get('SO_PHIEU_CDHA'); key = hid(eid)
            e = exams.setdefault(key, dict(exam=key, file=os.path.basename(jn), exam_name=clean(r.get('TEN_CDHA')), vi=clean(r.get('MO_TA')), clinical_dx=clean(r.get('CHANDOANBENH')), n_images=0))
            e['n_images'] += 1
            if clean(r.get('MO_TA')) != e['vi']: e.setdefault('text_conflicts', 0); e['text_conflicts'] += 1
        del recs
    return list(exams.values()), n_img

def summary(exams, n_img):
    L = [len(e['vi'].split()) for e in exams]; hist = collections.Counter(min(l // 5 * 5, 40) for l in L)
    return dict(exams=len(exams), images=n_img, exams_with_gt1_image=sum(e['n_images'] > 1 for e in exams), empty_text=sum(not e['vi'] for e in exams),
                text_conflicts_within_exam=sum(e.get('text_conflicts', 0) > 0 for e in exams), words_median=sorted(L)[len(L) // 2], words_max=max(L),
                words_hist_5_bins=dict(sorted(hist.items())), unique_texts=len({e['vi'] for e in exams}))

if __name__ == '__main__':
    exams, n = load_exams(); os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'exams.jsonl'), 'w').write(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in exams)); print(json.dumps(summary(exams, n), indent=1))
