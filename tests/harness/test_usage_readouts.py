"""The weekly-usage readouts (scripts/usage_codex.py, scripts/usage_claude.py).

Pure-function tests on canned responses; no network, no subprocess, no
credential file. The pace formula is the dispatch tiebreak's input, so it is
pinned here with the first live readings of 2026-10-27 as the fixtures.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class PaceFormula(unittest.TestCase):
    def setUp(self) -> None:
        self.codex = _load("usage_codex")

    def test_codex_first_reading(self) -> None:
        # 2026-10-27 02:41Z (epoch 1793068860): 22 % used, resets 2026-11-02 08:03Z
        # (epoch 1793606580) -> 11.1 % of the window elapsed, pace about 2.0.
        out = self.codex.pace_from(22, 10080, 1793606580, 1793068860)
        self.assertAlmostEqual(out["elapsed_fraction"], 0.111, places=2)
        self.assertAlmostEqual(out["pace"], 1.98, places=1)

    def test_claude_first_reading(self) -> None:
        # 21 % used at ~10 % of the window -> pace about 2.1.
        resets = 1_800_000_000.0
        now = resets - 0.9 * 7 * 86400
        out = self.codex.pace_from(21, 10080, resets, now)
        self.assertAlmostEqual(out["elapsed_fraction"], 0.1, places=3)
        self.assertAlmostEqual(out["pace"], 2.1, places=1)

    def test_fresh_window_does_not_divide_by_zero(self) -> None:
        out = self.codex.pace_from(0, 10080, 1_800_000_000.0, 1_800_000_000.0 - 7 * 86400)
        self.assertEqual(out["pace"], 0.0)
        self.assertGreater(out["elapsed_fraction"], 0.0)

    def test_past_reset_clamps_to_full_window(self) -> None:
        out = self.codex.pace_from(50, 10080, 1_000.0, 2_000.0)
        self.assertEqual(out["elapsed_fraction"], 1.0)
        self.assertEqual(out["pace"], 0.5)


class ClaudeParse(unittest.TestCase):
    def setUp(self) -> None:
        _load("usage_codex")
        self.claude = _load("usage_claude")

    def test_parses_seven_day_block(self) -> None:
        body = {
            "five_hour": {"utilization": 10.0, "resets_at": "2026-10-27T04:30:00+00:00"},
            "seven_day": {"utilization": 21.0, "resets_at": "2026-11-02T10:00:00.248465+00:00"},
        }
        import datetime as dt

        now = dt.datetime(2026, 10, 27, 2, 41, tzinfo=dt.UTC).timestamp()
        out = self.claude.parse_usage(body, now)
        self.assertEqual(out["lane"], "claude")
        self.assertEqual(out["used_percent"], 21.0)
        self.assertEqual(out["resets_at"], "2026-11-02T10:00:00Z")
        self.assertAlmostEqual(out["elapsed_fraction"], 0.099, places=2)
        self.assertAlmostEqual(out["pace"], 2.1, places=1)

    def test_missing_block_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.claude.parse_usage({"five_hour": {}}, 0.0)


if __name__ == "__main__":
    unittest.main()
