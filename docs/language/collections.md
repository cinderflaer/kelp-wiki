# Collections

Source section:
[`syntax.md` §12](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Three containers are compiler builtins: `List<T>`, `Map<K, V>` and `Box<T>`. They
are owned values with the same move and drop rules as everything else, and their
elements are stored **inline**, which is why they cannot nest directly.

## `List<T>`

```kelp
var xs: List<i32> = List.empty()      // element type from the annotation
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
| `List.empty()` | nothing | empty list; element type from the context |
| `List.of(x)` | one value | a list holding it |
| `len()` / `is_empty()` | shared | `usize` / `bool` |
| `get(i)` | shared, `usize` | the element, or a borrow of it |
| `set(i, v)` | exclusive | `Unit` |
| `push(v)` | exclusive | `Unit`; moves the element in |
| `pop()` | exclusive | the last element, moved out |
| `insert(i, v)` / `remove(i)` | exclusive | `Unit` / the removed element |
| `clear()` | exclusive | `Unit` |
| `sort()` | exclusive | `Unit`, for sortable elements |
| `reverse()` | exclusive | `Unit` |
| `contains(v)` | shared | `bool`, for comparable elements |
| `slice(from, to)` | shared | a copy of the range, for clonable elements |

`get` and `pop` move an owned element out and return a copy for a `Copy` element,
so `List<i32>.get(i)` is an `i32` while `List<String>.get(i)` is a `&String`.
Out-of-range indices and popping an empty list panic.

`f64` is **not** sortable (`nan` breaks the order), which is why
[`stats`](../libraries/stats.md) and [`benchkit`](../libraries/benchkit.md) carry
their own sorts.

### Restriction: no nested containers

The element type may be a scalar, `String`, `Bytes` or a `datac`. It may **not**
be a borrow, a `str`, `Unit`, a `List` or a `Map`. A nested container is wrapped
in a one-field `datac`:

```kelp
datac Row(val cells: List<String>)          // what csv uses for a row
val rows: List<Row> = List.empty()
```

`Box<T>` is the other way out, for a *recursive* type:

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
- **A key must be `String`, an integer, or `bool`.** The compiler generates the
  key's hash and equality from `K`, so the set is closed: a float is refused
  (`nan != nan` would make an inserted key unfindable) and a `datac`, container or
  borrow is refused (v1 has no equality for them).
- `Map<K, V>` is neither a list element nor a map value, so
  `Map<String, Map<i32>>` is impossible.
- A `String`-keyed map takes its key as a bare `str` in every method (the map
  copies it in), while other key types take the key by value. That split is why
  [`set`](../libraries/set.md) ships two types instead of one generic set.

| Method | Returns |
| --- | --- |
| `Map.new()` / `Map.empty()` | an empty map; key and value types from the binding |
| `len()` / `is_empty()` | `usize` / `bool` |
| `insert(key, v)` | `Unit`; stores `true`-style upsert |
| `get(key)` | the value, or a borrow of it; panics when absent |
| `get_or(key, fallback)` | the value or the fallback |
| `has(key)` | `bool` |
| `remove(key)` | the value, moved out; **panics** when the key is absent |
| `keys()` / `values()` | `List<String>` / `List<V>`, insertion order |
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

## Iterating

`for x in xs` walks a `List<T>` ([Control flow](control-flow.md)). `Map` has no
iterator: iterate `keys()` and look up, or iterate `values()` when the key is not
needed.

## See also

- [`std/list`](../stdlib/list.md) for `map`, `filter`, `each`, `find_index`,
  `any`, `all`
- [`listx`](../libraries/listx.md) for `fold`, `zip`, `chunks`, `sort_by`,
  `sum`/`min`/`max`, `unique`
- [`set`](../libraries/set.md) for `Set<T>` and `StrSet`
