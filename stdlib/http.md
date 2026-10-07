---
title: "`std/http`"
description: "An HTTP/1.1 client and server. The client speaks http and https; the server has request limits, keep-alive, chunked and Expect: 100-continue bodies, and worker threads. Holds net, so importing it needs net delegated."
isPublished: true
tags: "stdlib, networking"
---
An HTTP/1.1 **client and server**. The client speaks `http` and `https`; the
server speaks plain HTTP/1.1 over TCP. Ungated itself, but it **holds `net`**:
importing it requires delegating `net` on the `impl` line, and the grant the
consumer writes is what governs every connection the client makes and every
port the server binds.

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
| `Client.send(req)` | `Response` | the whole exchange, scheme decides plain or TLS; panics on any failure |
| `Client.try_send(req)` | `Result<Response, HttpErr>` | `send` with the failures as a value (see below) |
| `try_get(url)` | `Result<Response, HttpErr>` | `get` with the failures as a value |
| `Pool.try_send(req)` / `Pool.try_checkout(use_tls)` | `Result<Response, HttpErr>` / `Result<Lease, HttpErr>` | the pooled forms of the same |
| `empty_headers()` | `List<Header>` | |
| `Response.is_ok()` | `bool` | status in `200..299` |
| `Response.text()` | `String` | the body as text |
| `Response.has_header(name)` / `Response.header(name)` | `bool` / `String` | |
| `Response.retry_after()` | `Option<u64>` | the `Retry-After` header, seconds form only (see below) |
| `Response.rate_limit()` | `RateLimit` | the `X-RateLimit-*` bucket headers, each field `Option` |
| `send_fresh(...)`, `exchange(...)`, `one_exchange(...)` | `Response` | the lower-level steps, if you need them; each has a `_try` twin returning `Result<Response, HttpErr>` |

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
already knows the URL's scheme) says which. `checkout` only reuses an idle
connection of the scheme asked for: a kept connection of the other scheme is
closed and replaced by a fresh one, so an `https` request is never sent over a
plain connection or the reverse.

A `Lease` is a **ticket, not an owner**: the pool holds every descriptor, a lease
is permission to use one for one exchange, and `release` consumes it. Since a
`datac` is never `Copy`, releasing twice or using a lease after release is a
compile error: the ownership check is free.

## Multipart bodies

An attachment upload is a `multipart/form-data` body. `http.multipart(boundary)`
starts one; the boundary is yours (1 to 70 bytes from the RFC 2046 set, and long
enough that it never occurs in a part), because the module has no randomness and
a test wants a stable body. It panics on a bad boundary.

```kelp
var form = http.multipart("kelp-7f3a91c2d4e5")
form.add_field("content", "build finished")
form.add_file("file", "report.txt", "text/plain", Bytes.from_str("ok"))
val req = http.multipart_request("https://api.example.com/upload", &mut form)
```

| Function | What it does |
|---|---|
| `add_field(name, value)` | a text part |
| `add_file(name, filename, content_type, data)` | a file part |
| `content_type()` | `multipart/form-data; boundary=...`, the header to send |
| `finish()` | closes the body and returns the bytes; call it once, last |
| `multipart_request(url, form)` | a `POST` `Request` with the header and the finished body |

A `"` in a name or file name is written `%22`, CR `%0D`, LF `%0A` and `%` `%25`, as
browsers do, so a name cannot end its parameter or add a header line.

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

## The server

The same module serves HTTP/1.1, with no extra capability: it is pure Kelp over
[`std/net`](/stdlib/net). `listen`, `accept` and the connection calls are gated
exactly as `net.listen` is, checked against the **port** of the importing
module's `net` grant (`caps(net = ["127.0.0.1:8080"])` or `"127.0.0.1:*"`).
**The grant's host decides which interface the server binds:** `http.listen` goes
through `net.listen`, so under `caps(net = ["127.0.0.1:*"])` it binds `127.0.0.1`
only, and a grant that includes `*` (or any pattern matching `0.0.0.0`) binds
every interface. A server that must be reachable from the network needs a grant
that says so. See the [threat model](/reference/capability-threat-model).

### Types

