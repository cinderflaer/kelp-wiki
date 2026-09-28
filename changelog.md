---
title: "Changelog"
description: "Every release of Kelp, newest first: what the language gained and what the compiler that implements it gained with it. Entries are short; plan/done.md keeps the full milestone record."
isPublished: true
tags: "language, compiler"
---
Every release of Kelp, newest first. The version is the `kelpc` version
(`kelpc version`), the tag is in the
[kelp repository](https://homelabone.xenoo.dev/gittea/Juniper/kelp), and the
release notes and binary asset are on the
[releases page](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases).

A release entry covers **the language and the compiler together**, because in
this project they ship as one artifact: a new construct is a lexer, a parser, a
checker and a backend change at once. Tooling releases have their own pages:
[Coral changelog](/tooling/coral-changelog) and
[Lighthouse changelog](/tooling/lighthouse-changelog).

**Numbering.** Releases are numbered `YY.MM.N`: the two-digit year, the
two-digit month, and the release number *within that month*, starting at `0`.
The first under the scheme is [26.09.0](#26090-2026-09-20), and every release
from it on reports its own number: `kelpc version`, the tag and the release
asset are the same text. Cargo refuses a leading zero in a version component,
so `Cargo.toml` carries the semver-legal `26.9.0` and the printed name pads the
month back.

Nothing released before the scheme is renumbered. The tags `v0.2.0` to `v0.2.3`
were renamed to `v0.1.2` to `v0.1.5` in the pass that introduced it, and each one
keeps the commit and the release asset it was cut with, so those four assets are
still the original builds: running `kelpc-0.1.5-linux-x86_64 version` prints
`kelpc 0.2.3`. The renamed tags stay exactly as they are, and `26.09.0` and every
later release build their own asset from their own tag.

These entries are deliberately short. The authority for what a milestone
actually contained is
[`plan/done.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/done.md);
this page is the index to it.

| Version | Date | Headline |
| --- | --- | --- |
| [26.09.5](#26095-2026-09-28) | 2026-09-28 | `std/tls` and `https`; `coral.toml`'s `[caps]` and `[extern]`; rate-limit headers on `Response`; two assignment leaks fixed; every program now needs OpenSSL to build |
| [26.09.4](#26094-2026-09-26) | 2026-09-26 | the LLVM backend inlines builtin bodies; `Map`'s index halved, `Map.with_capacity`; unrolled loops, `noalias`, `llvm.sqrt.f64`; the benchmark suite published |
| [26.09.3](#26093-2026-09-25) | 2026-09-25 | `thread.sleep_ms`/`current_id`; a unit-returning worker can be joined; concurrent downloads; the memory model published; `kelpc check --text` |
| [26.09.2](#26092-2026-09-24) | 2026-09-24 | `pub` and private by default; tuples; threads; `std/ws`; `caps(*)`; `try_connect` |
| [26.09.1](#26091-2026-09-21) | 2026-09-21 | `llvm` is the compiler; `as name` and `with caps` removed; `-O0` to `-Os` |
| [26.09.0](#26090-2026-09-20) | 2026-09-20 | the `YY.MM.N` scheme; `try_to_<T>`; `std/encoding`; the outdated-syntax register |
| [0.1.5](#015-2026-09-20) | 2026-09-20 | the compiler emits its own x86-64 assembly; `kelpc fmt`; block comments |
| [0.1.4](#014-2026-09-19) | 2026-09-19 | five checker bugs found by a real 807-line program |
| [0.1.3](#013-2026-09-19) | 2026-09-19 | a literal takes its sibling operand's type on either side |
| [0.1.2](#012-2026-09-19) | 2026-09-19 | `View`, `char` literals, bitwise operators, `str` to `String` coercion |
| [0.1.1](#011-2026-09-19) | 2026-09-19 | the `for` loop, `spawn_in`/`run_in`, fallible `try_run`, `fs.symlink` |
| [0.1.0](#010-no-release) | 2026-09-19 | first tag: the core language, modules, containers, capabilities, stdlib |

## 26.09.5 (2026-09-28)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v26.09.5)
· 22 commits · 203 unit tests, 488 fixtures green.

**`https` works.** [`std/tls`](/stdlib/tls) ships a client-side TLS module and
`std/http`'s `parse_url` accepts `https://` (default port 443) instead of
refusing it by name. It is gated on the existing `net` domain, so a program that
already writes `impl "std/http" caps(net = [...])` needs nothing new. `std/tls`
never dials a socket, because a grant resolves one hop from the importing
program, so `std/http` hands it an already-connected `net.Socket`. Certificate
verification is unconditional and there is no insecure escape hatch. See
[`std/tls`](/stdlib/tls) for the new build requirement below.

**Every program needs OpenSSL to build now, TLS or not.** The link line carries
`-lssl -lcrypto` for every program, and a program that reaches any `extern`
object has OpenSSL's headers included in its generated `<out>.externs.c`. So a
program that never imports `std/tls` still needs the libraries to link and the
development output to compile. [Install and
build](/getting-started/install#requirements) lists both, and `nix-shell
shell.nix` supplies them.

**A project can restrict the entry module's own authority.** `coral.toml` gains
`[caps]`, which uses the same vocabulary as a `caps(...)` clause on an `impl`
line. A clause on one of `main`'s own `impl` lines grants the imported module,
never `main`, so until now `main` always held everything. A domain omitted from
`[caps]` is a resolution error at any reference to it in `main`, the same error
an ungranted imported module gets. No `[caps]` section means exactly the old
behaviour, so every existing `coral.toml` is unaffected.

**A user module can bind a native symbol.** `coral.toml` gains
`[extern."<module id>"]`: one of the six existing capability domains, a native
`library`, and an allowlisted `symbols` set, checked and gated exactly like a
stdlib module. `extern "C"` block syntax, variadics, function-pointer types and
link vocabulary beyond one library per section are still not there.

**`Response` carries the rate-limit headers.** `retry_after()` returns the
`Retry-After` header's seconds form and `rate_limit()` bundles the
`X-RateLimit-*` headers. Both are ungated, and the client never sleeps or
retries on its own: the caller reads the parsed headers and decides.

**Two assignment leaks are gone.** `*p = value` and `h.name = s` free the value
they overwrite, pinned under the ASAN and valgrind gates. `if c { b = a }` was
already leak-free.

## 26.09.4 (2026-09-26)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v26.09.4)
· 37 commits · 203 unit tests, 473 end-to-end green.

**The small builtin bodies are inlined.** `Bytes`, `String` and `View`'s `len`,
`is_empty`, `get`, `set`, `push`, `push_str` and `reserve` were calls into a
separately linked runtime object, while the C backend splices the same text into
its own translation unit and lets clang inline it. The LLVM backend now emits
those bodies as IR with internal linkage, so its own `-O2` inlines them, and
crosses into the object only when a buffer really has to grow. The bodies, their
bounds checks and their panic strings are the runtime file's own, and the
runtime object and the C backend still define every one of them. The `strings`
category went from 20.9ms to 9.3ms.

**`Map`'s index is half the size, and `Map.with_capacity(n)` exists.** An index
slot was an `i64` under a `4x len` growth policy, which for three million entries
meant a 134MB index rebuilt about twenty times, with every probe touching that
footprint. The slot is now `u32`, the container function sets carry internal
linkage too, and the new constructor sizes both buffers up front from the
binding's written types, taking its count as a `usize` or an `i64`. The count is
a hint, never a fence: a map that outgrows it grows exactly like one that
started empty.

**Small constant-bound loops unroll, `mut` parameters are `noalias`, and `sqrt`
is the intrinsic.** LLVM's reasons for refusing an N-body pair loop were "call
instruction cannot be vectorized" and then "unsafe dependent memory operations
in loop": `std/math`'s `sqrt_raw` is now `llvm.sqrt.f64` in the LLVM backend, a
parameter an exclusive borrow proves exclusive is marked `noalias` (never the
`pd` hidden parameter, since a callee holding the global's own address writes
memory the attribute would claim nobody else touches), and a `while` whose
condition states a literal upper bound of 16 or less is marked
`llvm.loop.unroll.full`, which turns the inner index loops into straight-line
code the SLP vectorizer packs into `sqrtpd`/`divpd`. Instructions per step in
that kernel fell from 835 to 449, against the C reference's 487.

**The benchmark suite is published.** Thirteen categories over three languages,
every program's stdout compared byte for byte before its timing is trusted, six
of them ports of the Computer Language Benchmarks Game problems whose C++ and
Rust files are the published submissions. Kelp is first in seven categories,
ahead of the C++ reference outright in `fasta` at 633ms against 679ms over
25,000,000 characters, and 3.06x ahead of C++ in `collections` on identical
keys. The table, the method and the caveats are at
[Benchmarks](/compiler/benchmarks).

## 26.09.3 (2026-09-25)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v26.09.3)
· 15 commits · 203 unit tests, 465 end-to-end green.

**`thread.sleep_ms` and `thread.current_id`.** MK9-S3-M1 stage C2: two ordinary
functions over `extern fun` bodies rather than checker builtins, a worker-shaped
backoff and a stable id distinct between the main thread and any worker.

**A worker that returns `unit` can be joined.** `thread.join` on a
`Thread<unit>` used to fail in codegen on both backends. `Ok`/`Some`
instantiated with `unit` now lay out payload-less, the same shape `None`
already had, a general fix that also covers a hand-written `Result<unit, E>`
or `Option<unit>`.

**Concurrent downloads, and the memory model published.** `examples/download_pool.kp`
shows four worker threads, each with its own keep-alive `http.Pool` for the
run's one host, never shared; no language or stdlib change was needed, since a
`Pool`'s mutable state staying inside its owning thread falls straight out of
the crossing rule threads already shipped with. The memory model is now
published as the language's own at
[Concurrency in v1](/language/concurrency), closing MK9-S3-M1.

**`kelpc check --text`.** Reads the entry file's content from stdin instead of
from disk, so a caller (an editor) can ask about an unsaved buffer and get a
real diagnostic instead of the last save's. [Lighthouse](/tooling/lighthouse)'s
debounced re-check uses it.

## 26.09.2 (2026-09-24)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v26.09.2)
· 82 commits · 203 unit tests, 461 end-to-end green.

**Modules are private by default.** A top-level item is private to its module
unless it is declared `pub`, and an exported signature may not name a type its
ow module does not export: the refusal names the item, the type and the module.
`pub` is accepted on a top-level `fun`, `extern fun`, `datac`, `enum` or `const`;
a `pd` is module-scoped by design, and a method's reachability follows its
declaring type. A compiler-shipped `std/...` module still exports everything,
transitionally, because the shipped modules import each other without `pub`.

**A function can hand back two things.** `(A, B)` is a type with positional
fields and `val (lo, hi) = min_max(xs)` binds one, so a pair no longer needs a
one-shot `datac`. A tuple owns its elements, is never `Copy`, takes the derived
deep copy and order position by position, and is read by destructuring only:
there is no `t.0` and no tuple pattern in `when`.

**Threads exist.** `thread.spawn(entry, arg).R: Thread<T>` starts a real OS
worker and `thread.join(handle).R: Result<T, ThreadErr>` waits for it, on both
backends. A panic inside a worker ends that worker and arrives at its joiner as
`Err`, while the rest of the program keeps running; the abandoned frame leaks,
deliberately, because v1 has no user `Drop`. `std/atomic` ships `Atomic<T>` and
`Ordering` with the one ordering v1 has, and `std/thread` the standalone
`thread.fence(order)`.

**`std/ws`, and a dial that is a value.** A WebSocket client (RFC 6455) over
`ws://`, pure Kelp over `std/net` and `std/encoding`, with `sha1` added for the
handshake and a grant line of `caps(net = [...], rand = [])` because the
handshake key and every masking key have to be unpredictable. `net.try_connect`
and `ws.try_connect` sit beside the panicking `connect` and hand back a reason
instead of ending the program, the shape `try_run` already has, so a reconnect
loop can back off and give up.

**A grant can be one word.** `impl "x" caps(*)` hands the imported module every
domain's whole resource, the same set the entry module holds. It is not a way to
acquire authority: a delegator gives only what it holds, so a module granted one
path or one host cannot use it.

**And the fixes**, several of which were silent: the `llvm` backend declared the
C bodies it calls without the C ABI's `zeroext` on a narrow integer, so a `u16`
such as a URL's port could be handed over with dirty upper bits and dial a
garbage port; an owned local a second `var` rebinds is now freed for the value its
own declaration owns, instead of leaking the first buffer or freeing the wrong
one; a function owning both a `move` parameter and an owned local frees both; a
literal that does not fit its context is refused instead of wrapping to `-1`; a
capability path of about a thousand segments is refused rather than killing the
process with SIGSEGV; `net.recv` with a length of zero returns at once; a `unit`
value can be bound at last; and a method on a concrete `enum` resolves on a value
of that enum.

## 26.09.1 (2026-09-21)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v26.09.1)
· 130 commits · 179 unit tests, 359 end-to-end green.

**`llvm` is the compiler.** `Backend::DEFAULT` is `Llvm`: `kelpc` lowers its
typed IR to LLVM IR and lets LLVM optimize, encode and write the object. There is
no choice to make and no flag to make it with: `--backend=` and `KELPC_BACKEND`
are both refused by name, and `--backend=asm`, the retired hand-written track,
left with its source. The C backend stays in the tree as the project's own oracle,
reached only by the suite, and it is what keeps "correct" a measurement rather
than an opinion: all 359 fixtures build and run under `llvm` and under `c`, the
corpus sweep builds 223 of 380 targets with both and records **0 refused, 0
mismatches, 0 crashes** at `-O0`, `-O1`, `-O2`, `-O3` and `-Os`, the differential
fuzzer's 256 generated programs agreed, and a 24-program conformance corpus fails
none. `pd` globals with their drops, the capability check with the same allowlist
and the same denial text, and the `extern fun` bodies all landed under `llvm`, so
`std/mem`, `std/math`, `std/time` and `std/path` reach it. A `kelpc` built this
way needs **`libLLVM-21.so` at runtime**, and `cc` is still the linker, so a C
compiler and glibc are still required.

**Two spellings are removed, and each fix is one line.** `impl "path" as name` is
gone: a module's namespace is its own name (`std/path` is `path`,
`deps/argparse/lib` is `argparse`), so **drop the clause** and rename the call
sites where the name differed. `impl "..." with caps(...)` is gone: `impl`
already means what the clause restated, so **drop the `with`** and leave the grant
as it is (`impl "std/fs" caps(fs = ["/var/log/**"])`). With both gone the
deprecation register is empty, so **no program produces an `outdated:` finding any
more**; the mechanism and `--deny-outdated` stay in place for the next spelling.

**The language gained `[T; N]`**, a fixed-size array held inline with its length
in the type, so a page table or an IDT buffer exists with no allocator in the
path; **documentation comments** (`//!`, `///`, and a `[docs(<kind>: <name>)]`
head for a block that documents something else); and **general `const`**, whose
initializer may use the operators, `if`, a conversion, other `const`s and a call
to a plain `fun`, so an array length can be an expression
(`[u64; PAGE_SIZE / ENTRY_SIZE]`). A `List` element takes a derived deep copy and
order from its fields, so `List<Digest>.clone()` and `.sort()` both mean
something; a method call's receiver is borrowed after its own arguments, so
`counts.insert(key = k, v = counts.get_or(key = k, fallback = 0) + 1)` is one
statement; and a bare `List.empty()` takes its element type from the first
operation that has to know it. A raw NUL byte in a string literal is refused by
the lexer, where the two backends used to disagree about the same source file.

**`kelpc build` takes `-O0` to `-Os`** and `-O2` is the default, so a build with
no flag is what it has always been; one level means one level for both backends,
and `-Oz` is refused because the C oracle's `cc` may be gcc. The `llvm` backend
carries **DWARF debug locations**, so a fault in a binary names the `.kp` file and
line (`gdb` reports `kelp_divide () at fault.kp:16`), where the C backend leaned
on `cc` and its `#line`. **`kelpc check <file.kp>`** is the front end with no
backend, and `--json` prints the findings as one document with a range per
finding, the interface the language server and Coral read instead of parsing a
message.

**Stdlib.** `std/fs` gains `cwd()`, `is_symlink`, `read_link` and the fallible
`try_read`/`try_read_text`/`try_open`, which return `Result<_, IoErr>` so a tool
skips a file it may not read instead of ending its run on the first one;
`std/io` gains `IoErr` and `errno_text`; `std/path` gains `absolute(base, p)`;
and `std/fmt` gains `commas_u64`/`commas_i64` and `human_size`.

**Runtime.** The capability matcher and the path normalizer are Kelp now
(`std/rt.kp`), each proven against the C it replaced by a differential corpus, so
the same code works under either backend; the stub resolver's DNS message parser
and its `/etc/hosts` and `/etc/resolv.conf` parser ship with their own
differential corpora. Nothing a program can write changes.

**Fixed.** The C backend's capability check evaluates a resource argument once
into a temporary the check and the call share, so a gated call whose resource
argument has an effect can no longer be admitted against one path and then read
another, and the gate table now covers a gated module's extern primitives, its
receiver methods, a gated item named as a function value, and a `pd` initializer's
check against the module that declared the passdown. The `llvm` backend no longer
miscompiles a borrow a function returns, and a `panic` in a value-returning tail
lowers instead of reporting an internal error. On the C side, a call temporary
whose field was read by value is dropped, `fs.remove_all` unlinks a symlink
instead of deleting into it, `&expr` on a chain that steps through a borrow is
accepted, a `when` or a `for` whose scrutinee is a temporary stages it at the root
instead of refusing it or re-running the call, and a written borrow as a container
element is refused by name instead of silently dropped. Two `compile_and_run`
tests that shared one output path no longer race.

## 26.09.0 (2026-09-20)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v26.09.0)
· 26 commits · 165 unit tests, 312 end-to-end green on the C backend, 267 of
them on the assembly backend.

**The first release under `YY.MM.N`**, the scheme this project and its tooling
now share: the two-digit year, the two-digit month, and the release number
within that month starting at `0`. The version is one text everywhere it
appears, so `kelpc version` prints `kelpc 26.09.0`, the tag is `v26.09.0`, and
the asset is `kelpc-26.09.0-linux-x86_64`.

**A module's namespace is the module's own name**: `impl "deps/argparse/lib"` is
`argparse.parse(...)` and `impl "shapes/circle"` is `circle`. The
`impl "path" as name` clause still compiles and still names the module, and it
is now **outdated**. **`n.try_to_u64()`** is the fallible twin of `n.to_u64()`: it
hands back `Option<T>` for every conversion that can lose a value, where the
plain conversion panics. **Radix literals** (`0xff`, `0b1010`), **byte
literals** (`b'\n'`, a `u8` by construction), the two-digit **`\xNN`** escape,
and **`elif`** beside `else if`. The capability grant is
`impl "std/fs" caps(fs = ["/var/log/myapp/*"])`, and the `with` it replaces is
outdated. `List<T>.clone()` copies a list and its elements, and `panic` takes an
owned `String`.

**Outdated syntax is a register, not a break** (`kelpc/src/deprecated.rs`): a
retired spelling warns under an `outdated:` label and still builds,
`--deny-outdated` turns those findings into errors, and every entry is removed on
the next development cycle. **`kelpc lint <path>...`** reports the comment run,
an `else if` link that `elif` spells better, and a name that does not match the
project's `naming_case`. The generated C carries a **`#line` directive** before
every statement, so `cc`'s own diagnostic names the `.kp` line that caused it.
An owned value can be **interpolated into a template** (`print("w = ${s}")`),
the assembly backend lowers **`List.sort`/`contains`/`slice`** for the element
kinds the C backend allows, and a local that shadows a module name is now
reported as the shadowing it is.

**Stdlib.** [`std/encoding`](/stdlib/encoding): base64, base32, base58, hex and
percent, ungated, with one failure case across every decoder and both percent
forms kept apart on purpose.

**Fixed.** `isize` compiles on the C backend: it is `ptrdiff_t`, and the
generated C never included `<stddef.h>`, so every shape of it died in `cc` while
the assembly backend built all of them. An `outdated:` finding is printed once,
not once per load pass. An owned local bound in a loop body and moved on one
path is no longer leaked, and an `else if let` behind a plain `if` compiles. A
field of a `datac`-returning call stages its temporary instead of reaching `cc`
as `&(rvalue).field`, and the borrow that really does outlive the call is
refused in the compiler's own voice. Five diagnostics now name the thing the
reader has to change: a bare `mut T` operand, `&o` where `o` is already a
borrow, a capability delegated but never granted, the rejected-template message
(a `String` is not the problem), and a chained call that reuses one temporary.

## 0.1.5 (2026-09-20)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.5)
· 84 commits · 112 unit tests, 291 end-to-end green on the C backend, 242 of
them on the assembly backend.

**The compiler emits its own x86-64 assembly.** `kelpc build --backend=asm`
writes assembly itself and finishes it with `as` and `ld`; no C compiler in
that chain. The C backend stays as the differential oracle, so every fixture is
built by both and their stdout compared byte for byte. Constructs the new
backend cannot lower yet are refused **by name** rather than miscompiled: the
`fs`/`io`/`net`/`path`/`process` extern bodies, closures and function values,
and a capability-gated call.

What the assembly backend covers: `enum` tagged unions with `when`, `if let`
and a generated per-`enum` drop; **float fields in aggregates with the real
SysV per-eightbyte classifier** (SSE only when every field overlapping the
eightbyte is a float), pinned by a test that reads the emitted assembly; float
locals in the xmm pool with direct memory and immediate operands; a scalar
`mut` borrow and the store through it; owned heap fields, `Box<T>`, `List<T>`,
`Map<K, V>`, `String` and `View`; extern calls through the PLT; passdowns as
generated storage, with owned ones freed from a generated `kelp_drop_pds` that
`main` registers with `atexit`. The division-and-add kernel went from 4.16x the
`-O0` column to 0.54x of `cc -O2`.

**`kelpc fmt`**, with `--check` and `-w`: a token-level, comment-preserving
formatter, plus the lexer trivia it needs, and a 27-pair corpus.

**Block comments** (`/* ... */`).

**The runtime's Kelp half.** The capability matcher and path normalizer are now
written in Kelp, with the reviewed C versions kept as the reference the
differential tests compare against.

**Memory safety.** A valgrind gate over both backends is now part of the test
suite, and found: a one-eightbyte aggregate field or element loaded as a whole
`QWORD` (an invalid read past a heap block, invisible to a stdout comparison);
a temporary read through a field access that was not dropped; a `?` reached
with a pending operand that fell into the stack, fixed by rebuilding `rsp` from
`rbp` in the epilogue; and the forked child's `argv` leak in
`process.spawn_raw`.

**Also fixed.** `?` leaking a frame's drops; passdown forwarding; float literal
emission; chained `if let` re-moving its own scrutinee; `%` below 64 bits; a
zero-capacity `String`; a literal wider than its type; a `pd var` borrow is
shared unless the function writes it; a wrong-width aggregate load in the
assembly backend; the drop plan keyed by a block's identity instead of its
source span, so an owned local in a desugared `if let` or `for` block is no
longer dropped out of scope; a closure typedef that named a module type's
typedef before that type existed; and the C backend's warning noise, a doubled
parenthesis on every comparison and a tautological conversion bound.

**Stdlib.** `str.less` and `str.is_digit`: the byte ordering and decimal digit
predicate the libraries in the catalogue had each written by hand.

**Build.** `kelpc build` with no `-o` writes into `build/` instead of the
working directory. The crate moved to the 2024 edition.

**Known, not fixed here.** An owned local bound in a loop body is not dropped
on a path that does not move it, so a program that rebinds one leaks. It
predates this release and reproduces on the C backend at `-O0`.

## 0.1.4 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.4)
· 2 commits · 80 unit tests, 230 end-to-end green.

Five checker bugs, all found by compiling a real program: an 807-line JSON
library written with no access to the compiler source, built against 0.1.2 and
0.1.3. Every error it hit was the checker refusing ordinary code.

- **A view through a pattern binding keeps its provenance.** `if let Str(s) = v
  { return s.as_str() }` returns a view of `v`; the borrow root used to be the
  binding's *name*, so the same borrow was accepted as `v.x.as_str()` and
  refused as `s.as_str()`. Only borrow-typed bindings now carry their root, so
  tracing through an owned `x` still cannot pass a view of a local as a view of
  a parameter.
- **`panic` tails diverge for the borrow checker too**, not only for the type
  checker. One predicate, both passes.
- **`str` and `&str` are one type in arm unification**, so a `when` whose arms
  return `.as_str()` and a literal joins to the borrow.
- **A borrow inside an initializer ends with the statement**:
  `str.parse_i64(cand.as_str())` borrows `cand` for one call and keeps nothing
  of it. A binding that *is* the borrow still pins its owner.
- **A `Copy` value is never moved**, so a receiver method that names a field
  and then calls another method on `self` no longer reports "cannot move
  'self' while it is borrowed" about a pointer.

`borrow_provenance_and_arms.kp` pins all five.

**Known, not fixed here**: two code-generation bugs, both with a ~10-line
reproduction. An owned local in an `if let` block whose body holds a nested
`if let` with a `return` gets its drop call emitted but not its declaration;
and a `pd var` written in a function called transitively from another non-`main`
function passes a value where the callee's hidden parameter is a pointer.

## 0.1.3 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.3)
· 3 commits · 80 unit tests, 229 end-to-end green.

**A bare literal takes its sibling operand's type on either side.** The same
807-line JSON library failed its UTF-8 encoder with `operator requires matching
numeric operands, found 'i32' and 'u32'` on
`out.push((192 + cp / 64).to_u8())`. `syntax.md` §2.4 already promised that a
literal takes the integer type its context requires, but the checker read
operands left to right only, so a literal on the *left* was typed `i32` before
the right operand was looked at. One `check_binary_operands` now types both
sides; arithmetic, the bitwise operators and the comparisons all get it. A
`const` is deliberately **not** a literal for this rule: it has a declared type,
so `BASE + wide` stays a real mismatch.

`literal_operand_typing.kp` covers every width in both directions;
`literal_const_is_not_a_literal.kp` pins the rejection.

## 0.1.2 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.2)
· 10 commits · 80 unit tests, 227 end-to-end green.

The five gaps a real program found, plus the reference section that was
missing. Recorded as **MK8-S2-M1**.

- **`to_f64`/`to_f32` on every integer type**, so widening is one call instead
  of formatting the integer and parsing it back. Operands still must match
  exactly: `n * 1.0` remains a type error.
- **Character literals**: `'x'`, `'\n'`, `'\u{4e2d}'`. One Unicode scalar
  value, taking the integer type its context asks for (so `c == '"'` works when
  `c` is a `u8`) and `char` when nothing constrains it. A code point that does
  not fit is a compile error, not a truncation.
- **Bitwise operators**: `& | ^ << >> ~`. `&` is bitwise-and infix and the
  borrow prefix in prefix position; `<<` and `>>` are two adjacent characters,
  so `List<List<i32>>` still closes. Precedence is C's except that the bitwise
  operators bind tighter than the comparisons, so `flags & MASK == 0` means
  what it looks like.
- **`str` or `View` becomes an owned `String`** where one is expected: a call
  argument, a `datac` field, a `List` element, a `Map` key or value, a written
  type, a return, an `if` branch, a `when` arm. The other direction stays
  explicit, because `String` to `str` is a borrow with a lifetime.
- **`View`**: a length-carrying borrowed text view. `s.view()`, then
  `len`/`is_empty`/`get`/`slice`/`eq`/`to_string`. A slice costs a pointer and
  a subtraction instead of an allocation. It follows `str`'s rules exactly and
  is never a `datac` field, an `enum` payload, a `List` element or a `Map` key:
  a slice has no NUL after it, and v1 has no lifetime syntax to tie a stored
  borrow to its source.
- **CLI**: `kelpc version`.
- **Docs**: `syntax.md` §22, "Writing a program: the rules that explain most
  errors", with the eight rules behind most diagnostics plus a complete scanner.

## 0.1.1 (2026-09-19)

[Release](https://homelabone.xenoo.dev/gittea/Juniper/kelp/releases/tag/v0.1.1)
· 11 commits · 80 unit tests, 214 end-to-end green (every heap fixture also
rebuilt with `-fsanitize=address` and run).

The first release with a Gitea release attached; `v0.1.0` was left where it was.
This is the state of `main` after **MK5-S2-M2** and **MK8-S1-M3**.

- **The `for` loop** (MK8-S1-M3). `for x in xs { ... }` walks a `List<T>` front
  to back, desugared by the parser into an index and a `while`, so no later pass
  knows it exists. The element binding is what `List.get` gives: a copy of a
  `Copy` element, a shared borrow of an owned one. A place iterable is borrowed,
  not moved; anything else is bound to a temporary the loop owns and frees, so it
  is evaluated once. The loop variable is a `val`; there is no `break` and no
  `continue`. `for` walks a `List` and nothing else.
- **MK5-S2-M2, the three stdlib gaps a Coral port hit.**
  `process.spawn_in(dir, program, args)` and `process.run_in(...)` `chdir` in the
  *child* between `fork` and `exec`, so no capability pattern's meaning moves; a
  child that cannot enter `dir` exits 126. `process.try_run`/`try_run_in` return
  `Result<RunResult, ProcErr>` where `ProcErr` is `NotFound`, `NotExecutable` or
  `DirNotFound`, all decided by a `stat`/`access` pre-check **before** the fork, so
  an `Err` always means the child never started. `process.executable(path)` is
  that pre-check as public surface. `fs.symlink(target, link)` checks both paths
  against the module's `fs` grant.

**Limits worth knowing.** A capability *denial* cannot be a value yet: the check
is compiled in per calling module and panics before any Kelp code runs, so
`ProcErr` has no `Denied` variant. `std/http` speaks `http` only. No threads.
`kelpc` has no `--version` flag; the release name is the version.

## 0.1.0 (no release)

Tag `v0.1.0`, pointing at the **pre-rebase** history: it is not an ancestor of
any later release, and its tree is the same as `main` at *MK8-S1-M2 phase E*
apart from a deleted `rebrand.md`. No Gitea release was attached to it.

Everything up to that point, in the older milestone numbering the repository used
at the time (the `M0` to `M9`, `C1`, `S1` to `S8` scheme; the current scheme's
mapping is in `plan/roadmap.md`):

- **Core language** (`M0` to `M4.5`): scaffold and lexer/parser for the full
  surface syntax; types and the C backend; `datac` with real per-field
  mutability and `while`; spans through a typed IR; the syntax rewrite to
  `fun`/`val`/`var`/`datac`/`when`; move checking; borrowing (`&`, `mut T`
  parameters, `*`, aliasing checks); receiver methods.
- **Modules and compile-time** (`M5.1` to `M5.3`): `impl` imports with
  module-qualified names, `coral.toml`, `pd` passdowns, string templates, and
  `%*alias*%` text substitution.
- **Heap and containers** (`M6.1` to `M6.3`, `M8`, `C1`): owned `Bytes` and
  `String`, `drop`, `extern fun`, `std/mem`, `std/str`, `std/path`, `const`,
  stdlib-only overloading, `&str` return elision, `Box<T>` and recursive
  `datac`s, the builtin monomorphized `List<T>`, and `str.split`/`join` and
  `fs.list` on top of it.
- **Capabilities** (`M7`): `caps(...)` grants with a real `fs`/`time`/`rand`
  behind them, then `fs.append`/`fs.sync`.
- **The standard library program** (`S1` to `S5`): growable `String`/`Bytes`,
  `panic`/`assert`, integer conversions, text building and number formatting,
  the `List` ordering surface, `io` and `process`, `net` (sockets, `poll`, name
  resolution), the `http` client, `Map<K, V>`, and `fs`/`env` breadth.
- **Errors as values** (`MK5-S6-M1`): `enum` tagged unions with pattern `when`,
  generic type declarations and generic functions/methods with explicit type
  arguments, `Map<K, V>` with a real key type, `if let`, the `?` operator,
  `std/option` and `std/result`, and the migration of the stdlib off the
  error-`datac` convention.
- **Function values and closures** (`MK8-S1-M2` phases A to E): `move T`,
  function values, anonymous `fun` literals, the stdlib callbacks that take
  them, and captures, where a literal that captures is a closure.
- The language was renamed from **X** to **Kelp** in this stretch.

## Maintaining this page

This page carries **released versions only**. Nothing goes here until a version
is tagged.

Changes in the meantime accumulate in `kelp/CHANGELOG.pending.md`, which is
gitignored and never committed: add a line there when a user-visible change
lands, grouped under language, compiler, stdlib, fixes and limits.

When a version drops, write its entry here from that file plus the tag's commits
and the Gitea release body, then wipe the pending file back to its header. Commit
the entry on the `unreleased` branch and merge that branch into `main`: the merge
is what publishes the entry together with the pages that changed for the release
([Working on this site](/meta/contributing#working-on-this-site)). Cut it
the way `0.1.5` above is cut: the version and date, a link to the Gitea release,
the numbers (unit tests, end-to-end tests per backend), then what changed,
grouped so a reader can skip what they do not care about.

Keep it short. Link to `plan/done.md` for the full story rather than copying it.

Write the page without em dashes. Use a colon or a comma for an aside, a
semicolon or a full stop between clauses, and a plain hyphen in a range.

## See also

- [Roadmap](/meta/roadmap): what is planned, and what is in progress
- [Compiler](/compiler): the pipeline each entry changed
- [Coral changelog](/tooling/coral-changelog) and
  [Lighthouse changelog](/tooling/lighthouse-changelog): the other two repositories
