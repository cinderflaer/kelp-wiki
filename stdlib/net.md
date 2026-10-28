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
host and another port. `http.listenOn(host, port)` is the same for a `Server`.

## Types

```kelp
datac Socket(val fd: i32)
datac Listener(val fd: i32)
datac ConnectErr(val reason: String)
datac NetErr(val reason: String)
```

`Socket` and `Listener` are neither `Copy`, so a socket is moved when passed and
there is exactly one owner of the descriptor. `ConnectErr` is what `connect`
hands back when the dial fails: `reason` is the whole refusal, a single `String`
rather than an `errno` (see below). `NetErr` is the same for a failed send,
receive or accept: `reason` is the text of the failure (the message line and the
`errno` detail line, or `net.recv: timed out` for a read that hit the socket's
timeout).

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `connect(host, port)` | `Result<Socket, ConnectErr>` | a refused dial is `Err`; only a capability denial panics |
| `listen(port)` | `Listener` | port `0` asks the OS for a free one |
| `accept(l)` | `Result<Socket, NetErr>` | blocks until a peer connects; a failed accept (including a timeout) is `Err` |
| `Listener.port()` | `u16` | the bound port: how you learn what `0` became |
| `Listener.setTimeout(ms)` | `Unit` | `mut` receiver; makes `accept` give up after `ms` (`0` waits forever) |
| `Listener.close()` | `Unit` | |
| `close(s)` | `Unit` | |
| `shutdown_write(s)` | `Result<unit, NetErr>` | half-close, which is how a line protocol says "no more input"; `Err` when the peer has already reset the socket |
| `send(s, data)` | `int` | one `send`; may write less than asked |
| `send_all(s, data)` | `Result<int, NetErr>` | loops until everything is written; the `Ok` count is always the whole buffer |
| `send_text(s, text)` | `Unit` | |
| `recv(s, max)` | `Result<Bytes, NetErr>` | up to `max` bytes; **an empty `Ok` means the peer closed**, or that `max` was `0` |
| `recv_into(s, buf, at)` | `Result<int, NetErr>` | `Ok(0)` is end of stream |
| `Socket.waitReadable(timeout_ms)` / `wait_writable(...)` | `bool` | |
| `Socket.setTimeout(ms)` | `Unit` | `mut` receiver |
| `mono_ms()` | `i64` | milliseconds on the monotonic clock, for deadlines: only the difference of two readings means anything |
| `Socket.peerAddr()` | `String` | |
| `resolve(host)` | `List<String>` | addresses, for a caller that wants to log one |

`send`, `wait_readable` and the other calls that are not in the table above keep
their panic: they have no value form, because nothing fallible happens in them
that a caller could act on.

Every fallible call returns a `Result`. A program that wants a panic on failure
wraps the call in `result.expect`, with the message to print:

```kelp
impl "std/net"
impl "std/result"

val s = result.expect(net.connect("api.example.com", 443), "cannot reach the API")
```

## A refused dial is a value

`connect` returns `Err` when `getaddrinfo` fails or nothing answers. The shape is
the one `std/process`'s `run` has, with the error as a named type (`ProcErr`).

`ConnectErr.reason` is the text of the failure, its message line and the detail
line under it, so a caller that logs `e.reason` prints the same words a panic
would have written:

```text
net.connect: connection failed
  errno 111: Connection refused
```

## A failed send or receive is a value

`send_all`, `recv` and `recv_into` return `Err(NetErr)` for a reset, a closed
peer or a timeout. The capability check still panics: a denial is not a value
in this module.

```kelp
impl "std/net" caps(net = ["127.0.0.1:*"])
impl "std/result"
impl "std/thread"

fun dial(port: u16) {
    when net.connect("127.0.0.1", port) {
        Ok(sock) -> {
            var s = sock
            s.setTimeout(300)
            when net.sendAll(s, Bytes.from_str("ping")) {
                Ok(n) -> print(n)
                Err(e) -> {
                    print("send failed")
                    print(e.reason)
                }
            }
            when net.recv(s, 16) {
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
}

fun main() {
    val l = net.listen(0)
    val port = l.port()
    val h = thread.spawn(dial, port)

    val peer = result.expect(net.accept(l), "accept")
    thread.sleepMs(3000)
    net.close(peer)

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
failures have no `errno` to put in one. The capability check is not a value,
because it runs at the call site before the dial.

A program that reconnects is what this is for: a refused dial is an `Err` to
retry rather than the end of the process. The port comes from the kernel, so
every attempt dials something nothing owns:

```kelp
impl "std/net"

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
        val r = net.connect("127.0.0.1", port)
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

`accept` blocks forever. `Listener.setTimeout(ms)` puts an upper bound on it,
and `accept` then returns an `Err` whose reason is `net.accept: timed out`, which
is how one thread serves many sockets or stops when nobody is coming.
`net.monoMs()` is the monotonic clock the deadlines are built on; it lives
here, not in `std/time`, so a module that holds only `net` can keep a deadline
without being handed the `time` capability too. `shutdown_write` answers `Err`
for a socket the peer has already reset: a server ending a connection it does
not know the state of is exactly that case.

```kelp
impl "std/net"
impl "std/result"

fun main() {
    var l = net.listen(0)
    l.setTimeout(100)
    val t0 = net.monoMs()
    when net.accept(l) {
        Ok(s) -> {
            net.close(s)
            print("unexpected connection")
        }
        Err(e) -> {
            print(e.reason)
            print(net.monoMs() - t0 >= 100)
        }
    }

    val c = result.expect(net.connect("127.0.0.1", l.port()), "connect")
    when net.accept(l) {
        Ok(s) -> {
            print(net.shutdownWrite(s).isOk())
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

The first `accept` waits the 100 ms and fails, so the elapsed reading is at
least `100`. The second accept has a client already queued, so
`shutdown_write` on the accepted socket is `Ok`, and `is_ok()` is `true`.

## Example

```kelp
impl "std/net"
impl "std/result"

fun main() {
    val l = net.listen(0)           // any free port
    val port = l.port()
    print(port > 0)

    val s = result.expect(net.connect("127.0.0.1", port), "connect")
    val peer = result.expect(net.accept(l), "accept")
    result.expect(net.sendAll(s, Bytes.from_str("hello")), "send")

    val got = result.expect(net.recv(peer, 64), "recv")
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
  [`std/tls`](/stdlib/tls), which `http.parseUrl` uses for `https`
  (MK5-S4b-M1) and `ws.parseUrl` uses for `wss` (`meta/milestones.md`). A `wss`
  connection is the same WebSocket client over a `TlsStream`.
- Fallible calls return `Result`, and a panic is `result.expect(call, "message")`.
  A capability denial still panics, since it is not a value in this module.

## See also

- [`std/http`](/stdlib/http): an HTTP/1.1 client over this module
- [`lineproto`](/libraries/lineproto): CRLF line protocols
- [Capability patterns](/reference/capability-patterns)
