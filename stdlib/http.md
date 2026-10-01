---
title: "`std/http`"
description: "An HTTP/1.1 client, http and https both. Ungated itself, but it holds net - importing it requires delegating net on the impl line, and the grant the consumer writes is what governs every connection it makes."
isPublished: true
tags: "stdlib, networking"
---
An HTTP/1.1 client, **`http` and `https` both**. Ungated itself, but it **holds
`net`**: importing it requires delegating `net` on the `impl` line, and the
grant the consumer writes is what governs every connection it makes.

```kelp
impl "std/http" caps(net = ["api.example.com:443"])
```

Naming `net.connect` needs the `net` domain, so a project that imports this module
without delegating gets a compile error naming the module: not a client that
fails at runtime. `https://` needs nothing extra: the same grant covers it,
because [`std/tls`](/stdlib/tls) never dials a socket itself, only wraps one
this module already opened.

## Types

```kelp
datac Url(val scheme: String, val host: String, val port: u16, val path: String)
datac Header(val name: String, val value: String)
datac Response(val status: i32, val headers: List<Header>, val body: Bytes, val reusable: bool)
datac RateLimit(
    val limit: Option<u64>,
    val remaining: Option<u64>,
    val reset: Option<f64>,
    val reset_after: Option<f64>,
    val bucket: Option<String>,
)
datac Request(val method: String, val url: String, val headers: List<Header>, val body: Bytes)
datac Client(val timeout_ms: u64, val max_redirects: i32, val follow_redirects: bool)
datac Pool(val host: String, val port: u16, val size: usize, val timeout_ms: u64, var idle: List<Conn>)
datac Lease(val fd: i32, val tls_handle: usize, val reused: bool)
datac Conn(val fd: i32, val tls_handle: usize)
```

`Conn` is one open connection, plain or TLS, and replaces the bare `net.Socket`
everywhere in this module: the dial, the pool, redirect-following and the
framing reader dispatch on it without needing to know which kind they were
handed. `tls_handle` is `0` for a plain connection (never a real handshake
result).

Constants: `DEFAULT_PORT` (`80`), `DEFAULT_HTTPS_PORT` (`443`),
`DEFAULT_TIMEOUT_MS` (`30000`), `DEFAULT_MAX_REDIRECTS` (`5`), and `pool_size`:
spliced in by the compiler from the project's `http_pool` setting in
`coral.toml` (default 4, `0` disables pooling).

## Requests

| Function | Returns | Notes |
| --- | --- | --- |
| `parse_url(s)` | `Url` | accepts both `http://` and `https://`; the latter defaults to port 443 |
| `default_client()` | `Client` | 30 s timeout, 5 redirects, following them |
| `Client.send(req)` | `Response` | the whole exchange, scheme decides plain or TLS |
| `empty_headers()` | `List<Header>` | |
| `Response.is_ok()` | `bool` | status in `200..299` |
| `Response.text()` | `String` | the body as text |
| `Response.has_header(name)` / `Response.header(name)` | `bool` / `String` | |
| `Response.retry_after()` | `Option<u64>` | the `Retry-After` header, seconds form only (see below) |
| `Response.rate_limit()` | `RateLimit` | the `X-RateLimit-*` bucket headers, each field `Option` |
| `send_fresh(...)`, `exchange(...)`, `one_exchange(...)` | `Response` | the lower-level steps, if you need them |

Response header lookup is case-insensitive (`name_eq`). The body framing handles
**all four** cases: `Content-Length`, `Transfer-Encoding: chunked`, a bodyless
response, and the read-to-end-of-file fallback: the last is the only one that
costs a connection. A redirect that changes host or port re-resolves the scheme
from the `Location` header, so a plain-to-TLS (or TLS-to-plain) hop across a
redirect is not stuck on the original connection's kind.

### Failure is a value

Every request call has a fallible twin returning `Result<_, HttpErr>`. The
variants split on the one question a retry needs answered: **could the server
have seen the request?**

```kelp
enum HttpErr {
    Dial(val reason: String)       // nothing was sent: the name did not resolve,
                                   // the connection was refused, or (for https)
                                   // the TLS handshake failed. Retrying any
                                   // method is safe
    Exchange(val reason: String)   // the connection was open: a send failed, the
                                   // peer reset or closed before the response was
                                   // complete, a read timed out, or the response
                                   // was malformed
    Redirects(val reason: String)  // the chain was longer than the client allows;
                                   // the requests before it did complete
}
```

| Fallible | Panicking | Returns |
| --- | --- | --- |
| `try_get(url)` | `get(url)` | `Result<Response, HttpErr>` / `Response` |
| `Client.try_send(req)` | `Client.send(req)` | as above |
| `Pool.try_send(req)` | `Pool.send(req)` | as above, over a pooled connection |
| `Pool.try_checkout(use_tls)` | `Pool.checkout(use_tls)` | `Result<Lease, HttpErr>` / `Lease` |
| `conn_send_all_try` / `conn_recv_try` / `conn_recv_into_try` | the plain trio | `Result<_, HttpErr>` |
| `send_fresh_try`, `exchange_try`, `one_exchange_try`, `read_response_try`, `follow_url_try`, `content_length_try`, `parse_status_line_try`, `status_code_try` | the plain forms | `Result<_, HttpErr>` |

