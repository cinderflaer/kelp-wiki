---
title: "`lineproto`: buffered CRLF lines over a socket"
description: "A small line-oriented request/response helper over a std/net Socket the caller already holds - send_line appends \\r\\n and sends it whole, and LineReader buffers recv chunks and hands back one..."
isPublished: true
tags: "library, networking"
---
A small line-oriented request/response helper over a `std/net` `Socket` the
caller already holds: `send_line` appends `\r\n` and sends it whole, and
`LineReader` buffers `recv` chunks and hands back one `\r\n`-terminated line at a
time. SMTP/IMAP/Redis-shaped text protocols.

**Gated on `net`.** The library never calls `net.connect`/`net.listen` itself,
only `net.send_all`/`net.recv` on a socket the consumer connected, but it
genuinely calls a `net`-gated function, so its consumer must delegate a real
grant:

```toml
[dependencies]
lineproto = "Juniper/fpl/lineproto"
```

```kelp
impl "deps/lineproto/lib" caps(net = ["example.com:25"])
```

The pattern must cover whatever host the consumer already connected
`net.Socket` to.

## Types

```kelp
datac LineReader(val fd: i32, var buf: Bytes, var start: usize)
```

`LineReader` stores the socket's raw `fd: i32` rather than a `net.Socket` field:
`net.Socket` is not `Copy`, and a `datac` field can only be read out by
reference, never moved out by value, so every call reconstructs
`net.Socket(fd = fd)` locally instead of storing one.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `send_line(s: net.Socket, line: &str)` | `Unit` | `<line>\r\n`, sent with `net.send_all` (not one `send`) |
| `new_reader(s: net.Socket)` | `LineReader` | takes the socket's `fd`; the caller keeps ownership of the socket |
| `reader.read_line(r: mut LineReader)` | `option.Option<String>` | the next line without its terminator; `None` when the peer closes with no further complete line pending |

Constants: `CR` (13), `LF` (10).

## Behaviour

- `read_line` scans the buffer for `\r\n`, copies out the bytes before it, and
  advances `start` past the terminator. Whatever a `recv` overshot is kept for the
  next call, so two lines arriving in one `recv` are still handed back one at a
  time, in order.
- On no complete line, it calls `net.recv(socket, 4096)` and appends; an empty
  chunk means the peer closed, and it returns `None` immediately.
- A trailing fragment with no `\r\n` at EOF is **discarded**, not returned.
- The terminator must be exactly CRLF: a bare `\n` is content.

## Example: the server side

```kelp
impl "std/net"
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])

fun main() {
    val l = net.listen(45678)
    print(l.port())
    val s = net.accept(l)
    var reader = lineproto.new_reader(s)
    var going = true
    while going {
        val got = reader.read_line()
        if let Some(line) = got {
            print(line)
        } else {
            going = false
        }
    }
    print("done")
}
```

A client that connects and sends two lines:

```kelp
impl "std/net"
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])

fun main() {
    val s = net.connect("127.0.0.1", 45678)
    lineproto.send_line(s, "HELLO 1")
    lineproto.send_line(s, "HELLO 2")
    net.close(s)
}
```

Server output after the client runs and closes (both verified against a real
socket pair):

```
45678
HELLO 1
HELLO 2
done
```

## Notes

- One connection, no reconnect, no timeouts: `read_line` blocks in `net.recv`
  until a line, a close, or an error. Set a socket timeout with
  `Socket.set_timeout(ms)` or check `Socket.wait_readable(ms)` first if a
  blocking read is not acceptable.
- No command/response pairing (no "send then read one reply" helper), no pipelining
  bookkeeping, no `\n`-only mode, no line-size limit beyond what memory allows.
- The buffer is never compacted: `start` advances and the buffer grows across
  calls. A very long-lived reader should be recreated per request, or the caller
  should finish the exchange and close.
