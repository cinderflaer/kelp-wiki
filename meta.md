---
title: "Meta"
description: "How this documentation relates to the code, what is known to be broken, and how to work on the project."
isPublished: true
tags: "meta"
---
How this documentation relates to the code, what is known to be broken, and how to
work on the project.

| Page | What it is |
| --- | --- |
| [Source documents](/meta/source-documents) | which file in which repository is the authority for what |
| [Contributing](/meta/contributing) | repository layout, tests, gates, and how this site is built and served |
| [Documentation audit, October 2026](/meta/audit-2026-10) | every runnable example run against the compiler, with the verdict for each block |

## The one-paragraph version

This site is a **derived** document. The authorities live in the repositories:
`plan/syntax.md` for the language and style, `plan/architecture.md` for the design,
`plan/roadmap.md` for the plan and `plan/done.md` for what has shipped. Each page
here cites the section it came from, and where a page and its source disagree, the
source wins. That is a bug in the page, so please report it.
