"""Inventory coverage tests for artifact notices, using synthetic onedir releases."""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import marshal
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_RELEASE_SKIP = (
    "Windows native/interpreter fixture: the synthetic release copies python312.dll "
    "and writes Clearwater.exe (no macOS release fixture yet)"
)
VENV_SITE_PACKAGES = Path(sysconfig.get_path("purelib"))


@pytest.mark.parametrize("variable", ["PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE"])
def test_notices_refuses_python_environment_overrides(release, monkeypatch, variable):
    """The fixture resolver must not bypass rejection of inherited search overrides."""
    monkeypatch.setenv(variable, "foreign")
    with pytest.raises(ValueError, match=f"build environment: {variable} is set"):
        plan(load_notices(), release)


def test_notices_default_resolver_refuses_duplicate_locked_name(release, monkeypatch):
    """A foreign matching numpy dist-info on sys.path must fail before resolution."""
    foreign = release["folder"].parent / "foreign"
    installed(foreign, "numpy", "2.5.4", {"numpy/foreign.dll": "foreign"})
    monkeypatch.syspath_prepend(str(foreign))
    module = load_notices()
    kwargs = writer_kwargs(release)
    kwargs.pop("distribution")
    with pytest.raises(ValueError, match="resolves more than once"):
        module.write_notices(release["folder"], **kwargs)


@pytest.mark.parametrize(
    "relative",
    [
        "PyInstaller/utils.py",
        "PyInstaller/loader/pyimod_fake/utils.py",
        "PyInstaller/hooks/rthooks/pyi_rth_fake/utils.py",
    ],
)
def test_pyinstaller_ordinary_stems_cannot_claim_top_level_modules(release, relative):
    """A hook utility's basename must not license an unrelated bundled utils module."""
    utility = release["site"] / relative
    utility.parent.mkdir(parents=True, exist_ok=True)
    utility.write_text("")
    record = release["site"] / "pyinstaller-6.22.3.dist-info/RECORD"
    record.write_text(record.read_text() + f"{relative},,\n")
    make_executable(release["folder"], ["clearwater", "utils"])
    with pytest.raises(ValueError, match=r"unknown.*utils"):
        plan(load_notices(), release)


def native_surface_inputs(manifest):
    """Enumerate terms, full excerpt blobs and attribution inputs for Git checks."""
    found = set()
    for row in manifest["components"]:
        if "carried_notice" in row:
            continue
        found.add((row["text_file"], row["text_sha256"], row["text_size_bytes"]))
        for field in ("text_lines", "attribution"):
            if field in row:
                value = row[field]
                found.add((value["file"], value["sha256"], value["size_bytes"]))
    return sorted(found)


