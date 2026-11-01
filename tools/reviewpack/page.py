"""Name-only CP5 HTML and ICC-managed sRGB viewing derivatives."""

from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Mapping, Sequence
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit

if __package__ in {None, "", "tools.reviewpack"}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "reviewpack"

from PIL import Image, ImageCms

from lookcheck.frames import OutputPathError, OutputRoots

from .select import GROUPS, pending_items
from .sheet import CONFLICT_RECOVERY

PRESET_SENTENCE = (
    "In v1 both starter presets carry AD-8's defaults, so the corrected items on this page "
    "are what both presets produce; at CP5 the owner may change either preset's values (AD-13)."
)


def pending_presets(
    presets: Mapping[str, Mapping[str, Any]], *, roots: OutputRoots
) -> tuple[str, ...]:
    """Find starter presets without both saved values and a product-exported file.

    Args:
        presets: Preset objects in the state of record.
        roots: Pack and source roots.

    Returns:
        Missing AD-13 names, without changing preset files or pack state.
    """
    return tuple(
        name
        for name in ("Snorkel (shallow)", "Scuba (deep)")
        if name not in presets
        or not roots.check(roots.allowed / "presets" / f"{name}.json").is_file()
    )


def _link(folder: str, name: str, label: str) -> str:
    if not name or Path(name).name != name or any(c in name for c in ("/", "\\", ":")):
        raise ValueError("artifact must have a bare file name")
    target = quote(f"{folder}/{name}" if folder else name, safe="/")
    return f'<a href="{target}">{escape(label)}</a>'


def _rgb(source: Path, short_side: int) -> tuple[Image.Image, bytes | None]:
    with Image.open(source) as original:
        image = original.convert("RGB")
        profile = original.info.get("icc_profile")
        icc = None
        if profile:
            target = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
            converted = ImageCms.profileToProfile(
                image, ImageCms.ImageCmsProfile(io.BytesIO(profile)), target, outputMode="RGB"
            )
            if converted is None:
                raise ValueError("ICC conversion returned no image")
            image = converted
            icc = target.tobytes()
        scale = short_side / min(image.size)
        image = image.resize((round(image.width * scale), round(image.height * scale)))
        image.info.clear()
        return image, icc


def _save(image: Image.Image, destination: Path, icc: bytes | None, roots: OutputRoots) -> Path:
    target = roots.check(destination)
    roots.mkdir(target.parent)
    image.save(target, format="JPEG", quality=90, icc_profile=icc)
    return destination


