"""Deterministic generators for the shared test fixtures (WP2.3).

Every sample the Phase 3 tests use is made here from code and numbers: no owner photo, no
owner footage, no GPS and no third-party file. ``generate.py`` writes the samples and
``manifest.json``; ``stills.py``, ``video.py``, ``flicker.py`` and ``files.py`` hold one
generator group each; ``manifest.py`` holds the schema and its validator.
"""
