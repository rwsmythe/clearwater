# CP2 (deep part) -- owner look check on the SCUBA footage

**Pack:** `work/wp1.3d/index.html` (WP1.3D, accepted 2026-10-20, main `7f9fea1`): 48 chapter
stills + 12 case candidates, each in c3 / ancuti2018 / ancuti2018-blue; 6 s clip of GX011600 at
the deepest candidate (staged statistics, 2.0 s Gaussian smoothing), c3 and ancuti2018 beside the
source. Walked with the owner by CHARC, one step at a time. Owner words verbatim with their time.

## Step 1 (2026-10-20 ~06:15Z) -- cases, stills, clip

> "c3 throughout showed the best performance, same issues with ancuti as in the previous scenes.
> No halo or clipping noted. For the clips, c3 also renders the best. Both clips had
> discontinuities at ~1 sec when the scene shifts from rock to open water with a step change in
> scene lighting. The effect is less pronounced in the original."

Reading: c3 handles all three spec-12 cases (open blue water, distance haze, deep-water noise)
acceptably across the candidates; the Ancuti variants repeat the shallow finding (red push on skin
and bright surfaces). No halo, no clipping. **New finding:** in the deep clip both corrected
renders show a discontinuity at about 1 s where the scene steps from rock to open water with a
step change in lighting; the step is present but less pronounced in the source. The 2 s staged
smoothing (PROVISIONAL per DR-25(3)) does not hide a lighting step; the correction amplifies it.
Routed to the temporal-smoothing design (see below), not a defect of the colour method.

## Step 2 (2026-10-20 ~06:25Z) -- noise, flicker, remaining cast

> "No grain noted. No flicker noted. The cast is fairly well greyed"

Reading: no visible noise in the deep stills or the c3 clip; no flicker in the 6 s clip apart from
the lighting-step discontinuity of step 1; the residual cast in c3 is neutral ("fairly well
greyed"), i.e. acceptable. The owner did not name single candidates per case; all four per case
are recorded as confirmed representatives.

## Outcome

**Deep CP2 COMPLETE 2026-10-20.** c3 confirmed as the default on deep footage as on shallow;
Ancuti variants stay selectable options. No halo, clipping, noise, flicker or residual cast. One
finding routed: the 2 s smoothing does not hide a lighting step (clip at ~1 s); to WP1.4b's open
smoothing question and the Phase 2 temporal design (step detection / window reset). The sheet in
`docs/reports/wp1.3d-deep-look-check.md` is filled from these words.
