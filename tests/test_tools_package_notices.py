"""Inventory coverage tests for artifact notices, using synthetic onedir releases."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import marshal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


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
    folder = tmp_path / "release"
    internal = folder / "_internal"
    (internal / "numpy/_core").mkdir(parents=True)
    (internal / "numpy/_core/test.pyd").write_bytes(b"synthetic native extension")
    (internal / "python312.dll").write_bytes(b"synthetic interpreter")
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
    ffmpeg["configure_line"] = "configuration: --enable-gpl --enable-version3 --enable-libx265"
    ffmpeg["components"] = [next(c for c in ffmpeg["components"] if c["name"] == "x265")]
    ffmpeg["excluded"] = []
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
    }


def plan(module, release):
    return module.plan_notices(
        release["folder"],
        audit_path=release["audit"],
        uv_lock_path=release["uv_lock"],
        ffmpeg_lock_path=release["ffmpeg_path"],
        distribution=release["distributions"].__getitem__,
    )


def add_ffmpeg(release):
    folder, pin = release["folder"], release["ffmpeg"]
    for name in ["ffmpeg.exe", "ffprobe.exe"]:
        (folder / name).write_bytes(b"synthetic tool; never executed")
    (folder / "ffmpeg-LICENSE.txt").write_text("synthetic GPL-3.0 licence")
    (folder / "ffmpeg-BUILD.txt").write_text(
        "\n".join(
            [
                f"Provider: {pin['provider']}",
                f"Release tag: {pin['release_tag']}",
                f"Asset: {pin['asset_name']}",
                f"SHA256: {pin['github_sha256']}",
                f"FFmpeg version: {pin['version']}",
                f"FFmpeg commit: {pin['ffmpeg_commit']}",
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
            "licence": "GPL-2.0-only",
            "licence_basis": "seat-verified",
            "licence_note": "synthetic conflict",
            "gpl3_compatible": "no",
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


@pytest.mark.parametrize("missing", ["ffprobe.exe", "ffmpeg-BUILD.txt", "ffmpeg-LICENSE.txt"])
def test_partial_ffmpeg_distribution_fails_closed(release, missing):
    notices = load_notices()
    add_ffmpeg(release)
    (release["folder"] / missing).unlink()
    with pytest.raises(ValueError, match=r"FFmpeg.*missing"):
        plan(notices, release)
