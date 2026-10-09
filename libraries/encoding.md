---
title: "`encoding`: base64, base32, base58, hex and percent encoding"
description: "Base64 (RFC 4648 standard alphabet, = padding), base32 (RFC 4648 section 6), base58 (Bitcoin alphabet), lowercase hex, percent-encoding (RFC 3986 unreserved set), a hexdump -C-shaped renderer and the application/x-www-form-urlencoded form."
isPublished: true
tags: "library, text"
---
Base64 (RFC 4648 standard alphabet, `=` padding), base32 (RFC 4648 §6 alphabet,
`=` padded), base58 (the Bitcoin alphabet), lowercase hex over a whole buffer,
and percent-encoding (RFC 3986 unreserved set) over `str`/`Bytes`, plus a
`hexdump -C`-shaped renderer and the `application/x-www-form-urlencoded` form.

No capability.

```toml
[dependencies]
encoding = "Lilly/fpl/encoding"
```

```kelp
impl "deps/encoding/lib"
```

> **`std/encoding` ships now.** The same codecs are part of the standard
> library from the current development cycle on, so a program on a current
> `kelpc` imports [`std/encoding`](/stdlib/encoding) instead of this folder. This
> library stays for a project pinned to an older compiler, and it is the version
> that works as a fetched dependency.

```kelp
enum DecodeErr {
    Invalid
}
```

Every decoder in the module returns `result.Result<T, DecodeErr>`, and `Invalid`
is the only error. None of them panic.

## Base64

| Function | Returns |
| --- | --- |
| `base64_encode(data: &Bytes)` | `String`, standard alphabet, padded |
| `base64_decode(text: &str)` | `result.Result<Bytes, DecodeErr>` |
| `b64_char(v: u8)` | the character for a 6-bit value |
| `b64_value(c: u8)` | `option.Option<u8>` for a character, `None` for `=` and anything outside the alphabet |

`base64_decode` fails (`Err(Invalid)`) on:

- a length that is not a multiple of 4,
- a character outside the alphabet,
- `=` anywhere but the last one or two positions.

Empty input decodes to empty `Bytes`. Whitespace is **not** skipped: trim or
strip line breaks yourself first.

## Base32

| Function | Returns |
| --- | --- |
| `base32_encode(data: &Bytes)` | `String`, `A`-`Z` then `2`-`7`, padded to a multiple of 8 |
| `base32_decode(text: &str)` | `result.Result<Bytes, DecodeErr>` |
| `b32_char(v: u8)` | the character for a 5-bit value |
| `b32_value(c: u8)` | `option.Option<u8>`, `None` for `=` and anything outside the alphabet |

This is the alphabet TOTP secrets and magnet URIs use. Lowercase is refused
rather than folded, because the RFC's reference encoder emits uppercase.

`base32_decode` fails (`Err(Invalid)`) on a length that is not a multiple of 8, a
character outside the alphabet, `=` before the final group, an all-padding input,
and a final group whose leftover bits are not zero. The valid final-group lengths
are the RFC's four: 2, 4, 5 and 7 characters of data.

## Base58

| Function | Returns |
| --- | --- |
| `base58_encode(data: &Bytes)` | `String`, no padding |
| `base58_decode(text: &str)` | `result.Result<Bytes, DecodeErr>` |
| `b58_char(v: u8)` | the character for a base-58 digit |
| `b58_value(c: u8)` | `option.Option<u8>`, `None` for `0`, `O`, `I`, `l` and anything else outside the alphabet |

The alphabet drops `0`, `O`, `I` and `l`, so a transcribed value cannot be read
two ways. A leading zero byte becomes a leading `1`, as the usual
implementations do: `base58_encode` of `[0, 0, 1, 2]` is `"115T"`, and
`base58_decode("1")` is one zero byte. An empty input is an empty `String` /
empty `Bytes`.

## Hex

| Function | Returns |
| --- | --- |
| `hex_encode(data: &Bytes)` | `String`, lowercase, two characters per byte |
| `hex_decode(text: &str)` | `result.Result<Bytes, DecodeErr>`, either case accepted |
| `hex_upper(nibble: u8)` | the uppercase hex character for a nibble |
| `hex_lower(nibble: u8)` | the lowercase hex character for a nibble |
| `hex_value(c: u8)` | `option.Option<u8>` for a hex digit, either case |

`std/fmt.hex` prints one `u64` with no leading zeros; this pair is the spelling
for a whole buffer. `hex_decode` fails on an odd length or a non-hex character;
no `0x` prefix and no separators are accepted.

