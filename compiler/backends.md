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
   error: the 'asm' backend does not support the enum `Maybe` yet
   ```

2. **A refusal is a feature.** The backend earns coverage by agreeing with the C
   backend on the fixtures it does build, and the coverage number can only rise.

## What the assembly backend covers

From its module header: every integer width, `bool`, `char`, `f32`/`f64`
arithmetic and comparison (including the unordered/NaN case), all unary and
binary operators including short-circuiting `&&`/`||`, `if`/`else` in statement
and value position, `while`, `for` (which desugars to a `while`), assignment,
calls with up to six integer and eight float arguments classified independently
per the SysV ABI, recursion, `print`/`print!` of integers, characters, booleans,
`str`, floats and an owned buffer, `panic`/`assert`, `datac` aggregates by value
at any size (including a `MEMORY`-class one as an argument), the six heap types
`Bytes`, `String`, `View`, `Box<T>`, `List<T>` and `Map<K, V>` with their own free
at every drop point, a `pd`'s generated storage, and calls to the `extern fun`s
whose bodies this backend owns or can forward to libc through the PLT.

What it does not cover yet is the refusal list below: `enum` (and therefore
`Option`/`Result`, `if let` and `?`), closures and function values, a `datac`
holding a float or a heap field, the `List` methods that need an element
comparison or a clone (`sort`, `contains`, `slice`), an owning `pd`, and a
capability-gated call. Printing through `fmt`'s `Display` machinery is not
covered either.

Its layout:

| Decision | Why |
| --- | --- |
| A stack machine: every expression evaluates into `rax`, and a binary operator spills the left operand to the stack | it is simple to get right, and correctness here is security-relevant |
| A linear-scan register allocator on top, pinning an integer/`bool`/`char` local to one of five callee-saved registers (`rbx`, `r12`-`r15`) for the whole function when its live range fits | removes memory traffic for locals without touching expression evaluation; `f32`/`f64` locals are deliberately excluded |
| One layout key per container (`$List`, `$Map`) rather than one per element type | the element or value pointer is what the routines move, so one routine set per instantiation and one growth helper whose element size is an argument serve every `List<T>` |
| The calling convention is generated, not assumed: stack-passed arguments and the `MEMORY`-class paths are emitted from one shared `memory_arg_area` | a call site and a callee's prologue have to agree, and generating both from one function is what makes them |

## How much of it works today

Measured on 2026-09-19 with the release binary, over
`kelpc/tests/fixtures/*.kp` (279 files), by building each fixture with both
backends:

| | Count |
| --- | --- |
| Rejected by the compiler itself (the `should fail` fixtures) | 134 |
| Accepted by the compiler | 145 |
| of those, built by the `asm` backend | 97 |
| of those, refused by the `asm` backend with the documented prefix | 48 |
| of those, failed for any other reason | 0 |

The plan's own status table records the *suite* number: `193 of 266` integration
tests passing under `--backend=asm`, with the C backend passing all 266, which
counts multi-file projects and subprocess cases too, and so is not the same
denominator as the fixture count above. Re-measure either before quoting it: both
move with every slice, and the plan's header says it is updated as work lands.

### What the 48 refusals are

The differential sweep groups them into the categories the plan's ranking table
uses (`cargo test --test backend_coverage -- --ignored --nocapture` prints it
verbatim, and it is the number the ratchet keeps honest):

| Category | Fixtures |
| --- | --- |
| a heap type | 20 |
| an `enum` | 18 |
| a `datac` holding a float or a heap field | 2 |
| a closure or a function value | 7 |
| a gated `extern` | 1 |

One refusal per category, plus a second from the heap row (its refusals come from
more than one place), as the sweep prints them:

```
error: the 'asm' backend does not support the parameter `s: &Shape` of `area` yet
error: the 'asm' backend does not support the parameter `f: &closure(i32).R: i32` of `apply` yet
error: the 'asm' backend does not support the parameter `self: &Circle` of `Circle#area` yet
error: the 'asm' backend does not support the method `List.sort` on a `List` yet
error: the 'asm' backend does not support the passdown `pd primes` (its type is `List<i32>`, and the
  asm backend does not yet free a passdown at process exit — see plan/mk7-own-backend.md §5) yet
error: the 'asm' backend does not support the `extern fun std.time.now_unix_raw` yet
error: the 'asm' backend does not support this struct-returning expression (only a struct literal, a
  named local, or a call are supported for a value over eight bytes wide) yet
```

The heap-type row is the largest one and it is the catch-all, not one gap: a
build stops at the first refusal it hits, so a fixture that would also meet an
`enum` later is counted here when the first thing in its way is a heap type, an
owned passdown, a standard-library call over `net`/`io`/`process`/`fs`, or the
`extern fun` behind one of those (the ranking treats an `extern fun` whose body
this backend has no routine for as part of the heap row, because the allocator is
what unblocks almost all of it). The category is recovered from each fixture's
first refusal message, so a fixture can move rows when a message's wording
changes. The ranking table this page summarizes, and the per-fixture lists behind
it, are in
[`plan/mk7-own-backend.md` §5](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-own-backend.md),
with the measured brief for the next slice in `plan/mk7-next-slice.md`.

Re-measured 2026-09-19, this is the state the plan calls "past halfway": the
container set is closed (`Box`, `List`, `Map` all lower), the six heap types
free themselves at every drop point, and what is left is one construct family at
a time — `enum`, closures, a `datac` with a float or heap field, the
comparison-and-clone `List` methods, an owning passdown, and a gated call.

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
runs `valgrind` over both backends' binaries (145 built by the C backend, 97 by
the `asm` one) and asserts no findings, because the AddressSanitizer gate
instruments generated C and cannot see this backend. See [Tests](/compiler/tests).

## See also

- [Pipeline](/compiler/architecture)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Install and build](/getting-started/install): the flags and environment variables
