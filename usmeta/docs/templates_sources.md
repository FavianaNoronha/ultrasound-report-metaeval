# Sources for the template structure (templates_v2)

Status key: **from memory, to confirm** = I (Claude) wrote this from general knowledge of the standard; I did NOT open the
source during this work, so the exact wording, edition and page must be checked by a person before it is cited in a paper.

## Breast: ACR BI-RADS Ultrasound lexicon (ACR BI-RADS Atlas, 5th ed., 2013) — from memory, to confirm
| report field | lexicon term(s) used | where the value comes from |
|---|---|---|
| shape | oval, round, irregular | BrEaST expert label |
| orientation | parallel / not parallel in the lexicon; we write "wider than tall" / "taller than wide" | **approximate**: bounding box of the mask (width >= height). Proxy only; BI-RADS orientation is relative to the skin line |
| margin | circumscribed; not circumscribed (indistinct, angular, microlobulated, spiculated) | BrEaST expert label |
| echo pattern | anechoic, hyperechoic, complex cystic and solid, hypoechoic, isoechoic, heterogeneous | BrEaST expert label |
| posterior features | no posterior features, enhancement, shadowing, combined | BrEaST expert label |
| calcifications | in a mass, outside a mass, intraductal | BrEaST expert label |
| halo | "echogenic halo" is listed under surrounding tissue / associated features — to confirm | BrEaST expert label |
| size | longest diameter | BrEaST: mask major axis x pixel size, **approximate** (unit of Pixel_size inferred, see unified.py). Others: % of image width, no mm |
| assessment | BI-RADS category 1-5 incl. 4a/4b/4c | dataset label |
| pathology, histology | not part of the lexicon (outcome fields) | dataset label |
| side, position | "side" is a labelled field (BUS-BRA only). "position" is the third of the image where the lesion centre falls, **not** a clock-face/quadrant location | mask |

## Thyroid: ACR TI-RADS lexicon (Tessler et al., J Am Coll Radiol 2017) — from memory, to confirm
composition (cystic, spongiform, mixed cystic and solid, solid), echogenicity (anechoic, hyperechoic/isoechoic, hypoechoic, very hypoechoic),
shape (wider-than-tall / taller-than-wide), margin (smooth, ill-defined, lobulated/irregular, extrathyroidal extension), echogenic foci
(none/large comet-tail, macrocalcifications, peripheral calcifications, punctate echogenic foci).
- DDTI labels use its own vocabulary (e.g. "predominantly solid", "marked hypoechogenicity", "well defined smooth"); we pass the dataset wording through, we do not remap it to the ACR terms.
- DDTI TI-RADS levels are written **2, 3, 4a, 4b, 4c, 5** (a Kwak-style subdivision), which differs from ACR TR1-TR5. We print "TI-RADS 4a" as labelled — **to confirm** which scheme DDTI used.
- TN3K / TN5000: no descriptors, no TI-RADS level. Their class 0/1 label is **left out of the true report** because its meaning is unconfirmed. Only count, image position, relative size and a box-based orientation proxy are stated.

## Fetal head: ISUOG-style biometry — from memory, to confirm (ISUOG Practice Guidelines: ultrasound assessment of fetal biometry and growth, 2019)
- Head circumference (HC) in mm, measured on an axial head plane. HC18: expert HC from the dataset CSV (**labelled**, 1 decimal).
- Fetal-head plane dataset (FetalHead): plane name (trans-thalamic / trans-cerebellum / trans-ventricular) is **labelled**; HC is **approximate**, computed from the mask's ellipse-equivalent axes with Ramanujan's perimeter formula.
- No structure descriptions are written (no per-structure labels are available in these records).

## What we deliberately do not write
Echo contrast of the lesion vs surrounding tissue, posterior shadowing computed from pixels, calcifications from pixels: images are not available on the machine that built these reports, and the brief says not to invent. Pathology / BI-RADS are never derived from masks.
