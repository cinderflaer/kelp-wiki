---
title: "Polyp changelog"
description: "Every tagged release of Polyp, newest first, with a link to the Gitea release. What a release added to the library, its backends and the WebKelp tree."
isPublished: true
tags: "library, ui"
---
Every release of [Polyp](/libraries/polyp), newest first. The source is the
[Polyp repository](https://homelabone.xenoo.dev/gittea/Lilly/polyp), and each entry
links to its own tag and release.

## 26.10.5 (2026-10-09)

[Release](https://homelabone.xenoo.dev/gittea/Lilly/polyp/releases/tag/v26.10.5)

Released with Kelp 26.10.5. The first release with the v5 layout, and the first to
list everything from v0 to v5 in one place.

**Layout.** The repository is `core/` (the backend-neutral loop, tree, diff,
diagnostics and animation maths), `backends/gtk/`, `backends/headless/`,
`backends/soft/`, `tools/`, `web/`, `docs/plan/` and `tests/`. A program still writes
`polyp.column { ... }`: the facade is `backends/gtk/polyp/lib.kp`, so the namespace
stays `polyp.`.

**WebKelp is in the repository.** The WebKelp compiler lives in `web/`, with its
history. Its standalone repository is archived, and its demo and playground sites
were removed. The README is rewritten in the WebKelp style.

**Callbacks carry a closure.** A row entry can capture its row index in an `on_change`
closure, `closure(String).return: M`. The closure returns a `Msg`. State still changes
only through `update` (decision D1 in `docs/plan/polyp-v5.md`).

**HTML output.** `polyp.emit_html(init, view)` writes a Polyp app's first frame as
static HTML. `kelpc` runs it when `coral.toml` sets `[build] emit = "html"` and
`emit_entry`. The page has no event wiring, and it shows the first frame only.

**Headless and soft backends run without a display.** The `tests/callbacks` program
(`anne`, `robert`, `hello`, `3`) and the nine `polyp-*` test projects in the Kelp
repository pass on this release.

**Also in this release: the v0 to v4 work.**
- v0: plain constructors and the first `run` loop.
- v1: the builder syntax, `polyp.column { k -> ... }`.
- v2: keyed patching of the live widget tree, `scrolled`, `checkbox`, `progress`,
  `separator`, layout options and `polyp.css`.
- v3: the `core/` split, the headless and soft backends, the integer software
  raster, the bare-metal proof and the work-budget benchmark.
- v4: a platform clock with timers, integer animations, UTF-8 soft text and editing,
  an on-demand accessibility tree, and memoised subtrees.

**Not in this release.** Lists with stable ids, manifest-generated externs and the
soft backend's stylesheet are on unmerged branches, so they are not described here.
