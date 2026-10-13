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
[`compiler/incremental.md`](/compiler/incremental).

## The split

The front end stays **whole-program**. Loading modules, resolving names, type
checking and borrow checking all still run once over the entire program, and
they are cheap: 3 to 4 ms over the whole corpus, where a build is dominated by
LLVM optimization, code generation and the `ld.lld` link. Only the backend is split.

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
computed from the typed IR before any module is built. The per-program externs
object defines no Kelp function and calls none directly, so it adds no reference.
An over-approximation is harmless; a missed reference is a link error, never a
silent miscompile, which is why every equivalence test links the real binary.

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
- **No hosted support.** A hosted build is whole-program, because the collector's
  descriptors and init are one module's. `--incremental` on a hosted build is refused
  by name, and a hosted manifest with `[build] incremental = true` is built
  whole-program with a warning.
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
  `ld.lld` link plus a fixed per-unit overhead; there is almost no backend work to
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
- [Backends](/compiler/backends): the `llvm` backend, the only code generator
- [Compiler](/compiler): the chapter index


## Incremental compilation: compilation units and front-end interfaces

Moved here from the retired `plan/incremental-compilation.md`. The text is kept as the record it was.

*Roadmap A-14. Slices 1 to 3 are separate compilation, the content-addressed
object cache over its units, and parallel unit compilation. Slice 4 is the
chosen generated-interface design for front-end incrementality. The measured
numbers for the shipped backend slices are at the end of this file.*

### The decision

The measured cost of `kelpc build` is almost all backend: LLVM optimization,
code generation and the link (`ld.lld` since 2026-10-10; `cc` before that). The front end (parse, check, borrow-check) is
3 to 4 ms on the whole corpus. Slices 1 to 3 therefore keep the front end
**whole-program** and split the backend into units:

- the program is partitioned into **units**, one per source module id, plus one
  unit named `_support`;
- each unit becomes its own LLVM module, is optimized at the selected `-O` level
  with the same pass pipeline the whole-program build uses, and is compiled to
  its own object file;
- `driver.rs` links every unit object, the runtime object and the per-program
  `extern fun` object into the binary.