def test_native_licence_text_is_exempt_from_checkout_normalization():
    """A CRLF checkout must preserve the seat-verified licence's exact bytes."""
    folder = ROOT / "tools/package/native-licences"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    relatives = sorted(
        {
            (folder / name).relative_to(ROOT).as_posix()
            for name, _sha, _size in native_surface_inputs(manifest)
        }
    )
    result = subprocess.run(
        ["git", "check-attr", "text", "--", *relatives],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert result.stdout.splitlines() == [f"{relative}: text: unset" for relative in relatives]


def test_native_licence_manifest_hash_matches_committed_blob():
    """Check every working text and its HEAD blob, or read-only Git hash before commit."""
    folder = ROOT / "tools/package/native-licences"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    for name, sha256, size in native_surface_inputs(manifest):
        relative = (folder / name).relative_to(ROOT).as_posix()
        tracked = subprocess.run(
            ["git", "ls-tree", "HEAD", "--", relative],
            cwd=ROOT,
            capture_output=True,
            check=True,
            timeout=30,
        )
        result = subprocess.run(
            (
                ["git", "cat-file", "-p", f"HEAD:{relative}"]
                if tracked.stdout
                else ["git", "hash-object", "--", relative]
            ),
            cwd=ROOT,
            capture_output=True,
            check=True,
            timeout=30,
        )
        if tracked.stdout:
            assert hashlib.sha256(result.stdout).hexdigest() == sha256
        else:
            # Read-only Git hashing uses the actual attributes; compare with the
            # raw Git blob identity to catch checkout/filter byte conversion too.
            data = (folder / name).read_bytes()
            blob = b"blob " + str(len(data)).encode() + b"\0" + data
            assert result.stdout.decode().strip() == hashlib.sha1(blob).hexdigest()
        working_bytes = (folder / name).read_bytes()
        assert len(working_bytes) == size, relative
        assert hashlib.sha256(working_bytes).hexdigest() == sha256, relative


def load_notices():
    path = ROOT / "tools/package/notices.py"
    spec = importlib.util.spec_from_file_location("wp63b_notices_checks", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def installed(site, name, version, files):
    info = site / f"{name.replace('-', '_')}-{version}.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
    paths = []
    for relative, body in files.items():
        target = site / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        paths.append(relative)
    paths.extend(
        [str((info / "METADATA").relative_to(site)), str((info / "RECORD").relative_to(site))]
    )
    (info / "RECORD").write_text("".join(f"{name},,\n" for name in paths))
    return importlib.metadata.PathDistribution(info)


def make_executable(folder, modules):
    writers = pytest.importorskip("PyInstaller.archive.writers")
    sources = folder.parent / "archive-sources"
    sources.mkdir(exist_ok=True)
    script = sources / "module.pyc"
    script.write_bytes(
        importlib.util.MAGIC_NUMBER + bytes(12) + marshal.dumps(compile("", "m", "exec"))
    )
    pyz = sources / "PYZ.pyz"
    writers.ZlibArchiveWriter(
        str(pyz),
        [(name, str(sources / "m.py"), "PYMODULE") for name in modules],
        code_dict={name: compile("", name, "exec") for name in modules},
    )
    writers.CArchiveWriter(
        str(folder / "Clearwater.exe"),
        [
            ("pyimod01_archive", str(script), True, "m"),
            ("pyi_rth_inspect", str(script), True, "s"),
            ("__main__", str(script), True, "s"),
            ("PYZ.pyz", str(pyz), False, "z"),
        ],
        "python312.dll",
    )


@pytest.fixture
def release(tmp_path):
    if sys.platform != "win32":
        pytest.skip(WINDOWS_RELEASE_SKIP)
    native_surface = _make_native_surface(tmp_path / "release-native-licences")
    folder = tmp_path / "release"
    internal = folder / "_internal"
    (internal / "numpy/_core").mkdir(parents=True)
    (internal / "numpy/_core/test.pyd").write_bytes(b"synthetic native extension")
    shutil.copyfile(Path(sys.base_prefix) / "python312.dll", internal / "python312.dll")
    make_executable(folder, ["clearwater", "json", "numpy", "numpy.linalg"])
    site = tmp_path / "site"
    distributions = {
        "numpy": installed(
            site,
            "numpy",
            "2.5.4",
            {
                "numpy/__init__.py": "",
                "numpy/linalg/__init__.py": "",
                "numpy/_core/test.pyd": "synthetic native extension",
                "numpy-2.5.4.dist-info/licenses/LICENSE.txt": "synthetic BSD licence\n",
            },
        ),
        "pyinstaller": installed(
            site,
            "pyinstaller",
            "6.22.3",
            {
                "PyInstaller/loader/pyimod01_archive.py": "",
                "PyInstaller/hooks/rthooks/pyi_rth_inspect.py": "",
                "pyinstaller-6.22.3.dist-info/licenses/COPYING.txt": "synthetic COPYING\n",
            },
        ),
    }
    audit = tmp_path / "audit.md"
    audit.write_text(
        """# Synthetic notices
## Runtime dependency audit
| Component | Version | Licence | Verdict and required notice | Source / full text |
| --- | --- | --- | --- | --- |
| Python | 3.12.13 (outside lock) | PSF-2.0 | COMPATIBLE | [Source](https://python.org) |
| numpy | 2.5.4 | BSD-3-Clause | COMPATIBLE | [Source](https://github.com/numpy/numpy/tree/v2.5.4) |
### Native components and conditions
""",
        encoding="utf-8",
    )
    uv_lock = tmp_path / "uv.lock"
    uv_lock.write_text("""version = 1
[[package]]
name = "numpy"
version = "2.5.4"
[[package]]
name = "pyinstaller"
version = "6.22.3"
""")
    ffmpeg = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_text())
    ffmpeg["configure_line"] = (
        "configuration: --enable-gpl --enable-version3 --enable-libx265 "
        "--disable-libzvbi --extra-version=20261106"
    )
    ffmpeg["components"] = [next(c for c in ffmpeg["components"] if c["name"] == "x265")]
    ffmpeg["excluded"] = [r for r in ffmpeg["excluded"] if r["stage"] == "scripts.d/50-zvbi.sh"]
    ffmpeg["toolchain_runtime"] = [
        r for r in ffmpeg["toolchain_runtime"] if r["name"] in {"libgcc", "libstdc++"}
    ]
    ffmpeg["toolchain"]["static_link_flags"] = []
    ffmpeg_path = tmp_path / "ffmpeg.lock.json"
    ffmpeg_path.write_text(json.dumps(ffmpeg))
    return {
        "folder": folder,
        "site": site,
        "distributions": distributions,
        "audit": audit,
        "uv_lock": uv_lock,
        "ffmpeg": ffmpeg,
        "ffmpeg_path": ffmpeg_path,
        "native_surface": native_surface,
    }


def plan(module, release, **kwargs):
    kwargs.setdefault("native_licences_path", release["native_surface"])
    return module.plan_notices(
        release["folder"],
        audit_path=release["audit"],
        uv_lock_path=release["uv_lock"],
        ffmpeg_lock_path=release["ffmpeg_path"],
        distribution=release["distributions"].__getitem__,
        **kwargs,
    )


def add_ffmpeg(release):
    folder, pin = release["folder"], release["ffmpeg"]
    texts = release["native_surface"] / "ffmpeg-toolchain"
    texts.mkdir(exist_ok=True)
    for filename in {t["path"] for r in pin["toolchain_runtime"] for t in r["texts"]}:
        shutil.copyfile(
            ROOT / "tools/package/native-licences/ffmpeg-toolchain" / filename, texts / filename
        )
    texts = release["native_surface"] / "ffmpeg-components"
    texts.mkdir(exist_ok=True)
    for filename in {
        t["path"]
        for c in pin["components"]
        for r in (c, *c["extra_repositories"])
        for t in r.get("texts", [])
    }:
        shutil.copyfile(
            ROOT / "tools/package/native-licences/ffmpeg-components" / filename, texts / filename
        )
    for name in ["ffmpeg.exe", "ffprobe.exe"]:
        (folder / name).write_bytes(b"synthetic tool; never executed")
    (folder / "ffmpeg-LICENSE.txt").write_text("synthetic GPL-3.0 licence")
    (folder / "ffmpeg-BUILD.txt").write_text(
        "\n".join(
            [
                f"Provider: {pin['provider']}",
                f"Parent provider: {pin['parent_provider']['repository']} @ "
                f"{pin['parent_provider']['commit']}",
                f"Release tag: {pin['release_tag']}",
                f"Asset: {pin['asset_name']}",
                f"SHA256: {pin['github_sha256']}",
                f"FFmpeg version: {pin['version']}",
                f"FFmpeg commit: {pin['ffmpeg_commit']}",
                f"FFmpeg ref: {pin['ffmpeg_ref']}",
                f"Build repository commit: {pin['build_repository_commit']}",
                f"Per-component source recipes: {pin['source_record_url']}",
                pin["configure_line"],
                "",
            ]
        )
    )


def test_inventory_selects_only_bundled_rows_and_maps_each_entry(release):
    notices = load_notices()
    result = plan(notices, release)
    rows = {r.name: r for r in result.rows}
    assert set(rows) == {
        "Clearwater",
        "Python",
        "numpy",
        "PyInstaller bootloader",
        "PyInstaller run-time hooks",
    }
    assert "file:_internal/numpy/_core/test.pyd" in rows["numpy"].entries
    assert "pyz:numpy.linalg" in rows["numpy"].entries
    assert rows["PyInstaller bootloader"].licence == "GPL-2.0-or-later WITH Bootloader Exception"
    assert rows["PyInstaller run-time hooks"].licence == "Apache-2.0"
    assert all(r.entries for r in result.rows)
    assert all(r.verdict == "Redistributed in this artifact" for r in result.rows)
    notices.validate_coverage(result.entries, result.rows)
    assert any(
        "GPU pack" in statement and "user-obtained" in statement
        for statement in result.user_obtained
    )

    (release["folder"].parent / "coverage-plan.json").write_text(
        json.dumps(
            {
                "entries": result.entries,
                "rows": [
                    {
                        "name": row.name,
                        "version": row.version,
                        "licence": row.licence,
                        "entries": row.entries,
                    }
                    for row in result.rows
                ],
                "user_obtained": result.user_obtained,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_pyi_runtime_support_requires_explicit_record_module(release):
    """Runtime support owns only modules named by PyInstaller's fake-module RECORD."""
    module = load_notices()
    dist = release["distributions"]["pyinstaller"]
    record = dist._path / "RECORD"
    for relative in (
        "PyInstaller/fake-modules/_pyi_rth_utils/__init__.py",
        "PyInstaller/fake-modules/_pyi_rth_utils/qt.py",
    ):
        path = release["site"] / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
        with record.open("a") as stream:
            stream.write(relative + ",,\n")
    make_executable(release["folder"], ["_pyi_rth_utils", "_pyi_rth_utils.qt"])
    row = next(r for r in plan(module, release).rows if r.name == "PyInstaller run-time hooks")
    assert {"pyz:_pyi_rth_utils", "pyz:_pyi_rth_utils.qt"} <= set(row.entries)
    assert row.licence == "Apache-2.0"
    make_executable(release["folder"], ["_pyi_rogue"])
    with pytest.raises(ValueError, match="pyz:_pyi_rogue"):
        plan(module, release)


@pytest.mark.parametrize("kind", ["data", "binary", "module"])
def test_unknown_bundle_content_fails_even_inside_a_known_package(release, kind):
    notices = load_notices()
    if kind == "module":
        make_executable(release["folder"], ["numpy", "mystery_package"])
        unknown = "mystery_package"
    else:
        unknown = "unknown.dll" if kind == "binary" else "unknown.dat"
        (release["folder"] / "_internal/numpy" / unknown).write_bytes(b"unknown")
    with pytest.raises(ValueError, match=unknown.replace(".", r"\.")):
        plan(notices, release)


def test_a_row_claiming_an_absent_entry_fails_coverage(release):
    notices = load_notices()
    result = plan(notices, release)
    extra = result.rows[0]._replace(name="absent component", entries=("file:not-here.dll",))
    with pytest.raises(ValueError, match="absent component"):
        notices.validate_coverage(result.entries, (*result.rows, extra))


def test_wrong_locked_distribution_version_fails(release):
    notices = load_notices()
    release["uv_lock"].write_text(
        release["uv_lock"].read_text().replace('version = "2.5.4"', 'version = "2.5.3"')
    )
    with pytest.raises(ValueError, match=r"numpy.*version"):
        plan(notices, release)


@pytest.mark.parametrize("kind", ["licence", "source"])
def test_missing_required_material_fails(release, kind):
    notices = load_notices()
    if kind == "licence":
        (release["site"] / "numpy-2.5.4.dist-info/licenses/LICENSE.txt").unlink()
    else:
        release["audit"].write_text(
            release["audit"]
            .read_text()
            .replace("[Source](https://github.com/numpy/numpy/tree/v2.5.4)", "missing source")
        )
    with pytest.raises(ValueError, match=f"numpy.*{kind}"):
        plan(notices, release)


def test_ffmpeg_refusal_names_every_incompatible_repository_in_one_line(release):
    notices = load_notices()
    c = release["ffmpeg"]["components"][0]
    c["gpl3_compatible"] = "no"
    c["extra_repositories"] = [
        {
            "repository": "https://example.invalid/extra.git",
            "pin": "a" * 40,
            "pin_kind": "commit",
            "status": "built",
            "licence": "GPL-2.0-or-later",
            "licence_basis": "seat-verified",
            "licence_note": "synthetic conflict",
            "gpl3_compatible": "no",
            "texts": copy.deepcopy(c["texts"]),
            "chosen": None,
        }
    ]
    release["ffmpeg_path"].write_text(json.dumps(release["ffmpeg"]))
    add_ffmpeg(release)
    with pytest.raises(ValueError) as caught:
        plan(notices, release)
    text = str(caught.value)
    assert "x265" in text and "extra.git" in text
    assert len(text.splitlines()) == 1
    assert "GPL-3.0-incompatible" in text


def test_no_ffmpeg_never_emits_ffmpeg_rows_despite_the_same_incompatible_lock(release):
    notices = load_notices()
    release["ffmpeg"]["components"][0]["gpl3_compatible"] = "no"
    release["ffmpeg_path"].write_text(json.dumps(release["ffmpeg"]))
    result = plan(notices, release)
    assert not any(r.name.startswith("FFmpeg") for r in result.rows)
    assert any(
        "FFmpeg" in s and "user-obtained, not redistributed" in s for s in result.user_obtained
    )


def test_compatible_ffmpeg_rows_require_matching_build_provenance(release):
    notices = load_notices()
    add_ffmpeg(release)
    result = plan(notices, release)
    rows = {r.name: r for r in result.rows}
    assert "FFmpeg / ffprobe" in rows
    assert rows["FFmpeg component: x265"].sources == (
        "https://github.com/Multicorewareinc/x265.git @ 5143a2a00ad0cc600831654a248b96ec7307eb4a",
    )
    record = release["folder"] / "ffmpeg-BUILD.txt"
    record.write_text(record.read_text().replace(release["ffmpeg"]["version"], "wrong-version"))
    with pytest.raises(ValueError, match=r"FFmpeg.*provenance"):
        plan(notices, release)


@pytest.mark.parametrize("damage", ["missing", "hash", "orphan", "after-plan"])
def test_ffmpeg_component_text_integrity_uses_the_selected_surface(release, damage):
    """A component text may not disappear, drift, be orphaned or change after planning."""
    module = load_notices()
    add_ffmpeg(release)
    texts = release["native_surface"] / "ffmpeg-components"
    path = texts / release["ffmpeg"]["components"][0]["texts"][0]["path"]
    if damage == "after-plan":
        result = plan(module, release)
    if damage == "missing":
        path.unlink()
        refusal = "component text missing/unsafe"
    elif damage == "orphan":
        (texts / "orphan-LICENSE").write_bytes(b"orphan")
        refusal = "component text directory differs"
    else:
        path.write_bytes(path.read_bytes() + b"changed")
        refusal = (
            "component: x265.*text byte count differs"
            if damage == "after-plan"
            else "component text sha256 mismatch"
        )
    with pytest.raises(ValueError, match=refusal):
        if damage == "after-plan":
            module.render_notices(result)
        else:
            plan(module, release)


def test_root_annex_has_the_same_component_rows_and_text_hashes_as_artifacts(release):
    """A root annex must not omit a stage, an unbuilt download or a text reference."""
    module = load_notices()
    release["ffmpeg"] = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    release["ffmpeg_path"].write_text(json.dumps(release["ffmpeg"]))
    add_ffmpeg(release)
    result = plan(module, release)
    artifact = module.render_notices(result).decode("utf-8")
    root = module.render_root_annex().decode()
    assert "## FFmpeg build components and toolchain runtime census" in root
    assert (
        "[Build-component and toolchain-runtime annex]"
        "(#ffmpeg-build-components-and-toolchain-runtime-census)" in root
    )
    assert "(#ffmpeg-toolchain-runtime-census)" not in root
    rows = [r for r in result.rows if r.name.startswith("FFmpeg component:")]
    assert len(rows) == 105
    for row in rows:
        assert f"| {row.name} |" in artifact
        root_row = next(line for line in root.splitlines() if line.startswith(f"| {row.name} |"))
        for item in row.licence_inputs:
            links = re.findall(r"\(tools/package/native-licences/([^)]*)\)", root_row)
            assert any(
                hashlib.sha256(
                    (ROOT / "tools/package/native-licences" / link).read_bytes()
                ).hexdigest()
                == item.sha256
                for link in links
            )


def test_fork_ffmpeg_notices_render_all_built_sources_and_explain_exclusions(release):
    """The pin renders all 105 stage records with their own exact texts."""
    module = load_notices()
    release["ffmpeg"] = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_text())
    release["ffmpeg_path"].write_text(json.dumps(release["ffmpeg"]))
    add_ffmpeg(release)
    result = plan(module, release)
    rows = [row for row in result.rows if row.name.startswith("FFmpeg")]
    assert len(rows) == 338
    stage_rows = [r for r in rows if r.name.startswith("FFmpeg component:")]
    assert len(stage_rows) == 105
    sources = {}
    for component in release["ffmpeg"]["components"]:
        sources["FFmpeg component: " + component["name"]] = component
        for index, extra in enumerate(component["extra_repositories"], 2):
            sources[f"FFmpeg component: {component['name']} / repository {index}"] = extra
    for row in stage_rows:
        source = sources[row.name]
        assert {(t.path.name, t.sha256) for t in row.licence_inputs} == {
            (t["path"], t["sha256"]) for t in source["texts"]
        }
        assert all(t.path.parent.name == "ffmpeg-components" for t in row.licence_inputs)
    downloaded = [r for r in stage_rows if "Source status: downloaded-not-built" in r.notes]
    assert [r.name for r in downloaded] == [
        "FFmpeg component: ffnvcodec / repository 2",
        "FFmpeg component: ffnvcodec / repository 3",
    ]
    assert all(r.licence_inputs for r in downloaded)
    assert all(
        r.verdict == "Source fetched by the build; not compiled into this artifact "
        "(notice carried by over-inclusion)"
        for r in downloaded
    )
    assert next(r for r in stage_rows if r.name == "FFmpeg component: x265").verdict == (
        "Redistributed in this artifact"
    )
    assert rows[0].licence_inputs[0].path.name == "ffmpeg-LICENSE.txt"
    assert not any(row.name == "FFmpeg component: zvbi" for row in rows)
    rendered = module.render_notices(result)
    for item in {item for row in stage_rows for item in row.licence_inputs}:
        text = item.path.read_bytes()
        source = next(
            t for r in sources.values() for t in r["texts"] if t["path"] == item.path.name
        )
        if "encoding" in source:
            text = text.decode(source["encoding"]).encode("utf-8")
        assert text in rendered
        assert rendered.count(f"SHA-256: `{item.sha256}`".encode()) == 1
    output = rendered.decode("utf-8")
    encodings = {
        "openjpeg--src--bin--wx--OPJViewer--source--license.txt": "latin-1",
        "rav1e--PATENTS": "cp1252",
        "openmpt--include--premake--binmodules--luasocket--LICENSE": "cp1252",
    }
    declared = {
        t["path"]: t["encoding"] for r in sources.values() for t in r["texts"] if "encoding" in t
    }
    assert declared == encodings
    assert output.count("transcoded from ") == 3
    for name, encoding in encodings.items():
        raw = (release["native_surface"] / "ffmpeg-components" / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        note = f"transcoded from {encoding}; original file sha256 {digest}"
        assert f"Original SHA-256: `{digest}`. Original bytes: {len(raw)}." in output
        match = re.search(
            r"^### [^\n]*"
            + re.escape(name)
            + r"\n"
            + re.escape(note)
            + r"\n\nSource: [^\n]*\n\n(`{4,})text\n(.*?)^\1$",
            output,
            re.M | re.S,
        )
        assert match is not None, name
        body = match[2]
        if not raw.endswith(b"\n"):
            body = body.removesuffix("\n")
        assert body.encode(encoding) == raw
    assert output.count("### Bundled FFmpeg GPL-3.0") == 1
    assert output.count("synthetic GPL-3.0 licence") == 1
    assert "Provider: rwsmythe/FFmpeg-Builds @ d77b8352" in output
    assert (
        "built from BtbN's scripts at 5031c6f1 with the zvbi stage disabled; "
        "FFmpeg release/9.0 at b204e94e"
    ) in output
    assert (
        "Excluded scripts.d/50-zvbi.sh (not-built(disabled)): "
        "GPL-2.0-only src/packet-830.* / src/pdc.*" in output
    )
    assert "Build stage scripts.d/55-rustdedup.sh (BUILT):" in output
    assert "Build stage scripts.d/zz-final.sh (ENTRY):" in output
    assert 'owner ruling 2026-11-05 "self-build is fine"' in output
    excluded = (
        "Test-only DEPS not built (BtbN -DSHADERC_SKIP_TESTS=ON, "
        "-DSPIRV_SKIP_EXECUTABLES=ON): googletest 52eb8108 "
        "(shaderc third_party/CMakeLists.txt L28-30), abseil-cpp dbf88f93, "
        "re2 972a15ce, effcee f8e8a164 (shaderc third_party/CMakeLists.txt L50-70; "
        "SPIRV-Tools external/CMakeLists.txt L97-191, CMakeLists.txt L316-317)."
    )
    shaderc = sources["FFmpeg component: shaderc"]["licence_note"]
    assert shaderc.endswith(" " + excluded)
    assert shaderc in output
    assert shaderc in module.render_root_annex().decode("utf-8")
    assert not any(character in excluded for character in "|`<>[]\\\r\n")


def test_stage_only_notices_explain_representative_and_shared_text_labels():
    """Stage-only surfaces need the shared-label disclaimer even without runtimes."""
    module = load_notices()
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    entries = ("file:ffmpeg.exe",)
    rows = module._ffmpeg_component_rows(lock, entries, ROOT / "tools/package/native-licences")
    assert not any(r.name.startswith("FFmpeg toolchain runtime:") for r in rows)
    output = module.render_notices(module.NoticePlan(entries, tuple(rows), ())).decode("utf-8")
    assert (
        "FFmpeg build-component and toolchain-runtime texts are labelled with "
        "a representative file name from the census; byte-identical texts are "
        "shared across components, so a label may name another component's copy of the same text."
    ) in output


@pytest.mark.parametrize("slot", ["primary", "extra"])
@pytest.mark.parametrize("damage", ["missing", "empty"])
def test_component_row_renderer_refuses_missing_texts_without_validator(slot, damage):
    """A bypassed validator must not silently omit a stage or an extra source."""
    module = load_notices()
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    title = "FFmpeg component: mingw-std-threads"
    row = lock["components"][0]
    if slot == "extra":
        component = next(c for c in lock["components"] if c["extra_repositories"])
        row = component["extra_repositories"][0]
        title = f"FFmpeg component: {component['name']} / repository 2"
    if damage == "missing":
        row.pop("texts")
    else:
        row["texts"] = []
    with pytest.raises(ValueError, match=re.escape(title) + ".*missing component texts"):
        module._ffmpeg_component_rows(
            lock, ("file:ffmpeg.exe",), ROOT / "tools/package/native-licences"
        )


def test_whole_document_utf8_backstop_names_wheel_source_and_offset(release):
    """A future non-UTF-8 wheel licence must fail with its source and global offset."""
    module = load_notices()
    path = release["site"] / "numpy-2.5.4.dist-info/licenses/LICENSE.txt"
    good = b"wheel copyright ? holder\n"
    path.write_bytes(good)
    expected = module.render_notices(plan(module, release))
    offset = expected.index(good) + good.index(b"?")
    path.write_bytes(good.replace(b"?", b"\xa9"))
    with pytest.raises(
        ValueError,
        match=rf"not strict UTF-8 at byte offset {offset}; source: Installed wheel: numpy "
        r".*numpy-2.5.4.dist-info/licenses/LICENSE.txt",
    ):
        module.render_notices(plan(module, release))


def test_whole_document_utf8_backstop_names_runtime_source_and_offset(release):
    """Runtime byte/hash validation must not let unreadable terms reach the artifact."""
    module = load_notices()
    add_ffmpeg(release)
    text = release["ffmpeg"]["toolchain_runtime"][0]["texts"][0]
    path = release["native_surface"] / "ffmpeg-toolchain" / text["path"]
    good = b"runtime copyright ? holder\n"

    def replace(body):
        path.write_bytes(body)
        for row in release["ffmpeg"]["toolchain_runtime"]:
            for item in row["texts"]:
                if item["path"] == path.name:
                    item["sha256"] = hashlib.sha256(body).hexdigest()
        release["ffmpeg_path"].write_text(json.dumps(release["ffmpeg"]))

    replace(good)
    expected = module.render_notices(plan(module, release))
    offset = expected.index(good) + good.index(b"?")
    replace(good.replace(b"?", b"\xa9"))
    with pytest.raises(
        ValueError,
        match=rf"not strict UTF-8 at byte offset {offset}; source: FFmpeg toolchain runtime: "
        rf".*{re.escape(path.name)}",
    ):
        module.render_notices(plan(module, release))


def test_ffmpeg_toolchain_census_renders_every_row_and_deduplicates_terms(release):
    """Dropping a runtime row or duplicating shared full texts loses census coverage."""
    module = load_notices()
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    release["ffmpeg"] = lock
    release["ffmpeg_path"].write_text(json.dumps(lock))
    add_ffmpeg(release)
    rows = module._ffmpeg_rows(release["folder"], release["ffmpeg_path"])
    runtime = [r for r in rows if r.name.startswith("FFmpeg toolchain runtime:")]
    assert len(runtime) == 232
    rendered = module.render_notices(module.NoticePlan(rows[0].entries, tuple(rows), ()))
    runtime_only = module.render_notices(module.NoticePlan(rows[0].entries, tuple(runtime), ()))
    # The root links byte-preserved inputs rather than copying them into a
    # Markdown file whose line endings Git changes on Windows checkout.
    root_annex = (
        (ROOT / "THIRD_PARTY_NOTICES.md")
        .read_text(encoding="utf-8")
        .split("<!-- WP6.3c generated FFmpeg toolchain runtime census -->", 1)[1]
    )
    artifact = runtime_only.decode().replace("\r\n", "\n")
    root_table = [
        line.rsplit("|", 2)[0]
        for line in root_annex.splitlines()
        if line.startswith("| FFmpeg toolchain runtime:")
    ]
    artifact_table = [
        line.rsplit("|", 2)[0]
        for line in artifact.splitlines()
        if line.startswith("| FFmpeg toolchain runtime:")
    ]
    assert root_table == artifact_table
    # Artifact anchors name deduplicated text blocks; root links name the exact
    # byte-preserved files. Compare per-row sets through the block SHA-256.
    files_by_hash = {t["sha256"]: t["path"] for r in lock["toolchain_runtime"] for t in r["texts"]}
    files_by_anchor = {
        anchor: files_by_hash[digest]
        for anchor, digest in re.findall(
            r'<a id="(licence-\d+)"></a>.*?SHA-256: `([a-f0-9]{64})`', artifact, re.S
        )
    }
    root_texts = [
        set(re.findall(r"\(tools/package/native-licences/ffmpeg-toolchain/([^)]*)\)", line))
        for line in root_annex.splitlines()
        if line.startswith("| FFmpeg toolchain runtime:")
    ]
    artifact_texts = [
        {files_by_anchor[anchor] for anchor in re.findall(r"\(#(licence-\d+)\)", line)}
        for line in artifact.splitlines()
        if line.startswith("| FFmpeg toolchain runtime:")
    ]
    assert root_texts == artifact_texts
    details = "## Component details and coverage\n"
    root_details = root_annex.split(details, 1)[1].split(
        "## Stage and runtime licence text files", 1
    )[0]
    root_details = (
        "### FFmpeg toolchain runtime:" + root_details.split("### FFmpeg toolchain runtime:", 1)[1]
    )
    artifact_details = artifact.split(details, 1)[1].split(
        "## Full licence texts and provenance", 1
    )[0]
    assert root_details.lstrip("\n") == artifact_details.lstrip("\n")
    expected_hashes = {t["sha256"] for r in lock["toolchain_runtime"] for t in r["texts"]}
    assert len(expected_hashes) == 157
    for digest in expected_hashes:
        assert rendered.count(f"SHA-256: `{digest}`".encode()) == 1
        assert root_annex.count(f"SHA-256: `{digest}`") == 1
    for filename in {t["path"] for r in lock["toolchain_runtime"] for t in r["texts"]}:
        assert "tools/package/native-licences/ffmpeg-toolchain/" + filename in root_annex
    for source, row in zip(lock["toolchain_runtime"], runtime, strict=True):
        assert (
            row.name == f"FFmpeg toolchain runtime: {source['name']} {source['version']} "
            f"({source['reached_via']})"
        )
        assert row.version == source["version"]
        assert row.licence == source["licence"]
        assert row.entries == rows[0].entries
        if source["pin_kind"] == "crate-sha256":
            assert row.sources == (
                f"{source['source_url']} (crate archive sha256 {source['pin']})",
                source["repository"],
            )
        else:
            assert source["source_url"] in row.sources
            assert f"{source['repository']} @ {source['pin']}" in row.sources
        parent = (
            "statically linked into ffmpeg.exe / ffprobe.exe by the fork build at "
            + lock["build_repository_commit"]
        )
        if source.get("linkage") == "superset":
            assert "carried as a superset of the static link; linkage not proven" in row.notes
            assert parent not in row.notes
        else:
            assert parent in row.notes
        if source["chosen"]:
            assert "licence chosen: " + source["chosen"] in row.notes
        if source["licence"] == "MPL-2.0":
            assert "MPL-2.0 (secondary licence: GPL-3.0 permitted, section 3.3)" in row.notes


def test_root_annex_generator_checks_committed_bytes_and_detects_a_changed_row(tmp_path, capsys):
    """A renderer drift or stale root annex must make the committed check fail."""
    module = load_notices()
    assert module.main(["--root-annex", "--check"]) == 0
    original = (ROOT / "THIRD_PARTY_NOTICES.md").read_bytes().replace(b"\r\n", b"\n")
    audit = tmp_path / "THIRD_PARTY_NOTICES.md"
    audit.write_bytes(original)
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    lock["toolchain_runtime"][0]["evidence"] += " changed evidence"
    pin = tmp_path / "changed-lock.json"
    pin.write_text(json.dumps(lock))
    args = ["--root-annex", "--audit", str(audit), "--ffmpeg-lock", str(pin)]
    assert module.main([*args, "--check"]) == 1
    assert "root annex differs" in capsys.readouterr().err
    assert audit.read_bytes() == original
    assert module.main([*args, "--write"]) == 0
    assert b"changed evidence" in audit.read_bytes()
    assert module.main([*args, "--check"]) == 0
    assert module.main([*args, "--write"]) == 0
    regenerated = audit.read_bytes()
    assert module.main([*args, "--write"]) == 0
    assert audit.read_bytes() == regenerated


def _order(items, key=None) -> list[int]:
    """The positions of ``items`` in their sorted order (``key`` None: the native order)."""
    return sorted(range(len(items)), key=lambda i: items[i] if key is None else key(items[i]))


def test_licence_texts_sort_in_windows_order_on_every_host():
    """WP6.5 G3 (C15): ``pathlib`` orders paths case-insensitively on Windows only, so the
    renderer's text order (and the ``licence-N`` numbering) depended on the host and the
    macOS runner's ``--root-annex --check`` failed. The key gives the Windows order for
    POSIX-style and Windows-style paths alike, here on the case-differing names of the zlib
    row and on every row of the committed root annex's FFmpeg rows."""
    from pathlib import PurePosixPath, PureWindowsPath

    module = load_notices()
    names = ["zlib--LICENSE", "zlib--contrib--dotzlib--LICENSE", "zlib--contrib--minizip--LICENSE"]
    posix = [module.LicenceInput(PurePosixPath("/r/ffmpeg-components", n)) for n in names]
    windows = [module.LicenceInput(PureWindowsPath("C:/r/ffmpeg-components", n)) for n in names]
    assert _order(windows) == [1, 2, 0]  # Windows: case-insensitive, 'c' < 'l'
    assert _order(posix) == [0, 1, 2]  # POSIX: case-sensitive, 'L' < 'c' (the runner's order)
    assert _order(posix, module._licence_order) == _order(windows) == [1, 2, 0]
    assert _order(windows, module._licence_order) == [1, 2, 0]

    native = ROOT / "tools/package/native-licences"
    lock = module._build_tool().validate_ffmpeg_lock(
        json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_text(encoding="utf-8")),
        component_texts_path=native / "ffmpeg-components",
    )
    entries = (
        "file:ffmpeg.exe",
        "file:ffprobe.exe",
        "file:ffmpeg-BUILD.txt",
        "file:ffmpeg-LICENSE.txt",
    )
    rows = module._ffmpeg_component_rows(lock, entries, native) + module._ffmpeg_runtime_rows(
        lock, entries, native
    )
    differing = 0
    for row in rows:
        items = list(row.licence_inputs)
        as_posix = [i._replace(path=PurePosixPath(i.path.as_posix())) for i in items]
        as_windows = [i._replace(path=PureWindowsPath(i.path.as_posix())) for i in items]
        windows_order = _order(as_windows)
        assert _order(as_posix, module._licence_order) == windows_order, row.name
        assert _order(as_windows, module._licence_order) == windows_order, row.name
        assert _order(items, module._licence_order) == windows_order, row.name
        differing += _order(as_posix) != windows_order
    print(f"rows whose native POSIX order differs: {differing} of {len(rows)}", flush=True)
    assert differing > 0  # the check distinguishes: native POSIX order differs on some rows


def test_runtime_notice_wording_distinguishes_supersets_and_shared_texts(release):
    """Unconditional linkage wording and misleading deduplication names regress."""
    module = load_notices()
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    release["ffmpeg"] = lock
    release["ffmpeg_path"].write_text(json.dumps(lock))
    add_ffmpeg(release)
    rows = module._ffmpeg_rows(release["folder"], release["ffmpeg_path"])
    supersets = [
        row
        for row in rows
        if "carried as a superset of the static link; linkage not proven" in row.notes
    ]
    assert {row.name for row in supersets} == {
        "FFmpeg toolchain runtime: libm 0.2.16 (toolchain)",
        "FFmpeg toolchain runtime: libstdc++ (fast_float) 16.2.0 (toolchain)",
    }
    output = module.render_notices(module.NoticePlan(rows[0].entries, tuple(rows), ())).decode(
        errors="backslashreplace"
    )
    assert (
        "a representative file name from the census; "
        "byte-identical texts are shared across components" in output
    )


@pytest.mark.parametrize("damage", ["missing", "hash", "after-plan"])
def test_ffmpeg_toolchain_text_identity_fails_closed(release, tmp_path, damage):
    """Runtime text integrity is checked both at planning and at rendering."""
    module = load_notices()
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    release["ffmpeg"] = lock
    release["ffmpeg_path"].write_text(json.dumps(lock))
    add_ffmpeg(release)
    texts = tmp_path / "runtime-texts/ffmpeg-toolchain"
    shutil.copytree(ROOT / "tools/package/native-licences/ffmpeg-toolchain", texts)
    shutil.copytree(
        ROOT / "tools/package/native-licences/ffmpeg-components", texts.parent / "ffmpeg-components"
    )
    path = texts / lock["toolchain_runtime"][0]["texts"][0]["path"]
    if damage == "after-plan":
        rows = module._ffmpeg_rows(release["folder"], release["ffmpeg_path"], texts.parent)
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match=r"FFmpeg toolchain runtime.*(text|identity|missing|hash)"):
        if damage == "after-plan":
            module.render_notices(module.NoticePlan(rows[0].entries, tuple(rows), ()))
        else:
            module._ffmpeg_rows(release["folder"], release["ffmpeg_path"], texts.parent)


@pytest.mark.parametrize("damage", ["extra-file", "extra-directory", "upper-case"])
def test_ffmpeg_toolchain_text_directory_is_exact(release, damage):
    """Unreferenced entries and Windows filename aliases cannot hide census drift."""
    module = load_notices()
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    release["ffmpeg"] = lock
    release["ffmpeg_path"].write_text(json.dumps(lock))
    add_ffmpeg(release)
    texts = release["native_surface"] / "ffmpeg-toolchain"
    if damage == "extra-file":
        (texts / "unreferenced-LICENSE").write_bytes(b"unreferenced terms")
    elif damage == "extra-directory":
        (texts / "unreferenced-directory").mkdir()
    else:
        lock["toolchain_runtime"][0]["texts"][0]["path"] = lock["toolchain_runtime"][0]["texts"][0][
            "path"
        ].upper()
        release["ffmpeg_path"].write_text(json.dumps(lock))
    with pytest.raises(ValueError, match="FFmpeg toolchain runtime text directory differs"):
        plan(module, release)


def test_ffmpeg_toolchain_texts_follow_native_surface_override(release):
    """The public planner uses runtime texts from the caller's native surface."""
    module = load_notices()
    lock = json.loads((ROOT / "tools/package/ffmpeg.lock.json").read_bytes())
    release["ffmpeg"] = lock
    release["ffmpeg_path"].write_text(json.dumps(lock))
    add_ffmpeg(release)
    result = plan(module, release)
    runtime = [r for r in result.rows if r.name.startswith("FFmpeg toolchain runtime:")]
    assert runtime
    texts = release["native_surface"] / "ffmpeg-toolchain"
    assert {t.path.parent for r in runtime for t in r.licence_inputs} == {texts}
    path = texts / lock["toolchain_runtime"][0]["texts"][0]["path"]
    path.write_bytes(path.read_bytes() + b"changed override")
    with pytest.raises(ValueError, match=r"FFmpeg toolchain runtime.*text hash differs"):
        plan(module, release)


@pytest.mark.parametrize("field", ["Parent provider", "FFmpeg ref"])
def test_ffmpeg_build_record_requires_parent_and_ref(release, field):
    """The in-artifact source record cannot omit the fork's parent or FFmpeg ref."""
    module = load_notices()
    add_ffmpeg(release)
    record = release["folder"] / "ffmpeg-BUILD.txt"
    record.write_text(
        "\n".join(
            line for line in record.read_text().splitlines() if not line.startswith(field + ":")
        )
    )
    with pytest.raises(ValueError, match="provenance differs: " + field):
        plan(module, release)


@pytest.mark.parametrize("missing", ["ffprobe.exe", "ffmpeg-BUILD.txt", "ffmpeg-LICENSE.txt"])
def test_partial_ffmpeg_distribution_fails_closed(release, missing):
    notices = load_notices()
    add_ffmpeg(release)
    (release["folder"] / missing).unlink()
    with pytest.raises(ValueError, match=r"FFmpeg.*missing"):
        plan(notices, release)


def text_plan(module, inputs, *, name="fixture", version="1.0"):
    row = module.NoticeRow(
        name,
        version,
        "fixture terms",
        ("https://example.invalid/source",),
        ("file:fixture.dll",),
        tuple(inputs),
    )
    return module.NoticePlan(("file:fixture.dll",), (row,), ())


def audited_block(path, block_id):
    section = path.read_text(encoding="utf-8").split(f'<a id="{block_id}"></a>', 1)[1]
    section = section.split('<a id="', 1)[0]
    body = section.split("````text\n", 1)[1].split("````", 1)[0].encode()
    source = re.search(r"Source: `([^`]+)`", section).group(1)
    return source, body


@pytest.mark.parametrize("number", range(36, 45))
def test_each_upstream_reuse_preserves_bytes_hash_and_true_label(number):
    """A wrong block, false wheel provenance or a rewritten upstream text fails."""
    module = load_notices()
    audit = ROOT / "THIRD_PARTY_NOTICES.md"
    source, expected = audited_block(audit, f"text-{number}")
    document = module.render_notices(
        text_plan(module, [module.LicenceInput(audit, f"text-{number}")])
    )
    assert expected in document
    assert source.encode() in document
    assert b"the 1.0.0 audit's upstream copy" in document
    assert hashlib.sha256(expected).hexdigest().encode() in document
    assert b"Installed wheel" not in document


@pytest.mark.parametrize("number", range(36, 45))
@pytest.mark.parametrize("damage", ["body", "hash", "size"])
def test_each_upstream_reuse_refuses_tampered_material(tmp_path, number, damage):
    module = load_notices()
    audit = ROOT / "THIRD_PARTY_NOTICES.md"
    text = audit.read_text(encoding="utf-8")
    marker = f'<a id="text-{number}"></a>'
    before, section = text.split(marker, 1)
    if damage == "body":
        section = section.replace("````text\n", "````text\nTAMPER\n", 1)
    elif damage == "hash":
        section = re.sub(
            r"SHA-256: `[a-f0-9]{64}`", "SHA-256: `" + "0" * 64 + "`", section, count=1
        )
    else:
        section = re.sub(r"UTF-8/LF bytes: \d+", "UTF-8/LF bytes: 1", section, count=1)
    changed = tmp_path / "audit.md"
    changed.write_text(before + marker + section, encoding="utf-8")
    with pytest.raises(ValueError, match=r"text-\d+.*(hash|byte|SHA|size)"):
        module.render_notices(text_plan(module, [module.LicenceInput(changed, f"text-{number}")]))


@pytest.mark.parametrize(
    "name, relative",
    [
        ("numpy", "numpy-2.5.4.dist-info/licenses/LICENSE.txt"),
        ("scipy", "scipy-1.18.1.dist-info/LICENSE.txt"),
        ("PyInstaller bootloader", "pyinstaller-6.22.3.dist-info/licenses/COPYING.txt"),
    ],
)
def test_real_wheel_licence_files_are_copied_byte_for_byte(name, relative):
    """Newline normalization or GPL-section elision must fail the byte comparison."""
    module = load_notices()
    path = VENV_SITE_PACKAGES / relative
    expected = path.read_bytes()
    output = module.render_notices(text_plan(module, [module.LicenceInput(path)], name=name))
    assert expected in output
    if name.startswith("PyInstaller"):
        boot = expected.split(b"Bootloader Exception", 1)[1].split(b"Run-time Hooks", 1)[0]
        hooks = expected.split(b"Run-time Hooks", 1)[1].split(b"The PyInstaller.isolated", 1)[0]
        assert boot in output and hooks in output


def test_commercial_qt_text_is_never_rendered_even_in_a_direct_plan(tmp_path):
    module = load_notices()
    commercial = tmp_path / "LicenseRef-Qt-Commercial.txt"
    commercial.write_bytes(b"PROHIBITED COMMERCIAL TEXT")
    with pytest.raises(ValueError, match="commercial"):
        module.render_notices(text_plan(module, [module.LicenceInput(commercial)]))


@pytest.mark.parametrize("ffmpeg", [False, True])
def test_rendering_has_one_dedicated_ffmpeg_block_only_when_carried(release, ffmpeg):
    module = load_notices()
    if ffmpeg:
        add_ffmpeg(release)
    output = module.render_notices(plan(module, release))
    assert output.count(b"### Bundled FFmpeg GPL-3.0") == int(ffmpeg)
    assert output.count(b"synthetic GPL-3.0 licence") == int(ffmpeg)
    assert b"Clearwater is GPL-2.0-or-later" in output
    assert (b"combined work distributed under GPL-3.0" in output) == ffmpeg
    assert b"Redistributed in this artifact" in output
    assert b"https://github.com/numpy/numpy/tree/v2.5.4" in output
    if not ffmpeg:
        assert b"FFmpeg / ffprobe: user-obtained, not redistributed" in output
    assert module.render_notices(plan(module, release)) == output


def add_distribution(release, name, version, files, modules):
    release["distributions"][name] = installed(release["site"], name, version, files)
    with release["uv_lock"].open("a") as stream:
        stream.write(f'\n[[package]]\nname = "{name}"\nversion = "{version}"\n')
    audit = release["audit"].read_text(encoding="utf-8")
    audit = audit.replace(
        "### Native components",
        f"| {name} | {version} | fixture terms | COMPATIBLE | "
        f"[Source](https://example.invalid/{name}) |\n### Native components",
    )
    release["audit"].write_text(audit, encoding="utf-8")
    for relative, body in files.items():
        if relative.endswith((".dll", ".pyd")):
            target = release["folder"] / "_internal" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body)
    make_executable(release["folder"], ["clearwater", "json", "numpy", *modules])


def append_upstream_audit(release):
    text = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    with release["audit"].open("a", encoding="utf-8") as stream:
        stream.write('\n<a id="text-36"></a>' + text.split('<a id="text-36"></a>', 1)[1])


@pytest.mark.parametrize(
    "name, package", [("pyside6-essentials", "PySide6"), ("shiboken6", "shiboken6")]
)
@pytest.mark.parametrize("wheel_text", [False, True])
def test_qt_replaceability_exact_sources_and_wheel_text_preference(
    release, name, package, wheel_text
):
    module = load_notices()
    info = f"{name.replace('-', '_')}-6.12.0.dist-info/licenses/"
    files = {
        f"{package}/__init__.py": "",
        f"{package}/Qt6Core.dll": "synthetic Qt DLL",
        info + "LicenseRef-Qt-Commercial.txt": "PROHIBITED COMMERCIAL TEXT",
    }
    if wheel_text:
        files[info + "LGPL-3.0.txt"] = (
            "GNU LESSER GENERAL PUBLIC LICENSE\nVersion 3\nSYNTHETIC WHEEL TEXT\n"
        )
    add_distribution(release, name, "6.12.0", files, [package])
    append_upstream_audit(release)
    output = module.render_notices(plan(module, release))
    assert b"replace the Qt DLLs" in output
    assert b"reverse engineering" in output
    assert b"v6.12.0" in output
    assert b"PROHIBITED COMMERCIAL TEXT" not in output
    assert b"LicenseRef-Qt-Commercial.txt" not in output
    assert (b"the 1.0.0 audit's upstream copy" in output) != wheel_text
    if wheel_text:
        assert (release["site"] / (info + "LGPL-3.0.txt")).read_bytes() in output
    else:
        assert (
            b"https://raw.githubusercontent.com/qt/qtbase/v6.12.0/LICENSES/LGPL-3.0-only.txt"
            in output
        )


def add_heif(release, *, wheel_text=False, native=True):
    prefix = "pillow_heif-1.8.1.dist-info/licenses/"
    manifest = (ROOT / ".venv/Lib/site-packages" / prefix / "LICENSES_bundled.txt").read_text()
    files = {
        "pillow_heif/__init__.py": "",
        prefix + "LICENSE.txt": "wrapper BSD terms\n",
        prefix + "LICENSES_bundled.txt": manifest,
    }
    if native:
        for name in (
            "libheif-abc.dll",
            "libde265-0-abc.dll",
            "libx265-217-abc.dll",
            "libgcc_s_seh-1-abc.dll",
            "libstdc++-6-abc.dll",
            "libwinpthread-1-abc.dll",
        ):
            files[name] = "synthetic native DLL"
    if wheel_text:
        for name in ("libheif", "libde265", "x265", "mingw", "winpthreads"):
            files[prefix + name + "-COPYING.txt"] = f"Full wheel licence for {name}\n"
    add_distribution(release, "pillow-heif", "1.8.1", files, ["pillow_heif"])
    append_upstream_audit(release)


@pytest.mark.parametrize("wheel_text", [False, True])
def test_heif_native_rows_sources_and_mingw_limitation(release, wheel_text):
    module = load_notices()
    add_heif(release, wheel_text=wheel_text)
    result = plan(module, release)
    by_name = {row.name: row for row in result.rows}
    assert by_name["pillow-heif / libheif"].version == "1.23.6"
    assert by_name["pillow-heif / libde265"].version == "1.1.3"
    assert by_name["pillow-heif / x265"].version == "4.3"
    assert by_name["pillow-heif / x265"].licence == "GPL-2.0-or-later"
    assert by_name["pillow-heif / libheif"].sources == (
        "https://github.com/strukturag/libheif/tree/v1.23.6",
    )
    output = module.render_notices(result)
    assert b"the wheel does not name the toolchain release" in output
    assert b"GPL-3.0 with the GCC Runtime Library Exception" in output
    for name in (b"libgcc_s_seh-1.dll", b"libstdc++-6.dll", b"libwinpthread-1.dll"):
        assert name in output
    assert b"MIT / BSD" in output
    assert b"replace" in output and b"LGPL" in output
    assert (b"the 1.0.0 audit's upstream copy" in output) != wheel_text


def test_heif_wrapper_without_native_libraries_never_claims_native_rows(release):
    module = load_notices()
    add_heif(release, native=False)
    result = plan(module, release)
    assert not any(row.name.startswith("pillow-heif / ") for row in result.rows)


def test_upstream_text_version_must_match_installed_component(release):
    module = load_notices()
    add_heif(release)
    manifest = release["site"] / "pillow_heif-1.8.1.dist-info/licenses/LICENSES_bundled.txt"
    manifest.write_text(manifest.read_text().replace("v1.23.6", "v1.23.7"))
    with pytest.raises(ValueError, match=r"libheif.*(version|source)"):
        plan(module, release)


def writer_kwargs(release):
    return {
        "audit_path": release["audit"],
        "uv_lock_path": release["uv_lock"],
        "ffmpeg_lock_path": release["ffmpeg_path"],
        "distribution": release["distributions"].__getitem__,
        "native_licences_path": release["native_surface"],
    }


def test_writer_generates_stable_complete_notices_without_extra_bundle_files(release):
    module = load_notices()
    destination = module.write_notices(release["folder"], **writer_kwargs(release))
    assert destination == release["folder"] / "THIRD_PARTY_NOTICES.md"
    expected = destination.read_bytes()
    assert b"file:THIRD_PARTY_NOTICES.md" in expected
    assert expected == module.render_notices(plan(module, release))
    assert module.write_notices(release["folder"], **writer_kwargs(release)) == destination
    assert destination.read_bytes() == expected
    assert not list(release["folder"].glob("*.tmp"))


def test_writer_validation_failure_preserves_previous_notice_bytes(release):
    module = load_notices()
    destination = release["folder"] / "THIRD_PARTY_NOTICES.md"
    destination.write_bytes(b"previous valid document")
    (release["folder"] / "_internal/mystery.dll").write_bytes(b"unknown")
    with pytest.raises(ValueError, match="mystery"):
        module.write_notices(release["folder"], **writer_kwargs(release))
    assert destination.read_bytes() == b"previous valid document"


@pytest.mark.parametrize("fails", [False, True])
def test_cli_writes_notices_or_returns_one_line_failure(release, monkeypatch, capsys, fails):
    module = load_notices()
    write = module.write_notices
    monkeypatch.setattr(
        module,
        "write_notices",
        lambda *a, **kw: write(*a, native_licences_path=release["native_surface"], **kw),
    )
    monkeypatch.setattr(
        module._build_tool(), "trusted_distributions", lambda versions: release["distributions"]
    )
    if fails:
        (release["folder"] / "_internal/mystery.dll").write_bytes(b"unknown")
    status = module.main(
        [
            str(release["folder"]),
            "--audit",
            str(release["audit"]),
            "--uv-lock",
            str(release["uv_lock"]),
            "--ffmpeg-lock",
            str(release["ffmpeg_path"]),
        ]
    )
    captured = capsys.readouterr()
    assert status == int(fails)
    if fails:
        assert len(captured.err.splitlines()) == 1
        assert "mystery" in captured.err
        assert not (release["folder"] / "THIRD_PARTY_NOTICES.md").exists()
    else:
        assert (
            (release["folder"] / "THIRD_PARTY_NOTICES.md").read_bytes().startswith(b"# Clearwater")
        )
        assert "wrote" in captured.out


def test_openssl_dlls_cannot_be_mislicensed_as_python_psf_terms(release, native_surface):
    """A carried OpenSSL library needs a row in the verified native input surface."""
    module = load_notices()
    (release["folder"] / "_internal/libcrypto-3-x64.dll").write_bytes(b"synthetic OpenSSL")
    document = json.loads((native_surface / "manifest.json").read_text())
    document["components"] = []
    (native_surface / "manifest.json").write_text(json.dumps(document))
    (native_surface / "openssl-3.5.5-LICENSE.txt").unlink()
    with pytest.raises(ValueError, match=r"OpenSSL.*missing.*(row|material)"):
        plan(module, release, native_licences_path=native_surface)


@pytest.mark.parametrize("ffmpeg", [False, True])
def test_complete_native_fixture_has_only_supported_rows_and_shared_upstream_blocks(
    release, ffmpeg
):
    """Native rows share verified texts without claiming absent binary components."""
    module = load_notices()
    add_heif(release)
    for name, package in (("pyside6-essentials", "PySide6"), ("shiboken6", "shiboken6")):
        commercial = (
            f"{name.replace('-', '_')}-6.12.0.dist-info/licenses/LicenseRef-Qt-Commercial.txt"
        )
        add_distribution(
            release,
            name,
            "6.12.0",
            {
                f"{package}/__init__.py": "",
                f"{package}/Qt6Core.dll": "synthetic Qt DLL",
                commercial: "COMMERCIAL TEXT",
            },
            [package],
        )
    for name, package, version, relative in (
        ("scipy", "scipy", "1.18.1", "scipy-1.18.1.dist-info/LICENSE.txt"),
        ("pillow", "PIL", "12.3.0", "pillow-12.3.0.dist-info/licenses/LICENSE"),
    ):
        add_distribution(
            release,
            name,
            version,
            {
                f"{package}/__init__.py": "",
                f"{package}/synthetic.pyd": "synthetic native",
                relative: (ROOT / ".venv/Lib/site-packages" / relative).read_text(encoding="utf-8"),
            },
            [package],
        )
    numpy_text = "numpy-2.5.4.dist-info/licenses/LICENSE.txt"
    (release["site"] / numpy_text).write_bytes(
        (ROOT / ".venv/Lib/site-packages" / numpy_text).read_bytes()
    )
    if ffmpeg:
        add_ffmpeg(release)
    destination = module.write_notices(release["folder"], **writer_kwargs(release))
    result = plan(module, release)
    names = {row.name for row in result.rows}
    expected = {
        "Clearwater",
        "Python",
        "PyInstaller bootloader",
        "PyInstaller run-time hooks",
        "numpy",
        "scipy",
        "pillow",
        "pillow-heif",
        "pyside6-essentials",
        "shiboken6",
        "pillow-heif / libheif",
        "pillow-heif / libde265",
        "pillow-heif / x265",
        "pillow-heif / MinGW runtime",
    }
    if ffmpeg:
        expected.update(
            {
                "FFmpeg / ffprobe",
                "FFmpeg component: x265",
                "FFmpeg toolchain runtime: libgcc 16.2.0 (toolchain)",
                "FFmpeg toolchain runtime: libstdc++ 16.2.0 (toolchain)",
            }
        )
    assert names == expected
    assert {entry for row in result.rows for entry in row.entries} == set(result.entries)
    output = destination.read_bytes()
    _source, lgpl = audited_block(release["audit"], "text-36")
    assert output.count(lgpl) == 1
    assert b"GCC RUNTIME LIBRARY EXCEPTION" in output
    assert output.count(b"### Bundled FFmpeg GPL-3.0") == int(ffmpeg)
    (release["folder"].parent / "rendered-plan.json").write_text(
        json.dumps(
            {
                "entries": result.entries,
                "rows": [
                    {
                        "name": row.name,
                        "entries": row.entries,
                        "licence": row.licence,
                        "version": row.version,
                        "sources": row.sources,
                    }
                    for row in result.rows
                ],
                "user_obtained": result.user_obtained,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_cli_invalid_archive_returns_one_stderr_line(release, capsys):
    module = load_notices()
    (release["folder"] / "Clearwater.exe").write_bytes(b"invalid CArchive")
    assert module.main([str(release["folder"])]) == 1
    captured = capsys.readouterr()
    assert len(captured.err.splitlines()) == 1
    assert "archive" in captured.err.lower()
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("existing", [False, True])
def test_writer_publication_failure_retains_old_content_and_removes_its_temporary_files(
    release, monkeypatch, existing
):
    module = load_notices()
    destination = release["folder"] / "THIRD_PARTY_NOTICES.md"
    if existing:
        destination.write_bytes(b"previous complete notices")

    def refuse_replace(source, target):
        raise OSError("planted publication failure")

    monkeypatch.setattr(module.os, "replace", refuse_replace)
    with pytest.raises(OSError, match="publication failure"):
        module.write_notices(release["folder"], **writer_kwargs(release))
    if existing:
        assert destination.read_bytes() == b"previous complete notices"
    else:
        assert not destination.exists()
    assert not list(release["folder"].parent.glob("*.tmp"))


@pytest.fixture
def native_surface(tmp_path):
    return _make_native_surface(tmp_path / "native-licences")


def _make_native_surface(destination):
    """Make an independent synthetic OpenSSL binding for either fixture consumer."""
    shutil.copytree(
        ROOT / "tools/package/native-licences",
        destination,
        ignore=shutil.ignore_patterns("ffmpeg-toolchain", "ffmpeg-components"),
    )
    # Existing OpenSSL tests carry synthetic bytes, so bind their copied input
    # surface to those bytes rather than the seat-measured production DLLs.
    path = destination / "manifest.json"
    document = json.loads(path.read_text())
    document["components"] = [document["components"][0]]
    document.pop("vendored_paths", None)
    document.pop("embedded_hosts", None)
    document.pop("limits", None)
    for text in destination.iterdir():
        if text.name not in {"manifest.json", document["components"][0]["text_file"]}:
            text.unlink()
    document["components"][0]["bundled_files"] = [
        {
            "name": name,
            "sha256": hashlib.sha256(b"synthetic interpreter native").hexdigest(),
            "size_bytes": len(b"synthetic interpreter native"),
        }
        for name in ("libcrypto-3-x64.dll", "libssl-3-x64.dll")
    ]
    path.write_text(json.dumps(document))
    return destination


def omit_production_embedded_census(surface):
    """Keep real standalone/vendored texts for a synthetic, non-census folder."""
    path = surface / "manifest.json"
    document = json.loads(path.read_text())
    document["components"] = [row for row in document["components"] if "embedded_in" not in row]
    document.pop("embedded_hosts", None)
    document.pop("limits", None)
    keep = {"manifest.json", *(name for name, _sha, _size in native_surface_inputs(document))}
    for item in surface.iterdir():
        # This subdirectory is checked separately against the FFmpeg lock.
        if item.name in {"ffmpeg-toolchain", "ffmpeg-components"} and item.is_dir():
            continue
        if item.name not in keep:
            item.unlink()
    path.write_text(json.dumps(document))


def change_native_row(surface, field, value):
    path = surface / "manifest.json"
    document = json.loads(path.read_text())
    document["components"][0][field] = value
    path.write_text(json.dumps(document), encoding="utf-8")


def add_openssl(release, names=("libcrypto-3-x64.dll", "libssl-3-x64.dll")):
    for name in names:
        (release["folder"] / "_internal" / name).write_bytes(b"synthetic interpreter native")


def test_real_native_manifest_verifies_the_seat_bytes():
    module = load_notices()
    surface = ROOT / "tools/package/native-licences"
    records = module.load_native_licences(surface)
    assert len([record for record in records if not record.embedded_in]) == 10
    row = records[0]
    assert row.component == "OpenSSL"
    assert row.upstream_version == "3.5.5"
    assert row.spdx == "Apache-2.0"
    assert row.licence_input.path == surface / "openssl-3.5.5-LICENSE.txt"
    data = row.licence_input.path.read_bytes()
    assert len(data) == 10175
    assert (
        hashlib.sha256(data).hexdigest()
        == "7d5450cb2d142651b8afa315b5f238efc805dad827d91ba367d8516bc9d49e7a"
    )


def test_production_embedded_hosts_have_complete_verified_source_text_rows():
    """The real census inputs load and bind all declared CPython/Qt hosts and texts."""
    module = load_notices()
    folder = ROOT / "tools/package/native-licences"
    document = json.loads((folder / "manifest.json").read_text())
    records = {record.component: record for record in module.load_native_licences(folder)}
    hosts = {host.relpath: host for host in module._embedded_declarations(document)}
    expected = {
        "_internal/python312.dll": 8,
        "_internal/pyexpat.pyd": 1,
        "_internal/_elementtree.pyd": 1,
        "_internal/_decimal.pyd": 1,
        "_internal/_bz2.pyd": 1,
        "_internal/_lzma.pyd": 1,
        "_internal/unicodedata.pyd": 1,
        "_internal/PySide6/Qt6Core.dll": 18,
        "_internal/PySide6/Qt6Gui.dll": 20,
        "_internal/PySide6/Qt6Network.dll": 2,
        "_internal/PySide6/Qt6Svg.dll": 1,
        "_internal/PySide6/plugins/imageformats/qjpeg.dll": 2,
        "_internal/PySide6/plugins/imageformats/qtiff.dll": 3,
        "_internal/PySide6/plugins/imageformats/qwebp.dll": 2,
        "_internal/PySide6/plugins/platforms/qwindows.dll": 1,
        "_internal/PySide6/plugins/platforms/qdirect2d.dll": 1,
        "_internal/shiboken6/shiboken6.abi3.dll": 1,
    }
    assert set(expected) <= set(hosts)
    for path, count in expected.items():
        host = hosts[path]
        assert len(host.components) == count
        for name, _source in host.components:
            assert path in records[name].embedded_in
    unicode_rows = [record for record in records.values() if record.spdx == "Unicode-3.0"]
    assert len({record.licence_input.path for record in unicode_rows}) == 1
    assert any(
        {"_internal/unicodedata.pyd", "_internal/PySide6/Qt6Core.dll"} <= set(record.embedded_in)
        for record in unicode_rows
    )


def test_release_archive_keeps_sourceware_repository_and_member_path(native_surface):
    """A non-GitHub source archive must not invent a GitHub-style tree URL."""
    document = synthetic_native_binding(native_surface)
    row = document["components"][0]
    row.update(upstream_repository="https://sourceware.org/git/bzip2.git", source_path="LICENSE")
    (native_surface / "manifest.json").write_text(json.dumps(document))
    record = load_notices().load_native_licences(native_surface)[0]
    assert "https://sourceware.org/git/bzip2.git" in record.source_urls
    assert all("bzip2.git/tree/" not in url for url in record.source_urls)
    assert "archive member LICENSE" in record.licence_input.provenance


@pytest.mark.parametrize("path", ["../outside", "/absolute", "C:/outside", "a\\b", ""])
def test_release_archive_refuses_unsafe_member_source_path(native_surface, path):
    """An archive-member provenance path is a safe relative path, as for git trees."""
    document = synthetic_native_binding(native_surface)
    document["components"][0]["source_path"] = path
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="unsafe source_path"):
        load_notices().load_native_licences(native_surface)


@pytest.mark.parametrize(
    "damage", ["text", "size", "hash", "missing-text", "orphan-text", "duplicate"]
)
def test_native_surface_refuses_integrity_and_coverage_errors(native_surface, damage):
    module = load_notices()
    path = native_surface / "openssl-3.5.5-LICENSE.txt"
    if damage == "text":
        data = path.read_bytes()
        path.write_bytes(b"!" + data[1:])
    elif damage == "size":
        change_native_row(native_surface, "text_size_bytes", 1)
    elif damage == "hash":
        change_native_row(native_surface, "text_sha256", "0" * 64)
    elif damage == "missing-text":
        path.unlink()
    elif damage == "orphan-text":
        (native_surface / "orphan-LICENSE.txt").write_bytes(b"unclaimed text")
    else:
        manifest = native_surface / "manifest.json"
        document = json.loads(manifest.read_text())
        document["components"].append(document["components"][0])
        manifest.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="native"):
        module.load_native_licences(native_surface)


@pytest.mark.parametrize(
    ("name", "admitted"),
    [
        ("ffmpeg-macos-components", True),
        ("ffmpeg-components", True),
        ("ffmpeg-toolchain", True),
        ("ffmpeg-linux-components", False),
    ],
)
def test_native_surface_leaves_the_ffmpeg_lock_text_folders_to_their_locks(
    native_surface, name, admitted
):
    """WP6.5 part 3b: the macOS FFmpeg lock's text folder, like the Windows lock's two, is
    checked by its own lock; any other unclaimed folder still fails closed."""
    folder = native_surface / name
    folder.mkdir(exist_ok=True)
    (folder / "x--COPYING").write_bytes(b"synthetic text\n")
    module = load_notices()
    if admitted:
        assert module.load_native_licences(native_surface)
    else:
        with pytest.raises(ValueError, match="without manifest rows: ffmpeg-linux-components"):
            module.load_native_licences(native_surface)


@pytest.mark.parametrize(
    "field, value",
    [
        ("component", ""),
        ("bundled_version_source", "invented.source"),
        ("upstream_version", None),
        ("source_tag", ""),
        ("source_commit", "not-a-commit"),
        ("source_tag_object", "0"),
        ("source_archive_url", "file:///source.tar.gz"),
        ("source_archive_sha256", "nope"),
        ("spdx", ""),
        ("text_file", "../outside.txt"),
        ("text_file", "sub\\outside.txt"),
        ("text_size_bytes", True),
        ("fetch_date", "yesterday"),
        ("fetched_by", "cell"),
    ],
)
def test_native_manifest_rejects_unverifiable_schema_fields(native_surface, field, value):
    module = load_notices()
    change_native_row(native_surface, field, value)
    with pytest.raises(ValueError, match="native"):
        module.load_native_licences(native_surface)


@pytest.mark.parametrize(
    "names",
    [("libcrypto-3-x64.dll",), ("libssl-3-x64.dll",), ("libcrypto-3-x64.dll", "libssl-3-x64.dll")],
)
def test_openssl_rows_and_verbatim_text_follow_only_carried_dlls(release, names):
    module = load_notices()
    add_openssl(release, names)
    result = plan(module, release)
    row = next(row for row in result.rows if row.name == "OpenSSL")
    assert row.version == "3.5.5"
    assert row.licence == "Apache-2.0"
    assert set(row.entries) == {f"file:_internal/{name}" for name in names}
    python_row = next(row for row in result.rows if row.name == "Python")
    assert not set(row.entries).intersection(python_row.entries)
    output = module.render_notices(result)
    text = (ROOT / "tools/package/native-licences/openssl-3.5.5-LICENSE.txt").read_bytes()
    assert output.count(text) == 1
    assert b"openssl-3.5.5" in output
    assert (
        b"https://github.com/openssl/openssl/releases/download/openssl-3.5.5/openssl-3.5.5.tar.gz"
        in output
    )
    assert b"b28c91532a8b65a1f983b4c28b7488174e4a01008e29ce8e69bd789f28bc2a89" in output
    assert b"The Windows download redistributes the interpreter's native libraries" in output
    assert b"the 1.0.0 source install did not" in output
    assert b"fetched by seat" in output
    assert b"Installed wheel: OpenSSL" not in output


@pytest.mark.parametrize(
    "reading", ["OpenSSL 9.9.9 1 Jan 2026", "LibreSSL 3.5.5", "OpenSSL 3.5.5-dev"]
)
def test_native_version_mismatch_fails_for_carried_openssl(release, monkeypatch, reading):
    module = load_notices()
    add_openssl(release)
    monkeypatch.setattr(module.ssl, "OPENSSL_VERSION", reading)
    with pytest.raises(ValueError, match=r"OpenSSL.*version"):
        plan(module, release)


def test_absent_openssl_never_emits_a_native_row_or_text(release):
    module = load_notices()
    result = plan(module, release)
    assert not any(row.name == "OpenSSL" for row in result.rows)
    output = module.render_notices(result)
    assert b"Seat-verified native input: OpenSSL" not in output
    assert b"openssl-3.5.5.tar.gz" not in output


def test_native_text_is_rechecked_when_rendering_after_a_plan(release, native_surface):
    module = load_notices()
    add_openssl(release)
    result = plan(module, release, native_licences_path=native_surface)
    path = native_surface / "openssl-3.5.5-LICENSE.txt"
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match=r"native.*(hash|byte|size)"):
        module.render_notices(result)


def test_different_python_build_release_fails_only_when_openssl_is_carried(release, native_surface):
    module = load_notices()
    path = native_surface / "manifest.json"
    document = json.loads(path.read_text())
    document["interpreter_build"]["release"] = "20260304"
    path.write_text(json.dumps(document))
    assert not any(
        row.name == "OpenSSL"
        for row in plan(module, release, native_licences_path=native_surface).rows
    )
    add_openssl(release)
    with pytest.raises(ValueError, match=r"OpenSSL.*build release"):
        plan(module, release, native_licences_path=native_surface)


def test_native_writer_keeps_openssl_coverage_and_bytes_deterministic(release):
    module = load_notices()
    add_openssl(release)
    path = module.write_notices(release["folder"], **writer_kwargs(release))
    expected = path.read_bytes()
    assert b"| OpenSSL | 3.5.5 | Apache-2.0 | Redistributed in this artifact |" in expected
    assert b"python-build-standalone 20260303" in expected
    assert module.write_notices(release["folder"], **writer_kwargs(release)) == path
    assert path.read_bytes() == expected
    result = plan(module, release)
    assert {entry for row in result.rows for entry in row.entries} == set(result.entries)


@pytest.mark.parametrize(
    "damage", ["not-object", "bool-schema", "missing-components", "bad-build", "missing-spdx"]
)
def test_native_manifest_rejects_invalid_document_shapes(native_surface, damage):
    module = load_notices()
    path = native_surface / "manifest.json"
    document = json.loads(path.read_text())
    if damage == "not-object":
        document = []
    elif damage == "bool-schema":
        document["schema_version"] = True
    elif damage == "missing-components":
        del document["components"]
    elif damage == "bad-build":
        document["interpreter_build"] = "unverified"
    else:
        del document["components"][0]["spdx"]
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="native"):
        module.load_native_licences(native_surface)


