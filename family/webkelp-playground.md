---
title: "WebKelp playground"
description: "An in-browser editor for WebKelp: write source on the left, see the compiled page on the right. The page is written in WebKelp and the compile backend is a Kelp HTTP server; this page covers the API, the limits and the security model."
isPublished: true
tags: "family, networking"
---

> # ARCHIVED PROJECT: WEBKELP MOVED TO POLYP
>
> WebKelp now lives in the Polyp repository, in the `web/` folder:
> https://homelabone.xenoo.dev/gittea/Juniper/polyp
>
> The WebKelp repository is archived, and its demo and playground sites have been removed.
> This page is kept for reference only and may be out of date.
The playground is at [**homelabone.xenoo.dev/webkelpplay**](https://homelabone.xenoo.dev/webkelpplay/).
Type WebKelp on the left and the page it compiles to appears on the right, with no login.
It is built the way the rest of the [Kelp family](/family) is: the page is written in
[WebKelp](/family/webkelp), and the backend is a Kelp program.

## What it does

- **Live preview.** The source is compiled about 250 ms after you stop typing, and the result is
  shown in an iframe. A second tab shows the generated HTML.
- **Examples.** A menu loads a hello page, a button, cards, raw HTML, and page settings.
- **Share.** *Copy link* puts the source in the URL fragment (`#…`), so a link reproduces your page and
  nothing is stored on the server.
- **Download.** *Download .html* saves the compiled page. The CSS is inlined, so it is one file.

## Architecture

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

## The API

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

## Limits and security

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

## Running it locally

```sh
./playground/build.sh                 # builds dist/index.html, dist/index.css, dist/webkelp-server
./playground/dist/webkelp-server 8094 &
```

The page posts to a relative `api/compile`, so for a local run serve `dist/` with anything that also
forwards `/api/` to port 8094. `kelpc` needs `cc` on `PATH` (see [WebKelp](/family/webkelp#build-it)).

## See also

- [WebKelp](/family/webkelp) and the [syntax reference](/family/webkelp-syntax)
- [How WebKelp is built](/family/webkelp-internals)
- [`std/net`](/stdlib/net) and [Capabilities](/language/capabilities)
