---
title: "Types"
description: "Source section - syntax.md \u00a73."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §3](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Kelp's types fall into three kinds, and the kind decides what assignment means:
a `Copy` value is copied, an owned value is *moved*, and a borrowed value is only
valid inside the scope that lent it.

## The table

| Type | Kind | Notes |
| --- | --- | --- |
| `i32` `i64` `u8` `u16` `u32` `u64` `usize` `isize` | Copy | integers; all widths are distinct |
| `f32` `f64` | Copy | IEEE floats |
| `bool` | Copy | `true` / `false` |
| `char` | Copy | one Unicode scalar value, written `'x'`. A code point, **not** an integer |
| `str` | borrowed | NUL-terminated UTF-8 view into storage owned elsewhere. No length: deriving one costs a `strlen` |
| `View` | borrowed | a **length-carrying** borrowed text view: pointer *and* length. Slices without allocating, scans without `strlen` |
| `String` | owned | UTF-8 text, validated on construction, freed at scope exit |
| `Bytes` | owned | raw byte buffer, freed at scope exit |
| `List<T>` | owned | growable sequence, one instantiation per element type |
| `Map<K, V>` | owned | keyed container, keeps insertion order; `Map<V>` means a `String` key |
| `Box<T>` | owned | one heap cell holding a `T` or nothing |
| `Atomic<T>` | owned | one location every access to which is a single atomic operation; **not `Copy`**, owns nothing and needs no drop. `T` is `bool` or an integer type. See [`std/atomic`](/stdlib/atomic) |
| `[T; N]` | Copy / owned | fixed-size array: `N` elements held **inline**, with the length part of the type and nothing allocated. `Copy` when `T` is, otherwise an owner that drops each element |
| `datac` name | owned | record with per-field `val`/`var`, optionally with type parameters |
| `enum` name | owned | tagged union: exactly one variant is live |
| `fun(T, U).R: V` | Copy | a function value: a function pointer, with the parameters it takes and what it returns |
| `closure(T, U).R: V` | owned | a function value **plus** the environment its captures were moved into |

There is no `void`: a function with no `.R: T` returns `Unit`.

## Nothing converts itself, except text

Operands must match exactly: there is no implicit numeric promotion at all. The
one implicit conversion in the language is `str`/`View` → `String`, and it fires
only at an exact `String` expectation:

```kelp
datac Doc(val title: String)

val d = Doc(title = "a title")     // the literal becomes the String
var xs: List<String> = List.empty()
xs.push("pushed")                  // so does an element
val s: String = "a literal"        // and an assignment
```

Nothing converts back: `String` → `str` is a borrow, written `.as_str()`.
[Text](/language/text) covers the whole picture.

## Integers convert explicitly

`to_<T>()` exists on every integer type for every integer type, and
`to_f64()`/`to_f32()` widen to a float. Widening is exact; **narrowing panics
when the value does not fit**; a float has no `to_<int>` at all, because that
would silently drop the fraction. Every conversion that can lose a value also
has a **fallible twin**, `try_to_<T>()`, which hands back `Option<T>` instead of
panicking:

```kelp
val n: i64 = 7
val x: f64 = n.to_f64()        // 7.0, exact for every i64
val b: u8 = 200
val idx: usize = b.to_usize()  // a byte used as an index
val back: u8 = idx.to_u8()     // panics if it does not fit
val small = idx.try_to_u8()    // Option<u8>: None where to_u8 would panic
```

`try_to_<T>` exists exactly where the plain conversion can fail: a widening is
already exact, so `b.try_to_usize()` is not a method (write `b.to_usize()`), and
the diagnostic names that rule. The `Option` it hands back is
[`std/option`](/stdlib/option)'s, so `if let Some(v) = idx.try_to_u8()` needs no
type written anywhere. That module has to be somewhere in the program's import
graph; a program that imports `std/str` has it already, since `std/str` imports
it, and one that imports nothing at all is told to add the `impl` line.

`n * 1.0` is a **type error**, not a conversion (syntax.md §5.0).

## Generic types

A `datac` or `enum` may declare type parameters, and each use site instantiates
them:

```kelp
datac Pair<A, B>(val first: A, val second: B)

val p: Pair<i32, String> = Pair(first = 1, second = "one")
```

- Write the arguments wherever a type is written: `Pair<i32, String>`,
  `List<Option<i32>>`, `Box<Pair<i32, i32>>`. The count is checked.
- Two instantiations are two different types: `Pair<i32, i32>` cannot be passed
  where `Pair<String, String>` is expected.
- A type argument may not be `str` or a reference: a field may not be borrowed.
- A generic type may refer to itself **through a `Box` or a `List`**.
- A `fun` may declare type parameters too (`fun identity<T>(x: T).R: T`), and a
  call site instantiates them, by inference or by writing them
  (`identity<i32>(x = 5)`).

## Truth and falsiness

There is none: `if` and `while` take a `bool`, and nothing else converts to one.

## See also

- [Text](/language/text) for `str`, `View`, `String`, `Bytes`
- [Collections](/language/collections) for `List`, `Map`, `Box`
- [Bindings and assignment](/language/bindings)
- [Generics and type parameters](/language/generics)
- [datac and enum](/language/data-types)
- [Ownership and borrowing](/language/ownership)
