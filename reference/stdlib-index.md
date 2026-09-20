---
title: "Standard library index"
description: "Every public name in the shipped standard library, one line each, generated from kelpc/std/.kp at kelp commit 940c524 by tools/stdlib-index.py, a generator kept at the archived branch mkdocs-archive, plus str.less and str.is_digit from kelp 2fa7de5. Behaviour, panics and examples live in the Standard..."
isPublished: true
tags: "reference"
---
Every public name in the shipped standard library, one line each, generated from
`kelpc/std/*.kp` by `tools/stdlib-index.py`, which lived in this repository's
MkDocs-era layout and is kept at branch `mkdocs-archive` and tag `mkdocs-final`,
not in the current tree.

The page was last re-derived with that script at `kelp` commit `54b6ba8`, plus
the three names that landed after it (`fmt.commas_u64`, `fmt.commas_i64` and
`fmt.human_size`, from `kelp` `a75deb6`). Three names and one module make that
worth saying: `str.less` and `str.is_digit` landed after the `940c524` revision
the page used to be pinned to, and `std/encoding` is new, and the script's own
`ORDER` list has to carry `encoding` before it writes that section. The script
prints the MkDocs layout (an H1 title, `docs/`-relative links, no front matter),
so the front matter and the absolute links on this page are the hand-kept part.

`std/rt` has no section: it ships inside the binary but is compiler-internal and
is not importable, so it is not part of the surface a program can name. Behaviour,
panics and examples live in the [Standard library](/stdlib) chapter.

A module marked with a domain needs that capability delegated on the `impl` line, e.g.
`impl "std/fs" caps(fs = ["/srv/data/**"])`.

## `std/mem`

Functions:

- `fun alloc(n: usize).R: Bytes`

## `std/str`

Types:

- `enum ParseErr { Empty, Invalid }`

Functions:

- `fun len(s: &str).R: usize`
- `fun byte(s: &str, i: usize).R: u8`
- `fun is_empty(s: &str).R: bool`
- `fun substring(s: &str, from: usize).R: &str`
- `fun char_count(s: &str).R: usize`
- `fun index_of(s: &str, needle: &str).R: option.Option<usize>`
- `fun starts_with_at(s: &str, needle: &str, at: usize).R: bool`
- `fun starts_with(s: &str, prefix: &str).R: bool`
- `fun ends_with(s: &str, suffix: &str).R: bool`
- `fun contains(s: &str, needle: &str).R: bool`
- `fun eq(a: &str, b: &str).R: bool`
- `fun less(a: &str, b: &str).R: bool`
- `fun is_space(c: u8).R: bool`
- `fun is_digit(c: u8).R: bool`
- `fun trim_start(s: &str).R: &str`
- `fun trim_end(s: &str).R: String`
- `fun prefix(s: &str, n: usize).R: String`
- `fun trim(s: &str).R: String`
- `fun to_upper(s: &str).R: String`
- `fun to_lower(s: &str).R: String`
- `fun repeat(s: &str, n: usize).R: String`
- `fun copy_range(s: &str, from: usize, to: usize).R: String`
- `fun split(s: &str, sep: &str).R: List<String>`
- `fun copy_into(dst: mut Bytes, at: usize, src: &str).R: usize`
- `fun join(parts: List<String>, sep: &str).R: String`
- `fun concat(a: &str, b: &str).R: String`
- `fun from_u64(n: u64).R: String`
- `fun from_i64(n: i64).R: String`
- `fun from_f64(x: f64, decimals: i32).R: String`
- `fun parse_i64(s: &str).R: result.Result<i64, ParseErr>`
- `fun parse_u64(s: &str).R: result.Result<u64, ParseErr>`
- `fun parse_f64(s: &str).R: result.Result<f64, ParseErr>`
- `fun parse_err(s: &str).R: ParseErr`
- `fun replace(s: &str, from: &str, to: &str).R: String`
- `fun byte_index(s: &str, i: usize).R: usize`
- `fun decode_at(s: &str, at: usize).R: u32`
- `fun char_at(s: &str, i: usize).R: u32`

## `std/path`

Functions:

- `fun is_absolute(s: &str).R: bool`
- `fun normalize(s: &str).R: String`
- `fun last_sep(s: &str).R: usize`
- `fun file_name(s: &str).R: &str`
- `fun extension(s: &str).R: &str`
- `fun stem(s: &str).R: String`
- `fun has_extension(s: &str, ext: &str).R: bool`
- `fun split(s: &str).R: List<String>`
- `fun join_all(parts: List<String>).R: String`
- `fun parent(s: &str).R: String`
- `fun join(a: &str, b: &str).R: String`