## Hex dump

| Function | Returns |
| --- | --- |
| `dump(data: &Bytes)` | `String`, `hexdump -C` shaped |

An 8-digit offset, 16 bytes per line in two groups of eight, then the line's
bytes as printable ASCII (`.`) for anything outside `0x20`-`0x7e`. Lines are
separated by `\n` with **no** trailing newline, so `print(dump(b))` emits the
lines and nothing more. An empty buffer renders as the empty string.

## Percent encoding, URL form

| Function | Returns |
| --- | --- |
| `percent_encode(text: &str)` | `String`, every byte outside the unreserved set as `%XX`, uppercase hex |
| `percent_decode(text: &str)` | `result.Result<String, DecodeErr>` |
| `is_unreserved(c: u8)` | `bool`: letters, digits, `-`, `.`, `_`, `~` |

`percent_encode` works on bytes, so a UTF-8 multi-byte character comes out as
one `%XX` per byte, which is what a URL wants.

`percent_decode` is URL percent-decoding, not
`application/x-www-form-urlencoded`: **`+` is left alone**. It fails on a
trailing `%` or a `%` not followed by two hex digits.

## Percent encoding, form body

| Function | Returns |
| --- | --- |
| `form_encode(text: &str)` | `String`, space as `+`, everything else as `%XX` |
| `form_decode(text: &str)` | `result.Result<String, DecodeErr>`, `+` as space |

The `application/x-www-form-urlencoded` pair is separate from the URL pair on
purpose. `+` is a space in a form body and data in a URL path, so guessing which
one a caller meant is how a `%2B` turns into a space. Use `form_*` for a request
body or an HTML form, and `percent_*` for everything else. The [`url`](/libraries/url)
library's `query_pairs` leaves `+` alone for the same reason.

## Example

```kelp
impl "deps/encoding/lib"
impl "std/result"

fun main() {
    val data = Bytes.from_str("foobar")
    print(encoding.base32_encode(&data))
    val b32 = encoding.base32_decode("MZXW6YTBOI======")
    if let Ok(b) = b32 {
        print(encoding.hex_encode(b))
    }
    val word = Bytes.from_str("hello")
    print(encoding.base58_encode(&word))
    print(encoding.hex_encode(&data))
    print(encoding.form_encode("a b+c/d"))
    val form = encoding.form_decode("a+b%2Bc%2Fd")
    if let Ok(s) = form {
        print(s)
    }
    var counter = Bytes.empty()
    var i: u8 = 0
    while i < 20 {
        counter.push(i)
        i = i + 1
    }
    print(encoding.dump(&counter))
}
```

Output:

```
MZXW6YTBOI======
666f6f626172
Cn8eVZg
666f6f626172
a+b%2Bc%2Fd
a b+c/d
00000000  00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f  |................|
00000010  10 11 12 13                                       |....|
```

The two `dump` lines are `hexdump -C`'s, byte for byte, minus its closing
total-offset line.

## Limits

- Standard base64 alphabet only: no URL-safe (`-`/`_`) variant, no unpadded
  variant, no whitespace tolerance.
- Base32 is uppercase only, and `base64_decode`/`base32_decode` skip no
  whitespace. Both are strict, which is deliberate: leniency in a decoder is how
  two implementations disagree about the same input.
- `percent_encode` never leaves a space as `+`; a space becomes `%20`. The `+`
  form is `form_encode`.
- Decoding produces a `String` by pushing raw bytes, and `String.push(u8)` does
  not validate UTF-8: `percent_decode("%FF")` succeeds and yields a `String`
  holding one non-UTF-8 byte (`len()` is 1), with no error. Decode only byte
  sequences you know are text, or check the bytes before treating the result as
  text.
- `dump` is one fixed shape: no `-b`/`-o`/`-d` variants, no `*` run compression
  for repeated lines, and no configurable width.

## `httpx` carries its own copies

`httpx` needs a base64 encoder and a percent-encoder for query strings and Basic
Auth. A folder in `fpl` must stand alone (a consumer fetches only the folder it
named), so `httpx` has its own small private copies rather than depending on this
library. Both are private to `httpx`; program code should use `encoding`.

The [`url`](/libraries/url) library carries the same kind of copy for
percent-encoding, and exposes only the URL-shaped part (`encode_path`,
`encode_component`, `decode_component`). Nothing here calls across folders.
