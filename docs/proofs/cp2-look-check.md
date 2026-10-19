# CP2 -- Look check (owner checkpoint record, LIVING until the owner finishes the sheet)

CP2 is the owner's visual review (plan section 5; spec D103: informal bar, no numeric
threshold). CHARC records the owner's words with their time; the WP1.3 report's section 9 sheet
is filled from this record when the look is complete. Material: the WP1.3 pack
`work\wp1.3\index.html` (24 stills x 3 variants, flicker pair) and the WP1.4 clips
`work\wp1.4\GX011627\clips\` (unsmoothed, staged, flat). Walkthrough given by CHARC in five
steps on 2026-10-19.

## Step 2 -- the stills (owner, 2026-10-19 ~01:35Z, chat to CHARC, verbatim)

"It looks like the green/blue is corrected out. Both of the ancuti algorithms seem to cause too
much red in the scene (skin and white boat show this in particular. C3 seems to match my
recollection of the actual scene."

CHARC reading: colour cast remaining = NO (all three variants). Red over-correction on skin and
the white boat = YES for `ancuti2018` and `ancuti2018-blue`, NO for `c3`. Preferred variant =
`c3`. This is a look-side input to the method default (spec 14.1) and to the WP1.6 gate report;
the Ancuti red push is consistent with the pack's gain table (red gains up to 1.38 against
c3's 0.98-1.03). Seriousness and decision for the red push: owner's, pending.

Owner, 2026-10-19 ~01:40Z (verbatim): "I saw no indications of halo, noise, or clipping. c3
should be the default, we can keep the other two as options."

Step-2 sheet rows (owner): colour cast remaining NO; magenta/red push YES on both Ancuti
variants (skin, white boat), NO on c3, decision: **c3 becomes the default method, ancuti2018
and ancuti2018-blue stay as selectable options**; over-sharpening halo NO; noise NO; clipping
NO. The default-method change is a spec decision (14.1 / the method default); CHARC carries it
into the spec revision bundle with the chapter deferral (owner approves the exact text).

## Step 3 -- flicker, WP1.3 pair (owner, 2026-10-19 ~01:45Z, verbatim)

"I don'tsee any brightness or color pulsing. I do see a smooth ramp up in overall red tint of
the coral as the camera shows more open water, but, as noted, it is a smooth shift."

Sheet row: flicker (unsmoothed, worst case) = NO. The owner's "smooth ramp up in red tint" is the
scene-driven gain drift the WP1.3 report measured on this clip (red gain 1.02 -> 1.32 over the 6 s
as the field of view fills with water; frame-to-frame jitter ~1 %), on the Ancuti-rendered clip.
Not flicker; a statistics-adaptation effect. Noted for the smoothing-window and method-default
discussion (c3 adapts far less, red gain 0.98-1.03 on the same frames).

## Steps 4-5: pending
