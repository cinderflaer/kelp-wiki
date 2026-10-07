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
| `Box<dyn Name>` | owned | an owned trait object: the address of a heap value plus a vtable, two words, **not `Copy`**, dropped through the vtable. See [Owned trait objects](/language/box-dyn) |
| `Atomic<T>` | owned | one location every access to which is a single atomic operation; **not `Copy`**, owns nothing and needs no drop. `T` is `bool` or an integer type. See [`std/atomic`](/stdlib/atomic) |
| `Ptr<T>` | Copy | a raw pointer: one machine address, may be null, owns nothing, needs no drop, carries no borrow tracking. `T` is a scalar, `bool`, `char`, a `datac`/`enum`, a fixed-size array, an `extern type` handle or another `Ptr`. Building one and doing arithmetic on it are safe; dereferencing it needs `unsafe`. See [Unsafe code and raw pointers](/language/unsafe) |
| `Mutex<T>`, `RwLock<T>` | owned | a lock around one owned value, reached only through a scoped block; **not `Copy`**, hosted only. See [`std/sync`](/stdlib/sync) |
| `Condvar` | owned | a condition variable paired with a `Mutex<T>` through `wait_while`; **not `Copy`**, hosted only. See [`std/sync`](/stdlib/sync) |
| `Thread<T>` | owned | a handle on one worker the runtime owns; **not `Copy`**, one pointer to a worker record. `T` is the entry point's return type. Accepted as a local, a `datac`/`enum` field and a parameter, refused as a `List`/`Map`/`Box`/array element, because joining is a one-shot thing a container's own routines would duplicate. See [`std/thread`](/stdlib/thread) |
| `[T; N]` | Copy / owned | fixed-size array: `N` elements held **inline**, with the length part of the type and nothing allocated. `Copy` when `T` is, otherwise an owner that drops each element |
| `datac` name | owned | record with per-field `val`/`var`, optionally with type parameters |
| `enum` name | owned | tagged union: exactly one variant is live |
| `(A, B)` | owned | a tuple: two or more element values held in **position order**. Not `Copy`, and it takes the derived deep copy and the derived order a `datac` takes, position by position. Read by destructuring or by position `t.0` ([Bindings and assignment](/language/bindings)) |
| `fun(T, U).R: V` | Copy | a function value: a function pointer, with the parameters it takes and what it returns |
| `closure(T, U).R: V` | owned | a function value **plus** the environment its captures were moved into |

There is no `void`: a function with no `.R: T` returns `Unit`, which has no
representation, so a binding of one holds nothing ([Returns](/language/returns)).

## Tuples

A tuple is two or more values held in **position order**, and it is a type:
`(i32, i32)` is a pair of `i32`s, written wherever a type is written.

```kelp
fun min_max(xs: &List<i32>).R: (i32, i32) {
    // ...
    return (lo, hi)
}

val (lo, hi) = min_max(xs)      // a tuple value is read by destructuring
```

- **Two or more elements.** `(T)` is not a one-element tuple: it is the
  parenthesized type `T`, exactly as `(e)` is the parenthesized expression `e`,
  so `val x = (5)` binds an `i32`. `()` is refused by name, because the absent
  value's type is spelled `unit`.
- **A tuple owns its elements.** There is nothing to declare: the compiler
  derives one record per element list, and an element is stored by value where
  the tuple sits. An element is field-like, so a borrow, a `str` or a `View`
  cannot be one, and neither can `unit`.
- **Not `Copy`.** Assigning a tuple moves it, and a parameter of the type
  borrows it, exactly as for a `datac`. Each element is copied or moved by its
  own rule.
- **The derived deep copy and the derived order are position by position**, the
  way a `datac`'s are field by field: `List.sort` orders a tuple whose elements
  have an order (the first position decides, the second breaks the tie), and
  `List.clone`/`List.slice`/`Map.get_or` copy a tuple whose elements can each be
  deep-copied ([Collections](/language/collections)). There is no `==` between
  two tuples, exactly as there is none between two `datac`s.
- **A position is read by destructuring or by a constant index.** `t.0` is the
  first position and `t.1.0` the first of the second (a literal only; there is no
  `t.n` with a variable). `val (lo, hi) = p` binds both positions, `_` ignores
  one, and a nested tuple takes a nested pattern
  ([Bindings and assignment](/language/bindings)). A tuple also takes part in a
  `for (a, b) in pairs` and in a `when (a, b)` ([Control flow](/language/control-flow)).
  Reading an owned position of a local (`t.0`) is a partial move, as for a
  `datac` field.
- **Where a tuple may appear:** wherever its elements may. A local, a parameter,
  a return type, a `datac` field, an `enum` payload, a `List`/`Map`/`Box`/array
  element, and a type argument.
- A tuple is a record, so `print` refuses one exactly as it refuses a `datac`:
  print its positions instead.

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
  A tuple is concrete, so it is a legal type argument: `List<(i32, i32)>`,
  `Box<(String, u64)>`.
- A generic type may refer to itself **through a `Box` or a `List`**.
- A `fun` may declare type parameters too (`fun identity<T>(x: T).R: T`), and a
  call site instantiates them, by inference or by writing them
  (`identity<i32>(x = 5)`).

## Opaque native handles

A module with an `[extern."<module id>"]` manifest section may declare an
`extern type`, an opaque pointer-sized `Copy` value with no readable contents:
`pub extern type Widget`. A handle is the only way a native pointer crosses the
boundary. It compares with `==`/`!=` (the pointers) and has no arithmetic, no
conversion to or from an integer, and no `print`; a parent chain, `null()`,
`is_null()` and the unchecked `cast()` are covered in
[User FFI](/language/externs).

## Truth and falsiness

There is none: `if` and `while` take a `bool`, and nothing else converts to one.

## See also

- [Text](/language/text) for `str`, `View`, `String`, `Bytes`
- [Collections](/language/collections) for `List`, `Map`, `Box`
- [Bindings and assignment](/language/bindings)
- [Generics and type parameters](/language/generics)
- [datac and enum](/language/data-types)
- [Ownership and borrowing](/language/ownership)
