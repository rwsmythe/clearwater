"""The transactional downloader against small wheels and a loopback-only HTTP index."""

from __future__ import annotations

import base64
import csv
import errno
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import threading
import time
import zipfile
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from clearwater import gpu_pack


def _installer():
    # Import here so the initial RED is a missing behavior, rather than collection failure.
    from clearwater import gpu_pack_install

    return gpu_pack_install


@pytest.fixture
def headless_entry(monkeypatch, tmp_path):
    # Resolve the native class before removing PySide6 from sys.modules. pytest-qt
    # processes events after fixture setup even in a module-alone headless run.
    from PySide6.QtWidgets import QApplication

    from test_frozen_entry import _fresh_entry

    for variable in (
        "APPDATA",
        "LOCALAPPDATA",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
    ):
        monkeypatch.setenv(variable, str(tmp_path / variable))
    QApplication.instance()  # No application or window is constructed.
    entry, blocker = _fresh_entry(monkeypatch)
    monkeypatch.setattr(entry.gpu_pack, "activate", lambda: pytest.fail("pack activated"))
    yield entry
    assert blocker.attempts == []


@pytest.mark.timeout(10)
def test_headless_install_progress_and_noop(fake_index, headless_entry, capsys):
    assert headless_entry.main(["clearwater", "--install-gpu-pack"]) == 0
    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 5
    for line, distribution in zip(lines[:-1], fake_index.distributions, strict=True):
        assert distribution.wheels[0][0] in line
    assert lines[-1] == "GPU support is installed. Restart Clearwater to use it."
    fake_index.requests.clear()
    assert headless_entry.main(["clearwater", "--install-gpu-pack"]) == 0
    assert capsys.readouterr().err.strip() == "GPU support is already installed"
    assert fake_index.requests == []
    assert headless_entry.main(["clearwater", "--remove-gpu-pack"]) == 0
    assert "takes effect at the next start" in capsys.readouterr().err
    assert not list(fake_index.root.iterdir())
    assert headless_entry.main(["clearwater", "--remove-gpu-pack"]) == 0
    assert capsys.readouterr().err.strip() == "no GPU pack is installed"


@pytest.mark.timeout(10)
@pytest.mark.parametrize("cancel", [False, True])
def test_headless_failure_and_cancel(headless_entry, monkeypatch, capsys, cancel):
    installer = _installer()
    outcome = installer.PackResult(False, "cancelled" if cancel else "no network", cancelled=cancel)
    monkeypatch.setattr(installer, "install", lambda progress: outcome)
    assert headless_entry.main(["clearwater", "--install-gpu-pack"]) == 1
    assert capsys.readouterr().err.strip() == outcome.message


@pytest.mark.timeout(10)
@pytest.mark.parametrize("operation", ["install", "remove"])
def test_headless_rejects_extra_arguments(headless_entry, monkeypatch, operation):
    monkeypatch.setattr(_installer(), operation, lambda *args: pytest.fail("installer called"))
    assert headless_entry.main(["clearwater", f"--{operation}-gpu-pack", "extra"]) != 0


@pytest.mark.timeout(10)
def test_headless_remove_failure(headless_entry, monkeypatch, capsys):
    installer = _installer()
    monkeypatch.setattr(
        installer, "remove", lambda: installer.PackResult(False, "folder is locked")
    )
    assert headless_entry.main(["clearwater", "--remove-gpu-pack"]) == 1
    assert capsys.readouterr().err.strip() == "folder is locked"


@pytest.mark.timeout(10)
@pytest.mark.parametrize("operation", ["install", "remove"])
def test_headless_windowed_without_stderr(headless_entry, monkeypatch, operation):
    installer = _installer()

    def run(*args):
        if args:
            args[0].report(1, 2, "wheel.whl")
            assert not args[0].cancelled()
        return installer.PackResult(True, "done")

    monkeypatch.setattr(installer, operation, run)
    monkeypatch.setattr(sys, "stderr", None)
    assert headless_entry.main(["clearwater", f"--{operation}-gpu-pack"]) == 0


class Progress:
    def __init__(self, cancel_wheel: str | None = None):
        self.reports = []
        self.cancel_wheel = cancel_wheel
        self.cancel = False

    def report(self, done, total, message):
        self.reports.append((done, total, message))
        if message == self.cancel_wheel:
            self.cancel = True

    def cancelled(self):
        return self.cancel


@pytest.fixture(autouse=True)
def network_guard(monkeypatch):
    allowed = set()
    refused = []
    create = socket.create_connection
    connect = socket.socket.connect

    def check(address):
        if not isinstance(address, tuple) or address[:2] not in allowed:
            refused.append(address)
            raise AssertionError(f"real or unapproved network refused: {address!r}")

    def guarded_create(address, *args, **kwargs):
        check(address)
        return create(address, *args, **kwargs)

    def guarded_connect(sock, address):
        check(address)
        return connect(sock, address)

    monkeypatch.setattr(socket, "create_connection", guarded_create)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    yield allowed, refused
    assert refused == [], f"test attempted forbidden network: {refused!r}"


