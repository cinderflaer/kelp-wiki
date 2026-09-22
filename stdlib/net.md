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
```

Neither is `Copy`, so a socket is moved when passed and there is exactly one owner
of the descriptor.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `connect(host, port)` | `Socket` | panics on failure (`net.connect: connection failed`) |
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
- There is no TLS: `http.parse_url` refuses `https` by name rather than pretending.
- Errors panic rather than returning `Result`.

## See also

- [`std/http`](/stdlib/http): an HTTP/1.1 client over this module
- [`lineproto`](/libraries/lineproto): CRLF line protocols
- [Capability patterns](/reference/capability-patterns)
