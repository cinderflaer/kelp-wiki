---
title: "Collections"
description: "The builtin containers: List<T>, Map<K, V>, Box<T> and the fixed-size array [T; N]. What each one may hold, and its methods."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §12](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md).

Three containers are compiler builtins: `List<T>`, `Map<K, V>` and `Box<T>`. They
are owned values with the same move and drop rules as everything else, and each
one owns its elements. The element sets are not the same: a `List` element and a
`Box` element may themselves be a `List` or a `Box`, while a `Map` value is
narrower, and every container refuses a borrow, a view, an atomic, a function
value and `unit` as an element.

A fourth type is not a container at all in that sense: `[T; N]`, a fixed-size
array whose length is part of its type. It allocates nothing, so it is what a
fixed-size buffer is written as (`[T; N]` below).

## `List<T>`

```kelp
var xs: List<i32> = List.empty()      // element type from the annotation
var zs = List.empty()                 // element type from the first `push`
zs.push(1)                            // ... which is this one
var ys = List.of(String.from_str("a"))   // element type from the argument

xs.push(3)
xs.push(1)
print(xs.len())
print(xs.get(0))
xs.set(0, 30)
xs.sort()
print(xs.contains(30))
val first_two = xs.slice(0, 2)
while !xs.is_empty() {
    print(xs.pop())
}
```

| Method | Takes | Returns |
| --- | --- | --- |
| `List.empty()` | nothing | empty list; element type from the context, or from the first `push`/`insert`/`set` |
| `List.with_capacity(n)` | `usize` or `i64` | an empty list with room for at least `n` elements, so filling it with `push` allocates once; the element type comes from the binding, and the list still grows past `n` |
| `List.of(x)` | one value | a list holding it |
| `len()` / `is_empty()` | shared | `usize` / `bool` |
| `get(i)` | shared, `usize` | the element, or a borrow of it |
| `set(i, v)` | exclusive | `unit` |
| `push(v)` | exclusive | `unit`; moves the element in |
| `pop()` | exclusive | the last element, moved out |
| `insert(i, v)` / `remove(i)` | exclusive | `unit` / the removed element |
| `clear()` | exclusive | `unit` |
| `clone()` | shared | a second owned list: the elements are copied, and every owned element with them |
| `sort()` | exclusive | `unit`, for sortable elements |
| `reverse()` | exclusive | `unit` |
| `contains(v)` | shared | `bool`, for comparable elements |
| `slice(from, to)` | shared | a copy of the range, for clonable elements |

`get` and `pop` move an owned element out and return a copy for a `Copy` element,
so `List<i32>.get(i)` is an `i32` while `List<String>.get(i)` is a `&String`.
Out-of-range indices and popping an empty list panic.

`clone()` is what a caller reaches for when the callee takes a list by value:
`str.join` consumes its list, so `str.join(sep = ",", parts = xs.clone())` leaves
`xs` usable. Every owned element is copied too, so the element type has to be
clonable.

A **`datac`/`enum` element gets a derived deep copy and a derived order from its
fields**, and a tuple element takes the same two position by position. It is
clonable (so `clone` and `slice` work) when every field it holds is, and sortable
when every field has an order. The order is field by field in declaration order,
a `String`/`Bytes` byte-wise, an `enum` by tag and then by the live variant's
payload:

```kelp
datac Digest(val path: String, val size: u64)

var xs: List<Digest> = List.empty()
xs.push(Digest(path = "b", size = 2))
val copy = xs.clone()     // a second list, with its own strings
xs.sort()                 // by path, then by size
```

A `List`, `Box`, `Map` or owned-array field has neither, so a record holding one
is refused for both, and the diagnostic says which. `contains` still needs
equality, which a `datac` does not have: a keyable `datac`'s derived equality is
`Map`'s own, used to find a key, and it is not a `==` a program can write.
`Map`'s `get_or` and `values` take the same clonable value set the `List`
operations take, so a map of records copies its value out.

Scalars sort too, and so do `f32`/`f64`: a float list with a `nan` in it has no
meaningful order, which is why [`stats`](/libraries/stats) and
[`benchkit`](/libraries/benchkit) carry their own sorts for data that may
contain one.

### Restriction: the element set

