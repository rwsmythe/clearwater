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


@pytest.mark.parametrize(
    ("field", "value", "refusal"),
    [
        # Removing the ref guard used to survive the entire test module.
        ("ffmpeg_ref", "master", "FFmpeg ref must be release/9.0"),
        ("ffmpeg_ref", "n9.0.2", "FFmpeg ref must be release/9.0"),
        # re.match instead of fullmatch used to accept trailing version junk.
        ("version", "n9.0.2-47-gb204e94e90-20261106-extra", "version hash differs"),
        # Removing the combined-licence guard used to survive all tests.
        ("licence", "MIT", "combined build must be GPL-3.0-or-later"),
        # Removing the full build-commit guard used to survive all tests.
        ("build_repository_commit", "d77b8352", "invalid build repository commit"),
        # Removing the archive-name guard used to survive all tests.
        ("asset_name", "other.zip", "asset name must match archive_root"),
        ("provider", "evil/x", "asset URL must match provider/release/asset"),
        ("asset_url", "https://example.org/other.zip", "asset URL must match"),
        (
            "asset_url",
            "https://github.com/evil/x/releases/download/tag/other.zip",
            "asset URL must match",
        ),
        (
            "source_record_url",
            "https://github.com/evil/x/tree/" + "0" * 40,
            "source record URL must match",
        ),
        (
            "source_record_url",
            "https://github.com/rwsmythe/FFmpeg-Builds/tree/" + "0" * 40,
            "source record URL must match",
        ),
    ],
)
def test_b_review_provenance_and_guard_mutations(field, value, refusal):
    """The B-r1 mutations must reach their named guard, not a later refusal."""
    data = lock_data()
    data[field] = value
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data)


