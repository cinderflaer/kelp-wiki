---
title: "Pipeline"
description: "The stages kelpc runs, in order: load and resolve, type check, borrow check and drop planning, LLVM code generation, then an `ld.lld` link. Each stage hands one structure to the next."
isPublished: true
tags: "compiler"
---
`kelpc` runs a fixed sequence of passes over the whole program.
Each pass reads the previous pass's output and hands one structure on: source text, tokens, an AST, a typed IR, a drop plan and LLVM IR.
The checks run once over the whole program, and only then is code generated.

## The order of the passes

`build` and `check` share the same front end.
`build` then generates code, and `check` stops after the checks.

| Step | Entry point | File |
| --- | --- | --- |
| Load and resolve the module graph | `resolve::load` | `resolve.rs` |
| Lex, expand aliases, parse each module | `visit_body` and `Parser::parse_program` | `resolve.rs`, `parser.rs` |
| Lower `defer` into ordinary statements | `defer::lower` | `resolve.rs`, `defer.rs` |
| Type check the whole program | `infer::check_program` | `infer.rs` |
| Check moves, borrows and build the drop plan | `borrowck::check_program` | `borrowck.rs` |
| Check the freestanding allowed set | `freestanding::check` | `freestanding.rs` |
| Generate LLVM IR and an object | `codegen_llvm::compile` | `codegen_llvm.rs` |
| Link with `ld.lld` | `driver::link_llvm_objects` | `driver.rs` |

The front end entry point is `front_end` in `main.rs`.
`kelpc check` calls it and prints the findings, with no code generation (`main.rs`).
`kelpc build` (`main.rs`) runs the same steps and then generates code.
A freestanding build runs `freestanding::prune` and type checks the pruned program a second time (`main.rs`).

## What each pass owns

- **Lexing and parsing** turn text into an untyped AST. Text aliases are expanded between the two. See [Front end](/compiler/frontend).
- **Module resolution** loads each `impl` path as a module, flattens the modules into one program and records each module's capability grant. See [Modules and capabilities](/compiler/resolve).
- **Type checking** gives every expression a concrete type and writes the typed IR (`tir.rs`). Generic functions are checked once per instance. See [Types](/compiler/types).
- **Borrow checking** rejects moves and borrows that conflict, and returns the drop plan that code generation reads. See [Ownership and drops](/compiler/ownership).
- **Code generation** lowers the typed IR to LLVM IR and emits an object. See [Backends](/compiler/backends).
- **The driver** runs the external tools, writes the output files and prints diagnostics. See [Driver](/compiler/driver).

## Following one program

This program uses a `datac`, a `List` and a `for` loop:

```kelp
impl "std/str"

datac Point(val x: i32, val y: i32)

fun area(p: Point) => i32 = p.x * p.y

fun main() {
    val p = Point(x = 3, y = 4)
    print(area(p))

    var xs: List<i32> = List.empty()
    xs.push(1)
    xs.push(2)
    for x in xs {
        print(x)
    }
}
```

Each pass does the following with it.

| Pass | What it does with this program |
| --- | --- |
| Lexer | Produces tokens with byte spans. Newlines are tokens and end statements. |
| Preprocessor | Nothing to expand. There is no `_name` reference. |
| Parser | Produces `Stmt::For` for the loop. It is not rewritten yet. |
| Resolver | Loads `std/str` as a module. Nothing gated is imported, so no grant is needed. |
| Type checker | Gives `area` a `Ty::Ref` parameter, because a `datac` parameter is borrowed. At the call site it inserts the `&` the program does not write. Turns the `for` into an index walk over the list. |
| Borrow checker | `p` is borrowed by `area` and is still owned afterwards. Builds drops for `p` and `xs`. |
| LLVM codegen | Emits `main`, `area` and the list helpers into one module, then runs the LLVM passes at `-O2`. |
| Driver | Writes `build/<name>.ll` and `build/<name>.o` and runs `ld.lld`. |

The loop desugaring is in `infer.rs`.
The borrow at the call site is inserted by `check_call_arg` (`infer.rs`).

## Known gaps in the pipeline

| Missing | What it means |
| --- | --- |
| Libraries as compiled objects | A library is a folder of `.kp` sources that is copied or fetched. See [Libraries](/libraries). |
| A dependency query | `kelpc check --json` returns diagnostics only. The modules a module depends on are not exposed. |
| A separate optimizer | `-O0`, `-O1`, `-O2`, `-O3` and `-Os` pick the LLVM pass pipeline and the codegen level. See [Backends](/compiler/backends). |
| Incremental front end | `--incremental` splits only the backend. Parsing, resolution, type checking and borrow checking run on every build. See [Incremental builds](/compiler/incremental). |

## See also

- [Front end](/compiler/frontend)
- [Modules and capabilities](/compiler/resolve)
- [Types](/compiler/types)
- [Ownership and drops](/compiler/ownership)
- [Backends](/compiler/backends)
- [Driver](/compiler/driver)
- [Runtime](/compiler/runtime)
