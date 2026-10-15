"""WP1.3 look check pack: frames, corrected variants and the flicker clip for CP2.

The package holds the frame extraction instrument (:mod:`lookcheck.frames`, reused by
WP1.4) and the pack builder (:mod:`lookcheck.pack`), which runs the WP1.1 prototype over
the extracted frames and writes the material the owner pages through at the look check.
It is instrument code: evidence for the prototype gate (plan section 6, Phase 1), not
product code, and its interfaces are not frozen. FFmpeg and ffprobe, run as separate
processes, are the only tools it drives.
"""
