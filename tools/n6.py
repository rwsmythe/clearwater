"""The shared N6 export target from D106 / spec v0.5.8 (WP-T8, DR-119 e).

The owner ruled "Concur with 12" on 2026-11-02; spec v0.5.8 recorded the
target at about 12 minutes of processing per minute of 4K footage, end to end.
These constants label instrument results; they do not change measured figures.
"""

N6_MIN_PER_MIN = 12.0
"""Minutes of processing per minute of 4K footage, including decode and encode."""

FRAME_BUDGET_S_29_97 = N6_MIN_PER_MIN / (30000 / 1001)
"""The N6 frame budget at the GoPro's 30000/1001 fps (29.97 rounded): 0.4004 s."""
