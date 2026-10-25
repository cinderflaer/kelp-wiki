---
title: "`url`: URI parsing, building and resolution"
description: "RFC 3986, the whole component model - scheme, authority, path, query and fragment. parse reads a reference, to_string writes one back byte for byte, and resolve implements the section 5.3 relative-reference algorithm."
isPublished: true
tags: "library, text"
---
RFC 3986, the whole component model: scheme, authority (userinfo, host, port),
path, query and fragment. `parse` reads a reference, `to_string` writes one back
byte for byte, and `resolve` implements the §5.3 algorithm that turns a relative
reference into an absolute URL against a base.

No capability.

```toml
[dependencies]
url = "Lilly/fpl/url"
```

```kelp
impl "deps/url/lib"
```

```kelp
datac Url(
    var scheme: String,
    var userinfo: String,
    var host: String,
    var port: i64,
    var authority: bool,
    var path: String,
    var query: String,
    var query_present: bool,
    var fragment: String,
    var fragment_present: bool
)

datac Pair(val name: String, val value: String)

enum ParseErr {
    BadPercent
    BadIpv6
    BadPort
}
```

## Parsing and writing

| Function | Returns | Notes |
| --- | --- | --- |
| `parse(text: &str)` | `result.Result<Url, ParseErr>` | a URI reference, absolute **or relative** |
| `to_string(u: &Url)` | `String` | the URL as text |
| `blank()` | `Url` | every field empty, `port = -1`, no delimiter present |

`parse` stores components **encoded**, exactly as they appeared: nothing is
decoded on the way in and nothing is re-encoded on the way out. So
`to_string(parse(s))` returns `s` unchanged for every input `parse` accepts.
Cases are preserved too: `HTTP://Example.COM` parses as written, and `normalize`
is the function that lowercases.

Two facts a `String` cannot carry are held as booleans, which is what makes the
round trip exact:

- `authority`: whether the `//` form was present, so `file:///a` and `file:/a`
  stay different.
- `query_present` / `fragment_present`: whether a `?` or `#` was there even when
  nothing followed it, so `http://h/p?` and `http://h/p` stay different.

`parse` fails on exactly three malformations:

- `BadPercent`: a `%` not followed by two hex digits;
- `BadIpv6`: an unbalanced `[` or `]` in the authority;
- `BadPort`: a port that is not all digits, or one too large for `i64`.

Everything else is accepted, deliberately. `parse` does not validate that a
scheme's syntax matches its authority, does not range-check a port
(`http://h:99999` parses), and passes non-ASCII bytes through. It also accepts
relative references, because `resolve` needs them.

## Reading a URL

| Function | Returns |
| --- | --- |
| `is_absolute(u: &Url)` | `bool`: a scheme is present |
| `has_authority(u: &Url)` | `bool` |
| `has_port(u: &Url)` | `bool` |
| `default_port(scheme: &str)` | `i64`: the scheme's default, or `-1` |
| `effective_port(u: &Url)` | `i64`: the written port, else the scheme's default, else `-1` |
| `host_and_port(u: &Url)` | `String`: `host`, with `:port` when one is written |
| `origin(u: &Url)` | `String`: `scheme://host[:port]`, RFC 6454, default port omitted |

`default_port` knows `http` (80), `https` (443), `ws`, `wss`, `ftp`, `ssh`,
`smtp`, `imap` and `gopher`, and compares the scheme **as written**.
`effective_port` lowercases first, so it answers for `HTTPS://h/` while
`default_port("HTTPS")` returns `-1`.

`origin` takes the scheme and host as given; it is written for an absolute URL.

## Normalizing and comparing

| Function | Returns |
| --- | --- |
| `normalize(u: &Url)` | `Url`: scheme and host lowercased, dot segments removed, a port equal to the scheme's default dropped |
| `normalize_path(path: &str)` | `String`: RFC 3986 §5.2.4 `remove_dot_segments` alone |
| `equivalent(a: &Url, b: &Url)` | `bool`: the two `normalize` forms, field by field |

Normalization is a separate, explicit step because it is **lossy**: it is the
comparison form, while `parse`/`to_string` are the faithful pair. `equivalent`
compares `userinfo` as well, since it changes what a request is authenticated as.

`normalize_path` follows RFC 3986 §5.2.4 and not `sh` or a filesystem's idea of
`..`:

| Input | Output |
| --- | --- |
| `/a/./b` | `/a/b` |
| `/a/../b` | `/b` |
| `/a/..` | `/` |
| `/a/../..` | `/` |
| `../../a` | `a` |
| `a/../` | `/` |
| `/a//b` | `/a//b` |
| `/a/b/` | `/a/b/` |

Two of those surprise people. A leading `..` is **dropped**, not kept, so
`../../a` normalizes to `a`; that is what the RFC's algorithm does. And `a/../`
normalizes to `/`, because the `/` that `"/../"` leaves behind is a real
separator. An empty segment is never removed: a URI path distinguishes `//`.

## Resolving a relative reference

| Function | Returns |
| --- | --- |
| `resolve(base: &Url, reference: &str)` | `result.Result<Url, ParseErr>` |

RFC 3986 §5.3. A reference with its own scheme replaces everything; an authority
replaces the authority and the path; an empty path keeps the base path and query;
a relative path is merged onto the base path and then normalized. The fragment
always comes from the reference. An empty reference returns the base with the
base's fragment dropped, which is what the RFC specifies.

