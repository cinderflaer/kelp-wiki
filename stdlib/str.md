---
title: "`std/str`"
description: "Text - search, slice, split, join, case, format, parse. Ungated."
isPublished: true
tags: "stdlib, text"
---
Text: search, slice, split, join, case, format, parse. Ungated.

```kelp
impl "std/str"
```

`str.len` and `str.byte` are byte-oriented; `str.char_count`, `str.char_at` and
`str.decode_at` are the codepoint-oriented set.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `len(s: &str)` | `usize` | bytes, not characters (a `strlen`, so it costs the length of the string) |
| `is_empty(s: &str)` | `bool` | |
| `byte(s: &str, i: usize)` | `u8` | byte at `i`; out of range panics. The bounds check reads `i + 1` bytes, not the whole string |
| `ptr(s: &str)` | `Ptr<u8>` | the address of the first byte, which is the NUL-terminated text itself; reading through it needs `unsafe` |
| `byte_index(s: &str, i: usize)` | `usize` | the byte offset of character `i` |
| `char_count(s: &str)` | `usize` | codepoints |
| `char_at(s: &str, i: usize)` | `u32` | the codepoint at character index `i` |
| `decode_at(s: &str, at: usize)` | `u32` | the codepoint starting at byte offset `at` |
| `substring(s: &str, from: usize)` | `&str` | from a byte offset to the end: a borrow, no copy |
| `copy_range(s: &str, from: usize, to: usize)` | `String` | copies the byte range |
| `prefix(s: &str, n: usize)` | `String` | the first `n` bytes, copied |
| `index_of(s: &str, needle: &str)` | `option.Option<usize>` | byte offset, `None` when absent |
| `starts_with(s, prefix)` / `starts_with_at(s, needle, at)` | `bool` | |
| `ends_with(s, suffix)` | `bool` | |
| `contains(s, needle)` | `bool` | |
| `eq(a: &str, b: &str)` | `bool` | byte equality; `str` cannot use `==` |
| `less(a: &str, b: &str)` | `bool` | byte order: first differing byte decides, a prefix is less; `str` has no `<` |
| `trim(s)` / `trim_start(s)` / `trim_end(s)` | `String` / `&str` / `String` | whitespace is space, tab, LF, CR |
| `is_space(c: u8)` | `bool` | space, tab, LF, CR |
| `is_digit(c: u8)` | `bool` | ASCII `0`-`9` |
| `to_upper(s)` / `to_lower(s)` | `String` | every letter with a simple Unicode case mapping; the full mappings are not applied, so `ß` stays as it is |
| `slice(s: &str, from: usize, to: usize)` | `String` | the bytes `[from, to)`, copied. Panics when `to` is past the end, when `from` is past `to`, or when either end lies inside a codepoint |
| `repeat(s: &str, n: usize)` | `String` | |
| `replace(s: &str, from: &str, to: &str)` | `String` | every occurrence |
| `split(s: &str, sep: &str)` | `List<String>` | keeps empty pieces: `"a,"` splits to 2 |
| `join(parts: List<String>, sep: &str)` | `String` | takes the list by value |
| `concat(a: &str, b: &str)` | `String` | allocates |
| `copy_into(dst: mut Bytes, at: usize, src: &str)` | `usize` | raw copy into a buffer |
| `from_i64(n)` / `from_u64(n)` / `from_f64(x, decimals)` | `String` | |
| `parse_i64(s)` / `parse_u64(s)` / `parse_f64(s)` | `result.Result<T, ParseErr>` | |
| `parse_err(s: &str)` | `ParseErr` | the error a failed parse would carry |

```kelp
enum ParseErr {
    Empty      // the text had no digits at all
    Invalid    // digits then junk, or a bad shape
}
```

## Example

```kelp
impl "std/str"
impl "std/result"

fun main() {
    val s = "  kelp, language  "
    val t = str.trim(s)
    print(t)                          // kelp, language
    print(str.len(t.as_str()))        // 14
    print(str.contains(t.as_str(), "lang"))
    print(str.starts_with(t.as_str(), "kelp"))
    print(str.to_upper(t.as_str()))   // KELP, LANGUAGE

    val parts = str.split(t.as_str(), ", ")
    print(parts.len())                // 2
    print(parts.get(1).as_str())      // language

    print(str.concat("a", "b"))       // ab
    print(str.join(parts, "-"))       // kelp-language
    print(str.repeat("ab", 3))        // ababab

    val n = str.parse_i64("41")
    if let Ok(v) = n {
        print(v + 1)                  // 42
    }
    val bad = str.parse_i64("4x")
    print(result.is_err(bad))         // true

    print(str.from_i64(-7))           // -7
    print(str.from_f64(1.5, 2))       // 1.50
}
```

## Notes

- **Scanning a long string byte by byte: take a `View` (or `Bytes`) first.** A
  `str` carries no length, so `str.len` walks to the terminating NUL and
  `str.byte(s, i)` walks `i + 1` bytes; a `while` loop over a 13 MB `str` is
  quadratic and does not finish. `val v = s.view()` pays one `strlen` (none from
  an owned `String`), and `v.len()` and `v.get(i)` are then constant time: the
  same 13 MB scan takes about 15 ms. See [Text](/language/text#view-borrowed-text-with-a-length).
- Everything byte-oriented counts bytes: `str.len("é")` is 2. Use `char_count`
  when the answer must be characters.
- `to_upper`/`to_lower` apply the simple Unicode case mappings (`kelpc/std/str.kp`, the generated table). U+00DF (sharp s) stays as it is, and U+0130 lowercases to U+0069.
- `slice` checks that both ends fall on codepoint boundaries. `copy_range` and `prefix` are byte-offset helpers and do not check.
- `split` keeps empty pieces, so a trailing separator produces a trailing empty
  string. To count the lines of a text file, split on `"\n"` and do not count
  a final empty piece.
- `str` cannot be compared with `==` (it is a pointer), so `str.eq` is the
  comparison and `str.less` is the ordering, for the same reason. `less`
  compares bytes, not codepoints, which is the same answer `List<u8>.sort` gives
  and the one a caller's sort depends on; write an explicit codepoint comparison
  if that is what you meant.
- `str.is_digit` pairs with `str.is_space` for hand-written number parsers.
- A `String` argument needs `.as_str()`: the module takes views, not owners.

## See also

- [`std/fmt`](/stdlib/fmt) for width-aware formatting
- [Text](/language/text) for `str`, `View`, `String`, `Bytes`