def record_hash(dist, relative, body):
    """Give one fixture RECORD entry a real wheel-style SHA-256 and size."""
    record = Path(str(dist.locate_file(""))) / dist._path.name / "RECORD"
    digest = base64.urlsafe_b64encode(hashlib.sha256(body).digest()).decode().rstrip("=")
    lines = record.read_text().splitlines()
    record.write_text(
        "\n".join(
            f"{relative},sha256={digest},{len(body)}" if line.split(",")[0] == relative else line
            for line in lines
        )
        + "\n"
    )


def synthetic_native_binding(
    surface, *, component="Fixture native", selector=None, body=b"native bytes"
):
    """Use a fixture row and fixture bytes; no real component provenance is added."""
    path = surface / "manifest.json"
    document = json.loads(path.read_text())
    row = document["components"][0]
    row["component"] = component
    row.pop("bundled_version_source", None)
    row["bundled_files"] = [
        {
            **(selector or {"name": "fixture.dll"}),
            "sha256": hashlib.sha256(body).hexdigest(),
            "size_bytes": len(body),
        }
    ]
    path.write_text(json.dumps(document))
    return document


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        {"method": "invented", "value": "1"},
        {"method": "embedded_string", "value": ""},
        {"method": "embedded_string", "value": "1", "extra": "x"},
    ],
)
def test_version_evidence_is_required_and_structured(native_surface, value):
    """Absent, empty or invented version evidence cannot enter a native row."""
    document = synthetic_native_binding(native_surface)
    row = document["components"][0]
    if value is None:
        row.pop("version_evidence", None)
    else:
        row["version_evidence"] = value
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="version_evidence"):
        load_notices().load_native_licences(native_surface)


