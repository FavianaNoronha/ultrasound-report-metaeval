# Step 2: true reports v2 (built from record facts only)

What was run: `python3 -m usmeta.templates_v2` on the 10 unified datasets (usmeta/local_data). No AI wrote any report. Each case has the facts, a provenance tag per field (labelled / measured / approximate) and three phrasing styles (terse, standard, long) with the same facts.

| dataset | cases | fields stated (share of cases) |
|---|---|---|
| BrEaST | 256 | lesion 100%, count 98%, pos 98%, orient 98%, size_mm 98%, shape 98%, margin 98%, echo 98%, post 98%, calc 98%, halo 98%, birads 100%, path 100% |
| BUS-BRA | 1875 | lesion 100%, count 100%, pos 100%, orient 100%, size_pct 100%, side 100%, birads 100%, path 100%, hist 100% |
| BUSI | 780 | lesion 100%, count 82%, pos 82%, orient 82%, size_pct 82%, path 100% |
| UDIAT | 163 | lesion 100%, count 100%, pos 100%, orient 100%, size_pct 100%, path 100%, hist 100% |
| BUS-UCLM | 683 | lesion 100%, count 38%, pos 38%, orient 38%, size_pct 38%, path 100% |
| TN3K | 3493 | lesion 100%, count 100%, pos 100%, orient 100%, size_pct 100% |
| TN5000 | 5000 | lesion 100%, count 100%, pos 100%, orient 100%, size_pct 100% |
| DDTI | 480 | lesion 100%, count 97%, pos 97%, orient 97%, size_pct 97%, comp 43%, echo 43%, margin 70%, foci 71%, tirads 71% |
| HC18 | 999 | hc_mm 100% |
| FetalHead | 2833 | plane 100%, hc_mm 98% |

Fields that are **not** expert labels (provenance):

- BUS-BRA: `orient` is approximate in 1875 cases
- BUS-BRA: `pos` is approximate in 1875 cases
- BUS-BRA: `size_pct` is measured in 1875 cases
- BUS-UCLM: `orient` is approximate in 264 cases
- BUS-UCLM: `pos` is approximate in 264 cases
- BUS-UCLM: `size_pct` is measured in 264 cases
- BUSI: `orient` is approximate in 647 cases
- BUSI: `pos` is approximate in 647 cases
- BUSI: `size_pct` is measured in 647 cases
- BrEaST: `orient` is approximate in 252 cases
- BrEaST: `pos` is approximate in 252 cases
- BrEaST: `size_mm` is approximate in 252 cases
- DDTI: `orient` is approximate in 466 cases
- DDTI: `pos` is approximate in 466 cases
- DDTI: `size_pct` is measured in 466 cases
- FetalHead: `hc_mm` is approximate in 2793 cases
- TN3K: `orient` is approximate in 3493 cases
- TN3K: `pos` is approximate in 3493 cases
- TN3K: `size_pct` is measured in 3493 cases
- TN5000: `orient` is approximate in 5000 cases
- TN5000: `pos` is approximate in 5000 cases
- TN5000: `size_pct` is measured in 5000 cases
- UDIAT: `orient` is approximate in 163 cases
- UDIAT: `pos` is approximate in 163 cases
- UDIAT: `size_pct` is measured in 163 cases

## Checks run (tests/test_templates_v2.py, 6 pass)
- every number in every style text equals a number in the facts (1,500-case sample, all three styles); all three styles carry the same numbers
- BrEaST size = mask long axis x pixel size; TN3K/TN5000 class 0/1 not stated; BUSI has no invented fields
- HC18: head circumference from the annotation ellipse (Ramanujan) vs the CSV value: mean abs error 1.46 mm, median 1.03 mm, bias about +1.1 mm. **4 of 999 cases** (787_HC, 628_2HC, 346_HC, 186_HC) have an ellipse larger than the image (extracted major axis 748-812 px on an 800 px image), errors 52-133 mm: a mask-extraction artefact for ellipses reaching the border, not a label error. HC18 true reports use the CSV value, so they are unaffected; FetalHead HC (mask-derived) could be affected the same way.

## Caveats
- Orientation ("wider than tall") comes from the bounding box: approximate.
- Position is a third of the image, not an anatomical location.
- BrEaST size is approximate: the pixel-size unit was inferred (centimetres per pixel) by the loader.
- BUSI, UDIAT, BUS-UCLM, BUS-BRA, TN3K, TN5000, DDTI have no mm: size is % of image width.
- DDTI TI-RADS uses 4a/4b/4c (not ACR TR1-5): to confirm. Template sources are from memory, marked to confirm in usmeta/docs/templates_sources.md.
- Image files are not on this Mac (records point to another machine); not needed for text-only Part A.

Total: 16562 true reports, 49686 style texts. Example (BrEaST, standard): An irregular mass (wider than tall) with not circumscribed (indistinct) margins and heterogeneous echo pattern is seen in the upper central part of the image, measuring approximately 25 mm. Posterior acoustic shadowing and no calcifications and no echogenic halo. Assessment: BI-RADS 2. Pathology: benign.

---
Limitations: see [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
