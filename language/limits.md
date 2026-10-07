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

- **`break` and `continue` exist** and act on the innermost loop, in a `while`
  and in either `for`. There is **no `loop` expression, no labelled loop and no
  `break` with a value**, and a deferred action cannot contain either
  ([Iterators, `for` and `break`](/language/iterators)).

## Errors

- **`?` converts a failure only through a `From` impl.** An identical failure
  type is moved across as is; a different one needs
  `impl convert.From<E1> for E2`, and the operator calls `E2.from(e1)`. There is
  no boxing, no blanket `Into`, and `?` never consults `Into`. `result.map_err`
  is still the bridge for a one-off conversion
  ([Generic traits, `From` and `?` conversion](/language/generic-traits)).
- A function returning `Unit` has nowhere to propagate to.

## Source size and shape

- **Nesting is capped at 200 levels, and a chain at 800 links.** The parser
  refuses more than 200 levels of expressions, prefix operators, types, type
  arguments, blocks and binding patterns inside one another, and more than 800
  links in an operator or access chain, with an ordinary error
  (`this nests more than 200 levels deep ...`, `this chain of operators or
  accesses is longer than 800 links ...`). Written code is nowhere near either.
  See [Front-end fuzzing and parser limits](/tooling/fuzzing).

## Compile time