@pytest.mark.parametrize(
    "change", ["release-ffmpeg", "release-fork", "zvbi-missing", "zvbi-built", "date"]
)
def test_lock_cross_binds_release_exclusion_and_build_date(change):
    """A byte pin must not conceal inconsistent source or exclusion claims."""
    data = lock_data()
    if change.startswith("release-"):
        prefix = (
            data["ffmpeg_commit"][:8]
            if change == "release-ffmpeg"
            else data["build_repository_commit"][:7]
        )
        data["release_tag"] = data["release_tag"].replace(prefix, "0" * len(prefix))
        data["asset_url"] = (
            f"https://github.com/{data['provider']}/releases/download/{data['release_tag']}/{data['asset_name']}"
        )
        refusal = "release tag must name FFmpeg and build commits"
    elif change == "zvbi-missing":
        data["excluded"] = [r for r in data["excluded"] if r["stage"] != "scripts.d/50-zvbi.sh"]
        refusal = "zvbi must be present only in excluded"
    elif change == "zvbi-built":
        row = copy.deepcopy(data["components"][0])
        row.update(stage="scripts.d/50-zvbi.sh", name="zvbi", configure_flag=None)
        data["components"].append(row)
        refusal = "zvbi must be present only in excluded"
    else:
        data["version"] = data["version"].replace("20261106", "20261107")
        refusal = "version date must match --extra-version"
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data)


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ("missing-toolchain", "invalid document fields"),
        ("missing-runtime", "invalid document fields"),
        ("toolchain-fields", "invalid toolchain fields"),
        ("gcc-fields", "invalid toolchain gcc fields"),
        ("rust-fields", "invalid toolchain rustc fields"),
        ("toolchain-commit", "invalid toolchain rustc commit"),
        ("flags-type", "invalid static_link_flags"),
        ("flags-unknown", "invalid static_link_flags"),
        ("runtime-type", "toolchain_runtime must be a list"),
        ("row-fields", "invalid toolchain runtime fields"),
        ("kind", "invalid runtime kind"),
        ("via", "invalid runtime reached_via"),
        ("pin-kind", "invalid runtime pin_kind"),
        ("pin-length", "invalid runtime pin"),
        ("commit-length", "invalid runtime pin"),
        ("basis", "invalid runtime basis"),
        ("no", "runtime gpl3_compatible must be yes"),
        ("stop", "runtime gpl3_compatible must be yes"),
        ("chosen", "invalid runtime chosen licence"),
        ("chosen-no-or", "invalid runtime chosen licence"),
        ("duplicate", "duplicate toolchain runtime"),
        ("crate-commit", "cargo-crate requires crate-sha256"),
        ("crate-source", "cargo-crate source_url differs"),
        ("missing-rav1e", "rav1e requires cargo-crate and rust-std"),
        ("missing-librsvg", "librsvg requires cargo-crate and rust-std"),
        ("missing-std", "rav1e requires cargo-crate and rust-std"),
        ("absent-rav1e", "runtime stage rav1e is not enabled"),
        ("absent-librsvg", "runtime stage librsvg is not enabled"),
        ("missing-libgcc", "static flags require gcc-runtime libgcc"),
        ("missing-libstdc++", "static flags require gcc-runtime libstdc++"),
        ("missing-libgomp", "static flags require gcc-runtime libgomp"),
        ("rust-pin", "rust-std pin differs from toolchain"),
        ("rust-version", "rust-std version differs from toolchain"),
        ("gcc-pin", "gcc-runtime pin/version differs from toolchain"),
        ("gcc-version", "gcc-runtime pin/version differs from toolchain"),
        ("texts-empty", "runtime texts must be nonempty"),
        ("text-fields", "invalid runtime text fields"),
        ("text-path", "unsafe runtime text path"),
        ("text-backslash", "unsafe runtime text path"),
        ("text-dotdot", "unsafe runtime text path"),
        ("text-hash", "invalid runtime text sha256"),
    ],
)
def test_runtime_census_refuses_missing_or_inconsistent_obligations(change, refusal):
    """Each mutation removes one required binding in the real runtime census."""
    data = lock_data()
    rows = data["toolchain_runtime"]
    crate = next(r for r in rows if r["kind"] == "cargo-crate")
    std = next(r for r in rows if r["name"] == "rust-std")
    gcc = next(r for r in rows if r["name"] == "libgcc")
    if change.startswith("missing-") and change[8:] in {"toolchain", "runtime"}:
        del data["toolchain" if change == "missing-toolchain" else "toolchain_runtime"]
    elif change == "toolchain-fields":
        data["toolchain"]["unexpected"] = True
    elif change in {"gcc-fields", "rust-fields"}:
        data["toolchain"]["gcc" if change == "gcc-fields" else "rustc"]["unexpected"] = True
    elif change == "toolchain-commit":
        data["toolchain"]["rustc"]["commit"] = "short"
    elif change == "flags-type":
        data["toolchain"]["static_link_flags"] = "-static-libgcc"
    elif change == "flags-unknown":
        data["toolchain"]["static_link_flags"].append("unknown")
    elif change == "runtime-type":
        data["toolchain_runtime"] = {}
    elif change == "row-fields":
        crate["unexpected"] = True
    elif change in {"kind", "via", "pin-kind", "basis", "chosen"}:
        crate[{"via": "reached_via", "pin-kind": "pin_kind"}.get(change, change)] = "unknown"
    elif change == "chosen-no-or":
        crate.update(licence="Apache-2.0", chosen="MIT")
    elif change in {"pin-length", "commit-length"}:
        (crate if change == "pin-length" else std)["pin"] = "short"
    elif change in {"no", "stop"}:
        crate["gpl3_compatible"] = change
    elif change == "duplicate":
        rows.append(copy.deepcopy(crate))
    elif change == "crate-commit":
        crate.update(pin_kind="commit", pin="a" * 40)
    elif change == "crate-source":
        crate["source_url"] = "https://static.crates.io/crates/other/other-1.crate"
    elif change in {"missing-rav1e", "missing-librsvg", "missing-std"}:
        data["toolchain_runtime"] = [
            r
            for r in rows
            if (
                r["kind"] != "rust-std"
                if change == "missing-std"
                else r["reached_via"] != change[8:]
            )
        ]
    elif change.startswith("absent-"):
        stage = change[7:]
        switch = "--enable-librav1e" if stage == "rav1e" else "--enable-librsvg"
        data["configure_line"] = data["configure_line"].replace(switch, "")
        data["components"] = [r for r in data["components"] if r["name"] != stage]
    elif change.startswith("missing-lib"):
        data["toolchain_runtime"] = [r for r in rows if r["name"] != change[8:]]
    elif change in {"rust-pin", "gcc-pin"}:
        (std if change == "rust-pin" else gcc)["pin"] = "a" * 40
    elif change in {"rust-version", "gcc-version"}:
        (std if change == "rust-version" else gcc)["version"] = "0.0.0"
    elif change == "texts-empty":
        crate["texts"] = []
    elif change == "text-fields":
        crate["texts"][0]["unexpected"] = True
    elif change.startswith("text-"):
        key, value = {
            "text-path": ("path", "../other"),
            "text-backslash": ("path", "other\\file"),
            "text-dotdot": ("path", "a..b"),
            "text-hash": ("sha256", "short"),
        }[change]
        crate["texts"][0][key] = value
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data)


