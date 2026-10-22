# datasets

The usmeta benchmark is built from 10 public ultrasound datasets. **The image files are not stored in this git repository**
(about 3 GB in total, GitHub rejects files over 100 MB, and several licences have not been checked yet). This folder holds what you
need to get the same data and to verify you have it:

- `manifest.json`: for each dataset the expected folder name, what `usmeta` reads from it, number of files, size in bytes and a tree hash
  (SHA-256 over sorted relative paths and file sizes). Built on the author's Mac by `python3 datasets/make_manifest.py`.
- `make_manifest.py`: rebuild the manifest for your own copy (`--root` = the folder holding the datasets) and compare `files`, `bytes`
  and `tree_sha256` with the committed one.
- Put the raw data in `~/Downloads` (or set `USMETA_DATA`) under the folder names in the manifest, then run
  `python3 -m usmeta.unified build` to create `usmeta/local_data/*.jsonl` (git-ignored) and `python3 -m usmeta.unified table` to see what each dataset supports.

| dataset | organ | expected folder | files | size |
|---|---|---|---|---|
| BrEaST | breast | BrEaST-Lesions_USG-images_and_masks | 522 | 70 MB |
| BUS-BRA | breast | archive-5 | 5,627 | 266 MB |
| BUSI | breast | Dataset_BUSI_with_GT | 1,578 | 266 MB |
| UDIAT | breast | archive-4 | 357 | 25 MB |
| BUS-UCLM | breast | archive-8 | 2,050 | 674 MB |
| TN3K | thyroid | archive-6 | 6,986 | 191 MB |
| TN5000 | thyroid | TN5000_forReview | 10,004 | 210 MB |
| DDTI | thyroid | archive-9 | 870 | 19 MB |
| HC18 | fetal | archive-7 | 2,335 | 176 MB |
| FetalHead (planes) | fetal | Trans-cerebellum, Trans-thalamic, Trans-ventricular | 2,869 | 1.1 GB |

Not in the table: HiSBreast (text only, separate brief) and UltraG thyroid / breast text labels (jsonl files, one over 100 MB).

## Before anyone downloads or cites
- **Licences are "to confirm" for every dataset.** Do not redistribute the images from this repository until each licence has been read.
- The citations in `manifest.json` were written from memory and must be checked against the dataset pages before use in a paper.
- Folder names such as `archive-5` are the names the files had after download; they are what `usmeta/unified.py` looks for.
- BUS-BRA `Side` has the value `single` for 253 images; it is not a laterality and is not used as one.
- TN3K / TN5000: the meaning of class 0 / 1 is not confirmed, so it is left out of the true reports.
