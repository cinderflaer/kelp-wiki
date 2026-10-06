---
title: "Standard library index"
description: "Every public name in the shipped standard library, one line each, kept by hand against kelpc/std/.kp. Behaviour, panics and examples live in the Standard library chapter."
isPublished: true
tags: "reference"
---
Every public name in the shipped standard library, one line each, kept by hand
against `kelpc/std/*.kp` and updated here when the standard library moves. The
MkDocs-era `tools/stdlib-index.py` that once wrote the page is archived at
branch `mkdocs-archive` and tag `mkdocs-final`, not in the current tree, and is
not run.

Names have landed in batches since the last full pass: `fmt.commas_u64`,
`fmt.commas_i64` and `fmt.human_size` (`kelp` `a75deb6`), then `fs.cwd`,
`fs.is_symlink`, `fs.read_link` and `path.absolute`, then `io.IoErr` and
`io.errno_text` with `fs.try_read`, `fs.try_read_text` and `fs.try_open`, and
finally `str.less`, `str.is_digit` and the whole `std/encoding` module. The
`std/atomic` names below (`Atomic<T>` and `Ordering`, MK9-S3-M1 stage A1) were
added by hand at `kelp` `724cb67` and the `std/thread` name below (`fence`,
stage A2 of the same milestone) at `kelp` `eb836da`, for the same reason the
rest of the page is hand-kept: the generator is not in the tree, so a new module
has to be written into the page by hand rather than re-derived. The last batch is
`std/ws`, the WebSocket client, at `kelp` `0d2c527`, with `encoding.sha1` beside
it. The batch after it is the fallible dial at `kelp` `93d050f`:
`net.try_connect` with `ConnectErr`, and `ws.try_connect` with `WsErr` beside the
three helpers that keep the panicking `connect` wrappers honest (`handshake`,
`refusal_text`, `fail_connect`). The batch after that is `thread.sleep_ms` and
`thread.current_id` (MK9-S3-M1 stage C2, `kelp` `54d3bdb`), the module's first
two names that are ordinary `.kp` signatures rather than compiler builtins. The
latest batch is `std/tls`, a new module (MK5-S4b-M1), plus `std/http`'s
`RateLimit`/`Conn` types and `retry_after`/`rate_limit` accessors
(`MISSING-p5Xtr`), all at `kelp` `e33ea55`. The batch after it is the typed
error surface: `std/tls`'s `TlsError`/`TlsOptions` and its `try_` family,
`std/http`'s `HttpErr` and `try_get`/`try_send`, and `std/net`'s `NetErr` with
`try_send_all`/`try_recv`/`try_recv_into`. The batch after that is `std/arena`,
kernel stage 13's bump arena, whose six functions and one type are below. The
batch documented here adds the HTTP/1.1 server to `std/http`
(`listen`/`accept`/`serve*`, `Limits`, `ServerRequest`/`ServerResponse`) with
`net.mono_ms`, `net.try_accept`, `net.try_shutdown_write` and
`Listener.set_timeout`, and a new module, `std/regex`, a linear-time Pike VM
that is freestanding-capable with the allocator pair. The batch documented here
adds `std/tz`, time zones over the system TZif database: the nine functions and
five types below are the whole surface, and it is hosted only because it reads a
file and `$TZDIR`. The
kernel-path language surface
(`unsafe`/`Ptr<T>`, `repr(...)`, statics, `defer`, the `[target]` manifest
section) is not a stdlib name and lives on the [language pages](/language), not
here.

`std/rt` has no section: it ships inside the binary but is the compiler's own
runtime module rather than part of the stdlib surface. `impl "std/rt"` resolves
(the resolver injects the module for a program that imports a gated module or
`std/path`, and the differential corpus imports it by name), but nothing should
be told it is a library to reach for. Behaviour,
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
- `fun absolute(base: &str, p: &str).R: String`
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

Trait:

- `pub trait Display { fun Self.to_text().R: String }`, the trait a `datac` or
  `enum` implements to appear in `"${x}"` and `print`
  ([Operator traits and `Display`](/language/operator-traits)).

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
- `fun rotl32(x: u32, n: u32).R: u32`
- `fun sha1(data: &Bytes).R: Bytes`
- `fun push_u32_be(out: mut Bytes, v: u32)`
- `fun form_encode(text: &str).R: String`
- `fun form_decode(text: &str).R: result.Result<String, DecodeErr>`

## `std/regex`

A linear-time regular expression engine (a Pike VM over bytes). Hosted only.
Full account on [`std/regex`](/stdlib/regex).

Types:

- `datac Regex(op: List<i32>, ax: List<i32>, ay: List<i32>, classes: List<u8>, ngroups: usize, var tl_pc: List<i32>, var tl_cap: List<i32>, var cnt: List<usize>, var mark: List<i64>, var gen: i64, var stk_a: List<i32>, var stk_b: List<i32>, var wcap: List<i32>, var res: List<i32>, var nsteps: i64)`
- `datac RegexErr(val message: String, val offset: usize)`
- `datac Match(val start: usize, val end: usize, val text: String)`
- `datac Captures(val text: String, val slots: List<i32>)`

