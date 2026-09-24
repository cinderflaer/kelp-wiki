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

## Types

```kelp
datac Socket(val fd: i32)
datac Listener(val fd: i32)
datac ConnectErr(val reason: String)
```

`Socket` and `Listener` are neither `Copy`, so a socket is moved when passed and
there is exactly one owner of the descriptor. `ConnectErr` is what
`try_connect` hands back instead of panicking: `reason` is the whole refusal, a
single `String` rather than an `errno` (see below).

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `connect(host, port)` | `Socket` | panics on failure (`net.connect: connection failed`) |
| `try_connect(host, port)` | `Result<Socket, ConnectErr>` | the fallible `connect`: a refused dial is `Err`, and only a capability denial still panics |
| `listen(port)` | `Listener` | port `0` asks the OS for a free one |
| `accept(l)` | `Socket` | blocks until a peer connects |
| `Listener.port()` | `u16` | the bound port: how you learn what `0` became |
| `Listener.close()` | `Unit` | |
| `close(s)` | `Unit` | |
| `shutdown_write(s)` | `Unit` | half-close, which is how a line protocol says "no more input" |
| `send(s, data)` | `usize` | one `send`; may write less than asked |
| `send_all(s, data)` | `usize` | loops until everything is written |
| `send_text(s, text)` | `Unit` | |
| `recv(s, max)` | `Bytes` | up to `max` bytes; **empty means the peer closed**, or that `max` was `0` |
| `recv_into(s, buf, at)` | `usize` | |
| `Socket.wait_readable(timeout_ms)` / `wait_writable(...)` | `bool` | |
| `Socket.set_timeout(ms)` | `Unit` | `mut` receiver |
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

fun dead_port().R: u16 {
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
- There is no TLS: `http.parse_url` refuses `https` and `ws.parse_url` refuses
  `wss`, both by name rather than pretending.
- Errors panic rather than returning `Result`, with the one exception of
  `try_connect`, whose dial failure is the `Err` it exists to hand back.

## See also

- [`std/http`](/stdlib/http): an HTTP/1.1 client over this module
- [`lineproto`](/libraries/lineproto): CRLF line protocols
- [Capability patterns](/reference/capability-patterns)
