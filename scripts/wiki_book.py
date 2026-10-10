#!/usr/bin/env python3
"""Build the Kelp wiki as an mdBook site from the same page files Wiki.js reads.

The page files do not change. This script reads them and does three things:

  summary   write SUMMARY.md at the repo root, from the folder layout and the
            front matter (title, isPublished). Pages with isPublished false are
            left out.
  stage     copy the public pages and the non-page assets into OUT/src, drop the
            Wiki.js front matter (the title becomes the page's H1 when the body
            has none), rewrite absolute links such as /tooling/coral into
            relative file links, and write OUT/src/SUMMARY.md.
  check     check every internal link and anchor in OUT/src. Exit 1 on a broken
            file link. Anchor misses are reported as warnings.
  build     stage, run mdbook on the staged book (book.toml is copied from the
            repo), then check the HTML output directory.

Only the Python standard library is used. mdbook comes from `nix shell
nixpkgs#mdbook` or from PATH. Nothing is written inside the repo except
SUMMARY.md, and nothing touches Wiki.js.

Usage:
    scripts/wiki_book.py summary
    scripts/wiki_book.py build /path/outside/the/repo/kelp-book
"""
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE = {"README.md"}  # the repo README is not a wiki page
NOT_ASSETS = {"book.toml", "SUMMARY.md", "wiki-mdbook-plan.txt", ".gitignore",
              "redirects.txt", "sidebar-order.txt"}
ORDER_FILE = "sidebar-order.txt"  # one page path per line, in sidebar order
FRONT_RE = re.compile(r"^(title|description|isPublished|tags):\s*(.*?)\s*$")
LINK_RE = re.compile(r"\]\((/[^)\s]*)\)")
MD_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")


FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^`]*)$")


def is_fence(line):
    """True for a line that opens or closes a fenced block (not inline ``` code)."""
    return FENCE_RE.match(line) is not None


def unquote(v):
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return v


def read_page(rel):
    """Return (front, body_lines) for a repo-relative .md path."""
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    front, body = {}, lines
    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                for line in lines[1:i]:
                    m = FRONT_RE.match(line)
                    if m:
                        front[m.group(1)] = unquote(m.group(2))
                body = lines[i + 1:]
                break
    return front, body


def git_files():
    out = subprocess.run(["git", "-C", REPO, "ls-files"], check=True,
                         capture_output=True, text=True).stdout
    return [f for f in out.splitlines() if f]


def pages():
    """All wiki pages, keyed by repo path, with their front matter."""
    result, hidden = {}, []
    for rel in git_files():
        if not rel.endswith(".md") or rel in EXCLUDE:
            continue
        front, body = read_page(rel)
        if front.get("isPublished", "true").lower() == "false":
            hidden.append(rel)
            continue
        redirect = "redirect" in front.get("tags", "").replace(" ", "").split(",")
        result[rel] = {"title": front.get("title", rel), "body": body, "redirect": redirect}
    return result, hidden


def sidebar_order():
    """Page paths from sidebar-order.txt, in the order they should appear."""
    path = os.path.join(REPO, ORDER_FILE)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]


def summary_lines(public):
    """Parent page first, then the pages in its folder (by file name), nested under it.

    A folder with no page of its own (no `name.md` beside it) has its pages
    listed at the level it sits in, so nothing disappears from the sidebar.
    """
    out = []
    order = {rel: i for i, rel in enumerate(sidebar_order())}
    # Stubs tagged redirect keep their old URL but stay out of the sidebar.
    public = {rel: page for rel, page in public.items() if not page["redirect"]}

    def key(rel):
        return (order.get(rel, len(order)), rel)

    def label(rel):
        return public[rel]["title"].replace("[", "\\[").replace("]", "\\]")

    def walk(folder, depth):
        prefix = "  " * depth + "- "
        here = sorted((p for p in public if os.path.dirname(p) == ("" if folder == "." else folder)), key=key)
        subdirs = sorted({p[len(folder) + 1 if folder != "." else 0:].split("/")[0]
                          for p in public if (folder == "." or p.startswith(folder + "/"))
                          and "/" in p[len(folder) + 1 if folder != "." else 0:]})
        for rel in here:
            if rel == "home.md":
                continue
            out.append(f"{prefix}[{label(rel)}]({rel})")
            sub = rel[:-3]
            if any(p.startswith(sub + "/") for p in public):
                walk(sub, depth + 1)
        for d in sorted(subdirs, key=lambda d: key((d if folder == "." else folder + "/" + d) + ".md")):
            path = d if folder == "." else folder + "/" + d
            if path + ".md" not in public:
                walk(path, depth)

    if "home.md" in public:
        out.append(f"- [{label('home.md')}](home.md)")
    walk(".", 0)
    return out


def write_summary():
    public, hidden = pages()
    text = "# Summary\n\n" + "\n".join(summary_lines(public)) + "\n"
    with open(os.path.join(REPO, "SUMMARY.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    return public, hidden, text


def page_target(path):
    return path[1:] if path.startswith("/") else path


def resolve_abs(target, public, repo_files):
    """Map a Wiki.js absolute path to a repo path, or None."""
    t = target.split("#", 1)[0].rstrip("/")
    if t in ("", "/"):
        return "home.md"
    t = page_target(t)
    if t + ".md" in public:
        return t + ".md"
    if t in repo_files:
        return t
    return None


def stage(out):
    public, hidden, summary = write_summary()
    repo_files = set(git_files())
    src = os.path.join(out, "src")
    if os.path.isdir(src):
        shutil.rmtree(src)
    os.makedirs(src)
    shutil.copy(os.path.join(REPO, "book.toml"), os.path.join(out, "book.toml"))
    with open(os.path.join(src, "SUMMARY.md"), "w", encoding="utf-8") as fh:
        fh.write(summary)
    problems = []
    for rel, page in public.items():
        body, fenced, text_lines = page["body"], False, []
        first = next((ln for ln in body if ln.strip()), "")
        if not first.startswith("# "):
            text_lines.append(f"# {page['title']}")
            text_lines.append("")
        for ln in body:
            if is_fence(ln):
                fenced = not fenced
            if not fenced and "](/" in ln:
                def repl(m):
                    target = m.group(1)
                    tgt_path = resolve_abs(target, public, repo_files)
                    if tgt_path is None:
                        # Not a page or asset in this repo (for example a WebKelp
                        # demo route). Left as written and reported as a warning.
                        problems.append(f"{rel}: not a page, left as written: {target}")
                        return m.group(0)
                    anchor = target[target.find("#"):] if "#" in target else ""
                    rel_to = os.path.relpath(tgt_path, os.path.dirname(rel) or ".")
                    return f"]({rel_to}{anchor})"
                ln = LINK_RE.sub(repl, ln)
            text_lines.append(ln)
        dest = os.path.join(src, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write("\n".join(text_lines))
    for rel in repo_files:
        if rel.endswith(".md") or rel in NOT_ASSETS or rel.startswith("scripts/"):
            continue
        if rel.startswith(".") or "/." in rel:
            continue
        dest = os.path.join(src, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy(os.path.join(REPO, rel), dest)
    for rel in hidden:
        print(f"hidden (isPublished false, not staged): {rel}")
    for p in problems:
        print("stage:", p)
    return 1 if problems else 0


def slugify(text):
    s = re.sub(r"<[^>]+>", "", text).strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def anchors_of(path, cache={}):
    if path not in cache:
        with open(path, encoding="utf-8") as fh:
            found, fenced, seen = set(), False, {}
            for ln in fh:
                if is_fence(ln):
                    fenced = not fenced
                    continue
                m = HEADING_RE.match(ln.rstrip("\n")) if not fenced else None
                if m:
                    base = slugify(m.group(1))
                    n = seen.get(base, 0)
                    found.add(base if n == 0 else f"{base}-{n}")
                    seen[base] = n + 1
            cache[path] = found
    return cache[path]


def check(out):
    src = os.path.join(out, "src")
    broken, warn = 0, 0
    for root, _, files in os.walk(src):
        for name in files:
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, src)
            fenced = False
            with open(path, encoding="utf-8") as fh:
                for ln in fh:
                    if is_fence(ln):
                        fenced = not fenced
                        continue
                    if fenced:
                        continue
                    ln = re.sub(r"`[^`]*`", "", ln)  # inline code is not a link
                    for m in MD_LINK_RE.finditer(ln):
                        t = m.group(1)
                        if t.startswith("/"):
                            print(f"warn {rel}: unrewritten absolute link {t}"); warn += 1
                            continue
                        if re.match(r"^[a-z]+:", t) or t.startswith("#"):
                            if t.startswith("#"):
                                if t[1:] not in anchors_of(path):
                                    print(f"warn {rel}: anchor {t}"); warn += 1
                            continue
                        f, _, a = t.partition("#")
                        target = os.path.normpath(os.path.join(os.path.dirname(path), f))
                        if not os.path.exists(target):
                            print(f"BROKEN {rel}: {t}"); broken += 1
                            continue
                        if a and target.endswith(".md") and a not in anchors_of(target):
                            print(f"warn {rel}: anchor {t}"); warn += 1
    print(f"link check: {broken} broken, {warn} anchor warnings")
    return 1 if broken else 0


def build(out):
    stage(out)
    env = dict(os.environ, MDBOOK_BUILD__BUILD_DIR=os.path.join(out, "out"))
    cmd = ["mdbook", "build", out]
    if shutil.which("mdbook") is None:
        cmd = ["nix", "shell", "nixpkgs#mdbook", "-c", "mdbook", "build", out]
    subprocess.run(cmd, check=True, env=env)
    return check(out)


def main(argv):
    if not argv or argv[0] not in ("summary", "stage", "check", "build"):
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "summary":
        write_summary()
        return 0
    out = os.path.abspath(argv[1]) if len(argv) > 1 else ""
    if not out or os.path.commonpath([out, REPO]) == REPO:
        print("give an output directory outside the repo")
        return 2
    os.makedirs(out, exist_ok=True)
    return {"stage": stage, "check": check, "build": build}[cmd](out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
