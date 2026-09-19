# Backends

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
directory holding `crt1.o` and `libc.so` — which is also what the error message
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
suite again with `KELPC_BACKEND` set to it — and the C backend's own output becomes
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

From its module header and the plan's status table: every integer width, `bool`,
`char`, `f32`/`f64` arithmetic and comparison (including the unordered/NaN case),
unary and binary operators including short-circuiting `&&`/`||`, `if`/`else` in
statement and value position, `while`, assignment, calls with up to six integer
and eight float arguments classified independently per the SysV ABI, recursion,
and `print`/`print!` of integers, characters, booleans, strings and floats.

Its layout:

| Decision | Why |
| --- | --- |
| A stack machine: every expression evaluates into `rax`, and a binary operator spills the left operand to the stack | it is simple to get right, and correctness here is security-relevant |
| A linear-scan register allocator on top, pinning an integer/`bool`/`char` local to one of five callee-saved registers (`rbx`, `r12`-`r15`) for the whole function when its live range fits | removes memory traffic for locals without touching expression evaluation; `f32`/`f64` locals are deliberately excluded |
| One growth helper (`kelp_rt$list_reserve`) that is *not* monomorphised | the element size is an argument, so one routine serves every `List<T>` |

## How much of it works today

Measured on 2026-09-19 with the release binary, over
`kelpc/tests/fixtures/*.kp` (279 files), by building each fixture with both
backends:

| | Count |
| --- | --- |
| Rejected by the compiler itself (the `should fail` fixtures) | 134 |
| Accepted by the compiler | 145 |
| — of those, built by the `asm` backend | 97 |
| — of those, refused by the `asm` backend with the documented prefix | 48 |
| — of those, failed for any other reason | 0 |

The plan's own status table records the *suite* number — `182 of 260` integration
tests passing under `--backend=asm`, with the C backend passing all 260 — which
counts multi-file projects and subprocess cases too, and so is not the same
denominator as the fixture count above. Re-measure either before quoting it: both
move with every slice, and the plan's header says it is updated as work lands.

Typical refusals, from the same run:

```
error: the 'asm' backend does not support a function value yet
error: the 'asm' backend does not support the method `List.sort` on a `List` yet
error: the 'asm' backend does not support the return type `std.option.Option<usize>` of `taken` yet
error: the 'asm' backend does not support the `extern fun std.net.connect_raw` yet
error: the 'asm' backend does not support the `extern fun std.str.parse_i64_raw` yet
error: the 'asm' backend does not support the passdown `pd banner` (its type is `String`, and the
  asm backend does not yet free a passdown at process exit — see plan/mk7-own-backend.md §5) yet
```

## Stages beyond tier 1

The plan splits the work into tiers, and only the first is in progress:

| Stage | State |
| --- | --- |
| 0 — the backend boundary | done |
| 1 — x86-64 assembly text, `as` + `ld` | in progress (see above) |
| 2 — machine-code bytes and a linker of our own | not started; tier 1 must pass the suite first |
| 3 — freestanding, no libc | not started; blocked on tier 2 |
| 8 — runtime decoupling (parallel track) | in progress; see [Runtime](runtime.md) |

## See also

- [Pipeline](architecture.md)
- [Runtime](runtime.md)
- [Tests](tests.md)
- [Install and build](../getting-started/install.md) — the flags and environment variables
