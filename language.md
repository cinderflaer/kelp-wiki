---
title: "The language"
description: "Kelp is small on purpose. This chapter is the surface-syntax reference; the authority is plan/syntax.md, and each page cites the section it came from."
isPublished: true
tags: "language"
---
The language chapter: the surface syntax of Kelp, one page per topic. The authority is
[`plan/syntax.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md),
and each page cites the section it came from.

## Pages

In reading order:

- [Lexical structure](/language/lexical): comments, identifiers, keywords, literals, templates and operators.
- [Types](/language/types): the type table, `Copy` vs owned vs borrowed, `str` and `View`.
- [Bindings and assignment](/language/bindings): `val` and `var`, type inference, assignment and mutable paths.
- [Operators and expressions](/language/expressions): precedence, arithmetic, bitwise operators, `?`, borrows and dereference.
- [Control flow](/language/control-flow): `if`, `if let`, `for`, `while`, `when`, `return`, `break` and `continue`.
- [Functions](/language/functions): declaration, `.return: T`, named arguments, function values and closures.
- [Return types and `return`](/language/returns): the `.return: T` clause, bodies, the divergence rule and borrowed returns.
- [Methods and receivers](/language/methods): `Type.name`, `mut` receivers and generic receivers.
- [`datac` and `enum`](/language/data-types): records, tagged unions, generics, construction and matching.
- [Generics and type parameters](/language/generics): type parameters, instantiation, generic receivers and generic functions.
- [Traits and static dispatch](/language/traits): methods, default bodies, supertraits, `impl Trait for Type`, bounds and `&dyn` objects.
- [Associated types](/language/associated-types): `type Item` in a trait and the `I::Item` and `Self::Item` projections.
- [Generic traits, `From` and `?` conversion](/language/generic-traits): `trait Name<T>`, static methods, `std/convert` and error conversion with `?`.
- [Owned trait objects](/language/box-dyn): `Box<dyn Trait>`, the coercion, `get()` and drop through the vtable.
- [Operator traits and `Display`](/language/operator-traits): `std/ops` (declarations and the module) and `fmt.Display` for operators, `${x}` and `print`.
- [Iterators, `for` and `break`](/language/iterators): the `Iterator` trait, `for x in it`, `break` and `continue`, and `std/iter`.
- [Const generics and `impl Trait` arguments](/language/const-generics): `<const N: usize>`, inference from an array and `fun f(x: impl Trait)`.
- [Ownership and borrowing](/language/ownership): moves, drops, borrows, partial moves and `Box.take`.
- [Text](/language/text): `str`, `View`, `String`, `Bytes`, printing and conversions.
- [Collections](/language/collections): `List<T>`, `Map<K, V>`, `Box<T>` and the fixed-size array `[T; N]`.
- [Concurrency in v1](/language/concurrency): `SeqCst`, the atomic cell, the fence and the one borrow that crosses to a worker.
- [Modules and imports](/language/modules): `impl`, aliases, visibility and projects.
- [Constants and passdowns](/language/passdowns): `const`, `pd` passdowns and the hidden borrow.
- [Capabilities](/language/capabilities): the model, grants, patterns and delegation.
- [User FFI](/language/externs): `extern fun`, `extern type` handles, variadics and `move closure` callbacks.
- [Unsafe code and raw pointers](/language/unsafe): `unsafe` blocks and `unsafe fun`, `Ptr<T>`, volatile access, `repr(...)` and byte order.
- [Statics and `defer`](/language/statics-and-defer): `static`, `static mut`, `pub static`, `Atomic` statics, `section(...)` and `defer`.
- [User `Drop`](/language/drop): `fun mut T.drop()`, the order of drops, what is refused and why there is no unwinding.
- [Per-CPU storage](/language/percpu): `percpu static mut`, `[target] cpus` and the per-CPU array.
- [Freestanding mode](/language/freestanding): the `[target]` manifest section, the allowed set, the allocator hook, riscv64 and aarch64.
- [Kernel 0](/language/kernel): the bare-metal examples under QEMU with their serial output, the timer scheduler and the x86-64 IDT.
- [Errors and panics](/language/errors): `Option`, `Result`, `?`, `panic` and `assert`.
- [Limits in v1](/language/limits): what the language deliberately does not have.
- [Style](/language/style): indentation, naming, file order and comments.
- [Grammar summary](/language/grammar): the whole surface grammar on one page.
- [Pitfalls](/language/pitfalls): the rules that explain most compile errors, and their fixes.

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

## The 60-second version

```kelp
impl "std/str"

datac Point(var x: i32, var y: i32)

fun area(p: &Point).return: i32 = p.x * p.y

enum Shape {
    Circle(val r: f64)
    Empty
}

fun describe(s: &Shape).return: &str = when s {
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
[Back to the home page](/)
