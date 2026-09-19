---
title: "Functions"
description: "Source section - syntax.md \u00a77."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §7](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

## Declaration

```kelp
fun add(a: i32, b: i32).R: i32 = a + b        // expression body, requires .R

fun greet(name: &str) {                       // no .R: returns Unit
    print(str.concat("hello, ", name))
}

fun abs_diff(a: i32, b: i32).R: i32 {         // block body
    if a > b {
        return a - b
    }
    return b - a
}
```

- The keyword is `fun`; the return type is written `.R: T` **after** the
  parameter list. There is no `->`, no trailing type, and no inferred return type
  for a block body. No `.R` means `Unit`.
- An expression body (`= expr`) requires `.R: T`; a block body ends with
  `return expr`.
- Parameters are `name: T`. A parameter is a **shared borrow** of its argument.
  `name: mut T` is an exclusive borrow: the only spelling for mutation in
  parameter position (`&mut T` there is a parse error). `name: move T` takes
  ownership.
- `mut` and `move` are mutually exclusive, `move` is refused on a `str` or a
  `&T`, and a receiver is always borrowed (there is no `fun move Type.name()`).

## Named arguments

Named arguments are allowed at any call site with more than one parameter, and
are matched by name first, then positionally:

```kelp
val p = Circle(r = 2.0, x = 1.0)
val d = math.pow(base = 2.0, exp = 8.0)
print(str.concat("a", "b"))            // positional is fine too
```

A name the function does not declare is an error, and so is naming an argument
twice. The convention in this repository is to use named arguments wherever a
call would otherwise be ambiguous: in practice every `datac` construction with
two or more fields.

## Overloading, recursion

- **A user program cannot overload a name.** `fun pick(a: i32)` and
  `fun pick(a: f64)` collide. Overloading exists only inside the shipped standard
  library, and only for `abs`, `min`, `max`, `clamp`, which is how `math.min`
  accepts `i32`, `i64` and `f64`.
- Recursion is unrestricted, including mutual recursion.
- A function may take type parameters: `fun first<T>(xs: List<T>).R: T`. Each
  call site is instantiated for the types it uses.

## Function values

A bare name of a declared `fun` is a value, typed `fun(T, U).R: V`: the `fun`
keyword, the parameter types, and the same `.R:` clause a declaration uses:

```kelp
fun double(x: i32).R: i32 = x * 2

fun apply(f: fun(i32).R: i32, x: i32).R: i32 = f(x)     // takes a callback

val f = double                     // a function value
print(f(21))
print(apply(double, 5))
print(apply(f, 6))
```

The parameter types of a function type follow the same rule a declaration's do:
`fun(String)` borrows, `fun(mut Counter)` borrows exclusively, `fun(move String)`
takes ownership. A function value is `Copy`, so it can live in a field, be
returned, and be called with ordinary call syntax wherever it is held.

## Closures

A `fun` literal is an anonymous function. A literal that names a binding from the
enclosing scope **captures** it, and that makes the literal a *closure*: a
function value plus the environment those captures were moved into. Its type is
written `closure(T, U).R: V`.

```kelp
fun make(step: i32).R: closure(i32).R: i32 {
    return fun(x: i32).R: i32 = x * step
}

val f = make(3)
print(f(7))                        // 21 — `step` outlives `make`
```

Capture rules:

- A capture is **move-only**, and `Copy` decides what that means: a `Copy` binding
  is *copied* into the environment (the enclosing binding stays usable), an owned
  binding is *moved* in (the enclosing binding is gone from that point on).
- A borrow (`str`, `&T`) **cannot** be captured: the environment outlives the
  frame the borrow points into and there is no lifetime syntax to say otherwise.
  Pass it as a parameter of the literal instead.
- Inside the body a capture is read *through a borrow of the environment*, so an
  owned capture can be used in place (a method called on it, a field read, passed
  to a parameter) but cannot be handed out by value.
- A closure owns its environment and frees it where the closure dies.

In practice, a stdlib or library callback is written `closure(&T).R: U`, and a
`Copy` element is used **directly** inside the literal: `acc + x`, not
`acc + *x`:

```kelp
val total = listx.fold(xs, 0, fun(acc: i32, x: &i32).R: i32 = acc + x)
```

> **Anonymous functions are not named nested functions**
>
> There is no way to write a named nested function and no `dyn`-style boxing of
> one.

## `pd` passdowns as hidden parameters

A function that mentions a `pd` binding gets it wired in as a hidden parameter;
one that never mentions one pays nothing. See
[Modules and imports](/language/modules).

## See also

- [Methods and receivers](/language/methods)
- [Control flow](/language/control-flow) for `return` and the divergence rule
