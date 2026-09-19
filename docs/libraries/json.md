# `json`: JSON (RFC 8259) reader, writer and transformer

Parses text into an owned `Json` tree, reads it back through typed accessors,
queries it by key or by [JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901),
transforms it (clone, equals, merge, sort keys) and writes it compact, pretty or
canonical.

No capability. Nothing here touches a file, a socket or the clock.

```toml
[dependencies]
json = "Juniper/fpl/json"
```

```kelp
impl "deps/json/lib" as json
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

`Json` is owned and read-only in practice: v1 matches an enum payload through a
shared borrow, so a payload cannot be pushed to in place. A document is built
bottom-up: collect `List`s of children, then wrap them with `array` or
`object`. The constructors exist so a program never spells a variant name.

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
| `float(x: f64)` | `Json.Float` |
| `text(s: &str)` | `Json.Str`, copied |
| `string(s: move String)` | `Json.Str`, moving `s` in |
| `array(items: move List<Json>)` | `Json.Array`, moving the list in |
| `object(keys: move List<String>, values: move List<Json>)` | `Json.Object`. Panics if the two lengths differ |
| `from_strings(xs: &List<String>)` | array of strings (each element cloned) |
| `from_ints(xs: &List<i64>)` / `from_floats` / `from_bools` | array of that scalar |

## Predicates

`is_null(v)`, `is_bool(v)`, `is_int(v)`, `is_float(v)`, `is_number(v)` (int or
float), `is_str(v)`, `is_array(v)`, `is_object(v)`: all `(&Json) -> bool`.

`is_integral(v)`: true for every `Int`, and for a finite `Float` that is its
own truncation (`1.0`, `-2.0`; not `1.5`, `inf`, `nan`).

`kind(v)` returns the JSON word for the type as an owned `String`: `"null"`,
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
| `try_f64(v)` | `option.Option<f64>` (an `Int` widens) |
| `as_bool_or(v, fallback: bool)` | `bool` |
| `as_i64_or(v, fallback: i64)` | `i64` |
| `as_f64_or(v, fallback: f64)` | `f64` |
| `text_or(v, fallback: &str)` | `String` |

There is no `try_str`: `Option<T>` is only offered for a `Copy` payload, and a
payload cannot be moved out of an enum in v1. `text_or` returns an owned copy
and applies the fallback.

## Keyed lookup

| Function | Returns |
| --- | --- |
| `key_index(v, key: &str)` | position of `key` in an object, or `-1` |
| `has(v, key)` | `bool` |
| `find(v, key)` | `option.Option<usize>` |
| `get(v, key)` | `&Json`; panics `json.get: key not found` |
| `keys(v)` | `List<String>` of every key, document order; empty list for a non-object |
| `index(v)` | `Map<String, usize>`: key to position, for repeated lookups. First occurrence wins |

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
| `count_nodes(v)` | node count of the subtree, `v` included |
| `depth_of(v)` | 1 for a scalar, 2 for an array of scalars, ... |
| `count_of_kind(v, want: &str)` | how many nodes report that `kind` |
| `index_of_kind(v, want)` | index of the first array element of that `kind`, or `-1` |
| `filter_array_by_kind(v, want)` | new `Json.Array` of cloned elements of that kind; panics if `v` is not an array |
| `collect_strings(v)` | every string leaf, document order, copied out NUL-safe |

**Closure-shaped traversal is not available.** `each_value(v, f)` and
`filter_array(v, pred)` cannot be declared on kelpc 0.2.2: a closure parameter
that is a borrow of a module-declared type emits a C typedef naming a tag
declared later in the file, and `cc` rejects the program. A closure parameter of
a builtin type does compile. Until that is fixed, write the index loop yourself
and use the helpers above for the callback-free shapes.

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
as the same value. A non-finite float (`inf`, `nan`, unreachable from `parse`)
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
| `parse_many(text)` | `result.Result<List<Json>, ParseError>`: every value in the text, however separated (NDJSON, a stream). Empty text yields an empty list |
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
impl "deps/json/lib" as json

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

- No closure-based traversal (see above).
- No `try_str`; use `text_or`.
- `Json` cannot be pushed to in place. Build children first, then wrap.
- `write`/`write_pretty` never emit `NaN`/`Infinity`: a non-finite float is
  `null`.
- `sort_keys` keeps duplicate keys: the sort picks the smallest untaken key each
  step, so equal keys keep their relative order instead of collapsing.

## Compiler bug affecting this library's idioms

On kelpc 0.2.2 an owned local (`List`, `Map`, `String`, `Bytes`) declared inside
`if let` or `for` emits its drop where the name is not in scope, so
`if let Ok(v) = json.parse(text) { var xs: List<..> = .. }` fails to build.
Declare the local before the block, or call a helper that owns it. Full report,
repro and the generated C: [Known issues](../meta/known-issues.md) (BUG-1).
