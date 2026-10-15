"""WP1.5 container spike (spec D104): re-encode a GoPro chapter and compare the containers.

The package holds the source-versus-output comparison instrument
(:mod:`container_spike.compare`) and the spike runner (:mod:`container_spike.spike`),
which records the encoder capabilities, records what the camera writes and runs the
identity re-encode. It is spike code: evidence for the prototype gate (plan section 6,
Phase 1), not product code, and its interfaces are not frozen. FFmpeg, run as a separate
process, is the only tool it drives.
"""
