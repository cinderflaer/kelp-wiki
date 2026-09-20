---
title: "`std/http`"
description: "An HTTP/1.1 client. Ungated itself, but it holds net - importing it requires delegating net on the impl line, and the grant the consumer writes is what governs every connection it makes."
isPublished: true
tags: "stdlib, networking"
---
An HTTP/1.1 client. Ungated itself, but it **holds `net`**: importing it requires
delegating `net` on the `impl` line, and the grant the consumer writes is what
governs every connection it makes.

```kelp
impl "std/http" caps(net = ["api.example.com:443"])
```

Naming `net.connect` needs the `net` domain, so a project that imports this module
without delegating gets a compile error naming the module: not a client that
fails at runtime.

## Types

```kelp
datac Url(val scheme: String, val host: String, val port: u16, val path: String)
datac Header(val name: String, val value: String)
datac Response(val status: i32, val headers: List<Header>, val body: Bytes, val reusable: bool)
datac Request(val method: String, val url: String, val headers: List<Header>, val body: Bytes)
datac Client(val timeout_ms: u64, val max_redirects: i32, val follow_redirects: bool)
datac Pool(val host: String, val port: u16, val size: usize, val timeout_ms: u64, var idle: List<i32>)
datac Lease(val fd: i32, val reused: bool)
```

Constants: `DEFAULT_SCHEME` (`http`), `DEFAULT_PORT` (`80`), `DEFAULT_TIMEOUT_MS`
(`30000`), `DEFAULT_MAX_REDIRECTS` (`5`), and `pool_size`: spliced in by the
compiler from the project's `http_pool` setting in `coral.toml` (default 4, `0`
disables pooling).

## Requests

| Function | Returns | Notes |
| --- | --- | --- |
| `parse_url(s)` | `Url` | refuses `https` by name |
| `default_client()` | `Client` | 30 s timeout, 5 redirects, following them |
| `Client.send(req)` | `Response` | the whole exchange |
| `empty_headers()` | `List<Header>` | |
| `Response.is_ok()` | `bool` | status in `200..299` |
| `Response.text()` | `String` | the body as text |
| `Response.has_header(name)` / `Response.header(name)` | `bool` / `String` | |
| `send_fresh(...)`, `exchange(...)`, `one_exchange(...)` | `Response` | the lower-level steps, if you need them |

Response header lookup is case-insensitive (`name_eq`). The body framing handles
**all four** cases: `Content-Length`, `Transfer-Encoding: chunked`, a bodyless
response, and the read-to-end-of-file fallback: the last is the only one that
costs a connection.

## Keep-alive and the pool

HTTP/1.1 is persistent by default, so the client does not send
`Connection: close`; a connection goes back into the pool when the body was
completely framed and the server did not ask to close.

The pool is keyed on the host **as written**: never on a resolved address,
because the capability check matches the string the author wrote. `size` is the
number of idle connections to *keep*, not a hard cap: a request that arrives while
every kept connection is busy gets a fresh one, so a program never fails because
its pool was small.

| Function | Returns |
| --- | --- |
| `pool(host, port)` | `Pool` |
| `Pool.warm()` | `Unit` (`mut`) |
| `Pool.checkout()` | `Lease` (`mut`) |
| `Pool.release(lease, reusable: bool)` | `Unit` (`mut`) |
| `Pool.size()` / `Pool.len()` | `usize`: the keep count, and how many are idle |
| `Lease.socket()` | `net.Socket` |

A `Lease` is a **ticket, not an owner**: the pool holds every descriptor, a lease
is permission to use one for one exchange, and `release` consumes it. Since a
`datac` is never `Copy`, releasing twice or using a lease after release is a
compile error: the ownership check is free.

## Example

```kelp
impl "std/http" caps(net = ["127.0.0.1:*"])
impl "std/str"

fun main() {
    val client = http.default_client()
    val req = http.Request(
        method = "GET",
        url = "http://127.0.0.1:8000/",
        headers = http.empty_headers(),
        body = Bytes.empty(),
    )
    val resp = client.send(req)
    print(resp.status)
    print(resp.is_ok())
    print(resp.text())
}
```

Start a server first (`python3 -m http.server 8000`, or the same program with
`net.listen`), because `send` panics when the connection fails.

## Notes

- **Not here, deliberately:** gzip, HTTP/2, cookies, proxies,
  `Expect: 100-continue`, idle reaping, and `https`: TLS is a later milestone,
  and `parse_url` refuses it by name rather than pretending.
- Redirects: `max_redirects` and `follow_redirects` on the `Client`. A 307/308
  keeps the body; other redirects drop it.
- Only `GET` and text-body `POST` ship as helpers. `PUT`, `DELETE` and `PATCH`
  are built by [`httpx`](/libraries/httpx), which also has the query-string
  builder, Basic Auth and `Set-Cookie` parsing.
- Header lists are `List<Header>`: there are no maps here, because insertion order
  and repeats both matter to HTTP.

## See also

- [`httpx`](/libraries/httpx)
- [`std/net`](/stdlib/net)
- [Capability patterns](/reference/capability-patterns)