Slice 1 is the split and the link. Nothing is cached and nothing is parallel yet,
so an incremental build today costs *more* than a whole-program one (the same
work plus a second module's worth of declarations). The point is the shape the
next two slices need, and the equivalence it must preserve: the same program must
produce the same stdout and exit status either way.

### Slice 4: generated front-end interfaces

The next slice changes that boundary. Its design is in
`plan/front-end-incremental.md`: an interface is compiler-generated from a
module's checked public surface, never checked in or edited by a user; an import
depends on that interface hash, not on another module's private implementation;
and `std/internal/...` is a compiler-reserved root that user `impl` lines cannot
name. This slice is deliberately module-granular. It does not introduce
cross-unit inlining or a query engine.

### The flag

Three ways to turn the mode on, and one way it stays off:

- `kelpc build --incremental <target>` and `kelpc run --incremental <target>`;
- `[build] incremental = true` in `coral.toml`;
- default **off**: with the mode off, the backend emits exactly one LLVM module
  named `kelp`, exactly as before this slice, and every existing test passes
  untouched.

The C backend is the suite's oracle (`KELPC_ORACLE=c`), not a user surface, and
it **ignores the flag**: its generated C stays one translation unit, because the
whole point of the oracle is to be the other answer to the same question. A
`--incremental` build under the oracle is therefore an ordinary C build, and the
equivalence test compares the two backends' *programs*, not their object counts.

`KELPC_DUMP_UNITS=<dir>` writes each unit's unoptimized LLVM IR to
`<dir>/<unit>.ll`. It is how the determinism test reads the IR (identical
sources must produce byte-identical unit IR) and how the cache tests read which
units' IR changed; it does nothing outside the mode.

`--timings` prints per-phase wall times (parse, resolve, infer, borrowck,
codegen, unit compile, link) and one line per unit with `hit` or `miss`, to
stderr. It is the observable half of slice 2.

### Unit assignment

One unit per source module id holds:

- that module's non-generic functions;
- the instances of **its** generic functions, whatever the type arguments (an
  instance of module `M`'s generic function is owned by `M`, not by the module
  that happened to instantiate it);
- its `statics` and its `section("...")` consts;
- the trampolines its `extern fun` declarations reach, which stay C in the
  per-program `externs.c` object (one object for the whole program, exactly as
  today: the C text is the C backend's own).

`main` and the program's own module are ordinary units.

One unit named `_support` holds everything with no single owning module:

- the compiler-generated per-type helpers: `drop`, `clone`, `eq`, `hash` and
  `order` for `datac`/`enum`, `List`, `Map`, `Box` and array instantiations;
- the string/bytes/list runtime helpers the backend emits as IR rather than
  taking from `kelp_rt.o`;
- closure thunks, the widening thunks and their environments, and the shims a
  known function value is widened through;
- the `&dyn` vtables and their thunks;
- panic helpers;
- the `pd` globals and the generated `kelp_init_pds`/`kelp_drop_pds`. A `pd`
  storage global is read by `main` and by the generated init function, so both
  readers sit outside the pd's own module; parking the storage in `_support`
  keeps the cross-unit reference in one direction instead of inventing an
  exported global per pd.

The name `_support` cannot collide with a module id: a module id is a path under
`src/` and a file must be a valid identifier, so it never starts with `_`.

### Cross-unit linkage

Every unit's module **declares** every function, static and pd global of the
program (a declaration costs no symbol in the object) and **defines** only what
it owns. Ownership is total: one symbol, one defining object.

- A symbol another unit references is external in its owner and a `declare` (or
  an `external global`) in the users; a symbol only its own unit uses is
  `internal`.
- The reference set is computed from the typed IR **before any module is
  built**: every callee, `FnRef`, closure literal, `StaticRef`, `pd` name, the
  dyn-vtable slot targets and the user `drop`/`hash`/`eq` methods the generated
  helpers call, plus two sources that are not in a unit's own bodies. The first
  is the widening of a *known* function value: its shim lives in `_support` and
  calls the function directly, so a function named as a value is referenced from
  outside its unit even when the reference was written inside it. The second is
  the per-program C object (`externs.c`): an `extern fun` body, the capability
  glue or a `std/rt` prototype can call a Kelp function across the object
  boundary in C, which no typed node shows, so the C text is scanned for the
  emitted symbol names. `main` is always external (the C runtime is what calls
  it). Everything `_support` defines is external, because a generated helper can
  be reached from any unit.
- An over-approximation is harmless (the symbol is merely visible); a missed
  reference is a link error, never a silent miscompile, which is why every
  equivalence test links the real binary.

Symbol names are already unique program-wide (module prefix plus type-argument
suffix) and stay exactly what they are today, so a unit's IR is reproducible:
emission order is a function of the program's own declaration order and of sorted
type/instantiation lists, never of a hash map's iteration order, and no counter or
pointer-derived name reaches a cross-unit symbol.

### Debug info and freestanding

- **Debug info is per unit.** The backend has no `-g` flag: DWARF is always on,
  and the builder is per lowering pass, so each unit gets its own compile unit
  naming its own first `.kp` file. A fault still resolves to the `.kp` file and
  line that caused it, and a multi-unit binary carries several compile units,
  which is ordinary DWARF.
- **Freestanding is refused by name** in this slice:
  `--incremental` with `[target] mode = "freestanding"` is an error naming the
  mode. The bare-metal path emits the entry stub, the panic state and the
  `probe-stack`/`noredzone` sweep at module scope, and its image is one ELF with
  no libc to link against; the split needs a single `_start` and one shared panic
  state rather than one per unit. That is its own slice. The refusal is a
  "not in this slice" decision, not a backend limitation: hosted LLVM is the
  default and the mode is defined for it.

### Slice 2: the object cache

Every unit is lowered to its LLVM IR either way, because the IR text is the
largest field of the key. The cache is then a pure lookup: on a hit the pass
pipeline and code generation for that unit are skipped and the stored object is
copied to `<out>.units/<unit>.o` (the artifact every build writes). On a miss the
unit is optimized, emitted and stored.

The design rests on one claim, and the whole slice is that claim: **a unit's
object is a pure function of (its IR text, target triple, CPU and feature
string, optimization level, relocation and code model, debug-info setting,
compiler version string)**. The IR already carries every front-end decision and
every cross-unit declaration, so if two IR texts are identical the objects are
identical, whatever changed elsewhere in the program. There is therefore no
dependency tracking and no interface file, and correctness cannot depend on a
dependency graph: a stale entry is impossible because the key names the exact
input that produced it.

#### The key

The key is the lowercase hex SHA-256 of a canonical byte string built from the
labelled fields and the IR text:

```
kelpc-object-cache-1
triple=...\ncpu=...\nfeatures=...\nreloc=...\ncode_model=...
opt=...\ndebug=...\ncompiler=...\nir-bytes=<n>\n<IR text>
```

Each field is labelled so its identity is part of the hashed bytes, and the IR
is last and length-prefixed because it is the one value that can contain a
newline. `opt` is the LLVM pipeline string (`default<O2>`), which pins the
module passes, and the machine's codegen level for that level is pinned by the
same one-to-one mapping. `compiler` is `kelpc <version>` plus the linked LLVM's
version: an object is the IR run through a specific LLVM, so a compiler built
against a different LLVM must not reuse these objects. SHA-256 is implemented in
`kelpc/src/sha256.rs` with the standard test vectors; `kelpc` deliberately has
no third-party dependency.

#### Layout and lifetime

The cache directory is `$KELPC_CACHE_DIR` when set, else `<out dir>/.kelpc-cache`
next to the build's other output, which for the default output path is
`build/.kelpc-cache`. Entries are `<key>.o`. A store writes a temporary file in
the same directory and then `rename`s it into place, so two concurrent builds
sharing one cache never observe a partial entry; the loser of the rename simply
installs the same bytes again. A lookup is a miss for an entry that is missing,
unreadable, empty, or visibly incomplete (an ELF whose section header table
falls outside the file), which is the corruption a truncated object presents.

A non-empty entry that survives that check but fails to link is not retried
silently: the link error is reported with the units whose objects came from the
cache, their entries are deleted, and the next build recompiles them. The build
that failed still fails; the deletion is the recovery, not a hidden second
try.

`KELPC_CACHE=off` turns lookups and stores off for one build. `KELPC_CACHE_STATS=1`
prints one stderr line, `kelpc cache: <H> hits, <M> misses, <S> stored`, and
`--timings` prints a per-phase line and a per-unit `hit`/`miss` line with
milliseconds. `KELPC_CACHE_MAX_MB` (default 1024) is the size cap: at the end of
a build, entries are deleted oldest-modified first until the total is under it.
`kelpc cache stats` prints the entry count and total size and `kelpc cache clear`
deletes the entries; both take `--dir`.

#### The limits this keeps

- **No cross-unit inlining.** Unchanged from slice 1: a call between two units
  is a real call in the object. The cache does not change this and cannot.
- **The cache grows with distinct IR.** A body edit produces a new key and a new
  entry; the old one is not evicted until the size cap or `kelpc cache clear`
  removes it. The cap is what bounds it, and it deletes by modification time, so
  a long-lived cache keeps the most recently useful objects.
- **The cache is not shared between machines.** The key names the triple, CPU,
  features, relocation and code model, so a directory copied to a different
  machine simply misses and rebuilds. It is also not shared across `kelpc`
  versions or LLVM versions, by the `compiler` field.
- **A signature change is broad.** Every unit declares every program item, so
  changing one callee's signature changes the declaring IR in more units than
  the caller's; they all miss. That is the price of having no interface files,
  and it is correctness rather than a defect: the alternative is a dependency
  graph the design deliberately refuses.

### Slice 3: parallel unit compilation

The work done here is a cache miss and nothing else: a hit is a file copy and
stays on the calling thread. A miss for one unit is lowered, optimized and
emitted on a worker thread, with its own LLVM state, and the objects are linked
once every worker has joined.

#### Worker count and LLVM initialization

- The worker count is `KELPC_JOBS` when it is set to a positive integer, else
  **2**. The default is deliberately not the CPU count: this host has little
  memory, each worker holds an LLVM context and the module it is compiling, and
the floor below (`src/guard.rs`) ends a build before the machine swaps itself to
death. A value that does not parse, or `0`, is the default rather than an error,
the same shape `KELPC_MIN_AVAILABLE_MB` uses. More workers than units spawns one
worker per unit.
- LLVM's targets are registered once, in `codegen_llvm::compile`, **before** the
  first worker starts (`initialize_native_target` or `initialize_target_for`).
  The registration calls are not thread-safe to run concurrently, and there is no
  reason to: one registration serves every unit.
- The workers run inside `std::thread::scope`, so the borrows of the typed
  program, the drop plan, the source map and the cache are ordinary shared
  borrows and no `'static` clone of the program is needed.

#### One context per unit, one machine per worker

- **An LLVM context is not shared between threads.** Each unit creates its own
  `Context` (`LLVMContextCreate`) and lowers its own `Module` into it, so two
  units never touch one context's type table at the same time, and a unit that
  panics drops exactly its own context instead of poisoning a shared one.
- A worker owns one `TargetMachine` for its whole life: the machine is a
  read-mostly description of the target, the machine fields in the cache key are
  identical for every worker, and building it once per worker rather than once
  per unit keeps the fixed cost out of the per-unit time. The machine is created
  after the worker starts and never crosses a thread boundary.
- `TargetMachine::data_layout()` is still read before any type is built, exactly
  as in the other two modes, so a unit's layout and the object it emits agree.

#### Determinism

- The unit list is the one `plan_units` already produces: every module id sorted,
  then `_support`. Every part of a unit's lowering is a function of the typed
  program, never of wall-clock order or of which worker got there first.
- Each worker writes its results into a slot indexed by the unit's position in
  that list, and the caller links the object paths **in that order**, whatever
  order the workers finished in. Two builds of the same sources therefore write
  the same objects and the same link line at `KELPC_JOBS=1` and at
  `KELPC_JOBS=4`; the determinism test compares the unit IR, the unit objects/
  byte-for-byte and the linked binaries' stdout.
- `--timings` still prints one line per unit in unit order and the phases sum the
  workers' times, so the readout is a property of the program and not of the
  schedule.

#### A unit that fails

- A unit's error or panic fails **the build**, naming that unit, but it does not
  stop the other workers: each unit runs inside `catch_unwind`, a failure is
  recorded against its index, and the remaining units are still processed so
  their cache entries are stored. After every worker has joined the caller scans
  the results in unit order and returns the first failure's message, so which
  unit is named does not depend on which worker lost the race.
- Partial progress is kept: the units that succeeded before the failure have
  their objects in the cache, and the next build resumes from them. The failed
  unit has no entry (its object was never stored), so the next build retries it.
- A panic is isolated to its own unit and its own context; the worker keeps its
  machine and continues with the next unit. The process does not abort and no
  other unit's work is discarded.
- The failure path is exercised with a real LLVM-level error, not a front-end
  refusal: the test-only `KELPC_TEST_CORRUPT_UNIT=<unit>` hook appends an
  unterminated basic block to that unit's module just before LLVM's verifier
  runs, so `LLVMVerifyModule` rejects it and the error names the unit. It is
  compiled into the binary but does nothing unless the variable names a unit.
  The variable is a test hook, not a user surface, and is absent from `usage()`.

#### The memory floor with workers running

The guard (`src/guard.rs`) is unchanged and keeps working:

- Its watchdog is a thread of its own. When `MemAvailable` falls below the floor
  it prints one line and calls `_exit(75)` from that thread. `_exit` is a
  process-wide immediate exit and runs **no** destructors on any thread, so the
  workers' live LLVM contexts and half-built modules are simply discarded by the
  kernel; no destructor runs under a running LLVM call and there is nothing to
  corrupt. The exit status stays 75.
- The floor can fire while unit workers are alive. No `cc` or `ld.lld` child is
  running during that phase (the per-program C object is compiled before the
  units and the link happens after they join), so there is no child for the guard
  to kill at that moment, and it does not need one: the workers die with the
  process.
- The memory-floor test is run for the whole-program build and for an
  `--incremental` build with workers, and both end with status 75.

### What these slices do not do

- It does not parallelize the front end: parse, resolve, infer and borrowck stay
  whole-program and sequential, which is the design (`The decision` above). Only
  unit compilation and codegen leave the calling thread.
- It does not inline across units, and that is the documented cost of the mode:
  a call between two modules is a real call in the object, not an inlinable one.
  Inside a unit, the existing pipeline is unchanged.
- It does not change the front end, the borrow checker, the C backend, or any
  diagnostic.
- The unit artifacts are written to `<out>.units/<unit>.ll` and
  `<out>.units/<unit>.o`, next to the binary the build produces.

### Measured numbers (slice 3)

Host: the small dev machine this work runs on (7.8 GiB RAM, limited free
memory), through `dev.nix`. Every cell is the **median of three runs**, in
milliseconds, of a real `kelpc` binary: the debug build
(`target/debug/kelpc`) and the release build (`target/release/kelpc`,
`cargo build --release --bin kelpc`). Both are available, so both are reported.
"Warm" is a build of unchanged sources whose cache the preceding build filled;
"edit" is one literal changed in one module of a program whose cache was filled
by the unedited build, so exactly that module misses.

The three programs:

- `hello`: `examples/hello.kp`, the 3-line example.
- `http_rate_limit`: `kelpc/tests/projects/http_rate_limit`, the largest hosted
  project under `kelpc/tests/projects/` that binds `std/http` (about 100 lines of
  Kelp plus the shipped `std` modules it reaches: `std/http`, `std/str`,
  `std/result`, `std/option`, `std/process`, and everything they pull in).
- `download_pool`: `examples/download_pool.kp`, 203 lines, `std/http` plus
  `std/thread` and `std/process`.

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
  one module (`hello`: the greeting; `http_rate_limit`: the `http://` prefix in
  `src/main.kp`; `download_pool`: the `http://` prefix), then run the same command
  again and time it; each of the three edit runs restores the original source,
  which is a cache hit, and applies a fresh literal (`e1`, `e2`, `e3`), so each
  timed build is one miss and nothing else.

#### What the numbers say

- **Incremental does not pay for a tiny program.** `hello`'s whole-program build
  is 133 to 136 ms; a cold incremental build is 141 to 156 ms, and the warm and
  one-line-edit builds are within about 10 ms of whole-program (128 to 142 ms,
  which is this host's noise plus or minus a few ms). A build that small is the
  link (`cc` at the time of the measurement, `ld.lld` since 2026-10-10) plus a fixed per-unit overhead; there is almost no backend work to
  save, and splitting one module into a unit plus `_support` adds two pieces of
  work where there was one. The mode is off by default for exactly this shape.
- **It starts to pay once a program pulls in heavy `std` modules.** A ~100-line
  program that uses `std/http` (`http_rate_limit`) goes from 4992 to 3130 ms
  (debug) and 3487 to 2418 ms (release) for a cold incremental build at two
  workers: about 1.4 to 1.6 times faster. The warm and one-line-edit builds are
  about 2.1 to 2.7 times faster than whole-program (2372/2418 vs 4992 debug,
  1299/1323 vs 3487 release). That is the size at which the backend work the
  split saves is larger than the link and the per-unit overhead.
- **Parallelism is what makes the cold build fast.** Two workers against one:
  4472 to 3130 ms (debug) and 3187 to 2418 ms (release) for `http_rate_limit`,
  4590 to 3228 ms and 3265 to 2504 ms for `download_pool`; 1.3 to 1.4 times. It
  does not change the warm build much, because a cache hit still lowers every
  unit's IR to compute its key (the IR is the key's largest field), and the link
  at the end is serial.
- **A one-line edit costs about a warm build, not a cold one.** The changed unit
  is one small module; the other units still lower and the link still runs, so
  the edit build is within noise of the warm build (2372 vs 2418 ms debug for
  `http_rate_limit`, 1299 vs 1323 ms release) and well under the cold build
  (3130 ms debug, 2418 ms release at two workers). The saving is the other
  units' pass pipeline and codegen, not their lowering.

The numbers are not a claim that every project is faster: `hello` does not
benefit (its cold build is slower and its warm build is within noise), and the
threshold is a program whose own backend work is larger than the link, which on
this host is a program that reaches the heavy `std` modules.
