# Modern Techniques for Correcting Underwater Imagery

**Scope:** Visual quality (photography/video look), offline video processing. Covers physics-based models, deep learning, and classic enhancement.
**Compiled:** 12 October 2026

---

## Summary

- **Physics-based** methods give the most trustworthy color.
- **Deep learning** gives the most polished look.
- For **video**, the main unsolved problem is **flicker (temporal inconsistency)**, because most methods are designed for single images.

---

## 1. Physics-based restoration

### Revised underwater image formation model (Akkaynak & Treibitz)
The foundation for nearly every modern physics-based method. Key findings:
- Signal attenuation is **not uniform** across the scene; it depends on object range and reflectance.
- The coefficient governing backscatter growth with distance **differs** from the signal attenuation coefficient.

Older "underwater dehazing" methods that reused the atmospheric haze model are wrong on both points.

### Sea-thru (CVPR 2019)
- Estimates backscatter from the darkest pixels and their known range.
- Then estimates the spatially varying illuminant to obtain the range-dependent attenuation coefficient.
- **Requires a depth (range) map.** The original work built range maps from multiple images of the same scene.
- Accuracy depends heavily on depth-map quality.

### Sea-thru with monocular depth
- Replaces measured depth with a depth-estimation network (e.g., StreamUR uses a pre-trained monocular depth network with the revised model for near-real-time restoration).
- Weakness: **scale ambiguity** — relative depth is easy, absolute range is not.

### Video helps the physics
- **USe-ReDI-Net (ICCV 2023):** combines the physical model with a view-synthesis constraint on neighboring video frames. Fully self-supervised; outputs depth and restored image at ~55 fps. Introduced the DRUVA real-sea video dataset.
- **SUCRe:** shows color restoration benefits strongly from multi-view observations of the same scene points.

### 3D reconstruction as restoration
- **SeaThru-NeRF:** a NeRF with separate fields for geometry and the water medium; render with the water removed. Slow (~0.07 fps rendering).
- **WaterSplatting:** 3D Gaussian Splatting for geometry plus a separate volumetric field for the medium. Real-time rendering, outperforms SeaThru-NeRF on its benchmark.
- **Gaussian Splashing:** another 3DGS adaptation built on the Sea-thru formation model.
- **Limitation:** needs mostly static scenes and good camera motion. **Strength:** inherently temporally consistent.

---

## 2. Classic enhancement (no learning, no depth)

### Color Balance and Fusion — Ancuti et al. (IEEE TIP 2018)
- Blends two images derived from a color-compensated, white-balanced version of the input.
- Weight maps favor edges and color contrast; multiscale fusion avoids artifacts.
- Cheap, no training, reasonably independent of camera settings.

### Color Channel Compensation (3C) — Ancuti et al. (IEEE TIP 2020)
- For cases where one channel (usually red) is nearly lost.
- Reconstructs the lost channel from the opponent color channel by subtracting a local mean.
- Works as a pre-processing step for other methods.

**Limitation of this family:** ignores distance, so far regions remain hazy.

---

## 3. Deep learning (single image)

### Supervised CNN / Transformer models
- **U-shape Transformer:** attention focused on the color channels and spatial regions with the most severe attenuation; loss combines RGB, LAB, and LCH color spaces. Released the **LSUI** dataset (5004 image pairs).
- Other notable models: Ucolor (medium-transmission-guided), Water-Net (UIEB baseline).

**Important caveat:** there is no true "water-removed" ground truth. Reference images in these datasets are generated, typically by selecting the best output among existing algorithms. Models learn a *preferred look*, not physical truth — acceptable for visual-quality goals, but results inherit the style biases of the reference set.

### Diffusion models
- **Osmosis (ECCV 2024):** trains an unconditional diffusion prior on joint color + depth using **in-air** RGBD datasets, then uses guidance based on the underwater formation model to sample clean images. Never sees underwater images in training, avoiding the ground-truth problem.
- A 2025 review judges diffusion-based enhancement better suited to offline post-processing and human-facing visualization than to real-time robotics.
- **Video caveat:** per-frame diffusion can change frame-to-frame cues, hurting consistency.

