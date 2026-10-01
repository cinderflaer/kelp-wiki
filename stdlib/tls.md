---
title: "`std/tls`"
description: "Client-side TLS: a typed `TlsError`, a `try_` family beside the panicking wrappers, `TlsOptions` (private CA file or directory, timeout), truncation detection and `wss`. Gated on net, the same domain std/net and std/http already hold."
isPublished: true
tags: "stdlib, networking, tls"
---
Client-side TLS. This is what makes `https://` work in
[`std/http`](/stdlib/http) and `wss://` work in [`std/ws`](/stdlib/ws); most
programs never import it directly.

**Gated on `net`, the same domain `std/net` and `std/http` already hold, not a
new capability.** `https` is still network access, so a program that already
writes

```kelp
impl "std/http" caps(net = ["api.example.com:443"])
```

needs nothing new to reach an `https://` URL: the grant it already holds is the
one that covers it, exactly as it covers `http://`.

## Why it takes a socket instead of dialing one

A capability grant is resolved **one hop from the importing program's own
`impl` line**. `net.connect` inside `std/http.kp` is checked against the grant
the *program* wrote on `impl "std/http" caps(net = [...])`; that is what makes
plain `http` work today. If `std/tls` dialed a socket itself, that call would
be checked against `std/tls`'s *own* `impl` line instead, which carries no
`caps()` clause and so is always empty, no matter what the program granted.

So `std/tls` never dials, listens, or resolves a name: `handshake` takes an
already-connected [`net.Socket`](/stdlib/net), wraps it, and everything after
that is read/write on the wrapped stream. The dial stays in `std/http.kp`, where
the check already works.

## Types

```kelp
datac TlsStream(val fd: i32, val handle: usize)

pub enum TlsError {
    Untrusted
    Expired
    HostMismatch
    ProtocolTooOld
    HandshakeFailed(val reason: String)
    PeerClosedUncleanly
    Timeout
    Io(val reason: String)
}

pub datac TlsOptions(val ca_file: String, val ca_dir: String, val timeout_ms: u64)
```

`TlsStream` pairs a plain `fd` with the OpenSSL handle bound to it, not a
`net.Socket`, because a `net.Socket` and its `TlsStream` would then be two owners
of one descriptor. The value is not `Copy`, so there is never a silent second
free of the handle. `shutdown` ends only the TLS session (sending
`close_notify` where the connection allows it) and frees the OpenSSL handle; it
does not close `fd`. The caller closes the socket itself afterward with
`net.close(net.Socket(fd = t.fd))`. Nothing closes on drop, the same rule
`net.Socket` and `net.Listener` follow.

`handle` is carried as a `usize` rather than an `extern type` handle: an `extern
type` is legal only in a module with its own `coral.toml` `[extern."<module
id>"]` section, and a compiler-shipped std module has no manifest.
`plan/release-goals.md` records the smallest compiler change that would lift
that, under "Follow-ups".

## Functions

Every call has a fallible form returning `Result<_, TlsError>` and a panicking
wrapper that panics with the error's own text.

| Fallible | Panicking | Returns | Notes |
| --- | --- | --- | --- |
| `try_handshake(s, host)` | `handshake(s, host)` | `Result<TlsStream, TlsError>` / `TlsStream` | the TLS handshake over an already-connected socket |
| `try_handshake_with(s, host, opts)` | `handshake_with(s, host, opts)` | as above, with `TlsOptions` | private CA, timeout |
| `try_handshake_timeout(s, host, ms)` | `handshake_timeout(s, host, ms)` | as above, with a deadline | shorthand for `TlsOptions` with only `timeout_ms` |
| `try_write(t, data)` | `write(t, data)` | `Result<usize, TlsError>` / `usize` | one write, may be partial |
| `try_write_all(t, data)` | `write_all(t, data)` | `Result<usize, TlsError>` / `usize` | loops until everything is written |
| `try_read(t, max)` | `read(t, max)` | `Result<Bytes, TlsError>` / `Bytes` | up to `max` bytes |
| `try_read_into(t, buf, at)` | `read_into(t, buf, at)` | `Result<usize, TlsError>` / `usize` | fills an existing buffer from offset `at` |
| `try_shutdown(t)` | `shutdown(t)` | `Result<bool, TlsError>` | ends the TLS session and frees the handle |

`set_timeout(t, ms)` sets the receive and send timeouts on the stream's socket,
so a blocking read on a silent peer gives up instead of hanging forever; `ms`
of `0` means "no timeout". The handshake's own timeout is set before it starts.

`TlsError` is a value a caller branches on: `Timeout` says retry, `Untrusted`
says install the CA, and so on. `HandshakeFailed` and `Io` carry OpenSSL's or
the socket's own sentence, so the detail is not thrown away. The panicking
wrappers panic with the text those variants carry.

