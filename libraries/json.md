---
title: "`json`: JSON (RFC 8259) reader, writer and transformer"
description: "Parses text into an owned Json tree, reads it back through typed accessors, queries it by key or by JSON Pointer, transforms it (clone, equals, merge, sort keys) and writes it compact, pretty or..."
isPublished: true
tags: "library, data-formats"
---
Parses text into an owned `Json` tree, reads it back through typed accessors —
including keyed ones that take a default, for a field that may be absent —
queries it by key or by
[JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901),
transforms it (clone, equals, merge, sort keys) and writes it compact, pretty or
canonical.

No capability. Nothing here touches a file, a socket or the clock.

```toml
[dependencies]
json = "Juniper/fpl/json"
```

```kelp
impl "deps/json/lib"
```

## The tree

```kelp
enum Json {
    Null
    Bool(val value: bool)
    Int(val value: i64)
    Float(val value: f64)
    Str(val value: String)
    Array(val items: List<Json>)
    Object(val keys: List<String>, val values: List<Json>)
}
```

`Json` is owned and read-only in practice: a match over an owned `Json` takes the
payload out of the enum into a binding, so a payload cannot be pushed to in
place. A document is built bottom-up: collect `List`s of children, then wrap them
with `array` or `object`. The constructors exist so a program never spells a
variant name.

`Object` is a pair of parallel lists, so key order is document order and
duplicate keys are preserved by the parser (`get` finds the first).

### Numbers

| Token | Becomes |
| --- | --- |
| `42`, `-7` | `Int(i64)` |
| anything with a `.` or an `e`/`E` | `Float(f64)` |
| an integer too large for `i64` | `Float(f64)` |

`as_f64` widens an `Int` exactly. `equals` compares two numbers by value, so
`Int(1)` equals `Float(1.0)`.

A `u64` above `i64` max has no number to ride in: the writer emits `i64` and a
float would lose the low bits. `uint(n)` writes such a value as its decimal
string instead, and `try_uint`/`get_uint` read either spelling back, so a hash
or a byte count survives a round trip exactly.

## Dependency

```kelp
impl "std/str"
impl "std/fmt"
impl "std/math"
impl "std/option"
impl "std/result"
```

## Constructors

| Function | Result |
| --- | --- |
| `null()` | `Json.Null` |
| `boolean(b: bool)` | `Json.Bool` |
| `int(n: i64)` | `Json.Int` |
| `uint(n: u64)` | `Json.Int` when it fits an `i64`, otherwise `Json.Str` with the decimal text |
| `float(x: f64)` | `Json.Float` |
| `text(s: &str)` | `Json.Str`, copied |
| `string(s: move String)` | `Json.Str`, moving `s` in |
| `array(items: move List<Json>)` | `Json.Array`, moving the list in |
| `object(keys: move List<String>, values: move List<Json>)` | `Json.Object`. Panics if the two lengths differ |
| `from_strings(xs: &List<String>)` | array of strings (each element cloned) |
| `from_ints(xs: &List<i64>)` / `from_floats` / `from_bools` | array of that scalar |

## Predicates

`is_null(v)`, `is_bool(v)`, `is_int(v)`, `is_float(v)`, `is_number(v)` (int or
float), `is_str(v)`, `is_array(v)`, `is_object(v)` — all `(&Json) -> bool`.

`is_integral(v)` — true for every `Int`, and for a finite `Float` that is its
own truncation (`1.0`, `-2.0`; not `1.5`, `inf`, `nan`).

`kind(v)` — the JSON word for the type, as an owned `String`: `"null"`,
`"boolean"`, `"number"`, `"string"`, `"array"`, `"object"`.

## Readers

Each reader **panics** when the value is the wrong type. Check with `is_*`
first, use a `try_*`/`_or` form, or use `find`/`key_index`, which never panic.

