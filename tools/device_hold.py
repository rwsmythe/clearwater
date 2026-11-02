"""Hold device-zero memory until a stop file appears or a timeout expires.

Usage: ``uv run python tools/device_hold.py --mib 256 --stop-file PATH --timeout-s 60``.
One flushed JSON line announces readiness: held_bytes is the allocator's actual block size;
free_before/free_after are driver free bytes before/after the live allocation, with the CUDA
context already initialised. The supplied stop file is only inspected, never written.
Before release, a second flushed JSON line reports {"stopped": "stop-file"} or
{"stopped": "timeout"} for a normal exit.
Normal stop or timeout exits 0; argument errors exit 2. Python-level exits release in finally;
process teardown releases the context even when an external kill cannot execute finally.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
import time
from collections.abc import Sequence
from pathlib import Path


def _positive_mib(value: str) -> int:
    mib = int(value)
    if mib <= 0:
        raise argparse.ArgumentTypeError("--mib must be a positive integer")
    return mib


def _positive_seconds(value: str) -> float:
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("--timeout-s must be finite and positive")
    return seconds


def main(argv: Sequence[str] | None = None) -> int:
    """Allocate one CuPy byte buffer, announce it, wait, then release it.

    Args:
        argv: CLI arguments, or None for sys.argv[1:].

    Returns:
        Zero on stop-file arrival or timeout; allocation/runtime errors propagate.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--mib", type=_positive_mib, required=True)
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--timeout-s", type=_positive_seconds, required=True)
    args = parser.parse_args(argv)
    if not args.stop_file.name or not args.stop_file.parent.is_dir():
        parser.error("--stop-file must name a file in an existing directory")
    if args.stop_file.exists():
        parser.error("--stop-file must not already exist")
    cp = importlib.import_module("cupy")
    with cp.cuda.Device(0):
        cp.cuda.runtime.free(0)
        free_before, _ = cp.cuda.runtime.memGetInfo()
        buffer = None
        try:
            buffer = cp.empty(args.mib * 2**20, dtype=cp.uint8)
            buffer.fill(1)
            cp.cuda.runtime.deviceSynchronize()
            free_after, _ = cp.cuda.runtime.memGetInfo()
            print(
                json.dumps(
                    {
                        "held_bytes": int(buffer.data.mem.size),
                        "free_before": int(free_before),
                        "free_after": int(free_after),
                    }
                ),
                flush=True,
            )
            deadline = time.monotonic() + args.timeout_s
            while not args.stop_file.exists():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(0.05, remaining))
            print(
                json.dumps({"stopped": "stop-file" if args.stop_file.exists() else "timeout"}),
                flush=True,
            )
        finally:
            buffer = None
            cp.get_default_memory_pool().free_all_blocks()
    return 0


if __name__ == "__main__":
    sys.exit(main())