The element type may be a scalar, `String`, `Bytes`, a `datac`/`enum`, a tuple,
another `List`, or a `Box`. It may **not** be a `Map`, a borrow, a `str`, a
`View`, an atomic, a function value or `unit`. A list of lists needs no wrapper:

```kelp
val rows: List<List<String>> = List.empty()
```

To hold a list inside a list element through a name, wrap it in a one-field
`datac`. That is a naming choice, not a requirement of the language.

`Box<T>` is the owning pointer for a *recursive* type:

```kelp
datac Node(val value: i32, val next: Box<Node>)
```

## `Map<K, V>`

```kelp
var counts: Map<String, i64> = Map.new()
counts.insert(key = "one", v = 1)
counts.insert(key = "two", v = 2)
print(counts.has(key = "two"))
print(counts.get(key = "two"))
print(counts.get_or(key = "nope", fallback = 0))
counts.insert(key = "two", v = 22)
print(counts.remove(key = "one"))
print(counts.keys().len())

var runs: Map<i32, i64> = Map.new()        // a scalar key
runs.insert(key = 7, v = 3)
print(runs.get(key = 7))
```

- Entries keep **insertion order**, which is why `keys()` and `values()` are lists
  and not hash order.
- **`Map<V>` written with one argument means `Map<String, V>`.**
- **A key must be keyable.** The compiler derives a key's hash and equality from
  `K`. A derived key is `String`, an integer, `bool`, `char`, or a `datac`, `enum`
  or tuple whose every field is itself keyable. A float is refused, because
  `nan != nan` would make an inserted key impossible to find again.
- **A key type can declare its own hash and equality instead.** A `datac` or `enum`
  that the derivation refuses needs both of these, with exactly these signatures:

  ```kelp
  fun T.hash().return: u64
  fun T.eq(other: &T).return: bool
  ```

  The map then calls these two in place of a derived pair. Declare both or neither.
  The key is still cloned into the entry, so the type must also be deep-copyable.
- On current `main`, an enum cannot be a `Map` key or a `Map` value. The checker refuses an
  enum value: `'Status' cannot be a 'Map' value: a hosted build cannot describe an 'enum'
  inside a map's entry yet, and a 'datac' that holds the enum is refused the same way. Keep
  the values in a `List<Status>` and store each value's index in the map instead`. A
  `Map<Kind, i32>` key was refused in a build before that check, with `a hosted build
  describes the enum 'Kind' only as a heap object (a Box payload or a List element); an enum
  stored inside a datac is not described yet`.
- A `Bytes`, container, view, borrow, or a `datac`/`enum` with a field outside the
  keyable set is refused. The message names the field, or the missing half of the
  pair.
- **A value is narrower than a list element.** The value set is a scalar,
  `String`, `Bytes`, a `datac`/`enum` or a tuple, so `Map<String, List<i32>>` and
  `Map<String, Box<i32>>` are refused; a value that holds a list wraps it in a
  one-field `datac`.
- A `Map` cannot be a list element or a map value.
- A `String`-keyed map takes its key as a bare `str` in every method (the map
  copies it in), a scalar key is passed by value, and a user key type is passed by
  shared borrow. That split is why
  [`set`](/libraries/set) ships two types instead of one generic set.
- **`Map.with_capacity(n)` sizes both buffers up front.** The count is a hint and
  never a fence: the index and the entry array start with room for `n` entries, a
  map that outgrows it grows exactly like one that started empty, and insertion
  order, `keys()` order and tombstone reuse are unchanged. It is the constructor
  for a caller that knows how many entries it is about to insert, and the only
  way to pay the growth once rather than as a series of rebuilds. The argument
  gets its key and value types from the binding, as `Map.new()` does.

| Method | Returns |
| --- | --- |
| `Map.new()` / `Map.empty()` | an empty map; key and value types from the binding, or from the first `insert` |
| `Map.with_capacity(n)` | the same empty map with room for `n` entries; `n` is a `usize` or an `i64` |
| `len()` / `is_empty()` | `usize` / `bool` |
| `insert(key, v)` | `unit`; stores `true`-style upsert |
| `get(key)` | the value, or a borrow of it; panics when absent |
| `get_or(key, fallback)` | the value or the fallback |
| `has(key)` | `bool` |
| `remove(key)` | the value, moved out; **panics** when the key is absent |
| `keys()` / `values()` | `List<K>` / `List<V>`, insertion order |
| `clear()` | `unit` |

