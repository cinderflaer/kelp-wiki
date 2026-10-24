---
title: "Your first program"
description: "A guided tour of Kelp's shape in one file, with output - run through Coral from the first line so the manifest is never something you learn later."
isPublished: true
tags: "getting-started"
---
The Kelp repository ships four examples: `kelpc/tests/fixtures/examples/hello.kp`, `kelpc/tests/fixtures/examples/fib.kp`,
`kelpc/tests/fixtures/examples/download.kp` and `kelpc/tests/fixtures/examples/download_pool.kp` (the last one fetches
several URLs concurrently with one worker thread per connection pool: see
[Concurrency in v1](/language/concurrency)). This page walks the first two,
then adds the pieces a real program needs.

Every command here is shown twice, once as bare `kelpc` and once through
[Coral](/tooling/coral). Both work. Start with Coral anyway: it costs one
`coral.toml` now, and it is the thing you would otherwise have to learn later,
at the moment your program grows past a single file and suddenly needs a task or a
dependency.

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

### The same thing through Coral

```sh
coral init hello        # coral.toml, src/main.kp, tests/, src/tasks/
coral run               # builds, then runs, forwarding argv and the exit code
```

`coral init` writes the manifest and a sample `src/main.kp`, so the same program
from a project looks like this:

```toml
name = "hello"
version = "0.1.0"
entry = "src/main.kp"
```

and `coral run` builds and runs it. That is the whole difference at this size.
What it buys you later is [what a project is](/getting-started/projects): `impl`
paths relative to `src/`, dependencies fetched by `coral sync`, extra entry points
as `[tasks]`, and a single `coral build` that fetches what the project declares.

From here on the page uses `kelpc`, because it is one word shorter and makes the
language the subject. `coral build` and `coral run` accept the same sources.

`print` takes exactly one argument and adds a newline; `print!` does not. Templates
interpolate:

```kelp
fun main() {
    val who = "world"
    print("hello, $who")
    print("twice two is ${2 * 2}")
}
```

Inside `print`/`print!` a template writes its text directly. Anywhere else it is a
`String` value. To build text a piece at a time, use `String.push_str`:

```kelp
var out = String.empty()
out.push_str("hello, ")
out.push_str(who.as_str())
print(out)
```

## Records and functions

```kelp
datac Point(val x: i32, val y: i32)

fun area(p: Point) => i32 = p.x * p.y

fun main() {
    val p = Point(x = 3, y = 4)
    print(area(p))            // 12
    print(p.x)                // 3
}
```

- A `datac` field is `val` (immutable) or `var` (mutable). A field with no keyword is `val`.
- A parameter is a **borrow**, so `area(p)` does not move `p` and `p` is still
  usable afterwards.
- The return type is written `=> T`; no return type means the function returns `Unit`.

## Enums and `when`

```kelp
enum Shape {
    Circle(val r: f64)
    Rect(val w: f64, val h: f64)
    Empty
}

fun area(s: &Shape) => f64 = when s {
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

A `Copy` payload binds as a copy (`r` is an `f64`). Here `s` is a borrow, so an
owned payload would bind as a shared borrow; over an owned local it binds by value
and moves out. Matching must be exhaustive.

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
the binding, or let the first `push`/`insert`/`set` decide it.

## Errors without exceptions

Fallible calls return `Result`, and `?` propagates a failure out of the enclosing
function. `if let` handles one on the spot:

```kelp
impl "std/str"
impl "std/result"

fun half(n: i64) => result.Result<i64, str.ParseErr> {
    if n < 0 {
        return result.Result.Err(error = str.ParseErr.Invalid)
    }
    return result.Result.Ok(value = n / 2)
}

fun quarter(n: i64) => result.Result<i64, str.ParseErr> {
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

- [A first real tool](/getting-started/first-tool): a `head` that runs, with `argv` and an exit code
- [Projects and coral.toml](/getting-started/projects): the manifest, dependencies, tasks
- [Coral](/tooling/coral): `init`, `build`, `run`, `check`, `sync`, the compiler install
- [Language](/language): the reference for everything above
- [Libraries (fpl)](/libraries): JSON, CSV, dates, globs, HTTP helpers