Large generated programs (long method chains, deeply nested calls and generics,
nested blocks, 300-arm `elif` ladders, 200-field `datac`s, a 5,000-element list
literal) are built on both backends by `kelpc/tests/scaling.rs`, and a step over
20 seconds fails the test. The notes are
[`plan/scaling.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/scaling.md).

- **Long method chains and nested generic calls take linear time now.** Type
  checking used to infer a method call's receiver twice (once to find its type,
  once as the `self` argument), so each link doubled the work of the link below:
  `a.f().f().f()...` took 0.4 s at 16 links and 21 s at 22 (the plan's figures),
  and a chain of 400 never finished. Arguments of a generic call or a generic
  `datac`/`enum` construction were checked twice in the same way, so
  `id(id(id(...)))` was exponential too. The checker keeps the first result and
  reuses it; no program that was accepted or refused changed, and no diagnostic
  did. A 400-link chain of a `datac` method (`x.inc().inc()...`) passes `kelpc
  check`, and built with the prebuilt compiler (LLVM, default `-O2`) in about
  0.2 s and printed `400`.
- **The parser limits are the real ceiling.** The parser refuses more than 800
  links in a chain and more than 200 levels of nesting
  ([Front-end fuzzing and parser limits](/tooling/fuzzing)), so a 400-link chain, 90
  nested calls and 60 nested `if` blocks are about the largest shapes a program
  can reach. Both limits were kept.
- **A very large array literal is slow at `-O2`.** (open) Every other generated
  shape finishes each step in about a second or less. A literal of 5,000
  elements takes 4.0-4.6 s to build on the LLVM backend at `-O2` in the plan's
  debug-build measurement, 2,500 elements 1.0 s and 1,250 elements 0.5 s: the time
  grows with the square of the length and sits inside LLVM's optimizer, which is
  handed the literal as one `[N x i32]` aggregate value (`-O0` takes 0.85 s for
  5,000). The all-constant literal is now emitted as one constant array, which
  halved `-O0` and left `-O2` unchanged. Emitting it as a private global plus a
  copy would remove the rest, and was left alone because it changes the IR of
  every array literal. Re-measured for this page with the release-built prebuilt
  compiler: a 5,000-element `[i32; 5000]` literal took about 2.9 s at `-O2` and
  about 0.5 s at `-O0`. Split a table that big into smaller literals or build it
  with a loop.
- Smaller costs the plan lists, all linear: 150 chained closures take about 1 s on
  LLVM and 1.6-2.2 s on the C oracle, and 50 nested generic enum constructions
  take 1.1-1.5 s.

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

## Scoped blocks

A trailing block (`f { x -> ... }`) passes a `scoped fun(...)` parameter, and it
may write what it captures ([Trailing blocks and scoped
parameters](/language/functions#trailing-blocks-and-scoped-parameters)). The
limits of that rule:

- **A block cannot be stored**, returned or put in a container: a scoped value is
  a type of its own and lives exactly as long as the call it was written in. A
  retained callback (a button's `on_click`) is still a message value, not a block.
- **A block inside a block cannot capture the outer block's exclusive capture**,
  even to read it. The message names the two ways out: pass the name to the inner
  call as an argument, or capture it in the outer function.
- **One owner, one exclusive capture per call.** A second capture of the same
  owner in the same call, a call whose other arguments or receiver mention the
  owner, and a borrow of the owner still used after the call are all refused.
- **Borrow roots are whole variables**, so a block writing `s.count` while the
  callee borrows `s.items` conflicts: there is no disjoint-field capture.
- A block that writes through an exclusive capture **cannot return a borrow**
  (`str`, `View`, `&T`); return an owned value.
- A general hole older than this rule is still open: two reborrows of one `mut`
  *parameter* in one ordinary call (`g(s, s)` with two `mut` parameters) are not
  checked. The block case is closed; the plain call is not.
- `kelpc fmt` has no rule for re-wrapping a trailing block yet (open item 75).

## Feature interactions

Every pair of the 2026-10 language features that had not been tested together is
a fixture (`matrix_*.kp`) run on both backends. Each cell either works with its
output pinned or is refused with a message that says what to do next:

| Pair | Result |
| --- | --- |
| associated types with `Box<dyn>` | refused by name: use a bounded type parameter (`<T: Source>`) instead |
| generic traits with operator traits | refused: `ops.Add` takes no type argument, the right-hand side is always `&Self`, so there is no `impl Add<Vec2> for Vec2` |
| iterators with `defer` | works: a `defer` in a loop body runs once per iteration, including the one a `return` leaves; a function-level `defer` runs last |
| iterators with const generics | limit: `impl Iterator for Ring<3>` is a trait for a generic instantiation, refused; wrap it in a non-generic cursor `datac` that walks the `Ring<N>` through a generic function |
| `From` with `?` inside an iterator's `next` | refused where the shapes differ (`next` returns an `Option`, so `?` there can only propagate `None`); convert in a helper that returns a `Result` and turn the failure into `None` with a `when` |
| `Display` with a generic function | works: `<T: fmt.Display>` calls `to_text`, and the same value interpolates in a template |
| `Ord` with `Map` keys | works, and `Ord` is never consulted: a declared `hash`/`eq` (or the derived field-wise pair) decides key identity, so an `Ord` that calls every pair equal still leaves two keys in the map |
| operator traits in a freestanding build | works: `std/ops` is in the freestanding allowed set |

## Ownership

- **A partial move takes one projection of an owned local.** `val xs = bag.xs`
  moves that field out of an owned `val`/`var` local or a `move T` parameter, and
  the binding keeps the fields that stayed. An owned `enum` payload read by value
  out of an owned place is the same partial move, which is what a `when`/`if let`
  over an owned place does with the payload it binds. A position of a tuple read
  out of an owned binding is the same partial move, and read out of a borrow it
  is refused. A nested owned field path is supported: it moves only its final
  field, leaving sibling fields readable; a borrowed structure is still refused.
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
- **The iterator protocol shipped, the adapters did not.** `for` walks a `List`,
  an array, or any type that implements `std/iter`'s `Iterator`. There is no
  `map`, `filter`, `take`, `skip`, `enumerate`, `zip` or `chain`, no
  `List.iter()` or `List.into_iter()`, and a `Map` still has no iterator
  (iterate `keys()` and look up). **(open)** The adapters need a generic trait
  impl (`impl<I: Iterator> Iterator for Take<I>`), which the parser does not
  accept yet ([Iterators, `for` and `break`](/language/iterators)).

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

- **`std/http` also serves HTTP/1.1.** The server is pure Kelp over `std/net`,
  with a `Limits` table, keep-alive, pipelining, chunked and
  `Expect: 100-continue` request bodies, and `serve_threaded` worker threads.
  **A listener binds the interface its grant allows:** `net.listen(port)` has no
  host argument, so a loopback-only grant (`127.0.0.1:8080`) binds `127.0.0.1`
  and a grant that includes `*` binds every interface
  ([threat model](/reference/capability-threat-model)); `net.listen_on(host,
  port)` names the host and is checked on `host:port` like `connect`. `net.mono_ms`, `net.try_accept`,
  `Listener.set_timeout` and `net.try_shutdown_write` exist for it.
- **(decided 2026-09-26, roadmap item 37; done, MK5-S4b-M1)** TLS shipped:
  [`std/tls`](/stdlib/tls) links the system OpenSSL, and `http.parse_url` now
  accepts `https`, and `ws.parse_url` accepts `wss` (`ws.connect_url` runs the
  WebSocket handshake over the same TLS layer, taking the scheme off the parsed
  URL).
- **TLS also serves.** [`std/tls`](/stdlib/tls#serving-tls) builds a
  `ServerConfig` from PEM bytes (`tls.server_config_pem`), accepts with
  `tls.accept`, negotiates ALPN, and can require client certificates (mutual
  TLS); [`std/http`](/stdlib/http#serving-https) serves HTTPS with
  `http.serve_tls`. Its limits: verification cannot be turned off on either
  side; `tlsfile.read_key` checks a key file's permissions and `read_pem` does
  not; an encrypted private key takes `ServerOptions.key_password`;
  `ServerConfig.reload_pem` swaps the certificate for new handshakes;
  `serve_tls` binds every interface (bind a host with `http.listen_on` and
  `serve_tls_on`); and the HTTP server speaks HTTP/1.1 only,
  so ALPN names a protocol but does not make the server speak `h2`.
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
  are no async and no coroutines, with no roadmap item tracking either yet.
  **Channels and a thread pool have shipped**, hosted only:
  `sync.bounded`/`sync.unbounded` with `Sender<T>` and `Receiver<T>` in
  [`std/sync`](/stdlib/sync#channels), and [`std/pool`](/stdlib/pool). A channel
  carries owned borrow-free values only, has no `select` and no zero-capacity
  form, and `send` returns an `Option` the compiler does not force a caller to
  read; a pool creates one thread per job, so it bounds concurrency rather than
  thread creation.
  `Mutex`, `RwLock` and `Condvar` have shipped ([`std/sync`](/stdlib/sync));
  thread-local storage is still a named backlog item (B-11, MK9-S3-M3) rather
  than ruled out, it is simply not built. Per-CPU storage has shipped: `percpu static mut` lays out
  `[target] cpus` copies and `cpu_index()`/`cpu_count()` read it back, in a
  freestanding build only; see [Per-CPU storage](/language/percpu). Today's shared-mutable shapes for hosted threads are `Atomic<T>`,
  `Mutex<T>`, `RwLock<T>` and `Condvar`, and values move between threads over a
  channel; a worker that needs to share something else still takes its own
  copy instead, the way
  `examples/download_pool.kp` gives each thread its own `http.Pool`. Two leaks
  are admitted: a panicking worker's frame is abandoned, and a handle nobody
  joins is detached with its worker record leaked (a bare `thread.spawn(...)` statement is refused, but a handle bound to a `val` and never joined still leaks). `must_use fun` exists ([Functions](/language/functions#must_use)); `Sender.send` carries it.
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
- **No regular-expression literals in the language.** Patterns are data, so a
  regex is [`std/regex`](/stdlib/regex): a linear-time Pike VM over bytes with a
  documented subset, freestanding with the `[target] alloc`/`dealloc` pair.
  [`glob`](/libraries/glob)
  still has the `*`/`?` shell patterns.

## Not present at all

**Settled for good**, with no roadmap item working toward them: no
exceptions, no garbage collector, no macros. These are the headline design, not
gaps: ownership without a GC, `Result` instead of throwing, and text
substitution (`kelpc`'s aliases) instead of a hygienic macro system. Operators
are overloaded only through the `std/ops` traits on a `datac`/`enum`
([Operator traits and `Display`](/language/operator-traits)); there is no
`derive`, no bitwise or `&&`/`||` overloading and no user operator trait.

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
- **Traits: what is still absent.** A-12. Named traits shipped in slices:
  static dispatch and bounds, default methods, supertraits and builtin impls,
  the borrowed trait object `&dyn Name`, [associated types](/language/associated-types),
  [generic traits and `From`](/language/generic-traits), the owned
  [`Box<dyn Name>`](/language/box-dyn), the [operator traits and
  `Display`](/language/operator-traits), and
  [`impl Trait` in argument position](/language/const-generics); see
  [Traits and static dispatch](/language/traits). What is still absent: an upcast
  between trait objects, `where` clauses, blanket impls, generic impls
  (`impl<T: A> B for Pair<T>`, which is also what blocks the iterator adapters),
  a bound or equality constraint on an associated type in a bound
  (`I: Iterator<Item = i64>`), default or generic associated types and
  associated consts, generic trait methods, `impl Trait` in a return position,
  `dyn` of a generic trait or of a trait with an associated type, `dyn` in a
  field or a return type when it is a `&dyn`, and the rest of the refusal list
  on those pages. A user `Drop` is a smaller thing that shipped on its own,
  `fun mut T.drop()`, and is not a trait; see [User `Drop`](/language/drop).
- **Const generics: value parameters only.** `<const N: usize>` shipped
  ([Const generics](/language/const-generics)); arithmetic on the parameter
  inside a type (`[T; N + 1]`), a const parameter on a trait and a non-integer,
  non-`bool` const parameter are refused.
- **Lifetime syntax, and the borrows it would allow in fields.** A-11/A-8.
  Two of A-11's pieces have shipped: a bound borrow ends at its last use rather
  than at the end of its scope, and a reference binding remembers the owner its
  value came from, so a pointer local can walk a structure as a cursor
  ([Ownership and borrowing](/language/ownership#cursors-and-provenance)).
  A direct text-view binding may promote its temporary owner, and a `datac` may
  store `str`/`View` when construction moves its String/Bytes owner into an
  earlier field of the same value. What stays out is explicit lifetime syntax
  (`'a`), enum-payload and container borrows, raw reference fields, and closures
  that capture a borrow.
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
