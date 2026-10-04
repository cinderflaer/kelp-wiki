---
title: "`std/tls`"
description: "Client and server TLS: typed `TlsError`, `try_` family, private CAs, `ServerOptions`, `tls.accept`, ALPN, mutual TLS with client certificates, `std/tlsfile` for PEM files, truncation detection and `wss`. Gated on net."
isPublished: true
tags: "stdlib, networking, tls"
---
Client and server TLS. This is what makes `https://` work in
[`std/http`](/stdlib/http) and `wss://` work in [`std/ws`](/stdlib/ws), and what
lets a program serve TLS itself ([Serving TLS](#serving-tls) below); a client that
only fetches URLs never imports it directly.

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
the check already works. The server side follows the same rule: `tls.accept`
takes the socket `net.accept` returned.

## Types

```kelp
datac TlsStream(val fd: i32, val handle: TlsHandle)

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

pub datac TlsOptions(val ca_pem: Bytes, val timeout_ms: u64)
```

`TlsOptions.ca_pem` is the PEM text of extra trusted CA certificates (empty means
the system store only). It is bytes, never a path: the TLS runtime does not open
files, so a module that holds only `net` cannot make the handshake read one. To
read a CA file, use `tlsfile.ca_pem(path)` ([below](#reading-the-files-stdtlsfile)),
which goes through the `fs` capability.

`TlsStream` pairs a plain `fd` with the OpenSSL handle bound to it, not a
`net.Socket`, because a `net.Socket` and its `TlsStream` would then be two owners
of one descriptor. The value is not `Copy`, so there is never a silent second
free of the handle. `shutdown` ends only the TLS session (sending
`close_notify` where the connection allows it) and frees the OpenSSL handle; it
does not close `fd`. The caller closes the socket itself afterward with
`net.close(net.Socket(fd = t.fd))`. Nothing closes on drop, the same rule
`net.Socket` and `net.Listener` follow.

`handle` is an `extern type`, `pub extern type TlsHandle`, not a `usize`. The
opaque OpenSSL `SSL*` crosses as a value the type system keeps whole: a handle
can be produced only by the library, not forged from an integer, compared with
one, or confused with a different handle type, so the accidental
integer-to-pointer path is gone. A std module the compiler ships may declare one
(`stdlib.rs`'s source table is what admits it, since its extern bodies come from
`externs.rs` rather than a manifest); a project module still needs its own
`coral.toml` `[extern."<module id>"]` section. `TlsHandle` is `Copy`, owns
nothing and has no drop, so a handle can still outlive the `try_shutdown` that
freed its `SSL`; the type buys spelling, not liveness. `try_shutdown` remains
the call that frees the `SSL*`, and `std/http`/`std/ws` carry the plain-or-TLS
choice as an `Option<TlsHandle>`, so `None` is the "no handle" value and no
integer sentinel has to stand in for one.

## Functions

Every call has a fallible form returning `Result<_, TlsError>` and a panicking
wrapper that panics with the error's own text.

| Fallible | Panicking | Returns | Notes |
| --- | --- | --- | --- |
| `try_handshake(s, host)` | `handshake(s, host)` | `Result<TlsStream, TlsError>` / `TlsStream` | the TLS handshake over an already-connected socket |
| `try_handshake_with(s, host, opts)` | `handshake_with(s, host, opts)` | as above, with `TlsOptions` | private CA bytes, timeout |
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

## Serving TLS

The server side is the same OpenSSL as the client, linked only by a program that
reaches `std/tls`, and hosted only. Verification stays on in both directions (see
[below](#certificate-verification-is-not-optional)).

```
tls.server_config_pem(cert_chain_pem: Bytes, key_pem: Bytes).R: Result<ServerConfig, TlsError>
tls.server_config_pem_with(cert, key, opts: &ServerOptions).R: Result<ServerConfig, TlsError>

tls.server_options().R: ServerOptions
ServerOptions.min_version(v: TlsVersion) -> ServerOptions       // Tls12 (default) | Tls13
ServerOptions.alpn(protocols: &List<String>) -> ServerOptions   // the server's preference order
ServerOptions.require_client_cert_pem(ca_pem: Bytes) -> ServerOptions
ServerOptions.handshake_timeout_ms(ms: u64) -> ServerOptions    // default 10000, 0 waits forever
ServerConfig.free()

tls.accept(config: &ServerConfig, s: net.Socket).R: Result<TlsStream, TlsError>
TlsStream.alpn().R: Option<String>                // negotiated protocol, server and client streams
TlsStream.peer_cert_subject().R: Option<String>   // RFC 2253 subject of the peer's certificate

// std/tlsfile
tlsfile.read_pem(path: &str, what: &str).R: Result<Bytes, TlsError>
tlsfile.ca_pem(path: &str).R: Result<Bytes, TlsError>   // read_pem with the role "CA certificate"
```

- **A configuration is built once from PEM bytes and never changes.** The
  options are a value (`ServerOptions`) given at build time, not mutators on a
  built config, so a new certificate means a new `ServerConfig`. It wraps one
  `SSL_CTX`, which OpenSSL lets every thread make sessions from, so one config is
  shared by reference between workers. `ServerConfig.free()` ends it; like every
  handle in this module, nothing is freed on drop, and sessions already made from
  it keep working until they end.
- **The certificate chain goes leaf first**, as PEM text. The key is a plain
  (unencrypted) PEM private key.
- **`TlsOptions` stays two fields.** ALPN and a client certificate live in
  `TlsClientOptions` (`tls.client_options()`, then `.alpn(...)`,
  `.client_cert_pem(cert, key)`, `.with_ca_pem(bytes)`, `.with_timeout_ms(...)`),
  used with `tls.try_handshake_opts(s, host, &opts)`.
- **`TlsError` has no new variant.** A file that cannot be read is `Io`; a
  malformed PEM, a key that does not match the certificate, a CA file with no
  certificate in it, an ALPN mismatch and a handshake an mTLS server refuses are
  `HandshakeFailed`; a client certificate from another CA is `Untrusted` and an
  expired one `Expired`, the same verify codes the client reports.
- **`net.Socket`, not a stream.** `tls.accept` takes the socket `net.accept`
  returns, and the descriptor lives on in the returned `TlsStream`.

### Reading the files: `std/tlsfile`

Reading a file is the `fs` capability, and a module that names `fs.try_read`
needs the `fs` grant from every program that imports it. Every `https` client
imports `std/tls`, so `std/tls` cannot hold `std/fs`. It takes PEM *bytes*, and
`std/tlsfile` holds the one gated read, which a program grants on its own line:

```kelp
impl "std/tlsfile" caps(fs = ["/etc/myapp/certs/**"])
```

`tlsfile.read_pem(path, what)` returns the bytes or `TlsError.Io` whose text names
the role (`what`) and path: `tls: cannot read the private key file <path>: No
such file or directory`. `std/tlsfile` cannot call `std/tls` (those functions are
`net`-gated and would need that grant too), so the program composes the two:

```kelp
val cert = tlsfile.read_pem(cert_path, "certificate chain")?
val key = tlsfile.read_pem(key_path, "private key")?
val cfg = tls.server_config_pem(cert, key)?
```

The same module reads a private CA for a client, which is how a client trusts a
server whose certificate was not issued by a public CA:

```kelp
val ca = tlsfile.ca_pem("/etc/myapp/certs/ca.pem")?
val opts = tls.client_options().with_ca_pem(ca).with_timeout_ms(10000)
```

**`ca_file` and `ca_dir` are gone.** Earlier releases took a CA *path* in
`TlsOptions(ca_file, ca_dir, timeout_ms)` and `TlsClientOptions.with_ca_file`, and
the handshake opened the path itself, with no `fs` check: a module holding only
`net` could make the client read any PEM path and learn from the result whether
verification succeeded (item 9 of the
[capability threat model](/reference/capability-threat-model#the-nine-fixed-holes)). Now a module
that wants a CA from a file needs `std/tlsfile`, which needs an `fs` grant; a
module with no `fs` grant is refused at compile time ("needs the 'fs'
capability"), and a path outside the grant is the ordinary `fs` denial and is
never opened. A directory of CAs (`ca_dir`) has no bytes form; read the
certificates you want and concatenate the PEM text. The old spellings are compile errors on both backends (checked on 2026-10-04):

```text
error: datac 'std.tls.TlsClientOptions' has no method 'with_ca_file'
```

and importing `std/tlsfile` without delegating `fs` is refused with
`'std.fs.try_read' needs the 'fs' capability, which module 'std/tlsfile' was not
granted; the module that imports this one must delegate it (`impl "<this module>"
caps(fs = ["<pattern>"])`)`. To migrate, replace
`.with_ca_file(path)` with `.with_ca_pem(tlsfile.ca_pem(path)?)` and
`TlsOptions(ca_file = ..., ca_dir = ..., timeout_ms = ...)` with
`TlsOptions(ca_pem = ..., timeout_ms = ...)`.

### Making a test certificate

`kelpc/tests/tls_server.rs` builds its certificates with the `openssl` command
line tool (and prints `skipped: no openssl` when it is missing). The same recipe,
a throwaway CA, a `localhost` server certificate and a client certificate, all
two-day:

```sh
printf 'subjectAltName=DNS:localhost\nbasicConstraints=CA:FALSE\n' > server.ext
printf 'extendedKeyUsage=clientAuth\nbasicConstraints=CA:FALSE\n' > client.ext
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
  -keyout ca.key -out ca.pem -subj "/CN=Kelp Test CA" -days 2 \
  -addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
  -keyout server.key -out server.csr -subj "/CN=localhost"
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
  -out server.pem -days 2 -extfile server.ext
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes \
  -keyout client.key -out client.csr -subj "/CN=kelp-client"
openssl x509 -req -in client.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
  -out client.pem -days 2 -extfile client.ext
chmod 600 *.key
```

The server certificate names `localhost`, and the client verifies the host name
it passes to the handshake, so connect to `localhost`, not to the address.

### Configuration errors are values, with fixed sentences

A bad configuration is a typed error and never a panic, and **the key never
appears in an error text**: the C code reports a fixed sentence for key
problems and clears OpenSSL's error queue after those calls instead of passing
OpenSSL's own text along. This program feeds `server_config_pem` a good pair, a
key from a different certificate, a file that is not PEM as the key, a file that
is not PEM as the certificate, and a path that does not exist:

```kelp
impl "std/tls"
impl "std/tlsfile" caps(fs = ["/etc/myapp/certs/**"])
impl "std/result"

fun say(e: move tls.TlsError) {
    val text = tls.error_text(e)
    print(text.as_str())
}

fun try_pair(cert_file: &str, key_file: &str) {
    val cert = tlsfile.read_pem(cert_file, "certificate chain")
    val key = tlsfile.read_pem(key_file, "private key")
    when cert {
        Err(e) -> say(e)
        Ok(c) -> when key {
            Err(e) -> say(e)
            Ok(k) -> when tls.server_config_pem(c, k) {
                Ok(cfg) -> {
                    print("config ok")
                    cfg.free()
                }
                Err(e) -> say(e)
            }
        }
    }
}

fun main() {
    try_pair("/etc/myapp/certs/server.pem", "/etc/myapp/certs/server.key")
    try_pair("/etc/myapp/certs/server.pem", "/etc/myapp/certs/other.key")
    try_pair("/etc/myapp/certs/server.pem", "/etc/myapp/certs/junk.pem")
    try_pair("/etc/myapp/certs/junk.pem", "/etc/myapp/certs/server.key")
    try_pair("/etc/myapp/certs/server.pem", "/etc/myapp/certs/missing.key")
}
```

I ran this program with the directory replaced by a scratch directory holding the
files above (`other.key` being a second key, `junk.pem` the text `this is not a
PEM file`), on the LLVM backend and under `KELPC_ORACLE=c`. Both print:

```text
config ok
the private key does not match the certificate
the private key is malformed (or encrypted: encrypted keys are not supported)
the certificate chain is not a valid PEM certificate
tls: cannot read the private key file <dir>/missing.key: No such file or directory
```

(`<dir>` stands for the scratch directory in the last line.) An **encrypted key is
therefore refused**: decrypt it first, and keep the plain key readable by the
serving user only. The library does not check the key file's permissions, and the
PEM bytes are read into ordinary memory that is not zeroed.

### ALPN, client certificates and `peer_cert_subject`

ALPN: the server selects the first of *its* protocols that the client also
offered. No overlap is a fatal `no_application_protocol` alert, a
`HandshakeFailed` on both sides. A client that offers none, or a server with none
configured, negotiates none and `alpn()` is `None`. A name that is empty or longer
than 255 bytes is not a protocol and makes the configuration fail.

`require_client_cert_pem(ca_pem)` makes the server verify client certificates
against the CAs in that PEM text **and refuse a connection that has none**; text
with no certificate in it is rejected when the configuration is built. On the
accepted side, `peer_cert_subject()` is the authenticated client.

One program, server and client on two threads over `127.0.0.1`. The server
prefers `h2` then `http/1.1` and requires a client certificate; the client offers
`http/1.1` then `h2`, and presents its certificate only when the first argument is
`cert`. The server reads the request before it closes (closing with it unread
would reset the connection):

```kelp
impl "std/net" caps(net = ["127.0.0.1:*"])
impl "std/tls"
impl "std/tlsfile" caps(fs = ["/etc/myapp/certs/**"])
impl "std/thread"
impl "std/process"
impl "std/result"
impl "std/option"
impl "std/str"

fun show(o: move option.Option<String>).R: String = when o {
    Some(v) -> v
    None -> String.from_str("-")
}

fun make_config().R: result.Result<tls.ServerConfig, tls.TlsError> {
    val cert = tlsfile.read_pem("/etc/myapp/certs/server.pem", "certificate chain")?
    val key = tlsfile.read_pem("/etc/myapp/certs/server.key", "private key")?
    val ca = tlsfile.read_pem("/etc/myapp/certs/ca.pem", "client CA")?
    var protos: List<String> = List.empty()
    protos.push(String.from_str("h2"))
    protos.push(String.from_str("http/1.1"))
    val opts = tls.server_options().alpn(&protos).require_client_cert_pem(ca)
    return tls.server_config_pem_with(cert, key, &opts)
}

fun serve_one(fd: i32).R: String {
    val l = net.Listener(fd = fd)
    return when make_config() {
        Err(_) -> String.from_str("server: config failed")
        Ok(cfg) -> {
            var line = String.from_str("server: no client")
            when net.try_accept(l) {
                Ok(sock) -> {
                    when tls.accept(&cfg, sock) {
                        Ok(t) -> {
                            val proto = show(t.alpn())
                            val who = show(t.peer_cert_subject())
                            line = String.from_str("server: alpn=")
                            line.push_str(proto.as_str())
                            line.push_str(" peer=")
                            line.push_str(who.as_str())
                            // read the request before closing, or the close resets the connection
                            val req = tls.try_read(t, 16)
                            val w = tls.try_write_all(t, Bytes.from_str("ok"))
                            val sd = tls.try_shutdown(t)
                        }
                        Err(_) -> line = String.from_str("server: handshake refused")
                    }
                    net.close(sock)
                }
                Err(_) -> {}
            }
            cfg.free()
            line
        }
    }
}

fun client(port: u16, with_cert: bool).R: String {
    var opts = tls.client_options().with_timeout_ms(10000)
    when tlsfile.ca_pem("/etc/myapp/certs/ca.pem") {
        Ok(pem) -> opts = opts.with_ca_pem(pem)
        Err(_) -> {}
    }
    var protos: List<String> = List.empty()
    protos.push(String.from_str("http/1.1"))
    protos.push(String.from_str("h2"))
    opts = opts.alpn(&protos)
    if with_cert {
        val c = tlsfile.read_pem("/etc/myapp/certs/client.pem", "client certificate")
        val k = tlsfile.read_pem("/etc/myapp/certs/client.key", "client private key")
        when c {
            Ok(cp) -> when k {
                Ok(kp) -> opts = opts.client_cert_pem(cp, kp)
                Err(_) -> {}
            }
            Err(_) -> {}
        }
    }
    val s = net.connect("127.0.0.1", port)
    var line = String.empty()
    when tls.try_handshake_opts(s, "localhost", &opts) {
        Ok(t) -> {
            // TLS 1.3 lets the client finish first, so a refused client
            // certificate shows on its first read.
            val w = tls.try_write_all(t, Bytes.from_str("hi"))
            when tls.try_read(t, 16) {
                Ok(b) -> {
                    line = String.from_str("client: got ")
                    val text = String.from_bytes(b)
                    line.push_str(text.as_str())
                }
                Err(_) -> line = String.from_str("client: refused after handshake")
            }
            val sd = tls.try_shutdown(t)
        }
        Err(_) -> line = String.from_str("client: handshake refused")
    }
    net.close(s)
    return line
}

fun main() {
    val args = process.args()
    val mode = args.get(1)
    val with_cert = str.eq(mode.as_str(), "cert")
    val l = net.listen(0)
    var lm = net.Listener(fd = l.fd)
    lm.set_timeout(10000)
    val port = l.port()
    val h = thread.spawn(serve_one, l.fd)
    val seen = client(port, with_cert)
    print(seen.as_str())
    when thread.join(h) {
        Ok(s) -> print(s.as_str())
        Err(_) -> print("server thread failed")
    }
    l.close()
}
```

I ran it on both backends with `/etc/myapp/certs` replaced by the scratch
directory (the real `caps(fs = [...])` pattern must be an absolute path, so the
grant carries the same directory). With a certificate (`./prog cert`) both
backends print:

```text
client: got ok
server: alpn=h2 peer=CN=kelp-client
```

and without one (`./prog nocert`):

```text
client: refused after handshake
server: handshake refused
```

Twelve further runs of each (six per backend) printed the same lines every time.
The server picked `h2`, its own first choice, although the client listed
`http/1.1` first.

## Failures a server sees

These are the outcomes `kelpc/tests/tls_server.rs` pins on both backends (client
line, then server line):

| Scenario | Client | Server |
| --- | --- | --- |
| echo, default options | ok, `alpn=-` | ok, `alpn=-` |
| ALPN, client lists `http/1.1`, `h2`; server prefers `h2` | `alpn=h2` | `alpn=h2` |
| ALPN, only `http/1.1` in common | `alpn=http/1.1` | `alpn=http/1.1` |
| ALPN with nothing in common | `HandshakeFailed` | `HandshakeFailed` |
| server has no ALPN, client offers some | ok, `alpn=-` | ok, `alpn=-` |
| mTLS, certificate from the configured CA | ok | ok, `peer=CN=kelp-client` |
| mTLS, no client certificate | an error value (on its handshake, or its first read under TLS 1.3) | `HandshakeFailed` |
| mTLS, client certificate from another CA | an error value | `Untrusted` |
| server certificate for another host name | `HostMismatch` | `HandshakeFailed` |
| expired server certificate | `Expired` | `HandshakeFailed` |
| peer sends data, then ends without `close_notify` | second read is `PeerClosedUncleanly` | - |

`ServerOptions.min_version(Tls13)` raises the floor for a server; TLS 1.2 is the
default, and there is no way to go lower.

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

The same holds on the server: it only ever *adds* `SSL_VERIFY_PEER` together with
`SSL_VERIFY_FAIL_IF_NO_PEER_CERT` when a client CA is given, and a peer that ends
without `close_notify` is `PeerClosedUncleanly` on a server stream too. There is
no `insecure` flag on either side. What there is, is a way to *add* a private CA:
`TlsOptions(ca_pem = ..., timeout_ms = ...)` adds the certificates in the PEM
bytes to the verification store (the runtime never opens a path). It can never
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

- [`std/http`](/stdlib/http) for `http.serve_tls` and `http.try_get_tls`
- [`std/ws`](/stdlib/ws)
- [`std/net`](/stdlib/net)
- [Capability patterns](/reference/capability-patterns)