```kelp
val base = url.parse("http://a.example.com/docs/index.html?p=1")
when base {
    Ok(b) -> {
        val next = url.resolve(b, "../api/v2?x=1")
        when next {
            Ok(u) -> print(url.to_string(u))     // http://a.example.com/api/v2?x=1
            Err(_) -> print("bad reference")
        }
    }
    Err(_) -> print("bad base")
}
```

## Components and query strings

| Function | Returns | Notes |
| --- | --- | --- |
| `path_segments(u: &Url)` | `List<String>` | decoded; a leading `/` gives an empty first segment |
| `query_pairs(u: &Url)` | `List<Pair>` | decoded, in order; an empty part between two `&`s is skipped |
| `query_get(u: &Url, name: &str)` | `option.Option<String>` | the first pair with that name |
| `query_get_or(u: &Url, name: &str, fallback: &str)` | `String` | the accessor to use when a key is optional |
| `query_from_pairs(pairs: &List<Pair>)` | `String` | `a=b&c=d`, both sides `encode_component`, list order kept |
| `encode_component(text: &str)` | `String` | everything but the unreserved set escaped |
| `encode_path(text: &str)` | `String` | a whole path: `/`, the sub-delimiters, `:` and `@` stay literal |
| `decode_component(text: &str)` | `result.Result<String, ParseErr>` | `%XX` undone; **`+` is data, not a space** |

`query_get` returns an owned `option.Option<String>`, and `option.unwrap` takes
its receiver with `move`, so `option.unwrap(o = query_get(u = u, name = "k"))`
compiles and hands the owned `String` out. `query_get_or` is the one-call
accessor for a fallback that does not panic.

`query_pairs` splits on `&`, then on the first `=`; a part with no `=` is a name
with an empty value. **`+` is not a space** here, because that is
`application/x-www-form-urlencoded` and not a URI. Run
[`encoding.form_decode`](/libraries/encoding) on each half if the query came from an
HTML form.

The sub-delimiters RFC 3986 §2.2 allows in a path include `!$&'()*+,;=`, so
`encode_path("/a&b")` leaves the `&` alone; `encode_component` escapes it.

## Example

```kelp project
impl "deps/url/lib"
impl "std/str"

fun main() {
    val parsed = url.parse("https://user:pw@example.com:8443/a/b%20c?x=1&y=%2F#frag")
    when parsed {
        Ok(u) -> {
            print(url.to_string(u))
            print(u.host.as_str())
            print(url.effective_port(u))
            val segments = url.path_segments(u)
            print(segments.get(2).as_str())
            print(url.query_get_or(u, "x", "none"))
            print(url.origin(u))
        }
        Err(e) -> print("bad url")
    }
    print(url.encode_path("/a b/c?d"))
    val decoded = url.decode_component("a%20b")
    when decoded {
        Ok(s) -> print(s)
        Err(e) -> print("bad escape")
    }
}
```

Output:

```
https://user:pw@example.com:8443/a/b%20c?x=1&y=%2F#frag
example.com
8443
b c
1
https://example.com:8443
/a%20b/c%3Fd
a b
```

## Building a URL

`Url`'s fields are `var`, so a URL is built by assignment from `blank()` rather
than through a ten-argument constructor. `authority`, `query_present` and
`fragment_present` have to be set as well, or `to_string` will leave the `//`,
`?` or `#` out.

```kelp
var u = url.blank()
u.scheme = "https"
u.authority = true
u.host = "example.com"
u.port = 8443
u.path = "/api"
u.query_present = true
u.query = "q=1"
print(url.to_string(u))     // https://example.com:8443/api?q=1
```

## Notes

- **An empty port reads as absent.** `http://h:/p` parses to a URL with no port,
  so that one input does not round-trip. RFC 3986's grammar allows the bare
  colon; nothing here keeps the distinction.
- **No scheme-specific handling.** Nothing is done with `data:`, `mailto:` or
  `urn:` beyond the generic component split.
- **No IDNA, no punycode, no case folding beyond `to_lower`.** A host with a
  non-ASCII name is passed through as written, and `normalize` lowercases it with
  `str.to_lower`, which is ASCII-only.
- **A decoded component may not be UTF-8.** `decode_component("%FF")` succeeds
  and yields a `String` holding one non-UTF-8 byte, the same caveat
  [`encoding`](/libraries/encoding) documents. Decode only byte sequences you know
  are text.
- **`normalize` does not decode.** `%2E` is not a dot segment, so
  `/a/%2E%2E/b` normalizes to itself.
- **No `+`-as-space.** That is the `application/x-www-form-urlencoded` form,
  which lives in [`encoding`](/libraries/encoding) as
  `form_encode`/`form_decode`.
- **Default ports are scheme-specific.** An unknown scheme has no default, so
  `effective_port` returns `-1` and `origin` keeps whatever port was written.
- **Everything else in the module is internal.** The predicates and scanners the
  functions above are written with (`eff_starts`, `strip_last_segment`,
  `find_byte` and the rest) carry no `pub`, and another module reaches a library
  item only when the library declares it `pub` (A-13), so these are not callable
  from outside the library, and program code should not call them anyway.
- **It carries its own percent codec.** A folder in `fpl` must stand alone, so
  this is not a dependency on [`encoding`](/libraries/encoding). Program code that
  wants plain percent coding should use `encoding`.
