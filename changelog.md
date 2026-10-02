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
| Unreleased | pending | `unsafe`/`Ptr<T>` and layout control; freestanding mode and kernel 0 booting under QEMU; per-CPU storage, user `Drop`, Sv39 and the user-mode syscall ABI; freestanding `String`/`Bytes`, `std/arena` and `Ptr.try_alloc`; stack guards and probing; a typed `TlsHandle` with `TlsError`/`TlsOptions`; the `try_` surface; the `mmio` capability; a compiler memory floor; traits with static dispatch; `==`/`!=` over a declared `eq`; the `for` mutation rule; `Mutex<T>` in `std/sync`; panic locations and double-panic detection; the `irq` and `frames` capabilities; the freestanding `std` subset; the x86-64 target |
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

## Unreleased

Not a version number yet: this is what has landed since 26.09.5 and is waiting
for a release to cut. Sixteen pieces, in the order they were built.

**`unsafe`, `Ptr<T>` and layout control.** A raw pointer type `Ptr<T>` and the
`unsafe` blocks and `unsafe fun` that are the only way to dereference one.
`p.read`/`write` and their `read_volatile`/`write_volatile` twins (volatile is
never merged, reordered or elided), the unaligned pair, `Ptr.alloc`/`free`,
`offset`/`byte_offset`/`cast`/`addr`/`is_null`, and `Ptr.from_ref`/`from_mut`/
`from_fn`. A module may contain any of it only if `coral.toml` lists it under
`[unsafe] modules`, parsed like `[extern.*]`, so the set of modules that leave
the checked language is short and reviewable, and a project with no `[unsafe]`
section is unchanged. `repr(c)` (the default, now a guarantee), `repr(packed)`
and `repr(align(N))`, the compile-time `size_of`/`align_of`/`offset_of`, and
explicit discriminants on a field-less enum with `repr(u8|...|i64)` storage and
`to_int`/`from_int`. Every integer wider than a byte has `swap_bytes`/
`to_be`/`to_le` and the static `from_be`/`from_le`, the direction asked of the
*target* rather than assumed, and `Bytes` has bounds-checked
`read_u16_le`...`read_i64_be`/`write_*` accessors with no alignment
requirement. Both backends write the same layout and the same bytes; a C helper
in `tests/projects/ffi_layout` checks the packed layout against a real C
compiler. See [Unsafe code and raw pointers](/language/unsafe).

**Freestanding mode, and kernel 0 boots.** A project with `[target] mode =
"freestanding"` in `coral.toml` gets no libc, no runtime preamble, a
compiler-emitted `_start` that sets `sp` and clears `[__bss_start,
__bss_end)`, the entry and panic functions and a linker script it names, and an
`ld.lld -T` static link with no runtime object. Everything that would reach
libc is a compile error, and so is any `std/*` module except the pure ones and
the `str` operations the compiler lowers itself. `static`/`static mut` and
`defer` are allowed, `asm` and naked functions are allowed, and a `[target]
alloc`/`dealloc`/`realloc` hook reroutes `Box`/`List`/`Map` onto the project's
own allocator. With that pair configured, `String` and `Bytes` join them: their
bodies are byte loops over the project's own buffers, so a kernel builds text
with `str.concat` and `str.from_u64`/`from_i64` and grows a `Bytes` by doubling,
with no `strlen` or `memcpy` in the image and a null allocation reaching the
handler with `"out of memory"`. The five
`memcpy`/`memmove`/`memset`/`memcmp`/`bcmp` routines LLVM's own aggregate
copies call are defined weakly in every freestanding object. Freestanding is LLVM-only: the C backend's preamble is libc, so
`KELPC_ORACLE=c` refuses such a project by name. `examples/kernel0` boots on
QEMU's riscv64 `virt` machine and prints `hello from kelp`; so do the trap, BSS,
panic, heap and string variants, and `examples/kernel0-aarch64` boots the second
architecture. See [Freestanding mode](/language/freestanding) and
[Kernel 0](/language/kernel).