def _wheel(name, *, hostile=None, omitted=False, nested_data=False):
    metadata = f"{name}-1.0.dist-info"
    files = {
        f"{name}/__init__.py": b"# synthetic package\n" * 100,
        f"{metadata}/METADATA": f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n".encode(),
        f"{metadata}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    if nested_data:
        files[f"{name}/.data/x"] = b"ordinary package data"
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    for path, data in files.items():
        if omitted and path.endswith("__init__.py"):
            continue
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
        writer.writerow((path, "sha256=" + digest.decode(), len(data)))
    writer.writerow((f"{metadata}/RECORD", "", ""))
    files[f"{metadata}/RECORD"] = buffer.getvalue().encode()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as wheel:
        for path, data in files.items():
            wheel.writestr(path, data)
        if hostile == "symlink":
            member = zipfile.ZipInfo(f"{name}/link")
            member.create_system = 3
            member.external_attr = (stat.S_IFLNK | 0o777) << 16
            wheel.writestr(member, "../../outside")
        elif hostile:
            member = zipfile.ZipInfo(hostile)
            # ZipInfo normalizes '\\' on Windows even before writing. Preserve the attack.
            member.filename = hostile
            wheel.writestr(member, b"escape")
    return archive.getvalue()


@pytest.fixture
def fake_index(tmp_path, monkeypatch, network_guard):
    installer = _installer()
    allowed, _ = network_guard
    bodies = {}
    requests = []
    mode = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.headers.get("Host"), self.path, self.headers.get("User-Agent")))
            if mode.get(self.path) == "unavailable":
                self.send_response(503)
                self.end_headers()
                return
            if self.path in mode and mode[self.path].startswith("http"):
                self.send_response(302)
                self.send_header("Location", mode[self.path])
                self.end_headers()
                return
            data = bodies[self.path]
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if mode.get(self.path) in ("short", "short-once"):
                if mode[self.path] == "short-once":
                    del mode[self.path]
                self.wfile.write(data[: len(data) // 2])
                self.wfile.flush()
                self.close_connection = True
            else:
                self.wfile.write(data)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    port = server.server_address[1]
    allowed.add(("127.0.0.1", port))
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
    )
    thread.start()
    root = tmp_path / "packs"
    root.mkdir()
    monkeypatch.setattr(gpu_pack, "pack_root", lambda: root)
    monkeypatch.setattr(gpu_pack, "STAMP", "test-cu12")
    monkeypatch.setattr(installer, "_DOWNLOAD_ORIGIN", ("http", "127.0.0.1", port))
    monkeypatch.setattr(installer, "_RETRY_DELAY", 0)
    monkeypatch.setattr(installer.urllib.request, "getproxies", lambda: {})

    def configure(*, hostile=None, omitted=False, nested_data=False):
        distributions = []
        for index in range(4):
            name = f"synthetic{index}"
            filename = f"{name}-1.0-py3-none-any.whl"
            data = _wheel(
                name,
                hostile=hostile if index == 0 else None,
                omitted=omitted,
                nested_data=nested_data,
            )
            bodies["/" + filename] = data
            distributions.append(
                gpu_pack.LockedDistribution(
                    name,
                    "1.0",
                    (
                        (
                            filename,
                            hashlib.sha256(data).hexdigest(),
                            f"http://127.0.0.1:{port}/{filename}",
                            len(data),
                        ),
                    ),
                )
            )
        monkeypatch.setattr(gpu_pack, "LOCKED_DISTRIBUTIONS", tuple(distributions))
        return distributions

    distributions = configure()
    try:
        yield SimpleNamespace(
            root=root,
            bodies=bodies,
            requests=requests,
            mode=mode,
            configure=configure,
            distributions=distributions,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)
        assert not thread.is_alive(), "fake index did not stop"
        assert all(host == f"127.0.0.1:{port}" and path in bodies for host, path, _ in requests)


@pytest.fixture
def empty_plan(tmp_path, monkeypatch):
    installer = _installer()
    root = tmp_path / "packs"
    monkeypatch.setattr(gpu_pack, "pack_root", lambda: root)
    monkeypatch.setattr(gpu_pack, "STAMP", "empty-cu12")
    monkeypatch.setattr(gpu_pack, "LOCKED_DISTRIBUTIONS", ())
    return installer, root


def test_plan_uses_the_running_tags_and_computed_size(fake_index):
    plan = _installer().plan()
    assert plan.stamp == "test-cu12"
    assert [w.name for w in plan.wheels] == [f"synthetic{i}" for i in range(4)]
    assert plan.download_size == sum(len(b) for b in fake_index.bodies.values())
    assert all(w.filename.endswith("py3-none-any.whl") for w in plan.wheels)


def test_happy_path_is_a_fully_checked_pack(fake_index):
    progress = Progress()
    result = _installer().install(progress)
    assert result.ok, result.message
    assert result.path == fake_index.root / "test-cu12"
    assert gpu_pack.check_pack(result.path) is None
    assert list(gpu_pack.pack_problems(result.path, full=True)) == []
    assert list(fake_index.root.iterdir()) == [result.path]
    assert not (result.path / "downloads").exists()
    document = json.loads((result.path / "manifest.json").read_text())
    for row in document["distributions"]:
        record = result.path / f"site-packages/{row['name']}-1.0.dist-info/RECORD"
        assert row["record_sha256"] == hashlib.sha256(record.read_bytes()).hexdigest()
    total = sum(len(b) for b in fake_index.bodies.values())
    assert progress.reports[-1][:2] == (total, total)
    assert [r[0] for r in progress.reports] == sorted(r[0] for r in progress.reports)
    assert all(agent == "Clearwater/1.0.0" for _, _, agent in fake_index.requests)


def test_hash_mismatch_stops_on_the_third_wheel(fake_index):
    path = "/synthetic2-1.0-py3-none-any.whl"
    data = fake_index.bodies[path]
    fake_index.bodies[path] = bytes([data[0] ^ 1]) + data[1:]
    result = _installer().install(Progress())
    assert not result.ok and path[1:] in result.message and "recorded hash" in result.message
    assert [r[1] for r in fake_index.requests] == [
        f"/synthetic{i}-1.0-py3-none-any.whl" for i in range(3)
    ]
    assert list(fake_index.root.iterdir()) == []


def test_short_http_body_retries_three_times_then_cleans_up(fake_index):
    fake_index.mode["/synthetic0-1.0-py3-none-any.whl"] = "short"
    result = _installer().install(Progress())
    assert not result.ok
    assert Counter(r[1] for r in fake_index.requests) == {"/synthetic0-1.0-py3-none-any.whl": 3}
    assert list(fake_index.root.iterdir()) == []


def test_a_retry_succeeds_without_regressing_progress(fake_index):
    fake_index.mode["/synthetic0-1.0-py3-none-any.whl"] = "short-once"
    progress = Progress()
    result = _installer().install(progress)
    assert result.ok, result.message
    assert Counter(r[1] for r in fake_index.requests) == {
        "/synthetic0-1.0-py3-none-any.whl": 2,
        "/synthetic1-1.0-py3-none-any.whl": 1,
        "/synthetic2-1.0-py3-none-any.whl": 1,
        "/synthetic3-1.0-py3-none-any.whl": 1,
    }
    assert [r[0] for r in progress.reports] == sorted(r[0] for r in progress.reports)
    total = sum(len(b) for b in fake_index.bodies.values())
    assert progress.reports[-1][:2] == (total, total)


def test_http_failure_is_retried_then_reported(fake_index):
    fake_index.mode["/synthetic0-1.0-py3-none-any.whl"] = "unavailable"
    result = _installer().install(Progress())
    assert not result.ok and "503" in result.message
    assert len(fake_index.requests) == 3
    assert list(fake_index.root.iterdir()) == []


def test_cancel_during_the_second_wheel_removes_staging(fake_index):
    result = _installer().install(Progress("synthetic1-1.0-py3-none-any.whl"))
    assert not result.ok and result.cancelled
    assert len(fake_index.requests) == 2
    assert list(fake_index.root.iterdir()) == []


@pytest.mark.parametrize("redirect_host", ["localhost", "127.0.0.1"])
def test_redirect_is_refused_before_a_second_connection(fake_index, redirect_host):
    hits = []

    class Other(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *_):
            pass

    second = ThreadingHTTPServer(("127.0.0.1", 0), Other)
    second.daemon_threads = True
    thread = threading.Thread(
        target=second.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
    )
    thread.start()
    try:
        fake_index.mode["/synthetic0-1.0-py3-none-any.whl"] = (
            f"http://{redirect_host}:{second.server_address[1]}/outside"
        )
        result = _installer().install(Progress())
        assert not result.ok and "redirect refused" in result.message
        assert hits == []
        assert list(fake_index.root.iterdir()) == []
    finally:
        second.shutdown()
        second.server_close()
        thread.join(2)
        assert not thread.is_alive()


@pytest.mark.parametrize(
    "hostile",
    [
        "../outside",
        "/absolute",
        "C:/drive",
        "a\\backslash",
        "symlink",
        "synthetic0-1.0.data/purelib/x",
    ],
)
def test_hostile_members_fail_without_leaving_anything(fake_index, hostile, tmp_path):
    fake_index.configure(hostile=hostile)
    result = _installer().install(Progress())
    assert not result.ok and "wheel member" in result.message
    assert not (tmp_path / "outside").exists()
    assert list(fake_index.root.iterdir()) == []


def test_already_installed_does_not_download(fake_index):
    installer = _installer()
    assert installer.install(Progress()).ok
    fake_index.requests.clear()
    result = installer.install(Progress())
    assert result.ok and result.message == "GPU support is already installed"
    assert fake_index.requests == []


def test_rejected_pack_is_replaced_and_dead_process_leftovers_removed(fake_index):
    rejected = fake_index.root / "test-cu12"
    rejected.mkdir()
    (rejected / "broken").write_bytes(b"broken")
    partial = fake_index.root / "test-cu12.partial-dead"
    partial.mkdir()
    (partial / "leftover").write_bytes(b"leftover")
    result = _installer().install(Progress())
    assert result.ok, result.message
    assert not (rejected / "broken").exists()
    assert not partial.exists()


def test_disk_space_refuses_before_network(fake_index, monkeypatch):
    monkeypatch.setattr(shutil, "disk_usage", lambda _: SimpleNamespace(free=1))
    result = _installer().install(Progress())
    assert not result.ok and "free" in result.message and "required" in result.message
    assert fake_index.requests == []
    assert list(fake_index.root.iterdir()) == []


def test_disk_budget_needs_only_the_largest_archive(fake_index, monkeypatch):
    monkeypatch.setattr(_installer(), "_INSTALLED_SIZE", 10_000)
    # Four 2,955-byte wheels: 15,000 permits installed + largest + 10%, not their sum.
    monkeypatch.setattr(shutil, "disk_usage", lambda _: SimpleNamespace(free=15_000))
    result = _installer().install(Progress())
    assert result.ok, result.message


def test_disk_full_during_download_cleans_up_without_transport_retries(fake_index, monkeypatch):
    original = Path.open

    def full(path, *args, **kwargs):
        if path.suffix == ".part":
            raise OSError(errno.ENOSPC, "synthetic full disk")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", full)
    result = _installer().install(Progress())
    assert not result.ok and "full disk" in result.message
    assert len(fake_index.requests) == 1
    assert list(fake_index.root.iterdir()) == []


def test_a_failed_final_rename_cleans_up_staging(fake_index, monkeypatch):
    replace = os.replace

    def denied(source, destination):
        if Path(destination).name == gpu_pack.STAMP:
            raise PermissionError("synthetic open handle prevents rename")
        return replace(source, destination)

    monkeypatch.setattr(os, "replace", denied)
    result = _installer().install(Progress())
    assert not result.ok and "open handle" in result.message
    assert list(fake_index.root.iterdir()) == []


def test_removal_handles_a_read_only_pack_file(fake_index):
    installer = _installer()
    assert installer.install(Progress()).ok
    payload = fake_index.root / "test-cu12/site-packages/synthetic0/__init__.py"
    payload.chmod(stat.S_IREAD)
    try:
        result = installer.remove()
        assert result.ok, result.message
        assert list(fake_index.root.iterdir()) == []
    finally:
        if payload.exists():
            payload.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_unlisted_nested_file_fails_full_verification(fake_index):
    fake_index.configure(omitted=True)
    result = _installer().install(Progress())
    assert not result.ok and "unlisted" in result.message
    assert list(fake_index.root.iterdir()) == []


def test_removal_deletes_pack_and_partial_but_refuses_an_outside_path(fake_index, tmp_path):
    installer = _installer()
    assert installer.install(Progress()).ok
    (fake_index.root / "test-cu12.partial-dead").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    refused = installer.remove(outside)
    assert not refused.ok and outside.is_dir()
    assert installer.remove().ok
    assert list(fake_index.root.iterdir()) == []
    assert installer.remove().message == "no GPU pack is installed"


def test_full_verify_precedes_manifest_then_disk_check_then_rename(empty_plan, monkeypatch):
    installer, root = empty_plan
    events = []
    check = gpu_pack.pack_problems
    write = installer.write_staging_manifest
    replace = os.replace

    def observed_check(folder, *, full=False, manifest=None, **kwargs):
        if full:
            assert not (folder / "manifest.json").exists(), "manifest written before full verify"
            assert manifest is not None
            assert not (root / gpu_pack.STAMP).exists()
            yield from check(folder, full=True, manifest=manifest, **kwargs)
            events.append("full")
        else:
            assert events == ["full", "manifest"]
            assert (folder / "manifest.json").is_file()
            yield from check(folder, **kwargs)
            events.append("disk")

    def observed_write(folder, document):
        assert events == ["full"]
        result = write(folder, document)
        events.append("manifest")
        return result

    def observed_replace(source, destination):
        assert events == ["full", "manifest", "disk"]
        result = replace(source, destination)
        events.append("rename")
        return result

    monkeypatch.setattr(gpu_pack, "pack_problems", observed_check)
    monkeypatch.setattr(installer, "write_staging_manifest", observed_write)
    monkeypatch.setattr(os, "replace", observed_replace)
    result = installer.install(Progress())
    assert result.ok, result.message
    assert events == ["full", "manifest", "disk", "rename"]


def test_manifest_corruption_is_caught_by_the_disk_check(empty_plan, monkeypatch):
    installer, root = empty_plan
    write = installer.write_staging_manifest

    def corrupt(folder, document):
        path = write(folder, document)
        path.write_text("{}", encoding="utf-8")
        return path

    monkeypatch.setattr(installer, "write_staging_manifest", corrupt)
    result = installer.install(Progress())
    assert not result.ok and "manifest format" in result.message
    assert list(root.iterdir()) == []


def test_platform_without_a_pack_refuses_without_network(monkeypatch):
    monkeypatch.setattr(gpu_pack, "pack_root", lambda: None)
    result = _installer().install(Progress())
    assert not result.ok and result.message == "GPU support is not available on this platform"


@pytest.mark.parametrize(
    "url", ["http://files.pythonhosted.org/not-https", "https://pypi.org/not-the-locked-host"]
)
def test_production_origin_policy_refuses_an_untrusted_url_before_connect(
    empty_plan, monkeypatch, url
):
    installer, root = empty_plan
    monkeypatch.setattr(
        gpu_pack,
        "LOCKED_DISTRIBUTIONS",
        (
            gpu_pack.LockedDistribution(
                "synthetic", "1.0", (("synthetic-1.0-py3-none-any.whl", "0" * 64, url, 1),)
            ),
        ),
    )
    result = installer.install(Progress())
    assert not result.ok and "download URL refused" in result.message
    assert list(root.iterdir()) == []


def test_nested_package_data_installs(fake_index):
    fake_index.configure(nested_data=True)
    result = _installer().install(Progress())
    assert result.ok, result.message
    assert (
        result.path / "site-packages/synthetic0/.data/x"
    ).read_bytes() == b"ordinary package data"


@pytest.mark.parametrize("name", [d.name for d in gpu_pack.LOCKED_DISTRIBUTIONS])
def test_real_locked_record_member_names_are_allowed(tmp_path, name):
    try:
        distribution = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        pytest.skip(f"{name} is not installed in this environment")
    locked = next(d for d in gpu_pack.LOCKED_DISTRIBUTIONS if d.name == name)
    if distribution.version != locked.version:
        pytest.skip(f"{name}: installed {distribution.version}, locked {locked.version}")
    text = distribution.read_text("RECORD")
    assert text is not None
    for row in csv.reader(io.StringIO(text)):
        _installer()._member_path(tmp_path / "site-packages", zipfile.ZipInfo(row[0]))


def test_oversized_body_never_writes_past_locked_size_or_retries(fake_index, monkeypatch):
    installer = _installer()
    first = fake_index.distributions[0]
    filename, digest, url, _ = first.wheels[0]
    limit = 128
    monkeypatch.setattr(installer, "_CHUNK_SIZE", 64)
    monkeypatch.setattr(
        gpu_pack,
        "LOCKED_DISTRIBUTIONS",
        (
            gpu_pack.LockedDistribution(
                first.name, first.version, ((filename, digest, url, limit),)
            ),
        ),
    )
    sizes = []
    original_open = Path.open

    def observed_open(path, *args, **kwargs):
        handle = original_open(path, *args, **kwargs)
        if path.suffix != ".part":
            return handle

        class PartWriter:
            def __enter__(self):
                handle.__enter__()
                return self

            def __exit__(self, *exc):
                return handle.__exit__(*exc)

            def write(self, block):
                count = handle.write(block)
                sizes.append(handle.tell())
                return count

        return PartWriter()

    monkeypatch.setattr(Path, "open", observed_open)
    result = installer.install(Progress())
    assert not result.ok and "recorded hash" in result.message
    assert sizes and max(sizes) <= limit
    assert len(fake_index.requests) == 1
    assert list(fake_index.root.iterdir()) == []


def test_partial_file_is_skipped_and_logged(fake_index, caplog):
    stray = fake_index.root / "test-cu12.partial-x"
    stray.write_text("keep")
    assert _installer().install(Progress()).ok
    assert stray.read_text() == "keep"
    assert "partial" in caplog.text and "skip" in caplog.text
    assert _installer().remove().ok
    assert list(fake_index.root.iterdir()) == [stray]


@pytest.mark.parametrize("kind", ["symlink", "junction"])
def test_partial_link_is_never_followed(fake_index, tmp_path, kind, caplog):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep").write_bytes(b"untouched")
    link = fake_index.root / "test-cu12.partial-link"
    if kind == "junction":
        if sys.platform != "win32":
            pytest.skip("NTFS junctions require win32")
        import _winapi

        _winapi.CreateJunction(str(outside), str(link))
    else:
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            pytest.skip(f"host refuses os.symlink: {error!r}")
    try:
        assert _installer().install(Progress()).ok
        assert _installer().remove().ok
        assert link.exists() and (outside / "keep").read_bytes() == b"untouched"
        assert "skipping" in caplog.text
    finally:
        if kind == "junction":
            link.rmdir()
        else:
            link.unlink()


def _fake_pack(root):
    folder = root / gpu_pack.STAMP
    folder.mkdir(parents=True)
    (folder / "a_first.py").write_bytes(b"keep first")
    (folder / "z_locked.dll").write_bytes(b"keep locked")
    return folder


def _deny_pack_rename(monkeypatch, folder):
    replace = os.replace

    def denied(source, target):
        if Path(source) == folder:
            raise PermissionError("synthetic file in use")
        return replace(source, target)

    monkeypatch.setattr(os, "replace", denied)


def test_remove_renames_before_deleting(empty_plan, monkeypatch):
    installer, root = empty_plan
    folder = _fake_pack(root)
    replace = os.replace
    events = []

    def renamed(source, target):
        events.append("rename")
        assert Path(source) == folder
        assert Path(target).name.startswith(gpu_pack.STAMP + ".partial-")
        return replace(source, target)

    cleanup = installer._remove_tree

    def removed(parent, target):
        assert events == ["rename"] and not folder.exists()
        events.append("delete")
        return cleanup(parent, target)

    monkeypatch.setattr(os, "replace", renamed)
    monkeypatch.setattr(installer, "_remove_tree", removed)
    assert installer.remove().ok
    assert events == ["rename", "delete"]
    assert list(root.iterdir()) == []


def test_remove_in_use_defers_intact_and_is_idempotent(empty_plan, monkeypatch):
    installer, root = empty_plan
    folder = _fake_pack(root)
    _deny_pack_rename(monkeypatch, folder)
    monkeypatch.setattr(installer, "_pack_in_use", lambda _: True, raising=False)
    result = installer.remove()
    assert result.ok and result.message == "GPU support will be removed at the next start"
    assert (folder / "a_first.py").read_bytes() == b"keep first"
    assert (folder / "z_locked.dll").read_bytes() == b"keep locked"
    assert (root / (gpu_pack.STAMP + ".remove")).read_bytes() == b""
    monkeypatch.setattr(os, "replace", lambda *args: pytest.fail("second rename"))
    assert installer.remove() == result


@pytest.mark.skipif(sys.platform != "win32", reason="POSIX permits renaming open files")
def test_real_nonmapped_open_file_defers_remove_and_pending_install(empty_plan):
    installer, root = empty_plan
    folder = _fake_pack(root)
    with (folder / "z_locked.dll").open("rb"):
        assert installer.remove().message == "GPU support will be removed at the next start"
        assert (folder / "a_first.py").exists()
        result = installer.install(Progress())
        assert not result.ok and "close it and try again" in result.message
    assert installer.apply_pending_removal().ok
    assert list(root.iterdir()) == []


def test_pending_removal_retries_and_clears_marker(empty_plan, monkeypatch, caplog):
    installer, root = empty_plan
    folder = _fake_pack(root)
    marker = root / (gpu_pack.STAMP + ".remove")
    marker.touch()
    with monkeypatch.context() as patch:
        _deny_pack_rename(patch, folder)
        result = installer.apply_pending_removal()
        assert not result.ok and marker.exists()
        assert (folder / "a_first.py").exists()
        assert len(caplog.records) == 1
    assert installer.apply_pending_removal().ok
    assert list(root.iterdir()) == []


@pytest.mark.parametrize("in_use", [False, True])
def test_install_applies_pending_removal_before_network(fake_index, monkeypatch, in_use):
    installer = _installer()
    folder = _fake_pack(fake_index.root)
    marker = fake_index.root / (gpu_pack.STAMP + ".remove")
    marker.touch()
    if in_use:
        _deny_pack_rename(monkeypatch, folder)
    result = installer.install(Progress())
    assert result.ok != in_use
    if in_use:
        assert "close it and try again" in result.message
        assert fake_index.requests == [] and marker.exists()
        assert (folder / "a_first.py").exists()
    else:
        assert not marker.exists() and fake_index.requests
        assert gpu_pack.check_pack(folder) is None


@pytest.mark.parametrize("operation", ["install", "remove", "pending"])
def test_operation_lock_refuses_second_operation(empty_plan, monkeypatch, operation):
    installer, root = empty_plan
    folder = _fake_pack(root)
    marker = root / (gpu_pack.STAMP + ".remove")
    if operation == "pending":
        marker.touch()
    with installer._operation_lock(root):
        if operation == "install":
            result = installer.install(Progress())
        elif operation == "remove":
            result = installer.remove()
        else:
            result = installer.apply_pending_removal()
        assert not result.ok and result.message == "another GPU pack operation is in progress"
        assert (folder / "a_first.py").exists()
    assert not (root / ".install.lock").exists()


def test_stale_operation_lock_is_broken(empty_plan):
    installer, root = empty_plan
    root.mkdir()
    (root / ".install.lock").write_text("dead owner")
    assert installer.install(Progress()).ok
    assert not (root / ".install.lock").exists()


def test_cancel_during_full_check_cleans_without_manifest(fake_index, monkeypatch):
    installer = _installer()
    progress = Progress()
    digest = gpu_pack._file_digest
    hashes = []

    def cancelling(path):
        result = digest(path)
        # Manifest construction hashes RECORDs before the full listed-file walk.
        if Path(path).name != "RECORD":
            hashes.append(path)
            progress.cancel = True
        return result

    monkeypatch.setattr(gpu_pack, "_file_digest", cancelling)
    monkeypatch.setattr(
        installer, "write_staging_manifest", lambda *args: pytest.fail("manifest written")
    )
    result = installer.install(progress)
    assert not result.ok and result.cancelled
    assert len(hashes) == 1
    assert list(fake_index.root.iterdir()) == []


def test_unpack_reports_work_after_download(fake_index):
    progress = Progress()
    assert _installer().install(progress).ok
    assert any("Unpacking" in message for _, _, message in progress.reports)


def test_headless_replacement_notice(fake_index, headless_entry, capsys):
    _fake_pack(fake_index.root)
    assert headless_entry.main(["clearwater", "--install-gpu-pack"]) == 0
    assert (
        capsys.readouterr().err.splitlines()[0]
        == "An existing GPU pack is not usable and will be replaced"
    )


@pytest.mark.parametrize("operation", ["install", "remove"])
def test_headless_lock_refusal_exits_one(empty_plan, headless_entry, operation, capsys):
    installer, root = empty_plan
    with installer._operation_lock(root):
        assert headless_entry.main(["clearwater", f"--{operation}-gpu-pack"]) == 1
    assert capsys.readouterr().err.strip() == "another GPU pack operation is in progress"


@pytest.mark.parametrize("operation", ["remove", "pending", "install-marker", "replace"])
def test_write_open_probe_defers_before_any_rename(fake_index, monkeypatch, operation):
    installer = _installer()
    folder = _fake_pack(fake_index.root)
    marker = fake_index.root / (gpu_pack.STAMP + ".remove")
    if operation in ("pending", "install-marker"):
        marker.touch()
    original_open = os.open
    probes = []

    def in_use(path, flags, *args, **kwargs):
        if Path(path).suffix.lower() in (".dll", ".pyd"):
            probes.append((Path(path), flags))
            raise PermissionError("mapped image denies write-open")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", in_use)
    monkeypatch.setattr(os, "replace", lambda *args: pytest.fail("pack was renamed"))
    if operation == "remove":
        result = installer.remove()
        assert result.ok and result.message == "GPU support will be removed at the next start"
    elif operation == "pending":
        assert not installer.apply_pending_removal().ok
    else:
        result = installer.install(Progress())
        assert not result.ok and "close it and try again" in result.message
    assert probes == [(folder / "z_locked.dll", os.O_RDWR)]
    assert marker.read_bytes() == b""
    assert (folder / "a_first.py").read_bytes() == b"keep first"
    assert (folder / "z_locked.dll").read_bytes() == b"keep locked"
    assert fake_index.requests == []
    assert not list(fake_index.root.glob("*.partial-*"))


@pytest.mark.skipif(sys.platform != "win32", reason="The write-open probe is Windows only")
def test_probe_opens_both_image_extensions_without_writing(empty_plan, monkeypatch):
    installer, root = empty_plan
    folder = _fake_pack(root)
    (folder / "extension.PYD").write_bytes(b"extension")
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in folder.iterdir()}
    original_open = os.open
    probes = []

    def observed(path, flags, *args, **kwargs):
        fd = original_open(path, flags, *args, **kwargs)
        probes.append((Path(path).name, flags, fd))
        return fd

    monkeypatch.setattr(os, "open", observed)
    assert not installer._pack_in_use(folder)
    assert {name for name, _, _ in probes} == {"z_locked.dll", "extension.PYD"}
    assert all(flags == os.O_RDWR for _, flags, _ in probes)
    for _, _, fd in probes:
        with pytest.raises(OSError):
            os.fstat(fd)
    assert before == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in folder.iterdir()}