@pytest.mark.parametrize(
    "expression",
    [
        "GPL-2.0-only",
        "MIT OR Unknown",
        "MIT AND GPL-2.0-only",
        "MIT WITH Unknown",
        "(MIT OR Apache-2.0",
        "MIT AND",
        "MIT Apache-2.0",
        "MIT / Apache-2.0",
        "()",
        "MIT OR OR MIT",
    ],
)
def test_runtime_licence_parser_refuses_unknown_atoms_and_invalid_grammar(expression):
    """A compatible marker cannot launder an unknown or malformed SPDX expression."""
    data = lock_data()
    data["toolchain_runtime"][0]["licence"] = expression
    with pytest.raises(ValueError, match="runtime licence expression"):
        build.validate_ffmpeg_lock(data)


@pytest.mark.parametrize(
    "expression",
    [
        "MIT",
        "(Apache-2.0 OR MIT) AND BSD-3-Clause",
        "MIT AND Apache-2.0 WITH LLVM-exception AND (MIT OR Apache-2.0)",
        "GPL-3.0-or-later WITH GCC-exception-3.1",
        "Unicode-3.0",
    ],
)
def test_runtime_licence_parser_accepts_ruled_compatible_expressions(expression):
    """WITH and parenthesized AND/OR expressions retain their SPDX meaning."""
    data = lock_data()
    data["toolchain_runtime"][0]["licence"] = expression
    assert build.validate_ffmpeg_lock(data) is data


def test_committed_lock_covers_the_verified_source_stages():
    """Missing pin records and unmapped library flags must fail validation."""
    assert LOCK.is_file(), "the verified FFmpeg lock is missing"
    data = lock_data()
    result = build.validate_ffmpeg_lock(data)
    assert result["schema_version"] == 2
    assert result["version"] == "n9.0.2-47-gb204e94e90-20261106"
    assert result["provider"] == "rwsmythe/FFmpeg-Builds"
    assert result["parent_provider"] == {
        "repository": "BtbN/FFmpeg-Builds",
        "commit": "5031c6f1082414e53688d39e521849905071070d",
    }
    assert result["ffmpeg_ref"] == "release/9.0"
    assert result["ffmpeg_commit"] == "b204e94e90fca64045e9ca7dd44c65678c7eb29e"
    assert "ffmpeg_tag" not in result
    assert len(result["components"]) == 97
    assert result["asset_url"].startswith(
        "https://github.com/rwsmythe/FFmpeg-Builds/releases/download/"
    )
    assert result["asset_name"] == result["archive_root"] + ".zip"
    flags = set(result["configure_line"].split())
    assert {
        "--disable-libzvbi",
        "--disable-libfdk-aac",
        "--enable-gpl",
        "--enable-libx265",
    } <= flags
    assert not {"--enable-libzvbi", "--enable-nonfree", "--enable-libfdk-aac"} & flags
    assert sum(c["pin_kind"] == "tag" for c in result["components"]) == 4
    assert sum(c["pin_kind"] == "svn-rev" for c in result["components"]) == 2
    nv = next(c for c in result["components"] if c["name"] == "ffnvcodec")
    assert nv["pin"] == "f2053071ea93137255b6dcf42e9b4c9e0965a44e"
    assert [r["status"] for r in nv["extra_repositories"]] == [
        "downloaded-not-built",
        "downloaded-not-built",
    ]


