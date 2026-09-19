# The language

Kelp is small on purpose. This chapter is the surface-syntax reference; the
authority is
[`plan/syntax.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md),
and each page cites the section it came from.

## The shape of a source file

```kelp
impl "std/fs"                     // 1. imports
impl "std/http" with caps(net = ["api.example.com:443"])

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
| [Lexical structure](lexical.md) | comments, identifiers, keywords, literals, templates, operators |
| [Types](types.md) | the type table, `Copy` vs owned vs borrowed, `str` and `View` |
| [Operators and expressions](expressions.md) | precedence, arithmetic, bitwise, `?`, borrows and dereference |
| [Control flow](control-flow.md) | `if`/`else`, `if let`, `for`, `while`, `when`, `return` |
| [Functions](functions.md) | declaration, `.R: T`, named arguments, function values, closures |
| [Methods and receivers](methods.md) | `Type.name`, `mut` receivers, generic receivers |
| [datac and enum](data-types.md) | records, tagged unions, generics, construction, matching |
| [Ownership and borrowing](ownership.md) | moves, drops, borrows, partial moves, `Box.take` |
| [Text](text.md) | `str`, `View`, `String`, `Bytes`, printing, conversions |
| [Collections](collections.md) | `List<T>`, `Map<K, V>`, `Box<T>` |
| [Modules and imports](modules.md) | `impl`, aliases, `pd` passdowns, projects |
| [Capabilities](capabilities.md) | the model, grants, patterns, delegation |
| [Errors and panics](errors.md) | `Option`, `Result`, `?`, `panic`, `assert` |
| [Limits in v1](limits.md) | what the language deliberately does not have |
| [Style](style.md) | indentation, naming, file order, comments |
| [Grammar summary](grammar.md) | the whole surface grammar on one page |
| [Pitfalls](pitfalls.md) | the rules that explain most compile errors |

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
