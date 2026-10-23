---
title: "WebKelp"
description: "WebKelp is a markdown-style language that compiles to plain HTML and CSS. A file of ordinary Markdown becomes a styled page, and raw HTML, attributes on anything and any CSS are always available. The compiler is written in Kelp."
isPublished: true
tags: "family, cli"
---

> # ARCHIVED PROJECT: WEBKELP MOVED TO POLYP
>
> WebKelp now lives in the Polyp repository, in the `web/` folder:
> https://homelabone.xenoo.dev/gittea/Lilly/polyp
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

The playground has been removed from the server. It was an in-browser editor: type WebKelp on
the left and the page it compiles to appears on the right, with no login. This section describes
how it worked.

It is built the way the rest of the [Kelp family](/family) is: the page is written in
[WebKelp](/family/webkelp), and the backend is a Kelp program.

### What it does

- **Live preview.** The source is compiled about 250 ms after you stop typing, and the result is
  shown in an iframe. A second tab shows the generated HTML.
- **Examples.** A menu loads a hello page, a button, cards, raw HTML, and page settings.
- **Share.** *Copy link* puts the source in the URL fragment (`#…`), so a link reproduces your page and
  nothing is stored on the server.
- **Download.** *Download .html* saves the compiled page. The CSS is inlined, so it is one file.

### Architecture

```
browser                          nginx                       webkelp-server (Kelp)
-------                          -----                       ---------------------
index.html (a .wk page)   --->   /webkelpplay/       static files
fetch POST  api/compile   --->   /webkelpplay/api/   proxy -> 127.0.0.1:8094 /compile
                                                             page.compile(source, inline css)
iframe.srcdoc = response  <---                       <---    text/plain (the HTML)
```

| Piece | Where | Notes |
| --- | --- | --- |
| The page | `playground/index.wk` | compiled by WebKelp itself; its editor script is a `::: script` block |
| The backend | `src/server.kp` | a small HTTP/1.1 server on `std/net`; calls the same `page.compile` as the CLI |
| The service | `webkelp-playground.service` | listens on `127.0.0.1:8094`; binary in `/var/lib/webkelpplay/` |
| The route | nginx `/webkelpplay/` | static page, and `/webkelpplay/api/` proxied to the service |

Kelp's `std/http` is a client only, so the server is written directly on `std/net`: `net.listen`,
`net.accept`, `net.recv` and `net.send_all`. It handles one request per connection, one connection at
a time. The compiler is fast enough (a few milliseconds for a normal page) that this is plenty.

### The API

`POST /compile`

| | |
| --- | --- |
| Request body | WebKelp source, UTF-8 text |
| Response | `200`, `text/plain`: a complete HTML document with its CSS inlined |
| Errors | `400` bad request or invalid UTF-8 or a NUL byte, `405` wrong method, `413` body over 32 KB |

`GET /health` answers `ok`. Everything else is `404`.

```sh
printf '# Hi\n\n[go](x.wk){.btn}\n' | curl -s --data-binary @- https://homelabone.xenoo.dev/webkelpplay/api/compile
```

### Limits and security

The endpoint is public and compiles text from strangers, so each layer bounds what a request can cost
or reach.

| Layer | Bound |
| --- | --- |
| nginx | 5 requests per second per client (burst 10), body capped at 40 KB, 15 s timeouts |
| server | body capped at 32 KB, headers at 8 KB, 4 s wait for the client; input must be valid UTF-8 with no NUL bytes |
| compiler | nesting depth is capped (24 block levels, 12 inline levels) and inline constructs look ahead at most 4,000 bytes, so hostile input like 30,000 nested `>` or unclosed `[` finishes in well under a second |
| response | `Content-Type: text/plain`, `X-Content-Type-Options: nosniff` and `Content-Security-Policy: sandbox`, so opening the endpoint directly can never run the compiled page as a document on the site |
| iframe | `sandbox="allow-scripts"` without `allow-same-origin`: the compiled page can run its own JavaScript, but has an opaque origin and cannot read the playground's or the site's storage or cookies |
| service | systemd `DynamicUser`, `ProtectSystem=strict`, no capabilities, `IPAddressDeny=any` except localhost, 256 MB memory limit, 50% CPU quota, `Restart=always` |

The service also restarts by itself if it ever crashes, so a bug is a brief blip rather than an outage.

### Running it locally

```sh
./playground/build.sh                 # builds dist/index.html, dist/index.css, dist/webkelp-server
./playground/dist/webkelp-server 8094 &
```

The page posts to a relative `api/compile`, so for a local run serve `dist/` with anything that also
forwards `/api/` to port 8094. `kelpc` needs `ld.lld` on `PATH` (see [Build it](#build-it)).

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
git clone http://localhost:8085/Lilly/webkelp.git
cd webkelp
kelpc build . -o webkelp
tests/run.sh          # golden tests; set WEBKELP=./webkelp
```

`kelpc` needs `ld.lld` and the OpenSSL libraries for a program that reaches `std/tls`. On NixOS:

```sh
nix-shell -p lld openssl --run 'kelpc build . -o webkelp'
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
