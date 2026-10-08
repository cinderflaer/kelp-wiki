---
title: "WebKelp"
description: "WebKelp is a markdown-style language that compiles to plain HTML and CSS. A file of ordinary Markdown becomes a styled page, and raw HTML, attributes on anything and any CSS are always available. The compiler is written in Kelp."
isPublished: true
tags: "family, cli"
---

> # ARCHIVED PROJECT: WEBKELP MOVED TO POLYP
>
> WebKelp now lives in the Polyp repository, in the `web/` folder:
> https://homelabone.xenoo.dev/gittea/Juniper/polyp
>
> The WebKelp repository is archived, and its demo and playground sites have been removed.
> This page is kept for reference only and may be out of date.
WebKelp is a markdown-style language, in `.wk` files, that compiles to plain **HTML and
CSS**. The compiler is a single native binary written in Kelp, and the output is static
files with no JavaScript unless you write some.

It has two goals that pull in opposite directions, and the design is the answer to both:

- **As easy as possible.** A file that contains only Markdown becomes a good-looking,
  responsive page. There is no configuration.
- **Never limiting.** Anything HTML or CSS can express, WebKelp can express. There is
  always an escape hatch, and it never needs an "unsafe" flag.

## Live demo

The live demo has been removed from the server. Its source is still in the repository:
`demo/index.wk` is a page written entirely in WebKelp, and `demo/build.sh` builds it.

## Playground

The playground has been removed from the server. It was an in-browser editor: write WebKelp on the left and
see the compiled page on the right. See [WebKelp playground](/family/webkelp-playground) for the reference.

## A first page

```markdown
---
title: Hello
---

# Hello, WebKelp

Write **Markdown**, add [links](about.wk), and drop to raw HTML whenever you like.

[Get started](/docs.wk){.btn}

::: style
.btn { letter-spacing: 0.02em }
:::
```

`webkelp build hello.wk` writes `dist/hello.html` and `dist/hello.css`:

```html
<h1 id="hello-webkelp">Hello, WebKelp</h1>
<p>Write <strong>Markdown</strong>, add <a href="about.html">links</a>, and drop to raw HTML whenever you like.</p>
<p><a href="/docs.html" class="btn">Get started</a></p>
```

Three things happened that plain Markdown cannot do: `{.btn}` put a class on the link,
`::: style` was lifted into `hello.css`, and the `.wk` link became `.html`.

## The escape-hatch ladder

Each rung covers what the one above it cannot, so there is always a way out:

| Rung | Syntax | Covers |
| --- | --- | --- |
| Attributes | `{#id .class key=value flag}` | class, id, `data-*`, `aria-*`, `style=`, `onclick=`, `hidden`, any attribute |
| Containers | `::: tag {attrs}` … `:::` | any element, including custom elements, with Markdown inside |
| Raw HTML | write the HTML | everything else; passed through untouched |
| CSS and head | `::: style`, `::: script`, `head:` | anything in the stylesheet or the document head |
| The shell | `html:`, `body:`, `shell: none` | the `<html>` and `<body>` attributes, or no document at all |

## Command line

```sh
webkelp build <file.wk|dir> [-o outdir] [--inline]
webkelp init [dir]
```

| Command | What it does |
| --- | --- |
| `build file.wk` | writes `file.html`, plus `file.css` when the page has any CSS |
| `build dir` | mirrors the tree: each `x.wk` becomes `x.html` (+ `x.css`), every other file is copied as an asset, and links to `x.wk` are rewritten to `x.html` |
| `-o outdir` | where the output goes; default `dist` |
| `--inline` | put the CSS in a `<style>` block instead of a separate file |
| `init [dir]` | write a starter `index.wk`; refuses to overwrite one |

Exit code `0` is success, `1` is a failure (a missing file, an existing `index.wk`), and
`2` is a usage error.

## Build it

```sh
git clone http://localhost:8085/Juniper/webkelp.git
cd webkelp
kelpc build . -o webkelp
tests/run.sh          # golden tests; set WEBKELP=./webkelp
```

`kelpc` finishes a build by calling `cc`, so a C compiler has to be on `PATH`. On NixOS,
where there is none by default:

```sh
nix-shell -p gcc openssl --run 'kelpc build . -o webkelp'
```

## Default theme

Unless a page says `theme: none`, its stylesheet starts with a small classless theme:
readable typography, light and dark modes from `prefers-color-scheme`, and a few helper
classes (`.center`, `.muted`, `.hero`, `.grid`, `.card`, `.btn`). Every colour is a
`--wk-*` custom property, so a page restyles it by overriding variables in a `::: style`
block.

## See also

- [WebKelp syntax reference](/family/webkelp-syntax)
- [How WebKelp is built](/family/webkelp-internals)
- [Kelp family](/family)