def co_licensed_surface(surface):
    """Two synthetic components share bytes only through explicit mutual links."""
    document = synthetic_native_binding(surface)
    row = document["components"][0]
    row["version_evidence"] = {"method": "embedded_string", "value": "fixture 3.5.5"}
    row["co_licensed_with"] = ["Other fixture"]
    other = {
        **copy.deepcopy(row),
        "component": "Other fixture",
        "co_licensed_with": [row["component"]],
    }
    document["components"].append(other)
    return document


@pytest.mark.parametrize("damage", ["asymmetric", "dangling", "missing-link", "missing-binding"])
def test_co_licence_links_require_symmetric_complete_claims(native_surface, damage):
    """A shared identity needs complete, mutual links to every component owner."""
    document = co_licensed_surface(native_surface)
    first, second = document["components"]
    if damage == "asymmetric":
        second.pop("co_licensed_with")
    elif damage == "dangling":
        first["co_licensed_with"] = ["Missing fixture"]
    elif damage == "missing-link":
        first.pop("co_licensed_with")
        second.pop("co_licensed_with")
    else:
        second["bundled_files"][0] = {**second["bundled_files"][0], "sha256": "a" * 64}
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match=r"native.*(co.licens|duplicate file claim)"):
        load_notices().load_native_licences(native_surface)


def test_co_licensed_file_renders_all_required_rows(release, native_surface):
    """Every owner of carried co-licensed bytes must appear in rendered notices."""
    module = load_notices()
    document = co_licensed_surface(native_surface)
    (native_surface / "manifest.json").write_text(json.dumps(document))
    (release["folder"] / "_internal/fixture.dll").write_bytes(b"native bytes")
    result = plan(module, release, native_licences_path=native_surface)
    label = "file:_internal/fixture.dll"
    assert {r.name for r in result.rows if label in r.entries} == {
        "Fixture native",
        "Other fixture",
    }
    output = module.render_notices(result)
    assert b"| Fixture native |" in output and b"| Other fixture |" in output
    assert b"embedded_string: fixture 3.5.5" in output
    # A selector can match several copies; linked components remain required
    # even when one selector would otherwise miss the carried copy.
    document["components"][1]["bundled_files"][0].pop("name")
    document["components"][1]["bundled_files"][0]["relpath_glob"] = "absent/fixture.dll"
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match=r"co.licens"):
        plan(module, release, native_licences_path=native_surface)


@pytest.mark.parametrize(
    "source",
    [None, {}, {"file": "LICENSE.txt", "lines": [0, 4]}, {"file": "LICENSE.txt", "lines": [8, 4]}],
)
def test_excerpt_requires_source_file_and_valid_line_range(native_surface, source):
    """An excerpt must name its audited source file and positive ordered line range."""
    document = synthetic_native_binding(native_surface)
    row = document["components"][0]
    row["text_kind"] = "excerpt"
    if source is not None:
        row["text_source"] = source
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="provenance"):
        load_notices().load_native_licences(native_surface)


def test_excerpt_provenance_is_rendered(release, native_surface):
    """Copying an excerpt retains the exact source-file and line attribution."""
    document = provenance_fixture(native_surface, "proprietary-redistributable")
    row = document["components"][0]
    source = (Path(sys.base_prefix) / "LICENSE.txt").read_bytes()
    excerpt = b"".join(source.splitlines(keepends=True)[282:320])
    row["text_source"].update(sha256=hashlib.sha256(source).hexdigest(), size_bytes=len(source))
    (native_surface / row["text_file"]).write_bytes(excerpt)
    row.update(text_sha256=hashlib.sha256(excerpt).hexdigest(), text_size_bytes=len(excerpt))
    (native_surface / "manifest.json").write_text(json.dumps(document))
    (release["folder"] / "_internal/fixture.dll").write_bytes(b"native bytes")
    module = load_notices()
    output = module.render_notices(plan(module, release, native_licences_path=native_surface))
    assert b"<build interpreter>/LICENSE.txt, lines 283-320" in output


@pytest.mark.parametrize(
    "filename",
    ["dataclasses.pyd", "python3999.dll", "python3_d.dll", "_ctypes.pyd", "python312.dll"],
)
def test_python_native_fallback_refuses_unverified_bytes(release, filename):
    """A Python-like filename never substitutes for the interpreter's exact bytes."""
    module = load_notices()
    (release["folder"] / "_internal" / filename).write_bytes(b"unverified PSF bytes")
    with pytest.raises(ValueError, match=re.escape(filename)):
        plan(module, release)


@pytest.mark.parametrize(
    "filename",
    [
        "vcomp140.dll",
        "vccorlib140.dll",
        "vcamp140.dll",
        "msvcr120.dll",
        "mfc140u.dll",
        "d3dcompiler_47.dll",
    ],
)
def test_additional_wheel_runtimes_need_native_rows(release, filename):
    """A wheel RECORD alone cannot license the additional Windows runtime families."""
    module = load_notices()
    relative = "numpy/_core/" + filename
    (release["site"] / relative).write_bytes(b"wheel bytes")
    record = release["distributions"]["numpy"]._path / "RECORD"
    with record.open("a") as stream:
        stream.write(relative + ",,\n")
    (release["folder"] / "_internal" / relative).write_bytes(b"wheel bytes")
    with pytest.raises(ValueError, match="missing native licence row.*" + re.escape(filename)):
        plan(module, release)