**Per-CPU storage, user `Drop`, Sv39 address spaces and user mode.**
`percpu static mut NAME: T = INIT` lays out `[target] cpus` copies (an integer
`1..=64`, default 1) as one 64-byte-aligned array in `.percpu`, and the
freestanding-only `cpu_index()`/`cpu_count()` read the register the kernel sets
(`tp` on riscv64, `TPIDR_EL1` on aarch64); the riscv64 `_start` stub parks every
hart but hart 0 before it loads `sp`. `fun mut T.drop()` gives a user `datac` or
`enum` a destructor that runs first at each drop point the plan already had,
with a moved value not dropped, a partial move refused, and no unwinding on a
panic. The kernel examples grew with it: `examples/kernel0-vm` builds Sv39 page
tables, drops to S-mode and aliases a high page, `examples/kernel0-vm-fault`
takes a load and a store page fault in an S-mode handler, and
`examples/kernel0-user` adds the trap frame, the `ecall` ABI and
untrusted-pointer validation for a program in U-mode. See
[Per-CPU storage](/language/percpu), [User `Drop`](/language/drop) and
[Kernel 0](/language/kernel).

**Arenas and fallible allocation.** `Ptr.try_alloc<T>(count)` is `Ptr.alloc`'s
non-panicking twin: unsafe like it, the same element set and alignment promise,
but a failed allocation is the null `Ptr<T>`, and a count whose
`count * size_of::<T>()` product would wrap `usize` is refused before the
allocator is asked. Hosted it is `malloc` on both backends; freestanding it is
the project's own `[target] alloc`, admitted by the same pair `Box`/`List`/`Map`
need. `std/arena` is a bump arena over a caller-owned region, in Kelp with no
externs and no libc, so it works hosted and freestanding and needs no allocator
hook: `arena.new(base, cap)` hands out aligned `Ptr<u8>` blocks, answers the
null pointer when a request does not fit or would wrap, panics on a
non-power-of-two `align`, and `reset` reclaims the whole region. `alloc_zeroed`
is the module's one unsafe operation, admitted by the compiler's own
`stdlib::UNSAFE_MODULES` list rather than a project manifest. See [Unsafe code
and raw pointers](/language/unsafe) and [`std/arena`](/stdlib/arena).

**Stack guards and probing.** Every function a freestanding LLVM build emits
carries `"probe-stack"="inline-asm"`, so a frame larger than a page is built by
touching each page from the top and an unmapped guard page traps it.
`examples/kernel0-stack` puts a 16 KiB trap stack below the image, an unmapped
4 KiB guard above it and an 8 KiB kernel stack above the guard, then takes both
overflows in one boot: a small-frame recursion into the guard, and a single
`[u8; 16384]` frame the probe walks down page by page. Both print `scause 0xf`
and an `stval` inside the guard bounds. Hosted builds carry no attribute. See
[Kernel 0](/language/kernel).

**Stable TLS, and the `try_` surface on the network modules.** `std/tls` gains
the typed `TlsError`, `TlsOptions` (a private CA file or directory, a timeout)
and a `try_handshake`/`try_read`/`try_write`/`try_shutdown` family beside the
panicking wrappers. `TlsStream` now carries the OpenSSL handle as a typed
`extern type TlsHandle` instead of a `usize`, so it cannot be forged from an
integer or confused with another handle, and `std/http`/`std/ws` carry the
plain-or-TLS choice as `Option<TlsHandle>` rather than an integer sentinel. A
stream that ends without a `close_notify` is
`PeerClosedUncleanly`, never a clean EOF, by design. `wss://` works over
[`std/ws`](/stdlib/ws). `std/http` gains `try_get` and `HttpErr` (`Dial`,
`Exchange`, `Redirects`), and `std/net` gains `try_send_all`/`try_recv`/
`try_recv_into` with `NetErr`. OpenSSL is linked, and its headers included, only
when a program reaches `std/tls` (which `std/http` and `std/ws` do). See
[`std/tls`](/stdlib/tls).