## `std/math`

Constants:

- `const PI: f64 = 3.141592653589793`
- `const E: f64 = 2.718281828459045`
- `const TAU: f64 = 6.283185307179586`

Functions:

- `fun sqrt(x: f64).R: f64`
- `fun pow(base: f64, exp: f64).R: f64`
- `fun floor(x: f64).R: f64`
- `fun ceil(x: f64).R: f64`
- `fun round(x: f64).R: f64`
- `fun trunc(x: f64).R: f64`
- `fun exp(x: f64).R: f64`
- `fun ln(x: f64).R: f64`
- `fun log2(x: f64).R: f64`
- `fun log10(x: f64).R: f64`
- `fun sin(x: f64).R: f64`
- `fun cos(x: f64).R: f64`
- `fun tan(x: f64).R: f64`
- `fun atan2(y: f64, x: f64).R: f64`
- `fun is_nan(x: f64).R: bool`
- `fun is_finite(x: f64).R: bool`
- `fun sign(x: f64).R: f64`
- `fun abs(x: i32).R: i32`
- `fun abs(x: i64).R: i64`
- `fun abs(x: f64).R: f64`
- `fun min(a: i32, b: i32).R: i32`
- `fun min(a: i64, b: i64).R: i64`
- `fun min(a: f64, b: f64).R: f64`
- `fun max(a: i32, b: i32).R: i32`
- `fun max(a: i64, b: i64).R: i64`
- `fun max(a: f64, b: f64).R: f64`
- `fun clamp(x: i32, lo: i32, hi: i32).R: i32`
- `fun clamp(x: i64, lo: i64, hi: i64).R: i64`
- `fun clamp(x: f64, lo: f64, hi: f64).R: f64`

## `std/fmt`

Functions:

- `fun int(n: i64).R: String`
- `fun uint(n: u64).R: String`
- `fun float(x: f64, decimals: i32).R: String`
- `fun hex(n: u64).R: String`
- `fun bytes(b: Bytes).R: String`
- `fun pad_left(s: &str, width: usize, fill: u8).R: String`
- `fun pad_right(s: &str, width: usize, fill: u8).R: String`
- `fun commas_u64(n: u64).R: String`
- `fun commas_i64(n: i64).R: String`
- `fun human_size(bytes: u64).R: String`

## `std/encoding`

Types:

- `enum DecodeErr { Invalid }`

Constants:

- `const B64_ALPHABET: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"`
- `const B32_ALPHABET: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"`
- `const B58_ALPHABET: str = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"`

Functions:

- `fun b64_char(v: u8).R: u8`
- `fun b64_value(c: u8).R: option.Option<u8>`
- `fun base64_encode(data: &Bytes).R: String`
- `fun base64_decode(text: &str).R: result.Result<Bytes, DecodeErr>`
- `fun b32_char(v: u8).R: u8`
- `fun b32_value(c: u8).R: option.Option<u8>`
- `fun base32_encode(data: &Bytes).R: String`
- `fun base32_decode(text: &str).R: result.Result<Bytes, DecodeErr>`
- `fun b58_char(v: u8).R: u8`
- `fun b58_value(c: u8).R: option.Option<u8>`
- `fun base58_encode(data: &Bytes).R: String`
- `fun base58_decode(text: &str).R: result.Result<Bytes, DecodeErr>`
- `fun hex_upper(nibble: u8).R: u8`
- `fun hex_lower(nibble: u8).R: u8`
- `fun hex_value(c: u8).R: option.Option<u8>`
- `fun hex_encode(data: &Bytes).R: String`
- `fun hex_decode(text: &str).R: result.Result<Bytes, DecodeErr>`
- `fun dump(data: &Bytes).R: String`
- `fun is_unreserved(c: u8).R: bool`
- `fun percent_encode(text: &str).R: String`
- `fun percent_decode(text: &str).R: result.Result<String, DecodeErr>`
- `fun form_encode(text: &str).R: String`
- `fun form_decode(text: &str).R: result.Result<String, DecodeErr>`

## `std/io`

Types:

- `datac File(val fd: i32)`
- `datac BufReader(val file: File, var buf: Bytes, var start: usize, var end: usize)`

Functions:

