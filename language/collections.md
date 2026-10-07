---
title: "Collections"
description: "Source section - syntax.md \u00a712."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §12](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Three containers are compiler builtins: `List<T>`, `Map<K, V>` and `Box<T>`. They
are owned values with the same move and drop rules as everything else, and each
one owns its elements. The element sets are not the same: a `List` element and a
`Box` element may themselves be a `List` or a `Box`, while a `Map` value is
narrower, and every container refuses a borrow, a view, an atomic, a function
value and `Unit` as an element.

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
| `set(i, v)` | exclusive | `Unit` |
| `push(v)` | exclusive | `Unit`; moves the element in |
| `pop()` | exclusive | the last element, moved out |
| `insert(i, v)` / `remove(i)` | exclusive | `Unit` / the removed element |
| `clear()` | exclusive | `Unit` |
| `clone()` | shared | a second owned list: the elements are copied, and every owned element with them |
| `sort()` | exclusive | `Unit`, for sortable elements |
| `reverse()` | exclusive | `Unit` |
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
`View`, an atomic, a function value or `Unit`. A list of lists needs no wrapper:

```kelp
val rows: List<List<String>> = List.empty()
```

A one-field `datac` is still how a library gives the inner list a name, as
`csv.Row`, `listx.Chunk` and `table.Row` do; it is a naming choice, not a
requirement of the language.

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
- **A key must be keyable.** The compiler derives the key's hash and equality from `K`, so the derived set is `String`, an integer, `bool`, `char`, or a `datac`/`enum`/tuple whose every field, variant payload or position is itself keyable. A `datac` or `enum` the derivation refuses becomes a key by declaring both `fun T.hash().return: u64` and `fun T.eq(other: &T).return: bool`, which the map calls instead of a derived pair and never alongside one; both halves are required, the two signatures are fixed (a shared receiver, no type parameters, `eq` taking one `&T`), and a half or a signature the map cannot call is refused where it is declared. The key is still cloned into the entry, so the type has to be deep-copyable as well. A float is refused (`nan != nan` would make an inserted key unfindable), and a `Bytes`, container, view, borrow or `datac`/`enum` with a field outside those sets is refused with a message that names the field (or names the half of the pair that is missing). A tuple declares no method, so it is a key by derivation or not at all.
- **A value is narrower than a list element.** The value set is a scalar,
  `String`, `Bytes`, a `datac`/`enum` or a tuple, so `Map<String, List<i32>>` and
  `Map<String, Box<i32>>` are refused; a value that holds a list wraps it in a
  one-field `datac`.
- `Map<K, V>` is neither a list element nor a map value, so
  `Map<String, Map<i32>>` is impossible.
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
  takes the binding's written types for `K` and `V`, as `Map.new()` does, because
  it is a count and not an element.

| Method | Returns |
| --- | --- |
| `Map.new()` / `Map.empty()` | an empty map; key and value types from the binding, or from the first `insert` |
| `Map.with_capacity(n)` | the same empty map with room for `n` entries; `n` is a `usize` or an `i64` |
| `len()` / `is_empty()` | `usize` / `bool` |
| `insert(key, v)` | `Unit`; stores `true`-style upsert |
| `get(key)` | the value, or a borrow of it; panics when absent |
| `get_or(key, fallback)` | the value or the fallback |
| `has(key)` | `bool` |
| `remove(key)` | the value, moved out; **panics** when the key is absent |
| `keys()` / `values()` | `List<K>` / `List<V>`, insertion order |
| `clear()` | `Unit` |

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
| `set(v)` | `Unit` |
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
| `set(i, v)` | exclusive, `usize` | `Unit` |

- The length is a **compile-time constant**: a literal, another `const`, or an
  expression over them ([Constants](/language/passdowns) has the rules). A `val`
  computed at runtime is refused.
- The element may be a scalar, `String`, `Bytes`, a `datac`, an `enum`, a tuple,
  or another array. It may not be a borrow or a `List`/`Map`/`Box`.
- The array is `Copy` when the element is. `[i32; 3]` is a value you can assign
  freely; `[String; 3]` owns its three strings, so assigning it moves it, and
  `set` frees the element it replaces.
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
