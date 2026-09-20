---
title: "Backends"
description: "Two code generators, chosen with --backend= or the KELPC_BACKEND environment variable. An explicit flag wins over the variable; the default is c."
isPublished: true
tags: "compiler"
---
Two code generators, chosen with `--backend=` or the `KELPC_BACKEND` environment
variable. An explicit flag wins over the variable; the default is `c`.

| Backend | Emits | Finished with | Status |
| --- | --- | --- | --- |
| `c` (default) | C source text | `cc -O2 -fwrapv -lm` | complete, and the reference |
| `asm` | x86-64 assembly text | `as --64`, then `ld` with `crt1.o`/`crti.o`/`crtn.o`, `-lc`, `-lm` | in progress, tier 1 of MK7 |

```sh
kelpc build examples/hello.kp --backend=asm
KELPC_BACKEND=asm kelpc run examples/hello.kp
```

No C compiler is in the `asm` chain: `as` assembles, `ld` links against glibc. If
the library directory is not found automatically, set `KELPC_GLIBC_DIR` to the
directory holding `crt1.o` and `libc.so`, which is also what the error message
says when it fails.

`backend.rs` holds only the selector: how a backend is named, which names exist,
and how the choice is resolved. The `match` that calls a generator stays at its
single call site in `main.rs`, and it becomes a trait when a third backend makes
the interface worth naming.