Functions:

- `fun compile(pattern: &str).R: result.Result<Regex, RegexErr>`
- `fun is_match(pattern: &str, text: &str).R: bool`
- `fun mut Regex.is_match(text: &str).R: bool`
- `fun mut Regex.find(text: &str).R: option.Option<Match>`
- `fun mut Regex.find_at(text: &str, start: usize).R: option.Option<Match>`
- `fun mut Regex.captures(text: &str).R: option.Option<Captures>`
- `fun mut Regex.find_all(text: &str).R: List<Match>`
- `fun mut Regex.replace(text: &str, replacement: &str).R: String`
- `fun mut Regex.replace_all(text: &str, replacement: &str).R: String`
- `fun mut Regex.split(text: &str).R: List<String>`
- `fun Regex.steps().R: i64`
- `fun mut Regex.reset_steps()`
- `fun Regex.group_count().R: usize`
- `fun Captures.get(i: usize).R: option.Option<String>`
- `fun Captures.span(i: usize).R: option.Option<Match>`
- `fun Captures.len().R: usize`

## `std/io`

Types:

- `datac File(val fd: i32)`
- `datac BufReader(val file: File, var buf: Bytes, var start: usize, var end: usize)`
- `datac IoErr(val errno: i32, val message: String)`

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
- `fun errno_text(errno: i32).R: String`

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
- `fun is_symlink(path: &str).R: bool`
- `fun read_link(path: &str).R: String`
- `fun cwd().R: String`
- `fun try_read(path: &str).R: result.Result<Bytes, io.IoErr>`
- `fun try_read_text(path: &str).R: result.Result<String, io.IoErr>`
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
- `fun try_open(path: &str, mode: &str).R: result.Result<io.File, io.IoErr>`
- `fun read_lines(path: &str).R: List<String>`
- `fun temp_path(prefix: &str).R: String`
- `fun metadata(path: &str).R: Metadata`

## `std/process` (needs `process`)

Types:

- `datac Child(val pid: i32, val stdin: io.File, val stdout: io.File, val stderr: io.File, var exited: bool, var code: i32, var signal: i32)`
- `datac RunResult(val code: i32, val signal: i32, val out: Bytes, val err: Bytes)`
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
- `datac ConnectErr(val reason: String)`
- `datac NetErr(val reason: String)`

Functions:

- `fun connect(host: &str, port: u16).R: Socket`
- `fun try_connect(host: &str, port: u16).R: result.Result<Socket, ConnectErr>`
- `fun listen(port: u16).R: Listener`
- `fun accept(l: Listener).R: Socket`
- `fun try_accept(l: Listener).R: result.Result<Socket, NetErr>`
- `fun close(s: Socket)`
- `fun Listener.close()`
- `fun Listener.set_timeout(ms: u64)`
- `fun shutdown_write(s: Socket)`
- `fun try_shutdown_write(s: Socket).R: bool`
- `fun mono_ms().R: i64`
- `fun send(s: Socket, data: Bytes).R: usize`
- `fun send_all(s: Socket, data: Bytes).R: usize`
- `fun send_text(s: Socket, text: &str)`
- `fun recv(s: Socket, max: usize).R: Bytes`
- `fun recv_into(s: Socket, buf: mut Bytes, at: usize).R: usize`
- `fun try_send_all(s: Socket, data: Bytes).R: result.Result<usize, NetErr>`
- `fun try_recv(s: Socket, max: usize).R: result.Result<Bytes, NetErr>`
- `fun try_recv_into(s: Socket, buf: mut Bytes, at: usize).R: result.Result<usize, NetErr>`
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
- `datac RateLimit(val limit: Option<u64>, val remaining: Option<u64>, val reset: Option<f64>, val reset_after: Option<f64>, val bucket: Option<String>)`
- `datac Pool(val host: String, val port: u16, val size: usize, val timeout_ms: u64, var idle: List<Conn>)`
- `datac Lease(val fd: i32, val tls_handle: usize, val reused: bool)`
- `datac Conn(val fd: i32, val tls_handle: usize)`
- `datac Cursor(val fd: i32, val tls_handle: usize, var buf: Bytes, var start: usize)`
- `enum HttpErr { Dial(val reason: String), Exchange(val reason: String), Redirects(val reason: String) }`
- `datac Limits(val max_request_line: usize, val max_header_bytes: usize, val max_headers: usize, val max_body: usize, val head_timeout_ms: u64, val body_timeout_ms: u64, val idle_timeout_ms: u64, val max_requests_per_conn: usize)`
- `datac ServerRequest(val method: String, val target: String, val path: String, val query: String, val headers: List<Header>, val body: Bytes)`
- `datac ServerResponse(val status: i32, val headers: List<Header>, val body: Bytes)`
- `datac Server(val fd: i32)`
- `datac ServerConn(val fd: i32, var buf: Bytes, var start: usize, var served: usize, var close_after: bool, var head_only: bool, var keep_alive_header: bool)`

