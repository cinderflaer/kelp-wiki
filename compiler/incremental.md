---
title: "Incremental builds"
description: "How `kelpc --incremental` splits the backend into per-module units plus a shared `_support` unit, caches each unit's object by a hash of its IR, and compiles the misses on parallel workers."
isPublished: true
tags: "compiler"
---
`kelpc` can build a program in **compilation units** instead of one translation
unit: each source module becomes its own LLVM module and object, and the objects
are linked into the binary. Because a unit's object depends only on that unit's
IR and the settings it was compiled with, an unchanged unit can be reused from a
content-addressed cache on the next build. This is roadmap item A-14, split into
three slices: separate compilation (slice 1), the object cache (slice 2) and
parallel unit compilation (slice 3). The mode is off by default and produces the
same program either way.

The command surface is on the [`kelpc` CLI](/tooling/kelpc-cli#incremental-builds-and-the-object-cache)
page; this page is how it works. The design authority is
[`plan/incremental-compilation.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/incremental-compilation.md).

## The split

The front end stays **whole-program**. Loading modules, resolving names, type
checking and borrow checking all still run once over the entire program, and
they are cheap: 3 to 4 ms over the whole corpus, where a build is dominated by
LLVM optimization, code generation and the `cc` link. Only the backend is split.

There are two kinds of unit:

- One unit per **source module id**. It holds that module's non-generic
  functions, the instances of its own generic functions whatever type arguments
  they were given, its `statics` and `section(...)` consts, and the trampolines
  its `extern fun` declarations reach. `main` and the program's own module are
  ordinary units.
- One unit named **`_support`**, holding everything with no single owning module:
  the compiler-generated per-type helpers (`drop`, `clone`, `eq`, `hash`,
  `order`, the `List`/`Map`/`Box`/array instantiations), the string and bytes
  helpers the backend emits as IR, closure thunks and widening shims, `&dyn`
  vtables, panic helpers, and the `pd` globals. A module id is a path under
  `src/` and a file must be a valid identifier, so it never starts with `_`: the
  name cannot collide.

Every unit **declares** every function, static and `pd` global of the program
(a declaration costs no symbol in the object) and **defines** only what it owns.
A symbol another unit references is external in its owner and a declaration in
its users; a symbol only its own unit uses stays `internal`. The reference set is
computed from the typed IR before any module is built, plus a scan of the
per-program C object, because an `extern fun` body or a capability shim can call
a Kelp function across the object boundary in C. An over-approximation is
harmless; a missed reference is a link error, never a silent miscompile, which is
why every equivalence test links the real binary.

The artifact is `<out>.units/<unit>.ll` and `<out>.units/<unit>.o`; a `/` in a
module id becomes `+`, so `shapes/circle` is `shapes+circle.o`. The objects are
linked with the runtime object and the per-program `extern fun` object. Debug
info is per unit: the backend always emits DWARF, so a multi-unit binary carries
one compile unit per module and a fault still resolves to the `.kp` line that
caused it, which is ordinary DWARF.

## Why the cache is always correct

The cache is a pure lookup, and the whole design is one claim:

> A unit's object is a pure function of its IR text, the target triple, the CPU
> and feature string, the optimization level, the relocation and code model, the
> debug-info setting and the compiler version string.

The unit's IR already carries every front-end decision and every cross-unit
declaration, so if two IR texts are identical the objects are identical, whatever
changed elsewhere in the program. There is therefore **no dependency tracking and
no interface file**, and correctness cannot depend on a dependency graph: a stale
entry is impossible because the key names the exact input that produced it.

The key is the lowercase hex SHA-256 of a labelled canonical byte string built
from those fields plus the length-prefixed IR text. Each field is labelled so its
identity is part of the hash, and the IR is last because it is the one value that
can contain a newline. `opt` is the LLVM pipeline string (`default<O2>`), so a
different `-O` cannot share a cached object; `compiler` is `kelpc <version>` plus
the linked LLVM's version, because an object is the IR run through a specific
LLVM. SHA-256 is implemented in the tree (`kelpc/src/sha256.rs`); `kelpc` has no
third-party dependency.

The directory is `$KELPC_CACHE_DIR`, else `<out dir>/.kelpc-cache` (for the
default output path, `build/.kelpc-cache`), and an entry is `<key>.o`. A store
writes a temporary file in the same directory and renames it into place, so two
builds sharing one cache never observe a partial entry. A lookup is a miss for an
entry that is missing, unreadable, empty or visibly truncated. A non-empty entry
that fails to link is not retried silently: the link error names the units whose
objects came from the cache, their entries are deleted, and the next build
recompiles them. `KELPC_CACHE_MAX_MB` (default 1024) caps the directory, deleting
oldest-modified entries first at the end of a build.

`KELPC_CACHE_STATS=1` prints `kelpc cache: <H> hits, <M> misses, <S> stored`, and
`--timings` adds one line per unit with `hit` or `miss`, and one `front-end interfaces: H hit, M miss` line (see below). Edit one module and
exactly the units whose IR changed miss, which on a `shapes` project (`main`,
`geom`, `shapes/circle`) looks like the transcript on the
[CLI page](/tooling/kelpc-cli#incremental-builds-and-the-object-cache): three
hits, the edited `main` misses, and the other two modules plus `_support` are
reused.

## Parallel workers

A cache hit is a file copy and stays on the calling thread. A **miss** is
lowered, optimized and emitted on a worker thread inside `std::thread::scope`,
each unit in its own LLVM context, each worker owning one `TargetMachine`. The
worker count is `KELPC_JOBS` when it names a positive integer and **2**
otherwise, deliberately not the CPU count on a small host where every worker
holds a live LLVM context. LLVM's targets are registered once before the first
worker starts.

Determinism does not depend on the schedule. The unit list is every module id
sorted, then `_support`; each worker writes into a slot indexed by the unit's
position, and the caller links the objects in that order whatever order the
workers finished in. Two builds of the same sources produce byte-identical unit
IR and byte-identical objects at `KELPC_JOBS=1` and `KELPC_JOBS=4`. A unit that
fails or panics is recorded against its index and the other workers still finish,
so the successful units keep their cache entries and the next build resumes from
them; the build then fails naming the first failing unit by index, not by race.
The memory guard is unchanged and still ends a build with `_exit(75)` when the
machine runs low, running no destructors on any worker.

## What it does not do

- **No cross-unit inlining.** A call between two units is a real call in the
  object. This is the documented cost of the mode and the cache cannot change it.
  Inside a unit the pipeline is unchanged.
- **Generated interface files are validated, not reused.** An incremental build
  writes one `.kpi` artifact per module (its public-surface hash, dependency
  hashes and a format version) beside the object entries, and `--timings` reports
  how many were current. A corrupt, truncated or old-format artifact is a miss and
  is rewritten atomically. The front end still parses, resolves and checks every
  module on every build, so nothing is skipped because of them yet. A module that
  declares a generic item, a `const`, a `static`, a `pd` or a destructor puts its
  whole text into its interface hash, since a body edit there can change an
  importer.
- **No dependency tracking.** The cache key names a unit's
  exact IR instead. A consequence is that a signature change is broad: every unit
  declares every program item, so changing one callee's signature changes the
  declaring IR in more units than the caller's and they all miss. That is
  correctness rather than a defect; the alternative is a dependency graph the
  design refuses.
- **No front-end incrementality.** Parse, resolve, infer and borrowck stay
  whole-program and sequential.
- **No shared cache.** The key names the triple, CPU, features, relocation, code
  model and compiler and LLVM versions, so a directory copied to another machine
  or used by another `kelpc` build simply misses and rebuilds.
- **No freestanding support.** `--incremental` with
  `[target] mode = "freestanding"` is refused by name: the bare-metal path emits
  the entry stub, the panic state and the `probe-stack`/`noredzone` sweep at
  module scope, and its image is one ELF with a single `_start` and one panic
  state. That is its own slice.

## Measured numbers

These were measured on an earlier build, not on the 26.10 releases. The commands
below reproduce them, and a fresh run is the number to trust.

Host: the small dev machine this work runs on (7.8 GiB RAM, limited free
memory). Every cell is the **median of three runs**, in milliseconds, of a real
`kelpc` binary: the debug build (`target/debug/kelpc`) and the release build
(`target/release/kelpc`). "Warm" is a build of unchanged sources whose cache the
preceding build filled; "edit" is one literal changed in one module of a program
whose cache was filled by the unedited build, so exactly that module misses.

The three programs are `examples/hello.kp` (3 lines); `http_rate_limit`, the
largest hosted project under `kelpc/tests/projects/` that binds `std/http`
(about 100 lines of Kelp plus the shipped `std` modules it reaches); and
`examples/download_pool.kp` (203 lines, `std/http` plus `std/thread` and
`std/process`).

| program | build | debug median (ms) | release median (ms) |
| --- | --- | ---: | ---: |
| hello | whole-program | 136 | 133 |
| hello | incremental, cold cache, jobs 1 | 145 | 150 |
| hello | incremental, cold cache, jobs 2 | 141 | 156 |
| hello | incremental, warm cache | 131 | 128 |
| hello | incremental, one-line edit in one module | 136 | 142 |
| http_rate_limit | whole-program | 4992 | 3487 |
| http_rate_limit | incremental, cold cache, jobs 1 | 4472 | 3187 |
| http_rate_limit | incremental, cold cache, jobs 2 | 3130 | 2418 |
| http_rate_limit | incremental, warm cache | 2372 | 1299 |
| http_rate_limit | incremental, one-line edit in one module | 2418 | 1323 |
| download_pool | whole-program | 5072 | 3669 |
| download_pool | incremental, cold cache, jobs 1 | 4590 | 3265 |
| download_pool | incremental, cold cache, jobs 2 | 3228 | 2504 |
| download_pool | incremental, warm cache | 2336 | 1356 |
| download_pool | incremental, one-line edit in one module | 2355 | 1397 |

The command lines, with `<target>` the program above, `<out>` a scratch output
path and `<cache>` a cache directory:

- whole-program: `kelpc build <target> -o <out>`
- incremental cold, one worker:
  `rm -rf <cache>; KELPC_JOBS=1 KELPC_CACHE_DIR=<cache> kelpc build <target> -o <out> --incremental`
- incremental cold, two workers: the same with `KELPC_JOBS=2`
- warm: run the jobs-2 command once, then run it again and time the second run
- edit: run the jobs-2 command once on the unedited source, change one literal in
  one module, then run the same command again and time it

### What the numbers say

- **Incremental does not pay for a tiny program.** `hello`'s whole-program build
  is 133 to 136 ms; a cold incremental build is 141 to 156 ms, and the warm and
  one-line-edit builds are within about 10 ms of whole-program (128 to 142 ms,
  which is this host's noise plus or minus a few ms). A build that small is the
  `cc` link plus a fixed per-unit overhead; there is almost no backend work to
  save, and splitting one module into a unit plus `_support` adds two pieces of
  work where there was one. The mode is off by default for exactly this shape.
- **It starts to pay once a program pulls in heavy `std` modules.** A ~100-line
  program that uses `std/http` goes from 4992 to 3130 ms (debug) and 3487 to
  2418 ms (release) for a cold incremental build at two workers: about 1.4 to 1.6
  times faster. The warm and one-line-edit builds are about 2.1 to 2.7 times
  faster than whole-program. That is the size at which the backend work the split
  saves is larger than the link and the per-unit overhead.
- **Parallelism is what makes the cold build fast.** Two workers against one is
  1.3 to 1.4 times on both large programs. It does not change the warm build
  much, because a cache hit still lowers every unit's IR to compute its key (the
  IR is the key's largest field) and the link at the end is serial.
- **A one-line edit costs about a warm build, not a cold one.** The changed unit
  is one small module; the other units still lower and the link still runs, so
  the edit build is within noise of the warm build and well under the cold build.
  The saving is the other units' pass pipeline and codegen, not their lowering.

The numbers are not a claim that every project is faster: `hello` does not
benefit, and the threshold is a program whose own backend work is larger than the
link, which on this host is a program that reaches the heavy `std` modules.

## See also

- [`kelpc` CLI](/tooling/kelpc-cli#incremental-builds-and-the-object-cache): the flags, environment variables and cache commands
- [Pipeline](/compiler/architecture): the stages the front end still runs whole-program
- [Backends](/compiler/backends): the `llvm` backend and the C oracle
- [Compiler](/compiler): the chapter index