**`mmio` as a capability.** An eighth capability domain, `mmio`, gates
`Ptr.from_addr` in a freestanding project: a grant is a list of half-open ranges
`"0xBASE+0xLEN"` or the whole address space as `["*"]`. A constant address must
fall inside a granted range, a computed one is refused unless the grant is
`["*"]`, and a module with no grant is refused by name. `mmio` is the one
domain the entry module does not hold by default and the one `caps(*)` leaves
out, so the whole-space grant is written where a reviewer sees it. Every
`examples/kernel0*` manifest now carries a grant. The check is on the address a
pointer is born at, so an offset applied afterwards is not revisited. See
[Capabilities](/language/capabilities#mmio-device-registers).

**The compiler's memory floor.** `kelpc build` and `kelpc run` watch
`MemAvailable` and, below `KELPC_MIN_AVAILABLE_MB` (default 384; `0` turns it
off), kill the `cc`/`ld.lld`/`pkg-config` children they spawned, print one
`error:` line and leave with `_exit(75)` (`EX_TEMPFAIL`) instead of letting the
kernel OOM killer pick a victim. `kelpc run` stops the guard before the compiled
program starts, and `fmt`/`lint`/`check`/`version` do not start it. See [`kelpc`
CLI](/tooling/kelpc-cli#the-memory-floor).

**`==`/`!=` over a declared `eq`.** The front end lowers `a == b` to
`a.eq(&b)` and `a != b` to `!a.eq(&b)` for a `datac`/`enum` that declares
`fun T.eq(other: &T).R: bool`, before borrow checking and code generation, so
both backends run the declared body and no operator is added anywhere. `eq`
alone is now a complete declaration: it gives the operator without making the
type a `Map` key, and a lone `hash` is still refused. Nothing is derived, so a
type with no declared `eq` keeps the old refusal, `<`/`>` stay refused, and
`View` against `View` or a `str` lowers to the builtin `View.eq`. See
[Operators and expressions](/language/expressions).

**Traits with static dispatch.** A `trait Name { fun [mut] Self.method(...) }`
is a named set of method signatures, `impl Name for Type { ... }` gives them to
a `datac`/`enum` in the trait's module or the type's, and `fun f<T: A + B>`
bounds a type parameter. At most one impl of a trait for a type, every
signature matched exactly, and an inherent method of the same name is refused
at the impl. Dispatch is static: the bound is checked at every call and
instantiation, and the body is then monomorphized per concrete type exactly as
generics already are, so neither backend nor the freestanding mode needed a new
lowering. `dyn` and trait objects, default methods, associated types, `impl
Trait` in argument position, a trait on a builtin or on a generic
instantiation, `where` clauses, supertraits and operator overloading through a
trait are each refused by name. See [Traits and static
dispatch](/language/traits).

**`Mutex<T>` in `std/sync`.** A compiler builtin generic in the shape
`Atomic<T>`/`Thread<T>` have: one monomorphized type per element, not `Copy`,
with a drop. The value is reached only through the scoped block
`m.lock { v -> ... }`, which passes `v: mut T` to a `scoped fun(mut T).R: R`, so
the borrow cannot escape; the block's tail is the call's value, and a `return`
or `?` inside it still releases the lock. A panic inside the block releases the
lock and marks the mutex POISONED, so a later `lock` panics with
`mutex poisoned`, and `into_inner` consumes the mutex. A `&Mutex<T>` crosses to
a worker exactly as a `&Atomic<T>` does. Hosted only: a freestanding manifest
refuses it by name and points at a spin lock over an `Atomic<T>`. See
[`std/sync`](/stdlib/sync).

**Bugfix pass.** The compiler's own warnings are zero, the differential fuzz ran
1500 generated programs plus the 24-program corpus with 0 mismatches, and one
real bug was fixed: `u8`/`u16` arithmetic was not narrowed to its declared width
in the C backend, so `u8 + u8` of 300 printed 300 where LLVM wrapped to 44. It
also closed the `for` rule: a body may no longer mutate the list it walks,
because an owned element already bound as a borrow but a `Copy` element did not,
so `for x in xs { xs.push(x) }` grew the list the loop re-read until memory ran
out. The body may read the iterated place and change a different list; a `mut`
receiver method, an assignment, a move, `&mut xs`, a `mut` argument and a
capturing `fun` literal are one error, `cannot mutate 'xs' while iterating over
it`, reported on the `for` line, and walking by index in a `while` is the
supported way to change what a loop walks. The differential sweep is a ratchet:
`LLVM_BUILT_BASELINE` is 362 of the 655 corpus
targets, 0 refused, 0 mismatches, 0 crashes, and it may only rise. See
[Backends](/compiler/backends).

**Panic semantics with no OS.** A freestanding panic handler may keep the
original `fun(msg: str)` shape or take the location as
`fun(msg: str, file: str, line: u32)`, and any other shape is refused by name.
Every compiler-inserted check calls one compiler-emitted entry, which carries
the check's own message and the 1-based line of the statement it was inserted
into: the same per-statement source-map values the hosted line tables use, read
from two `.bss` globals when the check lives in a generated body shared by every
call site. The entry exchanges a `.bss` flag, so a check that fires while the
handler is already running reaches `kelp_double_panic` instead of recursing; the
compiler defines that weakly as a `wfi`/`wfe` loop and a project may override it
with a strong definition. `examples/kernel0-panic2` boots one phase per check
(array bounds, narrowing, `str.byte`, the `panic` builtin, `option.unwrap`, and
a double panic) and asserts each exact line. Integer overflow still wraps and
division by zero is still an unchecked UB, so neither has a message. See
[Freestanding mode](/language/freestanding#panic-semantics) and
[Kernel 0](/language/kernel).

**`irq` and `frames` as capabilities.** Two device capabilities beside `mmio`:
`irq` takes a decimal line or an inclusive range (`irq = ["10", "32-47"]`) and
`frames` the same `"0xBASE+0xLEN"` byte windows. `irq.claim(n)` and
`frame.claim(addr)` in the shipped [`std/irq`](/stdlib/irq) and
[`std/frame`](/stdlib/frame) are the gated constructors and the only way a
`Line` or a `Frame` enters a program; their struct literals are sealed to their
modules, so another module cannot forge a receipt. A constant argument must fall
inside a granted range, a `Frame` address must be 4096-aligned, and a computed
argument needs the whole-resource `["*"]`. Unlike `mmio`, the check is in the
front end and applies to a hosted program and a freestanding image alike, and
the entry module holds both domains by default, so a kernel narrows them in
`[caps]`. `examples/kernel0-caps` claims one of each and prints them over the
UART. See
[Capabilities](/language/capabilities#irq-and-frames-interrupt-lines-and-physical-frames).

**The freestanding standard subset.** `freestanding.rs` decides each shipped
`std/*` module with one table row (`Pure`, `Allocator`, `Subset`, `Present`,
`Hosted`) instead of two hand-kept lists, the call-site check and the body
pruning are driven by the same row, and a whole-module refusal names the modules
a freestanding project may implement. Newly admitted: `std/math`'s integer
`abs`/`min`/`max`/`clamp` and, with the `[target] alloc`/`dealloc` pair,
`std/list` and the `std/option`/`std/result` callback combinators. The admitted
list is `std/arena`, `std/atomic`, `std/frame`, `std/irq`, `std/list`,
`std/math`, `std/option`, `std/result`, `std/str`; every other module is refused
by name with "needs a hosted runtime", and `std/math`'s libm externs and the
rest of `std/str` are refused by name inside the admitted module. See
[Freestanding mode](/language/freestanding#the-freestanding-standard-subset).

**The x86-64 target.** `[target] triple = "x86_64-unknown-none"` (the `-elf`
spelling too) gets the X86 target machine and an x86-64 `_start` stub: a
`.note.Xen` `XEN_ELFNOTE_PHYS32_ENTRY` note naming the entry, 32-bit code that
loads a GDT with a 64-bit code segment, builds an identity map for the first
1 GiB out of 2 MiB pages in a `.boot_pt` NOBITS section, enables PAE and
`EFER.LME`, loads CR3 and sets `CR0.PG|PE`, then far-jumps into long mode, where
it loads `rsp`, clears BSS, enables SSE and calls the entry; every emitted
function is `noredzone`, and the target machine uses the static relocation and
small code models. `examples/kernel0-x86_64` is a COM1 port-I/O driver and
`examples/kernel0-x86_64-lmode` reads CR0/CR4/EFER, prints `long mode on` and
then triple-faults on purpose; both boot under `qemu-system-x86_64 -M q35 -cpu
qemu64 -no-reboot`. Interrupts and an IDT, the APIC, SMP and ACPI are not part
of it. See [Freestanding mode](/language/freestanding#the-x86-64-target).

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
