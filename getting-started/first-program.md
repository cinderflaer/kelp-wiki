---
title: "Your first program"
description: "The Kelp repository ships three examples - examples/hello.kp, examples/fib.kp and examples/download.kp. This page walks the first two, then adds the pieces a real program needs."
isPublished: true
tags: "getting-started"
---
The Kelp repository ships three examples: `examples/hello.kp`, `examples/fib.kp`
and `examples/download.kp`. This page walks the first two, then adds the pieces a
real program needs.

## Hello

```kelp
fun main() {
    print("hello, kelp")
}
```

```sh
kelpc run hello.kp
# hello, kelp
```

`print` takes exactly one argument and adds a newline; `print!` does not. Templates
interpolate:

```kelp
fun main() {
    val who = "world"
    print("hello, $who")
    print("twice two is ${2 * 2}")
}
```

A template is **not a value**: it may only appear as the single argument of
`print`/`print!`. To build text, use `str.concat`, `fmt.*`, or a `String`:

```kelp
var out = String.empty()
out.push_str("hello, ")
out.push_str(who.as_str())
print(out)
```

## Records and functions

```kelp
datac Point(val x: i32, val y: i32)

fun area(p: &Point).R: i32 = p.x * p.y

fun main() {
    val p = Point(x = 3, y = 4)
    print(area(p))            // 12
    print(p.x)                // 3
}
```

- A `datac` field is `val` (immutable) or `var` (mutable).
- A parameter is a **borrow**, so `area(p)` does not move `p` and `p` is still
  usable afterwards.
- The return type is written `.R: T`; no `.R` means the function returns `Unit`.

## Enums and `when`

```kelp
enum Shape {
    Circle(val r: f64)
    Rect(val w: f64, val h: f64)
    Empty
}

fun area(s: &Shape).R: f64 = when s {
    Circle(r) -> 3.14159 * r * r
    Rect(w, h) -> w * h
    Empty -> 0.0
}

fun main() {
    print(area(Shape.Circle(r = 2.0)))          // 12.566360
    print(area(Shape.Rect(w = 3.0, h = 4.0)))   // 12.000000
    print(area(Shape.Empty))                    // 0.000000
}
```

A `Copy` payload binds as a copy (`r` is an `f64`), an owned payload binds as a
borrow. Matching must be exhaustive.

## Collections and loops

```kelp
fun main() {
    var xs: List<i32> = List.empty()
    xs.push(7)
    xs.push(35)
    xs.sort()

    for x in xs {
        print!("$x ")
    }
    print("")

    var counts: Map<String, i64> = Map.new()
    counts.insert(key = "a", v = 1)
    if counts.has(key = "a") {
        print(counts.get(key = "a"))
    }
}
```

`List.empty()` and `Map.new()` need the element type from somewhere: write it on
the binding.

## Errors without exceptions

Fallible calls return `Result`, and `?` propagates a failure out of the enclosing
function. `if let` handles one on the spot:

```kelp
impl "std/str"

fun half(n: i64).R: result.Result<i64, str.ParseErr> {
    if n < 0 {
        return result.Result.Err(error = str.ParseErr.Invalid)
    }
    return result.Result.Ok(value = n / 2)
}

fun quarter(n: i64).R: result.Result<i64, str.ParseErr> {
    val h = half(n = n)?          // a failure returns immediately
    return half(n = h)
}

fun main() {
    val parsed = str.parse_i64("42")
    if let Ok(n) = parsed {
        print(n + 1)              // 43
    }

    val r = quarter(n = 84)
    if let Ok(v) = r {
        print(v)                  // 21
    }
}
```

`panic(message)` ends the program with a non-zero status; `assert(cond)` is the
debug assertion. There are no exceptions and no `try`.

## Files and authority

Anything outside the program is a capability, and the `impl` line is where it is
granted:

```kelp
impl "std/fs"
impl "std/str"

fun main() {
    val path = "/tmp/kelp-first.txt"
    fs.write_text(path, "written by kelp\n")
    val text = fs.read_text(path)
    print(text)

    val lines = str.split(text.as_str(), "\n")
    print(lines.len())
    fs.remove(path)
}
```

A module that is **not** the entry module holds only what its importer granted, so
a library that reads files asks for `fs` where the read is written, and the
consumer decides the pattern. See [Capabilities](/language/capabilities).

## Next

- [Projects and coral.toml](/getting-started/projects): the manifest, dependencies, tasks
- [Language](/language): the reference for everything above
- [Libraries (fpl)](/libraries): JSON, CSV, dates, globs, HTTP helpers
