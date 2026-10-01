---
title: "Limits in v1"
description: "Source section - syntax.md \u00a717. Most are settled for good; a few are open work tracked on the roadmap, marked (open) below."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §17](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).
Most of these are settled design decisions, each with a workaround in this
documentation. A few are gaps nobody has ruled out for good, they are tracked
on [the roadmap](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/roadmap.md)
and may ship later. Those are marked **(open)**, with the item that tracks
them.

## Control flow

- **No `break` and no `continue`.** Iteration is a `for` over a `List`, or a
  `while` plus an index when the loop is not a front-to-back walk.
- No `loop` expression, no labelled loops.

## Errors

- **`?` propagates only an identical failure type.** There is no error
  conversion, no `From`, no boxing. `result.map_err` is the bridge.
- A function returning `Unit` has nowhere to propagate to.

## Data and generics

- **A tuple is read by destructuring and nothing else.** There is no positional
  access on a value (`t.0`), no tuple pattern in `when`, no destructuring `for`
  binding, and no tuple value in a `const` initializer. A tuple has two or more
  elements, so there is no one-element tuple: `(T)` is the type `T`, and `()` is
  refused by name. Bind the whole tuple to a `val` when its positions need to be
  visible separately. See [Types](/language/types).
- **No extra type parameters on a method.** A `datac`, an `enum` and a `fun` may
  each declare type parameters, but a receiver on a generic type must write the
  type's own parameters, in order: `fun Pair<A, B>.first()`. A method cannot add
  parameters of its own. See [Generics and type parameters](/language/generics).
- **A generic `enum`'s template carries no method.** A concrete `enum` may declare
  a receiver method and a value of the type calls it (`val e = E.A`, then
  `e.tag()`); a receiver that builds the variant names a type, so `E.A.tag()` is
  refused. The `Map` key pair below is such a method, and the combinators over
  `Option` and `Result` are free functions because those two are generic.
- **A `Map` key must be keyable.** The compiler derives the key's hash and
  equality from the fields, so the derived set is `String`, an integer, `bool`,
  `char`, or a `datac`/`enum`/tuple whose every field, variant payload or
  position is itself keyable. A `datac` or `enum` outside that set becomes a key
  by declaring both `fun T.hash().R: u64` and `fun T.eq(other: &T).R: bool`,
  which the map calls instead of a derived pair; the key is still cloned into the
  entry, so the type has to be deep-copyable. A float is refused (`nan`), and a
  `Bytes`, container, view, borrow or `datac`/`enum` with a field outside the set
  is refused with a message naming that field or the half of the pair that is
  missing.
