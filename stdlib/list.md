---
title: "`std/list`"
description: "Closure-shaped helpers over List<T>. Ungated."
isPublished: true
tags: "stdlib, collections"
---
Closure-shaped helpers over `List<T>`. Ungated.

```kelp
impl "std/list"
```

| Function | Returns | Notes |
| --- | --- | --- |
| `map<T, U>(xs, f: closure(&T) => U)` | `List<U>` | one new element per element |
| `filter<T>(xs, f: closure(&T) => bool)` | `List<T>` | **`T` must be `Copy`** |
| `each<T>(xs, f: closure(&T))` | `Unit` | for the side effect |
| `find_index<T>(xs, f: closure(&T) => bool)` | `option.Option<usize>` | the first match |
| `any<T>(xs, f: closure(&T) => bool)` | `bool` | |
| `all<T>(xs, f: closure(&T) => bool)` | `bool` | |

These are free functions rather than `List` methods because methods on a builtin
are compiler-generated, and a generic closure method is not something the builtin
set carries.

```kelp
impl "std/list"
impl "std/str"

fun main() {
    var xs: List<i64> = List.empty()
    xs.push(1)
    xs.push(2)
    xs.push(3)

    val doubled = list.map(xs, fun(x: &i64) => i64 = x * 2)
    print(doubled.len())                    // 3
    print(doubled.get(1))                   // 4

    val big = list.filter(xs, fun(x: &i64) => bool = x > 1)
    print(big.len())                        // 2

    val at = list.find_index(xs, fun(x: &i64) => bool = x == 3)
    if let Some(i) = at {
        print(i)                            // 2
    }

    print(list.any(xs, fun(x: &i64) => bool = x == 2))   // true
    print(list.all(xs, fun(x: &i64) => bool = x > 0))    // true

    list.each(xs, fun(x: &i64) = print(x))
}
```

## Notes

- The literal is written `fun(x: &T) => U = <expr>`, and inside it a `Copy`
  element is used **directly**: `x * 2`, not `*x * 2`.
- `filter` requires `Copy` (it builds a new list out of what `get` hands back),
  so `List<String>` cannot be filtered here. `listx` documents the same limit;
  clone in the callback if you need owned results.
- `map` needs no `Copy`: it hands the borrow to the callback and stores whatever
  the callback returns.
- There is no `fold`, `zip`, `chunks`, `sort_by`, `sum`/`min`/`max`, `unique` or
  `position`: those are in [`listx`](/libraries/listx).

## See also

- [`listx`](/libraries/listx)
- [Collections](/language/collections)
- [Functions](/language/functions) for closure and capture rules
