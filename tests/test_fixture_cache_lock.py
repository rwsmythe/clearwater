"""Process-level regression checks for the generated-fixture cache lock (WP-T4)."""

from __future__ import annotations

import json
import multiprocessing
import os
import time
from pathlib import Path
from typing import Any

import pytest

import fixture_plugin


def _race_worker(
    index: int,
    cache: Path,
    scratch: Path,
    checked: Any,
    calls: Any,
    complete: Any,
    partial: Any,
    first_returned: Any,
) -> None:
    """Expose a second writer's partial file to the first writer's real verifier."""
    original_verify = fixture_plugin.verify_generated
    original_generate = fixture_plugin.generate.generate
    initial = True
    writer = None
    record: dict[str, Any] = {"ok": False, "index": index}

    def synchronized_verify(entry: dict[str, Any], path: Path) -> str | None:
        nonlocal initial
        problem = original_verify(entry, path)
        if initial:
            initial = False
            checked.wait(timeout=60)
        return problem

    def delayed_generate(out: Path, generated_out: Path, groups: Any) -> Any:
        nonlocal writer
        with calls.get_lock():
            writer = calls.value
            calls.value += 1
        time.sleep(2)
        if writer == 0:
            result = original_generate(out, generated_out, groups)
            complete.set()
            # A locked waiter never enters the generator. An unlocked writer
            # opens a partial output before this provider's final verification.
            partial.wait(timeout=3)
            return result
        if not complete.wait(timeout=60):
            raise TimeoutError("the first generator did not finish")
        path = generated_out / "flicker" / "ad14-flicker.mkv"
        path.write_bytes(b"an in-progress second generation, not a complete Matroska clip")
        partial.set()
        if not first_returned.wait(timeout=60):
            raise TimeoutError("the first provider did not return")
        return original_generate(out, generated_out, groups)

    fixture_plugin.verify_generated = synchronized_verify
    fixture_plugin.generate.generate = delayed_generate
    try:
        provider = fixture_plugin.SampleProvider(
            fixture_plugin.load_manifest(),
            fixture_plugin.FIXTURES_DIR,
            cache,
            lambda: scratch / f"committed-{index}",
        )
        provider.path("ad14-flicker")
        record["ok"] = True
    except BaseException as error:
        record["error"] = f"{type(error).__name__}: {error}"
    finally:
        if writer == 0:
            first_returned.set()
        record["writer"] = writer
        (scratch / f"result-{index}.json").write_text(json.dumps(record), encoding="utf-8")


def _run_cold_cache_race(cache: Path, scratch: Path) -> dict[str, Any]:
    """Run two real providers with simultaneous cold misses and delayed writers."""
    assert not cache.exists(), f"the regression needs a cold cache: {cache}"
    scratch.mkdir(parents=True)
    context = multiprocessing.get_context("spawn")
    checked = context.Barrier(2)
    calls = context.Value("i", 0)
    complete, partial, first_returned = (context.Event() for _ in range(3))
    processes = [
        context.Process(
            target=_race_worker,
            args=(index, cache, scratch, checked, calls, complete, partial, first_returned),
        )
        for index in range(2)
    ]
    try:
        for process in processes:
            process.start()
        deadline = time.monotonic() + 120
        for process in processes:
            process.join(timeout=max(0, deadline - time.monotonic()))
        timed_out = any(process.is_alive() for process in processes)
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
            if process.pid is not None:
                process.join(timeout=10)
    records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(scratch.glob("result-*.json"))
    ]
    return {
        "timed_out": timed_out,
        "exitcodes": [process.exitcode for process in processes],
        "generation_calls": calls.value,
        "records": records,
    }


@pytest.mark.usefixtures("ffmpeg_tools")
def test_two_processes_share_one_verified_cold_cache_generation(tmp_path: Path) -> None:
    """A second provider must not overwrite a clip being generated or verified."""
    cache = tmp_path / "generated"
    result = _run_cold_cache_race(cache, tmp_path / "race")
    assert not result["timed_out"], result
    assert result["exitcodes"] == [0, 0], result
    assert len(result["records"]) == 2, result
    assert all(record["ok"] for record in result["records"]), result
    assert result["generation_calls"] == 1, result
    entry = next(
        entry
        for entry in fixture_plugin.load_manifest()["samples"]
        if entry["id"] == "ad14-flicker"
    )
    assert fixture_plugin.verify_generated(entry, cache / entry["path"]) is None


def test_busy_cache_lock_has_a_bounded_wait(tmp_path: Path) -> None:
    """An occupied cache fails at its wait bound without entering regeneration."""
    cache = tmp_path / "generated"
    with fixture_plugin._generated_cache_lock(cache):
        with (
            pytest.raises(TimeoutError, match="timed out waiting"),
            fixture_plugin._generated_cache_lock(cache, timeout_s=0),
        ):
            pytest.fail("a second owner entered the occupied lock")
        assert (tmp_path / ".generated.lock").is_file()
    assert not (tmp_path / ".generated.lock").exists()


def test_suspected_stale_lock_is_reported_without_stealing_it(tmp_path: Path) -> None:
    """An old lock requires confirmed-owner cleanup rather than unsafe age-based theft."""
    lock = tmp_path / ".generated.lock"
    lock.write_text("pid=12345\n", encoding="ascii")
    old = time.time() - 901
    os.utime(lock, (old, old))
    with (
        pytest.raises(TimeoutError, match=r"suspected stale.*confirm its owner has stopped"),
        fixture_plugin._generated_cache_lock(tmp_path / "generated"),
    ):
        pytest.fail("a second owner entered the suspected stale lock")
    assert lock.read_text(encoding="ascii") == "pid=12345\n"


def test_cache_lock_is_released_when_generation_raises(tmp_path: Path) -> None:
    """An interrupted generation in a live process leaves the cache lock reusable."""
    cache = tmp_path / "generated"
    with (
        pytest.raises(RuntimeError, match="generation failed"),
        fixture_plugin._generated_cache_lock(cache),
    ):
        raise RuntimeError("generation failed")
    assert not (tmp_path / ".generated.lock").exists()
    with fixture_plugin._generated_cache_lock(cache, timeout_s=0):
        assert (tmp_path / ".generated.lock").is_file()
