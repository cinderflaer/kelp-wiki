---
title: "`std/tls`"
description: "Client-side TLS for https. Gated on net, the same domain std/net and std/http already hold - not a new capability."
isPublished: true
tags: "stdlib, networking, tls"
---
Client-side TLS (MK5-S4b-M1). This is what makes `https://` work in
[`std/http`](/stdlib/http); most programs never import it directly.

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
that is read/write on the wrapped stream. The dial stays in `std/http.kp`,
where the check already works.

## Types

```kelp
datac TlsStream(val fd: i32, val handle: usize)
```

`handle` is the OpenSSL `SSL*`, carried as a `usize` (v1 has no raw pointer
type). It is opaque outside this module; nothing else needs to know its shape.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `handshake(s: net.Socket, host: &str)` | `TlsStream` | performs the TLS handshake over an already-connected socket |
| `write(t, data)` | `usize` | one write, may be partial |
| `write_all(t, data)` | `usize` | loops until everything is written |
| `read(t, max)` | `Bytes` | up to `max` bytes |
| `read_into(t, buf, at)` | `usize` | fills an existing buffer from offset `at` |
| `shutdown(t)` | `Unit` | closes the TLS session (not the underlying socket) |

All five panic on failure, the same style as [`std/net`](/stdlib/net)'s
`send`/`recv`/`close`.

## Certificate verification is not optional

The system trust store, `SSL_VERIFY_PEER`, and hostname verification against
the name the caller wrote to `handshake` (the same name the `net` grant was
checked against, not whatever the DNS resolution turned it into) are all on
unconditionally, and TLS 1.2 is the floor. A self-signed or mismatched
certificate is a handshake failure, not a silent connection. There is no
`insecure` flag: v1 has nowhere reviewable to put one that would not look like
a footgun left lying around for the next reader to trip on.

## Linking

The system OpenSSL (`-lssl -lcrypto`) is linked into every Kelp binary
unconditionally, the same "an unused library is free to link" reasoning
`-lm` already uses for `std/math` — there is no per-project opt-in and no
extra `coral.toml` line needed.

## See also

- [`std/http`](/stdlib/http)
- [`std/net`](/stdlib/net)
- [Capability patterns](/reference/capability-patterns)