Constants:

- `const DEFAULT_PORT: u16 = 80`
- `const DEFAULT_HTTPS_PORT: u16 = 443`
- `const DEFAULT_TIMEOUT_MS: u64 = 30000`
- `const DEFAULT_MAX_REDIRECTS: i32 = 5`
- `const pool_size: usize = __KELP_HTTP_POOL__`

Functions:

- `fun Conn.is_tls().R: bool`
- `fun conn_send_all(c: Conn, data: Bytes).R: usize`
- `fun conn_recv(c: Conn, max: usize).R: Bytes`
- `fun conn_recv_into(c: Conn, buf: mut Bytes, at: usize).R: usize`
- `fun conn_send_all_try(c: Conn, data: Bytes).R: result.Result<usize, HttpErr>`
- `fun conn_recv_try(c: Conn, max: usize).R: result.Result<Bytes, HttpErr>`
- `fun conn_recv_into_try(c: Conn, buf: mut Bytes, at: usize).R: result.Result<usize, HttpErr>`
- `fun conn_close(c: Conn)`
- `fun connect_configured(host: &str, port: u16, timeout_ms: u64, use_tls: bool).R: Conn`
- `fun Cursor.conn().R: Conn`
- `fun default_port_for(scheme: &str).R: u16`
- `fun url_is_https(u: Url).R: bool`
- `fun parse_url(s: &str).R: Url`
- `fun split_authority(rest: &str, scheme: &str).R: Url`
- `fun make_url(authority: String, path: &str, scheme: &str).R: Url`
- `fun parse_port(text: &str).R: u16`
- `fun name_eq(a: &str, b: &str).R: bool`
- `fun empty_headers().R: List<Header>`
- `fun Response.has_header(name: &str).R: bool`
- `fun Response.header(name: &str).R: String`
- `fun Response.is_ok().R: bool`
- `fun Response.text().R: String`
- `fun Response.retry_after().R: Option<u64>`
- `fun Response.rate_limit().R: RateLimit`
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
- `fun header_u64(hs: List<Header>, name: &str).R: Option<u64>`
- `fun header_f64(hs: List<Header>, name: &str).R: Option<f64>`
- `fun header_opt(hs: List<Header>, name: &str).R: Option<String>`
- `fun content_length_of(hs: List<Header>).R: i64`
- `fun is_chunked(hs: List<Header>).R: bool`
- `fun wants_close(hs: List<Header>).R: bool`
- `fun read_response(c: Conn).R: Response`
- `fun one_exchange(c: Conn, method: &str, u: Url, headers: List<Header>, body: Bytes).R: Response`
- `fun keep_body_on(status: i32).R: bool`
- `fun is_redirect(status: i32).R: bool`
- `fun absolute_url(base: Url, loc: &str).R: String`
- `fun follow_url(client: Client, base: Url, resp: Response, hops: i32).R: String`
- `fun default_client().R: Client`
- `fun Client.send(req: Request).R: Response`
- `fun Client.try_send(req: Request).R: result.Result<Response, HttpErr>`
- `fun send_fresh(`
- `fun exchange(c: Conn, req: Request).R: Response`
- `fun pool(host: &str, port: u16).R: Pool`
- `fun empty_idle().R: List<Conn>`
- `fun Pool.size().R: usize`
- `fun Pool.len().R: usize`
- `fun Lease.conn().R: Conn`
- `fun mut Pool.warm(use_tls: bool)`
- `fun mut Pool.checkout(use_tls: bool).R: Lease`
- `fun mut Pool.try_checkout(use_tls: bool).R: result.Result<Lease, HttpErr>`
- `fun mut Pool.release(lease: Lease, reusable: bool)`
- `fun mut Pool.close_all()`
- `fun pool_matches(p: Pool, u: Url).R: bool`
- `fun mut Pool.send(req: Request).R: Response`
- `fun mut Pool.try_send(req: Request).R: result.Result<Response, HttpErr>`
- `fun pooled_hop(`
- `fun get(url: &str).R: Response`
- `fun try_get(url: &str).R: result.Result<Response, HttpErr>`
- `fun make_get(url: &str).R: Request`
- `fun post_text(url: &str, body: &str, content_type: &str).R: Response`

