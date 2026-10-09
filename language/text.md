---
title: "Text"
description: "Kelp's text types, str, View, String and Bytes: conversions, printing, building text, parsing numbers, and the traps to avoid."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §11](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md).

Kelp has four text types, and the difference between them is where the bytes live
and whether the length is known.

| Type | Kind | What it is |
| --- | --- | --- |
| `str` | borrowed | a NUL-terminated UTF-8 pointer. No length: deriving one costs a `strlen` |
| `View` | borrowed | a pointer **and** a length. Slices without allocating, scans without `strlen` |
| `String` | owned | UTF-8 text, validated on construction, freed at scope end |
| `Bytes` | owned | a raw byte buffer |

## The one implicit conversion

`str` and `View` convert to `String` **by copying**, and only at an exact `String`
expectation:

```kelp
datac Doc(val title: String, val body: String)

val d = Doc(title = "a title", body = "text")   // no String.from_str needed
var xs: List<String> = List.empty()
xs.push("pushed")                               // an element converts
val s: String = "a literal"                     // an assignment converts
var m: Map<String, String> = Map.new()
m.insert(key = "k", v = "v")                    // a key and a value convert
```

Nothing converts the other way. `String` → `str` is a borrow, written
`.as_str()`, and a `View` is **not** a `str` (a slice has no NUL after it), so a
view that must become text takes `v.to_string()`.

`str` parameters (`str.len`, `str.eq`, `fs.write_text`, `path.join`, …) keep
taking a borrowed view with no allocation.

## Printing

`print` and `print!` are builtins; no import is needed.

```kelp
print("done")            // the text and a newline
print!("loading")        // no newline
print(42)                // integers, decimal
print(1.5)               // floats, six decimals: 1.500000
print(true)              // bools
print(some_str)          // a str
print(owned_string)      // a String, read without being consumed
print(owned_bytes)       // a Bytes buffer
print("first\nsecond")    // one call, two lines
print("name\tvalue")     // tabs, too; see the escape set in Lexical structure
```

`print` takes exactly one positional argument and accepts scalars, `str`,
`String`, `Bytes`, `View` and a template. It does **not** accept a `datac`, a
`List`, a `Map`, a `Box`, an `Option` or a `Result`, and it takes no named
arguments. A template (`"$x"`) is the only way to print a mixture, and a template
is not a value.

A template interpolates **any** scalar or text value, owned or borrowed, so
`print("w = ${s}")` works with `s` a `String`, a `Bytes` or a `View` as well as
with a `str` or a number. An owned piece is freed once the line is printed; a
borrow and a `View` are not freed at all.

`std/io` adds `print_bare`, `eprint` and `eprint_bare` for control over the
newline and the stream, plus `File` writes. See
[`std/io`](/stdlib/io).

## Building text

```kelp
var out = String.empty()
out.push_str("wrote ")
out.push_str(size_text.as_str())
print(out)
```

| `String` | Notes |
| --- | --- |
| `String.empty()`, `String.with_capacity(n)`, `String.from_str(&str)`, `String.from_bytes(Bytes)` | constructors |
| `push(u8)`, `push_str(&str)`, `reserve(n)`, `clear()` | grow and shrink |
| `len()`, `char_count()`, `is_empty()` | size |
| `clone()` | a second owned copy |
| `into_bytes()` | hand the buffer over as `Bytes` |
| `as_str()` | borrow as `str` |

| `Bytes` | Notes |
| --- | --- |
| `Bytes.empty()`, `Bytes.from_str(&str)` | constructors |
| `push(u8)`, `append(&Bytes)`, `reserve(n)`, `clear()` | grow and shrink |
| `len()`, `is_empty()` | size |
| `get(i)`, `set(i, b)` | element access (out of range panics) |
| `clone()`, `as_str()` | copy; borrow as text |

Arbitrary bytes are **built, not written**: a string literal is NUL-terminated,
so a `Bytes` built from one (`Bytes.from_str`) cannot carry a NUL byte, because
the lexer refuses a raw NUL or `\x00` in the literal first. Binary data is
`Bytes.empty()` plus `push`.

Growing a buffer takes an exclusive borrow, so a live `str` view of it blocks the
growth. That rule is what makes reallocation safe without lifetime syntax.

Formatting a number: `fmt.int(n)`, `fmt.uint(n)`, `fmt.float(x, decimals)`,
`fmt.hex(n)`, `fmt.pad_left(s, width, fill)`, `fmt.pad_right(...)`. All return
`String`. See [`std/fmt`](/stdlib/fmt).

## `View`: borrowed text with a length

```kelp
val text = "the quick brown fox"
val v = text.view()             // one strlen, once

print(v.len())                  // 19
print(v.get(0))                 // 116, the byte for 't'; out of range panics
print(v.slice(4, 9))            // "quick": a view, nothing allocated
print(v.eq("quick".view()))     // byte-wise, length-aware

val owned: String = v.slice(4, 9)   // copies by length, not by strlen
```

| Call | Returns |
| --- | --- |
| `s.view()` | `View` over a `str` (one `strlen`) |
| `v.len()`, `v.is_empty()` | `usize`, `bool` |
| `v.get(i)` | `u8` |
| `v.slice(from, to)` | `View` |
| `v.eq(other: View)` | `bool`: compares bytes and lengths |
| `v.to_string()` | `String` |

A `str` has no stored length, so `str.len(s)` and `str.byte(s, i)` each read as
much of the string as they need to (all of it, and `i + 1` bytes). Indexing a
long `str` in a loop is quadratic; take `s.view()` once and scan the view, whose
`len` and `get` are constant time.

A `View` is `Copy`. A `List`, `Map` or `Box` cannot store a borrow. A `datac`
may store a `View` only when construction moves its String/Bytes owner into an
earlier field of the same value. Text you must keep independently is a `String`.

## Conversions and parsing

```kelp
val n: i32 = -7
print(n.to_i64())            // widening, exact
print(fmt.int(n.to_i64()))   // "-7" as a String

val parsed = str.parse_i64(s = "41")   // Result<i64, str.ParseErr>
if let Ok(v) = parsed {
    print(v + 1)
}

val big: i64 = 3
val x: f64 = big.to_f64()            // 3.0, the only integer-to-float widening
```

- `to_<T>()` exists on every integer type for every integer type, plus
  `to_f64()`/`to_f32()`. Widening is exact; narrowing panics when the value does
  not fit; a float has no `to_<int>`.
- `try_to_<T>()` is the fallible twin, for the pairs whose plain conversion can
  lose a value: it hands back `Option<T>`, so a caller tests rather than
  panicking. A widening has no `try_to_<T>` (see [Types](/language/types)).
- `str.from_i64`, `str.from_u64` and `str.from_f64(x, decimals)` return `String`.
- `str.parse_i64`, `str.parse_u64`, `str.parse_f64` return
  `Result<T, str.ParseErr>`. `ParseErr` has two variants, `Empty` (the text was
  empty) and `Invalid` (the text is not a number).

## Two traps

- **A direct text-view binding promotes its temporary owner.**
  `val text = String.from_str("x").as_str()` and `val name =
  mkName().name.as_str()` remain valid for the binding's scope. A borrow that
  escapes its frame, including a returned borrow, still needs an owner supplied
  by the caller.
- **A `String` argument where a `str` parameter is expected** needs
  `.as_str()`: the error message names the argument.

## See also

- [`std/str`](/stdlib/str)
- [`std/fmt`](/stdlib/fmt)
- [`std/io`](/stdlib/io)
- [Pitfalls](/language/pitfalls)
