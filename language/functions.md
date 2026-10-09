---
title: "Functions"
description: "Declaring functions, named arguments, function values, closures, scoped blocks with exclusive captures, must_use, and how pd passdowns become hidden parameters."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §7](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

## Declaration

```kelp
fun add(a: i32, b: i32).return: i32 = a + b        // expression body, requires .return

fun greet(name: &str) {                       // no .return: returns unit
    print(str.concat("hello, ", name))
}

fun abs_diff(a: i32, b: i32).return: i32 {         // block body
    if a > b {
        return a - b
    }
    return b - a
}
```

- The keyword is `fun`; the return type is written `.return: T` **after** the
  parameter list. There is no `->`, no trailing type, and no inferred return type
  for a block body. No `.return` means `unit`.
- **`.R:` is an outdated spelling** of the same marker (outdated since 26.10.3). It still
  compiles, `kelpc build` and `kelpc run` print an `outdated:` finding for each
  one, and `--deny-outdated` turns the findings into errors; it is removed in the
  next development cycle. The two mean exactly the same thing and both are
  accepted on a declaration, a `fun` literal and a function type.
- An expression body (`= expr`) requires `.return: T`; a block body ends with
  `return expr`.
- Parameters are `name: T`. A parameter is a **shared borrow** of its argument.
  `name: mut T` is an exclusive borrow: the only spelling for mutation in
  parameter position (`&mut T` there is a parse error). `name: move T` takes
  ownership.
- `mut` and `move` are mutually exclusive, `move` is refused on a `str` or a
  `&T`, and a receiver is always borrowed (there is no `fun move Type.name()`).

## Named arguments

A call with more than one parameter can name its arguments. Names are matched
first, and the rest are matched by position:

```kelp
val p = Circle(r = 2.0, x = 1.0)
val d = math.pow(base = 2.0, exp = 8.0)
print(str.concat("a", "b"))            // positional is fine too
```

A name the function does not declare is an error, and so is naming an argument
twice. The convention in this repository is to use named arguments wherever a
call would otherwise be ambiguous: in practice every `datac` construction with
two or more fields.

## Overloading and recursion

- **A user program cannot overload a name.** `fun pick(a: i32)` and
  `fun pick(a: f64)` collide. Overloading exists only inside the shipped standard
  library, and only for `abs`, `min`, `max`, `clamp`, which is how `math.min`
  accepts `i32`, `i64` and `f64`.
- Recursion is unrestricted, including mutual recursion.
- A function may take type parameters: `fun first<T>(xs: List<T>).return: T`. Each
  call site is instantiated for the types it uses.

## Function values

A bare name of a declared `fun` is a value, typed `fun(T, U).return: V`: the `fun`
keyword, the parameter types, and the same `.return:` clause a declaration uses:

```kelp
fun double(x: i32).return: i32 = x * 2

fun apply(f: fun(i32).return: i32, x: i32).return: i32 = f(x)     // takes a callback

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
written `closure(T, U).return: V`.

```kelp
fun make(step: i32).return: closure(i32).return: i32 {
    return fun(x: i32).return: i32 = x * step
}

val f = make(3)
print(f(7))                        // 21, because `step` outlives `make`
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

In practice, a stdlib or library callback is written `closure(&T).return: U`, and a
`Copy` element is used **directly** inside the literal: `acc + x`, not
`acc + *x`:

```kelp
val total = listx.fold(xs, 0, fun(acc: i32, x: &i32).return: i32 = acc + x)
```

> **Anonymous functions are not named nested functions**
>
> There is no way to write a named nested function and no `dyn`-style boxing of
> one.

## Trailing blocks and scoped parameters

A `{ ... }` written on the same line after a call is that call's **last
argument**, a `fun` literal. A block may declare parameters by name only, and
their types come from the function type of the parameter the block is passed to.
A block whose body ends in an expression returns it when the expected return type
is non-unit.

A parameter written `scoped fun(T).return: U` accepts **only** a `fun` literal or a
trailing block written at the call site, never a stored value. Because the callee
may only call it during the call, the literal may capture an enclosing binding
**by borrow**, which an ordinary closure cannot do. The mode of each parameter
follows the expected type, so `scoped fun(mut Counter)` binds a block parameter as
an exclusive borrow.

```kelp
fun sum(xs: List<i32>, f: scoped fun(i32).return: i32).return: i32 {
    var total = 0
    var i: usize = 0
    while i < xs.len() {
        total += f(xs.get(i))
        i += 1
    }
    return total
}

fun main() {
    var xs: List<i32> = List.empty()
    xs.push(4)
    xs.push(5)
    xs.push(6)
    print(sum(xs) { n -> n * 10 })
}
```

```text
150
```

- A scoped value may be re-bound or passed to another scoped parameter: both stay
  inside the call.
- **A block may write what it captures** ([Exclusive
  captures](#exclusive-captures) below), under rules the compiler checks.
- A scoped value may not be stored in a `datac` field, returned, put in a
  container, passed to a plain parameter, or captured by another closure. Each of
  those is an ordinary type mismatch, because `scoped fun(...)` is a type of its
  own.
- The builder shape this exists for is `polyp.column { k -> k.text(s.title) }`,
  where the block reads the view's borrowed state.

### Exclusive captures

A block captures a binding **by exclusive borrow exactly when its body needs
one**. There is no annotation: writing through a capture (`s.count += n`,
`total = 5`), taking `&mut` of it, calling a `mut`-receiver method on it
(`xs.push(n)`) or passing it to a `mut` parameter makes that capture exclusive
for the whole call the block is written in. Every other capture stays what it
was: a shared borrow of an owned binding, or a copy of a `Copy` binding the block
only reads.

A needs-exclusive capture is accepted when the enclosing binding is an owned
`var` (a `datac`, a collection, a `String`, or a `Copy` scalar) or a `mut`
parameter, which the block reborrows for the call only. This program runs on
both backends:

```kelp
impl "std/sync"

datac State(var count: i32, var seen: List<i32>)

fun each(f: scoped fun(i32)) {
    f(1)
    f(2)
    f(3)
}

fun tally(s: mut State) {
    each { n ->
        s.count += n
        s.seen.push(n * 10)
    }
}

fun main() {
    var total = 0
    var calls = 0
    each { n ->
        total += n
        calls += 1
    }
    print(total)
    print(calls)

    var s = State(count = 100, seen = List.empty())
    tally(s)
    print(s.count)
    print(s.seen.len())

    // a lock block can update a local accumulator too
    val m: Mutex<i64> = Mutex.new(7)
    var grabbed: i64 = 0
    m.lock { v -> grabbed += *v }
    print(grabbed)
}
```

```text
6
3
106
3
7
```

`total` and `calls` are `Copy` scalars the block writes, so they are captured by
pointer and the new values are visible after the call. `tally` reborrows its
`mut` parameter. The owner is free again as soon as the call returns.

Inside the block an exclusive capture behaves like a `mut` parameter, so it can be
passed on to a function that takes `mut`, which is what lets an Elm-style drain
loop write the model without threading it through the callback (this is the body
of `pump` in the `excl_capture_drain` fixture, which prints `1`, `6`, `8`, `8` on
both backends):

```text
q.drain { msg ->
    update(model, msg)
    mark(model)
}
```

A `return` inside the block leaves only the block, and a `defer` in the block
runs when the block returns, once per call of it.

**What is refused**, each with the compiler's own text.

- Writing a `val`:

  ```
  error: cannot write to captured 'frozen': it is not declared 'var' in the enclosing function; declare it 'var' so a scoped block can write it
  ```

- Writing through a parameter that is only a shared borrow (`fun bump_all(s: State)`):

  ```
  error: cannot write to captured 's': it is a shared borrow in the enclosing function, so a block cannot write through it; take it as a 'mut' parameter there
  ```

- The same owner captured twice in one call, whether by two blocks or by a block
  and an ordinary argument (`two(s) { n -> s.count += n }` with
  `two(s: mut State, ...)`, or `both(fun(n: i32) { s.count += n }, fun(n: i32) { s.count += n * 2 })`):

  ```
  error: cannot borrow 's': already borrowed exclusively
  ```

- The owner is the call's receiver (`s.each { n -> s.count += n }`), or a field of
  it, or the callee's other argument is a shared view of it:

  ```
  error: cannot borrow 's' as exclusive: already borrowed exclusively
  error: cannot borrow 's' as exclusive: already borrowed as shared
  ```

  The second also covers a borrow taken before the call and still used after it
  (`val first = s.items.get(0)` ... `print(first)`): borrows end at their last
  use, so the same borrow dead before the call is fine.

- A `mut` parameter passed on in the same call that holds it in a block:

  ```
  error: cannot borrow 's' as exclusive: this call also uses it, and a block that writes through a captured exclusive borrow needs the call's other arguments to leave it alone
  ```

- A block inside a block is allowed (26.10.3) to use a name the outer block captures
  exclusively; what the inner call also uses is checked the same way, and a clash
  names the captured value:

  ```
  error: cannot borrow 'a captured value.count' as exclusive: this call also uses it, and a block that writes through a captured exclusive borrow needs the call's other arguments to leave it alone
  ```

- Returning a borrow from a block that holds an exclusive capture:

  ```
  error: this block writes through 's' (an exclusive capture) and returns a borrow ('str'): the borrow would outlive the call that holds 's' exclusively; return an owned value (a copy or a 'String.from_str(...)') instead
  ```

- Storing the block is still refused, unchanged: it may only be passed to another
  `scoped fun(...)` parameter, so a callback that must outlive the call is a
  message value, not a block.

The same rule is the reason [`Mutex.lock`](/stdlib/sync) and the other block APIs
can update a local accumulator. Its remaining limits are listed under
[Scoped blocks](/language/limits#scoped-blocks) in Limits in v1.

## `must_use`

`must_use fun` marks a function whose result a caller has to look at. A call to
one used as a statement, with the result thrown away, is a compile error:

```kelp
must_use fun check(n: i32).return: bool = n > 0

fun main() {
    check(1)             // error: the result of 'check' must be used
    val _r = check(1)    // the explicit discard
    if check(2) { print("ok") }
}
```

It goes where `unsafe` and `naked` go (`pub must_use fun`). The standard library
marks `Sender.send` (a refused send hands the value back) and the `fs.try_*`
mutators (`None` is success, `Some(IoErr)` is the failure). It is not a type
attribute: only a call written as a statement is checked, so passing the result
on, branching on it or binding it counts as using it.

## `pd` passdowns as hidden parameters

A function that mentions a `pd` binding gets it wired in as a hidden parameter;
one that never mentions one pays nothing. The parameter is a shared borrow
unless the function writes the passdown, directly or through a function it
calls, in which case it is exclusive. See
[Modules and imports](/language/modules).

## See also

- [Methods and receivers](/language/methods)
- [Return types and `return`](/language/returns)
- [Generics and type parameters](/language/generics)
- [Control flow](/language/control-flow) for `return` and the divergence rule
