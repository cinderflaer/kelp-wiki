---
title: "`std/ws`"
description: "A WebSocket client (RFC 6455) over ws:// and wss://. It holds net for the socket and rand for the handshake key and every masking key, so an import delegates both."
isPublished: true
tags: "stdlib, networking"
---
A WebSocket **client** (RFC 6455), over `ws://` and `wss://`. It holds `net` and `rand`.

Source section:
[`syntax.md` §16.18](/design/syntax).

```kelp
impl "std/ws" caps(net = ["gateway.example.com:80"], rand = [])
```

`std/ws` is Kelp over [`std/net`](/stdlib/net), [`std/tls`](/stdlib/tls) (for
`wss://`) and [`std/encoding`](/stdlib/encoding): no compiler change and no
dependency beyond the system TLS library `std/tls` already links.
**Two domains, because the module has two needs.** `net` reaches the socket, and
its half of the check is the host-and-port check `net.connect` already gives: the
grant matches the host as written and the port beside it, before name resolution
runs, and a call for anything else is denied at the connect or the fallible dial
with the message `net` produces. `rand` is there because RFC 6455 requires the
sixteen bytes of `Sec-WebSocket-Key` and the four-byte masking key of every client
frame to be unpredictable. A module holds exactly what its importer granted it, so a program
that leaves `rand` off does not build, and the refusal names the call inside
`std/ws`.

## Types

```kelp
datac Url(val scheme: String, val host: String, val port: u16, val path: String)
datac Header(val name: String, val value: String)
datac Frame(val fin: bool, val opcode: u8, val data: Bytes)
datac Conn(val fd: i32, var buf: Bytes, var start: usize, var frag_opcode: u8, var frag_data: Bytes)

enum WsErr {
    Dial(val reason: String)
    Handshake(val status: i32, val reason: String)
    Tls(val reason: String)
}

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

## A refused dial or handshake is a value

`ws.connect` returns `Err(WsErr)` for three of the refusals below, so a caller can
tell a network failure from a peer that answered something other than `101` from
a `wss` peer that would not do TLS. `WsErr.Dial(reason)` is the network half and
carries what `net.connect` gave back, the text of the dial failure. `WsErr.Handshake(status, reason)` is a peer that answered: `status` is what
it answered with and `reason` is the message `ws.connect` panics with for it. A
`101` whose `Sec-WebSocket-Accept` does not match the key this connection sent is
`Handshake` too, with `status` of `101`, because it is a handshake failure rather
than a network one. `WsErr.Tls(reason)` is the `wss` half, and `reason` is
`tls.error_text`'s sentence for the refused handshake or certificate. The
distinction is what a reconnecting caller needs: nothing
listening is worth another attempt, a peer answering `403` usually is not, and a
peer that is not speaking TLS is not a WebSocket server at all.

```kelp
val refused = ws.connect("127.0.0.1", port, "/gateway")
when refused {
    Err(e) -> {
        when e {
            Dial(reason) -> print("dial refused ${reason}")
            Handshake(status, reason) -> print("handshake ${status} ${reason}")
            Tls(reason) -> print("tls refused ${reason}")
        }
    }
    else -> print("connected")
}
```

A caller for whom the refusal is fatal writes `result.expect(ws.connect(...), "...")`,
which panics with the message the program gives. The shape is `std/process`'s
`run`, with the error as a named type (`ProcErr`).

**The gap, stated rather than hidden.** `Dial`, `Handshake` and `Tls` are the
only value cases, because each carries a network reason, a status or the TLS
half's own sentence. A response whose
head is not HTTP at all, a status code that does not convert, a head that overruns
`MAX_HEAD` and a peer that closes mid-handshake have no status to report and
`WsErr` has no arm to hold them, so they **still panic inside `ws.connect`**,
with the same messages `connect` uses. A caller cannot branch on them.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `ws.parse_url(s)` | `Url` | splits `ws://` or `wss://` `host[:port][/path]`; the port defaults to 80 for `ws` and 443 for `wss` |
| `ws.default_port_for(scheme)` | `u16` | the scheme's default port, `80` for `ws` and `443` for `wss` |
| `ws.connect(host, port, path)` | `Result<Conn, WsErr>` | the plain-`ws` HTTP/1.1 upgrade: a refused dial, a refused `wss` handshake and a non-`101` answer are values, the errors with no status still panic |
| `ws.connect_url(u)` | `Result<Conn, WsErr>` | `connect` for a parsed URL, so the scheme (`wss`) comes off `u` |
| `ws.connect_scheme(scheme, host, port, path)` | `Result<Conn, WsErr>` | `connect` with the scheme spelled out |
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