```kelp
datac Limits(
    val max_request_line: usize,
    val max_header_bytes: usize,
    val max_headers: usize,
    val max_body: usize,
    val head_timeout_ms: u64,
    val body_timeout_ms: u64,
    val idle_timeout_ms: u64,
    val max_requests_per_conn: usize,
)
datac ServerRequest(val method: String, val target: String, val path: String, val query: String,
                    val headers: List<Header>, val body: Bytes)
datac ServerResponse(val status: i32, val headers: List<Header>, val body: Bytes)
datac Server(val fd: i32)
datac ServerConn(val fd: i32, var buf: Bytes, var start: usize, var served: usize,
                 var close_after: bool, var head_only: bool, var keep_alive_header: bool)
```

`path` and `query` are the halves of `target` around the first `?`, still
percent-encoded. `ServerRequest.header`/`has_header` ignore case;
`query_param(name)` decodes form data (`+` is a space, `%XX` is a byte) and
returns `Option<String>`; `path_segments()` returns the non-empty `/`-separated
pieces, each decoded; `text()` panics on invalid UTF-8.

### The request surface

| Function | Returns | Notes |
| --- | --- | --- |
| `ServerRequest.header(name)` / `has_header(name)` | `String` / `bool` | case-insensitive, `""` when absent |
| `ServerRequest.query_param(name)` | `Option<String>` | form-decoded; `?a` is `Some("")` |
| `ServerRequest.path_segments()` | `List<String>` | `/users/42/` is `["users", "42"]` |
| `ServerRequest.text()` | `String` | panics on invalid UTF-8 |
| `ok_text(&str)` / `json(&str)` / `html(&str)` | `ServerResponse` | `200` with the matching `Content-Type` |
| `status(code)` / `not_found()` / `bad_request(&str)` | `ServerResponse` | status, `404`, `400` |
| `ServerResponse.with_header(name, value)` | `ServerResponse` | a copy with one more header |
| `ServerResponse.add_header(name, value)` | `Unit` (`mut`) | grows the response in place |

`Content-Length` is added automatically (not for `1xx`, `204` or `304`). A
handler's own `Content-Length`, `Transfer-Encoding` and `Connection` headers are
dropped, and a header whose name is not a token or whose value holds `CR`, `LF`
or `NUL` is dropped, so a handler cannot split the response. A `HEAD` request
answers with the headers and the `Content-Length` of the body it does not send.
Every body goes out with its head in one `send`.

### Limits

`default_limits()` is the table below. `Limits.with_timeouts(head, body,
idle)` returns a copy with other timeouts, and `Limits.dup()` copies one.
Every violation is answered with its status and a closed connection.

| Limit | Default | Violation |
| --- | --- | --- |
| request line | 8 KiB | `414` |
| header bytes after the request line | 16 KiB | `431` |
| header count | 100 | `431` |
| body (`Content-Length`, or the sum of chunks) | 1 MiB | `413`, before the body is read |
| head deadline | 10 s | `408` |
| body deadline | 30 s | `408` |
| keep-alive idle | 5 s | the connection closes with no answer |
| requests per connection | 100 | the 100th answer says `Connection: close` |

Other answers: `400` for a malformed request line, method, target, header,
chunk or framing; `411` for a `POST`, `PUT` or `PATCH` with neither
`Content-Length` nor chunking; `417` for an `Expect` other than
`100-continue`; `501` for an unknown transfer coding; `505` for a well-formed
`HTTP/d.d` other than `1.0` and `1.1` (a malformed version is `400`).
`Expect: 100-continue` on a body-carrying HTTP/1.1 request is answered with
`100 Continue` before the body is read. A request with both `Content-Length`
and `Transfer-Encoding`, two `Transfer-Encoding` headers, or two disagreeing
`Content-Length` headers is `400` (the request-smuggling guard). Folded header
lines are `400`. Pipelined requests are answered in order.

The timeouts are **deadlines, not per-read waits**: the head deadline runs from
the first byte of the request, so a client that trickles one byte at a time is
cut off when it passes. Waiting for the first byte is the idle wait
(`idle_timeout_ms` once the connection has served something, `head_timeout_ms`
on a fresh one); a fresh connection that sends nothing gets a `408`, an idle
keep-alive connection is closed silently. `HTTP/1.0` closes unless
`Connection: keep-alive` (the answer then says so); `Connection: close` (any
token of any `Connection` header) closes.

### Low level