@pytest.mark.parametrize(
    "selector",
    [
        {"name": "libcrypto-3-x64.dll"},
        {"relpath_glob": "_internal/libssl-*.dll"},
        {"relpath_glob": "_internal/*.dll"},
    ],
)
def test_openssl_files_cannot_be_claimed_by_another_native(release, native_surface, selector):
    """Neither literal nor broad selectors may reassign OpenSSL to another native."""
    module = load_notices()
    synthetic_native_binding(
        native_surface, selector=selector, body=b"synthetic interpreter native"
    )
    add_openssl(release)
    with pytest.raises(ValueError, match="OpenSSL"):
        plan(module, release, native_licences_path=native_surface)


@pytest.mark.parametrize("filename", ["libffi-8.dll", "sqlite3.dll", "tcl86t.dll", "tk86t.dll"])
def test_interpreter_non_psf_dll_needs_its_own_native_row(release, monkeypatch, filename):
    """Interpreter membership alone must never grant PSF terms to native DLLs."""
    module = load_notices()
    (release["folder"] / "_internal" / filename).write_bytes(b"interpreter DLL")
    with pytest.raises(ValueError, match=re.escape(filename)):
        plan(module, release)


@pytest.mark.parametrize(
    "relative",
    [
        "PySide6/opengl32sw.dll",
        "PySide6/msvcp140.dll",
        "numpy.libs/msvcp140-abc123.dll",
        "PySide6/vcruntime140_1.dll",
        "PySide6/concrt140.dll",
        "PySide6/api-ms-win-crt-runtime-l1-1-0.dll",
    ],
)
def test_wheel_record_cannot_absorb_third_party_runtime_terms(release, relative):
    """Separate native terms take priority over an exact wheel RECORD path."""
    module = load_notices()
    add_distribution(
        release,
        "pyside6-essentials",
        "6.12.0",
        {
            relative: "separately licensed native",
            "pyside6_essentials-6.12.0.dist-info/licenses/LGPL.txt": (
                "GNU LESSER GENERAL PUBLIC LICENSE\nVersion 3\nfixture"
            ),
        },
        [],
    )
    with pytest.raises(ValueError, match=re.escape(relative)):
        plan(module, release)


@pytest.mark.parametrize("filename", ["vcruntime140.dll", "ucrtbase.dll"])
def test_flattened_windows_runtime_is_named_as_missing_native_row(release, filename):
    module = load_notices()
    for name in ("pyside6-essentials", "shiboken6"):
        add_distribution(
            release,
            name,
            "6.12.0",
            {
                f"{name}/{filename}": "runtime",
                f"{name}-6.12.0.dist-info/licenses/LGPL.txt": (
                    "GNU LESSER GENERAL PUBLIC LICENSE\nVersion 3\nfixture"
                ),
            },
            [],
        )
        (release["folder"] / "_internal" / name / filename).unlink()
    (release["folder"] / "_internal" / filename).write_bytes(b"runtime")
    with pytest.raises(ValueError, match="native.*" + re.escape(filename)):
        plan(module, release)


@pytest.mark.parametrize(
    "relative, body",
    [
        ("elsewhere/test.pyd", b"synthetic native extension"),
        ("test.pyd", b"wrong bytes"),
    ],
)
def test_basename_fallback_requires_flattening_and_record_hash(release, relative, body):
    module = load_notices()
    record_hash(
        release["distributions"]["numpy"], "numpy/_core/test.pyd", b"synthetic native extension"
    )
    target = release["folder"] / "_internal" / relative
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(body)
    with pytest.raises(ValueError, match=re.escape(relative)):
        plan(module, release)


def test_correctly_hashed_flattened_wheel_native_is_accepted(release):
    module = load_notices()
    record_hash(
        release["distributions"]["numpy"], "numpy/_core/test.pyd", b"synthetic native extension"
    )
    (release["folder"] / "_internal/test.pyd").write_bytes(b"synthetic native extension")
    row = next(row for row in plan(module, release).rows if row.name == "numpy")
    assert "file:_internal/test.pyd" in row.entries


def test_stdlib_extension_and_python_dll_keep_psf_row(release):
    module = load_notices()
    shutil.copyfile(
        Path(sys.base_prefix) / "DLLs/_ctypes.pyd", release["folder"] / "_internal/_ctypes.pyd"
    )
    row = next(row for row in plan(module, release).rows if row.name == "Python")
    assert {"file:_internal/_ctypes.pyd", "file:_internal/python312.dll"} <= set(row.entries)


def test_openssl_name_with_wrong_bytes_fails_closed(release):
    module = load_notices()
    (release["folder"] / "_internal/libcrypto-3-x64.dll").write_bytes(b"wrong OpenSSL")
    with pytest.raises(ValueError, match=r"libcrypto-3-x64\.dll"):
        plan(module, release)


@pytest.mark.parametrize(
    "selector", [{"name": "fixture.dll"}, {"relpath_glob": "_internal/natives/*.dll"}]
)
def test_generic_native_row_covers_exact_bytes_and_reports_hash(release, native_surface, selector):
    module = load_notices()
    synthetic_native_binding(native_surface, selector=selector)
    target = release["folder"] / "_internal/natives/fixture.dll"
    target.parent.mkdir()
    target.write_bytes(b"native bytes")
    result = plan(module, release, native_licences_path=native_surface)
    row = next(row for row in result.rows if row.name == "Fixture native")
    assert row.version == "3.5.5"
    assert row.entries == ("file:_internal/natives/fixture.dll",)
    assert hashlib.sha256(b"native bytes").hexdigest().encode() in module.render_notices(result)


@pytest.mark.parametrize(
    "damage",
    [
        "root-key",
        "build-key",
        "row-key",
        "binding-key",
        "no-binding",
        "bad-hash",
        "duplicate-claim",
        "both-selectors",
        "unsafe-glob",
        "bool-size",
    ],
)
def test_native_binding_schema_fails_closed(native_surface, damage):
    module = load_notices()
    document = json.loads((native_surface / "manifest.json").read_text())
    row = document["components"][0]
    row["bundled_files"] = [{"name": "fixture.dll", "sha256": "a" * 64, "size_bytes": 12}]
    if damage == "root-key":
        document["unknown"] = True
    elif damage == "build-key":
        document["interpreter_build"]["unknown"] = True
    elif damage == "row-key":
        row["unknown"] = True
    elif damage == "binding-key":
        row["bundled_files"][0]["unknown"] = True
    elif damage == "no-binding":
        row.pop("bundled_files")
        row.pop("bundled_version_source")
    elif damage == "bad-hash":
        row["bundled_files"][0]["sha256"] = "bad"
    elif damage == "duplicate-claim":
        other = {**row, "component": "Other native"}
        other.pop("bundled_version_source")
        document["components"].append(other)
    elif damage == "both-selectors":
        row["bundled_files"][0]["relpath_glob"] = "_internal/*.dll"
    elif damage == "unsafe-glob":
        row["bundled_files"][0] = {**row["bundled_files"][0], "name": "../fixture.dll"}
    else:
        row["bundled_files"][0]["size_bytes"] = True
    (native_surface / "manifest.json").write_text(json.dumps(document))
    expected = "native.*duplicate file claim" if damage == "duplicate-claim" else "native"
    with pytest.raises(ValueError, match=expected):
        module.load_native_licences(native_surface)


@pytest.mark.parametrize("body", [b"wrong! bytes", b"native bytes plus extra"])
def test_generic_native_binding_refuses_changed_hash_or_size(release, native_surface, body):
    module = load_notices()
    synthetic_native_binding(native_surface)
    (release["folder"] / "_internal/fixture.dll").write_bytes(body)
    with pytest.raises(ValueError, match=r"native.*identity.*file:_internal/fixture\.dll"):
        plan(module, release, native_licences_path=native_surface)


@pytest.mark.parametrize(
    "relative",
    [
        "libffi-8.dll",
        "PySide6/opengl32sw.dll",
        "numpy.libs/msvcp140-abc123.dll",
    ],
)
def test_exact_native_identity_takes_priority_over_record_or_interpreter(
    release, native_surface, relative
):
    module = load_notices()
    synthetic_native_binding(native_surface, selector={"name": Path(relative).name})
    target = release["folder"] / "_internal" / relative
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(b"native bytes")
    result = plan(module, release, native_licences_path=native_surface)
    label = "file:_internal/" + relative
    assert [row.name for row in result.rows if label in row.entries] == ["Fixture native"]


def test_missing_native_census_names_every_carried_file(release):
    module = load_notices()
    names = ["libffi-8.dll", "sqlite3.dll", "ucrtbase.dll", "opengl32sw.dll"]
    for name in names:
        (release["folder"] / "_internal" / name).write_bytes(b"missing native")
    with pytest.raises(ValueError) as caught:
        plan(module, release)
    assert all("file:_internal/" + name in str(caught.value) for name in names)


def test_openssl_version_source_alone_cannot_claim_bytes(release, native_surface):
    module = load_notices()
    path = native_surface / "manifest.json"
    document = json.loads(path.read_text())
    document["components"][0].pop("bundled_files")
    path.write_text(json.dumps(document))
    add_openssl(release)
    with pytest.raises(ValueError, match=r"OpenSSL.*missing native.*libcrypto-3-x64\.dll"):
        plan(module, release, native_licences_path=native_surface)


@pytest.mark.parametrize(
    "relative, body",
    [
        ("elsewhere/test.pyd", b"synthetic native extension"),
        ("test.pyd", b"wrong bytes"),
    ],
)
def test_basename_only_match_without_record_digest_never_claims_file(release, relative, body):
    module = load_notices()
    target = release["folder"] / "_internal" / relative
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(body)
    with pytest.raises(ValueError, match=re.escape(relative)):
        plan(module, release)


def provenance_fixture(surface, kind):
    """Make one synthetic row in the requested strict provenance form."""
    document = synthetic_native_binding(surface)
    row = document["components"][0]
    row["provenance_kind"] = kind
    if kind != "release-archive":
        for key in list(row):
            if key.startswith("source_") or key == "upstream_repository":
                row.pop(key)
    if kind == "git-tree":
        row.update(source_repository="https://example.com/fixture/project", source_commit="a" * 40)
    elif kind == "proprietary-redistributable":
        row["bundled_files"][0]["version_evidence"] = {
            "method": "pe_file_version",
            "value": "1.2.3",
        }
        row.update(
            text_kind="excerpt",
            text_source={
                "file": "<build interpreter>/LICENSE.txt",
                "lines": [283, 320],
                "sha256": "b" * 64,
                "size_bytes": 25066,
            },
            licence_urls=["https://example.com/terms", "https://example.com/redistribution"],
        )
    return document


@pytest.mark.parametrize("kind", ["release-archive", "git-tree", "proprietary-redistributable"])
def test_provenance_kinds_accept_exactly_their_own_form(native_surface, kind):
    """Each ruled provenance form carries an independently valid identity."""
    document = provenance_fixture(native_surface, kind)
    (native_surface / "manifest.json").write_text(json.dumps(document))
    records = load_notices().load_native_licences(native_surface)
    assert records[0].provenance_kind == kind


@pytest.mark.parametrize(
    "kind,foreign",
    [
        ("release-archive", {"source_repository": "https://example.com/project"}),
        ("release-archive", {"licence_urls": ["https://example.com/terms"]}),
        ("git-tree", {"source_archive_sha256": "c" * 64}),
        ("git-tree", {"licence_urls": ["https://example.com/terms"]}),
        ("proprietary-redistributable", {"source_archive_url": "https://example.com/source.zip"}),
        ("proprietary-redistributable", {"source_commit": "c" * 40}),
    ],
)
def test_provenance_kinds_refuse_mixed_forms(native_surface, kind, foreign):
    """Fields belonging to another kind cannot disguise missing provenance."""
    document = provenance_fixture(native_surface, kind)
    document["components"][0].update(foreign)
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="provenance"):
        load_notices().load_native_licences(native_surface)


@pytest.mark.parametrize("damage", ["unknown", "short-commit", "tag-only", "object-only"])
def test_provenance_kind_identity_errors_fail_closed(native_surface, damage):
    """Unknown kinds, short commits and unpaired annotated tags are refused."""
    document = provenance_fixture(native_surface, "git-tree")
    row = document["components"][0]
    if damage == "unknown":
        row["provenance_kind"] = "optional-everything"
    elif damage == "short-commit":
        row["source_commit"] = "a" * 39
    elif damage == "tag-only":
        row["source_tag"] = "v1"
    else:
        row["source_tag_object"] = "d" * 40
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="provenance"):
        load_notices().load_native_licences(native_surface)


NATIVE_CENSUS_NAMES = (
    "libffi",
    "Microsoft Visual C++ Redistributable (Microsoft Distributable Code)",
    "Mesa",
    "LLVM",
)


@pytest.mark.parametrize("component", NATIVE_CENSUS_NAMES)
def test_census_native_rows_validate_and_bind_synthetic_bytes(release, tmp_path, component):
    """Each real row verifies its text and refuses changed carried binary bytes."""
    module = load_notices()
    surface = tmp_path / "real-native-surface"
    shutil.copytree(ROOT / "tools/package/native-licences", surface)
    omit_production_embedded_census(surface)
    document = json.loads((surface / "manifest.json").read_text())
    row = next((r for r in document["components"] if r["component"] == component), None)
    assert row is not None, f"missing census row: {component}"
    related = {component, *row.get("co_licensed_with", [])}
    body = b"synthetic census binary; never executed"
    for item in document["components"]:
        if item["component"] in related:
            for binding in item["bundled_files"]:
                binding["sha256"] = hashlib.sha256(body).hexdigest()
                binding["size_bytes"] = len(body)
    (surface / "manifest.json").write_text(json.dumps(document))
    records = module.load_native_licences(surface)
    assert component in {r.component for r in records}
    for binding in row["bundled_files"]:
        target = release["folder"] / binding["relpath_glob"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    result = plan(module, release, native_licences_path=surface)
    actual = next(r for r in result.rows if r.name == component)
    assert len(actual.entries) == (11 if component.startswith("Microsoft") else 1)
    output = module.render_notices(result)
    assert (surface / row["text_file"]).read_bytes() in output
    if component in {"Mesa", "LLVM"}:
        assert b"| Mesa |" in output and b"| LLVM |" in output
        assert (surface / "mesa-11.2.2-docs-license.html").read_bytes() in output
        assert (surface / "llvm-3.6.2-LICENSE.TXT").read_bytes() in output
    if component.startswith("Microsoft"):
        assert b"<build interpreter>/LICENSE.txt, lines 283-320" in output
        assert b"886a0ead2d89030ee62dbff52b04e47ab91998341295bb9c56fb952b4e081c7a" in output
        assert all(
            b["version_evidence"]["method"] == "pe_file_version" for b in row["bundled_files"]
        )
        assert b"https://visualstudio.microsoft.com/license-terms/" in output
        assert (
            b"https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution" in output
        )
    target.write_bytes(b"corrupt synthetic binary")
    with pytest.raises(ValueError, match="native file identity"):
        plan(module, release, native_licences_path=surface)
    target.write_bytes(body)
    text = surface / row["text_file"]
    text.write_bytes(text.read_bytes() + b"x")
    with pytest.raises(ValueError, match="native licence text"):
        module.load_native_licences(surface)


@pytest.mark.parametrize("damage", ["missing", "wrong-method", "empty"])
def test_proprietary_files_require_each_measured_file_version(native_surface, damage):
    """One row cannot hide multiple runtime versions behind a row-level label."""
    document = provenance_fixture(native_surface, "proprietary-redistributable")
    binding = document["components"][0]["bundled_files"][0]
    if damage == "missing":
        binding.pop("version_evidence")
    elif damage == "wrong-method":
        binding["version_evidence"] = {"method": "embedded_string", "value": "1.2.3"}
    elif damage == "empty":
        binding["version_evidence"] = {"method": "pe_file_version", "value": ""}
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="version_evidence"):
        load_notices().load_native_licences(native_surface)


@pytest.mark.parametrize("namespace", ["scipy._external", "scipy._external.packaging_version"])
def test_record_directory_maps_namespace_without_a_file(release, namespace):
    """A namespace owner comes from RECORD files beneath an exact directory."""
    add_distribution(
        release,
        "scipy",
        "1.18.1",
        {
            "scipy/_external/packaging_version/version.py": "",
            "scipy-1.18.1.dist-info/LICENSE.txt": "synthetic BSD",
        },
        [namespace],
    )
    result = plan(load_notices(), release)
    assert "pyz:" + namespace in next(r for r in result.rows if r.name == "scipy").entries


@pytest.mark.parametrize("damage", ["lookalike", "ambiguous"])
def test_namespace_directory_owner_is_exact_and_unique(release, damage):
    """A sibling prefix or two RECORD owners must never claim a namespace."""
    add_distribution(
        release,
        "scipy",
        "1.18.1",
        {
            ("scipy_evil" if damage == "lookalike" else "scipy") + "/_external/code.py": "",
            "scipy-1.18.1.dist-info/LICENSE.txt": "synthetic BSD",
        },
        ["scipy._external"],
    )
    if damage == "ambiguous":
        add_distribution(
            release,
            "other",
            "1.0",
            {
                "scipy/_external/other.py": "",
                "other-1.0.dist-info/LICENSE.txt": "synthetic MIT",
            },
            ["scipy._external"],
        )
    with pytest.raises(
        ValueError, match=r"unknown or ambiguous bundled entry pyz:scipy\._external"
    ):
        plan(load_notices(), release)


def declared_vendored_fixture(release, *, files=None, modules=None):
    """Install one synthetic declaration independently of its optional block."""
    add_distribution(
        release,
        "scipy",
        "1.18.1",
        files
        if files is not None
        else {
            "scipy/_external/cobyqa/__init__.py": "",
            "scipy/_external/_array_api_compat_vendor.py": "",
            "scipy-1.18.1.dist-info/LICENSE.txt": "synthetic BSD",
        },
        modules
        if modules is not None
        else ["scipy._external.cobyqa", "scipy._external._array_api_compat_vendor"],
    )
    path = release["native_surface"] / "manifest.json"
    document = json.loads(path.read_text())
    document["vendored_paths"] = [
        {
            "distribution": "scipy",
            "module": "scipy._external.cobyqa",
            "component": "fixture cobyqa",
        }
    ]
    path.write_text(json.dumps(document))
    return document


def test_declared_vendored_module_without_block_fails_closed(release):
    """A wheel RECORD is insufficient for a declared separately licensed subtree."""
    declared_vendored_fixture(release)
    with pytest.raises(ValueError, match=r"vendored.*missing.*block"):
        plan(load_notices(), release)


def test_vendored_block_covers_only_its_path_and_keeps_parent_shim(release):
    """The declared vendored package gets its text; SciPy's own shim stays BSD."""
    document = declared_vendored_fixture(release)
    row = copy.deepcopy(document["components"][0])
    row.update(
        component="fixture cobyqa",
        vendored_distribution="scipy",
        vendored_distribution_version="1.18.1",
        bundled_modules=["scipy._external.cobyqa", "scipy._external.cobyqa.*"],
        version_evidence={"method": "vendored_submodule_commit", "value": "a" * 40},
    )
    row.pop("bundled_version_source")
    row.pop("bundled_files")
    document["components"].append(row)
    (release["native_surface"] / "manifest.json").write_text(json.dumps(document))
    module = load_notices()
    result = plan(module, release)
    assert next(r for r in result.rows if r.name == "fixture cobyqa").entries == (
        "pyz:scipy._external.cobyqa",
    )
    assert (
        "pyz:scipy._external._array_api_compat_vendor"
        in next(r for r in result.rows if r.name == "scipy").entries
    )
    assert b"vendored_submodule_commit" in module.render_notices(result)


SCIPY_BLOCKS = (
    ("array-api-compat", "array_api_compat", "MIT"),
    ("array-api-extra", "array_api_extra", "MIT"),
    ("cobyqa", "cobyqa", "BSD-3-Clause"),
    ("prima (pyprima)", "pyprima", "BSD-3-Clause"),
    ("packaging.version", "packaging_version", "BSD-2-Clause"),
)