- `fun File.is_open().R: bool`
- `fun File.read(max: usize).R: Bytes`
- `fun File.read_into(buf: mut Bytes, at: usize).R: usize`
- `fun File.read_all().R: Bytes`
- `fun File.write(data: Bytes).R: usize`
- `fun File.write_text(text: String).R: usize`
- `fun File.write_str(text: &str).R: usize`
- `fun File.flush()`
- `fun File.close()`
- `fun mut File.set_nonblocking(on: bool)`
- `fun File.wait_readable(timeout_ms: u64).R: bool`
- `fun File.wait_writable(timeout_ms: u64).R: bool`
- `fun stdin().R: File`
- `fun stdout().R: File`
- `fun stderr().R: File`
- `fun buf_reader(f: File).R: BufReader`
- `fun mut BufReader.read_line_into(out: mut String).R: bool`
- `fun mut BufReader.read_line().R: option.Option<String>`
- `fun mut BufReader.read_all().R: Bytes`
- `fun read_line().R: option.Option<String>`
- `fun read_lines().R: List<String>`
- `fun read_all().R: Bytes`
- `fun print(s: &str)`
- `fun print_bare(s: &str)`
- `fun eprint(s: &str)`
- `fun eprint_bare(s: &str)`

## `std/fs` (needs `fs`)

Types:

- `datac Metadata(val size: u64, val mtime: i64, val mode: u32, val is_dir: bool, val is_file: bool)`

Functions:

- `fun read(path: &str).R: Bytes`
- `fun read_text(path: &str).R: String`
- `fun write(path: &str, data: Bytes)`
- `fun write_text(path: &str, text: String)`
- `fun exists(path: &str).R: bool`
- `fun is_file(path: &str).R: bool`
- `fun is_dir(path: &str).R: bool`
- `fun size(path: &str).R: u64`
- `fun remove(path: &str)`
- `fun rename(from: &str, to: &str)`
- `fun mkdir(path: &str)`
- `fun append(path: &str, data: Bytes)`
- `fun sync(path: &str)`
- `fun list(path: &str).R: List<String>`
- `fun mkdir_all(path: &str)`
- `fun remove_all(target: &str)`
- `fun walk(dir: &str).R: List<String>`
- `fun copy(from: &str, to: &str)`
- `fun symlink(target: &str, link: &str)`
- `fun touch(path: &str)`
- `fun open(path: &str, mode: &str).R: io.File`
- `fun read_lines(path: &str).R: List<String>`
- `fun temp_path(prefix: &str).R: String`
- `fun metadata(path: &str).R: Metadata`

## `std/process` (needs `process`)

Types:

- `datac Child(val pid: i32, val stdin: io.File, val stdout: io.File, val stderr: io.File, var exited: bool, var code: i32)`
- `datac RunResult(val code: i32, val out: Bytes, val err: Bytes)`
- `enum ProcErr { NotFound, NotExecutable, DirNotFound }`

Functions:

- `fun args().R: List<String>`
- `fun arg_count().R: usize`
- `fun spawn_in(dir: &str, program: &str, args: List<String>).R: Child`
- `fun spawn(program: &str, args: List<String>).R: Child`
- `fun run_in(dir: &str, program: &str, args: List<String>).R: RunResult`
- `fun run(program: &str, args: List<String>).R: RunResult`
- `fun executable(program: &str).R: bool`
- `fun try_run_in(dir: &str, program: &str, args: List<String>).R: result.Result<RunResult, ProcErr>`
- `fun try_run(program: &str, args: List<String>).R: result.Result<RunResult, ProcErr>`
- `fun mut Child.wait().R: i32`
- `fun mut Child.is_running().R: bool`
- `fun Child.kill(signal: i32)`
- `fun exit(code: i32)`
- `fun getpid().R: i64`

## `std/net` (needs `net`)

Types:

- `datac Socket(val fd: i32)`
- `datac Listener(val fd: i32)`

Functions:

- `fun connect(host: &str, port: u16).R: Socket`
- `fun listen(port: u16).R: Listener`
- `fun accept(l: Listener).R: Socket`
- `fun close(s: Socket)`
- `fun Listener.close()`
- `fun shutdown_write(s: Socket)`
- `fun send(s: Socket, data: Bytes).R: usize`
- `fun send_all(s: Socket, data: Bytes).R: usize`
- `fun send_text(s: Socket, text: &str)`
- `fun recv(s: Socket, max: usize).R: Bytes`
- `fun recv_into(s: Socket, buf: mut Bytes, at: usize).R: usize`
- `fun Socket.wait_readable(timeout_ms: u64).R: bool`
- `fun Socket.wait_writable(timeout_ms: u64).R: bool`
- `fun mut Socket.set_timeout(ms: u64)`
- `fun Listener.port().R: u16`
- `fun Socket.peer_addr().R: String`
- `fun resolve(host: &str).R: List<String>`

