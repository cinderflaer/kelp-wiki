---
title: "lines_server"
description: "A two-process line protocol - a server that turns PING into PONG and QUIT into BYE, and a client that drives it. This is the example to read before writing anything that talks over TCP."
isPublished: true
tags: "example, networking"
---
A two-process line protocol: a server that turns `PING` into `PONG` and `QUIT`
into `BYE`, and a client that drives it. This is the example to read before
writing anything that talks over TCP.

| | |
| --- | --- |
| Sources | [`src/lines_server.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/lines_server.kp), [`src/lines_client.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/lines_client.kp) |
| Needs | `lineproto = "Lilly/fpl/lineproto"`, with `net` delegated |
| Shows | `net.listen` and `net.accept`, a CRLF reader, a granted host on both sides |

## The dependency and the grants

```toml
[dependencies]
lineproto = "Lilly/fpl/lineproto"
```

Both programs delegate `net`, and both name the host they use. The library holds
what its consumer grants it, and it calls `net.send_all` and `net.recv` on a
socket the consumer already connected.

```kelp
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])
```

## The server

```kelp
impl "std/net"
impl "std/str"
impl "std/process"
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])

fun port_from(argv: &List<String>).return: u16 {
    if argv.len() >= 2 {
        val parsed = str.parse_i64(argv.get(1).as_str())
        if let Ok(v) = parsed {
            return v.to_u16()
        }
    }
    return 4599
}

fun main() {
    val argv = process.args()
    val port = port_from(argv)
    val listener = net.listen(port)
    print(listener.port())

    val sock = net.accept(listener)
    var reader = lineproto.new_reader(sock)
    var serving = true
    while serving {
        val line = reader.read_line()
        if let Some(text) = line {
            if str.eq(text.as_str(), "PING") {
                lineproto.send_line(sock, "PONG")
            } else if str.eq(text.as_str(), "QUIT") {
                lineproto.send_line(sock, "BYE")
                serving = false
            } else {
                val reply = str.concat("ERR unknown: ", text.as_str())
                lineproto.send_line(sock, reply.as_str())
            }
        } else {
            serving = false
        }
    }

    net.close(sock)
    listener.close()
}
```

The loop serves **one** connection and exits, which is what makes the example
runnable from a shell. A real server wraps the accept in another loop, and that is
the only structural difference.

## The client

```kelp
impl "std/net"
impl "std/str"
impl "std/process"
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])

fun port_from(argv: &List<String>).return: u16 {
    if argv.len() >= 2 {
        val parsed = str.parse_i64(argv.get(1).as_str())
        if let Ok(v) = parsed {
            return v.to_u16()
        }
    }
    return 4599
}

fun main() {
    val argv = process.args()
    val port = port_from(argv)

    val sock = net.connect("127.0.0.1", port)
    var reader = lineproto.new_reader(sock)

    lineproto.send_line(sock, "PING")
    val first = reader.read_line()
    if let Some(text) = first {
        print(text)
    }

    lineproto.send_line(sock, "QUIT")
    val second = reader.read_line()
    if let Some(text) = second {
        print(text)
    }

    net.close(sock)
}
```

## Run it

Two shells, or the server in the background:

```sh
kelpc build lines_server.kp -o lines_server
kelpc build lines_client.kp -o lines_client

./lines_server 4599 &
./lines_client 4599
```

## Output

The server prints the port it bound:

```
4599
```

The client prints the two replies:

```
PONG
BYE
```

## What to take from it

- **`net.listen(0)` asks the system for a free port,** and `Listener.port()` is
  how a program learns which one it got. This example takes the port as an
  argument so the two halves can be started separately.
- **`lineproto` never connects anything.** It sends on, and reads from, a socket
  the caller already holds, which is why the grants are written in the two
  programs rather than in the library.
- **`read_line` returns an `Option`,** and `None` means the peer closed. That is
  the loop's exit condition, so a client that hangs up ends the server rather than
  spinning.
- **The reader buffers what a `recv` overshoots,** so two lines arriving in one
  packet still come back one at a time, in order. A protocol handler never has to
  parse a partial buffer.
- **`send_line` appends CRLF and sends the whole line** with `send_all`, because a
  single `send` may write only part of a buffer.
- **The socket is passed to library calls without being moved.** A parameter is a
  borrow unless it is declared `move`, so `lineproto.send_line(sock, ...)` twice
  and then `net.close(sock)` all work on the same socket.
- **The error reply shows the unknown input,** which is the habit that makes a
  protocol debuggable: `ERR unknown: <what arrived>`.

## See also

- [`lineproto`](/libraries/lineproto) for the library itself
- [`std/net`](/stdlib/net) for sockets, listeners and timeouts
- [Capability patterns](/reference/capability-patterns) for `net` patterns
