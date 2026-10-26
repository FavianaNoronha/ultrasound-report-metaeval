"""HiSBreast rule-based field parser (TASK_hisbreast Step 2), run on the English translation AND on the Vietnamese original; agreement between the two is the automatic validation
(there is no bilingual reviewer). Fields: side, birads (highest code stated), finding type, axillary node, recommendation, suspicious wording."""
import re
from . import hisbreast_validate as V

FT_EN = [('abscess', r'abscess'), ('inflammation', r'inflam|mastitis'), ('post_surgical', r'post-?op|post-?surg|surgery|surgical|mastectomy|resect'), ('cyst', r'cyst'),
         ('multiple_masses', r'(multiple|several|numerous|scattered)\s+(\w+\s+){0,2}(mass|nodule|lesion)|masses|nodules'), ('mass', r'mass|tumou?r|nodule|lump|lesion'), ('fibro', r'fibro')]
FT_VI = [('abscess', r'áp[\s-]?xe|abscess'), ('inflammation', r'viêm'), ('post_surgical', r'sau mổ|phẫu thuật|đã mổ'), ('cyst', r'nang'),
         ('multiple_masses', r'(nhiều|rải rác)\s+(\w+\s+){0,2}(bướu|khối|nốt)|các (bướu|khối|nốt)'), ('mass', r'bướu|khối|\bu\b|nốt|tổn thương'), ('fibro', r'u xơ|xơ')]
REC_EN = [('fna', r'fna|aspirat'), ('biopsy', r'biops'), ('followup', r'follow|monitor|surveil')]; REC_VI = [('fna', r'chọc hút|fna'), ('biopsy', r'sinh thiết'), ('followup', r'theo dõi')]
SUSP_EN = r'suspic|suspect|malignan|cancer|carcinoma|\bk\b'; SUSP_VI = r'nghi ngờ|ung thư|ác tính|\bk\b'

def parse(text, lang):
    t = V.nfc(text); f = V.facts(text, lang); codes = f['birads']
    def rank(c): return (int(c[0]), c[1:] or '')
    top = max(codes, key=rank) if codes else None
    ft = None
    for name, rx in (FT_EN if lang == 'en' else FT_VI):
        if re.search(rx, t): ft = name; break
    if f['noabn'] and ft in (None, 'mass') and not re.search(r'mass|bướu|khối|nốt|nodule', t): ft = 'no_abnormality'
    if ft is None: ft = 'no_abnormality' if f['noabn'] else 'other'
    sides = f['side']; side = 'both' if ('B' in sides or ('R' in sides and 'L' in sides)) else ('right' if 'R' in sides else 'left' if 'L' in sides else 'unspecified')
    rec = [n for n, rx in (REC_EN if lang == 'en' else REC_VI) if re.search(rx, t)]
    return dict(side=side, birads=top, birads_all=codes, finding=ft, axillary=f['c_axillary'], recommendation=rec[0] if rec else None, suspicious=bool(re.search(SUSP_EN if lang == 'en' else SUSP_VI, t)))
