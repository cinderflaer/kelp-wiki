---
title: "`std/ws`"
description: "A WebSocket client (RFC 6455) over ws:// only. It holds net for the socket and rand for the handshake key and every masking key, so an import delegates both."
isPublished: true
tags: "stdlib, networking"
---
A WebSocket **client** (RFC 6455), over `ws://` only. It holds `net` and `rand`.

Source section:
[`syntax.md` §16.18](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

```kelp
impl "std/ws" caps(net = ["gateway.example.com:80"], rand = [])
```

`std/ws` is pure Kelp over [`std/net`](/stdlib/net) and
[`std/encoding`](/stdlib/encoding): no compiler change and no dependency.
**Two domains, because the module has two needs.** `net` reaches the socket, and
its half of the check is the host-and-port check `net.connect` already gives: the
grant matches the host as written and the port beside it, before name resolution
runs, and a call for anything else is denied at the connect with the message
`net` produces. `rand` is there because RFC 6455 requires the sixteen bytes of
`Sec-WebSocket-Key` and the four-byte masking key of every client frame to be
unpredictable. A module holds exactly what its importer granted it, so a program
that leaves `rand` off does not build, and the refusal names the call inside
`std/ws`.

## Types

```kelp
datac Url(val scheme: String, val host: String, val port: u16, val path: String)
datac Header(val name: String, val value: String)
datac Frame(val fin: bool, val opcode: u8, val data: Bytes)
datac Conn(val fd: i32, var buf: Bytes, var start: usize, var frag_opcode: u8, var frag_data: Bytes)

enum Msg {
    Text(val text: String)
    Binary(val data: Bytes)
    Ping(val data: Bytes)
    Pong(val data: Bytes)
    Close(val code: u16, val reason: String)
}
```

`path` carries the path *and* the query, exactly as `std/http`'s `Url` does.
`Frame` is the layer under `recv`: `recv` is what a caller wants, and the frame
type is public because a shipped module has no privacy. `Conn` holds a descriptor
rather than a `net.Socket`, for the reason `http.Cursor` does, and nothing closes
on drop: `close` is explicit.

Constants: `DEFAULT_PORT` (`80`), `DEFAULT_SCHEME` (`ws`), `WS_GUID`, the
opcodes, `MAX_FRAME` (1048576), `MAX_HEAD` (8192) and `CLOSE_NO_STATUS` (1005).

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `ws.parse_url(s)` | `Url` | splits `ws://host[:port][/path]`, port 80 when it is absent; refuses `wss` by name |
| `ws.connect(host, port, path)` | `Conn` | the HTTP/1.1 upgrade; panics on every refusal below |
| `Conn.send_text(text)` | `Unit` | one masked text frame |
| `Conn.send_binary(data)` | `Unit` | one masked binary frame |
| `Conn.ping(data)` / `Conn.pong(data)` | `Unit` | a control frame; the payload may not exceed 125 bytes |
| `Conn.close(code, reason)` | `Unit` | sends the close frame, then closes the descriptor |
| `Conn.recv()` | `Msg` | `mut`: the next message, or the next control frame |
| `Conn.read_frame()` | `Frame` | `mut`: the frame layer under `recv` |

## The handshake

`connect` sends a `GET` carrying `Upgrade: websocket`, `Connection: Upgrade`,
`Sec-WebSocket-Version: 13` and a `Sec-WebSocket-Key` of sixteen random bytes,
then reads the response. A `101` is accepted only when its
`Sec-WebSocket-Accept` equals the base64 of the SHA-1 of that key plus
`258EAFA5-E914-47DA-95CA-C5AB0DC85B11` (`WS_GUID`), which is what
[`encoding.sha1`](/stdlib/encoding) is there for. The accept value is the stronger
test of the same thing `Upgrade` and `Connection` say: keys are per-connection, so
a peer that is not the one the key was sent to cannot produce the digest.

## Messages and control frames

`recv` assembles a text or binary message across as many continuation frames as
the peer sends and hands back `Msg.Text` or `Msg.Binary`; a caller never sees half
a message. **A control frame is returned, not answered here**: `Ping`, `Pong` and
`Close` arrive as their own variants, and the caller answers a ping with
`conn.pong(payload)` and finishes the closing handshake with
`conn.close(code, reason)`. A control frame that arrives in the middle of a
fragmented message is returned while the partial message stays where it was, so the
next `recv` continues it.

Every client frame is masked, with a fresh masking key. `close` sends one frame
and **does not wait** for the peer's answering `Close`: a caller that wants that
answer reads until it sees `Msg.Close` (or end of file) first. Waiting would block
on a peer that has already gone, and v1 has no way to time that out.

A close frame with **no payload** arrives as `Msg.Close(code = 1005)` with an
empty reason: RFC 6455 7.1.5 reserves `1005` for "no status code was present", so
an absent code and a code of `1005` are the same value here and a caller cannot
tell them apart (`CLOSE_NO_STATUS`). `1005` is also not a code an endpoint may
send, so `close` refuses it: a caller that received one must not send it back.

## Refusals

Panics, not `Result` values, and each case has its own message. A `...` stands for
the number or code the module put there.

| Message | When |
| --- | --- |
| `ws.parse_url: 'wss' is not supported: v1 has no TLS, so only 'ws://' is reachable` | the scheme is `wss` |
| `ws.parse_url: only 'ws' is supported` | any other scheme |
| `ws.parse_url: URL must start with 'ws://' (no scheme found)` | there is no `://` |
| `ws.parse_url: URL has no host` | the authority is empty |
| `ws.parse_url: URL has an empty port` / `ws.parse_url: URL port is not a number` / `ws.parse_url: URL port is out of range` | a port that does not convert |
| `ws.connect: the server answered '...' instead of '101 Switching Protocols'` | a status other than `101` |
| `ws.connect: the 101 response has no Sec-WebSocket-Accept header, so it is not a WebSocket server` | the accept header is missing |
| `ws.connect: Sec-WebSocket-Accept does not match the key this connection sent, so the peer did not compute it from the handshake` | the accept value is computed from another key |
| `ws.connect: the response has no status line, so it is not an HTTP response` | a head that is not HTTP |
| `ws.connect: the status code is not a number` / `ws.connect: the status code is out of range` | a status code that does not convert |
| `ws.connect: the response head did not arrive within 8192 bytes, so the peer is not answering the handshake` | the head is over `MAX_HEAD` |
| `ws.connect: the connection closed before the response head arrived` | the peer closed mid-handshake |
| `ws.recv: the server masked a frame, and RFC 6455 5.1 forbids that for anything but a client` | a masked frame from the server |
| `ws.recv: a continuation frame arrived with no message to continue` | a continuation with nothing open |
| `ws.recv: a data frame arrived while a fragmented message was still open` | an interleaved data frame |
| `ws.recv: a control frame arrived fragmented, and RFC 6455 5.5 forbids that` | a fragmented control frame |
| `ws.recv: a control frame carries more than 125 bytes, and RFC 6455 5.5 forbids that` | an over-long control frame |
| `ws.recv: a close frame with a one-byte payload has no status code (RFC 6455 5.5.1)` | a close payload of exactly one byte |
| `ws.recv: frame opcode 0x... is reserved, so the peer is not speaking RFC 6455` | an unknown opcode |
| `ws.recv: a frame of ... bytes is beyond the 1048576-byte cap this client reads` | a payload over `MAX_FRAME` |
| `ws.recv: the connection closed in the middle of a frame` | end of file mid-frame |
| `ws.ping: a control frame's payload may not exceed 125 bytes` | an over-long ping payload, and the same for `ws.pong` |
| `ws.close: ... is not a status code an endpoint may send (RFC 6455 7.4.1, 7.4.2)` | a code below 1000, or one of 1004, 1005, 1006 and 1015 |
| `ws.close: a close reason may not exceed 123 bytes, because the code it follows takes two of a control frame's 125` | an over-long close reason |

A `Text` frame that is not UTF-8 panics inside `String.from_bytes`, because v1 has
no validating helper that returns a value.

The two capability refusals are the compiler's, not the module's:

- A program that does not grant `rand` does not build: `needs the 'rand'
  capability, which module 'std/ws' was not granted`.
- A connect to a host outside the `net` grant is denied at run time:
  `'example.com:80' is outside the net capability granted to module 'std/ws'`.

## Example

```kelp
impl "std/ws" caps(net = ["gateway.example.com:80"], rand = [])

fun main() {
    val u = ws.parse_url("ws://gateway.example.com/socket")
    var c = ws.connect(u.host.as_str(), u.port, u.path.as_str())
    c.send_text("hello")
    when c.recv() {
        Text(t) -> print(t)
        Ping(d) -> c.pong(d)
        Close(code, reason) -> print("closed ${code}")
        else -> print("other")
    }
    c.close(1000, "done")
}
```

## Notes

- **`wss://` is refused by name**, because v1 has no TLS; `std/http`'s client has
  the same limit for `https`. Nothing about the framing depends on the transport,
  which is why the client ships first.
- **Not here, deliberately:** a server, extensions
  (`Sec-WebSocket-Extensions`, so `permessage-deflate` and the `zlib-stream`
  transport a compressed gateway asks for), subprotocols
  (`Sec-WebSocket-Protocol`), redirects, automatic reconnect, and waiting for the
  peer's answering `Close` inside `close`.
- `parse_url` splits the port at the first `:`, so an IPv6 literal is not
  expressible here, the same rule `net`'s capability patterns follow.
- A frame above `MAX_FRAME` (1048576 bytes) is a protocol error rather than an
  allocation of whatever the peer announced, and a head above `MAX_HEAD` (8192
  bytes) is refused the same way.

## See also

- [`std/encoding`](/stdlib/encoding): `sha1`, which the accept check is built on
- [`std/net`](/stdlib/net): the socket layer this client is written over
- [`std/http`](/stdlib/http): the other client, and the same TLS limit for `https`
- [Capability patterns](/reference/capability-patterns)