## `std/http`

Types:

- `datac Url(val scheme: String, val host: String, val port: u16, val path: String)`
- `datac Header(val name: String, val value: String)`
- `datac Response(val status: i32, val headers: List<Header>, val body: Bytes, val reusable: bool)`
- `datac Request(val method: String, val url: String, val headers: List<Header>, val body: Bytes)`
- `datac Client(val timeout_ms: u64, val max_redirects: i32, val follow_redirects: bool)`
- `datac Pool(val host: String, val port: u16, val size: usize, val timeout_ms: u64, var idle: List<i32>)`
- `datac Lease(val fd: i32, val reused: bool)`
- `datac Cursor(val fd: i32, var buf: Bytes, var start: usize)`

Constants:

- `const DEFAULT_SCHEME: str = "http"`
- `const DEFAULT_PORT: u16 = 80`
- `const DEFAULT_TIMEOUT_MS: u64 = 30000`
- `const DEFAULT_MAX_REDIRECTS: i32 = 5`
- `const pool_size: usize = __KELP_HTTP_POOL__`

Functions:

- `fun parse_url(s: &str).R: Url`
- `fun split_authority(rest: &str).R: Url`
- `fun make_url(authority: String, path: &str).R: Url`
- `fun parse_port(text: &str).R: u16`
- `fun name_eq(a: &str, b: &str).R: bool`
- `fun empty_headers().R: List<Header>`
- `fun Response.has_header(name: &str).R: bool`
- `fun Response.header(name: &str).R: String`
- `fun Response.is_ok().R: bool`
- `fun Response.text().R: String`
- `fun build_head(method: &str, u: Url, headers: List<Header>, body_len: usize).R: String`
- `fun mut Cursor.ensure()`
- `fun mut Cursor.read_line().R: String`
- `fun mut Cursor.skip_line()`
- `fun mut Cursor.read_exact(n: usize).R: Bytes`
- `fun mut Cursor.read_to_end().R: Bytes`
- `fun hex_digit(c: u8).R: u32`
- `fun parse_hex(text: &str).R: usize`
- `fun mut Cursor.read_chunked().R: Bytes`
- `fun find_head_end(b: Bytes).R: usize`
- `fun head_text(b: Bytes, end: usize).R: String`
- `fun parse_status_line(line: &str).R: i32`
- `fun status_code(text: &str).R: i32`
- `fun parse_headers(lines: List<String>).R: List<Header>`
- `fun header_value(hs: List<Header>, name: &str).R: String`
- `fun content_length_of(hs: List<Header>).R: i64`
- `fun is_chunked(hs: List<Header>).R: bool`
- `fun wants_close(hs: List<Header>).R: bool`
- `fun read_response(s: net.Socket).R: Response`
- `fun one_exchange(s: net.Socket, method: &str, u: Url, headers: List<Header>, body: Bytes).R: Response`
- `fun keep_body_on(status: i32).R: bool`
- `fun is_redirect(status: i32).R: bool`
- `fun absolute_url(base: Url, loc: &str).R: String`
- `fun follow_url(client: Client, base: Url, resp: Response, hops: i32).R: String`
- `fun default_client().R: Client`
- `fun Client.send(req: Request).R: Response`
- `fun send_fresh(`
- `fun exchange(s: net.Socket, req: Request).R: Response`
- `fun pool(host: &str, port: u16).R: Pool`
- `fun empty_idle().R: List<i32>`
- `fun connect_configured(host: &str, port: u16, timeout_ms: u64).R: net.Socket`
- `fun Pool.size().R: usize`
- `fun Pool.len().R: usize`
- `fun Lease.socket().R: net.Socket`
- `fun mut Pool.warm()`
- `fun mut Pool.checkout().R: Lease`
- `fun mut Pool.release(lease: Lease, reusable: bool)`
- `fun mut Pool.close_all()`
- `fun pool_matches(p: Pool, u: Url).R: bool`
- `fun mut Pool.send(req: Request).R: Response`
- `fun pooled_hop(`
- `fun get(url: &str).R: Response`
- `fun make_get(url: &str).R: Request`
- `fun post_text(url: &str, body: &str, content_type: &str).R: Response`

## `std/time` (needs `time`)

Functions:

