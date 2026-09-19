#!/usr/bin/env python3
"""Generate the standard library index from the shipped stdlib sources.

The authority is `kelpc/std/*.kp` in the kelp repository: the signature of every
`fun`, `const`, `datac` and `enum` it declares. This writes

    docs/reference/stdlib-index.md

with one line per name, grouped by module, plus the module -> capability-domain
table the compiler's own `stdlib.rs` uses (`domain_of`).

Implementation bodies are stripped: `fun alloc(n: usize).R: Bytes = alloc_raw(n)`
is indexed as `fun alloc(n: usize).R: Bytes`, because the body is not part of the
API and would drown the page. Multi-line declarations (`datac Child(`, an `enum`
with several variants) are joined onto one line for the same reason.

Usage:
    python3 tools/stdlib-index.py [path/to/kelp]

Default source: ../kelp relative to this repository, which is the KelpLANG
checkout layout. Re-run it and commit the result when the stdlib changes.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_KELP = REPO.parent / "kelp"
PAGE = REPO / "docs" / "reference" / "stdlib-index.md"

# The module -> domain map, mirroring `kelpc/src/stdlib.rs::domain_of`.
GATED = {
    "fs": "fs",
    "net": "net",
    "process": "process",
    "env": "env",
    "time": "time",
    "rand": "rand",
}

ORDER = [
    "mem", "str", "path", "math", "fmt", "io", "fs", "process",
    "net", "http", "time", "rand", "env", "list", "option", "result",
]


def fun_sig(line: str) -> str:
    """A `fun` line with its implementation body removed."""
    head = line.strip()
    depth = 0
    for i, ch in enumerate(head):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                rest = head[i + 1:]
                cut = rest.find(" = ")
                if cut != -1:
                    head = head[: i + 1 + cut]
                break
    return f'`{head.rstrip(" {").strip()}`'


def joined(lines: list[str], start: int, opener: str, closer: str) -> str:
    """A declaration that spans lines, flattened onto one line."""
    depth = 0
    out = []
    for line in lines[start:]:
        depth += line.count(opener) - line.count(closer)
        out.append(line.strip())
        if depth <= 0 and opener in "".join(out):
            break
    text = re.sub(r"\s+", " ", " ".join(out))
    # `datac Child(\n    val pid: i32,\n)` flattens to `Child( val pid: i32, )`.
    text = text.replace("( ", "(").replace(", )", ")").replace(" )", ")")
    return text


def enum_sig(lines: list[str], start: int) -> str:
    """`enum Name { A, B(val x: T) }` on one line, variants comma-separated."""
    out = []
    for line in lines[start:]:
        out.append(line.strip())
        if line.rstrip().endswith("}"):
            break
    text = re.sub(r"\s+", " ", " ".join(out))
    match = re.match(r"(enum [A-Za-z0-9_]+(?:<[^>]*>)? )\{([^}]*)\}", text)
    if match:
        variants = re.findall(r"[A-Z][A-Za-z0-9_]*(?:\([^)]*\))?", match.group(2))
        text = f'{match.group(1)}{{ {", ".join(variants)} }}'
    return f"`{text}`"


def module_page(mod: str, path: pathlib.Path) -> tuple[list[str], int, int]:
    lines = path.read_text().split("\n")
    funs: list[str] = []
    types: list[str] = []
    consts: list[str] = []
    for i, line in enumerate(lines):
        if re.match(r"^fun ", line):
            funs.append(fun_sig(line))
        elif re.match(r"^datac ", line):
            types.append(f'`{joined(lines, i, "(", ")")}`' if line.rstrip().endswith("(") else fun_sig(line))
        elif re.match(r"^enum ", line):
            types.append(enum_sig(lines, i))
        elif re.match(r"^const ", line):
            consts.append(fun_sig(line))

    head = f"## `std/{mod}`"
    if mod in GATED:
        head += f" — needs `{GATED[mod]}`"
    out = [head + "\n"]
    if types:
        out.append("Types:\n")
        out.append("\n".join(f"- {t}" for t in types) + "\n")
    if consts:
        out.append("Constants:\n")
        out.append("\n".join(f"- {c}" for c in consts) + "\n")
    if funs:
        out.append("Functions:\n")
        out.append("\n".join(f"- {f}" for f in funs) + "\n")
    return out, len(funs), len(types) + len(consts)


def main() -> int:
    kelp = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_KELP
    std = kelp / "kelpc" / "std"
    if not std.is_dir():
        print(f"no stdlib at {std}", file=sys.stderr)
        return 1
    try:
        rev = subprocess.run(["git", "-C", str(kelp), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        rev = "unknown"

    page = [
        "# Standard library index",
        "",
        "Every public name in the shipped standard library, one line each, generated from",
        f"`kelpc/std/*.kp` at `kelp` commit `{rev}` by `tools/stdlib-index.py`. Behaviour, panics",
        "and examples live in the [Standard library](../stdlib/index.md) chapter.",
        "",
        "A module marked with a domain needs that capability delegated on the `impl` line, e.g.",
        '`impl "std/fs" with caps(fs = ["/srv/data/**"])`.',
        "",
    ]
    table = []
    for mod in ORDER:
        path = std / f"{mod}.kp"
        if not path.exists():
            continue
        body, n_fun, n_other = module_page(mod, path)
        page.extend(body)
        table.append((mod, n_fun, n_other))

    page += [
        "## Modules at a glance",
        "",
        "| Module | Functions | Types/constants | Domain |",
        "| --- | ---: | ---: | --- |",
    ]
    for mod, n_fun, n_other in table:
        page.append(f"| `std/{mod}` | {n_fun} | {n_other} | {GATED.get(mod, '—')} |")

    page += [
        "",
        "## Not importable",
        "",
        '`std/rt` holds the capability matcher the compiler uses internally and is excluded from',
        'the shipped list, so `impl "std/rt"` is refused. The importable glob matcher is',
        "[`glob`](../libraries/glob.md).",
        "",
        "## See also",
        "",
        "- [Standard library](../stdlib/index.md)",
        "- [Capabilities](../language/capabilities.md)",
        "- [Capability patterns](capability-patterns.md)",
        "",
    ]
    PAGE.write_text("\n".join(page))
    total = sum(n_fun + n_other for _m, n_fun, n_other in table)
    print(f"wrote {PAGE.relative_to(REPO)}: {len(table)} modules, {total} names, kelp rev {rev}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