---

## 4. Video-specific methods

Running any single-image method frame by frame causes flicker. Three approaches:

### Native video networks
- **UVEB (CVPR 2024):** main video benchmark — 1,308 paired sequences, >453,000 frame pairs, ~38% 4K.
- **UVE-Net** (UVEB baseline): converts current-frame information into convolutional kernels passed to adjacent frames. A smaller variant (UVE-Net-s) runs 2K video in real time.
- **WVEnet (JMSE 2025):** optical-flow-based enhancement over consecutive frames.

### Post-hoc temporal stabilizers
- **WaterWave (Dec 2025):** represents enhanced video in a wavelet-based temporal consistency field; includes an underwater-specific optical flow correction module. Needs no paired data and works on top of any single-image method.
- **Zero-TIG (2025):** zero-shot, Retinex + optical flow, with adaptive RGB balancing for underwater color distortion.

### Generative prior + physics + temporal constraints
- **UnDIVE (WACV 2025):** two-stage; a generative (diffusion) prior is incorporated into a physics-based formulation, with temporal consistency enforced between frames. Generalizes across water types.

---

## 5. Evaluation

- Common no-reference metrics (**UIQM, UCIQE, CCF**) are **unreliable** — a dedicated study found none satisfactorily rates enhanced underwater images.
- Known failures: a method with a strong reddish shift scored higher on UIQM; UCIQE rewards high contrast even when unnatural.
- For visual quality, side-by-side human judgment on your own footage remains the real test.

---

## 6. Practical takeaway for offline video

*(Synthesis — not from any single paper.)*

| Goal | Suggested approach |
|---|---|
| Easiest strong result | Per-frame method (Ancuti fusion or pretrained U-shape Transformer) + temporal stabilizer (WaterWave) |
| Most natural color | Sea-thru-style physics with monocular depth; estimate water parameters per shot and smooth over time instead of per frame (avoids flicker by design) |
| Static scene, slow camera pass | WaterSplatting-style reconstruction — water-free renders, consistent by construction |
| Best-looking single frames | Diffusion (Osmosis), paired with a temporal stabilizer |

---

## Sources

- Sea-thru (CVPR 2019): https://openaccess.thecvf.com/content_CVPR_2019/papers/Akkaynak_Sea-Thru_A_Method_for_Removing_Water_From_Underwater_Images_CVPR_2019_paper.pdf
- Color Balance and Fusion (Ancuti, TIP 2018): https://research.dial.uclouvain.be/handle/2078.5/253495
- Color Channel Compensation 3C (TIP 2020): https://research.dial.uclouvain.be/handle/2078.5/169548
- U-shape Transformer / LSUI: https://arxiv.org/abs/2111.11843
- Osmosis (ECCV 2024): https://arxiv.org/abs/2403.14837
- UVEB (CVPR 2024): https://arxiv.org/abs/2404.14542
- UnDIVE (WACV 2025): https://arxiv.org/abs/2411.05886
- WaterWave (2025): https://arxiv.org/abs/2512.05492
- WVEnet (JMSE 2025): https://mdpi-res.com/d_attachment/jmse/jmse-13-00127/article_deploy/jmse-13-00127.pdf
- Zero-TIG (2025): https://papers.cool/arxiv/2503.11175
- USe-ReDI-Net (ICCV 2023): https://mlanthology.org/iccv/2023/varghese2023iccv-selfsupervised
- SUCRe: https://arxiv.org/pdf/2212.09129
- WaterSplatting: https://arxiv.org/abs/2408.08206
- Gaussian Splashing: https://arxiv.org/pdf/2411.19588v2
- StreamUR (ISPRS 2024): https://isprs-archives.copernicus.org/articles/XLVIII-3-2024/1/2024/isprs-archives-XLVIII-3-2024-1-2024.pdf
- Visual enhancement and 3D representation review (2025): https://arxiv.org/pdf/2505.01869
- On the limits of perceptual quality measures: https://arxiv.org/abs/2207.05470
- Real-world Underwater Enhancement benchmark: https://arxiv.org/pdf/1901.05320
