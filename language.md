---
title: "The language"
description: "Kelp is small on purpose. This chapter is the surface-syntax reference; the authority is plan/syntax.md, and each page cites the section it came from."
isPublished: true
tags: "language"
---
Kelp is small on purpose. This chapter is the surface-syntax reference; the
authority is
[`plan/syntax.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md),
and each page cites the section it came from.

## The shape of a source file

```kelp
impl "std/fs"                     // 1. imports
impl "std/http" caps(net = ["api.example.com:443"])

const LIMIT: i32 = 10             // 2. constants
pd val app_name = "shapes"        //    and passdowns, in any mix

datac Point(val x: i32, var y: i32)   // 3. types and functions, in any mix

fun main() {
    print("hello")
}
```

The order is enforced by the parser: an `impl` after any declaration is a parse
error, and so is a `const` or `pd` after a `datac`, `enum` or `fun`
(syntax.md §13.2). There are no semicolons; a newline ends a statement
(§2.2).

## Reading order

| Page | What it covers |
| --- | --- |
| [Lexical structure](/language/lexical) | comments, identifiers, keywords, literals, templates, operators |
| [Types](/language/types) | the type table, `Copy` vs owned vs borrowed, `str` and `View` |
| [Bindings and assignment](/language/bindings) | `val` and `var`, type inference, assignment, mutable paths |
| [Operators and expressions](/language/expressions) | precedence, arithmetic, bitwise, `?`, borrows and dereference |
| [Control flow](/language/control-flow) | `if`/`else`, `if let`, `for`, `while`, `when`, `return` |
| [Functions](/language/functions) | declaration, `.R: T`, named arguments, function values, closures |
| [Return types and `return`](/language/returns) | the `.R: T` clause, bodies, the divergence rule, borrowed returns |
| [Methods and receivers](/language/methods) | `Type.name`, `mut` receivers, generic receivers |
| [datac and enum](/language/data-types) | records, tagged unions, generics, construction, matching |
| [Generics and type parameters](/language/generics) | type parameters, instantiation, generic receivers and functions |
| [Ownership and borrowing](/language/ownership) | moves, drops, borrows, partial moves, `Box.take` |
| [Text](/language/text) | `str`, `View`, `String`, `Bytes`, printing, conversions |
| [Collections](/language/collections) | `List<T>`, `Map<K, V>`, `Box<T>`, the fixed-size array `[T; N]` |
| [Concurrency in v1](/language/concurrency) | `SeqCst`, the atomic cell, the fence, and the one borrow that crosses to a worker |
| [Modules and imports](/language/modules) | `impl`, aliases, visibility, projects |
| [Constants and passdowns](/language/passdowns) | `const`, `pd` passdowns and the hidden borrow |
| [Capabilities](/language/capabilities) | the model, grants, patterns, delegation |
| [Errors and panics](/language/errors) | `Option`, `Result`, `?`, `panic`, `assert` |
| [Limits in v1](/language/limits) | what the language deliberately does not have |
| [Style](/language/style) | indentation, naming, file order, comments |
| [Grammar summary](/language/grammar) | the whole surface grammar on one page |
| [Pitfalls](/language/pitfalls) | the rules that explain most compile errors |

## The 60-second version

```kelp
datac Point(var x: i32, var y: i32)

fun area(p: &Point).R: i32 = p.x * p.y

enum Shape {
    Circle(val r: f64)
    Empty
}

fun describe(s: &Shape).R: &str = when s {
    Circle(_) -> "circle"
    Empty -> "empty"
}

fun main() {
    var p = Point(x = 3, y = 4)
    p.x = 10
    print(area(p))

    var xs: List<i32> = List.empty()
    xs.push(7)
    for x in xs {
        print("$x")
    }

    val parsed = str.parse_i64("41")     // Result<i64, str.ParseErr>
    if let Ok(n) = parsed {
        print(n + 1)
    }
}
```

Everything else in this chapter is detail on those four ideas: records and
tagged unions, borrows, containment (`List`/`Map`/`Box`), and errors as values.
