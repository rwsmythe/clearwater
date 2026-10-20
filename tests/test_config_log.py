"""WP3.15: the rotating log (D88, N9)."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

from clearwater.config import configure_logging, shutdown_logging
from clearwater.config.log import LOGGER_NAME, _ClearwaterHandler


@pytest.fixture(autouse=True)
def _clean_logger() -> Iterator[None]:
    shutdown_logging()
    logger = logging.getLogger(LOGGER_NAME)
    level = logger.level
    yield
    shutdown_logging()
    logger.setLevel(level)


def _handlers() -> list[logging.Handler]:
    return [h for h in logging.getLogger(LOGGER_NAME).handlers if isinstance(h, _ClearwaterHandler)]


def test_lines_carry_iso_time_level_logger_and_message(tmp_path: Path) -> None:
    path = configure_logging(tmp_path / "logs")
    logging.getLogger("clearwater.config.demo").warning("hello %s", "world")
    shutdown_logging()
    line = path.read_text(encoding="utf-8").strip()
    pattern = (
        r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}[+-]\d\d:\d\d "
        r"WARNING clearwater\.config\.demo hello world$"
    )
    assert re.match(pattern, line), line


def test_default_level_is_info(tmp_path: Path) -> None:
    path = configure_logging(tmp_path)
    log = logging.getLogger("clearwater.demo")
    log.debug("hidden")
    log.info("shown")
    shutdown_logging()
    text = path.read_text(encoding="utf-8")
    assert "shown" in text and "hidden" not in text


def test_text_round_trips_as_utf8(tmp_path: Path) -> None:
    path = configure_logging(tmp_path)
    message = "caf\u00e9 \u30d7\u30ea\u30bb\u30c3\u30c8 \u2603"
    logging.getLogger("clearwater.demo").info(message)
    shutdown_logging()
    assert message in path.read_bytes().decode("utf-8")


def test_second_call_is_idempotent(tmp_path: Path) -> None:
    first = configure_logging(tmp_path)
    second = configure_logging(tmp_path, level=logging.DEBUG)
    assert first == second
    assert len(_handlers()) == 1
    logging.getLogger("clearwater.demo").debug("one line")
    shutdown_logging()
    assert first.read_text(encoding="utf-8").count("one line") == 1


def test_another_folder_replaces_the_handler_and_releases_the_old_file(tmp_path: Path) -> None:
    old = configure_logging(tmp_path / "a")
    new = configure_logging(tmp_path / "b")
    assert len(_handlers()) == 1
    logging.getLogger("clearwater.demo").info("moved")
    shutdown_logging()
    assert "moved" in new.read_text(encoding="utf-8")
    assert "moved" not in old.read_text(encoding="utf-8")


def test_rotates_at_the_size_limit_and_keeps_only_the_backup_count(tmp_path: Path) -> None:
    path = configure_logging(tmp_path, max_bytes=2000, backup_count=3)
    log = logging.getLogger("clearwater.demo")
    for index in range(400):
        log.info("record %04d %s", index, "x" * 60)
    shutdown_logging()
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["clearwater.log", "clearwater.log.1", "clearwater.log.2", "clearwater.log.3"]
    for name in names:
        data = (tmp_path / name).read_bytes()
        # rollover happens before the limit; the handler counts characters, so a platform that
        # writes two bytes per line end may be over by one byte per line
        assert len(data) <= 2000 + data.count(b"\n")
    assert "record 0399" in path.read_text(encoding="utf-8")  # newest in the live file
    oldest = (tmp_path / "clearwater.log.3").read_text(encoding="utf-8")
    assert "record 0000" not in oldest  # the earliest records were dropped


def test_defaults_are_one_mebibyte_and_five_backups(tmp_path: Path) -> None:
    configure_logging(tmp_path)
    (handler,) = _handlers()
    assert isinstance(handler, _ClearwaterHandler)
    assert handler.maxBytes == 1024 * 1024
    assert handler.backupCount == 5


@pytest.mark.parametrize(("max_bytes", "backups"), [(0, 5), (1000, 0), (-1, 1)])
def test_unbounded_rotation_settings_are_refused(
    tmp_path: Path, max_bytes: int, backups: int
) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        configure_logging(tmp_path, max_bytes=max_bytes, backup_count=backups)
    assert _handlers() == []


def test_shutdown_without_configuration_is_harmless() -> None:
    shutdown_logging()
    shutdown_logging()
    assert _handlers() == []


def test_one_record_over_the_limit_is_written_whole_to_a_file_of_its_own(tmp_path: Path) -> None:
    configure_logging(tmp_path, max_bytes=1000, backup_count=2)
    log = logging.getLogger("clearwater.demo")
    log.info("small before")
    log.info("big %s", "y" * 5000)
    log.info("small after")
    shutdown_logging()
    sizes = {p.name: p.stat().st_size for p in tmp_path.iterdir()}
    assert len(sizes) <= 3  # the live file plus at most backup_count backups
    big = [name for name, size in sizes.items() if size > 1000]
    assert len(big) == 1  # the oversized record is whole, in one file, past the limit
    assert "y" * 5000 in (tmp_path / big[0]).read_text(encoding="utf-8")
