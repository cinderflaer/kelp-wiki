---
title: "`std/net`"
description: "TCP sockets. Gated on net."
isPublished: true
tags: "stdlib, networking"
---
TCP sockets. **Gated on `net`.**

```kelp
impl "std/net" caps(net = ["api.example.com:443"])
impl "std/net" caps(net = ["127.0.0.1:*"])
impl "std/net" caps(net = ["*"])                 // anyone
```

`net` patterns are matched against the **host string the program wrote**, never a
resolved address, so `127.0.0.1:*` does not cover `localhost`. A pattern is
`host`, `host:port`, `*.host`, `*:port` or `*`.

A pattern made only of digits, dots and `*` (`10.0.0.*`) matches **IPv4
literals only**: it does not admit a host *name* such as `10.0.0.xyz`, in
`connect` or in `resolve`.

`listen(port)` is checked against the **port** of the grant, and the grant's host
decides the interface: a grant that includes `*` or any pattern matching
`0.0.0.0` binds every interface, and a grant of loopback or named hosts only
(`127.0.0.1:*`, `localhost:*`) binds `127.0.0.1`. See the
[threat model](/reference/capability-threat-model).

`listen_on(host, port)` names the host to bind: `"127.0.0.1"` for loopback only,
`"0.0.0.0"` or `"*"` for every interface, or a name that resolves to an IPv4
address. It is checked on `host:port` exactly as `connect` is, so a grant of
`127.0.0.1:8080` lets a module listen on loopback and refuses `0.0.0.0`, another
host and another port. `http.listen_on(host, port)` is the same for a `Server`.

## Types

```kelp
datac Socket(val fd: i32)
datac Listener(val fd: i32)
datac ConnectErr(val reason: String)
datac NetErr(val reason: String)
```

