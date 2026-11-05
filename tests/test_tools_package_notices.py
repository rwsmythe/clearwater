"""Inventory coverage tests for artifact notices, using synthetic onedir releases."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import marshal
import re
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
    path = ROOT / ".venv/Lib/site-packages" / relative
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
    monkeypatch.setattr(
        module.importlib.metadata, "distribution", release["distributions"].__getitem__
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


def test_openssl_dlls_cannot_be_mislicensed_as_python_psf_terms(release):
    """The source-install Python audit has no redistributed OpenSSL licence text."""
    module = load_notices()
    (release["folder"] / "_internal/libcrypto-3-x64.dll").write_bytes(b"synthetic OpenSSL")
    with pytest.raises(ValueError, match=r"OpenSSL.*licence.*source"):
        plan(module, release)


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
        expected.update({"FFmpeg / ffprobe", "FFmpeg component: x265"})
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
