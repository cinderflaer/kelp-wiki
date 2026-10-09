---
title: "`httpx`: HTTP helpers over `std/http`"
description: "The pieces std/http's client deliberately leaves out - a query-string builder, a Basic-Auth header, the method helpers past GET/POST, and a minimal Set-Cookie reader."
isPublished: true
tags: "library, networking"
---
The pieces `std/http`'s client deliberately leaves out: a query-string builder, a
Basic-Auth header, the method helpers past `GET`/`POST`, and a minimal
`Set-Cookie` reader.

**No `net` grant of its own.** This library only builds and reads plain data
(`Request`, `Response`, `String`) and never calls a net-touching function, but
merely *importing* `std/http` requires delegating it a `net` grant (the module
holds `net` as a whole, not per function), so this library declares
`impl "std/http" caps(net = [])`: the smallest grant that satisfies the
compiler without asking the consumer for anything. The consumer holds the real
`net` grant and calls `http.Client.send` with what this library built.

```toml
[dependencies]
httpx = "Lilly/fpl/httpx"
```

```kelp
impl "std/http"
impl "deps/httpx/lib"
```

A consumer that both builds and sends still writes its own net grant on
`std/http`:

```kelp
impl "std/http" caps(net = ["api.example.com:443"])
impl "deps/httpx/lib"
```

## Query strings

`http.Header` is reused purely as a generic name/value pair here: nothing HTTP
about it at this call, but it saves declaring a second identical `datac`.

| Function | Returns | Notes |
| --- | --- | --- |
| `build_query(pairs: &List<http.Header>)` | `String` | `a=b&c=d`, both sides percent-encoded, unreserved set per RFC 3986 |
| `url_with_query(base: &str, pairs: &List<http.Header>)` | `String` | `base` with `?<query>` appended; no `?` when `pairs` is empty |
| `percent_encode(text: &str)` | `String` | the encoder `build_query` uses, exposed |
| `is_unreserved(c: u8)` / `hex_upper(nibble: u8)` | `bool` / `u8` | the supporting predicates |

## Basic Auth

| Function | Returns |
| --- | --- |
| `basic_auth_header(user: &str, pass: &str)` | `http.Header`: `Authorization: Basic <base64(user:pass)>` |
| `base64_encode(data: &Bytes)` | `String`: this library's own encoder |

The base64 encoder and the percent-encoder are this library's own copies, not a
dependency on the `encoding` folder: a folder here must stand alone (only the
named folder is fetched), so `httpx` carries its own small versions.

## Method helpers

`std/http` ships `GET` and text-body `POST`; these build the rest, with an empty
header list (`empty_headers()`).

| Function | Returns |
| --- | --- |
| `make_put(url: &str, body: move Bytes)` | `http.Request`, method `PUT` |
| `make_delete(url: &str)` | `http.Request`, method `DELETE`, empty body |
| `make_patch(url: &str, body: move Bytes)` | `http.Request`, method `PATCH` |
| `empty_headers()` | `List<http.Header>` |

## Cookies

| Function | Returns | Notes |
| --- | --- | --- |
| `parse_set_cookie(header_value: &str)` | `http.Header` | the `name=value` pair out of one `Set-Cookie` value |
| `segment_end(s: &str)` | `usize` | offset of the first `;`, or the length |

Attributes (`Path=`, `Expires=`, `HttpOnly`, ...) are dropped: a real cookie jar
would keep `Path`/`Domain`/`Max-Age`/`Secure` to decide when a cookie applies and
when it expires; this is the v1 cut of "read the value back".

`parse_set_cookie` **panics** (`httpx.parse_set_cookie: no '=' in cookie pair`)
when the header has no `=`.

## Example

```kelp
impl "std/http"
impl "deps/httpx/lib"

fun main() {
    var pairs: List<http.Header> = List.empty()
    pairs.push(http.Header(name = "q", value = "a b"))
    pairs.push(http.Header(name = "n", value = "7"))
    print(httpx.build_query(pairs))
    print(httpx.url_with_query("http://example.com/search", pairs))
    val auth = httpx.basic_auth_header("ada", "s3cret")
    print(auth.name.as_str())
    print(auth.value.as_str())
    val body = Bytes.from_str("{\"a\":1}")
    val put = httpx.make_put("http://example.com/x", body)
    print(put.method.as_str())
    print(put.body.len())
    val del = httpx.make_delete("http://example.com/x")
    print(del.method.as_str())
    val patch = httpx.make_patch("http://example.com/x", Bytes.from_str("y"))
    print(patch.method.as_str())
    val cookie = httpx.parse_set_cookie("sid=abc123; Path=/; HttpOnly")
    print(cookie.name.as_str())
    print(cookie.value.as_str())
}
```

Output:

```
q=a%20b&n=7
http://example.com/search?q=a%20b&n=7
Authorization
Basic YWRhOnMzY3JldA==
PUT
7
DELETE
PATCH
sid
abc123
```

## Notes

- Cookies are read, never stored or sent back: no jar, no expiry, no `Domain`
  matching.
- `build_query` does not sort or deduplicate pairs; order is list order.
- `percent_encode` uses the URL unreserved set only: no `+`-for-space form
  (`application/x-www-form-urlencoded`).
- Nothing here sends a request. Wiring it to `http.Client.send` (and therefore
  real `net` authority) is the caller's `impl` line.
