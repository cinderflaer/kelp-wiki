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
| [`design/syntax`](/design/syntax) | the language and the style: every section of the Language chapter cites it by number |
| [`design/architecture`](/design/architecture) | the design: compiler layout, the capability model, the v1 surface, the standard library's decisions |
| [`meta/roadmap`](/meta/roadmap) | the plan: the marks, the open items, the backlog. This page is the authority; it replaces the roadmap file that was in `plan/` |
| [`meta/open-issues`](/meta/open-issues) | the open bugs and missing features, with the rule for adding and closing one. This page replaces `plan/ISSUES.md` in the kelp repository |
| [`meta/milestones.md`](/meta/milestones) | the milestone record of what has shipped, including the MK7 LLVM backend and the retired hand-written track it replaced |
| [`kelp issue #245`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/issues/245) | the memory model and threads: the plan of record for MK9-S3-M1 (atomics, ordering, the Send/Sync-shaped discipline) and MK6-S1-M1 (threads, the per-thread panic policy). The decisions are settled, stage A1 (`Atomic<T>` and `Ordering`, in [`std/atomic`](/stdlib/atomic)), stage A2 (`thread.fence`), stage B1 (the crossing rules the checker enforces) and stage C1 (`thread.spawn` and `thread.join`) have shipped, and the stages after them have not |
| [`README.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/README.md) | the front door: what the language has, how to build, the repository layout |
| `kelpc/std/*.kp` | the standard library, which is the authority for its own signatures: the [index](/reference/stdlib-index) is kept in step with it |
| `kelpc/src/*.rs` | the compiler; each file's `//!` header describes its job |
| `kelpc/tests/` | the fixture suite and the gates |
| `bench/` | the thirteen-program benchmark suite and its harness `bench/run.sh`; `bench/RESULTS.md` holds the results and `bench/notes.md` the analysis |
| `bench/speed/`, `bench/write_20gb/` | two small workloads with their own recorded results |

## The other repositories

| Repository | Role | Authority |
| --- | --- | --- |
| [`coral`](https://homelabone.xenoo.dev/gittea/Lilly/coral) | the build tool and package manager: manifest, tasks, build cache, dependencies | its `README.md` is the source for [Coral](/tooling/coral) |
| [`lighthouse`](https://homelabone.xenoo.dev/gittea/Lilly/lighthouse) | IDE support: the LSP server, the IntelliJ plugin | its `README.md` is the source for [Lighthouse](/tooling/lighthouse) |
| [`fpl`](https://homelabone.xenoo.dev/gittea/Lilly/fpl) | the first-party library catalogue, one folder per library | each library's `lib.kp`, and its page in the [Libraries chapter](/libraries) |
| [`kelp-wiki`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki) | this wiki's sources | this repository: one file per page, and the file path is the page path |

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
does `tags.split(', ')`, so a list throws and the page is skipped entirely. That
has happened once already, and sixty pages went missing.

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