Source:
[`plan/mk7-own-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-own-backend.md).

## The C backend is the oracle

The fixture suite is backend-agnostic by construction: it compiles a fixture, runs
the result, and compares stdout. So a second backend is validated by running the
suite again with `KELPC_BACKEND` set to it, and the C backend's own output becomes
the thing the new backend is compared against, rather than a second opinion.

Two consequences worth knowing:

1. **A construct the `asm` backend cannot lower is refused by name, never
   miscompiled.** The refusal prefix is a constant in the test suite
   (`REFUSAL_PREFIX`, `kelpc/tests/backend_coverage.rs`), and the differential
   sweep asserts that every refusal begins with it:

   ```
   error: the 'asm' backend does not support the `extern fun std.time.now_unix_raw` yet
   ```

2. **A refusal is a feature.** The backend earns coverage by agreeing with the C
   backend on the fixtures it does build, and the coverage number can only rise.

## What the assembly backend covers

From its module header: every integer width, `bool`, `char`, `f32`/`f64`
arithmetic and comparison (including the unordered/NaN case), all unary and
binary operators including short-circuiting `&&`/`||`, `if`/`else` in statement
and value position, `while`, `for` (which desugars to a `while`), assignment, a
borrow of a named scalar local with the read and the store through it
(`*p`/`*p = v` for an integer or float pointee), calls with up to six integer
and eight float arguments classified independently per the SysV ABI, recursion,
`print`/`print!` of integers, characters, booleans, `str`, floats and an owned
buffer, `panic`/`assert`, `datac` aggregates by value at any size (including a
`MEMORY`-class one as an argument) with `f32`/`f64` fields, the six heap types
`Bytes`, `String`, `View`, `Box<T>`, `List<T>` and `Map<K, V>` with their own free
at every drop point, `enum` tagged unions with `f32`/`f64` payloads and a
generated per-`enum` drop that switches on the runtime tag (`when`, `if let`
and `?` all lower on top of them), the three `str` parsers
(`strtoll`/`strtoull`/`strtod` behind `externs.rs`'s own whitespace,
whole-string and `errno` checks), `List`'s comparison-and-clone methods
(`sort`, `contains`, `slice`, `clone`, for an element that is a number, `bool`,
`String` or `Bytes`; a `datac`/`enum` element's derived copy and order is a C-backend
surface as of the newest compiler commit, see the refusal list below), an owned
`String`/`Bytes`/`View` interpolated
into a `print` template (a piece costs two integer arguments, not one, and the five
non-float argument registers are the ceiling: a template with three owned pieces is
refused as `a print with more than five non-float interpolation arguments`), a `pd`'s
generated storage, `[T; N]` fixed-size arrays (a synthesized layout per element
type and length, so one is an ordinary by-value aggregate: `len()`/`is_empty()`
are the type's own constants, `get`/`set` are bounds-checked over the element's
stride, and an element that owns memory is dropped per element), a function that
returns a borrow of anything (`&str` was the only shape whose pointer-in-register
return this backend classified), and calls to the
`extern fun`s whose bodies this backend owns or can forward to libc through the
PLT.

The aggregate ABI behind that is a real per-eightbyte SysV classifier, not a size
test: an eightbyte is `SSE` only if every field overlapping it is a float or a
double, otherwise `INTEGER`, an `enum`'s payload eightbytes are classified
through the union, so a non-float variant sharing an eightbyte merges it back to
`INTEGER`, and an aggregate over sixteen bytes is `MEMORY`. That is what lets an
aggregate travel in `xmm` registers, or in an `INTEGER`+`SSE` register pair, as
well as in `rax` or the argument area. It is also the one place a differential
stdout comparison cannot see a mistake — both ends of every generated call are
this backend, so a *self-consistent* wrong register choice still prints the right
number — so the ABI is pinned by a `.s`-level test
(`the_classifier_puts_each_aggregate_eightbyte_in_its_own_register_file`,
`kelpc/tests/compile_and_run.rs`) that reads the emitted assembly and asserts the
register each eightbyte shape uses.

What it does not cover yet is the refusal list below: closures and function
values; the heap-bodied `fs`/`io`/`net`/`path`/`process` externs; a
gated call; a `List.clone`/`sort`/`slice` over a `datac` or `enum` element, whose
derived copy and order the newest compiler commit added to the frontend and to the
C backend; and a borrow of a field chain (`&xs.get(i).v`).

Its layout:

| Decision | Why |
| --- | --- |
| A stack machine: every expression evaluates into `rax`, and a binary operator spills the left operand to the stack | it is simple to get right, and correctness here is security-relevant |
| A linear-scan register allocator on top, pinning an integer/`bool`/`char` local to one of five callee-saved registers (`rbx`, `r12`-`r15`) for the whole function when its live range fits | removes memory traffic for locals without touching expression evaluation; `f32`/`f64` locals are deliberately excluded |
| One layout key per container (`$List`, `$Map`) rather than one per element type | the element or value pointer is what the routines move, so one routine set per instantiation and one growth helper whose element size is an argument serve every `List<T>` |
| The calling convention is generated, not assumed: stack-passed arguments and the `MEMORY`-class paths are emitted from one shared `memory_arg_area` | a call site and a callee's prologue have to agree, and generating both from one function is what makes them |

## How much of it works today

Measured at compiler commit `c3a8759` by building each fixture with both
backends, and recorded
in [`plan/mk7-own-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-own-backend.md)
§0 and §5. Those two sections own these numbers; this page quotes them.

| | Count |
| --- | --- |
| Fixture files under `kelpc/tests/fixtures/*.kp` | 357 |
| Rejected by the compiler itself (the `should fail` fixtures) | 156 |
| Accepted by the compiler | 201 |
| of those, built by the `asm` backend | 176 |
| of those, refused by the `asm` backend with the documented prefix | 25 |
| of those, failed for any other reason | 0 |

The plan's own status table records the *suite* number: **285 of 336** integration
tests passing under `--backend=asm`, with the C backend passing all 336, which
counts multi-file projects and subprocess cases too, and so is not the same
denominator as the fixture count above. Re-measure either before quoting it: both
move with every slice, and the plan's header says it is updated as work lands.

### What the 25 refusals are

The differential sweep groups the refusals into the categories the plan's ranking
table uses (`cargo test --test backend_coverage -- --ignored --nocapture` prints
it verbatim, and it is the number the ratchet keeps honest). Six rows are printed
and three of them are empty:

| Category | Fixtures |
| --- | --- |
| a heap type | 14 |
| a fixed-size array (A-18) | 0 |
| an `enum` | 0 |
| a `datac` holding a float or heap field | 0 |
| a closure or a function value | 10 |
| a gated `extern` | 1 |

