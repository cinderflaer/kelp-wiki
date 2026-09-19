# Modules and imports

Source section:
[`syntax.md` §13](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

A module **is** a file. `impl` names it, optionally aliases it, and optionally
grants it authority.

```kelp
impl "std/fs"                                        // the standard library
impl "std/net" with caps(net = ["api.example.com:443"])
impl "shapes/circle" as circle                       // a file in this project
impl "deps/json/lib" as json                         // a dependency
```

```kelp
fun main() {
    val c = circle.Circle(r = 2.0)
    print(c.area())
    print(json.write(json.int(1)))
}
```

## Rules

- **Nothing is imported by default**, not even the standard library. A module's
  own top-level names are visible without qualification; everything else is
  `alias.name`.
- **The alias is the name.** Two imports of the same file under different aliases
  are the same module under two names.
- **Only the entry module has unprefixed access to the whole program.** Every
  other module sees exactly what it imported.
- **Authority is declared at the import**, and it is the only place it can be
  acquired. See [Capabilities](capabilities.md).
- A local `impl` path is a path in the project's `src/` without the `.kp`
  extension: `impl "shapes/circle"` is `src/shapes/circle.kp`.

## Canonical file order

```kelp
impl "std/fs"          // 1. imports
alias %*debug*% = true // 2. aliases, anywhere a statement can start
const LIMIT: i32 = 10  // 3. constants and passdowns, in any mix
pd val app = "demo"
datac Point(val x: i32, val y: i32)   // 4. types and functions, in any mix
fun main() { ... }
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
initializer must be foldable at compile time, and every use is substituted as a
literal — so a `const` costs no storage and no startup work. A `const` may only
name constants declared before it.

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

- A function that mentions a passdown gets it wired in as a hidden parameter; one
  that never mentions one pays nothing.
- The reference is a borrow: `pd var` is an exclusive borrow and is therefore
  writable from inside functions, while `pd val` is shared. Ordinary borrow rules
  apply, so two functions cannot hold the same `pd var` exclusively at once.
- A passdown is module-scoped. A local of the same name shadows it inside that
  scope, and there is no spelling for reaching another module's passdown.
- An owned passdown is freed once, at process exit.

!!! warning "The `pd var` foot-gun"
    On kelpc 0.2.2 a module-scope `pd var` counter does not thread reliably
    through a call chain: a function that only *calls* a function which reads the
    passdown does not see it. That is why [`testkit`](../libraries/testkit.md)
    takes an explicit `mut Report` parameter instead of a global tally.

## Projects and path resolution

`impl` paths are resolved against the project's `src/`, not the working directory
and not the importing file, so `impl "shapes/circle"` means the same file from
anywhere in the tree. See [Projects and coral.toml](../getting-started/projects.md).

## Aliases

`alias %*name*% = <raw text to end of line>` is textual substitution that runs
before parsing, so it can rewrite an import path:

```kelp
alias %*db*% = "storage/postgres"
impl %*db*%
```

Aliases also come from `alias.kpconf` at the project root, one
`name="replacement text"` per line. Substitution has no parameters, no scoping
and no hygiene — `%*a*%` defined as `%*b*% * 2` with `%*b*%` defined as `40 + 2`
prints `84`, because precedence is whatever the expanded text happens to produce.

## See also

- [Capabilities](capabilities.md)
- [Projects and coral.toml](../getting-started/projects.md)
- [Tooling](../tooling/index.md)