- **No user overloading** (permanent: `abs`, `min`, `max`, `clamp` are the
  only overloads in the language, and they are stdlib-only). User `extern`
  bodies bind to real symbols (MK9-S1-M1, roadmap B-1): a `coral.toml`
  `[extern."<module id>"]` section assigns a user module one of the seven
  capability domains (`ui` included) plus a native library, a `header`,
  `include_dirs`/`library_dirs`, an optional `pkg_config` package and an
  allowlisted symbol set, so its `extern fun` declarations bind a real C
  symbol under a name the section can rename, gated exactly like a stdlib
  module. `extern type` handles with parents, `null()`/`cast()`, `...`
  variadics and `move closure(...)` callbacks all ship; see
  [User FFI](/language/externs) and
  [Coral: the manifest](/tooling/coral#extern-user-modules-that-bind-a-native-symbol).
  **(still open)** `extern "C"` block syntax, function-pointer types for user
  externs, and a `repr(C)` struct crossing by value.

## Ownership

- **A partial move takes one projection of an owned local.** `val xs = bag.xs`
  moves that field out of an owned `val`/`var` local or a `move T` parameter, and
  the binding keeps the fields that stayed. An owned `enum` payload read by value
  out of an owned place is the same partial move, which is what a `when`/`if let`
  over an owned place does with the payload it binds. A position of a tuple read
  out of an owned binding is the same partial move, and read out of a borrow it
  is refused. A projection read out of a
  borrowed structure or out of a nested place is still refused.
- **The helpers whose receiver stays a borrow are `Copy`-only.** `option.unwrap`
  on an `Option<String>` and `result.map` over a `Result<T, MyErr>` take their
  receiver with `move` now, so both work. `option.or_else`, `result.unwrap`,
  `result.unwrap_or`, `result.unwrap_err`, `result.expect`, `result.expect_err`,
  `result.and_then`, `result.or_else` and `list.filter` over a `List<String>`
  read through a borrow and rebuild what they hand back, so the payload (or the
  accepted element) must be `Copy`.
- **No references (and no `View`) in fields, `List` elements, `Map` values,
  array elements or `Box` contents.** Text you must store is a `String`; a view
  is taken at the point of use.
- A `View` never becomes a `str`: a slice has no NUL after it, so `str.len`/
  `str.eq` on one would read past the slice. Take `v.to_string()`.

## Containers

- **A `List` element and a `Box` element may be a `List` or a `Box`;** a `Map`
  value and an array element may not be a container at all, and every container
  refuses a borrow, a `str`, a `View`, an atomic, a function value and `Unit` as
  an element. A map that holds a list, or a named row, wraps the inner one in a
  one-field `datac` (as `csv.Row`, `listx.Chunk`, `table.Row` do).
- **`[T; N]` is fixed at its written length.** There is no `[T; 0]`, no `a[i]`
  subscript (write `.get`/`.set`, as on a `List`) and no growth. The repeat form
  `[x; N]` copies `x` into every slot, so its element has to own nothing, which
  is the one array shape a `datac` element cannot take: write the elements out,
  or start from a literal and `set` each one. An array cannot be a `List` or
  `Map` element, and an array element cannot be a `List`, `Map` or `Box`.
- **(open, roadmap A-5)** No iteration protocol: `for` is a desugared index
  walk over a `List` or an array, and a `Map` has no iterator: iterate
  `keys()` and look up. A reusable `iter`/`next` protocol is an open question
  with no schedule, not a closed decision: the cheap `for` shipped in
  MK8-S1-M3 and has been enough so far, and nothing has asked for the more
  expensive protocol yet.

## Compile-time evaluation

- **A `const` is the same language, not a second one.** Its initializer may use
  the operators, `if`, an integer conversion, other `const`s, and a call to a
  plain `fun` whose own body stays inside that set. There is no `comptime`
  block, no compile-time `List`/`Map`, and no `size_of`/`align_of`; a builtin, an
  `extern fun` and a method call are all out of reach, so `str.len("x")` cannot
  be a constant.
- Evaluation is bounded: one million steps and sixty-four nested calls, and
  exceeding either is a diagnostic. A constant that calls a function is running
  inside the compiler, so the function has to terminate on the values the
  constant gives it.

## Networking

- **(decided 2026-09-26, roadmap item 37; done, MK5-S4b-M1)** TLS shipped:
  [`std/tls`](/stdlib/tls) links the system OpenSSL, and `http.parse_url` now
  accepts `https`, and `ws.parse_url` accepts `wss` (`ws.connect_secure` runs the
  WebSocket handshake over the same TLS layer).
- **`std/ws` is a client, not a server.** Not scheduled anywhere on the
  roadmap: a WebSocket server, extensions (`Sec-WebSocket-Extensions`, so
  `permessage-deflate` and the `zlib-stream` transport a compressed gateway
  asks for), subprotocols (`Sec-WebSocket-Protocol`), redirects, automatic
  reconnect, and waiting for the peer's answering `Close` inside `close`. A
  caller that wants that answer reads until it sees `Msg.Close` or end of file
  first, because waiting would block on a peer that has already gone and v1
  has no way to time that out.
- **`ws.parse_url` splits the port at the first `:`**, so an IPv6 literal is not
  expressible, the same rule `net`'s capability patterns follow.
- A WebSocket frame above `MAX_FRAME` (1048576 bytes) is a protocol error rather
  than an allocation of whatever the peer announced, and a response head above
  `MAX_HEAD` (8192 bytes) is refused the same way.

The two clients carry these limits by decision, not by accident: `std/http` is
[`syntax.md` §16.12](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md)
and `std/ws` is §16.18 of the same document.

## Concurrency

- **Real threads exist, with a move-only crossing rule.** `thread.spawn(entry,
  arg)` in [`std/thread`](/stdlib/thread) starts an OS thread, and
  `thread.join(handle)` waits for it and consumes the handle, handing back `Ok`
  with the worker's value or `Err` with the panic text. An owned argument is
  **moved** into the worker, and the single borrow that may cross is a shared
  borrow of a `pd` whose pointee has no reachable `var` field. `Atomic<T>` in
  [`std/atomic`](/stdlib/atomic) is one location every access to which is a
  single atomic operation, and it satisfies that rule by construction, so a
  `pd val` atomic is the shared counter a worker and its joiner both reach. A
  `&mut T`, a `str`, a `View`, a frame local's `&T` and a `datac` with a
  reachable `var` field are all refused. The workers are OS threads rather than
  green ones, and a program that needs isolation rather than sharing still
  spawns a process.
- **One ordering, and nothing else around it.** The single ordering v1 has is
  `SeqCst`; `Relaxed`, `Acquire` and `Release` are reserved, not shipped. There
  are no channels, no async and no coroutines, with no roadmap item tracking
  any of the three yet. **(open)** `Mutex` and thread-local storage are
  different: both are named backlog items (`Mutex` alongside the threads work;
  thread-local storage as B-11, MK9-S3-M3) rather than ruled out, they are
  simply not built. Per-CPU storage has shipped: `percpu static mut` lays out
  `[target] cpus` copies and `cpu_index()`/`cpu_count()` read it back, in a
  freestanding build only; see [Per-CPU storage](/language/percpu). Today's one
  shared-mutable shape for hosted threads is `Atomic<T>`; a worker that needs to
  share something bigger takes its own copy instead, the way
  `examples/download_pool.kp` gives each thread its own `http.Pool`. Two leaks
  are admitted: a panicking worker's frame is abandoned, and a handle nobody
  joins is detached with its worker record leaked, because v1 has no `must_use`.
  A user `Drop` now exists ([User `Drop`](/language/drop)), but it does not run
  on the panic path: there is still no unwinding. A worker that returns `unit`
  joins to `Result<unit, ThreadErr>` with nothing in its `Ok`, the same shape
  `None` already has.
  `thread.fence(order)` in [`std/thread`](/stdlib/thread) joins the total order
  while naming no location, and changes nothing a single-threaded program can
  observe. [Concurrency in v1](/language/concurrency) has the model as it
  stands and what it still does not have.

## Text

- `str.to_upper`/`to_lower` are **ASCII-only**.
- A string is UTF-8 by convention and bytes by API: most functions count bytes and
  the codepoint helpers are the separate `char_*` set.
- No regular expressions anywhere. [`glob`](/libraries/glob) has `*`/`?`,
  and that is the whole pattern language.

## Not present at all

**Settled for good**, with no roadmap item working toward them: no
exceptions, no garbage collector, no macros, no operator overloading. These
are the headline design, not gaps: ownership without a GC, `Result` instead
of throwing, and text substitution (`kelpc`'s aliases) instead of a hygienic
macro system.

**(open)** The rest of this list is absent from v1 today but is either an
active roadmap item or a named future milestone, not a closed decision:

- **Provenance and address-space control.** `unsafe`, raw pointers and the
  layout and data-format surface the kernel path needed have shipped
  (`unsafe` blocks and `unsafe fun`, `Ptr<T>` with
  `offset`/`byte_offset`/`cast`/`addr`, volatile and unaligned access,
  `alloc`/`free` and the fallible `try_alloc`, `repr(c)`/`repr(packed)`/
  `repr(align(N))`, `size_of`/`align_of`/`offset_of`, the byte-order
  conversions, the `[unsafe] modules` gate, and the [`std/arena`](/stdlib/arena)
  bump region): see [Unsafe code and raw
  pointers](/language/unsafe). `from_addr` names an address, and a freestanding
  module must hold an `mmio` grant to do it, but there is still no provenance or
  address-space model, which is why a granted range admits any address reachable
  from it by arithmetic. `AtomicPtr`, `transmute` and a read of a non-`Copy`
  element are absent too.
- **Traits, interfaces, `dyn` dispatch.** A-12. Slice 1 already shipped (a
  `datac`/`enum` can declare its own `hash`/`eq` pair, and a concrete `enum`
  can declare a receiver method); named traits and dynamic dispatch are slice 2
  and beyond, unscheduled but named. A user `Drop` is a smaller thing that
  shipped on its own, `fun mut T.drop()`, and is not a trait; see
  [User `Drop`](/language/drop).
- **Lifetime syntax, and the borrows it would allow in fields.** A-11/A-8.
  This is why a `str`/`View` cannot be a `datac` field or an `enum` payload
  today, and why a closure cannot capture a borrow: both need a way to say
  what a stored borrow is tied to, which v1 does not have yet.
- No undefined-behaviour escape hatch: `unsafe` marks the operations the
  compiler cannot check, it does not make undefined behaviour allowed, the same
  way Rust's `unsafe` does not.
- **Named nested functions.** No roadmap item names this one at all, closures
  (a `fun` literal capturing a binding) shipped instead and cover most of
  what a nested function would be for; a named one that can recurse or be
  referenced before its own definition is simply an unanswered question
  rather than a decision either way.

## See also

- [Concurrency in v1](/language/concurrency)
- [Pitfalls](/language/pitfalls)
- [Ownership and borrowing](/language/ownership)
- [Collections](/language/collections)