The program below points `try_handshake` at a local plain-TCP peer that answers
with something that is not a TLS record, so the handshake fails and the typed
error is reported. `report` matches every variant; a real caller usually has
somewhere to go for only a few of them.

```kelp
impl "std/net" caps(net = ["127.0.0.1:*"])
impl "std/tls"
impl "std/thread"

fun serve(l: move net.Listener) {
    val peer = net.accept(l)
    net.send_text(peer, "this is not a TLS record\n")
    thread.sleep_ms(200)
    net.close(peer)
    l.close()
}

fun report(e: move tls.TlsError) {
    when e {
        Untrusted -> print("untrusted certificate")
        Expired -> print("expired certificate")
        HostMismatch -> print("host mismatch")
        ProtocolTooOld -> print("protocol too old")
        HandshakeFailed(reason) -> {
            print("handshake failed")
            print(reason)
        }
        PeerClosedUncleanly -> print("peer closed without close_notify")
        Timeout -> print("timeout")
        Io(reason) -> {
            print("io error")
            print(reason)
        }
    }
}

fun main() {
    val l = net.listen(0)
    val port = l.port()
    val h = thread.spawn(serve, l)

    when net.try_connect("127.0.0.1", port) {
        Ok(sock) -> {
            when tls.try_handshake(sock, "127.0.0.1") {
                Ok(t) -> {
                    print("handshake ok")
                    tls.shutdown(t)
                }
                Err(e) -> report(e)
            }
        }
        Err(e) -> print(e.reason)
    }

    when thread.join(h) {
        Ok(_) -> {}
        Err(_) -> {}
    }
}
```

```text
protocol too old
```

## Truncation is detected

A connection that ends without a `close_notify` is an error, never a clean EOF.
`try_read` is `Ok` with an empty `Bytes` on a clean `close_notify`, and
`Err(TlsError.PeerClosedUncleanly)` when the stream ended without one. This is
by design: a peer that stops mid-body is never a clean end of stream. It is what
makes `std/http`'s framing refuse a short body rather than accepting it as
complete.

## Timeouts

`TlsOptions.timeout_ms` is applied as `SO_RCVTIMEO`/`SO_SNDTIMEO` before the
handshake starts, so a silent peer is `Err(Timeout)` instead of a hang. The
settings stay on the socket for the reads and writes that follow, and
`set_timeout` changes them later. `0` is "no timeout", which is `SO_RCVTIMEO`'s
own meaning; there is no silent default deadline.

## Certificate verification is not optional

The system trust store (`SSL_CTX_set_default_verify_paths`, which honours
`SSL_CERT_FILE` and `SSL_CERT_DIR`), `SSL_VERIFY_PEER`, and hostname
verification against the name the caller wrote to `handshake` (the same name the
`net` grant was checked against, not whatever the DNS resolution turned it into)
are all on unconditionally, and TLS 1.2 is the floor. A self-signed or
mismatched certificate is a handshake failure, not a silent connection.

There is no `insecure` flag. What there is, is a way to *add* a private CA:
`TlsOptions(ca_file = ..., ca_dir = ..., timeout_ms = ...)` calls
`SSL_CTX_load_verify_locations` with the named file or directory. It can never
remove the requirement to verify and it does not lower the TLS 1.2 minimum.

## `wss`

`std/ws` speaks `wss://` over this module: the scheme comes off the parsed URL
and the dial stays in `std/ws`, exactly as the `https` dial stays in
`std/http`. A `wss` connection is the same WebSocket client over a `TlsStream`,
so certificate verification, the TLS 1.2 floor and truncation detection all
apply unchanged.

```kelp
impl "std/ws" caps(net = ["*"], rand = [])

fun main() {
    val u = ws.parse_url("wss://example.com/socket")
    print(u.scheme)
    print(u.port)
}
```

```text
wss
443
```

## Linking

The system OpenSSL (`-lssl -lcrypto`) is linked, and OpenSSL's headers are
included in the program's extern object, **only when a program reaches
`std/tls`**. `std/http` and `std/ws` import it, so a program that uses either
gets it too; a program that never touches TLS does not need either the library
or the development output.

```sh
# a program that reaches std/tls: its <out>.externs.c includes openssl/ssl.h
# a program that does not: the file carries no openssl include and the link
# line carries no -lssl
```

When it is needed, the linker has to find `libssl` and `libcrypto`, and the
OpenSSL headers have to be on the include path. `nix-shell shell.nix` provides
both; [Install and build](/getting-started/install#requirements) lists them for
every other setup.

## See also

- [`std/http`](/stdlib/http)
- [`std/ws`](/stdlib/ws)
- [`std/net`](/stdlib/net)
- [Capability patterns](/reference/capability-patterns)