def test_no_image_probe_off_win32(empty_plan, monkeypatch):
    installer, root = empty_plan
    folder = _fake_pack(root)
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(os, "open", lambda *args, **kwargs: pytest.fail("write-open off win32"))
    assert not installer._pack_in_use(folder)


@pytest.mark.parametrize("operation", ["remove", "pending", "install-marker", "replace"])
def test_delete_race_defers_and_locked_partial_does_not_block_start(
    empty_plan, monkeypatch, caplog, operation
):
    installer, root = empty_plan
    folder = _fake_pack(root)
    cleanup = installer._remove_tree
    marker = root / (gpu_pack.STAMP + ".remove")
    if operation in ("pending", "install-marker"):
        marker.touch()

    def mapped_after_probe(parent, target):
        if ".partial-" in target.name:
            assert not folder.exists()
            raise PermissionError("image mapped after write-open probe")
        return cleanup(parent, target)

    with monkeypatch.context() as patch:
        patch.setattr(installer, "_remove_tree", mapped_after_probe)
        if operation == "remove":
            result = installer.remove()
            assert result.ok and result.message == "GPU support will be removed at the next start"
        elif operation == "pending":
            assert not installer.apply_pending_removal().ok
        else:
            result = installer.install(Progress())
            assert not result.ok and "close it and try again" in result.message
        assert marker.exists() and not folder.exists()
        assert len(list(root.glob("*.partial-*"))) == 1
        caplog.clear()
        assert installer.apply_pending_removal().ok
        assert not marker.exists()
        assert len(list(root.glob("*.partial-*"))) == 1
        assert len(caplog.records) == 1 and "partial" in caplog.text
    assert installer.remove().ok
    assert list(root.iterdir()) == []