| Function | Returns | Panic message on the wrong type |
| --- | --- | --- |
| `as_bool(v)` | `bool` | `json.as_bool: value is not a boolean` |
| `as_i64(v)` | `i64` | `json.as_i64: value is not an integer` |
| `as_f64(v)` | `f64` (widens `Int`) | `json.as_f64: value is not a number` |
| `as_str(v)` | `&str` (NUL-terminated view) | `json.as_str: value is not a string` |
| `as_string(v)` | `&String` | `json.as_string: value is not a string` |
| `as_array(v)` | `&List<Json>` | `json.as_array: value is not an array` |
| `array_len(v)` | `usize` | `json.array_len: value is not an array` |
| `array_get(v, i)` | `&Json` | `json.array_get: value is not an array` |
| `object_len(v)` | `usize` | `json.object_len: value is not an object` |
| `object_key(v, i)` | `&str` | `json.object_key: value is not an object` |
| `object_key_string(v, i)` | `&String` | `json.object_key_string: value is not an object` |
| `object_value(v, i)` | `&Json` | `json.object_value: value is not an object` |

Use `as_string` (not `as_str`) for text that may hold a `\u0000`: a `str` stops
at the first NUL, a `String` carries its own length.

### Safe readers

| Function | Returns |
| --- | --- |
| `try_bool(v)` | `option.Option<bool>` |
| `try_i64(v)` | `option.Option<i64>` |
| `try_uint(v)` | `option.Option<u64>`: an `Int` that is not negative, or a decimal string |
| `try_f64(v)` | `option.Option<f64>` (an `Int` widens) |
| `as_bool_or(v, fallback: bool)` | `bool` |
| `as_i64_or(v, fallback: i64)` | `i64` |
| `as_uint_or(v, fallback: u64)` | `u64` |
| `as_f64_or(v, fallback: f64)` | `f64` |
| `text_or(v, fallback: &str)` | `String` |

There is no `try_str`: the `try_*` readers take `&Json`, a borrow, and an owned
payload cannot be moved out of a borrow, so only a `Copy` payload can come back
inside an `Option`. `text_or` returns an owned copy and applies the fallback.

## Keyed lookup

| Function | Returns |
| --- | --- |
| `key_index(v, key: &str)` | position of `key` in an object, or `-1` |
| `has(v, key)` | `bool` |
| `find(v, key)` | `option.Option<usize>` |
| `get(v, key)` | `&Json`; panics `json.get: key not found` |
| `keys(v)` | `List<String>` of every key, document order; empty list for a non-object |
| `index(v)` | `Map<String, usize>` — key to position, for repeated lookups. First occurrence wins |

### Keyed lookup with a default

`get` panics on an absent key and the safe readers above take a *value* rather
than a key, so "this field, or a default" had no direct spelling: a caller wrote
`if json.has(doc, key) { ... json.get(doc, key) ... }` by hand, and the
natural-looking `json.text_or(v = json.get(doc, "body"), fallback = "")` panics on
the record that leaves the field out: which is exactly the record a default
exists for.

| Function | Returns |
| --- | --- |
| `get_text(v, key, fallback: &str)` | `String`: the field, or the fallback when it is absent or not a string |
| `get_int(v, key, fallback: i64)` | `i64`: likewise, and likewise for a number |
| `get_float(v, key, fallback: f64)` | `f64`; an `Int` widens, as `as_f64_or` does |
| `get_bool(v, key, fallback: bool)` | `bool` |
| `get_uint(v, key, fallback: u64)` | `u64`: an `Int` that is not negative, or the decimal string `uint` writes above `i64` max |
| `get_strings(v, key)` | `List<String>`: an array of strings as an owned list |

Each is a presence check followed by the matching value-level accessor, so they
agree with `text_or`/`as_i64_or`/`as_f64_or`/`as_bool_or` by construction, and each
answers the fallback for a **wrongly typed** field as well as for an absent one: a
`body` that is a number reads as the default instead of panicking.

`get_strings` skips a non-string element rather than turning it into an empty
string, so `["bug", 7, "ui"]` reads as two labels and not three: a caller that
gets two cannot mistake the hole for a value, while a caller that got `""` would
store a label nobody typed. An absent key, a `null` and a non-array all read as
an empty list.

