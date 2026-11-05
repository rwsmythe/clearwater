"""Offline release FFmpeg lock and synthetic archive checks (WP6.3b)."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import re
import urllib.request
from email.message import Message
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("wp63b_ffmpeg_build", ROOT / "tools/package/build.py")
assert spec is not None and spec.loader is not None
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
LOCK = ROOT / "tools/package/ffmpeg.lock.json"


def lock_data():
    return json.loads(LOCK.read_text(encoding="utf-8"))


def test_committed_lock_covers_the_verified_source_stages():
    """Missing pin records and unmapped library flags must fail validation."""
    assert LOCK.is_file(), "the verified FFmpeg lock is missing"
    data = lock_data()
    result = build.validate_ffmpeg_lock(data)
    assert result["version"] == "n9.0.2-39-g7adfbe40dc-20261031"
    assert len(result["components"]) == 98
    assert sum(c["pin_kind"] == "tag" for c in result["components"]) == 4
    assert sum(c["pin_kind"] == "svn-rev" for c in result["components"]) == 2
    nv = next(c for c in result["components"] if c["name"] == "ffnvcodec")
    assert nv["pin"] == "f2053071ea93137255b6dcf42e9b4c9e0965a44e"
    assert [r["status"] for r in nv["extra_repositories"]] == [
        "downloaded-not-built",
        "downloaded-not-built",
    ]


@pytest.mark.parametrize(
    "change",
    [
        "schema",
        "missing",
        "digest-length",
        "digest-mismatch",
        "missing-gpl",
        "missing-x265",
        "nonfree",
        "fdk",
        "extract",
        "duplicate-stage",
        "duplicate-name",
        "unmapped",
        "reverse-map",
        "major",
        "component-schema",
        "pin",
        "basis",
        "extra-source",
    ],
)
def test_lock_rejects_inconsistent_or_unsafe_data(change):
    data = copy.deepcopy(lock_data())
    if change == "schema":
        data["schema_version"] = 2
    elif change == "missing":
        del data["provider"]
    elif change == "digest-length":
        data["github_sha256"] = data["seat_sha256"] = "123"
    elif change == "digest-mismatch":
        data["seat_sha256"] = "0" * 64
    elif change == "missing-gpl":
        data["configure_line"] = data["configure_line"].replace("--enable-gpl", "--disable-gpl")
    elif change == "missing-x265":
        data["configure_line"] = data["configure_line"].replace("--enable-libx265", "")
    elif change in {"nonfree", "fdk", "unmapped"}:
        data["configure_line"] += (
            " --enable-"
            + {"nonfree": "nonfree", "fdk": "libfdk-aac", "unmapped": "new-external"}[change]
        )
    elif change == "extract":
        data["extract_members"].append("bin/ffplay.exe")
    elif change in {"duplicate-stage", "duplicate-name"}:
        field = change.removeprefix("duplicate-")
        data["components"][1][field] = data["components"][0][field]
    elif change == "reverse-map":
        data["components"][0]["configure_flag"] = ["--enable-missing"]
    elif change == "major":
        data["version"] = "n8.0.2-39-g7adfbe40dc-20261031"
    elif change == "component-schema":
        del data["components"][0]["repository"]
    elif change == "pin":
        data["components"][0]["pin"] = "moving-branch"
    elif change == "basis":
        data["components"][0]["licence"] = None
        data["components"][0]["licence_basis"] = "cell-read"
    elif change == "extra-source":
        data["components"][0]["extra_repositories"] = [{"repository": "https://example.invalid"}]
    with pytest.raises(ValueError):
        build.validate_ffmpeg_lock(data)


@pytest.fixture
def synthetic_bundle(tmp_path, monkeypatch):
    """Use real ZIP/file transport and Python tool stubs, never a real binary."""
    import os
    import subprocess
    import sys
    import zipfile

    data = lock_data()
    source = tmp_path / data["asset_name"]
    root = data["archive_root"]
    members = {}
    for tool in ("ffmpeg", "ffprobe"):
        script = (
            "import json, os, sys\nfrom pathlib import Path\n"
            "Path('observed-' + Path(__file__).stem + '.json').write_text(json.dumps({"
            "'path': os.environ['PATH'], 'cwd': os.getcwd(), 'args': sys.argv[1:]}))\n"
            f"print({tool + ' version ' + data['version'] + ' Copyright test'!r})\n"
            f"print({data['configure_line']!r})\n"
        )
        members[root + "/bin/" + tool + ".exe"] = script.encode()
    members[root + "/LICENSE.txt"] = b"synthetic GPL-3.0 text\n"
    members[root + "/bin/ffplay.exe"] = b"do not extract"
    members[root + "/doc/extra.txt"] = b"do not extract"
    pin = tmp_path / "test-lock.json"
    destination = tmp_path / "release"
    destination.mkdir()
    out = tmp_path / "out"

    def write(extra=(), omit=()):
        with zipfile.ZipFile(source, "w") as archive:
            for name, payload in members.items():
                if name not in omit:
                    archive.writestr(name, payload)
            for name, payload in extra:
                if isinstance(name, str) and "\\" in name:
                    info = zipfile.ZipInfo(name)
                    info.filename = name  # retain raw backslashes; Windows ZipInfo normalizes them
                    name = info
                archive.writestr(name, payload)
        data["size_bytes"] = source.stat().st_size
        data["github_sha256"] = data["seat_sha256"] = hashlib.sha256(
            source.read_bytes()
        ).hexdigest()
        data["asset_url"] = source.as_uri()
        pin.write_text(json.dumps(data), encoding="utf-8")

    # Windows cannot execute a text .exe. Only replace the native loader boundary;
    # the scripts run in a real bounded child with the production cwd/env/options.
    real_run = subprocess.run

    def launch(args, **kwargs):
        assert args[1:] == ["-version"]
        assert kwargs["env"]["PATH"] == str(destination)
        assert Path(kwargs["cwd"]) == destination
        assert kwargs["timeout"] <= 120
        assert kwargs["stdin"] == subprocess.DEVNULL
        if os.name == "nt":
            assert kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW
        return real_run([sys.executable, *args], **kwargs)

    monkeypatch.setattr(build, "FFMPEG_LOCK_PATH", pin, raising=False)
    monkeypatch.setattr(build, "_TEST_ALLOW_FILE_URLS", True, raising=False)
    monkeypatch.setattr(build.subprocess, "run", launch)
    write()
    return data, source, destination, out, members, write, pin


def bundle(fixture, **kwargs):
    data, _source, destination, out, *_ = fixture
    return build.bundle_ffmpeg(
        destination,
        out=out,
        url=kwargs.get("url", data["asset_url"]),
        sha256=kwargs.get("sha256", data["github_sha256"]),
    )


def test_local_file_bundle_checks_both_tools_and_extracts_only_release_files(synthetic_bundle):
    data, source, destination, out, *_ = synthetic_bundle
    result = bundle(synthetic_bundle)
    assert [path.name for path, line in result] == ["ffmpeg.exe", "ffprobe.exe"]
    for tool in ("ffmpeg", "ffprobe"):
        seen = json.loads((destination / f"observed-{tool}.json").read_text())
        assert seen == {"path": str(destination), "cwd": str(destination), "args": ["-version"]}
        assert (destination / f"{tool}.exe").is_file()
    assert (destination / "ffmpeg-LICENSE.txt").read_bytes() == b"synthetic GPL-3.0 text\n"
    assert not (destination / "ffplay.exe").exists()
    assert not (destination / data["archive_root"]).exists()
    assert (out / "ffmpeg" / source.name).read_bytes() == source.read_bytes()
    text = (destination / "ffmpeg-BUILD.txt").read_text(encoding="utf-8")
    for field in (
        "provider",
        "release_tag",
        "asset_name",
        "github_sha256",
        "version",
        "configure_line",
        "build_repository_commit",
        "source_record_url",
    ):
        assert data[field] in text


@pytest.mark.parametrize("kind", ["argument", "lock", "download"])
def test_hash_mismatch_fails_before_any_extraction_or_execution(synthetic_bundle, kind):
    data, source, destination, _out, _members, _write, pin = synthetic_bundle
    actual = data["github_sha256"]
    if kind == "lock":
        data["github_sha256"] = data["seat_sha256"] = "0" * 64
        pin.write_text(json.dumps(data), encoding="utf-8")
    if kind == "download":
        payload = source.read_bytes()
        source.write_bytes(payload[:-1] + bytes([payload[-1] ^ 1]))
    with pytest.raises(ValueError, match="sha256"):
        bundle(synthetic_bundle, sha256="0" * 64 if kind == "argument" else actual)
    assert list(destination.iterdir()) == []


@pytest.mark.parametrize(
    "name",
    [
        "../escape.exe",
        "/absolute.exe",
        "C:/escape.exe",
        "C:relative.exe",
        "root/../escape.exe",
        "root\\escape.exe",
        "root/file:ads",
        "root/trailing. ",
    ],
)
def test_unsafe_archive_members_fail_before_writing(synthetic_bundle, name):
    *_, write, _pin = synthetic_bundle
    write(extra=[(name, b"unsafe")])
    with pytest.raises(ValueError, match="unsafe"):
        bundle(synthetic_bundle)
    assert list(synthetic_bundle[2].iterdir()) == []


def test_zip_symlink_is_refused(synthetic_bundle):
    import stat
    import zipfile

    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    synthetic_bundle[5](extra=[(info, b"bin/ffmpeg.exe")])
    with pytest.raises(ValueError, match="unsafe"):
        bundle(synthetic_bundle)
    assert list(synthetic_bundle[2].iterdir()) == []


@pytest.mark.parametrize("kind", ["missing", "duplicate", "case-duplicate"])
def test_missing_or_duplicate_members_fail_before_writing(synthetic_bundle, kind):
    data, _source, destination, _out, members, write, _pin = synthetic_bundle
    name = data["archive_root"] + "/bin/ffmpeg.exe"
    if kind == "missing":
        write(omit=[name])
    else:
        duplicate = name if kind == "duplicate" else name.upper()
        if kind == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate name"):
                write(extra=[(duplicate, members[name])])
        else:
            write(extra=[(duplicate, members[name])])
    with pytest.raises(ValueError, match=r"missing|duplicate"):
        bundle(synthetic_bundle)
    assert list(destination.iterdir()) == []


@pytest.mark.parametrize("tool", ["ffmpeg", "ffprobe"])
@pytest.mark.parametrize("kind", ["version", "configuration", "nonzero"])
def test_tool_output_must_match_the_pin(synthetic_bundle, tool, kind):
    data, _source, _destination, _out, members, write, _pin = synthetic_bundle
    name = data["archive_root"] + f"/bin/{tool}.exe"
    script = members[name]
    if kind == "version":
        script = script.replace(data["version"].encode(), b"n9.0.2-other")
    elif kind == "configuration":
        script = script.replace(b"--enable-libx265", b"--disable-libx265")
    else:
        script += b"raise SystemExit(3)\n"
    members[name] = script
    write()
    with pytest.raises(RuntimeError, match=r"version|configuration|exit"):
        bundle(synthetic_bundle)


def test_fetch_refuses_an_unpinned_url_before_opening_it(synthetic_bundle):
    with pytest.raises(ValueError, match="URL"):
        bundle(synthetic_bundle, url="https://example.invalid/never-fetch.zip")
    assert list(synthetic_bundle[2].iterdir()) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pin_kind", []),
        ("pin_kind", None),
        ("extra_repositories", "bad"),
        ("configure_flag", "--enable-libx265"),
        ("licence", 42),
    ],
)
def test_malformed_component_types_are_validation_errors(field, value):
    data = lock_data()
    data["components"][0][field] = value
    with pytest.raises(ValueError):
        build.validate_ffmpeg_lock(data)


@pytest.mark.parametrize("failure", ["timeout", "oserror"])
def test_a_tool_that_cannot_finish_is_a_bundle_failure(synthetic_bundle, monkeypatch, failure):
    import subprocess

    def blocked(*args, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args[0], 120)
        raise OSError("synthetic loader refusal")

    monkeypatch.setattr(build.subprocess, "run", blocked)
    with pytest.raises(RuntimeError, match="did not run"):
        bundle(synthetic_bundle)


def test_short_archive_is_rejected_without_extraction(synthetic_bundle):
    _data, source, destination, _out, _members, _write, _pin = synthetic_bundle
    source.write_bytes(source.read_bytes()[:10])
    with pytest.raises(ValueError, match="sha256"):
        bundle(synthetic_bundle)
    assert list(destination.iterdir()) == []


def test_lock_records_seat_verified_licences_and_preserves_the_zvbi_stop():
    data = build.validate_ffmpeg_lock(lock_data())
    sources = [source for c in data["components"] for source in (c, *c["extra_repositories"])]
    assert len(sources) == 103
    for source in sources:
        assert source["licence"]
        assert source["licence_basis"] == "seat-verified"
        assert source["gpl3_compatible"] in {"yes", "no"}
        assert source["licence_note"]
    bad = [c["name"] for c in data["components"] if c["gpl3_compatible"] == "no"]
    assert bad == ["zvbi"]


@pytest.mark.parametrize("slot", ["primary", "extra"])
@pytest.mark.parametrize("change", ["null", "unverified", "cell-read", "missing-compatible"])
def test_lock_refuses_unverified_licences_even_on_extra_repositories(slot, change):
    data = lock_data()
    row = (
        data["components"][0]
        if slot == "primary"
        else next(c["extra_repositories"][0] for c in data["components"] if c["extra_repositories"])
    )
    if change == "null":
        row["licence"] = None
        row["licence_basis"] = "UNVERIFIED"
    elif change in {"unverified", "cell-read"}:
        row["licence_basis"] = "UNVERIFIED" if change == "unverified" else change
    else:
        row.pop("gpl3_compatible", None)
    with pytest.raises(ValueError):
        build.validate_ffmpeg_lock(data)


def test_lock_accepts_incompatibility_as_data_for_the_release_refusal():
    data = lock_data()
    for component in data["components"]:
        for source in (component, *component["extra_repositories"]):
            source["licence_basis"] = "seat-verified"
            source["gpl3_compatible"] = "no"
            source["licence_note"] = "synthetic incompatible licence"
    assert build.validate_ffmpeg_lock(data)["components"][0]["gpl3_compatible"] == "no"


def test_lock_refuses_http_asset_url():
    data = lock_data()
    data["asset_url"] = data["asset_url"].replace("https:", "http:", 1)
    with pytest.raises(ValueError, match="HTTPS"):
        build.validate_ffmpeg_lock(data)


def test_local_file_transport_needs_explicit_test_hook(synthetic_bundle, monkeypatch):
    monkeypatch.setattr(build, "_TEST_ALLOW_FILE_URLS", False, raising=False)
    with pytest.raises(ValueError, match="HTTPS"):
        bundle(synthetic_bundle)


def test_cli_refuses_file_url_even_when_test_hook_enabled(monkeypatch):
    monkeypatch.setattr(build, "_TEST_ALLOW_FILE_URLS", True, raising=False)
    with pytest.raises(SystemExit) as caught:
        build.parse_args(
            [
                "--form",
                "onedir",
                "--ffmpeg-from",
                "file:///fixture.zip",
                "--ffmpeg-sha256",
                "a" * 64,
            ]
        )
    assert caught.value.code == 2


def _scripted_transport(monkeypatch, redirects):
    """Drive urllib's real redirect machinery entirely in-process, without sockets."""
    from urllib.response import addinfourl

    payload = b"scripted hash-verified archive"
    requests = []
    real_build_opener = urllib.request.build_opener

    class Scripted(urllib.request.BaseHandler):
        handler_order = 100

        def https_open(self, request):
            url = request.full_url
            requests.append(url)
            headers = Message()
            if url in redirects:
                headers["Location"] = redirects[url]
                response = addinfourl(io.BytesIO(b""), headers, url, 302)
                response.msg = "Found"
            else:
                response = addinfourl(io.BytesIO(payload), headers, url, 200)
                response.msg = "OK"
            return response

        http_open = https_open

    monkeypatch.setattr(
        build.urllib.request,
        "build_opener",
        lambda *handlers: real_build_opener(Scripted(), *handlers),
    )
    # HEAD's urlopen path is also intercepted, so the RED never contacts a host.
    monkeypatch.setattr(
        build.urllib.request,
        "urlopen",
        lambda url, **kwargs: real_build_opener(Scripted()).open(url, **kwargs),
    )
    pin = lock_data()
    pin["size_bytes"] = len(payload)
    pin["github_sha256"] = pin["seat_sha256"] = hashlib.sha256(payload).hexdigest()
    return pin, payload, requests


