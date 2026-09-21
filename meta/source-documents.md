---
title: "Source documents"
description: "This documentation is derived from files that live in the repositories. Where a page here and its source disagree, the source is right and the page is a bug."
isPublished: true
tags: "meta"
---
This documentation is derived from files that live in the repositories. Where a
page here and its source disagree, the source is right and the page is a bug.

## `kelp`

| File | Authority for |
| --- | --- |
| [`plan/syntax.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md) | the language and the style: every section of the Language chapter cites it by number |
| [`plan/architecture.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/architecture.md) | the design: compiler layout, the capability model, the v1 surface, the standard library's decisions |
| [`plan/roadmap.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/roadmap.md) | the plan: the marks, the open items, the backlog |
| [`plan/done.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/done.md) | the milestone record of what has shipped |
| [`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md) | the compiler's LLVM backend: the crate and linking decision, what stays the same, what is our work, the switch criteria and the stages |
| [`plan/asm-backend/`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/) | the removed hand-written backend track: its plans, its call-overhead measurement, and the encoder and ELF-writer inventory |
| [`README.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/README.md) | the front door: what the language has, how to build, the repository layout |
| `kelpc/std/*.kp` | the standard library, which is the authority for its own signatures: the [index](/reference/stdlib-index) is generated from it |
| `kelpc/src/*.rs` | the compiler; each file's `//!` header describes its job |
| `kelpc/tests/` | the fixture suite and the gates |
| `bench/speed/` | the four-workload benchmark |

## The other repositories

| Repository | Role | Authority |
| --- | --- | --- |
| [`coral`](https://homelabone.xenoo.dev/gittea/Juniper/coral) | the build tool and package manager: manifest, tasks, build cache, dependencies | its `README.md` is the source for [Coral](/tooling/coral) |
| [`lighthouse`](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse) | IDE support: the LSP server, the VS Code extension, the IntelliJ plugin | its `README.md` is the source for [Lighthouse](/tooling/lighthouse) |
| [`fpl`](https://homelabone.xenoo.dev/gittea/Juniper/fpl) | the first-party library catalogue, one folder per library | each library's `lib.kp`, and its page in the [Libraries chapter](/libraries) |
| [`kelp-wiki`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki) | this wiki's sources | this repository: one file per page, and the file path is the page path |

## How this wiki is built

[Wiki.js](https://kelp.xenoo.dev/) with the pages stored in this repository. The
file path is the page path: `language/types.md` is the page `language/types`,
`language.md` is its parent, and `home.md` is the home page. Adding a file adds a
page; the wiki picks it up on the next sync.

Front matter carries the four keys the git storage module reads:

```yaml
---
title: "Types"
description: "Kelp's types fall into three kinds ..."
isPublished: true
tags: "language, ownership"
---
```

`tags` must be a comma-space separated **string**, not a YAML list. The module
does `tags.split(', ')`, so a list throws and the page is skipped entirely — which
is how sixty pages went missing once already.

Two parts of the navigation are separate:

- The hierarchy is the file layout. Nothing else declares it.
- The ordered sidebar menu is not in this repository. Wiki.js navigation items
  have no children field, so that menu lives in Wiki.js itself, as
  `/var/lib/wikijs/nav.json` on `homelabone`, and is applied with one `update
  navigation` statement.

The git module syncs every five minutes in both directions: a page edited in the
browser arrives here as a commit, and a commit here becomes a page. Kelp code
blocks are not syntax-highlighted: Wiki.js has no `kelp` grammar, and the
highlighter the MkDocs build used lived in `hooks/kelp_lexer.py` of the archived
layout.

## See also

- [Contributing](/meta/contributing)