def test_remove_retries_existing_marker_after_holder_exits(empty_plan):
    installer, root = empty_plan
    _fake_pack(root)
    (root / (gpu_pack.STAMP + ".remove")).touch()
    assert installer.remove().ok
    assert list(root.iterdir()) == []


def test_unreadable_partial_does_not_keep_absent_pack_marker(empty_plan, monkeypatch, caplog):
    installer, root = empty_plan
    root.mkdir()
    partial = root / (gpu_pack.STAMP + ".partial-unreadable")
    partial.mkdir()
    marker = root / (gpu_pack.STAMP + ".remove")
    marker.touch()
    original_lstat = Path.lstat

    def denied(path, *args, **kwargs):
        if path == partial:
            raise PermissionError("partial metadata unavailable")
        return original_lstat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", denied)
        assert installer.apply_pending_removal().ok
        assert not marker.exists() and partial.exists()
        assert len(caplog.records) == 1 and "partial" in caplog.text
    assert installer.remove().ok
    assert list(root.iterdir()) == []


def test_real_record_validator_skips_mismatched_environment(tmp_path, monkeypatch):
    name = gpu_pack.LOCKED_DISTRIBUTIONS[0].name
    stale = SimpleNamespace(version="0.0", read_text=lambda _: pytest.fail("stale RECORD read"))
    monkeypatch.setattr(importlib.metadata, "distribution", lambda _: stale)
    with pytest.raises(pytest.skip.Exception, match=r"installed 0\.0, locked"):
        test_real_locked_record_member_names_are_allowed(tmp_path, name)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows mapped-image sharing semantics")
