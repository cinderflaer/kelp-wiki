---
title: "Constants and passdowns"
description: "const is a file-level value computed by the compiler. pd is a file-level binding that every function in its module can name, passed as a hidden borrow."
isPublished: true
tags: "language, ownership"
---
Source: [`syntax.md` §14](/design/syntax).

Two declarations live at file scope and are not statements. `const` is a value
folded at compile time. `pd` (passdown) is a value every function in the module can
name without receiving it as a parameter.

## `const`

```kelp
const LIMIT: i32 = 10
const NAME: str = "x"
const PI2: f64 = math.PI * 2.0

const PAGE_SIZE: usize = 4096
const ENTRY_SIZE: usize = 8
const TABLE_ENTRIES: usize = entries_for(pages = 64)

fun entries_for(pages: usize) => usize {
    var total: usize = 0
    var i: usize = 0
    while i < pages {
        total += PAGE_SIZE / ENTRY_SIZE
        i += 1
    }
    total
}
```

- The type is optional. `const NAME: T = value` has type `T`. Without the
  annotation, `const NAME = value`, the const takes the type its value has with no
  expected type: an integer literal is `int` (the native width), a float is `f64`,
  and a `bool`, `char` or `str` keeps its own type. A const built from a typed
  const keeps that type, so `const WIDE: u8 = 200` and `const WRAPPED = WIDE + 100`
  make `WRAPPED` a `u8` that wraps to 44.
- A use never changes a const's type. A const used where another type is needed,
  such as a `usize` address or a `usize` length, keeps its annotation: with
  `const BASE = 0x1000`, `val p: usize = BASE` is refused, and `const BASE: usize = 0x1000`
  is the fix.
- Only a scalar (a number, `bool`, `char` or `str`) can leave the type out. An
  array or a tuple, and a `section("...")` array, keep the annotation.
- Every `const` and `pd` must come before the first `datac`, `enum`, `trait` or
  `fun` in the file.
- The initializer is **evaluated while the compiler runs**. It may use a
  literal, another `const` declared before it, the operators (arithmetic,
  comparison, `&&`/`||`, the bitwise ones), an integer conversion such as
  `n.to_usize()`, `if`/`else`, `while`, and **a call to a plain `fun`** whose body
  stays inside that set. The function can be declared after the `const` that calls
  it. A call takes named or positional arguments, and a recursive call works as
  long as it terminates.
- What is out of reach: a builtin (`print`, `panic`, `assert`), an `extern fun`,
  a method call, a generic function, a `when`, a `?`, an array or a `datac`
  value, and a template. Each is refused.
- Evaluation is bounded, because it is the compiler doing the running: one
  million steps and sixty-four nested calls.
- The result has to be a scalar, a `bool`, a `char` or a `str`. Arithmetic is the declared type's, so a `u8` wraps at 256 and `>>` on a
  signed type is arithmetic, exactly as at runtime.
- Every use is substituted as a literal, so a `const` costs no storage and no work
  at startup.
- An array's length is the same compiled expression, which is what lets
  `[u64; PAGE_SIZE / ENTRY_SIZE]` be one type ([Collections](/language/collections)).

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
pd var config: String = "api"

fun describe(name: String) {
    print(name.as_str())
    print(config.as_str())   // shared: the argument and this read coexist
}

fun main() {
    describe(config)
}
```

### Scope

- A passdown is module-scoped. Every function in its module can name it, and no
  other module can.
- A `pd` never takes `pub`: `pub pd val x = 1` is refused where it is written,
  because a passdown is module-scoped by design. A `fun` that reads the passdown
  is what another module uses, and that function can be `pub`.
- A local `val` or `var` of the same name shadows it inside that scope.
- There is no spelling for reaching another module's passdown. A library therefore
  cannot tally into its caller's state. A `mut` parameter can cross a module
  boundary, and a `pd var` cannot. This is why [`testkit`](/libraries/testkit)
  takes an explicit `mut Report`.
- An owned passdown is freed once, at process exit.

A `pd var` that nothing writes is the common shape for configuration and lookup
tables, and reading one costs nothing.

## See also

- [Modules and imports](/language/modules)
- [Bindings and assignment](/language/bindings)
- [Ownership and borrowing](/language/ownership)
