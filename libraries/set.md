---
title: "`set` (`Set<T>` and `StrSet`)"
description: "A thin wrapper over the builtin Map<K, bool> - Set<T> for Copy keys (integers and bool), StrSet for String keys, with union, intersect and difference."
isPublished: true
tags: "library, collections"
---
A thin wrapper over the builtin `Map<K, bool>`: `Set<T>` for `Copy` keys
(integers and `bool`), `StrSet` for `String` keys, with union, intersect and
difference.

No capability.

```toml
[dependencies]
set = "Juniper/fpl/set"
```

```kelp
impl "deps/set/lib" as set
```

## Why two types

A `String`-keyed `Map` takes its key as a bare `str` in every method
(`insert`/`has`/`remove`: the map copies it in) while every other key type takes
it by value. That split is baked into the compiler's `Map` builtin (syntax.md
§12.2), so one generic `insert<T>(v: T)` cannot serve both: at `T = String` the
body would need `v.as_str()`, and at `T = i64` it must not have it. Hence
`Set<T>` for the other key types and `StrSet` as the `String` twin.

## `Set<T>`

```kelp
datac Set<T>(var entries: Map<T, bool>)
```

| Function | Returns |
| --- | --- |
| `new<T>()` | empty `Set<T>` |
| `insert(s: mut Set<T>, v: T)` | `Unit` |
| `has(s: &Set<T>, v: T)` | `bool` |
| `remove(s: mut Set<T>, v: T)` | `bool`: whether `v` was present |
| `len(s)` / `is_empty(s)` | `usize` / `bool` |
| `clear(s: mut Set<T>)` | `Unit` |
| `to_list(s: &Set<T>)` | `List<T>`, insertion order (the order `Map.keys()` gives) |
| `union(a, b)` | `Set<T>` |
| `intersect(a, b)` | `Set<T>` |
| `difference(a, b)` | `Set<T>` |

Instantiate with an explicit type argument when inference has nothing to go on:
`var s: Set<i32> = set.new()` works, as does `set.new<i32>()`.

## `StrSet`

```kelp
datac StrSet(var entries: Map<String, bool>)
```

| Function | Returns |
| --- | --- |
| `new_str()` | empty `StrSet` |
| `insert(s: mut StrSet, v: &str)` | `Unit`: takes the text borrowed and copies it in |
| `has(s: &StrSet, v: &str)` | `bool` |
| `remove(s: mut StrSet, v: &str)` | `bool` |
| `len(s)` / `is_empty(s)` / `clear(s)` | as above |
| `to_list(s: &StrSet)` | `List<String>`, insertion order |
| `union_str(a, b)` / `intersect_str(a, b)` / `difference_str(a, b)` | `StrSet` |

`to_list` gives owned `String`s, so compare with `str.eq(x.as_str(), name)`.

## Semantics

- Membership is the builtin `Map` key hash/equality: `bool` and integer keys, or
  `String` byte equality.
- Insertion order is preserved and is the order `to_list` yields.
- Inserting an existing member is a no-op (the value is always `true`).
- `union`/`intersect`/`difference` build a fresh set; the receiver's order is
  kept for the left operand, then `b`'s new elements are appended.
- There are no `Copy`/`Clone` helpers: copy with a `to_list`/`insert` loop.

## Example

```kelp
impl "deps/set/lib" as set

fun main() {
    var a: set.Set<i32> = set.new()
    a.insert(1)
    a.insert(2)
    a.insert(2)
    print(a.len())
    print(a.has(2))
    print(a.remove(1))
    print(a.len())

    var b: set.Set<i32> = set.new()
    b.insert(2)
    b.insert(3)
    val u = set.union(a, b)
    val i = set.intersect(a, b)
    val d = set.difference(b, a)
    print(u.len())
    print(i.len())
    print(d.len())
    val al = a.to_list()
    print(al.get(0))

    var names: set.StrSet = set.new_str()
    names.insert("ada")
    names.insert("bob")
    names.insert("ada")
    print(names.len())
    print(names.has("bob"))
    var names2: set.StrSet = set.new_str()
    names2.insert("bob")
    names2.insert("cyd")
    val su = set.union_str(names, names2)
    val si = set.intersect_str(names, names2)
    print(su.len())
    val sil = si.to_list()
    print(sil.get(0).as_str())
    val nl = names.to_list()
    print(nl.get(0).as_str())
}
```

Output:

```
2
true
true
1
2
1
1
2
2
true
3
bob
ada
```

## Notes

- A `float` cannot be a `Set` key: the compiler's `Map` key set is `String`,
  the integers and `bool`: `nan != nan` would make an inserted key unfindable.
- A `datac`, an enum or a container cannot be a key either: v1 has no equality
  for them.
- Calling a method on a returned temporary is refused
  (`set.union(a, b).len()`): bind the result to a `val` first.