Each case has its own message. The dial failures, the `wss` handshake failures
and the answers with a status are values (`WsErr.Dial`, `WsErr.Tls`,
`WsErr.Handshake`), and the rest still panic. A `...` stands for
the number or code the module put there.

| Message | When |
| --- | --- |
| `ws.parse_url: only 'ws' and 'wss' are supported` | any other scheme |
| `ws.parse_url: URL must start with 'ws://' or 'wss://' (no scheme found)` | there is no `://` |
| `ws.parse_url: URL has no host` | the authority is empty |
| `ws.parse_url: URL has an empty port` / `ws.parse_url: URL port is not a number` / `ws.parse_url: URL port is out of range` | a port that does not convert |
| `net.connect: connection failed`, with a second line `  errno N: ...` | the dial failed: nothing is listening, or every resolved address refused (`WsErr.Dial`) |
| `net.connect: cannot resolve host`, with a second line `  getaddrinfo: ...` | the host does not resolve (`WsErr.Dial`) |
| the `tls.error_text` sentence, such as `tls: the peer does not speak TLS 1.2 or newer` | the `wss` handshake or certificate check failed (`WsErr.Tls`; the same sentence through `connect`) |
| `ws.connect: the server answered '...' instead of '101 Switching Protocols'` | a status other than `101` (`WsErr.Handshake`; a panic through `connect`) |
| `ws.connect: the 101 response has no Sec-WebSocket-Accept header, so it is not a WebSocket server` | the accept header is missing (`WsErr.Handshake`; a panic through `connect`) |
| `ws.connect: Sec-WebSocket-Accept does not match the key this connection sent, so the peer did not compute it from the handshake` | the accept value is computed from another key, `status` of `101` included (`WsErr.Handshake`; a panic through `connect`) |
| `ws.connect: the response has no status line, so it is not an HTTP response` | a head that is not HTTP (a panic in both forms, because there is no status to report) |
| `ws.connect: the status code is not a number` / `ws.connect: the status code is out of range` | a status code that does not convert (a panic in both forms) |
| `ws.connect: the response head did not arrive within 8192 bytes, so the peer is not answering the handshake` | the head is over `MAX_HEAD` (a panic in both forms) |
| `ws.connect: the connection closed before the response head arrived` | the peer closed mid-handshake (a panic in both forms) |
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
impl "std/result"

fun main() {
    val u = ws.parse_url("ws://gateway.example.com/socket")
    var c = result.expect(ws.connect(u.host.as_str(), u.port, u.path.as_str()), "connect")
    c.send_text("hello")
    when c.recv() {
        Text(t) -> print(t)
        Ping(d) -> c.pong(d)
        Close(code, _) -> print("closed ${code}")
        else -> print("other")
    }
    c.close(1000, "done")
}
```

## Notes

- **`wss://` is the same client over TLS.** `connect_url` (and `connect_scheme`)
  takes the scheme off the URL and
  wrap the dialed socket in a [`std/tls`](/stdlib/tls)
  session before the WebSocket handshake, checking the certificate against the
  host as written, exactly as `https` does. The `net` grant is the same
  host-and-port check (`caps(net = ["gateway.example.com:443"], rand = [])`);
  TLS needs nothing beyond it. A failed TLS handshake or certificate check is
  `WsErr.Tls`, carrying `tls.error_text`'s sentence. `connect` stays plain-`ws`.
- **A refused dial is a value, a head that is not HTTP is not.**
  `ws.connect` returns `WsErr.Dial` for a dial that failed, `WsErr.Tls` for a
  `wss` handshake or certificate refusal and
  `WsErr.Handshake` for a peer that answered something other than `101`, so a
  reconnect loop can tell them apart. The errors that carry no status (a head that
  is not HTTP, a status code that does not convert, a head over `MAX_HEAD`, a peer
  that closes mid-handshake) still panic inside `connect`, because `WsErr` has
  no arm for them.
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
