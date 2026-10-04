---
title: "Tutorial 14: Networking, HTTP and TLS"
description: "Chapter 14 of the Kelp tutorial: an HTTP server and client in one process, failures as values, a net grant that refuses an ungranted host, and serving HTTPS with a throwaway CA, all run on loopback ports."
isPublished: true
tags: "tutorial, networking, http, tls"
---
Networking is gated like everything else: `std/http` **holds `net`**, so importing it
means writing the grant on the `impl` line, and that grant governs every connection
the client makes and every port the server binds. The references are
[`std/http`](/stdlib/http), [`std/net`](/stdlib/net) and [`std/tls`](/stdlib/tls).
Every program here ran on `127.0.0.1` only, on ports in the range 36000 to 36099.

## A server and a client in one program

```kelp
impl "std/http" caps(net = ["127.0.0.1:36010"])
impl "std/thread"
impl "std/result"
impl "std/option"
impl "std/str"

fun handle(req: &http.ServerRequest).R: http.ServerResponse {
    if str.eq(req.path.as_str(), "/hello") {
        var name = String.from_str("world")
        if let Some(n) = req.query_param("name") {
            name = n
        }
        val body = str.concat("hello, ", name.as_str())
        return http.ok_text(body.as_str())
    }
    return http.not_found()
}

fun serve(fd: i32).R: u64 {
    val server = http.Server(fd = fd)
    val limits = http.default_limits()
    val n = http.serve_on(&server, handle, &limits, 3)
    server.close()
    return n
}

fun show(url: &str) {
    when http.try_get(url) {
        Ok(r) -> print("${url} -> ${r.status}: ${r.text()}")
        Err(e) -> print("request failed")
    }
}

fun main() {
    val server = http.listen(36010)
    val worker = thread.spawn(serve, server.fd)
    show("http://127.0.0.1:36010/hello")
    show("http://127.0.0.1:36010/hello?name=Kelp")
    show("http://127.0.0.1:36010/missing")
    when thread.join(worker) {
        Ok(n) -> print("server answered ${n} requests")
        Err(e) -> print(e.message)
    }
}
```

```text
http://127.0.0.1:36010/hello -> 200: hello, world
http://127.0.0.1:36010/hello?name=Kelp -> 200: hello, Kelp
http://127.0.0.1:36010/missing -> 404: not found

server answered 3 requests
```

Both backends printed this, including the empty line (the `404` body is
`not found` followed by a newline, and `print` adds another).

The pieces:

- `impl "std/http" caps(net = ["127.0.0.1:36010"])`: this one line is the program's
  whole network authority. The same grant covers the listener and the client.
- `http.listen(36010)` binds first, and `http.Server(fd = ...)` rebuilds a server
  handle in the worker (a handle crosses `thread.spawn` as the plain `fd`). Binding
  before the client starts removes any race over who is ready first. `listen(0)` would
  ask the kernel for a free port, and `server.port()` reports which.
- The handler is a plain function `fun(&ServerRequest).R: ServerResponse`. A
  `ServerRequest` has `method`, `path`, `query`, `headers` and `body`;
  `query_param(name)` returns an `Option<String>` that is form-decoded, and
  `path_segments()` splits the path. `http.ok_text`, `http.json`, `http.html`,
  `http.not_found` and `http.status(code)` build responses, and `Content-Length` is added
  for you.