@pytest.mark.parametrize(
    "destination",
    [
        "https://elsewhere.invalid/archive.zip",
        "http://github.com/archive.zip",
        "https://github.com:444/archive.zip",
    ],
)
def test_download_refuses_redirect_host_or_scheme(monkeypatch, tmp_path, destination):
    start = lock_data()["asset_url"]
    pin, _payload, requests = _scripted_transport(monkeypatch, {start: destination})
    with pytest.raises(ValueError, match="redirect.*" + re.escape(destination)):
        build._download_ffmpeg(start, pin["github_sha256"], tmp_path, pin)
    assert requests == [start]
    assert not list(tmp_path.rglob("*.part"))


def test_download_accepts_https_github_asset_redirect_chain(monkeypatch, tmp_path):
    start = lock_data()["asset_url"]
    middle = "https://objects.githubusercontent.com/fixture"
    end = "https://release-assets.githubusercontent.com/fixture.zip"
    pin, payload, requests = _scripted_transport(monkeypatch, {start: middle, middle: end})
    result = build._download_ffmpeg(start, pin["github_sha256"], tmp_path, pin)
    assert result.read_bytes() == payload
    assert requests == [start, middle, end]


def test_loopback_redirect_to_another_origin_is_refused_in_process():
    """The handler sees a loopback 302 without opening a socket or following it."""
    request = urllib.request.Request("http://127.0.0.1:54321/archive.zip")
    with pytest.raises(ValueError, match=r"redirect.*https://elsewhere.invalid"):
        build._FFmpegRedirectHandler().redirect_request(
            request, None, 302, "Found", Message(), "https://elsewhere.invalid/archive.zip"
        )