## `Box<T>`

A box holds one value or nothing. It is the owning pointer, and it is what makes
recursive types (and moving a value out of a borrowed structure) expressible.

```kelp
var slot: Box<i32> = Box.empty()
print(slot.is_empty())
slot.set(5)
print(slot.get())
print(slot.take())          // moved out; the box is empty again

var list = Node(value = 1, next = Box.empty())
list = Node(value = 2, next = Box.of(list))
```

| Method | Returns |
| --- | --- |
| `Box.empty()` | an empty box |
| `Box.of(v)` | a box holding `v` |
| `is_empty()` | `bool` |
| `get()` | a copy for a `Copy` element, otherwise a borrow |
| `set(v)` | `unit` |
| `take()` | the value, moved out; the box is left empty. **Panics** on an empty box |

A `Box` can also hold a trait object, `Box<dyn Name>`, which has its own method
surface (no `take` or `set`) and is the owned form of `&dyn Name`; see
[Owned trait objects](/language/box-dyn).

## `[T; N]`

A fixed-size array: `N` elements of `T` held inline, with the length part of the
type, so `[u8; 4]` and `[u8; 8]` are different types. Nothing is allocated, which
is the point: a page table, an IDT/GDT or a register-save frame has to exist with
no allocator in the path.

```kelp
const PAGE_SIZE: usize = 4096
const ENTRY_SIZE: usize = 8
const ENTRIES: usize = PAGE_SIZE / ENTRY_SIZE

val xs: [i32; 3] = [10, 20, 30]         // the length is the count of elements
print(xs.len())                          // 3, from the type: nothing is loaded
print(xs.get(i = 1))

var buf: [u8; 4] = [0; 4]                // the repeat form: a zeroed buffer
buf.set(i = 2, v = 7)

val table: [u64; ENTRIES] = [0; ENTRIES]
val grid: [[u8; 2]; 3] = [[1, 2], [3, 4], [5, 6]]   // nesting is held inline
print(grid.get(i = 2).get(i = 1))
```

| Method | Takes | Returns |
| --- | --- | --- |
| `len()` | shared | `usize`, as a compile-time constant |
| `is_empty()` | shared | `bool`, always `false` |
| `get(i)` | shared, `usize` | the element, or a borrow of it |
| `set(i, v)` | exclusive, `usize` | `unit` |

- The length is a **compile-time constant**: a literal, another `const`, or an
  expression over them ([Constants](/language/passdowns) has the rules). A `val`
  computed at runtime is refused.
- The element may be a scalar, `String`, `Bytes`, a `datac`, an `enum`, a tuple,
  or another array. It may not be a borrow or a `List`/`Map`/`Box`.
- The array is `Copy` when the element is. `[i32; 3]` is a value you can assign
  freely; `[String; 3]` owns its three strings, so assigning it moves it, and
  `set` drops the element it replaces.
- `[x; N]` copies `x` into every slot, so `x` has to own nothing: a scalar, or a
  `datac` whose fields are all scalars. A `String` element is refused by name,
  because `[s; 4]` would be four owners of one buffer.
- There is no `[T; 0]`, no `a[i]` subscript (use `.get`/`.set`) and no growth. A
  sequence that grows is a `List<T>`.
- A `datac` field may be one, and so may a parameter, a return value or a
  `Box` element. A plain parameter follows the rule every other type follows
  ([Ownership and borrowing](/language/ownership)): an array whose element owns
  something is borrowed, so the caller keeps its array, a `Copy` array is passed
  by value as a scalar is, `mut [T; N]` writes through a borrow and
  `move [T; N]` takes the value over.

## Iterating

`for x in xs` walks a `List<T>` or a `[T; N]`
([Control flow](/language/control-flow)). `for (key, value) in map` walks a `Map`
(a snapshot of its keys, in insertion order,
[Iterators](/language/iterators)); `for v in map.values()` walks the values
alone.

## See also

- [`std/list`](/stdlib/list) for `map`, `filter`, `each`, `find_index`,
  `any`, `all`
- [`listx`](/libraries/listx) for `fold`, `zip`, `chunks`, `sort_by`,
  `sum`/`min`/`max`, `unique`
- [`set`](/libraries/set) for `Set<T>` and `StrSet`
