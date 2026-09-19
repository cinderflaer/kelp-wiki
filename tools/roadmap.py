#!/usr/bin/env python3
"""Generate the roadmap page (and the Home page's roadmap block) from the plan.

The authority is `plan/roadmap.md` in the kelp repository: its "The marks at a
glance" table and its "The critical path" table. This script reads those two
tables and writes

    docs/meta/roadmap.md                     the full page
    docs/index.md                            the block between the
                                             `<!-- roadmap:start -->` and
                                             `<!-- roadmap:end -->` markers

Nothing is invented: a mark's name, size and status come from the table, and the
diagrams are drawn from that data. No dates are invented — the diagrams show
order and status, not calendar time, because the roadmap has no dates.

Usage:
    python3 tools/roadmap.py [path/to/roadmap.md]

Default source: ../kelp/plan/roadmap.md relative to this repository, which is the
KelpLANG checkout layout. Re-run it and commit the result when the roadmap moves.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = REPO.parent / "kelp" / "plan" / "roadmap.md"
PAGE = REPO / "docs" / "meta" / "roadmap.md"
HOME = REPO / "docs" / "index.md"

START = "<!-- roadmap:start -->"
END = "<!-- roadmap:end -->"

# Which band a status belongs in, and the colour that band gets in the diagram.
BANDS = [
    ("done", "Done", "statusDone", re.compile(r"^\s*(~~)?\s*Done\b|\*\*Done\*\*")),
    ("active", "In progress", "statusActive", re.compile(r"In progress", re.I)),
    ("planned", "Not started", "statusPlanned", re.compile(r"Not started", re.I)),
    ("proposed", "Proposed", "statusProposed", re.compile(r"Proposed", re.I)),
]

CLASS_DEFS = """    classDef statusDone fill:#2e8b57,color:#ffffff,stroke:#24633f
    classDef statusActive fill:#c47f00,color:#ffffff,stroke:#9a6400
    classDef statusPlanned fill:#5b6b7a,color:#ffffff,stroke:#455260
    classDef statusProposed fill:#7c6a94,color:#ffffff,stroke:#615275
"""


def band_of(status: str) -> str:
    for key, _label, _cls, pattern in BANDS:
        if pattern.search(status):
            return key
    return "proposed"


def clean(cell: str) -> str:
    """A table cell as plain text: no bold, no links, no strikethrough."""
    cell = cell.replace("**", "").replace("~~", "")
    cell = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell)
    return re.sub(r"\s+", " ", cell).strip()


def short(status: str, limit: int = 110) -> str:
    """The status cell trimmed to its first clause, for a table."""
    text = clean(status)
    for cut in (";", " — ", " - ", ". "):
        if cut in text:
            text = text.split(cut)[0]
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_marks(text: str) -> list[dict]:
    """Rows of the `The marks at a glance` table."""
    marks = []
    for line in text.split("\n"):
        if not re.match(r"^\|\s*\*\*MK\d+\*\*\s*\|", line):
            continue
        c = cells(line)
        if len(c) < 5:
            continue
        code = clean(c[0])
        marks.append({
            "code": code,
            "name": clean(c[1]),
            "stages": clean(c[2]),
            "size": clean(c[3]),
            "status": clean(c[4]),
            "band": band_of(c[4]),
        })
    return marks


def parse_critical_path(text: str) -> list[dict]:
    """Rows of `The critical path` table, which has a struck-through number when done."""
    rows = []
    section = text.split("## The critical path", 1)
    if len(section) < 2:
        return rows
    body = section[1].split("### ", 1)[0]
    for line in body.split("\n"):
        if not re.match(r"^\|\s*(~~)?\s*\d+\s*(~~)?\s*\|", line):
            continue
        c = cells(line)
        if len(c) < 4:
            continue
        done = "~~" in c[0]
        label = clean(c[1])
        code = label.split(":")[0].split(" ")[0]
        rows.append({
            "code": code,
            "label": label,
            "size": clean(c[2]),
            "why": clean(c[3]),
            "done": done,
        })
    return rows


def parse_unscheduled(text: str) -> list[dict]:
    rows = []
    body = text.split("### Also possible, not scheduled", 1)
    if len(body) < 2:
        return rows
    body = body[1].split("\n## ", 1)[0]
    for line in body.split("\n"):
        if not line.startswith("|") or re.match(r"^\|\s*-+", line) or "| Item |" in line:
            continue
        c = cells(line)
        if len(c) < 3:
            continue
        rows.append({"item": clean(c[0]), "blocked": clean(c[1]), "note": clean(c[2])})
    return rows


def marks_diagram(marks: list[dict]) -> str:
    lines = ["```mermaid", "flowchart LR"]
    for key, label, _cls, _pattern in BANDS:
        group = [m for m in marks if m["band"] == key]
        if not group:
            continue
        lines.append(f'    subgraph {key}["{label}"]')
        lines.append("        direction TB")
        for m in group:
            label_text = f'{m["code"]} {m["name"]}<br/>{m["size"]}'
            lines.append(f'        {m["code"]}["{label_text}"]')
        lines.append("    end")
    lines.append(CLASS_DEFS.rstrip("\n"))
    for key, _label, cls, _pattern in BANDS:
        group = [m["code"] for m in marks if m["band"] == key]
        if group:
            lines.append(f'    class {",".join(group)} {cls}')
    lines.append("```")
    return "\n".join(lines)


def critical_diagram(rows: list[dict]) -> str:
    lines = ["```mermaid", "flowchart LR"]
    for i, row in enumerate(rows):
        status = "statusDone" if row["done"] else "statusActive"
        lines.append(f'    {row["code"]}["{i + 1}. {row["label"]}<br/>{row["size"]}"]:::{status}')
    for i in range(len(rows) - 1):
        lines.append(f'    {rows[i]["code"]} --> {rows[i + 1]["code"]}')
    lines.append(CLASS_DEFS.rstrip("\n"))
    lines.append("```")
    return "\n".join(lines)


def home_block(marks: list[dict], critical: list[dict], rev: str) -> str:
    done = [m for m in marks if m["band"] == "done"]
    active = [m for m in marks if m["band"] == "active"]
    planned = [m for m in marks if m["band"] in ("planned", "proposed")]
    next_row = next((r for r in critical if not r["done"]), None)
    summary = (
        f"Of the {len(marks)} marks, **{len(done)} are done**, "
        f"**{len(active)} in progress** ({', '.join(m['code'] for m in active)}) and "
        f"{len(planned)} planned or proposed."
    )
    if next_row:
        summary += (
            f" The critical path is next at **{next_row['code']}** — "
            f"{next_row['label'].split(':', 1)[-1].strip()}."
        )
    return f"""{START}
