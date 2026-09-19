# `encoding` — base64 and percent encoding

Base64 (RFC 4648 standard alphabet, `=` padding) and percent-encoding
(RFC 3986 unreserved set) over `str`/`Bytes`.

No capability.

```toml
[dependencies]
encoding = "Juniper/fpl/encoding"
```

```kelp
impl "deps/encoding/lib" as encoding
```

```kelp
enum DecodeErr {
    Invalid
}
```

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

## Percent encoding

| Function | Returns |
| --- | --- |
| `percent_encode(text: &str)` | `String`, every byte outside the unreserved set as `%XX`, uppercase hex |
| `percent_decode(text: &str)` | `result.Result<String, DecodeErr>` |
| `is_unreserved(c: u8)` | `bool` — letters, digits, `-`, `.`, `_`, `~` |
| `hex_upper(nibble: u8)` | the uppercase hex character for a nibble |
| `hex_value(c: u8)` | `option.Option<u8>` for a hex digit |

`percent_encode` works on bytes, so a UTF-8 multi-byte character comes out as
one `%XX` per byte — which is what a URL wants.

`percent_decode` is URL percent-decoding, not
`application/x-www-form-urlencoded`: **`+` is left alone**. It fails on a
trailing `%` or a `%` not followed by two hex digits.

## Example

```kelp
impl "deps/encoding/lib" as encoding
impl "std/result"

fun main() {
    val data = Bytes.from_str("hello, kelp")
    val enc = encoding.base64_encode(&data)
    print(enc)
    val dec = encoding.base64_decode(enc.as_str())
    if let Ok(b) = dec {
        print(b.as_str())
    }
    print(encoding.percent_encode("a b/c?d=e&f"))
    val pdec = encoding.percent_decode("a%20b%2Fc")
    if let Ok(s) = pdec {
        print(s)
    }
    val bad = encoding.percent_decode("%zz")
    print(result.is_err(bad))
}
```

Output:

```
aGVsbG8sIGtlbHA=
hello, kelp
a%20b%2Fc%3Fd%3De%26f
a b/c
true
```

## Limits

- Standard base64 alphabet only: no URL-safe (`-`/`_`) variant, no unpadded
  variant, no whitespace tolerance.
- `percent_encode` never leaves a space as `+`; a space becomes `%20`.
- Decoding produces a `String` by pushing raw bytes, and `String.push(u8)` does
  not validate UTF-8: `percent_decode("%FF")` succeeds and yields a `String`
  holding one non-UTF-8 byte (`len()` is 1), with no error. Decode only byte
  sequences you know are text, or check the bytes before treating the result as
  text.

## `httpx` carries its own copies

`httpx` needs a base64 encoder and a percent-encoder for query strings and Basic
Auth. A folder in `fpl` must stand alone (a consumer fetches only the folder it
named), so `httpx` has its own small private copies rather than depending on this
library. Both are private to `httpx`; program code should use `encoding`.