@pytest.mark.parametrize(
    ("change", "refusal"),
    [
        ("schema", "unsupported schema_version"),
        ("unknown", "invalid document fields"),
        ("ffmpeg-tag", "invalid document fields"),
        ("short-commit", "invalid FFmpeg commit"),
        ("uppercase-commit", "invalid FFmpeg commit"),
        ("version-commit", "version hash differs from the FFmpeg commit"),
        ("short-version-commit", "version hash differs from the FFmpeg commit"),
        ("double-version-commit", "version hash differs from the FFmpeg commit"),
        ("missing-disable-zvbi", "zvbi must be disabled"),
        ("enable-zvbi", "zvbi must be disabled"),
        ("parent-unknown", "invalid parent_provider fields"),
        ("parent-missing", "invalid parent_provider fields"),
        ("parent-repository", "invalid parent repository"),
        ("parent-short-commit", "invalid parent commit"),
        ("parent-uppercase-commit", "invalid parent commit"),
        ("missing", "invalid document fields"),
        ("digest-length", "sha256 readings differ or are not 64 hex digits"),
        ("digest-mismatch", "sha256 readings differ or are not 64 hex digits"),
        ("missing-gpl", "GPL, version3 and libx265 are required"),
        ("missing-x265", "GPL, version3 and libx265 are required"),
        ("nonfree", "nonfree or libfdk-aac is forbidden"),
        ("fdk", "nonfree or libfdk-aac is forbidden"),
        ("extract", "extract_members must name only the two tools and licence"),
        ("duplicate-stage", "duplicate component stage or name"),
        ("duplicate-name", "duplicate component stage or name"),
        ("unmapped", "configure coverage differs; unmapped="),
        ("reverse-map", "configure coverage differs; unmapped="),
        ("major", "FFmpeg major must be 9"),
        ("component-schema", "invalid component fields"),
        ("pin", "invalid source commit"),
        ("basis", "every licence must be seat-verified"),
        ("extra-source", "invalid extra source fields"),
    ],
)
def test_lock_rejects_inconsistent_or_unsafe_data(change, refusal):
    data = copy.deepcopy(lock_data())
    if change == "schema":
        data["schema_version"] = 1
    elif change == "unknown":
        data["unknown"] = "value"
    elif change == "ffmpeg-tag":
        data["ffmpeg_tag"] = "n9.0.2"
    elif change == "short-commit":
        data["ffmpeg_commit"] = data["ffmpeg_commit"][:10]
    elif change == "uppercase-commit":
        data["ffmpeg_commit"] = data["ffmpeg_commit"].upper()
    elif change in {"version-commit", "short-version-commit"}:
        data["version"] = (
            "n9.0.2-47-g"
            + ("0" * 10 if change == "version-commit" else data["ffmpeg_commit"][:6])
            + "-20261106"
        )
    elif change == "double-version-commit":
        data["version"] = data["version"].replace("-20261106", "-g0000000-20261106")
    elif change == "missing-disable-zvbi":
        data["configure_line"] = data["configure_line"].replace("--disable-libzvbi", "")
    elif change == "enable-zvbi":
        data["configure_line"] += " --enable-libzvbi"
        # Keep coverage valid so only the explicit zvbi guard refuses this lock.
        component = copy.deepcopy(data["components"][0])
        component.update(
            stage="scripts.d/50-zvbi.sh", name="zvbi", configure_flag=["--enable-libzvbi"]
        )
        data["components"].append(component)
        data["excluded"] = [
            row for row in data["excluded"] if row["stage"] != "scripts.d/50-zvbi.sh"
        ]
    elif change.startswith("parent-"):
        data["parent_provider"] = {
            "repository": "BtbN/FFmpeg-Builds",
            "commit": "5031c6f1082414e53688d39e521849905071070d",
        }
        if change == "parent-unknown":
            data["parent_provider"]["extra"] = "value"
        elif change == "parent-missing":
            del data["parent_provider"]["repository"]
        elif change == "parent-repository":
            data["parent_provider"]["repository"] = "evil/x"
        elif change == "parent-uppercase-commit":
            data["parent_provider"]["commit"] = data["parent_provider"]["commit"].upper()
        else:
            data["parent_provider"]["commit"] = "5031c6f1"
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
        data["components"][0]["licence_basis"] = "cell-read"
    elif change == "extra-source":
        data["components"][0]["extra_repositories"] = [{"repository": "https://example.invalid"}]
    with pytest.raises(ValueError, match=re.escape(refusal)):
        build.validate_ffmpeg_lock(data)


