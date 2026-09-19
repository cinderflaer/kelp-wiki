---
title: "About this repository"
description: "How the Kelp documentation wiki is stored: one file per page, the path is the page path, and Wiki.js syncs it every five minutes in both directions."
isPublished: true
tags: "meta"
---

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

- **Hierarchy** comes from the file paths. Nothing declares it.
- **The ordered sidebar menu** is edited in the admin UI, under *Theming →
  Navigation*, and stored in the `navigation` row of the Wiki.js database.
  Navigation items have no children field, so that menu is flat; the pages under
  a chapter come from the file paths.

`/var/lib/wikijs/nav.json` on `homelabone` is a **record** of that menu, not its
source. The admin UI is the editor, and the record is refreshed from it:

```sh
ssh thinkbox "sudo -u postgres psql -d wikijs -tAc \"select config::text from navigation where key='site'\"" \
  | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))' > nav.json
```

The reverse, writing the file back into the wiki:

```sh
scp nav.json thinkbox:/tmp/ && ssh thinkbox "sudo install -o root -g root -m 644 /tmp/nav.json /var/lib/wikijs/nav.json \
  && sudo -u postgres psql -d wikijs -c \"update navigation set config = (select pg_read_file('/var/lib/wikijs/nav.json'))::json where key='site'\" \
  && sudo systemctl restart podman-wikijs"
```

The mode is a separate setting in the same admin screen: `TREE`, `MIXED` (menu
plus page tree), `STATIC` (menu only) or `NONE`. It is currently `STATIC`.

## Sync

Wiki.js syncs every five minutes in both directions. A page edited in the browser
arrives here as a commit; a commit here becomes a page. Neither side is
authoritative over the other, so edit where it suits you.

There is one directed dependency: Wiki.js imports the diff of the **last commit
only**, and a branch is checked out by the module's init step on every container
restart. Two consequences:

- A container restart between your commit and the next sync marks the commit as
  handled without importing it. Touch the file again in a new commit.
- An interrupted sync does the same. The same fix applies.

## History

`main` was the MkDocs Material source until 2026-09-19: `docs/`, `mkdocs.yml`,
`hooks/` and `tools/`, served at `homelabone.xenoo.dev/kelp/`. That layout is
kept at branch `mkdocs-archive` and tag `mkdocs-final`.

Kelp syntax highlighting was lost in the move. The MkDocs build registered a
custom `kelp` fence language in `hooks/kelp_lexer.py`; Wiki.js has no such
grammar and renders Kelp blocks unhighlighted.