## Roadmap

{summary} No dates: the milestones are ordered by dependency, not by calendar — a
mark moves when its prerequisites land, and `plan/roadmap.md` is the record.

{marks_diagram(marks)}

[The full roadmap](meta/roadmap.md) has every mark's scope and status, the
five-row critical path, and what is named but not scheduled. Generated from
`plan/roadmap.md` at `kelp` commit `{rev}`.
{END}"""


def git_rev() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(REPO.parent / "kelp"), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    source = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.exists():
        print(f"roadmap source not found: {source}", file=sys.stderr)
        return 1
    text = source.read_text()
    marks = parse_marks(text)
    if not marks:
        print("no mark rows parsed — has the table changed shape?", file=sys.stderr)
        return 1
    critical = parse_critical_path(text)
    unscheduled = parse_unscheduled(text)
    rev = git_rev()

    page = [
        "# Roadmap",
        "",
        f"Kelp's milestones are **marks** (a named goal), **stages** (a significant part of a "
        f"mark) and **stages' milestones**; the hierarchy and the identifier rules are in "
        f"[`plan/roadmap.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/roadmap.md), "
        f"which is the authority for everything on this page.",
        "",
        f"Generated from `plan/roadmap.md` at `kelp` commit `{rev}` by `tools/roadmap.py` in the "
        f"wiki repository — re-run it and commit the result when the roadmap moves. The diagrams "
        f"show order and status, not calendar time: the roadmap has no dates, because a mark "
        f"moves when its prerequisites land rather than on a schedule.",
        "",
        "## The marks at a glance",
        "",
        marks_diagram(marks),
        "",
        "| Mark | What it is | Stages | Size | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    for m in marks:
        page.append(f'| **{m["code"]}** | {m["name"]} | {m["stages"]} | {m["size"]} | {short(m["status"])} |')

    if critical:
        done = sum(1 for r in critical if r["done"])
        page += [
            "",
            "## The critical path",
            "",
            f"Five milestones, in order — {done} of them done. Each is here because the one "
            "before it is a prerequisite, or because the payoff is what the rest of the list "
            "exists for. Everything else is in the open items or the backlog.",
            "",
            critical_diagram(critical),
            "",
            "| # | Milestone | Size | Why it is next |",
            "| --- | --- | --- | --- |",
        ]
        for i, r in enumerate(critical):
            number = f"~~{i + 1}~~" if r["done"] else str(i + 1)
            page.append(f'| {number} | **{r["label"]}** | {r["size"]} | {r["why"]} |')

    if unscheduled:
        page += [
            "",
            "## Named, not scheduled",
            "",
            "Real work that is not next: nothing here is a question (those are the open items) "
            "and nothing here is a commitment (those are the marks).",
            "",
            "| Item | Blocked on | Note |",
            "| --- | --- | --- |",
        ]
        for r in unscheduled:
            page.append(f'| {r["item"]} | {r["blocked"]} | {r["note"]} |')

    page += [
        "",
        "## See also",
        "",
        "- [Source documents](source-documents.md) — which file is the authority for what",
        "- [Known issues](known-issues.md) — what is broken today, with repros",
        "- [Compiler](../compiler/index.md) — the pipeline the milestones extend",
        "",
    ]
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text("\n".join(page))

    home = HOME.read_text()
    if START not in home or END not in home:
        print(f"index.md has no {START} / {END} markers — page written, home untouched", file=sys.stderr)
    else:
        head, rest = home.split(START, 1)
        _old, tail = rest.split(END, 1)
        HOME.write_text(head + home_block(marks, critical, rev) + tail)

    by_band = {key: sum(1 for m in marks if m["band"] == key) for key, *_ in BANDS}
    print(f"wrote {PAGE.relative_to(REPO)}: {len(marks)} marks {by_band}, "
          f"{len(critical)} critical-path rows, {len(unscheduled)} unscheduled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
