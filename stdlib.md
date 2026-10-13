---
title: "Standard library"
description: "The standard library ships inside the kelpc binary as Kelp sources, so the text functions are reviewable Kelp rather than a C blob. It is imported with impl \"std/<module>\"; a module that touches..."
isPublished: true
tags: "stdlib"
---
One page per `std/*` module, the capability domain each one needs, and the compiler builtins.

## Pages

- [`std/arena`](/stdlib/arena): a bump arena over a caller-owned byte region, usable freestanding.
- [`std/atomic`](/stdlib/atomic): `Atomic<T>` and the one ordering v1 has.
- [`std/encoding`](/stdlib/encoding): base64, base32, base58, hex and percent encoding.
- [`std/env`](/stdlib/env): `has`, `get`, `set` and `unset` for environment variables (gated on `env`).
- [`std/fmt`](/stdlib/fmt): number, grouping, byte-size and padding formatting, and the `Display` trait.
- [`std/frame`](/stdlib/frame): a physical frame as a capability, `frame.claim(addr)` (gated on `frames`).
- [`std/fs`](/stdlib/fs): read, write, walk and metadata (gated on `fs`).
- [`std/http`](/stdlib/http): an HTTP/1.1 client and server, with the `try_` variants (needs `net` delegated).
- [`std/io`](/stdlib/io): `File`, `BufReader`, `print` and `eprint`.
- [`std/irq`](/stdlib/irq): an interrupt line as a capability, `irq.claim(n)` (gated on `irq`).
- [`std/list`](/stdlib/list): closure-shaped helpers over `List<T>`: `map`, `filter`, `each`, `find_index`, `any`, `all`.
- [`std/math`](/stdlib/math): `sqrt`, `pow`, trigonometry and `abs`, `min`, `max`, `clamp`.
- [`std/mem`](/stdlib/mem): raw allocation: `mem.alloc`, a zero-filled `Bytes`.
- [`std/net`](/stdlib/net): TCP connect, listen, accept, send and receive (gated on `net`).
- [`std/option`](/stdlib/option): `Option<T>` and its free-function combinators.
- [`std/path`](/stdlib/path): lexical path handling.
- [`std/pool`](/stdlib/pool): a fixed thread pool (hosted builds only; refused on current `main`).
- [`std/process`](/stdlib/process): `args`, `spawn`, `run` and `exit` (gated on `process`).
- [`std/rand`](/stdlib/rand): unseeded `u64`, `below` and `bytes` (gated on `rand`).
- [`std/regex`](/stdlib/regex): a linear-time regular expression engine.
- [`std/result`](/stdlib/result): `Result<T, E>` and its free-function combinators.
- [`std/source`](/stdlib/source): the `file` and `line` of the Kelp call site.
- [`std/str`](/stdlib/str): text search, slicing, splitting, parsing and formatting.
- [`std/sync`](/stdlib/sync): `Mutex`, `RwLock`, `Condvar` and channels (hosted builds only; channels build on current `main` inside one thread).
- [`std/sys`](/stdlib/sys): `os()` and `arch()`, the build target's names.
- [`std/thread`](/stdlib/thread): `spawn`, `join`, `fence`, `sleep_ms` and `current_id`.
- [`std/time`](/stdlib/time): `now_unix`, `now_mono_ns` and `sleep_ms` (gated on `time`).
- [`std/tls`](/stdlib/tls): client and server TLS, with the `tlsfile` PEM reads (needs `net` delegated).
- [`std/trace`](/stdlib/trace): opt-in stderr events and timed spans (gated on `time`).
- [`std/tz`](/stdlib/tz): TZif time zones and a `strftime` subset (gated on `fs` and `env`; hosted only).
- [`std/ws`](/stdlib/ws): a WebSocket client (RFC 6455) over `ws://` and `wss://` (needs `net` and `rand` delegated).
- `std/ops`, `std/convert` and `std/iter` have no page of their own: they are documented in the language chapter, in [Operator traits](/language/operator-traits), [Generic traits, `From` and `?`](/language/generic-traits) and [Iterators](/language/iterators).

