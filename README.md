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
- **`description` must be 255 characters or fewer.** The `pages.description`
  column is `varchar(255)`, so a longer value makes the insert fail with `value
  too long for type character varying(255)`. Wiki.js logs `Failed to process
  <path>` and then reports the sync as `COMPLETED`, so the page never exists and
  nothing else says so: the first sign is a 404 on a page that is plainly in the
  repository. Four pages were over the limit when this was found (`discord`,
  `kelpc-cli`, `backends`, `runtime`); three of them were live only because
  Wiki.js rewrites a page that has not changed, so the trap waits for the next
  edit.
- `isPublished` must be a boolean. `published:` is not read and does nothing.
- `tags` must be a comma-space separated **string**. The module does
  `tags.split(', ')`; a YAML list makes it throw `_.get(...).split is not a
  function` and drops the page without creating it. Forty-three pages once
  survived a bad import only because their titles broke YAML parsing and left them
  without a `tags` key at all.

**Run `./check-front-matter.sh` before committing a page and at every release.**
It checks each rule above (a `description` over 255 characters, `tags` that is
not a quoted string, `published:` in place of `isPublished`, a missing key) and
exits non-zero with one `path: what is wrong` line per failure, so a page that
Wiki.js would silently drop fails here instead.

Tag vocabulary, so the tag browser stays useful: one chapter tag per page
(`overview`, `getting-started`, `language`, `stdlib`, `library`, `example`,
`compiler`, `tooling`, `reference`, `family`, `meta`) plus cross-cutting topics
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

## Syntax highlighting

Kelp fences are highlighted by a Prism grammar that Wiki.js does not ship. Wiki.js
sets `Prism.plugins.autoloader.languages_path = "/_assets/js/prism/"` and calls
`Prism.highlightAllUnder()` after every render, so the grammar belongs at that
path, and the container ships 471 Prism components and none of them is Kelp.

Files written inside the container are lost when it is recreated, so nginx answers
the path from the host instead. Two paths, one file:

| URL | Why |
| --- | --- |
| `/_assets/js/prism/prism-kelp.min.js` | what Prism's autoloader asks for |
| `/_assets/kelp/prism-kelp.js` | what the theme loads, sent `no-store` |

Source: `/var/lib/wikijs/prism/prism-kelp.min.js` on `homelabone`. The nginx
locations are in `/etc/nixos/wikijs.nix`.

The second path is not redundant. Cloudflare cached a 404 for the first one for
four hours while it did not exist, and the tunnel token has no cache-purge
permission, so the theme could not rely on the autoloader recovering. The injected
head waits for Prism to exist, loads the grammar, and highlights once, which also
covers a page that rendered before the grammar arrived.

## Theme

The admin Theme screen covers the built-in options. Beyond it, `injectCSS` and
`injectHead` are the levers, and both live in the `theming` row of the database, so
neither is versioned by this repository. The current injected CSS and head are kept
on disk at `/var/lib/wikijs/theme-inject-css.css` and
`/var/lib/wikijs/theme-inject-head.html`.

### The accent is the seaweed green

Blue is gone: the accent is the green of `seaweed.png`, the site logo. The three
tones of that file are `#79d16d` light, `#64b659` mid and `#529c4e` dark. Surfaces
and text take the dark tone, because white navigation labels on the mid tone fall
to 2.3:1 contrast, and hover and focus states take the mid tone. Inline code in
prose keeps the Wiki.js indigo, so that code stays distinct from links.

The accent cannot be set from the admin Theme screen. Wiki.js builds Vuetify with
`new Vuetify({ rtl, theme: { dark } })`, so the palette stays at the factory
values, and the light primary is the Vuetify blue `#1976D2`. The theme's own
`accentColor` property (`blue darken-2` in `themes/default/theme.yml`) is not read
by the compiled theme either: `theme0.js` names `blue` directly. Both are
overridden in `injectCSS`, which restyles the theme classes `.primary` and
`.primary--text`, the two link rules in `app.css`, and the pieces of theme chrome
that name a blue palette directly (`.blue`, `.blue-grey`, `.indigo`, the admin
`.dialog-header` gradient and the form focus ring).

Every selector starts with `html body`. Wiki.js injects this CSS into the head
before Vuetify appends its runtime `<style id="vuetify-theme-stylesheet">`, and
that stylesheet sets `.primary` with `!important`: the extra element selector makes
the override win on specificity instead of on order, which no amount of ordering
would do.

The injected head carries two scripts: the Kelp Prism grammar loader described
above, and a few lines that repaint the browser-chrome metas. `views/master.pug`
hardcodes `#1976d2` in `theme-color` and `msapplication-TileColor`, and the
container image is not ours to edit.

### Changing it

Edit the row, then restart: Wiki.js reads the settings once per process, so a
write to the database alone changes nothing.

```sh
scp theming.json theme-inject-css.css thinkbox:/tmp/ \
  && ssh thinkbox "sudo install -o root -g root -m 644 /tmp/theme-inject-css.css /var/lib/wikijs/theme-inject-css.css \
  && sudo install -o root -g root -m 644 /tmp/theming.json /var/lib/wikijs/theming.json \
  && sudo -u postgres psql -d wikijs -c \"update settings set value = (select pg_read_file('/var/lib/wikijs/theming.json'))::json where key='theming'\" \
  && sudo systemctl restart podman-wikijs"
```

The file read back by `pg_read_file` has to live under `/var/lib/wikijs`: the
PostgreSQL unit runs with a private `/tmp`, so a file copied to `/tmp` is not the
file the database sees, and the update fails with `No such file or directory`.

The row as it stood before the green, head script included, is kept at
`/var/lib/wikijs/theming-backup.json`.

## History

`main` was the MkDocs Material source until 2026-09-19: `docs/`, `mkdocs.yml`,
`hooks/` and `tools/`, served at `homelabone.xenoo.dev/kelp/`. That layout is
kept at branch `mkdocs-archive` and tag `mkdocs-final`.

Kelp syntax highlighting was lost in the move. The MkDocs build registered a
custom `kelp` fence language in `hooks/kelp_lexer.py`; Wiki.js has no such
grammar and renders Kelp blocks unhighlighted.
