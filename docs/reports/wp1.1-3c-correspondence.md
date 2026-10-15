# WP1.1 -- 3C: the kappa -> Cr, lambda -> Cb correspondence (spec 14.1)

**Result: confirmed.** kappa (the paper's red-green opponent channel a\*) belongs on Cr and
lambda (the blue-yellow channel b\*) on Cb, as spec section 6.3.2 states. The b\* axis is
the Cb axis (reversed) within 1 degree; the a\* axis is about 29 degrees from the Cr axis,
rotated toward +Cb, so "corresponds most closely" (the spec's wording) is the accurate
description for a\*. The sign reversal of b\* against Cb does not matter: the 3C equation
is linear in the channel (`C' = C - k M G{C}` holds for `-C` as well).

Reproduction: a short script over `tools/prototype/pipeline.py` (`srgb_to_lab`,
`rgb_to_ycbcr`, `compensate_c3`, plus an inverse CIELAB conversion for the Lab reference),
kept outside the repository with the review evidence as
`C:\Users\rwsmy\clearwater-review-evidence\wp1.1\analysis\c3corr.py`. Every number below
is its output on 2026-10-14 (run from the worktree root with `uv run python`).

## 1. Derivation

**The paper's roles** ([3C], Ancuti et al., IEEE TIP 29, 2020; spec 6.1, 6.3.2). 3C works
on the opponent channels of CIELAB: a\* runs green (negative) to red/magenta (positive),
b\* runs blue (negative) to yellow (positive). Underwater, the red loss shows up as a
strongly negative a\* (and the blue-green cast in both channels); the paper's underwater
defaults are kappa = 1.0 on a\* and lambda = 0.7 on b\*.

**BT.709 YCbCr** (ITU-R BT.709-6 items 3.2-3.3; `RGB_TO_YCBCR` in `pipeline.py`):
`Y = 0.2126 R + 0.7152 G + 0.0722 B`, `Cb = (B - Y) / 1.8556`, `Cr = (R - Y) / 1.5748`,
full range and zero-centred. Cr is the red-minus-luma difference (positive = red, negative
= cyan/green); Cb is blue-minus-luma (positive = blue, negative = yellow).

So by construction Cr is the red-green opponent axis and Cb the blue-yellow axis with the
opposite sign to b\*. To measure how closely the axes coincide, the gradients of a\* and
b\* (sRGB -> CIELAB D65, the conversion of `srgb_to_lab`) with respect to RGB were taken at
neutral grays and written in the (Y, Cb, Cr) basis (central differences, step 1e-3):

| Gray level | a\* in (Y, Cb, Cr) | b\* in (Y, Cb, Cr) | a\* axis vs Cr | b\* axis vs -Cb |
|---|---|---|---|---|
| 0.25 | (-0.015, +136.98, +246.46) | (-0.009, -310.86, +4.53) | 29.1 deg | 0.8 deg |
| 0.50 | (+0.045, +121.55, +218.66) | (-0.000, -275.78, +4.03) | 29.1 deg | 0.8 deg |
| 0.75 | (-0.000, +112.85, +202.97) | (+0.006, -255.99, +3.73) | 29.1 deg | 0.8 deg |

Near the gray axis both opponent channels are pure chroma (the Y coefficient is ~0).
b\* = -276 Cb (+ a negligible Cr term): the same axis. a\* = 219 Cr + 122 Cb: mostly Cr,
with a blue component, because CIELAB's red-green axis points to magenta-red rather than
to the red primary. No assignment of the two YCbCr channels fits better: a\* has its
larger component on Cr, b\* almost all of its component on Cb.

## 2. Effect on a synthetic red-deficient image

A 96 x 128 gradient image with a strong blue-green cast (R 0.06-0.16, G 0.40-0.70,
B 0.50-0.70), compensated with the defaults (kappa 1.0, lambda 0.7, kernel 0.05 of the
short side, mask threshold 0.85). Means over the image:

| Variant | mean R, G, B | Cb | Cr | a\* | b\* |
|---|---|---|---|---|---|
| input | 0.110, 0.550, 0.550 | +0.0504 | -0.2200 | -28.53 | -8.72 |
| 3C in YCbCr, kappa -> Cr, lambda -> Cb (the prototype) | 0.457, 0.454, 0.485 | +0.0151 | +0.0000 | +1.95 | -4.28 |
| 3C in YCbCr, swapped (0.7 -> Cr, 1.0 -> Cb) | 0.353, 0.487, 0.457 | -0.0000 | -0.0660 | -13.93 | +0.35 |
| 3C in CIELAB, the paper's space (reference) | 0.487, 0.497, 0.513 | +0.0092 | -0.0054 | +0.00 | -2.62 |

The prototype's assignment raises Cr from -0.22 to 0 (kappa = 1 removes the local mean
entirely) and lifts mean red from 0.11 to 0.46, close to the Lab reference (mean absolute
per-pixel difference to the Lab result 0.031, 0.043, 0.029 for R, G, B). The swapped
assignment leaves a third of the red deficit (Cr -0.066, a\* -13.9, mean red 0.35; mean
absolute difference to the Lab result 0.135 on R). The Lab reference also changes the
brightness slightly (it holds L\*, not luma, so Y moves from 0.457 to 0.496); YCbCr holds
Y exactly. That difference, and the a\* axis rotation, are the cost of the spec's choice of
YCbCr (D47), which the paper reports as giving similar results.

The tests `test_c3_raises_cr_on_a_red_deficient_image` and
`test_c3_is_identity_on_a_neutral_gray_image` in `tests/test_prototype_pipeline.py` pin the
direction of the effect.