The standard library ships **inside the `kelpc` binary** as Kelp sources, so the
text functions are reviewable Kelp rather than a C blob. It is imported with
`impl "std/<module>"`; a module that touches the outside world needs the domain
**delegated on the `impl` line**.

`std/internal/...` is reserved for compiler implementation modules. It is not
part of the public library: a project cannot import it or place its own source
under that path.

```kelp
impl "std/fs"                                          // needs fs
impl "std/net" caps(net = ["api.example.com:443"]) // names the host it may dial
impl "std/str"                                          // needs nothing
```

The domain each module needs comes from the compiler's own table
(`kelpc/src/stdlib.rs::domain_of`):

| Module | Domain | Notes |
| --- | --- | --- |
| `std/mem` | - | `alloc` |
| `std/str` | - | text: search, slice, split, parse, format |
| `std/path` | - | lexical path handling |
| `std/sys` | - | `os()` and `arch()`: the build target's names |
| `std/math` | - | `sqrt`, `pow`, trig, `abs`/`min`/`max`/`clamp` |
| `std/fmt` | - | number, grouping, byte-size and padding formatting into `String`, and the `Display` trait |
| `std/encoding` | - | base64, base32, base58, hex and percent encoding |
| `std/regex` | - | a linear-time regular expression engine (freestanding with the allocator pair) |
| `std/io` | - | `File`, `BufReader`, `print`/`eprint` |
| `std/fs` | `fs` | read, write, walk, metadata |
| `std/process` | `process` | `args`, `spawn`, `run`, `exit` |
| `std/net` | `net` | TCP connect/listen/accept, `send`/`recv`, and the `try_connect`/`try_send_all`/`try_recv`/`try_recv_into` value returns |
| `std/http` | `net` (held) | an HTTP/1.1 client and server; the client speaks `http` and `https`, the server is HTTP/1.1 (plain, or HTTPS through `serve_tls`) with request limits and worker threads. Ungated itself, but importing it needs `net` delegated. The `try_get`/`try_send` family returns `HttpErr` |
| `std/tls` | `net` (held) | client and server TLS: a typed `TlsError`, a private CA, a `try_` family, truncation detection, `ServerOptions`/`tls.accept`, ALPN and client certificates. Wraps a socket, never dials its own |
| `std/tlsfile` | `fs` | `read_pem(path, what)`: the one gated file read behind `std/tls`'s PEM-bytes functions |
| `std/ws` | `net`, `rand` (both held) | a WebSocket client (RFC 6455) over `ws://` and `wss://`; importing it needs both delegated |
| `std/time` | `time` | `now_unix`, `now_mono_ns`, `sleep_ms` |
| `std/source` | - | `file`, `line` at the Kelp call site |
| `std/trace` | `time` | opt-in stderr events and timed spans, with explicit source locations |
| `std/tz` | `fs`, `env` | TZif time zones: the offset at an instant, the wall clock it names, the `One`/`Ambiguous`/`Gap` answers and a `strftime` subset; hosted only |
| `std/rand` | `rand` | unseeded `u64`, `below`, `bytes` |
| `std/env` | `env` | `has`, `get`, `set`, `unset` |
| `std/list` | - | `map`, `filter`, `each`, `find_index`, `any`, `all` |
| `std/option` | - | `Option<T>` and its combinators |
| `std/result` | - | `Result<T, E>` and its combinators |
| `std/arena` | - | a bump arena over a caller-owned byte region; pure pointer arithmetic, so it needs no allocator and works freestanding |
| `std/irq` | `irq` | an interrupt line as a capability: `irq.claim(n)` is the only constructor, checked against the calling module's `irq` grant |
| `std/frame` | `frames` | a physical frame as a capability: `frame.claim(addr)` is the only constructor, checked against the calling module's `frames` grant and 4 KiB-aligned |
| `std/atomic` | - | `Atomic<T>` and the one ordering v1 has |
| `std/thread` | - | `spawn`, `join`, `fence(order)`, `sleep_ms`, `current_id` and the `ThreadErr` a join hands back |
| `std/sync` | - | `Mutex<T>`, `RwLock<T>` and `Condvar` through scoped blocks, plus channels (`sync.bounded`, `sync.unbounded`, `Sender`, `Receiver`) and `Mutex.share`/`swap`; hosted only; channels build on current `main` inside one thread (see the page) |
| `std/pool` | - | a fixed thread pool: `pool.new`, `Pool.spawn`, `join`, `panicked`; hosted only; refused on current `main` (see the page) |
| `std/iter` | - | the `Iterator` trait `for` walks, `Range`, and `count`/`sum_i64`/`collect_list` |
| `std/ops` | - | the operator traits `Add`, `Sub`, `Mul`, `Div`, `Rem`, `Neg` and `Ord` |
| `std/convert` | - | the `From<T>` and `Into<T>` traits; `?` converts a failure through `From` |
| `std/rt` | - | the compiler's own runtime module (the capability matcher), injected for a program that imports a gated module; not part of the stdlib surface |