def write_page(
    items: Sequence[Mapping[str, Any]],
    presets: Mapping[str, Mapping[str, Any]],
    *,
    roots: OutputRoots,
    sheet_message: str = "",
) -> Path:
    """Write the grouped CP5 page and display README with pack-relative links.

    Args:
        items: Persisted item results.
        presets: Product-exported preset objects.
        roots: Pack and source roots.
        sheet_message: Safe explanation if the existing owner sheet was retained.

    Returns:
        The written index path.
    """
    # Schema introspection supplies effective defaults; it never corrects media.
    from clearwater.app.composition import correction_methods

    methods = correction_methods()
    pending = pending_items(items)
    missing_presets = pending_presets(presets, roots=roots)
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8">',
        "<title>CP5 visual review pack</title>",
        "<style>body{font:18px sans-serif;margin:2em;max-width:1500px}"
        "figure{display:inline-block;width:45%;margin:1%}figure img{max-width:100%;height:auto}"
        "video{max-width:100%}"
        "article{border-top:1px solid #aaa;padding:1em 0}td,th{padding:.3em}</style>",
        "<h1>CP5 visual review pack</h1>",
        f"<p>Pending: {len(pending)}; "
        + ", ".join(
            f"{group}={sum(item.group == group for item in pending)}"
            for group in GROUPS
            if any(item.group == group for item in pending)
        )
        + (". Pack is not ready for CP5.</p>" if pending else ".</p>"),
        "<p>Only the owner judges these items. D65 asks whether the corrected result is "
        "preferred on at least 80 % of the headline set. Record halos, banding, color errors, "
        "shimmer and flicker, and flag above-surface items in the sheet. "
        "P-Z and V-Z are pre-corrected candidates with separate tallies.</p>",
        "<p>Source is on the left; corrected is on the right. Photo source views use the "
        "product's neutral export with the same orientation, ICC handling and bit depth. "
        "Each pair clip is a viewing aid; the linked product output is the item of record.</p>",
        "<p>Sheet entries use exact lowercase values with no surrounding spaces: "
        "blank means unjudged; yes, no and undecided count as judged; "
        "only yes counts as preferred. A viewing_aid_failed flag is shown when a viewing aid "
        "could not be built. Those rows keep the linked product output and count normally "
        "when judged.</p>",
        "<p>Pair viewing aid encoding: NVENC HEVC, p5/hq, VBR CQ 20 with no bitrate target. "
        "CPU fixture controls use libx265 ultrafast. Product exports keep shipped defaults.</p>",
        "<p>Limit: run commands from the worktree root; invocation from another working "
        "directory is outside this instrument's supported scope.</p>",
    ]
    if missing_presets:
        parts.append(
            "<p>Pending presets: "
            + escape(", ".join(missing_presets))
            + ". Pack is not ready for CP5.</p>"
        )
    if (roots.allowed / "review-sheet.csv").is_file():
        parts.append(_link("", "review-sheet.csv", "Owner review sheet (CSV)"))
    if sheet_message:
        parts.append(f"<p>Sheet: {escape(sheet_message)}</p>")
    parts.append("<h2>Starter presets</h2>")
    if not missing_presets:
        parts.append(f"<p>{PRESET_SENTENCE}</p>")
    for name, preset in presets.items():
        if name in missing_presets:
            continue
        parts.append(f"<h3>{escape(name)}</h3>" + _link("presets", name + ".json", name + ".json"))
        method_id = str(preset["method"])
        schema = methods[method_id].parameters
        values = {p.name: p.default for p in schema}
        values.update(preset["parameters"])
        parts.append(f"<p>Method {escape(method_id)}; effective method defaults</p><table>")
        for key, value in values.items():
            parts.append(f"<tr><th>{escape(key)}</th><td>{escape(str(value))}</td></tr>")
        parts.append("</table>")
    for group in GROUPS:
        parts.append(f"<h2>{group}</h2>")
        for item in items:
            if item["group"] != group:
                continue
            parts.append(f"<article><h3>{escape(str(item['source_name']))}</h3>")
            parts.append(
                f"<p>{escape(str(item['status']))}: {escape(str(item.get('message', '')))}</p>"
            )
            for warning in item.get("warnings", []):
                parts.append(f"<p>Warning: {escape(str(warning))}</p>")
            if item["status"] == "done":
                folder = "photos" if item["kind"] == "photo" else "clips"
                parts.append(
                    _link(folder, item["corrected_name"], "Product: " + item["corrected_name"])
                )
                if item["kind"] == "photo" and item.get("source_view_name"):
                    parts.append(_link("photos", item["source_view_name"], "Source (neutral)"))
                for key, label in (("source_thumb", "Source"), ("corrected_thumb", "Corrected")):
                    if item.get(key):
                        name = str(item[key])
                        _link("thumbs", name, label)  # Validate the name before constructing src.
                        parts.append(
                            f'<figure><img src="{quote("thumbs/" + name)}" alt="{label}">'
                            f"<figcaption>{label}</figcaption></figure>"
                        )
                if item.get("pair_name"):
                    parts.append(_link("pairs", item["pair_name"], "Pair clip (viewing aid)"))
                for still in item.get("stills", []):
                    parts.append(
                        _link("pairs", still["name"], f"Pair still {100 * still['fraction']:g} %")
                    )
            if item.get("aid_message"):
                parts.append(f"<p>Viewing aid: {escape(item['aid_message'])}</p>")
            if item.get("refusal_message"):
                parts.append(f"<p>{escape(item['refusal_message'])}</p>")
            parts.append("</article>")
    not_built = [
        item
        for item in items
        if item["status"] in {"excerpt_failed", "failed", "pending", "not run", "cancelled"}
        or item.get("viewing_aid_failed")
        or item.get("aid_message")
        or item.get("expected_refusal_failed")
    ]
    parts.append("<h2>Not built</h2>")
    for item in not_built:
        aid_failed = item.get("viewing_aid_failed") or item.get("aid_message")
        status = "viewing_aid_failed" if aid_failed else str(item["status"])
        message = item.get("aid_message", "") if aid_failed else item.get("message", "")
        if item.get("expected_refusal_failed"):
            status = "expected_refusal_failed"
            message = item["refusal_message"] + " " + str(message)
        parts.append(
            f"<p>{escape(str(item['source_name']))}: {escape(status)} {escape(str(message))}</p>"
        )
        if item["status"] == "done":
            folder = "photos" if item["kind"] == "photo" else "clips"
            parts.append(
                _link(folder, item["corrected_name"], "Product: " + item["corrected_name"])
            )
    display_note = (
        "Video stills are converted BT.1886 -> sRGB for display; both halves alike; "
        "the player's rendering differs."
    )
    check_note = 'page --check is a link check, not "finished"; use plain page for completion.'
    limits = (
        "Limits: unquoted paths with spaces and unlisted extensions may retain folder words. "
        "Untagged video still halves can differ in tone; every commissioned source is tagged."
    )
    roots.write_text(
        roots.allowed / "README.md",
        display_note + "\n" + check_note + "\n" + CONFLICT_RECOVERY + "\n" + limits + "\n",
    )
    parts.append(
        f"<footer><p>{escape(display_note)}</p><p>{escape(check_note)}</p></footer></html>"
    )
    return roots.write_text(roots.allowed / "index.html", "\n".join(parts) + "\n")


