# Why Gemma replies were "unreadable" (Step 48, candidate P)

Source: gemma_raw_retry_setc.jsonl (488 Set C audit calls that Step 47 counted as unparsed; re-asked with the same prompt, same model, greedy, raw text saved). Analysed 2026-11-27.

| Cause | Replies |
|---|---|
| Valid JSON, but verdict "minor" while every issue is "major" (verdict and issues disagree) | 324 |
| Valid JSON, but an issue type outside the allowed list ("added" 131, "none" 21, "unsure" 12, "supported" 8, "rephrased" 4, ...) | 149 |
| Not JSON or cut off at the 700-token limit | 15 |

So 473 of 488 (97%) were well-formed JSON that our strict checker rejected for schema reasons, not unreadable text. The first lenient parser (fences, quotes, trailing commas) recovers only 4.

Candidate P2 (to test in Stage 1, decided before looking at routing results):
- verdict = worst issue severity (major > minor > unsure), "clean" if no issues;
- type "added", "added unsupported" -> "unsupported"; issues typed "none" or "supported" dropped; any other unknown type kept as "unsupported";
- truncated replies stay unparsed (routed, as before).
