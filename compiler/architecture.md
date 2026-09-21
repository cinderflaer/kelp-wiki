---
title: "Pipeline"
description: "Every stage below reads the previous stage's output and hands one structure on - source text, tokens, an untyped AST, a typed IR, a drop plan, and finally C or LLVM IR. The pass boundaries are..."
isPublished: true
tags: "compiler"
---
Every stage below reads the previous stage's output and hands one structure on:
source text, tokens, an untyped AST, a typed IR, a drop plan, and finally C or
LLVM IR. The pass boundaries are deliberate: a checker bug is easier to find
when the pass that owns it is the only one running.

Authority:
[`plan/architecture.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/architecture.md),
"Compiler crate layout" and "Key implementation notes".

## Lexing (`lexer.rs`)

Source text to span-carrying tokens. Every token carries a byte range
(`Span { start, end }`), which is what makes a diagnostic point at a line and
column rather than at an offset. Two details matter downstream:

- The lexer is **newline-sensitive**: a newline ends a statement, which is why the
  language has no semicolons.
- `tokenize_with_trivia` keeps comments as tokens. `kelpc fmt` is built on that
  entry point, because the parser's input drops comments and the AST has no node
  for them.

## Preprocessing (`preprocess.rs`)

`%*alias*%` substitution, a flat, global, purely textual pass with no parameters,
no hygiene and no scoping. Two definition sites feed one table:

| Source | Form |
| --- | --- |
| `alias.kpconf` at the project root | one `name="replacement text"` per line |
| an inline declaration in any `.kp` | `alias %*name*% = <raw text to end of line>` |

The right-hand side is macro text, never type-checked, which is why the
declaration has its own keyword. The pass runs over the token stream before the
parser and keeps **both** the definition span and the use span, so an
alias-induced type error still points somewhere useful.

## Parsing (`parser.rs`)

Recursive descent for declarations and statements, with a Pratt parser for
expression precedence. Three constructs do not survive parsing as themselves:

- `if let` is desugared into a match with a synthesized scrutinee binding
  (the parser names it under `IF_LET_PREFIX`), which is what lets `if let Ok(v) =
  f(x)` accept a temporary scrutinee at all.
- `for x in xs` is desugared into the index-and-`while` walk (under `FOR_PREFIX`),
  so no later pass knows the loop kind exists and there is no iterator protocol to
  implement.
- A `when` whose scrutinee is not a place is desugared in `infer.rs`
  (`check_when_scrutinee`, under `WHEN_TEMP_PREFIX`) into the same block a
  hand-written `val h = ...` would give, because the arms borrow a payload and
  the borrow has to outlive them. Both desugarings stage the *root* of a field
  chain (`ast::temporary_root`), so the whole temporary is freed once.

`pretty.rs` is an AST printer and is dead code: a formatter cannot be built on
the AST, for the reasons `fmt.rs`'s header gives.

## Modules and resolution (`resolve.rs`)

Multi-file loading and name resolution:

- `impl "shapes/circle"` loads `src/shapes/circle.kp`, which is reached as `circle`:
  the last path segment, except that a module whose path ends in `/lib` under `deps/`
  takes the name of the directory Coral fetched it into
  (`impl "deps/argparse/lib"` is `argparse`). The `as name` clause that used to
  choose the name is gone, and the parser refuses it by name; the `with` that
  used to introduce a capability grant is outdated, and a build warns about it,
  with the clause now written `caps(...)` on its own.
- Paths are relative to `src/`, may not contain `..`, and may not reach outside the
  project.
- Names are strictly module-qualified: module `m`'s items are reachable elsewhere
  only as `m.Item`, and bare inside `m` itself.
- **Capability gating happens here.** Each module has a capability-domain set
  computed from its incoming `caps(...)` grant; resolving `net.connect` in a
  module whose set lacks `net` is an undefined-name error, not a runtime check that
  could be forgotten. See [Capabilities](/language/capabilities).

`std/…` ids go through the same path with their text coming from `stdlib.rs`, so
the standard library is compiled by the same lexer, parser and checker as user
code.

## Type checking (`infer.rs`)

The largest pass (~7.6k lines). It owns:

- type inference and checking over the AST, including generics and `Option`/`Result`;
- **stdlib-only argument-type overloading** for `math.abs`/`min`/`max`/`clamp`;
- resolving `datac`-typed parameters into `Ty::Ref` and synthesizing the borrow
  node at call sites: callers never write `&`;
- the `when`/`if let` pattern rules, including that a payload binds as a copy when
  it is `Copy` and as a shared borrow otherwise;
- rejecting an `extern` that has no compiler-supplied body;
- **compile-time evaluation** (A-19), which runs here rather than as a pass of its
  own: a `const` initializer and an array's `[T; N]` length are folded by a small
  evaluator over the AST (`ConstEvaluator`), which binds parameters and walks the
  body of a plain `fun` the constant calls. It carries its own step and call-depth
  budget, and it runs before any signature is built, so a `const` and the `fun` it
  calls may reference each other in either order.

The output is `tir.rs`: the same shape, every node annotated with its resolved
type and span.

## Move and borrow checking (`borrowck.rs`)

Two milestones in one pass, over the typed IR:

| Rule | Detail |
| --- | --- |
| Moves | scalars and `&str` are `Copy`; a `datac` is not, so a bare identifier read moves it, while a `.field` read goes through the place chain without consuming anything |
| Borrows | a `datac` parameter is a shared borrow unless `mut`-marked; a borrow lives to the end of its scope, with a statement-sized exception for a borrow taken inside an initializer |
| Drops | the pass produces a **drop plan** keyed by span, which the code generators consult: no second walk, and no lockstep between two passes |

The drop plan is why `codegen_c.rs` only has to ask "which locals die at the end of
this block" and "which die before this return" as it writes each one, and
`codegen_llvm.rs` asks the same two questions at the same points.

## Code generation

| Module | Emits | Notes |
| --- | --- | --- |
| `codegen_c.rs` | C source text | value-position blocks use the GNU statement-expression extension `({ ...; expr; })`, which both `gcc` and `clang` accept; the `Bytes`/`String` runtime (allocation, bounds checks, `free`) is the text of `kelpc/runtime/kelp_rt.c`, emitted into every generated program; the generated C carries a `#line` directive before every statement, so a `cc` failure names the `.kp` file and the line the statement is written on (plan item 20, closed) |
| `codegen_llvm.rs` | LLVM IR | the MK7 backend: a peer of `codegen_c.rs` over the same `tir`, covering the scalar subset (S1), `datac` records (S2A), the heap slice (S2B: `Bytes`/`String` through the runtime, an owned field, the drop plan, `panic`/`assert`), tagged unions (S2C: `enum` at the C `{ tag, union }` layout, `when`, `if let`, `?`, one `switch` per drop) and the containers (S2D: `List`, `Map`, `Box` and `[T; N]` at the C backend's header layouts), and references that are not a `datac` (S2F: `Ty::Ref` is one `ptr` whatever the pointee, so `&place` is the place's address, `*p` a pointee-typed load and `*p = v` a store, and a `&T` parameter or return is a `ptr`), and refusing everything outside them by name. See [Backends](/compiler/backends) and [`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md) |
| `kelpc/runtime/kelp_rt.c` | the C runtime text, not a compiler module | the single source for the bytes/string routines, the panic and assert paths, the allocation helpers and `kelp_argc`/`kelp_argv`: `codegen_c.rs` emits it into every generated program, and the `llvm` path links it as an object |
| `kelpc/build.rs` | the runtime object | compiles `kelp_rt.c` once, at `kelpc`'s own build time, into `kelp_rt.o`; `driver.rs` embeds that object with `include_bytes!` and writes it to a temporary file when the `llvm` path links |

Details, and what each backend refuses, are in [Backends](/compiler/backends).

## Finishing (`driver.rs`)

The only place in the compiler that invokes an external tool, and a backend does
not share it:

| Backend | Steps |
| --- | --- |
| `c` | write `<out>.c` beside the binary, then `cc -O2 -o <out> <out>.c -fwrapv -lm` |
| `llvm` | write `<out>.ll` and `<out>.o` beside the binary, then `cc -O2 -o <out> <out>.o -lm` |

The generated C is deliberately **kept** next to the binary rather than deleted,
so debugging the generated program is `gdb ./foo` against a file that is actually
there. `-fwrapv` makes signed overflow wrap in C, matching what the language
promises; `-lm` is for `std/math`'s externs.

## Following one program through the passes

```kelp
impl "std/str"

datac Point(val x: i32, val y: i32)

fun area(p: Point).R: i32 = p.x * p.y

fun main() {
    val p = Point(x = 3, y = 4)
    if p.x > 0 {
        print(area(p))
    }

    var xs: List<i32> = List.empty()
    xs.push(1)
    xs.push(2)
    for x in xs {
        print(x)
    }
}
```

| Pass | What it makes of the program above |
| --- | --- |
| `lexer.rs` | tokens, each with a byte range; the newlines are tokens too, and they are what ends statements |
| `preprocess.rs` | unchanged here: there is no `%*alias*%` to substitute |
| `parser.rs` | the AST, with `for x in xs` already rewritten into an index-and-`while` walk over the list |
| `resolve.rs` | a module graph with `std/str` next to this file, and the capability set of each module (empty here, since nothing gated is imported) |
| `infer.rs` | `area(p)`: the parameter is a `datac`, so it becomes a shared borrow and the call site gets a synthesized `&` the author never wrote |
| `tir.rs` | the same tree, every node carrying `Ty` and `Span` |
| `borrowck.rs` | `p` is borrowed by `area` and still owned afterwards; a drop plan for the `Point` and for the `List` |
| `codegen_c.rs` | C, with a `#line` marker before every statement back into the `.kp`, plus the runtime text from `runtime/kelp_rt.c` that the drop plan asked for |
| `driver.rs` | `<out>.c` written beside the binary, `cc -O2 -fwrapv -lm` invoked |

## What is *not* in the pipeline

| Missing | Consequence |
| --- | --- |
| A library or object target | "Using a library" means copying or fetching a folder of `.kp` sources: see [Libraries](/libraries) |
| A module dependency list | `kelpc check --json` answers with diagnostics; which module depends on which is still not askable outside the compiler, which is the other half of the interface a build cache wants |
| An optimiser | For the `c` backend it is whatever `cc -O2` does to the generated C. The `llvm` backend emits its object at LLVM's default codegen level because no IR optimization pass pipeline exists yet; choosing the pipeline is MK7 stage S6, and DWARF debug info is stage S4. |
| Incremental compilation and a build cache | [Coral](/getting-started/install) owns the project-level cache |

## See also

- [Backends](/compiler/backends)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Capabilities](/language/capabilities)
- [Ownership and borrowing](/language/ownership)