def check_links(path: Path, *, roots: OutputRoots) -> list[str]:
    """Find missing or unsafe href and src targets in a generated page.

    Args:
        path: Page to inspect.
        roots: Pack and source roots.

    Returns:
        Descriptions of every unresolved or nonlocal link.
    """

    class Links(HTMLParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            """Collect href/src values from parsed HTML start tags."""
            for key, value in attrs:
                if key in {"href", "src"} and value is not None:
                    targets.append(value)

    targets: list[str] = []
    errors = []
    try:
        roots.check(path)
        Links().feed(path.read_text(encoding="utf-8"))
    except (OSError, OutputPathError) as exc:
        return [f"index.html: {type(exc).__name__}"]
    for target in targets:
        parsed = urlsplit(target)
        name = unquote(parsed.path)
        try:
            if (
                parsed.scheme
                or parsed.netloc
                or parsed.query
                or not name
                or "\\" in name
                or Path(name).is_absolute()
            ):
                raise ValueError("nonlocal link")
            checked = roots.check(path.parent / name)
            if not checked.is_file():
                raise ValueError("missing file")
        except (ValueError, OSError, OutputPathError):
            errors.append(f"unresolved or unsafe link: {target}")
    return errors


def thumbnail(source: Path, destination: Path, *, roots: OutputRoots) -> Path:
    """Make a short-side-540 JPEG, converting embedded ICC colour to sRGB.

    Args:
        source: Viewing PNG, with or without an embedded ICC profile.
        destination: Guarded thumbnail target.
        roots: Pack and source roots.

    Returns:
        The thumbnail path.
    """
    image, icc = _rgb(source, 540)
    return _save(image, destination, icc, roots)


def pair_still(source: Path, corrected: Path, destination: Path, *, roots: OutputRoots) -> Path:
    """Write a source-left/corrected-right JPEG with short-side-1080 halves.

    Args:
        source: Source viewing PNG.
        corrected: Matching corrected viewing PNG.
        destination: Guarded pair-still target.
        roots: Pack and source roots.

    Returns:
        The pair-still path.
    """
    left, left_icc = _rgb(source, 1080)
    right, right_icc = _rgb(corrected, 1080)
    if left.size != right.size:
        raise ValueError("pair still display dimensions differ")
    pair = Image.new("RGB", (2 * left.width + 2, left.height), "white")
    pair.paste(left, (0, 0))
    pair.paste(right, (left.width + 2, 0))
    return _save(pair, destination, left_icc or right_icc, roots)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the stand-alone page link checker.

    Args:
        argv: Link-check arguments or process arguments when absent.

    Returns:
        Zero for resolved links or two for a failed check.
    """
    parser = argparse.ArgumentParser(description="Check all local review-pack links")
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args(argv)
    roots = (
        OutputRoots.from_config(subdir="wp5.3")
        if args.root is None
        else OutputRoots(args.root, args.root.parent / "__no_source_links__")
    )
    errors = check_links(roots.allowed / "index.html", roots=roots)
    for error in errors:
        print(error.encode("ascii", "backslashreplace").decode("ascii"))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