```kelp
// A record with a required field and three optional ones, read the way a codec
// reads one: the required field goes through `get` (and panics when it is not
// there), the optional ones through the keyed accessors.
val parsed = json.parse("{\"id\":7,\"title\":\"a ticket\",\"tags\":[\"bug\",7,\"ui\"]}")
if let Ok(doc) = parsed {
    print(json.get_int(doc, "id", 0))            // 7
    print(json.as_i64(json.get(doc, "id")))       // 7 — the panicking form
    print(json.get_text(doc, "body", ""))        // "" — the field is absent
    print(json.get_text(doc, "title", ""))       // "a ticket"
    val tags = json.get_strings(doc, "tags")      // ["bug", "ui"]
    print(tags.len())                            // 2
    print(json.get_bool(doc, "closed", false))   // false
}
```

## JSON Pointer

A pointer is `/`-separated; `~1` is `/`, `~0` is `~`; an array segment is a
decimal index; the empty pointer names the whole document.

| Function | Returns |
| --- | --- |
| `has_ptr(v, ptr: &str)` | `bool`, the non-panicking half of `at` |
| `at(v, ptr)` | `&Json`; panics with the pointer in the message when it does not resolve |
| `ptr_segments(ptr)` | `List<String>` of decoded segments |
| `decode_pointer(raw)` | one segment decoded (`~1` -> `/`, `~0` -> `~`) |
| `is_pointer_index(s)` | `bool`: is `s` a pointer-legal array index (`0`, or no leading zero) |

## Owned transformations

| Function | Does |
| --- | --- |
| `clone(v)` | deep copy; clones by length, so an embedded `\u0000` survives |
| `equals(a, b)` | deep equality; numbers by value, objects by key set whatever the order, text byte for byte |
| `merge(a, b)` | shallow layer: `b`'s value wins on a shared key, `b`'s new keys are appended; a non-object on either side makes the result a clone of `b` |
| `sort_keys(v)` | recursive copy with every object's keys sorted byte-lexicographically |

### Bulk traversal

| Function | Returns |
| --- | --- |
| `each_value(v, f: closure(&Json))` | visits every node in document order, `v` included |
| `filter_array(v, pred: closure(&Json).return: bool)` | new `Json.Array` of cloned elements the predicate accepts; panics if `v` is not an array |
| `count_nodes(v)` | node count of the subtree, `v` included |
| `depth_of(v)` | 1 for a scalar, 2 for an array of scalars, ... |
| `count_of_kind(v, want: &str)` | how many nodes report that `kind` |
| `index_of_kind(v, want)` | index of the first array element of that `kind`, or `-1` |
| `filter_array_by_kind(v, want)` | new `Json.Array` of cloned elements of that kind; panics if `v` is not an array |
| `collect_strings(v)` | every string leaf, document order, copied out NUL-safe |

The two callback-shaped helpers take a closure that borrows `Json`, which is
legal since `kelpc 0.1.5` fixed the C typedef a module-declared borrow in a
closure parameter emits. `each_value` is for looking at every node;
`filter_array` is the predicate form of `filter_array_by_kind`:

```kelp
val ints = json.filter_array(json.get(doc, "items"),
    fun(x: &json.Json).return: bool = json.is_int(x))
json.each_value(doc, fun(x: &json.Json) = print(json.kind(x)))
```

## Writing

| Function | Output |
| --- | --- |
| `write(v)` | compact: no space outside a string |
| `write_pretty(v)` | two spaces per level, one entry per line |
| `write_pretty_with(v, indent: usize)` | the same, chosen width |
| `write_sorted(v)` | canonical compact text: keys sorted first |
| `write_sorted_pretty(v)` | canonical and indented |
| `quote(s: &str)` | the JSON string literal for `s`, escapes included |

Number formatting is exposed too: `format_float(x: f64) -> String` (the shortest
spelling that reads back as the same double) and `to_scientific(x) -> Scientific(m, e)`
with `m` in `[1, 10)`, over the `Scientific(val m: f64, val e: i32)` datac. The
inner writers `write_into`, `pretty_into` and `write_string(s: View, out: mut String)`
append to an existing `String` instead of returning one.