## Compiler builtins

These are generated by the compiler, not the standard library, and need no
`impl`:

| Type | Methods |
| --- | --- |
| `String` | `empty`, `with_capacity`, `from_str`, `from_bytes`, `push`, `push_str`, `reserve`, `clear`, `len`, `char_count`, `is_empty`, `clone`, `into_bytes`, `as_str`, `view` |
| `Bytes` | `empty`, `from_str`, `push`, `append`, `reserve`, `clear`, `len`, `is_empty`, `get`, `set`, `clone`, `as_str` |
| `View` | `len`, `is_empty`, `get`, `slice`, `eq`, `to_string` (see [Text](/language/text)) |
| `List<T>` | `empty`, `of`, `len`, `is_empty`, `get`, `set`, `push`, `pop`, `insert`, `remove`, `clear`, `sort`, `reverse`, `contains`, `slice`, `clone` |
| `Map<K, V>` | `new`, `with_capacity`, `empty`, `len`, `is_empty`, `insert`, `get`, `get_or`, `has`, `remove`, `keys`, `values`, `clear` |
| `Box<T>` | `empty`, `of`, `is_empty`, `get`, `set`, `take` |
| `Ptr<T>` | the raw pointer: `null`, `from_addr`, `from_ref`, `from_mut`, `from_fn`, `addr`, `is_null`, `offset`, `byte_offset`, `cast`, `read`, `write`, `read_volatile`, `write_volatile`, `read_unaligned`, `write_unaligned`, `alloc`, `try_alloc`, `free`. Every access needs `unsafe` (see [Unsafe code and raw pointers](/language/unsafe)) |
| `Atomic<T>` | `new`, `load`, `store`, `swap`, `compare_exchange`, `fetch_add`/`sub`/`and`/`or`/`xor` |
| `Mutex<T>` | `new`, `lock`, `wait_while`, `wait_while_timeout`, `share`, `swap`, `into_inner` (see [`std/sync`](/stdlib/sync)) |
| `RwLock<T>` | `new`, `read`, `write`, `try_read`, `try_write`, `into_inner` (see [`std/sync`](/stdlib/sync)) |
| `Condvar` | `new`, `notify_one`, `notify_all` (see [`std/sync`](/stdlib/sync)) |

The builtins are described in [Text](/language/text) and
[Collections](/language/collections).

## Conventions

Two conventions worth knowing before reading a page:

- **A `str` parameter takes a borrowed view.** A `String` needs `.as_str()`;
  a literal needs nothing.
- **`Option`/`Result` have no methods.** Every combinator is a free function in
  `std/option` / `std/result`: `option.unwrap(o = maybe)`, `result.is_err(r)`.

[Back to the home page](/)