@pytest.mark.parametrize("kind", ["dll", "pyd"])
def test_child_mapped_image_keeps_pack_intact_until_exit(empty_plan, tmp_path, kind):
    installer, root = empty_plan
    folder = _fake_pack(root)
    if kind == "dll":
        source = Path(sys.base_prefix) / "python3.dll"
        target = folder / "mapped.dll"
    else:
        source = Path(importlib.util.find_spec("_queue").origin)
        target = folder / "_queue.pyd"
    shutil.copy2(source, target)
    ready, release = tmp_path / "ready", tmp_path / "release"
    environment = os.environ.copy()
    for key in (
        "APPDATA",
        "LOCALAPPDATA",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
    ):
        environment[key] = str(tmp_path / key)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    code = r"""
import importlib.abc, importlib.util, sys, time
from pathlib import Path
class NoQt(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in ('PySide6', 'shiboken6') or name == 'clearwater.app.main':
            raise ImportError('Qt blocked in mapped-image child')
sys.meta_path.insert(0, NoQt())
kind, image, ready, release = sys.argv[1:]
if kind == 'dll':
    import ctypes
    mapped = ctypes.WinDLL(image)
else:
    spec = importlib.util.spec_from_file_location('_queue', image)
    mapped = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mapped)
Path(ready).touch()
deadline = time.monotonic() + 8
while not Path(release).exists():
    if time.monotonic() > deadline:
        raise SystemExit('mapped-image child timed out')
    time.sleep(0.02)
"""
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    with (tmp_path / "mapped-child.log").open("wb") as log:
        child = subprocess.Popen(
            [sys.executable, "-c", code, kind, str(target), str(ready), str(release)],
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            assert ready.exists(), "mapped-image child failed to become ready; see mapped-child.log"
            result = installer.remove()
            assert result.ok and result.message == "GPU support will be removed at the next start"
            marker = root / (gpu_pack.STAMP + ".remove")
            assert marker.read_bytes() == b""
            assert folder.is_dir() and not list(root.glob("*.partial-*"))
            assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
            assert not installer.apply_pending_removal().ok
            assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
            assert not installer.install(Progress()).ok
            assert {p.name: p.read_bytes() for p in folder.iterdir()} == before
        finally:
            release.touch()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)
        assert child.returncode == 0
    assert installer.apply_pending_removal().ok
    assert list(root.iterdir()) == []