Pointer helpers beyond `has_ptr`/`at`/`ptr_segments`: `is_pointer_index(s)`,
`decode_pointer(raw)`, `index_value(s) -> i64` (a segment as a number, `-1` on
overflow) and `segment_end`/`segment_end_at`.

Numbers round-trip: `write` picks the shortest spelling that `parse` reads back
as the same value. A non-finite float (`inf`, `nan` — unreachable from `parse`)
is written as `null`. `-0.0` is written `-0.0`. A float is always given a
fraction or an exponent, so `1.0` never reads back as the integer `1`.

## Parsing and parse errors

```kelp
datac ParseError(val message: String, val offset: usize)
```

| Function | Returns |
| --- | --- |
| `parse(text: &str)` | `result.Result<Json, ParseError>`; trailing whitespace allowed, anything else after the value is an error |
| `parse_ok(text)` | `bool` |
| `parse_many(text)` | `result.Result<List<Json>, ParseError>` — every value in the text, however separated (NDJSON, a stream). Empty text yields an empty list |
| `line_of(e, text)` | 1-based line the offset falls on |
| `column_of(e, text)` | 1-based byte column within that line |
| `describe(e, text)` | one line: `line 1 column 6 (byte 5): unexpected end of input` |

`line_of`/`column_of`/`describe` clamp an offset past the end of `text` to the
end, so a caller that hands them a different buffer cannot read out of bounds.

Limits and rules:

- Nesting deeper than `MAX_DEPTH` (128) is refused with an `Err`, not a stack
  overflow.
- A bare control character inside a string is an error; `\uXXXX` is decoded,
  including surrogate pairs, and re-encoded as UTF-8.
- An invalid `~` escape in a pointer is kept literally rather than refused.

## Example

```kelp
impl "deps/json/lib"

fun main() {
    val parsed = json.parse("{\"name\":\"kelp\",\"tags\":[\"lang\",\"caps\"],\"stars\":42}")
    if let Ok(doc) = parsed {
        print(json.write(doc))
        print(json.write_pretty(doc))
        print(json.text_or(v = json.get(doc, "name"), fallback = "?"))
        print(json.as_i64(json.get(doc, "stars")))
        print(json.array_len(json.get(doc, "tags")))
        print(json.has_ptr(doc, "/tags/1"))
        print(json.as_str(json.at(doc, "/tags/1")))
        print(json.kind(doc))
        print(json.count_nodes(doc))
        print(json.depth_of(doc))
        print(json.count_of_kind(doc, "string"))
    }

    val bad = json.parse("{\"a\":")
    if let Err(e) = bad {
        print(json.describe(e, "{\"a\":"))
    }

    var xs: List<i64> = List.empty()
    xs.push(3)
    xs.push(1)
    print(json.write(json.from_ints(xs)))

    var keys: List<String> = List.empty()
    keys.push("b")
    keys.push("a")
    var vals: List<json.Json> = List.empty()
    vals.push(json.int(2))
    vals.push(json.int(1))
    val obj = json.object(keys, vals)
    print(json.write_sorted(obj))
    print(json.write(json.merge(obj, obj)))
    print(json.equals(json.int(1), json.float(1.0)))
    print(json.quote("a\"b\nc"))
    print(json.is_integral(json.float(2.0)))
}
```

Output:

```
{"name":"kelp","tags":["lang","caps"],"stars":42}
{
  "name": "kelp",
  "tags": [
    "lang",
    "caps"
  ],
  "stars": 42
}
kelp
42
2
true
caps
object
6
3
3
line 1 column 6 (byte 5): unexpected end of input
[3,1]
{"a":1,"b":2}
{"b":2,"a":1}
true
"a\"b\nc"
true
```

## Limits

- No `try_str`; use `text_or`, or `get_text` when the field may be absent.
- `Json` cannot be pushed to in place. Build children first, then wrap.
- `write`/`write_pretty` never emit `NaN`/`Infinity`: a non-finite float is
  `null`.
- `sort_keys` keeps duplicate keys: the sort picks the smallest untaken key each
  step, so equal keys keep their relative order instead of collapsing.