@pytest.mark.parametrize("component,path,spdx", SCIPY_BLOCKS)
def test_real_scipy_vendored_blocks_bind_module_inventory(release, tmp_path, component, path, spdx):
    """Each seat text is selected by its actual declared PYZ path, not by wheel ownership alone."""
    module = load_notices()
    surface = tmp_path / "vendored-real-surface"
    shutil.copytree(ROOT / "tools/package/native-licences", surface)
    omit_production_embedded_census(surface)
    records = module.load_native_licences(surface)
    record = next((r for r in records if r.component == component), None)
    assert record is not None, f"missing SciPy component: {component}"
    prefix = "scipy._external." + path
    add_distribution(
        release,
        "scipy",
        "1.18.1",
        {
            prefix.replace(".", "/") + "/code.py": "",
            "scipy/_external/_array_api_compat_vendor.py": "",
            "scipy-1.18.1.dist-info/LICENSE.txt": "synthetic BSD",
        },
        [prefix, prefix + ".code", "scipy._external", "scipy._external._array_api_compat_vendor"],
    )
    result = plan(module, release, native_licences_path=surface)
    row = next(r for r in result.rows if r.name == component)
    assert row.licence == spdx
    assert row.entries == ("pyz:" + prefix, "pyz:" + prefix + ".code")
    assert record.licence_input.path.read_bytes() in module.render_notices(result)
    assert "pyz:scipy._external" in next(r for r in result.rows if r.name == "scipy").entries
    record.licence_input.path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="native licence text"):
        module.load_native_licences(surface)


@pytest.mark.parametrize("damage", ["sha256", "size_bytes", "lines"])
def test_msvc_excerpt_is_bound_to_the_build_interpreter(release, tmp_path, damage):
    """A carried runtime cannot render an excerpt attributed to a different build licence."""
    surface = tmp_path / "msvc-source-surface"
    shutil.copytree(ROOT / "tools/package/native-licences", surface)
    document = json.loads((surface / "manifest.json").read_text())
    row = next(r for r in document["components"] if r["component"].startswith("Microsoft"))
    for binding in row["bundled_files"]:
        body = b"synthetic runtime binary"
        binding["sha256"] = hashlib.sha256(body).hexdigest()
        binding["size_bytes"] = len(body)
        target = release["folder"] / binding["relpath_glob"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    row["text_source"][damage] = {"sha256": "0" * 64, "size_bytes": 1, "lines": [1, 2]}[damage]
    (surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match=r"(text source|excerpt)"):
        plan(load_notices(), release, native_licences_path=surface)


@pytest.mark.parametrize("wrong_version", [False, True])
def test_vendored_block_can_bind_only_files_and_still_checks_distribution_version(
    release, wrong_version
):
    """File-only vendored blocks retain hash and parent-wheel version requirements."""
    document = declared_vendored_fixture(release)
    row = copy.deepcopy(document["components"][0])
    row.pop("bundled_version_source")
    body = b"synthetic vendored file"
    relative = "_internal/scipy/_external/cobyqa/data.bin"
    row.update(
        component="fixture cobyqa",
        vendored_distribution="scipy",
        vendored_distribution_version="0.0" if wrong_version else "1.18.1",
        version_evidence={"method": "vendored_submodule_commit", "value": "a" * 40},
        bundled_files=[
            {
                "relpath_glob": relative,
                "sha256": hashlib.sha256(body).hexdigest(),
                "size_bytes": len(body),
            }
        ],
    )
    document["components"].append(row)
    (release["native_surface"] / "manifest.json").write_text(json.dumps(document))
    make_executable(
        release["folder"], ["clearwater", "numpy", "scipy._external._array_api_compat_vendor"]
    )
    target = release["folder"] / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    module = load_notices()
    if wrong_version:
        with pytest.raises(ValueError, match="vendored distribution version"):
            plan(module, release)
    else:
        result = plan(module, release)
        assert next(r for r in result.rows if r.name == "fixture cobyqa").entries == (
            "file:" + relative,
        )
        target.write_bytes(b"changed bytes")
        with pytest.raises(ValueError, match="native file identity"):
            plan(module, release)


@pytest.mark.parametrize("kind", ["git-tree", "release-archive"])
@pytest.mark.parametrize("field", ["text_source", "text_kind"])
def test_nonproprietary_rows_refuse_excerpt_fields(native_surface, kind, field):
    """F1: unverified excerpt claims must not enter either source-bearing kind."""
    document = provenance_fixture(native_surface, kind)
    document["components"][0][field] = {
        "text_kind": "excerpt",
        "text_source": {
            "file": "invented LICENSE",
            "lines": [1, 999],
            "sha256": "0" * 64,
            "size_bytes": 1,
        },
    }[field]
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="provenance"):
        load_notices().load_native_licences(native_surface)


@pytest.mark.parametrize("filename", ["__init__.py", "_fast.pyd", "data.bin"])
def test_declared_vendored_files_cannot_fall_through_to_parent(release, filename):
    """F2: a declared subtree needs its block even when only files are shipped."""
    relative = "scipy/_external/cobyqa/" + filename
    declared_vendored_fixture(
        release,
        files={relative: "vendored bytes", "scipy-1.18.1.dist-info/LICENSE.txt": "synthetic BSD"},
        modules=[],
    )
    make_executable(release["folder"], ["clearwater", "numpy"])
    target = release["folder"] / "_internal" / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"vendored bytes")
    with pytest.raises(ValueError, match=r"vendored.*missing.*block.*" + re.escape(filename)):
        plan(load_notices(), release)


@pytest.mark.parametrize("linked", [False, True])
def test_co_licence_link_requires_nonempty_file_bindings(native_surface, linked):
    """F3: module-only rows cannot promise that an uncarried co-owner is required."""
    document = co_licensed_surface(native_surface)
    for row in document["components"]:
        row.pop("bundled_files")
        row.update(component=row["component"], bundled_version_source="ssl.OPENSSL_VERSION")
    # Use real supported version-source rows; no bytes are claimed by either row.
    first, second = document["components"]
    first["component"] = "OpenSSL"
    first["co_licensed_with"] = [second["component"]]
    second.pop("bundled_version_source")
    second.update(
        vendored_distribution="scipy",
        vendored_distribution_version="1.18.1",
        bundled_modules=["scipy._external.fixture"],
        version_evidence={"method": "vendored_submodule_commit", "value": "a" * 40},
        co_licensed_with=["OpenSSL"],
    )
    document["vendored_paths"] = [
        {
            "distribution": "scipy",
            "module": "scipy._external.fixture",
            "component": second["component"],
        }
    ]
    if not linked:
        first["co_licensed_with"] = []
        second["co_licensed_with"] = []
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match=r"co_licensed_with.*(file|binding)"):
        load_notices().load_native_licences(native_surface)


def test_clearwater_own_licence_is_lf_normalized_before_hashing(release, tmp_path):
    """k2: checkout CRLF changes neither the rendered project text nor its digest."""
    module = load_notices()
    original = plan(module, release)
    text = tmp_path / "LICENSE"
    lf = b"project licence\nsecond line\n"
    text.write_bytes(lf)
    rows = tuple(
        row._replace(licence_inputs=(module.LicenceInput(text),))
        if row.name == "Clearwater"
        else row
        for row in original.rows
    )
    planned = original._replace(rows=rows)
    expected = module.render_notices(planned)
    text.write_bytes(lf.replace(b"\n", b"\r\n"))
    actual = module.render_notices(planned)
    assert actual == expected
    assert hashlib.sha256(lf).hexdigest().encode() in actual
    assert lf in actual and b"project licence\r\n" not in actual


def test_in_tree_component_labels_and_llvm_source_subtree():
    """k1/F4: artifact pointers describe in-tree code and LLVM's actual subtree."""
    module = load_notices()
    records = {
        row.component: row
        for row in module.load_native_licences(ROOT / "tools/package/native-licences")
    }
    for component in ("prima (pyprima)", "packaging.version"):
        assert records[component].version_evidence[0] == "vendored_in_tree_path"
    assert records["LLVM"].source_path == "llvm"
    assert records["LLVM"].source_urls[0].endswith("/llvm")
    assert not records["Mesa"].source_path


@pytest.mark.parametrize("path", ["/abs", "a/../b", "a\\b", "C:/x", "a//b", "a/", "./a", "", ".."])
def test_git_tree_source_path_refuses_unsafe_values(native_surface, path):
    """A4 claim 1: deleting source_path safety must admit an invalid pointer."""
    document = provenance_fixture(native_surface, "git-tree")
    document["components"][0]["source_path"] = path
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="unsafe source_path"):
        load_notices().load_native_licences(native_surface)


def test_vendored_prefix_sibling_keeps_parent_licence(release):
    """A4 claim 2: a cobyqa_evil sibling is outside cobyqa's declaration."""
    declared_vendored_fixture(
        release,
        files={
            "scipy/_external/cobyqa_evil/__init__.py": "",
            "scipy-1.18.1.dist-info/LICENSE.txt": "synthetic BSD",
        },
        modules=["scipy._external.cobyqa_evil"],
    )
    module = load_notices()
    result = plan(module, release)
    assert (
        "pyz:scipy._external.cobyqa_evil"
        in next(row for row in result.rows if row.name == "scipy").entries
    )
    assert not any(row.name == "fixture cobyqa" for row in result.rows)


def test_co_licence_asymmetry_is_refused_before_duplicate_claim_check(native_surface):
    """A4 claim 3: a different selector cannot mask a missing mutual back-link."""
    document = co_licensed_surface(native_surface)
    second = document["components"][1]
    second.pop("co_licensed_with")
    second["bundled_files"][0].pop("name")
    second["bundled_files"][0]["relpath_glob"] = "_internal/fixture.dll"
    (native_surface / "manifest.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="dangling/asymmetric link"):
        load_notices().load_native_licences(native_surface)


def embedded_host_fixture(release, *, parent="python", carried=True):
    """Declare synthetic embedded sources independently of their licence rows."""
    if parent == "pyside6-essentials":
        add_distribution(
            release,
            parent,
            "6.12.0",
            {
                "PySide6/QtCore.dll": "synthetic Qt host",
                "pyside6_essentials-6.12.0.dist-info/licenses/LGPL-3.0.txt": (
                    "GNU LESSER GENERAL PUBLIC LICENSE\nsynthetic Qt terms\n"
                ),
            },
            [],
        )
        append_upstream_audit(release)
    relative = {
        "python": "_internal/python312.dll",
        "numpy": "_internal/numpy/_core/test.pyd",
        "pyside6-essentials": "_internal/PySide6/QtCore.dll",
    }[parent]
    host = release["folder"] / relative
    body = host.read_bytes()
    surface = release["native_surface"]
    document = json.loads((surface / "manifest.json").read_text())
    source = {
        "provenance_kind": "git-tree",
        "source_repository": "https://example.org/synthetic-source",
        "source_commit": "a" * 40,
        "source_tag": "v1.0",
        "source_tag_object": "b" * 40,
        "source_path": "Doc/synthetic-licence.rst",
    }
    names = ["Embedded alpha", "Embedded gamma", "Embedded beta"]
    document["embedded_hosts"] = [
        {
            "relpath": relative,
            "sha256": hashlib.sha256(body).hexdigest(),
            "size_bytes": len(body),
            "parent": parent,
            "parent_version": (
                ".".join(map(str, sys.version_info[:3]))
                + " (python-build-standalone "
                + (Path(sys.base_prefix) / "BUILD").read_text().strip()
                + ")"
                if parent == "python"
                else release["distributions"][parent].version
            ),
            "components": [{"component": name, "source": copy.deepcopy(source)} for name in names],
        }
    ]
    text = b"Synthetic embedded terms, shared by alpha and beta.\n"
    (surface / "embedded-terms.txt").write_bytes(text)
    for name in names:
        terms = b"Synthetic distinct gamma terms.\n" if name == "Embedded gamma" else text
        filename = "gamma-terms.txt" if name == "Embedded gamma" else "embedded-terms.txt"
        (surface / filename).write_bytes(terms)
        document["components"].append(
            {
                "component": name,
                **source,
                "upstream_version": "synthetic-1.0",
                "spdx": "MIT",
                "text_file": filename,
                "text_sha256": hashlib.sha256(terms).hexdigest(),
                "text_size_bytes": len(terms),
                "fetch_date": "2026-11-05",
                "fetched_by": "seat",
                "version_evidence": {"method": "interpreter_build_record", "value": "fixture"},
                "embedded_in": [relative],
            }
        )
    for reference in document["embedded_hosts"][0]["components"]:
        row = next(
            row for row in document["components"] if row["component"] == reference["component"]
        )
        reference["source"].update(
            {key: row[key] for key in ("text_file", "text_sha256", "text_size_bytes")}
        )
    if not carried:
        host.unlink()
    save_embedded_fixture(release, document)
    return document, host, text


def save_embedded_fixture(release, document):
    """Write only the test copy's manifest after a negative-control mutation."""
    (release["native_surface"] / "manifest.json").write_text(json.dumps(document))


@pytest.mark.parametrize("change", ["renamed", "moved", "duplicate"])
def test_embedded_renamed_or_moved_host_requires_recensus(release, change):
    """Wheel ownership at a new path must not drop the embedded census."""
    _document, host, _text = embedded_host_fixture(release, parent="numpy")
    new = host.with_name("test-newhash.pyd")
    new.write_bytes(b"new wheel build" if change == "renamed" else host.read_bytes())
    if change != "duplicate":
        host.unlink()
    installed_old = release["site"] / "numpy/_core/test.pyd"
    installed_new = installed_old.with_name(new.name)
    installed_new.write_bytes(new.read_bytes())
    if change != "duplicate":
        installed_old.unlink()
    record = release["site"] / "numpy-2.5.4.dist-info/RECORD"
    old_record = record.read_text()
    record.write_text(
        old_record.replace("numpy/_core/test.pyd", "numpy/_core/test-newhash.pyd")
        if change != "duplicate"
        else old_record + "numpy/_core/test-newhash.pyd,,\n"
    )
    release["distributions"]["numpy"] = importlib.metadata.PathDistribution(record.parent)
    with pytest.raises(ValueError) as error:
        plan(load_notices(), release)
    message = str(error.value)
    assert host.name in message and "re-census required" in message
    assert (
        ("moved" in message and new.name in message) if change != "renamed" else "numpy" in message
    )


@pytest.mark.parametrize("change", ["renamed", "same-name"])
def test_embedded_content_hashed_wheel_dll_requires_recensus(release, change):
    """A rebuilt DLL needs re-census even when its wheel parent version is unchanged."""
    document, _host, _text = embedded_host_fixture(release, parent="numpy")
    add_heif(release, native=False)
    name = "libx265-217-276e7d75772a32bd086b54d54e01fd11.dll"
    relative = "_internal/" + name
    wheel_relative = "pillow_heif.libs/" + name
    body = b"synthetic pillow-heif x265 census build"
    host = release["folder"] / relative
    host.write_bytes(body)
    wheel_host = release["site"] / wheel_relative
    wheel_host.parent.mkdir()
    wheel_host.write_bytes(body)
    record = release["site"] / "pillow_heif-1.8.1.dist-info/RECORD"

    def record_line(path, data):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        return f"{path},sha256={digest},{len(data)}\n"

    with record.open("a") as stream:
        stream.write(record_line(wheel_relative, body))
    declared = document["embedded_hosts"][0]
    declared.update(
        relpath=relative,
        sha256=hashlib.sha256(body).hexdigest(),
        size_bytes=len(body),
        parent="pillow-heif",
        parent_version="1.8.1",
    )
    for row in document["components"]:
        if "embedded_in" in row:
            row["embedded_in"] = [relative]
    save_embedded_fixture(release, document)
    release["distributions"]["pillow-heif"] = importlib.metadata.PathDistribution(record.parent)
    result = plan(load_notices(), release)
    parent = next(row for row in result.rows if row.name == "pillow-heif")
    assert parent.version == "1.8.1"
    embedded = next(row for row in result.rows if row.name == "Embedded alpha")
    assert "file:" + relative in embedded.entries
    metadata = record.with_name("METADATA").read_bytes()

    new_name = "libx265-217-0123456789abcdef0123456789abcdef.dll" if change == "renamed" else name
    new_body = b"different pillow-heif x265 build bytes"
    new_host = host.with_name(new_name)
    new_wheel_host = wheel_host.with_name(new_name)
    host.unlink()
    wheel_host.unlink()
    new_host.write_bytes(new_body)
    new_wheel_host.write_bytes(new_body)
    record.write_text(
        record.read_text().replace(
            record_line(wheel_relative, body),
            record_line("pillow_heif.libs/" + new_name, new_body),
        )
    )
    release["distributions"]["pillow-heif"] = importlib.metadata.PathDistribution(record.parent)
    assert record.with_name("METADATA").read_bytes() == metadata
    assert release["distributions"]["pillow-heif"].version == "1.8.1"
    assert record_line("pillow_heif.libs/" + new_name, new_body) in record.read_text()
    assert record_line(wheel_relative, body) not in record.read_text()
    assert (release["site"] / "pillow_heif.libs" / new_name).is_file()
    with pytest.raises(ValueError) as error:
        plan(load_notices(), release)
    message = str(error.value)
    assert relative in message and "re-census required" in message
    if change == "renamed":
        assert "pillow-heif" in message and "absent" in message
    else:
        assert "identity differs" in message
        assert declared["sha256"] in message
        assert hashlib.sha256(new_body).hexdigest() in message


def test_embedded_absent_host_with_carried_parent_requires_recensus(release):
    """Missing native bytes cannot disappear when the parent still ships modules."""
    _document, host, _text = embedded_host_fixture(release, parent="numpy", carried=False)
    with pytest.raises(ValueError, match=re.escape(host.name) + r".*numpy.*re-census required"):
        plan(load_notices(), release)


def test_embedded_parent_upgrade_requires_recensus(release):
    """A legitimate lock/audit/installed upgrade still needs fresh host evidence."""
    _document, host, _text = embedded_host_fixture(release, parent="numpy")
    for path in (
        release["site"] / "numpy-2.5.4.dist-info/METADATA",
        release["uv_lock"],
        release["audit"],
    ):
        path.write_text(path.read_text().replace("2.5.4", "2.5.5"))
    with pytest.raises(ValueError, match=host.name + ".*numpy.*2.5.4.*2.5.5.*re-census required"):
        plan(load_notices(), release)


def test_embedded_unknown_parent_requires_recensus_even_when_host_is_absent(release):
    """A misspelled census parent must not silently omit all embedded rows."""
    document, host, _text = embedded_host_fixture(release, parent="numpy", carried=False)
    document["embedded_hosts"][0]["parent"] = "numpy-typo"
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError) as error:
        plan(load_notices(), release)
    message = str(error.value)
    assert host.name in message and "numpy-typo" in message
    assert "declared parent unknown to this build; re-census required" in message


@pytest.mark.parametrize("value", [None, "", " version", "version\nforged", 1])
def test_embedded_parent_census_version_is_required(release, value):
    """Host declarations must pin a single nonempty parent build identity."""
    document, _host, _text = embedded_host_fixture(release)
    if value is None:
        document["embedded_hosts"][0].pop("parent_version")
    else:
        document["embedded_hosts"][0]["parent_version"] = value
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match="embedded host"):
        plan(load_notices(), release)


def test_embedded_whole_text_swap_requires_independent_host_pin(release):
    """Updating the component text alone must not update the host's independent pin."""
    document, host, _text = embedded_host_fixture(release)
    row = document["components"][-1]
    terms = b"Different, self-consistently hashed terms.\n"
    (release["native_surface"] / "new-terms.txt").write_bytes(terms)
    row.update(
        text_file="new-terms.txt",
        text_sha256=hashlib.sha256(terms).hexdigest(),
        text_size_bytes=len(terms),
    )
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match=host.name + ".*Embedded beta.*source pin"):
        plan(load_notices(), release)


@pytest.mark.parametrize("key", ["component", "statement"])
@pytest.mark.parametrize("control", ["\n", "\r", "\t", "\0", "\x1b", "\x7f", "\x85"])
def test_limits_refuse_control_characters(release, key, control):
    """A limits value cannot inject another Markdown section or console control."""
    document, _host = limits_fixture(release)
    document["limits"][0][key] = "before" + control + "## forged"
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match="limits"):
        plan(load_notices(), release)