Every `reason` is the text the panicking form panics with, so a caller that
logs it prints what `send` would have printed on stderr. The panicking wrappers
are thin: `get` is `default_client().send(make_get(url))`, and `send` is
`when self.try_send(req) { Ok(r) -> r, Err(e) -> fail_http(e) }`.

A refused dial is a `Dial` error, not the end of the process:

```kelp
impl "std/http" caps(net = ["127.0.0.1:1"])

fun main() {
    when http.try_get("http://127.0.0.1:1/") {
        Ok(r) -> print(r.status)
        Err(e) -> when e {
            Dial(reason) -> {
                print("dial failed")
                print(reason)
            }
            Exchange(reason) -> {
                print("exchange failed")
                print(reason)
            }
            Redirects(reason) -> {
                print("too many redirects")
                print(reason)
            }
        }
    }
}
```

```text
dial failed
net.connect: connection failed
  errno 111: Connection refused
```

### Rate limits

`Response.retry_after()` parses the `Retry-After` header's **seconds form**
only (`Retry-After: 2`); the rarer HTTP-date form reads as `None` rather than
being parsed, because turning a date into a delay needs a clock, and giving
every `std/http` program a second capability (`time`) just for the rare 429
case was rejected as too costly for what it buys. `Response.rate_limit()`
reads `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`,
`X-RateLimit-Reset-After` and `X-RateLimit-Bucket` into a `RateLimit`, each
field `None` when the server didn't send that header. Neither method sleeps
or retries: the client hands the caller the parsed values and leaves the
policy (back off, queue, fail) to them.

```kelp
val resp = client.send(req)
if resp.status == 429 {
    when resp.retry_after() {
        is Some(secs) -> print("retry after " + secs.to_str() + "s")
        is None -> print("no Retry-After header")
    }
}
```

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
| `Pool.warm(use_tls: bool)` | `Unit` (`mut`) |
| `Pool.checkout(use_tls: bool)` | `Lease` (`mut`) |
| `Pool.release(lease, reusable: bool)` | `Unit` (`mut`) |
| `Pool.size()` / `Pool.len()` | `usize`: the keep count, and how many are idle |
| `Lease.conn()` | `Conn` |

`warm`/`checkout` take `use_tls` because a pool is keyed on `host:port` alone,
and the same address could in principle be dialed either way; the caller (which
already knows the URL's scheme) says which.

A `Lease` is a **ticket, not an owner**: the pool holds every descriptor, a lease
is permission to use one for one exchange, and `release` consumes it. Since a
`datac` is never `Copy`, releasing twice or using a lease after release is a
compile error: the ownership check is free.

## Example

```kelp
impl "std/http" caps(net = ["127.0.0.1:*", "api.example.com:443"])
impl "std/str"

fun main() {
    val client = http.default_client()
    val req = http.Request(
        method = "GET",
        url = "https://api.example.com/",
        headers = http.empty_headers(),
        body = Bytes.empty(),
    )
    val resp = client.send(req)
    print(resp.status)
    print(resp.is_ok())
    print(resp.text())
}
```

`send` panics when the connection or the TLS handshake fails; a mismatched or
self-signed certificate is a handshake failure too, since [`std/tls`](/stdlib/tls)
verifies unconditionally.

## Notes

- **Not here, deliberately:** gzip, HTTP/2, cookies, proxies,
  `Expect: 100-continue`, and idle reaping.
- **`https` works** (MK5-S4b-M1): TLS is [`std/tls`](/stdlib/tls), gated under
  the same `net` domain this module already holds, no new capability needed.
  Because this module imports `std/tls`, a program that reaches `std/http`
  links the system OpenSSL (`-lssl -lcrypto`) and needs its headers to build;
  a program that never touches TLS does not. See
  [`std/tls`](/stdlib/tls#linking).
- Redirects: `max_redirects` and `follow_redirects` on the `Client`. A 307/308
  keeps the body; other redirects drop it. A redirect can cross schemes.
- Only `GET` and text-body `POST` ship as helpers. `PUT`, `DELETE` and `PATCH`
  are built by [`httpx`](/libraries/httpx), which also has the query-string
  builder, Basic Auth and `Set-Cookie` parsing.
- Header lists are `List<Header>`: there are no maps here, because insertion order
  and repeats both matter to HTTP.

## See also

- [`std/tls`](/stdlib/tls)
- [`httpx`](/libraries/httpx)
- [`std/net`](/stdlib/net)
- [Capability patterns](/reference/capability-patterns)
