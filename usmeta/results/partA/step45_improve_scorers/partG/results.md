# Step 45, Part G: pretrained-encoder U-Net and MedSAM prompted by the U-Net box

**DOES NOT PASS the pre-registered rule** (pooled position AUROC >= 0.92 and the paired difference CI excluding 0). On the same 498 usable test scans as Step 40 the ImageNet-pretrained U-Net reaches pooled position AUROC **0.905 (0.877-0.930)** (random-init Step 29 model: 0.892 (0.862-0.919)); paired difference +0.013 (95% CI -0.007 to +0.034, 242 groups): the CI includes 0 and the point estimate is below 0.92. MedSAM prompted by the box of the pretrained U-Net's mask: 0.895 (0.865-0.921), paired difference +0.003 (-0.021 to +0.027): also does not pass. Thyroid (reported separately; Step 40: 0.79): random-init 0.790 (0.725-0.848), pretrained U-Net 0.830 (0.769-0.884) (paired +0.040, CI -0.008 to +0.096), MedSAM from the U-Net box 0.806 (0.747-0.860). Breast is unchanged (0.942 (0.918-0.963) vs 0.942 (0.915-0.964)).

Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_partG.py`, `step45_partG_report.py` (new; step29 training, the Step 20 image check on the Step 40 scans and partb MedSAM imported unchanged).

## What was run

- **Pretrained encoder:** the Step 29 U-Net with the ResNet-18 encoder initialised from torchvision ImageNet weights (`resnet18-f37072fd.pth`, IMAGENET1K_V1; source `https://download.pytorch.org/models/resnet18-f37072fd.pth`; SHA-256 `f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec`; 46.8 MB; downloaded with the owner's approval into the git-ignored `local_data/step45/`, **not committed**); the first convolution is the sum of the RGB filters (one grey channel); the decoder stays randomly initialised. A unit check confirmed that the encoder tensors equal the pretrained ones. Same training code and settings as Step 29 (dev only, leak filter, flips and intensity augmentation, 30 epochs at most, patience 6, early stopping and threshold / largest-component choice on val), one model per organ, seed 0. Breast: 1270 dev images, 30 epochs, best val Dice 0.830 (Step 29 breast model 0.815); thyroid: 1438 dev images, 29 epochs, best val Dice 0.791 (Step 29 thyroid 0.751). Note: the `encoder` field of `train_*_pt.json` is written by the unchanged Step 29 code and still reads 'random init'; the weights used are the ImageNet ones above.
- **MedSAM from the U-Net box:** wanglab/medsam-vit-base (as Step 16); for each scan the box of the largest component of the pretrained U-Net mask is the prompt; an empty U-Net mask stays empty.
- **Evaluation:** the Step 20 tolerance-aware image check (tau 0.3, adjacent position), per-scan position AUROC on the same 498 usable test scans as Step 40 (the random-init model's per-scan values come from Step 40's `rows.json`); paired per scan, group bootstrap 1,000, seed 0.

## Results

| model | scans | pooled position AUROC (95% CI) | breast | thyroid | mean Dice | paired vs random-init, pooled (95% CI) |
|---|---|---|---|---|---|---|
| random-init U-Net (Step 29 / Step 40) | 498 | 0.892 (0.862-0.919) | 0.942 (0.918-0.963) | 0.790 (0.725-0.848) | 0.763 | — |
| ImageNet-pretrained U-Net | 498 | 0.905 (0.877-0.930) | 0.942 (0.915-0.964) | 0.830 (0.769-0.884) | 0.793 | +0.013 (-0.007 to +0.034) |
| MedSAM from the pretrained U-Net's box | 498 | 0.895 (0.865-0.921) | 0.938 (0.911-0.961) | 0.806 (0.747-0.860) | 0.701 | +0.003 (-0.021 to +0.027) |

Paired scans: 285 scans with a defined per-scan position AUROC in both models (position AUROC exists only for scans with a planted position error). Mean Dice uses the scans with a true mask (TN5000 has boxes only). The MedSAM variant lowers the mean Dice (0.701 vs 0.793) (MedSAM masks overlap the true masks less than the U-Net's); the position AUROC is the pre-registered metric.

## Deviations from the PREREG

- None known in the design; the PREREG did not say which model carries the pass rule, so both new models are tested against it and neither passes. The test split was read once for this part (`usmeta.step45_partG` in the test-access log).

## Caveats

- 30 or more groups in every pooled cell (242 groups); the thyroid cell has 90 groups. The difference in thyroid (+0.04) is inside its interval.
- One seed and one split; templated candidates; the position AUROC is limited by the 23 scans whose position is wrong, so a ceiling near 0.92 needs very few further corrections.
