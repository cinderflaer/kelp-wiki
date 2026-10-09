---
title: "Modules and imports"
description: "A module is a file. impl names it and can grant it authority. Covers module names, pub visibility, file order, pd and const, and aliases."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §13](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md).

A module **is** a file. `impl` names it, and optionally grants it authority.

```kelp
impl "std/fs"                                        // the standard library
impl "std/net" caps(net = ["api.example.com:443"])
impl "deps/discord/lib" caps(*)                      // the whole set, one clause
impl "shapes/circle"                                 // a file in this project
impl "deps/json/lib"                                 // a dependency
```

```kelp project
fun main() {
    val c = circle.Circle(r = 2.0)
    print(c.area())
    print(json.write(json.int(1)))
}
```

## Rules

- **Nothing is imported by default**, not even the standard library. A module's
  own top-level names are visible without qualification; everything else is
  `module.name`, and only for the items that module exports with `pub` (see
  [Visibility](#visibility)).
- **The module's name is its own name**: the last path segment, so `impl
  "shapes/circle"` is `circle` and `impl "std/fs"` is `fs`. A **dependency's
  entry module**, a path ending in `/lib` under `deps/`, is named after the
  directory Coral fetched it into: `impl "deps/json/lib"` is `json`, whichever
  repository or folder it came from.
- **`impl "path" as name` is removed.** A module has one name, its own. A program
  that still writes the `as` clause gets an error that names the module's name to
  use instead.
- **A bare name belongs to the module that writes it.** Every module names its
  own items without qualification; another module's item is reached as
  `alias.Item`, never by its bare name.
- **Authority is declared at the import**, and it is the only place it can be
  acquired. See [Capabilities](/language/capabilities).
- A local `impl` path is a path in the project's `src/` without the `.kp`
  extension: `impl "shapes/circle"` is `src/shapes/circle.kp`.

## Visibility

Every top-level item is **private to its own module**. A module that imports
another reaches only the items that module exports with `pub`:

```kelp
pub const LIMIT: i32 = 10
pub datac Point(val x: i32, val y: i32)
pub enum Shape { Circle(val r: f64) Empty }
pub fun scale(v: f64, k: f64).return: f64 = v * k
pub extern fun clock_ticks().return: u64
```

- `pub` is accepted only on a top-level `fun`, `extern fun`, `extern type`,
  `datac`, `enum` or `const`. Written anywhere else it is a parse error that
  names those forms:

  ```text
  'pub' applies to a top-level 'fun', 'extern fun', 'extern type', 'datac', 'enum' or 'const', found Val
  ```
- A `pd` never takes `pub`: a passdown is module-scoped by design, so
  `pub pd ...` is refused where it is written: `a 'pd' cannot be 'pub': a
  passdown is module-scoped by design, so another module cannot reach it; a
  'fun' that reads it can be exported instead`. A `fun` that reads the passdown
  is what another module uses, and that function can be `pub`.
- A method never takes `pub`. A method's reachability follows its declaring
  type, so `pub datac Circle` is what lets another module call `value.area()` on
  a `Circle` it holds, however the method was declared. Writing `pub` on a method
  is an error that says to mark the type instead.
- Inside its own file an item is reachable by its bare name whether or not it is
  written `pub`. `pub` governs only another module's `alias.Item` spelling.
- A private item that exists gets an error of its own, distinct from a name that
  does not exist:

  ```text
  error: 'lib.hidden' is private: 'hidden' is declared in module 'lib' without 'pub', so only that module can name it; add 'pub' to its declaration to export it
  error: module 'lib' has no item 'nope'
  ```

  A "did you mean" hint never offers a private item.
- **An exported declaration may name only a type its own module exports.**
  Reachability scopes the shape of a signature as well as the name of an item: a
  `pub fun`'s parameters and return, a method declared inside a `pub datac` or
  `pub enum` (reached through a value of that type), a `pub extern fun`, a `pub
  datac`'s field types, a `pub enum`'s variant payload types and a `pub const`'s
  written type must all be names a consumer can reach. The check walks a written
  type to the bottom, so it recurses through `List<T>`, `Box<T>`, `Map<K, V>`,
  `[T; N]`, generic arguments, borrows and function types. `pub fun make().return:
  Hidden` is refused when `Hidden` is private, even though a caller could still
  read `make().x` without naming the type. A private declaration may name
  anything, because nothing outside its module can name it either, and a type
  parameter is not a declared type, so naming one is never a violation. The
  refusal names the fix:

  ```text
  error: 'lib.make' is exported but its signature names 'lib.Hidden', which module 'lib' does not export: add 'pub' to 'Hidden', or make 'lib.make' private
  ```

  The check reads the whole program's export set, so a private type declared
  after the item that names it is refused the same way as one declared before:
  the order of two declarations in one file does not decide the answer.
- **The shipped standard library is exempt, transitionally.** A compiler-shipped
  `std/...` module exports every top-level item whether or not it is written
  `pub`, because the shipped modules import each other (`std/fmt` imports
  `std/str`, `std/net` imports `std/io` and `std/str`, and so on). The signature
  rule above is vacuous there for the same reason. Without the exemption the
  standard library stops building, and it goes away when the shipped
  declarations are marked `pub`.

## Canonical file order

```kelp
impl "std/fs"          // 1. imports
alias %*debug*% = true // 2. aliases, anywhere a statement can start
const LIMIT: i32 = 10  // 3. constants and passdowns, in any mix
pd val app = "demo"
datac Point(val x: i32, val y: i32)   // 4. types and functions, in any mix
fun main() {
    print(LIMIT)
}
```

The parser enforces the steps: an `impl` written after any declaration is a parse
error, and so is a `const` or `pd` after a `datac`, `enum` or `fun`. The order of
types and functions among themselves is a review convention, not a rule.

## `const`

```kelp
const LIMIT: i32 = 10
const NAME: str = "x"
const PI2: f64 = math.PI * 2.0
```

A `const` is a top-level compile-time value. The type is mandatory, the
initializer is evaluated while the compiler runs, and every use is substituted as
a literal, so a `const` costs no storage and no startup work. A `const` may only
name constants declared before it; it may also call a plain `fun` whose own body
stays inside what a constant can evaluate, and that function may be declared
after it. A `const` may be a tuple of constants (`const ORIGIN: (i32, i32) = (1, 2)`,
read as `ORIGIN.0` or by destructuring). [Constants and passdowns](/language/passdowns)
has the rules.

## `pd` passdowns

A passdown is a top-level binding that every function in the module can name
without it being passed:

```kelp
pd val app_name = "shapes"
pd var requests = 0

fun log_area(c: Circle) {
    requests += 1
    print("[$app_name #$requests] area = ${c.area()}")
}
```

- A function that mentions a passdown gets it wired in as a hidden parameter. One
  that never mentions one pays nothing.
- The hidden parameter is a **borrow**. A function that writes the passdown,
  directly or through a function it calls, holds an exclusive borrow. A function
  that only reads it holds a shared one. So `pd var` is writable from inside functions while the
  ordinary borrow rules still apply: two functions cannot hold the same passdown
  exclusively at once, and one call cannot take it both exclusively and shared
  (`combine(tally, tally)` where `combine` takes `mut Tally` is refused). A
  `pd var` that no function writes is a shared borrow everywhere, so handing it
  to a function that also reads it is fine.
- A passdown is module-scoped. A local of the same name shadows it inside that
  scope. There is no spelling for reaching another module's passdown, which is
  also why a library cannot keep the caller's tally in one.
- An owned passdown is freed once, at process exit.

A `pd var` that nothing writes is the common case for configuration and lookup
tables, and it costs nothing to read:

```kelp
pd var config: String = String.from_str(s = "api")

fun describe(name: &String) {
    print(name.as_str())
    print(config.as_str())   // shared borrow: the argument and this read coexist
}

fun main() {
    describe(config)
}
```

Write to it once, with `config = ...` in any function or a `mut` method on it.
After that, every reference in the chain is an exclusive borrow, which is what
makes the write checked.

> **Why a library still takes a `mut` parameter**
>
> [`testkit`](/libraries/testkit) takes an explicit `mut Report` rather than a
> module-scope counter, and the reason is scope, not the borrow rules: a
> passdown belongs to the module that declares it, so a library could never
> tally into its caller's state. A `mut` parameter crosses the module
> boundary; a `pd var` cannot.

## Projects and path resolution

`impl` paths are resolved against the project's `src/`, not the working directory
and not the importing file, so `impl "shapes/circle"` means the same file from
anywhere in the tree. See [Projects and coral.toml](/getting-started/projects).

## Aliases

`alias %*name*% = <raw text to end of line>` is textual substitution, and it runs
before parsing. It can rewrite an import path:

```kelp
alias %*db*% = "storage/postgres"
impl %*db*%
```

Aliases also come from `alias.kpconf` at the project root, one
`name="replacement text"` per line. Substitution has no parameters, no scoping
and no hygiene: `%*a*%` defined as `%*b*% * 2` with `%*b*%` defined as `40 + 2`
prints `84`, because precedence is whatever the expanded text happens to produce.

## See also

- [Capabilities](/language/capabilities)
- [Constants and passdowns](/language/passdowns)
- [Projects and coral.toml](/getting-started/projects)
- [Tooling](/tooling)