def test_git_excerpt_counts_only_lf_as_a_line_boundary(release):
    """A lone CR is source content, not a second line in Git's numbering."""
    document, _host, _terms = git_excerpt_fixture(release)
    blob = b"header\rcontinued\nnext\n"
    terms = b"header\rcontinued\n"
    surface = release["native_surface"]
    (surface / "source-blob.c").write_bytes(blob)
    (surface / "header-excerpt.txt").write_bytes(terms)
    row = document["components"][-1]
    row.update(text_sha256=hashlib.sha256(terms).hexdigest(), text_size_bytes=len(terms))
    row["text_lines"].update(
        lines=[1, 1],
        sha256=hashlib.sha256(blob).hexdigest(),
        size_bytes=len(blob),
        git_blob_sha1=hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest(),
    )
    document["embedded_hosts"][0]["components"][-1]["source"].update(
        **{key: row[key] for key in ("text_sha256", "text_size_bytes", "text_lines")}
    )
    save_embedded_fixture(release, document)
    module = load_notices()
    assert terms in module.render_notices(plan(module, release))


@pytest.mark.parametrize(
    "reference_name,original_name,audit",
    [
        ("GCC runtime (SciPy static)", "scipy", True),
        ("MinGW", "pillow-heif", False),
        ("libsharpyuv/libyuv (Pillow)", "pillow", False),
    ],
)
def test_shared_reference_preserves_original_heading(
    tmp_path, reference_name, original_name, audit
):
    """Reference sort order must not replace the source wheel/audit provenance label."""
    module = load_notices()
    terms = b"Synthetic original terms\n"
    digest = hashlib.sha256(terms).hexdigest()
    path = tmp_path / "original.txt"
    if audit:
        path.write_text(
            '<a id="terms"></a>\nSource: `https://example.org/terms`. '
            f"SHA-256: `{digest}`. UTF-8/LF bytes: {len(terms)}.\n"
            "````text\n" + terms.decode() + "````\n"
        )
        item = module.LicenceInput(path, block_id="terms")
        label = f"{original_name} 1; https://example.org/terms; the 1.0.0 audit's upstream copy"
    else:
        path.write_bytes(terms)
        item = module.LicenceInput(path)
        label = f"Installed wheel: {original_name} 1; original.txt"
    original = module.NoticeRow(
        original_name, "1", "MIT", ("https://example.org",), ("file:host.pyd",), (item,)
    )
    record = {
        "component": reference_name,
        "upstream_version": "runtime",
        "spdx": "MIT",
        "embedded_in": ["host.pyd"],
        "version_evidence": {"method": "embedded_string", "value": "fixture"},
        "carried_notice": {
            "row": original_name,
            "inputs": [{"sha256": digest, "size_bytes": len(terms)}],
        },
    }
    reused = module._carried_notice_rows(
        {"components": [record]}, {reference_name: [("file:host.pyd", "a" * 64)]}, [original]
    )
    rendered = module.render_notices(module.NoticePlan(original.entries, (*reused, original), ()))
    assert rendered.count(terms) == 1
    assert ("### " + label + "\n").encode() in rendered
    assert ("Source: " + label + ". SHA-256:").encode() in rendered


def omit_parent(release, parent):
    """Remove carried parent entries while retaining installed build metadata."""
    if parent == "numpy":
        make_executable(release["folder"], ["clearwater", "json"])
    elif parent == "python":
        (release["folder"] / "_internal/python312.dll").unlink(missing_ok=True)
        make_executable(release["folder"], ["clearwater", "numpy", "numpy.linalg"])


LIMITS_HEADING = b"## Components with no carried licence text, and limits\n\n"


def limits_fixture(release):
    """Bind both text-bearing and textless statements to independently measured hosts."""
    document, host, _text = embedded_host_fixture(release)
    relative = host.relative_to(release["folder"]).as_posix()
    document["limits"] = [
        {
            "component": "Textless algorithm",
            "hosts": [relative],
            "statement": "No statement exists.",
        },
        {"component": "Embedded alpha", "hosts": [relative], "statement": "Inclusion is inferred."},
    ]
    save_embedded_fixture(release, document)
    return document, host


@pytest.mark.parametrize(
    "damage",
    [
        "top-key",
        "entry-key",
        "missing-key",
        "not-list",
        "not-entry",
        "undeclared",
        "duplicate-component",
        "blank-component",
        "trim-component",
        "bad-component",
        "blank-statement",
        "trim-statement",
        "bad-statement",
        "empty-hosts",
        "not-hosts",
        "duplicate-host",
        "unsafe-host",
        "unsorted-hosts",
    ],
)
def test_limits_schema_refuses_invalid_or_undeclared_statements(release, damage):
    """Limits cannot bypass exact schema, declaration or deterministic-host requirements."""
    document, _host = limits_fixture(release)
    entry = document["limits"][0]
    if damage == "top-key":
        document["unexpected"] = []
    elif damage == "entry-key":
        entry["unexpected"] = "unknown"
    elif damage == "missing-key":
        del entry["statement"]
    elif damage == "not-list":
        document["limits"] = {}
    elif damage == "not-entry":
        document["limits"] = [None]
    elif damage == "undeclared":
        entry["hosts"] = ["_internal/absent.pyd"]
    elif damage == "duplicate-component":
        document["limits"].append(copy.deepcopy(entry))
    elif damage in {"blank-component", "trim-component", "bad-component"}:
        entry["component"] = {"blank-component": "", "trim-component": " name", "bad-component": 1}[
            damage
        ]
    elif damage in {"blank-statement", "trim-statement", "bad-statement"}:
        entry["statement"] = {
            "blank-statement": " ",
            "trim-statement": "terms ",
            "bad-statement": None,
        }[damage]
    elif damage == "empty-hosts":
        entry["hosts"] = []
    elif damage == "not-hosts":
        entry["hosts"] = entry["hosts"][0]
    elif damage == "duplicate-host":
        entry["hosts"] *= 2
    elif damage == "unsafe-host":
        entry["hosts"] = ["../host.pyd"]
    else:
        second = copy.deepcopy(document["embedded_hosts"][0])
        second["relpath"] = "_internal/another.pyd"
        document["embedded_hosts"].append(second)
        entry["hosts"].append(second["relpath"])
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match="schema" if damage == "top-key" else "limits"):
        load_notices().load_native_licences(release["native_surface"])


def test_limits_empty_or_absent_preserves_existing_render_bytes(release):
    """Optional empty lists leave the complete pre-limits output byte-identical."""
    document, _host, _text = embedded_host_fixture(release)
    module = load_notices()
    before = module.render_notices(plan(module, release))
    assert LIMITS_HEADING not in before
    document["limits"] = []
    save_embedded_fixture(release, document)
    assert module.render_notices(plan(module, release)) == before


def test_limits_render_both_carried_text_and_verbatim_statement_in_sorted_section(release):
    """Statements remain separate from text rows and sort independently of manifest order."""
    document, host = limits_fixture(release)
    module = load_notices()
    result = plan(module, release)
    before = module.render_notices(result)
    relative = host.relative_to(release["folder"]).as_posix()
    expected = (
        LIMITS_HEADING.decode()
        + "Component: Embedded alpha\nHosts: file:"
        + relative
        + "\nInclusion is inferred.\n\nComponent: Textless algorithm\nHosts: file:"
        + relative
        + "\nNo statement exists.\n\n"
    ).encode()
    assert expected in before
    assert before.index(b"### Embedded alpha\n") < before.index(expected)
    assert before.index(expected) < before.index(b"## Full licence texts and provenance")
    assert b"Synthetic embedded terms, shared by alpha and beta.\n" in before
    assert not any(row.name == "Textless algorithm" for row in result.rows)
    document["limits"].reverse()
    save_embedded_fixture(release, document)
    assert module.render_notices(plan(module, release)) == before


@pytest.mark.parametrize("carried", [0, 1, 2])
def test_limits_absent_hosts_follow_embedded_claims_and_only_name_carried_hosts(release, carried):
    """All-absent statements disappear; partial carriage retains only the actual hosts."""
    document, first = limits_fixture(release)
    relative = "_internal/numpy/_core/test.pyd"
    second = release["folder"] / relative
    host = copy.deepcopy(document["embedded_hosts"][0])
    host.update(
        relpath=relative,
        parent="numpy",
        parent_version="2.5.4",
        sha256=hashlib.sha256(second.read_bytes()).hexdigest(),
        size_bytes=second.stat().st_size,
    )
    document["embedded_hosts"].append(host)
    for row in document["components"][1:]:
        row["embedded_in"].append(relative)
    for entry in document["limits"]:
        entry["hosts"] = sorted([relative, first.relative_to(release["folder"]).as_posix()])
    if carried < 2:
        second.unlink()
        omit_parent(release, "numpy")
    if carried == 0:
        first.unlink()
        make_executable(release["folder"], ["clearwater"])
    save_embedded_fixture(release, document)
    module = load_notices()
    rendered = module.render_notices(plan(module, release))
    if carried == 0:
        assert LIMITS_HEADING not in rendered
    else:
        section = rendered.split(LIMITS_HEADING)[1].split(b"## Full licence texts")[0]
        actual = [
            name for name in document["limits"][0]["hosts"] if (release["folder"] / name).exists()
        ]
        assert ("Hosts: " + ", ".join("file:" + name for name in actual)).encode() in section
        assert (relative.encode() in section) == (carried == 2)


def test_limits_only_component_cannot_weaken_host_identity_check(release):
    """A limits-only dangling binding cannot be silently omitted during selection."""
    document, _host = limits_fixture(release)
    # The absent textless host has no embedded rows for _embedded_claims to check.
    document["limits"][0]["hosts"] = ["_internal/undeclared-textless.pyd"]
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match=r"limits.*Textless algorithm.*undeclared-textless"):
        plan(load_notices(), release)


def test_production_limits_bind_every_commissioned_host_to_its_census():
    """All seventeen commissioned limits use exact declared identities, without new texts."""
    module = load_notices()
    folder = ROOT / "tools/package/native-licences"
    document = json.loads((folder / "manifest.json").read_bytes())
    module.load_native_licences(folder)
    entries = document.get("limits", [])
    assert len(entries) == 17
    assert [entry["component"] for entry in entries] == sorted(
        entry["component"] for entry in entries
    )
    declared = {host["relpath"] for host in document["embedded_hosts"]}
    by_name = {entry["component"]: entry for entry in entries}
    for entry in entries:
        assert set(entry["hosts"]) <= declared
        assert entry["hosts"] == sorted(set(entry["hosts"]))
    suffix = ".cp312-win_amd64.pyd"
    assert by_name["QUADPACK"]["hosts"] == ["_internal/scipy/integrate/_quadpack" + suffix]
    assert by_name["FITPACK"]["hosts"] == [
        "_internal/scipy/interpolate/" + name + suffix for name in ("_dierckx", "_fitpack")
    ]
    scipy = sorted(
        path for path in declared if path.startswith("_internal/scipy/") and path.endswith(".pyd")
    )
    assert len(scipy) == 82
    for name in ("Cython-generated code (U-S8)", "Ryu / fast_float in SciPy (U-H3)"):
        assert by_name[name]["hosts"] == scipy
    assert len(by_name["mdspan (Kokkos, U-S6)"]["hosts"]) == 7


def git_excerpt_fixture(release):
    """Bind a header excerpt to its complete, independently hashed source blob."""
    document, host, _text = embedded_host_fixture(release)
    blob = b"/*\r\nSynthetic header terms.\r\n*/\r\nint implementation;\r\n"
    surface = release["native_surface"]
    (surface / "source-blob.c").write_bytes(blob)
    terms = b"/*\r\nSynthetic header terms.\r\n*/\r\n"
    (surface / "header-excerpt.txt").write_bytes(terms)
    row = document["components"][-1]
    row.update(
        text_file="header-excerpt.txt",
        text_sha256=hashlib.sha256(terms).hexdigest(),
        text_size_bytes=len(terms),
        text_kind="excerpt",
        text_lines={
            "file": "source-blob.c",
            "lines": [1, 3],
            "git_blob_sha1": hashlib.sha1(b"blob 54\0" + blob).hexdigest(),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "size_bytes": len(blob),
        },
    )
    # Git's header includes the decimal byte length (54 for this literal blob).
    assert len(blob) == 54
    document["embedded_hosts"][0]["components"][-1]["source"].update(
        text_kind="excerpt",
        text_lines=copy.deepcopy(row["text_lines"]),
        **{key: row[key] for key in ("text_file", "text_sha256", "text_size_bytes")},
    )
    save_embedded_fixture(release, document)
    return document, host, terms


def test_git_excerpt_preserves_exact_line_bytes_and_blob_provenance(release):
    """The artifact renders only the exact header, with its source-blob identity."""
    _document, _host, terms = git_excerpt_fixture(release)
    output = load_notices().render_notices(plan(load_notices(), release))
    assert output.count(terms) == 1
    assert b"int implementation;" not in output
    assert b"lines 1-3" in output
    assert b"Git blob SHA-1" in output


@pytest.mark.parametrize("damage", ["range", "blob", "text", "missing", "source-bytes"])
def test_git_excerpt_refuses_wrong_range_blob_or_excerpt(release, damage):
    """A self-consistent excerpt hash cannot replace equality with the source range."""
    document, host, _terms = git_excerpt_fixture(release)
    surface = release["native_surface"]
    row = document["components"][-1]
    if damage == "range":
        row["text_lines"]["lines"] = [2, 4]
    elif damage == "blob":
        row["text_lines"]["git_blob_sha1"] = "f" * 40
    elif damage == "text":
        terms = b"Self-consistent but invented licence terms.\n"
        (surface / row["text_file"]).write_bytes(terms)
        row.update(text_sha256=hashlib.sha256(terms).hexdigest(), text_size_bytes=len(terms))
    elif damage == "missing":
        (surface / "source-blob.c").unlink()
    else:
        (surface / "source-blob.c").write_bytes(b"changed source")
    document["embedded_hosts"][0]["components"][-1]["source"].update(
        text_lines=copy.deepcopy(row["text_lines"])
    )
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match=r"embedded.*" + host.name + r".*Embedded beta.*"):
        plan(load_notices(), release)


@pytest.mark.parametrize(
    "field,value",
    [
        ("lines", [0, 3]),
        ("lines", [True, 3]),
        ("lines", [3, 2]),
        ("lines", [1, 999]),
        ("file", "../outside.c"),
        ("git_blob_sha1", "bad"),
        ("sha256", "bad"),
        ("size_bytes", True),
    ],
)
def test_git_excerpt_schema_and_bounds_fail_closed(release, field, value):
    """Unsafe source paths and malformed or out-of-bounds ranges are refused."""
    document, _host, _terms = git_excerpt_fixture(release)
    row = document["components"][-1]
    row["text_lines"][field] = value
    document["embedded_hosts"][0]["components"][-1]["source"]["text_lines"] = copy.deepcopy(
        row["text_lines"]
    )
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError):
        plan(load_notices(), release)


def test_git_excerpt_revalidates_source_on_render(release):
    """A source changed after planning cannot authorize the previously valid excerpt."""
    _document, _host, _terms = git_excerpt_fixture(release)
    module = load_notices()
    planned = plan(module, release)
    (release["native_surface"] / "source-blob.c").write_bytes(b"changed after planning")
    with pytest.raises(ValueError, match=r"embedded.*Embedded beta"):
        module.render_notices(planned)


def attribution_fixture(release):
    """Carry the copyright attribution separately from generic licence terms."""
    document, _host, _text = embedded_host_fixture(release)
    data = b'{"Copyright": "Copyright 2026 Synthetic Author"}\n'
    (release["native_surface"] / "attribution.json").write_bytes(data)
    attribution = {
        "file": "attribution.json",
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "git_blob_sha1": hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest(),
        "source_path": "src/qt_attribution.json",
    }
    document["components"][-1]["attribution"] = attribution
    document["embedded_hosts"][0]["components"][-1]["source"]["attribution"] = copy.deepcopy(
        attribution
    )
    save_embedded_fixture(release, document)
    return document, data


def test_embedded_attribution_preserves_copyright_and_pinned_source(release):
    """Generic terms must retain the component's separately published copyright."""
    _document, data = attribution_fixture(release)
    module = load_notices()
    output = module.render_notices(plan(module, release))
    assert output.count(data) == 1
    assert b"src/qt_attribution.json" in output


@pytest.mark.parametrize("damage", ["bytes", "missing", "blob", "path"])
def test_embedded_attribution_fails_closed(release, damage):
    """A missing, changed or misidentified attribution cannot disappear silently."""
    document, _data = attribution_fixture(release)
    path = release["native_surface"] / "attribution.json"
    if damage == "bytes":
        path.write_bytes(b"invented attribution")
    elif damage == "missing":
        path.unlink()
    else:
        field = "git_blob_sha1" if damage == "blob" else "source_path"
        document["components"][-1]["attribution"][field] = (
            "e" * 40 if damage == "blob" else "../unsafe"
        )
        document["embedded_hosts"][0]["components"][-1]["source"]["attribution"] = copy.deepcopy(
            document["components"][-1]["attribution"]
        )
        save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match=r"embedded.*Embedded beta"):
        plan(load_notices(), release)


@pytest.mark.parametrize("parent", ["python", "numpy"])
def test_embedded_missing_component_cannot_fall_back_to_parent(release, parent):
    """Removing a row must fail even with a valid interpreter or wheel owner."""
    document, host, _text = embedded_host_fixture(release, parent=parent)
    document["components"].pop()
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match=r"embedded.*" + re.escape(host.name) + r".*Embedded beta"):
        plan(load_notices(), release)


@pytest.mark.parametrize("damage", ["hash", "size"])
def test_embedded_changed_host_requires_recensus(release, damage):
    """Measure carried bytes before fallback and name expected and actual identities."""
    document, host, _text = embedded_host_fixture(release)
    declared = document["embedded_hosts"][0]
    body = host.read_bytes()
    host.write_bytes(bytes([body[0] ^ 1]) + body[1:] if damage == "hash" else body + b"x")
    with pytest.raises(ValueError) as error:
        plan(load_notices(), release)
    for fragment in (
        host.name,
        declared["sha256"],
        str(declared["size_bytes"]),
        hashlib.sha256(host.read_bytes()).hexdigest(),
        str(host.stat().st_size),
        "expected",
        "actual",
        "re-census required",
    ):
        assert fragment in str(error.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_commit", "c" * 40),
        ("source_tag", "v2.0"),
        ("source_path", "Doc/wrong.rst"),
        ("source_tag_object", "d" * 40),
    ],
)
def test_embedded_wrong_source_pin_fails_by_host_and_component(release, field, value):
    """A valid replacement source pin cannot reuse the declared host bytes."""
    document, host, _text = embedded_host_fixture(release)
    document["components"][-1][field] = value
    save_embedded_fixture(release, document)
    with pytest.raises(
        ValueError, match=r"embedded.*" + re.escape(host.name) + r".*Embedded beta.*source pin"
    ):
        plan(load_notices(), release)


@pytest.mark.parametrize("damage", ["hash", "size", "missing"])
def test_embedded_tampered_text_names_host_and_component(release, damage):
    """Every embedded text's integrity remains mandatory, with actionable context."""
    _document, host, text = embedded_host_fixture(release)
    path = release["native_surface"] / "embedded-terms.txt"
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"X" + text[1:] if damage == "hash" else text + b"x")
    with pytest.raises(
        ValueError, match=r"embedded.*" + re.escape(host.name) + r".*Embedded alpha.*text"
    ):
        plan(load_notices(), release)


def test_embedded_absent_host_emits_no_component_claim_or_text(release):
    """An absent parent and host create no redistribution claim from declarations."""
    _document, _host, text = embedded_host_fixture(release, parent="numpy", carried=False)
    omit_parent(release, "numpy")
    module = load_notices()
    result = plan(module, release)
    assert not any(row.name.startswith("Embedded ") for row in result.rows)
    assert text not in module.render_notices(result)
    module.validate_coverage(result.entries, result.rows)


@pytest.mark.parametrize("parent", ["python", "numpy", "pyside6-essentials"])
def test_embedded_complete_host_keeps_parent_and_distinct_text_blocks(release, parent):
    """Parent terms and every component cover the host; identical terms render once."""
    _document, host, text = embedded_host_fixture(release, parent=parent)
    module = load_notices()
    result = plan(module, release)
    rows = {row.name: row for row in result.rows}
    label = "file:" + host.relative_to(release["folder"]).as_posix()
    parent_row = rows["Python" if parent == "python" else parent]
    for name in ("Embedded alpha", "Embedded gamma", "Embedded beta"):
        assert rows[name].entries == (label,)
        assert rows[name].sources == (
            "https://example.org/synthetic-source/tree/" + "a" * 40 + "/Doc/synthetic-licence.rst",
        )
        assert label in parent_row.entries
        assert any(name in note and host.name in note for note in parent_row.notes)
    rendered = module.render_notices(result)
    assert rendered.count(text) == 1
    assert rendered.count(b"Synthetic distinct gamma terms.\n") == 1
    assert parent_row.licence_inputs[0].path.read_bytes() in rendered
    assert b"source pin" in rendered
    module.validate_coverage(result.entries, result.rows)


