---
title: "Constants and passdowns"
description: "Source section - syntax.md \u00a714. `const` is a top-level compile-time value; a `pd` passdown is a top-level binding every function in the module can name, wired in as a hidden borrow."
isPublished: true
tags: "language, ownership"
---
Source section:
[`syntax.md` §14](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Two declarations live at file scope and are not statements. `const` is a value
folded at compile time. `pd` (passdown) is a value every function in the module can
name without receiving it as a parameter.

## `const`

```kelp
const LIMIT: i32 = 10
const NAME: str = "x"
const PI2: f64 = math.PI * 2.0
```

- The type is mandatory.
- The initializer must be foldable at compile time.
- Every use is substituted as a literal, so a `const` costs no storage and no work
  at startup.
- A `const` may only name constants declared before it.

## `pd` passdowns

```kelp
pd val app_name = "shapes"
pd var requests = 0

fun log_area(c: Circle) {
    requests += 1
    print("[$app_name #$requests] area = ${c.area()}")
}
```

The forms are `pd val name = expr`, `pd var name = expr`, and either of those with
an explicit type: `pd val name: T = expr`.

A function that mentions a passdown gets it wired in as a hidden parameter. A
function that never mentions one pays nothing: no parameter, no register, no
runtime lookup.

### The hidden parameter is a borrow

Its mutability is what the function does with the passdown:

- A function that only reads it holds a **shared** borrow.
- A function that writes it, directly or through a function it calls, holds an
  **exclusive** borrow.

So `pd var` is writable from inside any function in the module, and the ordinary
borrow rules still apply to it:

- Two functions cannot hold the same passdown exclusively at once.
- One call cannot take it both exclusively and shared: `combine(tally, tally)`
  where `combine` takes `mut Tally` is refused.
- A `pd var` that no function writes is a shared borrow everywhere, so handing it
  to a function that also reads it is fine.

Write it once, `config = ...` in any function or a `mut` method on it, and every
reference in the chain becomes an exclusive borrow instead. That is what makes the
write checked rather than free.

```kelp
pd var config: String = String.from_str(s = "api")

fun describe(name: &String) {
    print(name.as_str())
    print(config.as_str())   // shared: the argument and this read coexist
}

fun main() {
    describe(config)
}
```

### Scope

- A passdown is module-scoped. Every function in the module may name it, and no
  other module can.
- A local `val` or `var` of the same name shadows it inside that scope.
- There is no spelling for reaching another module's passdown. A library therefore
  cannot tally into its caller's state: that is why [`testkit`](/libraries/testkit)
  takes an explicit `mut Report`, because a `mut` parameter crosses a module
  boundary and a `pd var` cannot.
- An owned passdown is freed once, at process exit.

A `pd var` that nothing writes is the common shape for configuration and lookup
tables, and reading one costs nothing.

## See also

- [Modules and imports](/language/modules)
- [Bindings and assignment](/language/bindings)
- [Ownership and borrowing](/language/ownership)
