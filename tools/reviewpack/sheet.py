"""Owner-review CSV preservation and numeric D65 tallies without a quality verdict."""

from __future__ import annotations

import csv
import io
import re
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from lookcheck.frames import OutputRoots

from .select import GROUPS, catalog

ARTIFACTS = ("halos", "banding", "color_errors", "shimmer", "flicker")
HEADER = (
    "item",
    "group",
    "kind",
    "source_name",
    "corrected_name",
    "preferred",
    *ARTIFACTS,
    "above_surface",
    "note",
    "viewing_aid_failed",
)
HEADLINE = frozenset({"P-A", "V-S", "V-D", "V-P"})


def _read(path: Path) -> list[dict[str, str]]:
    expected = {item.stem: item for item in catalog() if item.group != "V-R"}
    seen: set[str] = set()
    rows = []
    data = path.read_bytes()
    try:
        decoded = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        # Count CSV records, including a partially decoded quoted multiline cell.
        # The sentinel also accounts for an error at the first byte of a new row.
        prefix = exc.object[: exc.start].decode("utf-8")
        number = sum(1 for _ in csv.reader(io.StringIO(prefix + "\ufffd", newline="")))
        raise ValueError(f"row {number}: invalid UTF-8 encoding; save the sheet as UTF-8") from exc
    with io.StringIO(decoded, newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) not in {HEADER, HEADER[:-1]}:
            raise ValueError("sheet header must match the CP5 columns exactly")
        for number, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"row {number}: incorrect cell count")
            row = {key: str(value) for key, value in raw.items()}
            row.setdefault("viewing_aid_failed", "")
            item = expected.get(row["item"])
            if (
                item is None
                or row["item"] in seen
                or row["group"] != item.group
                or row["kind"] != item.kind
                or row["source_name"].casefold() != item.name.casefold()
            ):
                raise ValueError(f"row {number}: unknown, inconsistent or duplicate item identity")
            name = row["corrected_name"]
            suffix = ".png" if item.kind == "photo" else ".mp4"
            if (
                not name
                or "/" in name
                or "\\" in name
                or ":" in name
                or Path(name).suffix.lower() != suffix
                or not re.fullmatch(
                    re.escape(item.stem) + r"(?:-\d+)?_corrected(?:_\d+)?" + re.escape(suffix),
                    name,
                    flags=re.IGNORECASE,
                )
            ):
                raise ValueError(f"row {number}: invalid corrected name")
            if row["preferred"] not in {"", "yes", "no", "undecided"}:
                raise ValueError(f"row {number}: invalid preferred value")
            for key in (*ARTIFACTS, "above_surface", "viewing_aid_failed"):
                if row[key] not in {"", "yes"}:
                    raise ValueError(f"row {number}: invalid {key} value")
            seen.add(row["item"])
            rows.append(row)
    return rows


def _available(item: Mapping[str, Any]) -> bool:
    return bool(
        item["status"] == "done"
        and item["group"] != "V-R"
        and (
            item.get("reviewable", True)
            or item.get("viewing_aid_failed")
            or item.get("aid_message")
        )
    )


def write_sheet(
    items: Sequence[Mapping[str, Any]], destination: Path, *, roots: OutputRoots
) -> Path:
    """Write or extend the review sheet without losing existing owner answers.

    Args:
        items: Persisted item results, including unreviewable states.
        destination: Guarded CSV target.
        roots: Pack and source roots.

    Returns:
        The sheet path.
    """
    roots.check(destination)
    bom = destination.exists() and destination.read_bytes().startswith(b"\xef\xbb\xbf")
    old = _read(destination) if destination.exists() else []
    by_item = {row["item"]: row for row in old}
    current = {str(item["item"]): item for item in items}
    for existing_row in old:
        item = current.get(existing_row["item"])
        if item is None or not _available(item):
            raise ValueError(
                f"changed reviewable pair for {existing_row['item']}; owner sheet retained"
            )
    rows = list(old)
    for item in items:
        if not _available(item):
            continue
        row = dict.fromkeys(HEADER, "")
        row.update({key: str(item[key]) for key in HEADER[:5]})
        previous = by_item.get(row["item"])
        flag = "yes" if item.get("viewing_aid_failed") or item.get("aid_message") else ""
        row["viewing_aid_failed"] = flag
        if previous is not None:
            if any(previous[key] != row[key] for key in HEADER[:5]):
                raise ValueError(f"changed pair identity for {row['item']}; owner sheet retained")
            previous["viewing_aid_failed"] = flag
        else:
            rows.append(row)
            by_item[row["item"]] = row
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    temporary = destination.with_name(f".{destination.name}-{uuid.uuid4().hex}.tmp")
    try:
        roots.write_bytes(temporary, buffer.getvalue().encode("utf-8-sig" if bom else "utf-8"))
        roots.rename(temporary, destination)
    finally:
        if temporary.exists():
            roots.remove(temporary)
    return destination


def tally(path: Path) -> dict[str, Any]:
    """Strictly read the filled CSV and count groups, headline and candidates.

    Args:
        path: Owner sheet to read without modifying it.

    Returns:
        Preference, artifact and above-surface counts with no quality verdict.
    """
    rows = _read(path)

    def counts(groups: set[str] | frozenset[str]) -> dict[str, Any]:
        selected = [row for row in rows if row["group"] in groups]
        judged = sum(row["preferred"] != "" for row in selected)
        preferred = sum(row["preferred"] == "yes" for row in selected)
        expected = sum(item.group in groups for item in catalog())
        return {
            "expected": expected,
            "available": len(selected),
            "missing": expected - len(selected),
            "unjudged": len(selected) - judged,
            "judged": judged,
            "preferred": preferred,
            "fraction": preferred / judged if judged else 0.0,
            "artifacts": {key: sum(row[key] == "yes" for row in selected) for key in ARTIFACTS},
            "above_surface": sum(row["above_surface"] == "yes" for row in selected),
            "viewing_aid_failed": sum(row["viewing_aid_failed"] == "yes" for row in selected),
        }

    return {
        "groups": {group: counts({group}) for group in GROUPS if group != "V-R"},
        "headline": counts(HEADLINE),
        "candidates": counts({"P-Z", "V-Z"}),
    }


def format_tally(result: Mapping[str, Any]) -> str:
    """Format numeric results with D65's bar and no judgement words.

    Args:
        result: Parsed tally counts.

    Returns:
        Console-safe tally lines.
    """
    lines = []
    for label, values in [
        *result["groups"].items(),
        ("headline", result["headline"]),
        ("candidates", result["candidates"]),
    ]:
        line = (
            f"{label}: {values['preferred']}/{values['judged']} = {100 * values['fraction']:.1f} %"
        )
        if label == "headline":
            line += "  (D65 bar 80 %)"
        lines.append(line)
        lines.append(
            "  coverage: "
            + ", ".join(
                f"{key}={values[key]}" for key in ("expected", "available", "missing", "unjudged")
            )
        )
        lines.append(
            "  "
            + ", ".join(f"{key}={values['artifacts'][key]}" for key in ARTIFACTS)
            + f", above_surface={values['above_surface']}"
            + f", viewing_aid_failed={values['viewing_aid_failed']}"
        )
    return "\n".join(lines)
