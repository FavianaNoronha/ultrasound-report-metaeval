Flip sanity test: Qwen2.5-VL-3B report on original vs horizontally flipped scan (20 scans). Identical report = 1.00.

| dataset | n | bleu | rougeL | chrf |
|---|---|---|---|---|
| TN3K | 5 | 0.49 | 0.50 | 0.64 |
| BUS-BRA | 5 | 0.52 | 0.54 | 0.63 |
| TN5000 | 5 | 0.54 | 0.54 | 0.63 |
| HC18 | 5 | 0.48 | 0.46 | 0.61 |

---
Limitations: see [docs/LIMITATIONS.md](docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