- `fun now_unix().R: i64`
- `fun now_mono_ns().R: i64`
- `fun sleep_ms(ms: u64)`

## `std/rand` (needs `rand`)

Functions:

- `fun u64().R: u64`
- `fun below(n: u64).R: u64`
- `fun bytes(n: usize).R: Bytes`

## `std/env` (needs `env`)

Functions:

- `fun has(name: &str).R: bool`
- `fun get(name: &str).R: String`
- `fun set(name: &str, value: &str)`
- `fun unset(name: &str)`

## `std/list`

Functions:

- `fun map<T, U>(xs: &List<T>, f: closure(&T).R: U).R: List<U>`
- `fun filter<T>(xs: &List<T>, f: closure(&T).R: bool).R: List<T>`
- `fun each<T>(xs: &List<T>, f: closure(&T))`
- `fun find_index<T>(xs: &List<T>, f: closure(&T).R: bool).R: option.Option<usize>`
- `fun any<T>(xs: &List<T>, f: closure(&T).R: bool).R: bool`
- `fun all<T>(xs: &List<T>, f: closure(&T).R: bool).R: bool`

## `std/option`

Types:

- `enum Option<T> { Some(val value: T), None }`

Functions:

- `fun is_some<T>(o: &Option<T>).R: bool`
- `fun is_none<T>(o: &Option<T>).R: bool`
- `fun unwrap_or<T>(o: &Option<T>, fallback: T).R: T`
- `fun unwrap<T>(o: &Option<T>).R: T`
- `fun expect<T>(o: &Option<T>, message: &str).R: T`
- `fun map<T, U>(o: &Option<T>, f: closure(&T).R: U).R: Option<U>`
- `fun and_then<T, U>(o: &Option<T>, f: closure(&T).R: Option<U>).R: Option<U>`
- `fun or_else<T>(o: &Option<T>, f: closure().R: Option<T>).R: Option<T>`
- `fun each<T>(o: &Option<T>, f: closure(&T))`

## `std/result`

Types:

- `enum Result<T, E> { Ok(val value: T), Err(val error: E) }`

Functions:

- `fun is_ok<T, E>(r: &Result<T, E>).R: bool`
- `fun is_err<T, E>(r: &Result<T, E>).R: bool`
- `fun unwrap_or<T, E>(r: &Result<T, E>, fallback: T).R: T`
- `fun unwrap<T, E>(r: &Result<T, E>).R: T`
- `fun unwrap_err<T, E>(r: &Result<T, E>).R: E`
- `fun expect<T, E>(r: &Result<T, E>, message: &str).R: T`
- `fun expect_err<T, E>(r: &Result<T, E>, message: &str).R: E`
- `fun map<T, U, E>(r: &Result<T, E>, f: closure(&T).R: U).R: Result<U, E>`
- `fun map_err<T, E, F>(r: &Result<T, E>, f: closure(&E).R: F).R: Result<T, F>`
- `fun and_then<T, U, E>(r: &Result<T, E>, f: closure(&T).R: Result<U, E>).R: Result<U, E>`
- `fun or_else<T, E, F>(r: &Result<T, E>, f: closure(&E).R: Result<T, F>).R: Result<T, F>`
- `fun each<T, E>(r: &Result<T, E>, f: closure(&T))`

## Modules at a glance

| Module | Functions | Types/constants | Domain |
| --- | ---: | ---: | --- |
| `std/mem` | 1 | 0 | — |
| `std/str` | 37 | 1 | — |
| `std/path` | 11 | 0 | — |
| `std/math` | 29 | 3 | — |
| `std/fmt` | 10 | 0 | — |
| `std/encoding` | 23 | 4 | — |
| `std/io` | 26 | 2 | — |
| `std/fs` | 24 | 1 | fs |
| `std/process` | 14 | 3 | process |
| `std/net` | 17 | 2 | net |
| `std/http` | 54 | 13 | — |
| `std/time` | 3 | 0 | time |
| `std/rand` | 3 | 0 | rand |
| `std/env` | 4 | 0 | env |
| `std/list` | 6 | 0 | — |
| `std/option` | 9 | 1 | — |
| `std/result` | 12 | 1 | — |

## Not importable

`std/rt` holds the capability matcher the compiler uses internally and is excluded from
the shipped list, so `impl "std/rt"` is refused. The importable glob matcher is
[`glob`](/libraries/glob).

## See also

- [Standard library](/stdlib)
- [Capabilities](/language/capabilities)
- [Capability patterns](/reference/capability-patterns)
