# kelp-wiki

The content of the Kelp documentation wiki, served at
<https://kelp.xenoo.dev/>.

This repository is the storage backend for a [Wiki.js](https://js.wiki/) instance
on `homelabone`. There is no build step and no site generator: Wiki.js reads this
repository every five minutes, both ways, and the file layout *is* the page structure.

## Layout

The path of a file is the path of the page.

| File | Page |
| --- | --- |
| `home.md` | the home page, at `/` |
| `language.md` | the parent page `language` |
| `language/types.md` | the child page `language/types`, at `/language/types` |
| `examples/src/wordcount.kp` | not a page; a downloadable asset |

Adding a file adds a page. Deleting one removes it. Renaming one moves it.

Wiki.js decides which files are pages by extension, so anything that is not
markdown is stored as an asset instead.

## Front matter

Only four keys are read by the git storage module:

```yaml
---
title: "Types"
description: "Kelp's types fall into three kinds, and the kind decides what assignment means ..."
isPublished: true
tags: "language, ownership"
---
```

- `title` and `description` are rendered in the page header, the search index and
  link previews. Quote them: titles contain `: ` and backticks.
- `isPublished` must be a boolean. `published:` is not read and does nothing.
- `tags` must be a comma-space separated **string**. The module does
  `tags.split(', ')`; a YAML list makes it throw `_.get(...).split is not a
  function` and drops the page without creating it. Forty-three pages once
  survived a bad import only because their titles broke YAML parsing and left them
  without a `tags` key at all.

Tag vocabulary, so the tag browser stays useful: one chapter tag per page
(`overview`, `getting-started`, `language`, `stdlib`, `library`, `example`,
`compiler`, `tooling`, `reference`, `meta`) plus cross-cutting topics
(`capability`, `ownership`, `errors`, `cli`, `networking`, `filesystem`, `text`,
`collections`, `data-formats`, `math`, `time`, `testing`).

## Navigation

Two independent things:

- **Hierarchy** comes from the file paths. Nothing declares it.
- **The ordered sidebar menu** is not in this repository. Wiki.js navigation
  items have no children field, so the menu lives in Wiki.js itself: on
  `homelabone` it is `/var/lib/wikijs/nav.json`, generated from the navigation
  order the MkDocs site used, and applied with an `update navigation` statement
  followed by a restart.

## Sync

Wiki.js syncs every five minutes in both directions. A page edited in the browser
arrives here as a commit; a commit here becomes a page. Neither side is
authoritative over the other, so edit where it suits you.

There is one directed dependency: Wiki.js imports the diff of the **last commit
only**. A commit that touches many files is fine, but if a sync is interrupted
mid-run, the module considers the commit handled and will not retry it. Touch the
files again in a new commit to force a re-import.

## History

`main` was the MkDocs Material source until 2026-09-19: `docs/`, `mkdocs.yml`,
`hooks/` and `tools/`, served at `homelabone.xenoo.dev/kelp/`. That layout is
kept at branch `mkdocs-archive` and tag `mkdocs-final`.

Kelp syntax highlighting was lost in the move. The MkDocs build registered a
custom `kelp` fence language in `hooks/kelp_lexer.py`; Wiki.js has no such
grammar and renders Kelp blocks unhighlighted.
