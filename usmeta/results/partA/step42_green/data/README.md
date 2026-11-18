# Step 42 data (GREEN, 4-bit, Colab T4)

Inputs and raw outputs behind `../results.md`. Text is built from dataset labels with our templates; no images and no HiSBreast text.

| file | what |
|---|---|
| `green_pairs.jsonl` | the reference/candidate pairs sent to GREEN (built before scoring) |
| `pair_key.json` | answer key: which pairs hold a planted error, its type and size, and the rewording type |
| `n_chosen.json` | how many units the pre-registered size rule picked, written before scoring |
| `dev_timing_pairs.jsonl`, `dev_timing.json`, `dev_green_scores.jsonl` | dev-only timing run used by the size rule |
| `green_scores.jsonl` | GREEN score and error counts for the 507 scored pairs |
| `colab_env.json` | library versions and GPU on the Colab run |

Notebook: `usmeta/notebooks/step42_green_colab.ipynb`.
