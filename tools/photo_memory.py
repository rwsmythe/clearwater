"""Measure one WP5.2 synthetic PNG16 in fresh default-device and forced-CPU runners.

Seat-only CLI: ``measure INPUT --name W52-2 --exclusive [--config FILE]``. INPUT must resolve
below <working>/wp5.2, outside footage. Records, runner logs, settings and outputs stay below
<working>/wp5.2/photo/<name>-<leg>-<unique id>. The 5d record schema is retained with class
synthetic-png16 instead of an owner HEIC/JPEG class. Exit 0 means both legs passed; 1 means a
measurement failed (including a disk/output refusal raised inside a measurement leg);
2 means usage/config/input/output refusal before measurement. No EXIF or raw runner payload
is copied into the summary. Full-size generation and measurement belong in EXCLUSIVE windows.

The executable 48 MP generator recipe is in ``docs/proofs/wp5.2-ledger.md``, section 5,
R3. It imports ``unit_content``, ``quantize``, ``png16_bytes`` and ``srgb_profile`` from
``fixtures.stills``: WP2.3's seeded low-red RGB16, 8064x6048, with no EXIF. The recipe
guards its new output under <working>/wp5.2/W52-2 and refuses an existing file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

import photo_verify as pv
from clearwater.core.memory import memory_estimate_bytes
from local_config import LocalConfigError, load_local_config
from spike_io.guard import OutputRefusedError, WriteGuard


def _write(path: Path, record: dict[str, Any], guard: WriteGuard) -> None:
    with guard.check(path).open("x", encoding="ascii", newline="\n") as output:
        output.write(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def _measure(source: Path, guard: WriteGuard, name: str, force_cpu: bool) -> dict[str, Any]:
    width, height = pv._dimensions(source)
    pv._disk_check(guard.root, width * height * 6)
    label = "cpu" if force_cpu else "default"
    folder = guard.folder(f"{name}-{label}-{uuid.uuid4().hex[:12]}")
    out = guard.folder(folder.name, "out")
    settings = guard.folder(folder.name, "settings")
    memory = pv.device_memory()
    estimate = memory_estimate_bytes(height, width, "c3")
    record: dict[str, Any] = {
        "schema": 1,
        "command": "memory",
        "file": source.name,
        "class": "synthetic-png16",
        "stored_size": [width, height],
        "method": "c3",
        "force_cpu": force_cpu,
        "forced_cpu": force_cpu,
        "exclusive": True,
        "estimate_bytes": estimate,
        "device_free_before_bytes": None if memory is None else memory["free_bytes"],
        "device_total_bytes": None if memory is None else memory["total_bytes"],
        "estimate_exceeds_free_before": None if memory is None else estimate > memory["free_bytes"],
        "estimate_fits_free_before": None if memory is None else estimate < memory["free_bytes"],
        "rss_scope": "tool-runner-tree-including-sampler-children",
        "decoder_versions": pv._decoder_versions(),
        "ram_limit_bytes": 16_000_000_000,
        "device_limit_bytes": 8188 * 2**20,
        "measured_at_utc": datetime.now(UTC).isoformat(),
    }
    sampler = pv.MemorySampler(psutil.Process(os.getpid()))
    guard_token = pv._ACTIVE_GUARD.set(guard)
    sampler_token = pv._ACTIVE_SAMPLER.set(sampler)
    try:
        sampler.start()
        try:
            exit_code, raw = pv.launch_runner(
                source,
                out,
                guard.check(folder / "runner.json"),
                settings,
                bit_depth=16,
                force_cpu=force_cpu,
                neutral=False,
            )
        finally:
            sampler.stop()
    finally:
        pv._ACTIVE_SAMPLER.reset(sampler_token)
        pv._ACTIVE_GUARD.reset(guard_token)
    record.update(sampler.record())
    items = raw.get("items", [])
    reason = pv._device_reason(items[0].get("device")) if len(items) == 1 else None
    record.update(
        runner_exit=exit_code,
        device_reason=reason,
        read_ok=exit_code == 0,
        automatic_fallback=bool(reason and reason.startswith("CPU:") and reason != "CPU: forced"),
        memory_capacity_fallback=bool(reason and reason.startswith("CPU: estimate ")),
    )
    failures = [] if exit_code == 0 and reason is not None else ["runner_failed"]
    for prefix, peak, count, active, unavailable in (
        ("ram", "rss_tree_peak_bytes", "rss_samples", "rss_active_samples", "rss_unavailable"),
        (
            "device",
            "device_used_peak_bytes",
            "device_samples",
            "device_active_samples",
            "device_unavailable",
        ),
    ):
        limit = record[prefix + "_limit_bytes"]
        observations = [record.get(peak)]
        if prefix == "ram":
            observations.append(record.get("os_peak_working_set_bytes"))
        known = [value for value in observations if value is not None]
        complete = (
            record.get(peak) is not None
            and record.get(count, 0) > 0
            and record.get(active, 0) > 0
            and unavailable not in record["sampler_errors"]
            and (prefix != "device" or memory is not None)
        )
        breached = any(value > limit for value in known)
        record[prefix + "_within_limit"] = False if breached else (True if complete else None)
        if not complete:
            failures.append(
                "memory_rss_measurement" if prefix == "ram" else "memory_device_measurement"
            )
        if breached:
            failures.append("memory_ram_limit" if prefix == "ram" else "memory_device_limit")
    record["failed_checks"] = failures
    _write(folder / "record.json", record, guard)
    return record


def main(argv: Sequence[str] | None = None) -> int:
    """Validate one input and measure the default device followed by forced CPU.

    Args:
        argv: CLI arguments, or None for sys.argv[1:].

    Returns:
        Zero for two successful records; one for measurement failure, including a refusal
        inside a leg; two for refusal before measurement.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    measure = commands.add_parser("measure")
    measure.add_argument("input", type=Path)
    measure.add_argument("--name", required=True)
    measure.add_argument("--exclusive", action="store_true", required=True)
    measure.add_argument("--config", type=Path)
    args = parser.parse_args(argv)
    try:
        config = load_local_config(args.config)
        name = pv._name(args.name)
        root = config.working_path.resolve() / "wp5.2"
        input_guard = WriteGuard(root, config.footage_path)
        source = input_guard.check(args.input).resolve()
        if not source.is_file() or source.suffix.lower() != ".png":
            raise ValueError("input must be an existing synthetic PNG16 file under working/wp5.2")
        # Check the PNG IHDR directly: Pillow presents RGB16 as RGB8 on read.
        with source.open("rb") as stream:
            header = stream.read(29)
        if (
            len(header) != 29
            or header[:8] != b"\x89PNG\r\n\x1a\n"
            or header[12:16] != b"IHDR"
            or header[24:26] != b"\x10\x02"
        ):
            raise ValueError("input must be RGB PNG16")
        guard = WriteGuard(root / "photo", config.footage_path)
        guard.folder()
    except (LocalConfigError, ValueError, OSError, OutputRefusedError) as error:
        print(f"REFUSED {error}", file=sys.stderr)
        return 2
    failed = False
    for force_cpu in (False, True):
        try:
            record = _measure(source, guard, name, force_cpu)
        except Exception as error:
            print(f"FAILED {type(error).__name__}: {error}", file=sys.stderr)
            return 1
        print(json.dumps(record, ensure_ascii=True, allow_nan=False), flush=True)
        failed = failed or bool(record["failed_checks"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