@pytest.mark.parametrize(
    "damage",
    [
        "wildcard",
        "duplicate",
        "bad-hash",
        "bad-size",
        "bad-parent",
        "unknown-key",
        "bad-source",
        "duplicate-component",
        "unbound-row",
    ],
)
def test_embedded_schema_refuses_ambiguous_or_unsafe_declarations(release, damage):
    """No wildcard, duplicate host, malformed pin or unattached row is accepted."""
    document, _host, _text = embedded_host_fixture(release)
    declared = document["embedded_hosts"][0]
    if damage == "wildcard":
        declared["relpath"] = "_internal/*.dll"
    elif damage == "duplicate":
        document["embedded_hosts"].append(copy.deepcopy(declared))
    elif damage == "bad-hash":
        declared["sha256"] = "bad"
    elif damage == "bad-size":
        declared["size_bytes"] = True
    elif damage == "bad-parent":
        declared["parent"] = "Python"
    elif damage == "unknown-key":
        declared["accept_new_build"] = True
    elif damage == "bad-source":
        declared["components"][0]["source"]["source_commit"] = "branch"
    elif damage == "duplicate-component":
        declared["components"].append(copy.deepcopy(declared["components"][0]))
    else:
        document["components"][-1]["embedded_in"] = ["_internal/undeclared.dll"]
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match="embedded"):
        plan(load_notices(), release)


@pytest.mark.parametrize("binding", [None, [], "_internal/python312.dll"])
def test_embedded_removed_or_malformed_binding_cannot_use_parent(release, binding):
    """A declared source row must explicitly bind the measured host with a list."""
    document, host, _text = embedded_host_fixture(release)
    document["components"][-1]["embedded_in"] = binding
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match="embedded.*" + re.escape(host.name) + ".*Embedded beta"):
        plan(load_notices(), release)


def test_embedded_missing_unique_component_is_named_before_orphan_text(release):
    """A removed row cannot hide behind generic unused-text or parent coverage errors."""
    document, host, _text = embedded_host_fixture(release)
    document["components"] = [
        row for row in document["components"] if row["component"] != "Embedded gamma"
    ]
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match="embedded.*" + re.escape(host.name) + ".*Embedded gamma"):
        plan(load_notices(), release)


@pytest.mark.parametrize("carried", [False, True])
def test_embedded_component_may_bind_several_independently_measured_hosts(release, carried):
    """A component can span Python and a wheel while each host retains its parent."""
    document, _host, _text = embedded_host_fixture(release)
    relative = "_internal/numpy/_core/test.pyd"
    host = release["folder"] / relative
    second = copy.deepcopy(document["embedded_hosts"][0])
    second.update(
        relpath=relative,
        parent="numpy",
        parent_version="2.5.4",
        sha256=hashlib.sha256(host.read_bytes()).hexdigest(),
        size_bytes=host.stat().st_size,
    )
    document["embedded_hosts"].append(second)
    for row in document["components"][1:]:
        row["embedded_in"].append(relative)
    if not carried:
        host.unlink()
        omit_parent(release, "numpy")
    save_embedded_fixture(release, document)
    module = load_notices()
    result = plan(module, release)
    rows = {row.name: row for row in result.rows}
    for name in ("Embedded alpha", "Embedded beta", "Embedded gamma"):
        assert ("file:" + relative in rows[name].entries) == carried
        assert "file:_internal/python312.dll" in rows[name].entries
    assert ("numpy" in rows) == carried
    module.validate_coverage(result.entries, result.rows)


def test_embedded_parent_declaration_must_match_actual_owner(release):
    """The source census cannot invent a parent attribution to another package."""
    document, host, _text = embedded_host_fixture(release)
    document["embedded_hosts"][0]["parent"] = "numpy"
    document["embedded_hosts"][0]["parent_version"] = "2.5.4"
    save_embedded_fixture(release, document)
    with pytest.raises(
        ValueError, match="embedded.*" + re.escape(host.name) + ".*parent attribution"
    ):
        plan(load_notices(), release)


def test_embedded_shared_text_is_rechecked_for_each_component_at_render(release):
    """Deduplication cannot skip a second path's text verification after planning."""
    document, host, text = embedded_host_fixture(release)
    duplicate = release["native_surface"] / "beta-terms.txt"
    duplicate.write_bytes(text)
    document["components"][-1]["text_file"] = duplicate.name
    document["embedded_hosts"][0]["components"][-1]["source"]["text_file"] = duplicate.name
    save_embedded_fixture(release, document)
    module = load_notices()
    result = plan(module, release)
    assert module.render_notices(result).count(text) == 1
    duplicate.write_bytes(b"X" + text[1:])
    with pytest.raises(
        ValueError, match="embedded.*" + re.escape(host.name) + ".*Embedded beta.*text"
    ):
        module.render_notices(result)


def carried_notice_fixture(release):
    """Bind a second host claim to numpy's already rendered, measured terms."""
    module = load_notices()
    original = plan(module, release)
    parent = next(row for row in original.rows if row.name == "numpy")
    assert len(parent.licence_inputs) == 1
    terms = parent.licence_inputs[0].path.read_bytes()
    relative = "_internal/numpy/_core/test.pyd"
    body = (release["folder"] / relative).read_bytes()
    reference = {
        "row": "numpy",
        "inputs": [{"sha256": hashlib.sha256(terms).hexdigest(), "size_bytes": len(terms)}],
    }
    document = json.loads((release["native_surface"] / "manifest.json").read_text())
    document["embedded_hosts"] = [
        {
            "relpath": relative,
            "sha256": hashlib.sha256(body).hexdigest(),
            "size_bytes": len(body),
            "parent": "numpy",
            "parent_version": "2.5.4",
            "components": [
                {"component": "Carried runtime", "source": {"carried_notice": reference}}
            ],
        }
    ]
    document["components"].append(
        {
            "component": "Carried runtime",
            "upstream_version": "fixture runtime",
            "spdx": "MIT",
            "version_evidence": {"method": "embedded_string", "value": "fixture"},
            "embedded_in": [relative],
            "carried_notice": reference,
        }
    )
    save_embedded_fixture(release, document)
    return module, document, terms


def test_embedded_carried_notice_reuses_existing_text_without_copy(release):
    """An embedded runtime must reuse its audited input and retain its host attribution."""
    module, _document, terms = carried_notice_fixture(release)
    result = plan(module, release)
    runtime = next(row for row in result.rows if row.name == "Carried runtime")
    assert runtime.entries == ("file:_internal/numpy/_core/test.pyd",)
    output = module.render_notices(result)
    assert output.count(terms) == 1
    assert b"Carried runtime" in output and b"Reused carried notice: numpy" in output
    assert (
        b"### Installed wheel: numpy 2.5.4; numpy-2.5.4.dist-info/licenses/LICENSE.txt\n" in output
    )
    assert b"### Reused carried notice:" not in output


@pytest.mark.parametrize("damage", ["hash", "size", "missing-row", "extra-field", "source-pin"])
def test_embedded_carried_notice_refuses_unverified_reference(release, damage):
    """Wrong or ambiguous references cannot silently fall back to the host's owner."""
    module, document, _terms = carried_notice_fixture(release)
    row = document["components"][-1]
    if damage == "hash":
        row["carried_notice"]["inputs"][0]["sha256"] = "f" * 64
    elif damage == "size":
        row["carried_notice"]["inputs"][0]["size_bytes"] += 1
    elif damage == "missing-row":
        row["carried_notice"]["row"] = "Absent source"
    elif damage == "extra-field":
        row["carried_notice"]["extra"] = "bad"
    else:
        row["source_commit"] = "a" * 40
    # Mutate both independent declarations so the reference resolver is exercised.
    document["embedded_hosts"][0]["components"][0]["source"] = {
        "carried_notice": copy.deepcopy(row["carried_notice"])
    }
    save_embedded_fixture(release, document)
    with pytest.raises(ValueError, match=r"carried notice|source pin differs"):
        plan(module, release)


def test_embedded_carried_notice_rechecks_terms_at_render(release):
    """Changing a reused source input after planning must refuse rendering."""
    module, _document, _terms = carried_notice_fixture(release)
    result = plan(module, release)
    runtime = next(row for row in result.rows if row.name == "Carried runtime")
    with runtime.licence_inputs[0].path.open("ab") as stream:
        stream.write(b"x")
    with pytest.raises(ValueError, match=r"Carried runtime|carried notice"):
        module.render_notices(result)


def test_production_wheel_census_binds_every_scipy_native_runtime():
    """All audited SciPy natives must require the appropriate carried runtime texts."""
    module = load_notices()
    document = json.loads((ROOT / "tools/package/native-licences/manifest.json").read_text())
    hosts = {host.relpath: host for host in module._embedded_declarations(document)}
    scipy = {path: host for path, host in hosts.items() if host.parent == "scipy"}
    assert len(scipy) == 83
    extensions = {path: host for path, host in scipy.items() if path.endswith(".pyd")}
    assert len(extensions) == 82
    for host in extensions.values():
        names = {name for name, _pin in host.components}
        assert {
            "GCC runtime (SciPy static)",
            "MinGW-w64 CRT and winpthreads (static wheels)",
        } <= names
    assert any(path.endswith("/_slsqplib.cp312-win_amd64.pyd") for path in extensions)


@pytest.mark.parametrize(
    "component,expected",
    [
        ("libaom (Pillow)", ("_internal/PIL/_avif.cp312-win_amd64.pyd",)),
        ("json11 (x265)", ("_internal/libx265-217-276e7d75772a32bd086b54d54e01fd11.dll",)),
        ("fast_float (libstdc++)", ("_internal/libstdc++-6-e4d43a335d57132a6ec3004cece76b4f.dll",)),
        (
            "SuperLU (SciPy)",
            ("_internal/scipy/sparse/linalg/_dsolve/_superlu.cp312-win_amd64.pyd",),
        ),
    ],
)
def test_production_wheel_texts_bind_exact_censused_hosts(component, expected):
    """The verified library terms cannot be detached from their actual carried host."""
    module = load_notices()
    records = {
        row.component: row
        for row in module.load_native_licences(ROOT / "tools/package/native-licences")
    }
    assert records[component].embedded_in == expected
    if component == "libaom (Pillow)":
        assert (
            records[component].licence_input.sha256
            == "60f3f7e003a4a7736aad7c008380fbfbcd3bf19544c589efebba824a2b9e145b"
        )


@pytest.mark.parametrize("rehash", [False, True])
def test_carried_audit_text_refusal_names_embedded_host_and_component(tmp_path, rehash):
    """Even internally valid replacement audit blocks must match the embedded text pin."""
    module = load_notices()
    data = b"Original runtime exception terms.\n"
    digest = hashlib.sha256(data).hexdigest()
    audit = tmp_path / "audit.md"
    altered = b"Replaced runtime exception terms.\n"
    recorded = hashlib.sha256(altered).hexdigest() if rehash else digest
    audit.write_text(
        '<a id="text-1"></a>\n'
        f"Source: `https://example.org/terms`. SHA-256: `{recorded}`. "
        f"UTF-8/LF bytes: {len(altered)}.\n"
        "````text\n" + altered.decode() + "````\n",
        encoding="utf-8",
    )
    item = module.LicenceInput(
        audit,
        "text-1",
        digest,
        len(data),
        context="embedded _internal/test.pyd component Runtime carried notice: ",
    )
    row = module.NoticeRow(
        "Runtime",
        "1",
        "MIT",
        ("https://example.org/source",),
        ("file:_internal/test.pyd",),
        (item,),
    )
    result = module.NoticePlan(row.entries, (row,), ())
    with pytest.raises(ValueError, match=r"test.pyd.*Runtime"):
        module.render_notices(result)


def test_carried_notice_absent_host_adds_no_claim(release):
    """A declared but absent host cannot redistribute a runtime reference."""
    module, _document, _terms = carried_notice_fixture(release)
    (release["folder"] / "_internal/numpy/_core/test.pyd").unlink()
    omit_parent(release, "numpy")
    assert not any(row.name == "Carried runtime" for row in plan(module, release).rows)


def test_production_tnc_retains_original_tnbc_attribution():
    """The TNC terms must not discard the original Stephen G. Nash TNBC credit."""
    records = load_notices().load_native_licences(ROOT / "tools/package/native-licences")
    row = next((row for row in records if row.component == "TNBC original credit (TNC)"), None)
    assert row is not None
    assert b"STEPHEN G. NASH" in row.licence_input.path.read_bytes()
    assert row.embedded_in == ("_internal/scipy/optimize/_moduleTNC.cp312-win_amd64.pyd",)


@pytest.mark.parametrize(
    "component,stems,spdx,text_sha256",
    [
        (
            "L-BFGS-B original licence",
            ["scipy/optimize/_lbfgsb"],
            "BSD-3-Clause",
            "919e78c1c48cc7d179efe63075590cfb5942e6ae1da2bf373dd754fe795139b5",
        ),
        (
            "L-BFGS-B authors and citation",
            ["scipy/optimize/_lbfgsb"],
            "BSD-3-Clause",
            "283efcb76166e067a3d17d1156f548456318cb7850f67409fa7d96f59a5dfe1d",
        ),
        (
            "MINPACK original notice",
            ["scipy/optimize/_minpack"],
            "Minpack",
            "f5b330efdad110cdd84d585ec61220b0650461fa599e36b13e1726c9346dcfb9",
        ),
        (
            "SLSQP ACM release statement",
            ["scipy/optimize/_slsqplib"],
            "LicenseRef-SLSQP-ACM-BSD",
            "f1d9aa03a6a8d5bafc0b6bd20b64a86ec622fe9b3cde2052fbf5ccdbda69e843",
        ),
        (
            "SLSQP Dieter Kraft copyright",
            ["scipy/optimize/_slsqplib"],
            "LicenseRef-SLSQP-ACM-BSD",
            "98de00e1b3ce1545541a39e2b2e57d7edd0101e52b7ddfa6346943cff227b2d2",
        ),
        (
            "ID 0.4 original notice",
            ["scipy/linalg/_decomp_interpolative"],
            "BSD-3-Clause",
            "d49f6f31635740cc9f3737dfa99833789dd9eb6c25d3e0bcb4f7234ea541d6e3",
        ),
        (
            "DCDFLIB original legalities",
            ["scipy/special/_ufuncs", "scipy/special/cython_special"],
            "LicenseRef-DCDFLIB-Legalities",
            "d1afd8036f0b6c60b7fa8f912b91298e7e47cc350146ad30d1bad23577c8568c",
        ),
        (
            "AOM patent licence",
            ["PIL/_avif"],
            "LicenseRef-AOM-Patent-License-1.0",
            "661fb8e504744e95587b556b94a58343448300606a41bea8c7a9b97125696e61",
        ),
        (
            "libyuv patent grant",
            ["PIL/_avif"],
            "LicenseRef-libyuv-Patents",
            "4da84211f947c6f9f7dd8fbce513e1522e01833407ae732b8c9a2bbb75fed495",
        ),
        (
            "fastfeat (libaom)",
            ["PIL/_avif"],
            "BSD-3-Clause",
            "499041ddee5227b6f29ca06c17803e5fe24d60f243c69635cd76b7ba08d0ddd5",
        ),
        (
            "vector (libaom)",
            ["PIL/_avif"],
            "MIT",
            "ff6c857ce2708e87701323078aef115c1872a1f80a9649f86dc899b48083bc60",
        ),
        (
            "x86inc (libaom)",
            ["PIL/_avif"],
            "ISC",
            "719d8fa235f2068e0ae6d6a7dceb0a7720d7840f0f0ebed29957989e6ded3cd8",
        ),
    ],
)
def test_originals_and_patents_bind_verified_texts_to_carried_hosts(
    component, stems, spdx, text_sha256
):
    """Omitting an original obligation or attaching it to a different host must fail."""
    module = load_notices()
    folder = ROOT / "tools/package/native-licences"
    records = {row.component: row for row in module.load_native_licences(folder)}
    assert component in records
    row = records[component]
    expected = {f"_internal/{stem}.cp312-win_amd64.pyd" for stem in stems}
    assert set(row.embedded_in) == expected
    assert row.spdx == spdx
    assert hashlib.sha256(row.licence_input.path.read_bytes()).hexdigest() == text_sha256
    document = json.loads((folder / "manifest.json").read_text())
    hosts = {host.relpath: host for host in module._embedded_declarations(document)}
    for path in expected:
        assert component in {name for name, _source in hosts[path].components}


def test_original_obligations_render_verbatim_with_canonical_sources_and_citation(release):
    """A real plan must preserve CRLF, patent bytes and the required SLSQP citation."""
    module = load_notices()
    production = json.loads((ROOT / "tools/package/native-licences/manifest.json").read_text())
    names = {
        "L-BFGS-B original licence",
        "L-BFGS-B authors and citation",
        "MINPACK original notice",
        "SLSQP ACM release statement",
        "SLSQP Dieter Kraft copyright",
        "ID 0.4 original notice",
        "DCDFLIB original legalities",
        "AOM patent licence",
        "libyuv patent grant",
        "fastfeat (libaom)",
        "vector (libaom)",
        "x86inc (libaom)",
    }
    selected = [copy.deepcopy(row) for row in production["components"] if row["component"] in names]
    assert {row["component"] for row in selected} == names
    # Use the real texts and provenance with a disposable synthetic host; the
    # separate production test pins the actual census paths and declarations.
    relative = "_internal/numpy/_core/test.pyd"
    data = (release["folder"] / relative).read_bytes()
    surface = release["native_surface"]
    document = json.loads((surface / "manifest.json").read_text())
    for row in selected:
        filenames = [row["text_file"]]
        if "text_lines" in row:
            filenames.append(row["text_lines"]["file"])
        for filename in filenames:
            shutil.copyfile(ROOT / "tools/package/native-licences" / filename, surface / filename)
        row["embedded_in"] = [relative]
    document["components"].extend(selected)
    document["embedded_hosts"] = [
        {
            "relpath": relative,
            "parent": "numpy",
            "parent_version": "2.5.4",
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
            "components": [
                {
                    "component": row["component"],
                    "source": {
                        key: value for key, value in row.items() if key in module._PROVENANCE_FIELDS
                    },
                }
                for row in selected
            ],
        }
    ]
    save_embedded_fixture(release, document)
    output = module.render_notices(plan(module, release))
    for row in selected:
        terms = (surface / row["text_file"]).read_bytes()
        assert output.count(terms) == 1
    minpack = next(row for row in selected if row["component"] == "MINPACK original notice")
    terms = (surface / minpack["text_file"]).read_bytes()
    assert len(terms) == 2246 and terms.count(b"\r\n") == 52
    assert b"This product includes software developed by the\r\n   University of Chicago" in output
    assert (
        output.count(
            b"D. Kraft, Algorithm 733: TOMP - Fortran modules for optimal control calculations, "
            b"ACM Transactions on Mathematical Software 20(3), 1994, pp. 262-281, "
            b"DOI 10.1145/192115.192124, https://www.netlib.org/toms/733."
        )
        == 1
    )
    for url, digest in [
        (
            b"https://users.iems.northwestern.edu/~nocedal/Software/Lbfgsb.3.0.tar.gz",
            b"f5b9a1c8c30ff6bcc8df9b5d5738145f4cbe4c7eadec629220e808dcf0e54720",
        ),
        (
            b"https://www.netlib.org/minpack/disclaimer",
            b"f5b330efdad110cdd84d585ec61220b0650461fa599e36b13e1726c9346dcfb9",
        ),
        (
            b"https://netlib.org/random/dcdflib.f.tar.gz",
            b"93938e358d67eb4c4de78baaacea085c683fd183672a1092507229e513fe95aa",
        ),
    ]:
        assert url in output and digest in output
