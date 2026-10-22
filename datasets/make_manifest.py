"""Build datasets/manifest.json: for each dataset used by usmeta, where it is expected, how many files, total size and a tree hash
(SHA-256 over sorted 'relative path + size' lines). Images are NOT stored in git; this lets anyone check they hold the same files.
    python3 datasets/make_manifest.py [--root ~/Downloads]"""
import os, sys, json, hashlib, argparse
SPEC = [  # name, folder under root, organ, what usmeta reads, citation (from memory: TO CONFIRM before citing)
 ('BrEaST', 'BrEaST-Lesions_USG-images_and_masks', 'breast', 'images, masks, expert BI-RADS descriptors (baseline_exp/breast.xlsx in this repo)', 'Pawłowska et al. 2024, BrEaST-Lesions-USG (TCIA)'),
 ('BUS-BRA', 'archive-5', 'breast', 'BUSBRA/BUSBRA/{Images,Masks,bus_data.csv}', 'Gómez-Flores et al. 2024, BUS-BRA'),
 ('BUSI', 'Dataset_BUSI_with_GT', 'breast', '{benign,malignant,normal}/*.png and *_mask*.png', 'Al-Dhabyani et al. 2020, Dataset of breast ultrasound images'),
 ('UDIAT', 'archive-4', 'breast', 'UDIAT_Dataset_B/{original,GT,DatasetB.xlsx}', 'Yap et al. 2018, UDIAT dataset B'),
 ('BUS-UCLM', 'archive-8', 'breast', 'BUS-UCLM/{images,masks,INFO.csv}', 'Vallez et al. 2025, BUS-UCLM'),
 ('TN3K', 'archive-6', 'thyroid', '{trainval,test}-{image,mask}/', 'Gong et al. 2021, TN3K (TRFE-Net)'),
 ('TN5000', 'TN5000_forReview', 'thyroid', '{JPEGImages,Annotations,ImageSets}/', 'TN5000 (2025), to confirm'),
 ('DDTI', 'archive-9', 'thyroid', 'jpg images + xml outlines', 'Pedraza et al. 2015, DDTI'),
 ('HC18', 'archive-7', 'fetal', '{training_set,test_set}/, training_set_pixel_size_and_HC.csv', 'van den Heuvel et al. 2018, HC18 challenge'),
 ('FetalHead', 'Trans-cerebellum;Trans-thalamic;Trans-ventricular', 'fetal', 'three plane folders (Patient..._Plane..png + masks)', 'to confirm (fetal head plane dataset)'),
]
def tree(path):
    h = hashlib.sha256(); n = 0; size = 0
    for d, _, fs in sorted(os.walk(path)):
        for f in sorted(fs):
            if f == '.DS_Store': continue
            p = os.path.join(d, f); s = os.path.getsize(p); h.update(f'{os.path.relpath(p, path)}\t{s}\n'.encode()); n += 1; size += s
    return n, size, h.hexdigest()
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--root', default='~/Downloads'); a = ap.parse_args(); root = os.path.expanduser(a.root); out = []
    for name, folder, organ, reads, cite in SPEC:
        ent = dict(dataset=name, organ=organ, expected_folder=folder, usmeta_reads=reads, citation_from_memory_to_confirm=cite, licence='to confirm')
        parts = [os.path.join(root, f) for f in folder.split(';')]
        if all(os.path.isdir(p) for p in parts):
            t = [tree(p) for p in parts]; ent.update(present_on_this_machine=True, files=sum(x[0] for x in t), bytes=sum(x[1] for x in t), tree_sha256=hashlib.sha256(''.join(x[2] for x in t).encode()).hexdigest())
        else: ent.update(present_on_this_machine=False, note='not on the machine that built this manifest')
        out.append(ent); print(name, ent.get('files'), ent.get('bytes'))
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'manifest.json'), 'w'), indent=1)