@pytest.mark.parametrize("length", [7, 10, 40])
def test_lock_version_accepts_only_a_matching_commit_prefix(length):
    """FFmpeg's printed abbreviation may vary, but it must identify the pinned commit."""
    data = lock_data()
    data["version"] = f"n9.0.2-47-g{data['ffmpeg_commit'][:length]}-20261106"
    assert build.validate_ffmpeg_lock(data) is data


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
            "print('Exiting with exit code 0')\n"
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


def test_lock_records_compatible_sources_and_explains_the_zvbi_exclusion():
    data = build.validate_ffmpeg_lock(lock_data())
    sources = [source for c in data["components"] for source in (c, *c["extra_repositories"])]
    assert len(sources) == 102
    for source in sources:
        assert source["licence"]
        assert source["licence_basis"] == "seat-verified"
        assert source["gpl3_compatible"] == "yes"
        assert source["licence_note"]
    assert not any(c["name"] == "zvbi" for c in data["components"])
    excluded = next(c for c in data["excluded"] if c["stage"] == "scripts.d/50-zvbi.sh")
    assert "GPL-2.0-only" in excluded["reason"]
    assert "src/packet-830.*" in excluded["reason"]
    assert "src/pdc.*" in excluded["reason"]
    assert data["build_repository_commit"] in excluded["reason"]


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


@pytest.mark.parametrize("slot", ["primary", "extra"])
def test_bundled_incompatible_source_is_still_refused_by_notices(
    synthetic_bundle, monkeypatch, slot
):
    """A schema-2 fork pin must not bypass notices' incompatible-source refusal."""
    data, _source, destination, _out, _members, write, pin = synthetic_bundle
    source = (
        data["components"][0]
        if slot == "primary"
        else next(
            extra
            for component in data["components"]
            for extra in component["extra_repositories"]
            if extra["status"] == "built"
        )
    )
    source["gpl3_compatible"] = "no"
    source["licence_note"] = "synthetic incompatible licence"
    write()
    bundle(synthetic_bundle)
    spec = importlib.util.spec_from_file_location(
        "wp63c_ffmpeg_notices", ROOT / "tools/package/notices.py"
    )
    assert spec is not None and spec.loader is not None
    notices = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(notices)
    monkeypatch.setattr(notices, "_build_tool", lambda: build)
    with pytest.raises(ValueError, match=r"FFmpeg GPL-3\.0-incompatible"):
        notices._ffmpeg_rows(destination, pin)


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
