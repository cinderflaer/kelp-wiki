---
title: "Const generics and `impl Trait` arguments"
description: "A datac, enum or fun can take a const parameter such as N: usize, inferred from an array argument. fun f(x: impl Shape) is shorthand for a bounded type parameter. Arithmetic on N in a type and impl Trait returns are refused."
isPublished: true
tags: "language"
---
Source: [`language/const-generics.md`](/language/const-generics).

Two spellings that remove a reason to write a converter: a **const type
parameter**, a compile-time value in the type-argument slot, and **`impl Trait`
in argument position**. Both are the generic machinery
([Generics and type parameters](/language/generics)) with a small front-end
change, so neither backend learned a new case.

## Const type parameters

A parameter of a `datac`, an `enum` or a `fun` may be a value instead of a type:

```kelp
datac Ring<const N: usize>(var items: [i32; N], var len: int)
fun sum<const N: usize>(a: &[i32; N]) => i32
fun mut Ring<const N: usize>.push(v: i32) => bool
```

The declared type is one of `usize`, `u8`, `u16`, `u32`, `u64`, `i32`, `i64` or
`bool`. This program uses it for a fixed-capacity ring, a summing function and
`impl Trait` arguments:

```kelp
const CAP: usize = 4

datac Ring<const N: usize>(var items: [i32; N], var len: int)

fun mut Ring<const N: usize>.push(v: i32) => bool {
    if self.len >= N.to_int() {
        return false
    }
    self.items.set(i = self.len, v = v)
    self.len += 1
    return true
}

fun Ring<const N: usize>.capacity() => usize = N

fun sum<const N: usize>(a: &[i32; N]) => i32 {
    var total: i32 = 0
    var i: int = 0
    while i < N.to_int() {
        total += a.get(i = i)
        i += 1
    }
    return total
}

trait Shape {
    fun Self.area() => i64
}

datac Square(val side: i64)
datac Rect(val w: i64, val h: i64)

impl Shape for Square {
    fun Self.area() => i64 = self.side * self.side
}

impl Shape for Rect {
    fun Self.area() => i64 = self.w * self.h
}

fun bigger(a: impl Shape, b: &impl Shape) => bool = a.area() > b.area()

fun main() {
    var small = Ring(items = [0; 2], len = 0)
    var large: Ring<CAP> = Ring(items = [0; CAP], len = 0)
    print(small.capacity())
    print(large.capacity())
    print(small.push(1))
    print(small.push(2))
    print(small.push(3))
    print(large.push(7))
    val xs: [i32; 3] = [4, 5, 6]
    print(sum(a = &xs))
    val r = Rect(w = 2, h = 8)
    print(bigger(Square(side = 3), &r))
}
```

It prints:

```
2
4
true
true
false
true
15
false
```

- `Ring(items = [0; 2], len = 0)` infers `N = 2` from the array, and
  `Ring<CAP>` writes the argument explicitly. `Ring<2>` and `Ring<4>` are two
  types with two sets of generated functions, each keeping its own state.
- Inside the body `N` is a **value**: `self.len >= N` compares against `2` or
  `4`. It is an array length too (`[0; N]`, `[i32; N]`).
- `sum(a = &xs)` infers `N = 3` from `&xs`'s type, with nothing else to go on. A
  `[T; N]` against an `[i32; 4]` binds `T` and `N` together. A parameter nothing
  determines is the ordinary "cannot infer" error.
- A parameter written `&[i32; N]` is a borrow of the caller's array, the one way
  to say that, because an array is otherwise a by-value type.
- A `bool` parameter (`datac Flag<const ON: bool>`) reads as a bool in the body.
- A `char` parameter (from 26.10.4) reads as a character in the body, and each
  character is its own instantiation:

  ```kelp
  fun glyph<const C: char>() => char = C

  fun main() {
      print(glyph<'x'>())      // x
  }
  ```

### Writing the argument

A const argument is written exactly like a type argument, and may be a literal, a
`const` (of this module or another), arithmetic over those, or a call to a plain
`fun`: `Buf<16>`, `Buf<SIZE * 2>`, `capacity<twice(n = 4)>()`. The parser tells a
const argument from a type argument by lookahead: a literal, a leading `-`, or a
name that is called or used in arithmetic is a value, and a bare or dotted name
is read as a type and turned back into the constant where the parameter is a
`const`.

### Refusals

- **Arithmetic on a const parameter inside a type** (`[T; N + 1]`, `Buf<N * 2>`):

  ```
  error: 'N' is a const parameter, and arithmetic on one in a type ('[T; N + 1]') is not in this slice: write the length the instantiation binds ('[T; N]'), or compute it from a 'const' ('const M: usize = ...')
  ```

- **A length mismatch** reports both lengths:

  ```
  error: argument 'a' has type '[i32; 3]', expected '[i32; 4]'
  ```

- A value that does not fit the declared type, a const parameter used where a
  type belongs, a type written where a const argument belongs (or the reverse),
  and a `bool` parameter given a non-boolean.
- **A const parameter on a trait**, or a const argument in a trait's argument
  list.
- **A `char` parameter used as an array length** (`[i32; C]`), arithmetic on one
  (`[i32; C + 1]`), or a `char` parameter given a number (and the reverse). These
  are refused by name.
- **A const parameter that is not an integer, `bool` or `char`.**

## `impl Trait` in argument position

`fun f(x: impl Shape, y: &impl Shape)` is sugar for two fresh type parameters,
one per `impl`, each bounded by the trait: `fun f<A: Shape, B: Shape>(x: A, y:
&B)`. The two may be different types, as in `bigger(Square(side = 3), &r)` above.
Everything after parsing sees an ordinary generic function, so the bound is
checked and the body is instantiated per concrete type.

It is legal as a whole parameter type, bare or behind `&`. It is refused in:

- a **return type**: write `fun f<T: Trait>(...) => T` when the caller picks the
  type, or return a `Box<dyn Trait>` ([Owned trait objects](/language/box-dyn)):

  ```
  error: 'impl Trait' is not allowed in return position: write a named type parameter and bound it ('fun f<T: Trait>(...) => T') when the caller needs a concrete type, or return the owning value ('Box<dyn Trait>')
  ```

- a `val`/`var` type, a field, an enum payload, a container element and any
  nested position (`List<impl Shape>`):

  ```
  error: 'impl Shape' is only legal as a whole parameter type of a declared function: write 'fun f(x: impl Shape)', and name a type parameter where a stored, returned or container type belongs
  ```

- a receiver method's parameter, and a trait method's signature.
- **Two traits in one `impl`.** `impl A + B` is a parse error; write a type
  parameter bounded `T: A + B`.

## See also

- [Generics and type parameters](/language/generics)
- [Traits and static dispatch](/language/traits)
- [Collections](/language/collections) for the fixed-size array `[T; N]`
- [Constants and passdowns](/language/passdowns)
