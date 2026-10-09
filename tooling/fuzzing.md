---
title: "Front-end fuzzing and parser limits"
description: "How the front end is fuzzed, what it found, and the two limits the parser now enforces: 200 levels of nesting and 800 links in a chain, with the exact error text from real kelpc check runs."
isPublished: true
tags: "tooling, testing, limits"
---
A compiler should answer junk with a diagnostic, never with a crash. The front end
(everything `kelpc check` runs: lexer, preprocessor, module resolution, parser,
type inference, borrow check and the diagnostic renderers) is fuzzed for exactly
that, and what the fuzzer found turned into two parser limits that a program can
meet. The plan is
[`plan/fuzzing.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/fuzzing.md).

## The two fuzzers

1. `kelpc/tests/differential_fuzz.rs` generates valid programs from a seed and
   compares the C oracle with the LLVM backend byte for byte. It asks whether the
   backends agree, never whether the compiler survives junk.
2. `kelpc/tests/frontend_fuzz.rs` mutates the 800-odd fixtures in
   `kelpc/tests/fixtures/` and feeds the result to `kelpc check`. The property is
   **survival**: no panic, abort, stack overflow, hang or memory blowup. The
   outcome is either exit 0 or a diagnostic and exit 1.

The mutations are deterministic (mutation `i` is a pure function of
`FUZZ_SEED_BASE + i`): delete, duplicate or swap a token or a line; truncate at a
character boundary or in the middle of a code point; insert a keyword, operator
or bracket; nest brackets, prefix operators, type arguments or blocks up to
100,000 deep; replace a number with a boundary or huge literal; insert odd
Unicode, NUL bytes, bidi controls, stray escapes or raw invalid UTF-8. One to
three are stacked per mutant. Each mutant runs as a subprocess under
`ulimit -v 2097152; ulimit -t 20` and a 40 s wall clock, half of them with
`--json`, because the renderer's column arithmetic is a classic panic site.

Not fuzzed: LLVM IR validity beyond the verifier, the linker and `cc`, `kelpc
build` option parsing, `coral.toml` parsing, `fmt` and `lint`, and the
incremental cache. Only survival is checked, not that the diagnostic is a good one.

### Running it

From the compiler repository's `kelpc` directory:

```text
# default suite: 2,000 mutations, seeds 1..2000 (about 30 s)
cargo test --test frontend_fuzz

# replay one mutant
FUZZ_SEED_BASE=1004247 FUZZ_MUTATIONS=1 cargo test --test frontend_fuzz fuzz_frontend

# the maintainer's run: 100,000 mutations, seeds 1,000,000.. (an hour or more)
cargo test --release --test frontend_fuzz fuzz_frontend_long -- --ignored --nocapture
```

A failing mutant is saved as `FAIL_mutant_<seed>.kp` under
`target/tmp/frontend_fuzz/<short|long>/` and named in the failure message. A fixed
case is kept, minimized, in `kelpc/tests/fuzz-corpus/frontend/` and replayed by
`the_frontend_regression_inputs_stay_survivable`. After the fix below, 12,000
mutations on seeds 1,000,000.. and the default 2,000 were clean. (These commands
were not run for this page; the figures are the plan's.)

## What it found, and the limits that came of it

Deeply nested or very long left-leaning input overflowed the compiler's stack and
aborted it, because every later pass walks the tree recursively. The parser now
refuses, with a normal diagnostic:

- more than **200 levels of nesting** (expression, unary, type, type argument,
  block and binding pattern, one inside another);
- more than **800 links** in a chain of operators or accesses (the loop that builds
  one does not recurse, but the tree it makes is as deep as the chain is long).

Written Kelp stays far below both: the deepest fixture nests under 30 levels.

### The messages

Nesting, here 100 parentheses around a literal (`val x: i32 = ((( ... 1 ... )))`
inside `fun main`):

```text
$ kelpc check p100.kp; echo "rc=$?"
error: this nests more than 200 levels deep (expressions, blocks, types and patterns inside one another); split it into smaller pieces
  --> p100.kp:2:117
rc=1
```

A chain, 801 terms joined by `+` (`val x: i32 = 1 + 1 + 1 ...`):

```text
$ kelpc check chain801.kp; echo "rc=$?"
error: this chain of operators or accesses is longer than 800 links; split it into smaller pieces
  --> chain801.kp:2:3220
rc=1
```

The location is the column where the limit was crossed. A chain of exactly 800
`+` links passes (`rc=0`), and 801 is the first refused.

### The nesting count is levels, not characters

The nesting number counts the parser's own recursion, and one written construct
can cost more than one level. These are the largest depths that passed, and the
first that was refused, when the construct is the initializer of a `val` in
`fun main`:

| Written | Last accepted | First refused |
| --- | --- | --- |
| `((( ... 1 ... )))` | 98 parentheses | 99 |
| `- - - ... 1` (prefix `-`) | 197 | 198 |
| `{ { ... } }` (blocks) | 66 | 67 |
| `List<List< ... i32 ... >>` | 99 | 100 |

So 200 is the ceiling for the cheapest construct, and a deeply parenthesised
expression or nested block hits the error well before 200 written levels. Split the
expression with an intermediate `val`, or move the inner part to a function. These
figures come from a bisection with the prebuilt compiler; the exact cost of each
construct is the parser's business and can change.

## See also

- [Limits in v1](/language/limits), including how long chains and large literals
  scale in compile time
- [Sanitizer builds](/tooling/sanitizers), which cover runtime behavior of the
  compiled programs
- [`kelpc` CLI](/tooling/kelpc-cli)