| Function | Returns | Notes |
| --- | --- | --- |
| `listen(port)` | `Server` | port `0` asks the kernel for a free one |
| `Server.port()` | `u16` | the bound port |
| `Server.set_accept_timeout(ms)` | `Unit` | `0` waits forever |
| `Server.accept()` / `Server.try_accept()` | `ServerConn` / `Result<ServerConn, HttpErr>` | |
| `Server.close()` | `Unit` | |
| `ServerConn.read_request(&Limits)` | `Result<ServerRequest, HttpErr>` | |
| `ServerConn.write_response(&ServerResponse)` | `Result<usize, HttpErr>` | a gone peer is `Err`, never a panic |
| `ServerConn.write_error(&HttpErr)` | `Result<usize, HttpErr>` | answers a failed read |
| `ServerConn.mark_close()` / `wants_close()` | `Unit` / `bool` | |
| `ServerConn.close()` | `Unit` | half-close, drain briefly, then close |
| `http_error_status(&HttpErr)` | `i32` | the status of a failed read, or `0` |

The status of a failed read travels inside `HttpErr.Exchange.reason`, starting
with the code and a space (`408 the request did not arrive in time`); a reason
with no leading code (the peer reset, closed between requests, or sat idle) has
status `0` and is answered with nothing. A request counts once the server has
produced a response for it: a handler that ran, or an error response written. A
connection that closes with nothing, or mid-body, counts for nothing. Closing is
gentle: `shutdown(SHUT_WR)`, then whatever the peer still sends is read and
discarded for at most 250 ms and 1 MiB, then `close`.

### Serving

| Function | Notes |
| --- | --- |
| `serve(port, handler)` | forever, one connection at a time |
| `serve_n(port, handler, max_requests)` | returns `u64` after `max_requests` answered, listener closed |
| `serve_on(&Server, handler, &Limits, max_requests)` | the same on a listener you hold |
| `serve_threaded(port, handler, workers)` | forever, `workers` threads on one listener |
| `serve_threaded_on(&Server, handler, &Limits, workers, idle_ms)` | returns `u64`; each worker stops after `idle_ms` with no client (`0` never stops) |
| `default_limits()` / `Limits.with_timeouts(head, body, idle)` / `Limits.dup()` | |

`handler` is a plain `fun(&ServerRequest).R: ServerResponse` function value, so
nothing borrowed crosses a thread. `serve_on` and `serve_threaded_on` exist
because `serve_n(port, ...)` cannot tell a program which port the kernel gave
for port `0`: bind first, print `Server.port()`, then serve. A panic in a
handler ends the process under `serve`/`serve_n` and one worker thread under
`serve_threaded*`.

### Example

```kelp
impl "std/http" caps(net = ["127.0.0.1:*"])
impl "std/net"
impl "std/thread"
impl "std/str"

fun handle(req: &http.ServerRequest).R: http.ServerResponse {
    if str.eq(req.path.as_str(), "/ping") {
        return http.ok_text("pong\n")
    }
    return http.not_found()
}

fun client(port: u16).R: String {
    var out = String.empty()

    val a = net.connect("127.0.0.1", port)
    net.send_text(a, "GET /ping HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
    val ok = net.recv(a, 4096)
    out.push_str(ok.as_str())
    net.close(a)

    // A request line over the 8 KiB limit is answered 414 and closed.
    var over = String.with_capacity(8300)
    over.push_str("GET /")
    var i: usize = 0
    while i < 8200 {
        over.push('x')
        i += 1
    }
    over.push_str(" HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
    val b = net.connect("127.0.0.1", port)
    net.send_text(b, over.as_str())
    val bad = net.recv(b, 4096)
    out.push_str(bad.as_str())
    net.close(b)

    return out
}

fun main() {
    val server = http.listen(0)
    val port = server.port()
    val t = thread.spawn(client, port)

    val limits = http.default_limits()
    val answered = http.serve_on(&server, handle, &limits, 2)
    server.close()

    when thread.join(t) {
        Ok(text) -> print(text.as_str())
        Err(_) -> print("client failed")
    }
    print("served ${answered} request(s)")
}
```

```text
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
Content-Length: 5
Connection: close

pong
HTTP/1.1 414 URI Too Long
Content-Type: text/plain; charset=utf-8
Content-Length: 29
Connection: close

the request line is too long

served 2 request(s)
```

### Not here

