# http_fetch

Fetches a URL and writes the body to a file atomically. It is the example that
puts two capabilities in one program: a network grant for the request, and a
filesystem grant for the write.

| | |
| --- | --- |
| Source | [`src/http_fetch.kp`](src/http_fetch.kp) |
| Needs | `fsx = "Juniper/fpl/fsx"` |
| Shows | a grant on an import, a request built as data, a response read, `write_atomic` |

## The dependency and the two grants

```toml
[dependencies]
fsx = "Juniper/fpl/fsx"
```

```kelp
impl "std/http" with caps(net = ["127.0.0.1:*"])
impl "std/str"
impl "deps/fsx/lib" as fsx with caps(fs = ["/tmp/**"])
```

`std/http` is ungated itself but it holds `net`, so importing it means delegating
`net` somewhere. That is this program's `net` authority. The `fsx` grant is a
separate domain, and the pattern is the directory the write may land in.

## The program

```kelp
impl "std/http" with caps(net = ["127.0.0.1:*"])
impl "std/str"
impl "deps/fsx/lib" as fsx with caps(fs = ["/tmp/**"])

fun main() {
    val client = http.default_client()
    val request = http.Request(
        method = "GET",
        url = "http://127.0.0.1:8765/notes.txt",
        headers = http.empty_headers(),
        body = Bytes.empty(),
    )

    val response = client.send(request)
    print(response.status)
    print(response.is_ok())

    val body = response.text()
    print(str.len(body.as_str()))

    val path = "/tmp/kelp-http-body.txt"
    fsx.write_atomic(path, Bytes.from_str(body.as_str()))
    print(path)
}
```

## Run it

Any static server on loopback will do:

```sh
mkdir -p /tmp/kelp-http
printf 'fetched by kelp\n' > /tmp/kelp-http/notes.txt
python3 -m http.server 8765 --directory /tmp/kelp-http &

kelpc build http_fetch.kp -o http_fetch && ./http_fetch
```

## Output

```
200
true
16
/tmp/kelp-http-body.txt
```

And the file it wrote contains what was served:

```text
fetched by kelp
```

## What to take from it

- **A request is data.** `http.Request` is a `datac` with a method, a URL, a
  header list and a body, and `Client.send` performs it. Nothing happens at
  construction time, which is what makes a request easy to build in pieces.
- **`write_atomic` writes to a sibling temp file and renames it over the target.**
  A rename inside one filesystem is atomic, so a reader never sees half a file,
  and a crash halfway leaves the previous file intact. `fs.write_text` truncates
  in place and would not.
- **The status is a number and `is_ok()` is the range check.** A caller that
  cares about a 404 or a 304 asks `response.status` directly. `http.Response`
  carries the headers and the body, so a redirect chain or a content type is
  available without a second request.
- **`response.text()` copies the body into a `String`,** so `str.len` on it counts
  bytes and `Bytes.from_str` turns it back into a buffer for the write. A binary
  body would stay a `Bytes` throughout.
- **Two domains, two patterns, no interaction.** The `net` grant says which host
  may be dialled and the `fs` grant says which directory may be written. Neither
  one widens the other, and a program that only fetches does not need the
  filesystem grant at all.
- **`http.parse_url` refuses `https` by name.** TLS is a later milestone, so a URL
  scheme this client cannot speak is a compile-time-refused call rather than a
  plaintext request to a port that will not answer.

## See also

- [`httpx`](../libraries/httpx.md) for query strings, Basic auth and the other methods
- [`std/http`](../stdlib/http.md) for keep-alive, framing and the connection pool
- [`fsx`](../libraries/fsx.md) for `write_atomic`, `copy_dir` and `tail`
