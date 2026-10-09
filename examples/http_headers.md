---
title: "http_headers"
description: "Builds the pieces of an HTTP request that std/http leaves to the caller - a query string, a Basic auth header, the methods past GET and POST, and the value out of a Set-Cookie."
isPublished: true
tags: "example, networking"
---
Builds the pieces of an HTTP request that `std/http` leaves to the caller: a query
string, a Basic auth header, the methods past `GET` and `POST`, and the value out
of a `Set-Cookie`.

| | |
| --- | --- |
| Source | [`src/http_headers.kp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki-wikijs/raw/branch/main/examples/src/http_headers.kp) |
| Needs | `httpx` (and `std/http` for its types) |
| Shows | request data built offline, which the caller then sends under its own grant |

## The dependency

```toml
[dependencies]
httpx = "Juniper/fpl/httpx"
```

`httpx` carries its own base64 and percent encoders, because a folder in a git
repo has to stand alone: it cannot import the `encoding` library, since only the
folder you named is fetched.

## The program

```kelp project
impl "std/http"
impl "deps/httpx/lib"
impl "std/str"

fun main() {
    // httpx reuses http.Header as a name/value pair, which saves a second type.
    var pairs: List<http.Header> = List.empty()
    pairs.push(http.Header(name = "q", value = "kelp lang"))
    pairs.push(http.Header(name = "page", value = "2"))

    val query = httpx.build_query(pairs)
    print(str.concat("httpx      query = ", query.as_str()))

    val url = httpx.url_with_query("http://example.invalid/search", pairs)
    print(str.concat("httpx      url = ", url.as_str()))

    val auth = httpx.basic_auth_header("ada", "s3cret")
    print(str.concat("httpx      header = ", auth.name.as_str()))
    print(str.concat("httpx      value = ", auth.value.as_str()))

    val put = httpx.make_put("http://example.invalid/items/1", Bytes.from_str("{\"n\":1}"))
    print(str.concat("httpx      put method = ", put.method.as_str()))
    print("httpx      put body bytes = ${put.body.len()}")

    val patch = httpx.make_patch("http://example.invalid/items/1", Bytes.from_str("{}"))
    print(str.concat("httpx      patch method = ", patch.method.as_str()))

    val delete = httpx.make_delete("http://example.invalid/items/1")
    print(str.concat("httpx      delete method = ", delete.method.as_str()))

    // Attributes are dropped: this reads the pair, not a cookie jar.
    val cookie = httpx.parse_set_cookie("sid=abc123; Path=/; HttpOnly")
    print(str.concat("httpx      cookie name = ", cookie.name.as_str()))
    print(str.concat("httpx      cookie value = ", cookie.value.as_str()))
}
```

## Run it

```sh
kelpc run http_headers.kp
```

## Output

```
httpx      query = q=kelp%20lang&page=2
httpx      url = http://example.invalid/search?q=kelp%20lang&page=2
httpx      header = Authorization
httpx      value = Basic YWRhOnMzY3JldA==
httpx      put method = PUT
httpx      put body bytes = 7
httpx      patch method = PATCH
httpx      delete method = DELETE
httpx      cookie name = sid
httpx      cookie value = abc123
```

Nothing here touches the network, which is why the program runs with no grant:
`Basic YWRhOnMzY3JldA==` is `base64("ada:s3cret")`, and the requests are values.

## What to take from it

- **`http.Header` doubles as a name/value pair** for the query builder, which
  saves declaring a second identical `datac`. The reuse is deliberate and noted in
  the source.
- **Both sides of a query are percent-encoded,** so a space is `%20` and a `/` is
  `%2F`. `url_with_query` appends nothing when the list is empty.
- **`basic_auth_header` returns a `Header`, not a string,** so it drops straight
  into a request's header list.
- **`httpx` holds no authority.** It never dials; the caller does that with
  `http.Client.send` under its own `net` grant. Importing `std/http` is what
  requires `net` to be delegated somewhere, and `httpx` satisfies that internally
  with an empty grant for the module it does not use.
- **`parse_set_cookie` keeps the pair and drops the attributes.** A real cookie jar
  would keep `Path`, `Domain` and `Max-Age`; this is the "read the value back" cut,
  and it panics when there is no `=`.
- **`PUT` and `PATCH` take the body by `move`,** so `Bytes.from_str(...)` goes
  straight in as a temporary with no binding.

## See also

- [`httpx`](/libraries/httpx)
- [`std/http`](/stdlib/http) for the client, keep-alive and the connection pool
- [http_fetch](/examples/http_fetch) for the same client used over a real socket