HTTP/2 (an HTTPS server still speaks HTTP/1.1), `Date` and `Server` headers, `Host`
enforcement, absolute-form and `CONNECT` targets, ranges, compression, cookies,
response streaming (bodies are always `Content-Length`-framed, so no chunked
responses), a send deadline (a client that never reads blocks its worker), a
connection limit, and `Expect` on anything but `100-continue`.

### Serving HTTPS

`http.serve_tls(port, config, handler)`, `serve_tls_n(port, config, handler, max_requests)`
and `serve_tls_on(&server, config, handler, &limits, max_requests)` are `serve`,
`serve_n` and `serve_on` with every accepted connection put through
[`tls.accept`](/stdlib/tls#serving-tls) first. `config` is a `tls.ServerConfig`,
shared and never changed, and the limits, status table and per-connection rules
are the plain server's. A client whose handshake fails (no certificate where one
is required, no common protocol, a reset) costs that socket and nothing else: it
is closed and the loop goes on. `serve_tls_n` returns the number of requests
answered. Like `net.listen`, `serve_tls` binds every interface; to bind one host,
listen with `http.listen_on("127.0.0.1", port)` and serve with `serve_tls_on`.

On the client side, `http.try_get_tls(url, &opts)`, `http.get_tls` and
`Client.try_send_tls(req, &opts)` take a `tls.TlsClientOptions` (private CA as
PEM bytes, client certificate, ALPN). The CA bytes come from
`tlsfile.ca_pem(path)`, which needs an `fs` grant; there is no `ca_file` option.

This program serves one HTTPS request on a second thread and fetches it with a
private CA (the certificate files are made as in
[`std/tls`](/stdlib/tls#making-a-test-certificate); `/etc/myapp/certs` was
replaced by a scratch directory for the run):

```kelp
impl "std/http" caps(net = ["*"])
impl "std/tls"
impl "std/tlsfile" caps(fs = ["/etc/myapp/certs/**"])
impl "std/thread"
impl "std/result"
impl "std/fmt"

fun hello(req: &http.ServerRequest).R: http.ServerResponse {
    return http.ok_text("hello over tls")
}

fun serve(fd: i32).R: u64 {
    val cert = tlsfile.read_pem("/etc/myapp/certs/server.pem", "certificate chain")
    val key = tlsfile.read_pem("/etc/myapp/certs/server.key", "private key")
    return when cert {
        Ok(c) -> when key {
            Ok(k) -> serve_with(c, k, fd)
            Err(_) -> 0
        }
        Err(_) -> 0
    }
}

fun serve_with(cert: move Bytes, key: move Bytes, fd: i32).R: u64 {
    return when tls.server_config_pem(cert, key) {
        Ok(cfg) -> {
            val server = http.Server(fd = fd)
            val limits = http.default_limits()
            val n = http.serve_tls_on(&server, cfg, hello, &limits, 1)
            cfg.free()
            n
        }
        Err(e) -> 0
    }
}

fun main() {
    val server = http.listen(0)
    server.set_accept_timeout(10000)
    val port = server.port()
    val h = thread.spawn(serve, server.fd)

    var url = String.from_str("https://localhost:")
    val digits = fmt.uint(port.to_u64())
    url.push_str(digits.as_str())
    url.push_str("/")
    when tlsfile.ca_pem("/etc/myapp/certs/ca.pem") {
        Ok(ca) -> {
            val opts = tls.client_options().with_ca_pem(ca).with_timeout_ms(10000)
            when http.try_get_tls(url.as_str(), &opts) {
                Ok(resp) -> {
                    print(resp.status)
                    print(String.from_bytes(resp.body.clone()))
                }
                Err(e) -> print(http.http_error_text(&e))
            }
        }
        Err(_) -> print("cannot read the CA file")
    }
    when thread.join(h) {
        Ok(n) -> print(n)
        Err(_) -> print("server thread failed")
    }
    server.close()
}
```

Both backends print:

```text
200
hello over tls
1
```

I also ran `http.serve_tls_n(36010, &cfg, handler, 2)` as a stand-alone server
and fetched it with `curl --cacert ca.pem https://localhost:36010/hello`, which
answered `hello over tls`, and a path the handler does not know, which answered
`404`; the server then returned and printed `2`, on both backends.

## Notes

- **Not here, deliberately:** on the client, gzip, HTTP/2, cookies, proxies,
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