`Socket` and `Listener` are neither `Copy`, so a socket is moved when passed and
there is exactly one owner of the descriptor. `ConnectErr` is what
`try_connect` hands back instead of panicking: `reason` is the whole refusal, a
single `String` rather than an `errno` (see below). `NetErr` is the same for a
failed send or receive: `reason` is the text the panicking form would have
panicked with (the message line and the `errno` detail line, or
`net.recv: timed out` for a read that hit the socket's timeout).

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `connect(host, port)` | `Socket` | panics on failure (`net.connect: connection failed`) |
| `try_connect(host, port)` | `Result<Socket, ConnectErr>` | the fallible `connect`: a refused dial is `Err`, and only a capability denial still panics |
| `try_send_all(s, data)` / `try_recv(s, max)` / `try_recv_into(s, buf, at)` | `Result<usize, NetErr>` / `Result<Bytes, NetErr>` / `Result<usize, NetErr>` | `send_all`, `recv` and `recv_into` with a reset, a closed peer or a timeout as `Err` (`NetErr.reason` is the panic text) instead of a panic; an empty or zero `Ok` is still end of stream |
| `listen(port)` | `Listener` | port `0` asks the OS for a free one |
| `accept(l)` | `Socket` | blocks until a peer connects |
| `try_accept(l)` | `Result<Socket, NetErr>` | `accept` with a failed accept (including a timeout) as an `Err` instead of a panic |
| `Listener.port()` | `u16` | the bound port: how you learn what `0` became |
| `Listener.set_timeout(ms)` | `Unit` | `mut` receiver; makes `accept`/`try_accept` give up after `ms` (`0` waits forever) |
| `Listener.close()` | `Unit` | |
| `close(s)` | `Unit` | |
| `shutdown_write(s)` | `Unit` | half-close, which is how a line protocol says "no more input" |
| `try_shutdown_write(s)` | `bool` | `shutdown_write` that answers `false` when the peer has already reset the socket |
| `send(s, data)` | `usize` | one `send`; may write less than asked |
| `send_all(s, data)` | `usize` | loops until everything is written |
| `send_text(s, text)` | `Unit` | |
| `recv(s, max)` | `Bytes` | up to `max` bytes; **empty means the peer closed**, or that `max` was `0` |
| `recv_into(s, buf, at)` | `usize` | |
| `try_send_all(s, data)` | `Result<usize, NetErr>` | the fallible `send_all`; the `Ok` count is always the whole buffer |
| `try_recv(s, max)` | `Result<Bytes, NetErr>` | the fallible `recv`; an empty `Ok` is still the peer's clean end of stream |
| `try_recv_into(s, buf, at)` | `Result<usize, NetErr>` | the fallible `recv_into`; `Ok(0)` is end of stream |
| `Socket.wait_readable(timeout_ms)` / `wait_writable(...)` | `bool` | |
| `Socket.set_timeout(ms)` | `Unit` | `mut` receiver |
| `mono_ms()` | `i64` | milliseconds on the monotonic clock, for deadlines: only the difference of two readings means anything |
| `Socket.peer_addr()` | `String` | |
| `resolve(host)` | `List<String>` | addresses, for a caller that wants to log one |

## A refused dial is a value

`connect` panics when `getaddrinfo` fails or nothing answers; `try_connect` is the
same call with that failure as a value. The shape is `std/process`'s, `run`
beside `try_run` with the error as a named type (`ProcErr`), which is the pair the
stdlib already had for a program that must survive a failure instead of ending on
it. `connect` stays as the convenience wrapper for a caller for whom a refused
dial really is fatal.

`ConnectErr.reason` is the text `connect` panics with, its message line and the
detail line under it, so a caller that logs `e.reason` prints exactly what the
panicking form would have written to stderr:

```text
net.connect: connection failed
  errno 111: Connection refused
```

## A failed send or receive is a value

`try_send_all`, `try_recv` and `try_recv_into` are the same calls with a reset,
a closed peer or a timeout as `Err(NetErr)` instead of a panic. The capability
check still panics: a denial is not a value in this module.

```kelp
impl "std/net" caps(net = ["127.0.0.1:*"])
impl "std/thread"

fun serve(l: move net.Listener) {
    val peer = net.accept(l)
    thread.sleep_ms(3000)
    net.close(peer)
    l.close()
}

fun main() {
    val l = net.listen(0)
    val port = l.port()
    val h = thread.spawn(serve, l)

    when net.try_connect("127.0.0.1", port) {
        Ok(sock) -> {
            var s = sock
            s.set_timeout(300)
            when net.try_send_all(s, Bytes.from_str("ping")) {
                Ok(n) -> print(n)
                Err(e) -> {
                    print("send failed")
                    print(e.reason)
                }
            }
            when net.try_recv(s, 16) {
                Ok(b) -> print(b.len())
                Err(e) -> {
                    print("recv failed")
                    print(e.reason)
                }
            }
            net.close(s)
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
4
recv failed
net.recv: timed out
```

A name that does not resolve is the other message, and its detail line is the
resolver's own text rather than an `errno`:

```text
net.connect: cannot resolve host
  getaddrinfo: <the resolver's message>
```

That pair is why `reason` is one `String` and not an `errno` field: half the
failures have no `errno` to put in one. The capability check is not a value in
either form, because it runs at the call site before the dial.

A program that reconnects is what this exists for: a refused dial is an `Err` to
retry rather than the end of the process. The port comes from the kernel, so
every attempt dials something nothing owns:

```kelp
impl "std/net"
impl "std/result"

fun dead_port() => u16 {
    val l = net.listen(0)
    val port = l.port()
    l.close()
    return port
}

fun main() {
    val port = dead_port()
    var attempt = 1
    while attempt <= 3 {
        val r = net.try_connect("127.0.0.1", port)
        when r {
            Ok(s) -> {
                net.close(s)
                print("attempt ${attempt}: connected, so something took the port after it was released")
            }
            Err(e) -> print("attempt ${attempt}: ${e.reason}")
        }
        attempt = attempt + 1
    }
    print("gave up")
}
```

```text
attempt 1: net.connect: connection failed
  errno 111: Connection refused
attempt 2: net.connect: connection failed
  errno 111: Connection refused
attempt 3: net.connect: connection failed
  errno 111: Connection refused
gave up
```

## A listener that can time out

`accept` blocks forever. `Listener.set_timeout(ms)` puts an upper bound on it,
and `try_accept` turns the bounded failure into an `Err` whose reason is
`net.accept: timed out`, which is how one thread serves many sockets or stops
when nobody is coming. `net.mono_ms()` is the monotonic clock the deadlines are
built on; it lives here, not in `std/time`, so a module that holds only `net`
can keep a deadline without being handed the `time` capability too.
`try_shutdown_write` is `shutdown_write` with a socket the peer has already
reset as `false` instead of a panic: a server ending a connection it does not
know the state of is exactly that case.

```kelp
impl "std/net"

fun main() {
    var l = net.listen(0)
    l.set_timeout(100)
    val t0 = net.mono_ms()
    when net.try_accept(l) {
        Ok(s) -> {
            net.close(s)
            print("unexpected connection")
        }
        Err(e) -> {
            print(e.reason)
            print(net.mono_ms() - t0 >= 100)
        }
    }

    val c = net.connect("127.0.0.1", l.port())
    when net.try_accept(l) {
        Ok(s) -> {
            print(net.try_shutdown_write(s))
            net.close(s)
        }
        Err(e) -> print(e.reason)
    }
    net.close(c)
    l.close()
}
```

```text
net.accept: timed out
true
true
```

The first `try_accept` waits the 100 ms and fails, so the elapsed reading is at
least `100`. The second accept has a client already queued, so
`try_shutdown_write` on the accepted socket is `true`.

## Example

```kelp
impl "std/net"

fun main() {
    val l = net.listen(0)           // any free port
    val port = l.port()
    print(port > 0)

    val s = net.connect("127.0.0.1", port)
    val peer = net.accept(l)
    net.send_all(s, Bytes.from_str("hello"))

    val got = net.recv(peer, 64)
    print(got.as_str())
    net.close(peer)
    net.close(s)
    l.close()
}
```

## Notes

- `recv` returning **empty** `Bytes` is the only end-of-stream signal; a partial
  read is normal and a loop is the caller's job
  ([`lineproto`](/libraries/lineproto) does exactly that). A `max` of `0` also
  returns empty, immediately rather than after blocking, which is what
  `recv_into` with an empty buffer already did.
- `send` may write fewer bytes than asked; use `send_all` unless you are
  implementing your own back-pressure.
- Blocking is the default. `set_timeout` and `wait_readable` are how a caller gets
  a bounded wait.
- `std/net` itself is plain TCP; TLS lives one layer up in
  [`std/tls`](/stdlib/tls), which `http.parse_url` uses for `https`
  (MK5-S4b-M1) and `ws.parse_url` uses for `wss` (`meta/milestones.md`). A `wss`
  connection is the same WebSocket client over a `TlsStream`.
- Errors panic rather than returning `Result`, except `try_connect` and the
  `try_send_all`/`try_recv`/`try_recv_into` trio, whose failure is the `Err`
  they exist to hand back. A capability denial still panics either way.

## See also

- [`std/http`](/stdlib/http): an HTTP/1.1 client over this module
- [`lineproto`](/libraries/lineproto): CRLF line protocols
- [Capability patterns](/reference/capability-patterns)