The server surface (a plain HTTP/1.1 server; see the
[`std/http`](/stdlib/http#the-server) page):

- `fun ok_text(text: &str).R: ServerResponse`
- `fun json(text: &str).R: ServerResponse`
- `fun html(text: &str).R: ServerResponse`
- `fun status(code: i32).R: ServerResponse`
- `fun not_found().R: ServerResponse`
- `fun bad_request(message: &str).R: ServerResponse`
- `fun ServerRequest.header(name: &str).R: String`
- `fun ServerRequest.has_header(name: &str).R: bool`
- `fun ServerRequest.text().R: String`
- `fun ServerRequest.query_param(name: &str).R: option.Option<String>`
- `fun ServerRequest.path_segments().R: List<String>`
- `fun ServerResponse.with_header(name: &str, value: &str).R: ServerResponse`
- `fun mut ServerResponse.add_header(name: &str, value: &str)`
- `fun listen(port: u16).R: Server`
- `fun Server.port().R: u16`
- `fun Server.set_accept_timeout(ms: u64)`
- `fun Server.close()`
- `fun Server.accept().R: ServerConn`
- `fun Server.try_accept().R: result.Result<ServerConn, HttpErr>`
- `fun ServerConn.read_request(limits: &Limits).R: result.Result<ServerRequest, HttpErr>`
- `fun mut ServerConn.write_response(resp: &ServerResponse).R: result.Result<usize, HttpErr>`
- `fun mut ServerConn.write_error(e: &HttpErr).R: result.Result<usize, HttpErr>`
- `fun mut ServerConn.mark_close()`
- `fun ServerConn.wants_close().R: bool`
- `fun ServerConn.close()`
- `fun default_limits().R: Limits`
- `fun Limits.with_timeouts(head_ms: u64, body_ms: u64, idle_ms: u64).R: Limits`
- `fun Limits.dup().R: Limits`
- `fun serve(port: u16, handler: fun(&ServerRequest).R: ServerResponse)`
- `fun serve_n(port: u16, handler: fun(&ServerRequest).R: ServerResponse, max_requests: u64).R: u64`
- `fun serve_on(server: &Server, handler: fun(&ServerRequest).R: ServerResponse, limits: &Limits, max_requests: u64).R: u64`
- `fun serve_threaded(port: u16, handler: fun(&ServerRequest).R: ServerResponse, workers: usize)`
- `fun serve_threaded_on(server: &Server, handler: fun(&ServerRequest).R: ServerResponse, limits: &Limits, workers: usize, idle_ms: u64).R: u64`
- `fun http_error_status(e: &HttpErr).R: i32`
- `fun http_error_text(e: &HttpErr).R: String`

## `std/tls` (needs `net`)

Client and server TLS (MK5-S4b-M1; the server side, ALPN and client certificates are on [`std/tls`](/stdlib/tls#serving-tls), with `ServerOptions`, `ServerConfig`, `TlsClientOptions`, `server_config_pem`, `server_config_pem_with`, `accept`, `try_handshake_opts` and `TlsStream.alpn`/`peer_cert_subject`; `std/tlsfile` has `read_pem` and `ca_pem`, both read through `fs`). Client side for `https`. Never dials or closes a socket
itself: a capability grant is resolved one hop from the importing program's
own `impl` line, so `handshake` takes an already-connected `net.Socket`
instead of calling `net.connect`. Full account on [`std/tls`](/stdlib/tls).

Types:

- `datac TlsStream(val fd: i32, val handle: usize)`
- `pub datac TlsOptions(val ca_pem: Bytes, val timeout_ms: u64)`
- `pub enum TlsError { Untrusted, Expired, HostMismatch, ProtocolTooOld, HandshakeFailed(val reason: String), PeerClosedUncleanly, Timeout, Io(val reason: String) }`

Functions:

- `fun handshake(s: net.Socket, host: &str).R: TlsStream`
- `fun handshake_with(s: net.Socket, host: &str, opts: TlsOptions).R: TlsStream`
- `fun handshake_timeout(s: net.Socket, host: &str, ms: u64).R: TlsStream`
- `fun try_handshake(s: net.Socket, host: &str).R: result.Result<TlsStream, TlsError>`
- `fun try_handshake_with(s: net.Socket, host: &str, opts: TlsOptions).R: result.Result<TlsStream, TlsError>`
- `fun try_handshake_timeout(s: net.Socket, host: &str, ms: u64).R: result.Result<TlsStream, TlsError>`
- `fun set_timeout(t: TlsStream, ms: u64)`
- `fun write(t: TlsStream, data: Bytes).R: usize`
- `fun write_all(t: TlsStream, data: Bytes).R: usize`
- `fun read(t: TlsStream, max: usize).R: Bytes`
- `fun read_into(t: TlsStream, buf: mut Bytes, at: usize).R: usize`
- `fun try_write(t: TlsStream, data: Bytes).R: result.Result<usize, TlsError>`
- `fun try_write_all(t: TlsStream, data: Bytes).R: result.Result<usize, TlsError>`
- `fun try_read(t: TlsStream, max: usize).R: result.Result<Bytes, TlsError>`
- `fun try_read_into(t: TlsStream, buf: mut Bytes, at: usize).R: result.Result<usize, TlsError>`
- `fun shutdown(t: TlsStream)`
- `fun try_shutdown(t: TlsStream).R: result.Result<bool, TlsError>`

## `std/time` (needs `time`)

Functions:

- `fun now_unix().R: i64`
- `fun now_mono_ns().R: i64`
- `fun sleep_ms(ms: u64)`

## `std/source`

Functions:

- `fun file().R: str`
- `fun line().R: usize`

## `std/trace` (needs `time`)

Types:

- `datac Span(val name: String, val start_ns: i64)`

Functions:

- `fun event(file: &str, line: usize, name: &str)`
- `fun begin(file: &str, line: usize, name: &str).R: Span`
- `fun end(file: &str, line: usize, span: Span)`

## `std/tz` (needs `fs` and `env`)

Types:

- `datac Zone(val times: List<i64>, val at_type: List<u8>, val offs: List<i32>, val dsts: List<bool>, val names: List<String>, val default_type: i32, val uniques: List<i32>, val tz: TzString)`
- `datac Offset(val seconds: i32, val abbrev: String, val is_dst: bool)`
- `datac LocalTime(val year: i32, val month: i32, val day: i32, val hour: i32, val minute: i32, val second: i32, val weekday: i32, val yday: i32, val offset: Offset)`
- `enum Resolved`: `One(val unix: i64)`, `Ambiguous(val first: i64, val second: i64)`, `Gap`
- `enum TzErr`: `NotFound`, `Denied`, `Corrupt(val message: String)`

Functions:

- `fun load(name: &str).R: result.Result<Zone, TzErr>`
- `fun load_in(dir: &str, name: &str).R: result.Result<Zone, TzErr>`
- `fun parse(data: move Bytes).R: result.Result<Zone, TzErr>`
- `fun utc().R: Zone`
- `fun fixed(offset_seconds: i32).R: Zone`
- `fun Zone.offset_at(unix_seconds: i64).R: Offset`
- `fun Zone.local_parts(unix_seconds: i64).R: LocalTime`
- `fun Zone.to_unix(y: i32, m: i32, d: i32, h: i32, mi: i32, s: i32).R: Resolved`
- `fun Zone.format(unix_seconds: i64, fmt: &str).R: String`

Hosted only, because it reads a TZif file and `$TZDIR`. Full account on
[`std/tz`](/stdlib/tz).

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
- `fun unwrap_or<T>(o: move Option<T>, fallback: move T).R: T`
- `fun unwrap<T>(o: move Option<T>).R: T`
- `fun expect<T>(o: move Option<T>, message: &str).R: T`
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
- `fun map<T, U, E>(r: move Result<T, E>, f: closure(&T).R: U).R: Result<U, E>`
- `fun map_err<T, E, F>(r: move Result<T, E>, f: closure(&E).R: F).R: Result<T, F>`
- `fun and_then<T, U, E>(r: &Result<T, E>, f: closure(&T).R: Result<U, E>).R: Result<U, E>`
- `fun or_else<T, E, F>(r: &Result<T, E>, f: closure(&E).R: Result<T, F>).R: Result<T, F>`
- `fun each<T, E>(r: &Result<T, E>, f: closure(&T))`

## `std/arena`

Types:

- `datac Arena(var base: Ptr<u8>, val cap: usize, var used: usize)`

Functions:

- `fun new(base: Ptr<u8>, cap: usize).R: Arena`
- `fun Arena.used().R: usize`
- `fun Arena.remaining().R: usize`
- `fun mut Arena.reset()`
- `fun mut Arena.alloc(size: usize, align: usize).R: Ptr<u8>`
- `fun mut Arena.alloc_zeroed(size: usize, align: usize).R: Ptr<u8>`

A bump arena over a caller-owned byte region. It allocates nothing, so it works
in a freestanding image and needs no `[target] alloc` pair. On
[`std/arena`](/stdlib/arena).

## `std/irq` (needs `irq`)

Types:

- `datac Line(val n: u32)`

Functions:

- `fun claim(n: u32).R: Line`
- `fun Line.number().R: u32`

An interrupt line as a capability. `claim` is the only constructor and its
argument is checked against the calling module's `irq` grant, so the `Line` is
the receipt for the grant. The constructor is sealed to `std/irq`, so another
module cannot build one. On [`std/irq`](/stdlib/irq).

## `std/frame` (needs `frames`)

Types:

- `datac Frame(val addr: usize)`

Functions:

- `fun claim(addr: usize).R: Frame`
- `fun Frame.addr().R: usize`
- `fun Frame.offset(byte: usize).R: usize`

A physical frame as a capability. `claim` is the only constructor, its argument
must fall inside the calling module's `frames` grant and be 4 KiB-aligned, and
the `Frame` is the receipt for the grant. `offset` is bounds-checked against
the frame's own 4096. On [`std/frame`](/stdlib/frame).

## `std/atomic`

Types:

- `enum Ordering { SeqCst }`

Functions (the `Atomic<T>` methods are compiler builtins rather than
declarations in `std/atomic.kp`; the module declares the `Ordering` type they
take):

- `fun Atomic<T>.new(value: T).R: Atomic<T>`
- `fun Atomic<T>.load(order: Ordering).R: T`
- `fun Atomic<T>.store(value: T, order: Ordering)`
- `fun Atomic<T>.swap(value: T, order: Ordering).R: T`
- `fun Atomic<T>.compare_exchange(current: T, new: T, order: Ordering).R: result.Result<T, T>`
- `fun Atomic<T>.fetch_add(value: T, order: Ordering).R: T`
- `fun Atomic<T>.fetch_sub(value: T, order: Ordering).R: T`
- `fun Atomic<T>.fetch_and(value: T, order: Ordering).R: T`
- `fun Atomic<T>.fetch_or(value: T, order: Ordering).R: T`
- `fun Atomic<T>.fetch_xor(value: T, order: Ordering).R: T`

The element set is `bool` and the integer types, spelled with the names
`AtomicBool`, `AtomicU8`, `AtomicU16`, `AtomicU32`, `AtomicU64`, `AtomicUsize`,
`AtomicI32`, `AtomicI64` and `AtomicIsize`; there is no `AtomicI8`/`AtomicI16`.
The `fetch_*` set exists on the integer instantiations only, never on
`AtomicBool`.

## `std/sync`

`Mutex<T>` guarded access. The three calls are compiler builtins rather than
declarations in `std/sync.kp`; the module exists so a program can name the
surface it is using, and the type is reachable without the import and is
refused in a freestanding project.

- `fun Mutex.new(value: move T).R: Mutex<T>`
- `fun Mutex<T>.lock(block: scoped fun(mut T).R: R).R: R`
- `fun Mutex<T>.into_inner().R: T`

`lock` runs the block while the mutex is held, hands the block `v: mut T`, and
releases the lock on every exit, including a `return` or `?` out of the block; a
panic inside the block releases the lock and poisons the mutex, so a later
`lock` panics with `mutex poisoned`. `into_inner` consumes the mutex. The slot
holds any owned, borrow-free value. The whole surface is on
[`std/sync`](/stdlib/sync).

`RwLock<T>` and `Condvar` are builtins of the same kind:

- `fun RwLock.new(value: move T).R: RwLock<T>`
- `fun RwLock<T>.read(block: scoped fun(&T).R: R).R: R`
- `fun RwLock<T>.write(block: scoped fun(mut T).R: R).R: R`
- `fun RwLock<T>.try_read(block: scoped fun(&T).R: R).R: Option<R>`
- `fun RwLock<T>.try_write(block: scoped fun(mut T).R: R).R: Option<R>`
- `fun RwLock<T>.into_inner().R: T`
- `fun Condvar.new().R: Condvar`
- `fun Condvar.notify_one()`
- `fun Condvar.notify_all()`
- `fun Mutex<T>.wait_while(cv: &Condvar, pred: fun(&T).R: bool, block: scoped fun(mut T).R: R).R: R`
- `fun Mutex<T>.wait_while_timeout(cv: &Condvar, pred: fun(&T).R: bool, millis: i64, block: scoped fun(mut T).R: R).R: Option<R>`

- `fun Mutex<T>.share().R: Mutex<T>`, `fun Condvar.share().R: Condvar`, `fun Mutex<T>.swap(value: move T).R: T`
- `fun sync.bounded<T>(cap: usize).R: (Sender<T>, Receiver<T>)` and `fun sync.unbounded<T>().R: (Sender<T>, Receiver<T>)`
- `fun Sender<T>.send(value: move T).R: option.Option<T>`, `Sender<T>.clone()`
- `fun Receiver<T>.recv().R: result.Result<T, RecvErr>`, `try_recv().R: option.Option<T>`, `recv_timeout(millis: i64).R: result.Result<T, RecvTimeout>`, and `for v in rx`

Channels are written in Kelp in `std/sync` (see [Channels](/stdlib/sync#channels)).

## `std/pool`

- `fun pool.new(workers: i32).R: Pool`
- `fun Pool.spawn(job: move closure())`
- `fun Pool.join()`
- `fun Pool.panicked().R: i32`

Full account on [`std/pool`](/stdlib/pool).

## `std/iter`

- `pub trait Iterator { type Item  fun mut Self.next().R: option.Option<Self::Item> }`
- `pub datac Range(var lo: i64, val hi: i64, val step: i64)`, which implements `Iterator`
- `fun range(a: i64, b: i64).R: Range`
- `fun range_step(a: i64, b: i64, step: i64).R: Range`
- `fun count<I: Iterator>(it: move I).R: usize`
- `fun sum_i64<I: Iterator>(it: move I).R: i64`
- `fun collect_list<I: Iterator>(it: move I).R: List<I::Item>`

The whole surface is on [`std/iter`](/stdlib/iter).

## `std/ops`

Traits, each with one method: `Add`, `Sub`, `Mul`, `Div` and `Rem`
(`fun Self.name(rhs: &Self).R: Self`), `Neg` (`fun Self.neg().R: Self`) and `Ord`
(`fun Self.cmp(other: &Self).R: i32`). The whole surface is on
[`std/ops`](/stdlib/ops).

## `std/convert`

- `pub trait From<T> { fun from(value: T).R: Self }`
- `pub trait Into<T> { fun Self.into().R: T }`

The whole surface is on [`std/convert`](/stdlib/convert).

## `std/thread`

Types:

- `datac ThreadErr(val message: String)`

Functions (`spawn`, `join` and `fence` are compiler builtins rather than
declarations in `std/thread.kp`; `sleep_ms` and `current_id` are ordinary `.kp`
signatures over an `extern fun` body, MK9-S3-M1 stage C2; the module's only
`.kp` declaration is `ThreadErr`, and the `Ordering` the fence takes is
`std/atomic`'s type):

- `fun spawn(entry, arg: move A).R: Thread<T>`
- `fun join(handle: move Thread<T>).R: result.Result<T, ThreadErr>`
- `fun fence(order: Ordering)`
- `fun sleep_ms(ms: u64)`
- `fun current_id().R: u64`

`spawn` and `join` are not in the builtin signature table: what crosses the
thread boundary decides their types, so the checker builds the signature at the
call site. `entry` is a declared `fun`, a `fun` literal or a capturing closure
taking one parameter; `arg` is moved into the worker; and `T` is `entry`'s
return type. `join` consumes the handle, so a handle is joined once, and hands
back `Ok` with the worker's value or `Err` with a `ThreadErr`, whose `message`
is the panic text. `sleep_ms` sleeps the calling thread and takes no
capability, the same as `time.sleep_ms`; `current_id` returns a `u64` stable
for the calling thread's lifetime, backed by `pthread_self`. The whole surface
is on [`std/thread`](/stdlib/thread).

## `std/ws`

Holds `net` for the socket and `rand` for the sixteen bytes of
`Sec-WebSocket-Key` and the masking key of every frame, so an import delegates
both: `impl "std/ws" caps(net = ["host:port"], rand = [])`. The `net` half of
the check is the host-and-port check `net.connect` gives, against the host as
written, before name resolution. `ws.try_connect` is the fallible connect beside
the panicking `ws.connect`: a refused dial comes back as `WsErr.Dial`, a refused
`wss` handshake or certificate check as `WsErr.Tls` and an
answer that is not `101` as `WsErr.Handshake`, while a head that is not HTTP and a
peer that closes mid-handshake still panic, because neither has a status to
report. The scheme comes off a parsed URL in the `connect_url`/`try_connect_url`
spellings, which is what reaches `wss`.

Types:

- `datac Url(val scheme: String, val host: String, val port: u16, val path: String)`
- `datac Header(val name: String, val value: String)`
- `datac Frame(val fin: bool, val opcode: u8, val data: Bytes)`
- `datac Conn(val fd: i32, var buf: Bytes, var start: usize, var frag_opcode: u8, var frag_data: Bytes)`
- `enum WsErr { Dial(val reason: String), Handshake(val status: i32, val reason: String), Tls(val reason: String) }`
- `enum Msg { Text(val text: String), Binary(val data: Bytes), Ping(val data: Bytes), Pong(val data: Bytes), Close(val code: u16, val reason: String) }`

Constants:

- `const DEFAULT_PORT: u16 = 80`
- `const DEFAULT_WSS_PORT: u16 = 443`
- `const DEFAULT_SCHEME: str = "ws"`
- `const WSS_SCHEME: str = "wss"`
- `const WS_GUID: str = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"`
- `const MAX_FRAME: usize = 1048576`
- `const MAX_HEAD: usize = 8192`
- `const OP_CONTINUATION: u8 = 0`
- `const OP_TEXT: u8 = 1`
- `const OP_BINARY: u8 = 2`
- `const OP_CLOSE: u8 = 8`
- `const OP_PING: u8 = 9`
- `const OP_PONG: u8 = 10`
- `const CLOSE_NO_STATUS: u16 = 1005`

Functions:

- `fun parse_url(s: &str).R: Url`
- `fun default_port_for(scheme: &str).R: u16`
- `fun split_authority(rest: &str, scheme: &str).R: Url`
- `fun make_url(authority: String, path: &str, scheme: &str).R: Url`
- `fun parse_port(text: &str).R: u16`
- `fun accept_for(key: &str).R: String`
- `fun with_number(prefix: &str, n: u64, suffix: &str).R: String`
- `fun build_head(scheme: &str, host: &str, port: u16, path: &str, key: &str).R: String`
- `fun find_head_end(b: Bytes).R: usize`
- `fun head_text(b: Bytes, end: usize).R: String`
- `fun name_eq(a: &str, b: &str).R: bool`
- `fun split_head_headers(head: &str).R: List<Header>`
- `fun header_value(hs: List<Header>, name: &str).R: String`
- `fun parse_status(head: &str).R: i32`
- `fun status_code(text: &str).R: i32`
- `fun try_connect(host: &str, port: u16, path: &str).R: result.Result<Conn, WsErr>`
- `fun try_connect_url(u: Url).R: result.Result<Conn, WsErr>`
- `fun try_connect_scheme(scheme: &str, host: &str, port: u16, path: &str).R: result.Result<Conn, WsErr>`
- `fun conn_send_all(fd: i32, tls_handle: option.Option<tls.TlsHandle>, data: Bytes).R: usize`
- `fun conn_recv(fd: i32, tls_handle: option.Option<tls.TlsHandle>, max: usize).R: Bytes`
- `fun conn_recv_into(fd: i32, tls_handle: option.Option<tls.TlsHandle>, buf: mut Bytes, at: usize).R: usize`
- `fun conn_close(fd: i32, tls_handle: option.Option<tls.TlsHandle>)`
- `fun handshake(scheme: &str, fd: i32, tls_handle: move option.Option<tls.TlsHandle>, host: &str, port: u16, path: &str, key_text: &str, expected: &str).R: result.Result<Conn, WsErr>`
- `fun connect_tls(scheme: &str, s: net.Socket, host: &str).R: result.Result<option.Option<tls.TlsHandle>, WsErr>`
- `fun refusal_text(e: move WsErr).R: String`
- `fun fail_connect(e: move WsErr).R: Conn`
- `fun connect(host: &str, port: u16, path: &str).R: Conn`
- `fun connect_url(u: Url).R: Conn`
- `fun connect_scheme(scheme: &str, host: &str, port: u16, path: &str).R: Conn`
- `fun Conn.send_frame(opcode: u8, data: &Bytes)`
- `fun Conn.send_text(text: &str)`
- `fun Conn.send_binary(data: &Bytes)`
- `fun Conn.ping(data: &Bytes)`
- `fun Conn.pong(data: &Bytes)`
- `fun sendable_close_code(code: u16).R: bool`
- `fun Conn.close(code: u16, reason: &str)`
- `fun mut Conn.read_head().R: String`
- `fun mut Conn.read_exact(n: usize).R: Bytes`
- `fun mut Conn.read_frame().R: Frame`
- `fun data_msg(opcode: u8, data: move Bytes).R: Msg`
- `fun close_msg(data: Bytes).R: Msg`
- `fun mut Conn.recv().R: Msg`

`recv` is the message layer: it assembles a text or binary message across as
many continuation frames as the peer sends and returns one `Msg`, and it returns
a `Ping`, a `Pong` or a `Close` rather than answering one. `read_frame` is the
layer under it. The whole surface is on [`std/ws`](/stdlib/ws).

## Modules at a glance

| Module | Functions | Types/constants | Domain |
| --- | ---: | ---: | --- |
| `std/mem` | 1 | 0 | - |
| `std/str` | 37 | 1 | - |
| `std/path` | 12 | 0 | - |
| `std/math` | 29 | 3 | - |
| `std/fmt` | 10 | 1 | - |
| `std/encoding` | 26 | 4 | - |
| `std/regex` | 16 | 4 | - |
| `std/io` | 27 | 3 | - |
| `std/fs` | 30 | 1 | fs |
| `std/process` | 14 | 3 | process |
| `std/net` | 22 | 3 | net |
| `std/http` | 102 | 20 | - |
| `std/tls` | 6 | 1 | net |
| `std/ws` | 32 | 18 | net, rand |
| `std/time` | 3 | 0 | time |
| `std/source` | 2 | 0 | - |
| `std/trace` | 3 | 1 | time |
| `std/tz` | 9 | 5 | fs, env |
| `std/rand` | 3 | 0 | rand |
| `std/env` | 4 | 0 | env |
| `std/list` | 6 | 0 | - |
| `std/option` | 9 | 1 | - |
| `std/result` | 12 | 1 | - |
| `std/arena` | 6 | 1 | - |
| `std/atomic` | 10 | 1 | - |
| `std/thread` | 5 | 1 | - |
| `std/iter` | 5 | 2 | - |
| `std/ops` | 0 | 7 | - |
| `std/convert` | 0 | 2 | - |

## Not part of the stdlib surface

`std/rt` holds the capability matcher the compiler uses internally and is excluded from
the shipped list. Its source still ships, and `impl "std/rt"` resolves, because
the differential corpus imports it to compare the matcher with its C reference,
but it is not a library to reach for. The importable glob matcher is
[`glob`](/libraries/glob).

## See also

- [Standard library](/stdlib)
- [Capabilities](/language/capabilities)
- [Capability patterns](/reference/capability-patterns)
