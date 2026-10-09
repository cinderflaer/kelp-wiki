---
title: "Roadmap"
description: "A pointer to plan/roadmap.md in the kelp repository, which is the authority for the marks, the stages, the stages' milestones and their identifier rules."
isPublished: true
tags: "meta"
---

Kelp's milestones are **marks** (a named goal), **stages** (a significant part of a mark) and **stages' milestones**. The hierarchy, the identifier rules and every mark's status are defined in [`plan/roadmap.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/roadmap.md), which is the authority for the roadmap. The roadmap has no dates: a mark moves when its prerequisites land, not on a calendar.

## Status of the marks

The table below was copied from the marks-at-a-glance table in `plan/roadmap.md` on the kelp repository's `main` branch on 2026-10-09. Where it and that file disagree, the file wins and this table is out of date.

| Mark | Name | Status |
| --- | --- | --- |
| MK1 | Core language | Done |
| MK2 | Modules and compile-time | Done |
| MK3 | Heap and containers | Done |
| MK4 | Capability security | Done |
| MK5 | Standard library program | In progress |
| MK6 | Concurrency | Done: threads, the memory model, and concurrent downloads |
| MK7 | LLVM backend | Done: LLVM is the default backend, released in 26.10.0 |
| MK8 | Language ergonomics and scale | In progress |
| MK9 | Systems substrate | Started |
| MK10 | Capability model extensions | Proposed |
| MK11 | Verification and semantics | Proposed |

Kelp 26.10.4 is the current release, and the [changelog](/changelog) has what each release added.

## See also

- [Source documents](/meta/source-documents): which file is the authority for what
- [Compiler](/compiler): the pipeline the milestones extend