Rows a previous version of this page carried are empty now, which is what the
slices in between did: an `enum` whose payload is a float and a `datac` holding a
float field (the float-in-aggregate slice lowered both), and a fixed-size array
(the A-18 slice, whose `[T; N]` is a synthesized by-value layout on this backend
now, so both its literals and the type itself lower).

One refusal per non-empty row, and the heap row's two shapes with it, as the
backend names them:

```
error: the 'asm' backend does not support the `extern fun std.io.is_open_raw` yet
error: the 'asm' backend does not support the method `List.clone` on a `List` yet
error: the 'asm' backend does not support the parameter `f: &closure(i32).R: i32` of `apply` yet
error: the 'asm' backend does not support the `extern fun std.time.now_unix_raw` yet
```

The heap-type row is the largest one and it is the catch-all, not one gap: 12 of
its 14 name an `extern fun` whose body this backend has no routine for, one names
the `List.clone` a `datac` element's derived copy needs, and one names a borrow of
a field chain. A build stops at the first refusal it hits, so a fixture that would
also meet a closure or a `List` method later is counted here when the first thing
in its way is a heap type, a standard-library call over `net`/`io`/`process`/`fs`,
or the `extern fun` behind one of those (the ranking treats an `extern fun` whose
body this backend has no routine for as part of the heap row, because the
allocator is what unblocks almost all of it). The category is recovered from each
fixture's first refusal message, so a fixture can move rows when a message's
wording changes. That is also why the gated-`extern` row is one fixture rather
than ten: ten fixtures the C backend builds import a gated module, and every one
of them names an extern body first, so the capability check is still masked
behind the extern bodies and is the first refusal of none of them. The ranking
table this page summarizes, and the per-fixture lists behind it, are in
[`plan/mk7-own-backend.md` §5](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-own-backend.md),
with the measured brief for the next slice in `plan/mk7-next-slice.md`.

Re-measured at that commit, item 4 is closed outright: the container set is closed
(`Box`, `List`, `Map` all lower) and so is the aggregate set: the per-eightbyte
classifier admits a `datac` field or an `enum` payload holding a float exactly as
it admits an integer one, and an aggregate over sixteen bytes goes `MEMORY`-class.
The six heap types free themselves at every drop point, an owned passdown frees
itself at process exit (the generated `kelp_drop_pds`, registered with `atexit`
exactly as the C backend's handler is), and what is left is one construct family
at a time: closures, the heap-bodied `fs`/`io`/`net`/`path`/`process` externs, a
gated call, the derived copy and order for a `datac`/`enum` list element, and a
borrow of a field chain. The most recent slices closed the `List`
comparison-and-clone methods for a numeric, `bool`, `String` or `Bytes` element
and an owned piece in a `print` template, which is why this implementation now
builds 176 of the 201 fixtures the C backend accepts.

## Stages beyond tier 1

The plan splits the work into tiers, and only the first is in progress:

| Stage | State |
| --- | --- |
| 0: the backend boundary | done |
| 1: x86-64 assembly text, `as` + `ld` | in progress (see above) |
| 2: machine-code bytes and a linker of our own | not started; tier 1 must pass the suite first |
| 3: freestanding, no libc | not started; blocked on tier 2 |
| 8: runtime decoupling (parallel track) | in progress; see [Runtime](/compiler/runtime) |

The memory gate is a test rather than an argument: `kelpc/tests/memory_gate.rs`
runs `valgrind` over both backends' binaries, and its last run checked
201 binaries from the C backend and 176 from the `asm` one, out of the 357
fixtures in the directory, which skipped the 25 this backend refuses and the 156
the compiler itself rejects, with zero findings from any of them. So it asserts no
findings, because the AddressSanitizer gate instruments generated C and cannot see
this backend. See [Tests](/compiler/tests).

## See also

- [Pipeline](/compiler/architecture)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Install and build](/getting-started/install): the flags and environment variables