- `serve_on(&server, handler, &limits, 3)` answers three requests and returns the count.
  `serve` runs forever and `serve_threaded` uses several workers on one listener.
  The default limits (8 KiB request line, 1 MiB body, 10 s head deadline, and more) are in
  the [limits table](/stdlib/http#limits); each violation gets its own status.
- On the client, `http.try_get(url)` returns `Result<Response, HttpErr>`, and
  `Response` has `status`, `headers`, `text()` and `is_ok()`. `http.get` and
  `Client.send` are the panicking forms.

## Failure is a value, a denied grant is a panic

`HttpErr` splits on the one question a retry needs answered: *could the server have
seen the request?* `Dial` means nothing was sent, `Exchange` means the connection
was open, `Redirects` means the chain was too long.

```kelp
impl "std/http" caps(net = ["127.0.0.1:36011"])

fun main() {
    when http.try_get("http://127.0.0.1:36011/") {
        Ok(r) -> print("status ${r.status}")
        Err(e) -> when e {
            Dial(reason) -> print("dial failed: ${reason}")
            Exchange(reason) -> print("exchange failed")
            Redirects(reason) -> print("too many redirects")
        }
    }
    print("now a host that was not granted")
    when http.try_get("http://localhost:36011/") {
        Ok(r) -> print("status ${r.status}")
        Err(e) -> print("an error value")
    }
}
```

```text
$ ./c14b; echo "exit $?"
std/http.kp:332:18: panic: 'localhost:36011' is outside the net capability granted to module 'std/http'
  granted:
    127.0.0.1:36011
dial failed: net.connect: connection failed
  errno 111: Connection refused
now a host that was not granted
exit 1
```

Nothing listened on port 36011, so the first request is a `Dial` error with the
operating system's own words. The second request used `localhost`, which the grant
`127.0.0.1:36011` does **not** cover, because grants match the host string the program
wrote, never the resolved address. That is not an error value: it is a panic, naming the
module and what it was granted (chapter 12). A mistake in the grant is a bug in the
program, not a network condition to retry.

## Serving HTTPS

TLS needs a certificate. These were made with the recipe on the
[`std/tls` page](/stdlib/tls#making-a-test-certificate): a throwaway CA, and a
`localhost` certificate it signed, valid for two days.

```sh
printf 'subjectAltName=DNS:localhost\nbasicConstraints=CA:FALSE\n' > server.ext
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
  -keyout ca.key -out ca.pem -subj "/CN=Kelp Test CA" -days 2 \
  -addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
  -keyout server.key -out server.csr -subj "/CN=localhost"
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
  -out server.pem -days 2 -extfile server.ext
chmod 600 *.key
```

I ran that in `/tmp/kelp-tut-certs`. Then the program: a server worker that loads the
certificate and key with `std/tlsfile` (which needs its own `fs` grant, the path of the
certificate directory), builds a `tls.ServerConfig`, and answers one request with
`http.serve_tls_on`; and a client in `main` that trusts the test CA through
`with_ca_pem`:

```kelp
impl "std/http" caps(net = ["127.0.0.1:36012", "localhost:36012"])
impl "std/tls"
impl "std/tlsfile" caps(fs = ["/tmp/kelp-tut-certs/**"])
impl "std/thread"
impl "std/result"

fun hello(req: &http.ServerRequest).R: http.ServerResponse {
    return http.ok_text("hello over tls")
}

fun serve(fd: i32).R: u64 {
    val cert = tlsfile.read_pem("/tmp/kelp-tut-certs/server.pem", "certificate chain")
    val key = tlsfile.read_pem("/tmp/kelp-tut-certs/server.key", "private key")
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
    val server = http.listen(36012)
    server.set_accept_timeout(10000)
    val worker = thread.spawn(serve, server.fd)

    val ca = tlsfile.read_pem("/tmp/kelp-tut-certs/ca.pem", "certificate")
    when ca {
        Ok(pem) -> {
            val opts = tls.client_options().with_ca_pem(pem).with_timeout_ms(10000)
            when http.try_get_tls("https://localhost:36012/", &opts) {
                Ok(resp) -> print("status ${resp.status}: ${resp.text()}")
                Err(_) -> print("https request failed")
            }
        }
        Err(_) -> print("could not read the CA")
    }
    when thread.join(worker) {
        Ok(n) -> print("served ${n} over tls")
        Err(e) -> print(e.message)
    }
}
```

```text
status 200: hello over tls
served 1 over tls
```

Notice how the capabilities line up: `net` for `localhost:36012` (the client writes the
host name the certificate names, so the grant lists that spelling too), `fs` for the
certificate directory only, and nothing else. TLS verification is not optional: there
is no switch to turn it off.

A client that does not know the CA fails, and the server just goes on:

```kelp
impl "std/http" caps(net = ["127.0.0.1:36012", "localhost:36012"])
impl "std/tls"
impl "std/tlsfile" caps(fs = ["/tmp/kelp-tut-certs/**"])
impl "std/thread"
impl "std/result"

fun hello(req: &http.ServerRequest).R: http.ServerResponse {
    return http.ok_text("hello over tls")
}

fun serve(fd: i32).R: u64 {
    val cert = tlsfile.read_pem("/tmp/kelp-tut-certs/server.pem", "certificate chain")
    val key = tlsfile.read_pem("/tmp/kelp-tut-certs/server.key", "private key")
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
    val server = http.listen(36012)
    server.set_accept_timeout(2000)
    val worker = thread.spawn(serve, server.fd)

    // no private CA given: the system roots do not know our test CA
    when http.try_get("https://localhost:36012/") {
        Ok(resp) -> print("status ${resp.status}")
        Err(e) -> when e {
            Dial(reason) -> print("dial failed: ${reason}")
            Exchange(reason) -> print("exchange failed: ${reason}")
            Redirects(reason) -> print("redirects: ${reason}")
        }
    }
    when thread.join(worker) {
        Ok(n) -> print("served ${n} over tls")
        Err(e) -> print(e.message)
    }
}
```

```text
dial failed: tls: the certificate is not trusted by the system store
served 0 over tls
```

The handshake failure arrives as a `Dial` error (nothing was sent), and the server,
which got a client that went away, counted no request and stopped at its accept timeout.

A few options for later, all on the `std/tls` page: ALPN, a minimum protocol version,
and mutual TLS with a client certificate (`require_client_cert_pem`).

## Exercises

1. Add a `/add?a=2&b=40` route to the server that returns the sum as text, and fetch it.
2. In the HTTPS program, what would make the client fail with a host mismatch rather
   than an untrusted certificate? (Think about what name the certificate carries.)

<details>
<summary>Solutions</summary>

1.

```kelp
impl "std/http" caps(net = ["127.0.0.1:36013"])
impl "std/thread"
impl "std/result"
impl "std/option"
impl "std/str"
impl "std/fmt"

fun number(req: &http.ServerRequest, name: &str).R: i64 {
    if let Some(text) = req.query_param(name) {
        if let Ok(n) = str.parse_i64(text.as_str()) {
            return n
        }
    }
    return 0
}

fun handle(req: &http.ServerRequest).R: http.ServerResponse {
    if str.eq(req.path.as_str(), "/add") {
        val sum = number(req, "a") + number(req, "b")
        val text = fmt.int(sum)
        return http.ok_text(text.as_str())
    }
    return http.not_found()
}

fun serve(fd: i32).R: u64 {
    val server = http.Server(fd = fd)
    val limits = http.default_limits()
    val n = http.serve_on(&server, handle, &limits, 1)
    server.close()
    return n
}

fun main() {
    val server = http.listen(36013)
    val worker = thread.spawn(serve, server.fd)
    when http.try_get("http://127.0.0.1:36013/add?a=2&b=40") {
        Ok(r) -> print("2 + 40 = ${r.text()}")
        Err(e) -> print("request failed")
    }
    val joined = thread.join(worker)
}
```

```text
2 + 40 = 42
```

2. The certificate names `DNS:localhost`, and the client checks the host name it passes to
   the handshake. The same program with the URL changed to `https://127.0.0.1:36012/`
   (the grant already lists that host) printed, on both backends:

```text
dial failed: tls: the certificate does not match the host name
served 0 over tls
```

   The name in the certificate was not the name the client dialled.

</details>

Next: [Testing and tooling](/tutorial/15-tooling).
