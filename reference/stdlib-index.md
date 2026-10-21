---
title: "Standard library index"
description: "Every public name in the shipped standard library, one signature per line, as declared in kelpc/std/ on main. Behaviour and examples live on the module pages."
isPublished: true
tags: "reference"
---
Every public name in the shipped standard library, one signature per line. The
list is taken from `kelpc/std/*.kp` on the main branch, so each line is the
declaration as the compiler reads it. Behaviour, panics and examples are on the
[Standard library](/stdlib) chapter and its module pages.

Left out of this index:

- the `extern` bodies named `*_raw`, which the compiler supplies and no program
  calls directly;
- the plumbing each module uses for itself (the HTTP and WebSocket connection
  and framing steps, the regex parser and compiler, the time-zone file reader,
  the encoding alphabets). These are not documented as API, and the module pages
  do not describe them.

Each module section lists its types first, then its constants, then its
functions. Methods are written as `fun Type.method(...)`, and `mut` marks a
method that takes the receiver by mutable borrow.

A module marked with a domain needs that capability delegated on the `impl` line,
for example `impl "std/fs" caps(fs = ["/srv/data/**"])`. The domain for each
module is in the [Standard library](/stdlib) chapter.

`std/rt` is the compiler's own runtime module, not part of the library surface,
so it has no section here.

## `std/mem`

Functions:

- `fun alloc(n: usize) => Bytes`

## `std/str`

Types:

- `enum ParseErr`

Functions:

- `fun len(s: &str) => usize`
- `fun byte(s: &str, i: usize) => u8`
- `fun ptr(s: &str) => Ptr<u8>`
- `fun is_empty(s: &str) => bool`
- `fun substring(s: &str, from: usize) => &str`
- `fun char_count(s: &str) => usize`
- `fun index_of(s: &str, needle: &str) => option.Option<usize>`
- `fun starts_with_at(s: &str, needle: &str, at: usize) => bool`
- `fun starts_with(s: &str, prefix: &str) => bool`
- `fun ends_with(s: &str, suffix: &str) => bool`
- `fun contains(s: &str, needle: &str) => bool`
- `fun eq(a: &str, b: &str) => bool`
- `fun less(a: &str, b: &str) => bool`
- `fun is_space(c: u8) => bool`
- `fun is_digit(c: u8) => bool`
- `fun trim_start(s: &str) => &str`
- `fun trim_end(s: &str) => String`
- `fun prefix(s: &str, n: usize) => String`
- `fun trim(s: &str) => String`
- `fun to_upper(s: &str) => String`
- `fun to_lower(s: &str) => String`
- `fun repeat(s: &str, n: usize) => String`
- `fun copy_range(s: &str, from: usize, to: usize) => String`
- `fun split(s: &str, sep: &str) => List<String>`
- `fun copy_into(dst: mut Bytes, at: usize, src: &str) => usize`
- `fun join(parts: List<String>, sep: &str) => String`
- `fun concat(a: &str, b: &str) => String`
- `fun from_u64(n: u64) => String`
- `fun from_i64(n: i64) => String`
- `fun from_f64(x: f64, decimals: i32) => String`
- `fun parse_i64(s: &str) => result.Result<i64, ParseErr>`
- `fun parse_u64(s: &str) => result.Result<u64, ParseErr>`
- `fun parse_f64(s: &str) => result.Result<f64, ParseErr>`
- `fun parse_err(s: &str) => ParseErr`
- `fun replace(s: &str, from: &str, to: &str) => String`
- `fun byte_index(s: &str, i: usize) => usize`
- `fun decode_at(s: &str, at: usize) => u32`
- `fun char_at(s: &str, i: usize) => u32`

## `std/path`

Functions:

- `fun is_absolute(s: &str) => bool`
- `fun normalize(s: &str) => String`
- `fun absolute(base: &str, p: &str) => String`
- `fun last_sep(s: &str) => usize`
- `fun file_name(s: &str) => &str`
- `fun extension(s: &str) => &str`
- `fun stem(s: &str) => String`
- `fun has_extension(s: &str, ext: &str) => bool`
- `fun split(s: &str) => List<String>`
- `fun join_all(parts: List<String>) => String`
- `fun parent(s: &str) => String`
- `fun join(a: &str, b: &str) => String`

## `std/sys`

Functions (re-exported from `std/os`, ungated):

- `fun os() => str`
- `fun arch() => str`

## `std/os`

Gated per item (see [`std/os`](/stdlib/os)). Ungated: `os`, `arch`, `pid`, `parent_pid`, `exe_path`, `current_dir`, `set_current_dir`, `exit`, `cpu_count`, `total_memory`, and the `path` of a `TempDir` or `TempFile`.

Functions:

- `fun env_var(name: &str) => option.Option<String>` (`env`)
- `fun set_env_var(name: &str, value: &str)` (`env`)
- `fun unset_env_var(name: &str)` (`env`)
- `fun hostname() => String` (`machine`)
- `fun user_name() => String` (`machine`)
- `fun home_dir() => option.Option<String>` (`machine`)
- `fun temp_dir() => String` (`machine`)
- `fun uid() => u32` (`machine`)
- `fun gid() => u32` (`machine`)
- `fun make_temp_dir(template: &str) => result.Result<TempDir, OsError>` (`fs`, checked against the template)
- `fun make_temp_file(template: &str) => result.Result<TempFile, OsError>` (`fs`, checked against the template)

Types:

- `enum OsError { BadTemplate, CreateFailed }`
- `datac TempDir(val dir: String)` and `datac TempFile(val file: String)`, each with `fun path() => &str` and a drop that removes what it owns

## `std/math`

Constants:

- `const PI: f64`
- `const E: f64`
- `const TAU: f64`

Functions:

- `fun sqrt(x: f64) => f64`
- `fun pow(base: f64, exp: f64) => f64`
- `fun floor(x: f64) => f64`
- `fun ceil(x: f64) => f64`
- `fun round(x: f64) => f64`
- `fun trunc(x: f64) => f64`
- `fun exp(x: f64) => f64`
- `fun ln(x: f64) => f64`
- `fun log2(x: f64) => f64`
- `fun log10(x: f64) => f64`
- `fun sin(x: f64) => f64`
- `fun cos(x: f64) => f64`
- `fun tan(x: f64) => f64`
- `fun atan2(y: f64, x: f64) => f64`
- `fun is_nan(x: f64) => bool`
- `fun is_finite(x: f64) => bool`
- `fun sign(x: f64) => f64`
- `fun abs(x: i32) => i32`
- `fun abs(x: i64) => i64`
- `fun abs(x: f64) => f64`
- `fun min(a: i32, b: i32) => i32`
- `fun min(a: i64, b: i64) => i64`
- `fun min(a: f64, b: f64) => f64`
- `fun max(a: i32, b: i32) => i32`
- `fun max(a: i64, b: i64) => i64`
- `fun max(a: f64, b: f64) => f64`
- `fun clamp(x: i32, lo: i32, hi: i32) => i32`
- `fun clamp(x: i64, lo: i64, hi: i64) => i64`
- `fun clamp(x: f64, lo: f64, hi: f64) => f64`
- `fun sqrt(x: f32) => f32`
- `fun floor(x: f32) => f32`
- `fun ceil(x: f32) => f32`
- `fun round(x: f32) => f32`
- `fun trunc(x: f32) => f32`
- `fun exp(x: f32) => f32`
- `fun ln(x: f32) => f32`
- `fun log2(x: f32) => f32`
- `fun log10(x: f32) => f32`
- `fun sin(x: f32) => f32`
- `fun cos(x: f32) => f32`
- `fun tan(x: f32) => f32`
- `fun pow(base: f32, exp: f32) => f32`
- `fun atan2(y: f32, x: f32) => f32`
- `fun is_nan(x: f32) => bool`
- `fun is_finite(x: f32) => bool`
- `fun sign(x: f32) => f32`
- `fun abs(x: f32) => f32`
- `fun min(a: f32, b: f32) => f32`
- `fun max(a: f32, b: f32) => f32`
- `fun clamp(x: f32, lo: f32, hi: f32) => f32`

## `std/fmt`

Types:

- `trait Display`

Functions:

- `fun int(n: i64) => String`
- `fun uint(n: u64) => String`
- `fun float(x: f64, decimals: i32) => String`
- `fun hex(n: u64) => String`
- `fun bytes(b: Bytes) => String`
- `fun pad_left(s: &str, width: usize, fill: u8) => String`
- `fun pad_right(s: &str, width: usize, fill: u8) => String`
- `fun commas_u64(n: u64) => String`
- `fun commas_i64(n: i64) => String`
- `fun group_digits(text: &str) => String`
- `fun human_size(bytes: u64) => String`
- `fun human_scale(bytes: u64, div: u64, unit: &str) => String`

## `std/encoding`

Types:

- `enum DecodeErr`

Functions:

- `fun base64_encode(data: &Bytes) => String`
- `fun base64_decode(text: &str) => result.Result<Bytes, DecodeErr>`
- `fun base32_encode(data: &Bytes) => String`
- `fun base32_decode(text: &str) => result.Result<Bytes, DecodeErr>`
- `fun base58_encode(data: &Bytes) => String`
- `fun base58_decode(text: &str) => result.Result<Bytes, DecodeErr>`
- `fun hex_upper(nibble: u8) => u8`
- `fun hex_lower(nibble: u8) => u8`
- `fun hex_value(c: u8) => option.Option<u8>`
- `fun hex_encode(data: &Bytes) => String`
- `fun hex_decode(text: &str) => result.Result<Bytes, DecodeErr>`
- `fun dump(data: &Bytes) => String`
- `fun percent_encode(text: &str) => String`
- `fun percent_decode(text: &str) => result.Result<String, DecodeErr>`
- `fun sha1(data: &Bytes) => Bytes`
- `fun form_encode(text: &str) => String`
- `fun form_decode(text: &str) => result.Result<String, DecodeErr>`

## `std/regex`

Types:

- `datac RegexErr(val message: String, val offset: usize)`
- `datac Match(val start: usize, val end: usize, val text: String)`
- `datac Captures(val text: String, val slots: List<i32>)`
- `datac Regex(`

Functions:

- `fun compile(pattern: &str) => result.Result<Regex, RegexErr>`
- `fun Regex.steps() => i64`
- `fun mut Regex.reset_steps()`
- `fun Regex.group_count() => usize`
- `fun mut Regex.is_match(text: &str) => bool`
- `fun mut Regex.find_at(text: &str, start: usize) => option.Option<Match>`
- `fun mut Regex.find(text: &str) => option.Option<Match>`
- `fun mut Regex.captures(text: &str) => option.Option<Captures>`
- `fun mut Regex.find_all(text: &str) => List<Match>`
- `fun mut Regex.replace(text: &str, replacement: &str) => String`
- `fun mut Regex.replace_all(text: &str, replacement: &str) => String`
- `fun mut Regex.split(text: &str) => List<String>`
- `fun is_match(pattern: &str, text: &str) => bool`

## `std/io`

Types:

- `datac IoErr(val errno: i32, val message: String)`
- `datac File(val fd: i32)`
- `datac BufReader(val file: File, var buf: Bytes, var start: usize, var end: usize)`

Functions:

- `fun errno_text(errno: i32) => String`
- `fun File.is_open() => bool`
- `fun File.read(max: usize) => Bytes`
- `fun File.read_into(buf: mut Bytes, at: usize) => usize`
- `fun File.read_all() => Bytes`
- `fun File.write(data: Bytes) => usize`
- `fun File.write_text(text: String) => usize`
- `fun File.write_str(text: &str) => usize`
- `fun File.flush()`
- `fun File.close()`
- `fun mut File.set_nonblocking(on: bool)`
- `fun File.wait_readable(timeout_ms: u64) => bool`
- `fun File.wait_writable(timeout_ms: u64) => bool`
- `fun stdin() => File`
- `fun stdout() => File`
- `fun stderr() => File`
- `fun buf_reader(f: File) => BufReader`
- `fun mut BufReader.read_line_into(out: mut String) => bool`
- `fun mut BufReader.read_line() => option.Option<String>`
- `fun mut BufReader.read_all() => Bytes`
- `fun read_line() => option.Option<String>`
- `fun read_lines() => List<String>`
- `fun read_all() => Bytes`
- `fun print(s: &str)`
- `fun print_bare(s: &str)`
- `fun eprint(s: &str)`
- `fun eprint_bare(s: &str)`

## `std/fs`

Types:

- `datac Metadata(val size: u64, val mtime: i64, val mode: u32, val is_dir: bool, val is_file: bool)`

Functions:

- `fun read(path: &str) => Bytes`
- `fun try_read(path: &str) => result.Result<Bytes, io.IoErr>`
- `fun read_text(path: &str) => String`
- `fun try_read_text(path: &str) => result.Result<String, io.IoErr>`
- `fun write(path: &str, data: Bytes)`
- `fun try_write(path: &str, data: Bytes) => option.Option<io.IoErr>`
- `fun write_text(path: &str, text: String)`
- `fun try_write_text(path: &str, text: String) => option.Option<io.IoErr>`
- `fun cwd() => String`
- `fun exists(path: &str) => bool`
- `fun is_file(path: &str) => bool`
- `fun is_dir(path: &str) => bool`
- `fun is_symlink(path: &str) => bool`
- `fun read_link(path: &str) => String`
- `fun size(path: &str) => u64`
- `fun remove(path: &str)`
- `fun try_remove(path: &str) => option.Option<io.IoErr>`
- `fun rename(from: &str, to: &str)`
- `fun try_rename(from: &str, to: &str) => option.Option<io.IoErr>`
- `fun mkdir(path: &str)`
- `fun append(path: &str, data: Bytes)`
- `fun try_append(path: &str, data: Bytes) => option.Option<io.IoErr>`
- `fun sync(path: &str)`
- `fun list(path: &str) => List<String>`
- `fun try_list(path: &str) => result.Result<List<String>, io.IoErr>`
- `fun mkdir_all(path: &str)`
- `fun try_mkdir_all(path: &str) => option.Option<io.IoErr>`
- `fun remove_all(target: &str)`
- `fun try_remove_all(target: &str) => option.Option<io.IoErr>`
- `fun walk(dir: &str) => List<String>`
- `fun copy(from: &str, to: &str)`
- `fun symlink(target: &str, link: &str)`
- `fun try_symlink(target: &str, link: &str) => option.Option<io.IoErr>`
- `fun touch(path: &str)`
- `fun set_mode(path: &str, mode: u32)`
- `fun open(path: &str, mode: &str) => io.File`
- `fun try_open(path: &str, mode: &str) => result.Result<io.File, io.IoErr>`
- `fun read_lines(path: &str) => List<String>`
- `fun temp_path(prefix: &str) => String`
- `fun metadata(path: &str) => Metadata`

## `std/process`

Types:

- `datac Child(`
- `datac RunResult(val code: i32, val signal: i32, val out: Bytes, val err: Bytes)`
- `enum ProcErr`

Functions:

- `fun args() => List<String>`
- `fun arg_count() => usize`
- `fun spawn_in(dir: &str, program: &str, args: List<String>) => Child`
- `fun spawn(program: &str, args: List<String>) => Child`
- `fun run_in(dir: &str, program: &str, args: List<String>) => RunResult`
- `fun run(program: &str, args: List<String>) => RunResult`
- `fun run_inherit_in(dir: &str, program: &str, args: List<String>) => RunResult`
- `fun run_inherit(program: &str, args: List<String>) => RunResult`
- `fun executable(program: &str) => bool`
- `fun try_run_in(dir: &str, program: &str, args: List<String>) => result.Result<RunResult, ProcErr>`
- `fun try_run(program: &str, args: List<String>) => result.Result<RunResult, ProcErr>`
- `fun mut Child.wait() => i32`
- `fun mut Child.is_running() => bool`
- `fun Child.kill(signal: i32)`
- `fun exit(code: i32)`
- `fun getpid() => i64`

## `std/net`

Types:

- `datac Socket(val fd: i32)`
- `datac Listener(val fd: i32)`
- `datac ConnectErr(val reason: String)`
- `datac NetErr(val reason: String)`

Functions:

- `fun connect(host: &str, port: u16) => Socket`
- `fun try_connect(host: &str, port: u16) => result.Result<Socket, ConnectErr>`
- `fun try_send_all(s: Socket, data: Bytes) => result.Result<usize, NetErr>`
- `fun try_recv(s: Socket, max: usize) => result.Result<Bytes, NetErr>`
- `fun try_recv_into(s: Socket, buf: mut Bytes, at: usize) => result.Result<usize, NetErr>`
- `fun listen(port: u16) => Listener`
- `fun listen_on(host: &str, port: u16) => Listener`
- `fun accept(l: Listener) => Socket`
- `fun try_accept(l: Listener) => result.Result<Socket, NetErr>`
- `fun mono_ms() => i64`
- `fun close(s: Socket)`
- `fun Listener.close()`
- `fun shutdown_write(s: Socket)`
- `fun try_shutdown_write(s: Socket) => bool`
- `fun send(s: Socket, data: Bytes) => usize`
- `fun send_all(s: Socket, data: Bytes) => usize`
- `fun send_text(s: Socket, text: &str)`
- `fun recv(s: Socket, max: usize) => Bytes`
- `fun recv_into(s: Socket, buf: mut Bytes, at: usize) => usize`
- `fun Socket.wait_readable(timeout_ms: u64) => bool`
- `fun Socket.wait_writable(timeout_ms: u64) => bool`
- `fun mut Socket.set_timeout(ms: u64)`
- `fun mut Listener.set_timeout(ms: u64)`
- `fun Listener.port() => u16`
- `fun Socket.peer_addr() => String`
- `fun resolve(host: &str) => List<String>`

## `std/http`

Types:

- `datac Url(val scheme: String, val host: String, val port: u16, val path: String)`
- `datac Header(val name: String, val value: String)`
- `datac Response(val status: i32, val headers: List<Header>, val body: Bytes, val reusable: bool)`
- `datac RateLimit(`
- `datac Request(val method: String, val url: String, val headers: List<Header>, val body: Bytes)`
- `datac Client(val timeout_ms: u64, val max_redirects: i32, val follow_redirects: bool)`
- `enum HttpErr`
- `datac Pool(`
- `datac Lease(val fd: i32, val tls_handle: option.Option<tls.TlsHandle>, val reused: bool)`
- `datac Conn(val fd: i32, val tls_handle: option.Option<tls.TlsHandle>)`
- `datac Multipart(val boundary: String, var out: Bytes, var parts: usize)`
- `datac Limits(`
- `datac ServerRequest(`
- `datac ServerResponse(val status: i32, val headers: List<Header>, val body: Bytes)`
- `datac Server(val fd: i32)`

Constants:

- `const DEFAULT_PORT: u16`
- `const DEFAULT_HTTPS_PORT: u16`
- `const DEFAULT_TIMEOUT_MS: u64`
- `const DEFAULT_MAX_REDIRECTS: i32`

Functions:

- `fun Conn.is_tls() => bool`
- `fun Conn.tls() => tls.TlsStream`
- `fun parse_url(s: &str) => Url`
- `fun Response.has_header(name: &str) => bool`
- `fun Response.header(name: &str) => String`
- `fun Response.is_ok() => bool`
- `fun Response.text() => String`
- `fun Response.retry_after() => option.Option<u64>`
- `fun Response.rate_limit() => RateLimit`
- `fun Client.send(req: Request) => Response`
- `fun Client.try_send(req: Request) => result.Result<Response, HttpErr>`
- `fun pool(host: &str, port: u16) => Pool`
- `fun Pool.size() => usize`
- `fun Pool.len() => usize`
- `fun mut Pool.warm(use_tls: bool)`
- `fun mut Pool.checkout(use_tls: bool) => Lease`
- `fun mut Pool.try_checkout(use_tls: bool) => result.Result<Lease, HttpErr>`
- `fun mut Pool.release(lease: Lease, reusable: bool)`
- `fun mut Pool.close_all()`
- `fun mut Pool.set_idle_timeout(ms: u64)`
- `fun mut Pool.close_idle(after_ms: u64) => usize`
- `fun mut Pool.send(req: Request) => Response`
- `fun mut Pool.try_send(req: Request) => result.Result<Response, HttpErr>`
- `fun Client.try_send_tls(req: Request, opts: &tls.TlsClientOptions) => result.Result<Response, HttpErr>`
- `fun try_get_tls(url: &str, opts: &tls.TlsClientOptions) => result.Result<Response, HttpErr>`
- `fun get_tls(url: &str, opts: &tls.TlsClientOptions) => Response`
- `fun get(url: &str) => Response`
- `fun try_get(url: &str) => result.Result<Response, HttpErr>`
- `fun make_get(url: &str) => Request`
- `fun post_text(url: &str, body: &str, content_type: &str) => Response`
- `fun multipart(boundary: &str) => Multipart`
- `fun mut Multipart.add_field(name: &str, value: &str)`
- `fun mut Multipart.add_file(name: &str, filename: &str, content_type: &str, data: Bytes)`
- `fun Multipart.content_type() => String`
- `fun mut Multipart.finish() => Bytes`
- `fun multipart_request(url: &str, form: mut Multipart) => Request`
- `fun Limits.with_timeouts(head_ms: u64, body_ms: u64, idle_ms: u64) => Limits`
- `fun Limits.dup() => Limits`
- `fun ServerRequest.header(name: &str) => String`
- `fun ServerRequest.has_header(name: &str) => bool`
- `fun ServerRequest.text() => String`
- `fun ServerRequest.query_param(name: &str) => option.Option<String>`
- `fun ServerRequest.path_segments() => List<String>`
- `fun ok_text(text: &str) => ServerResponse`
- `fun json(text: &str) => ServerResponse`
- `fun html(text: &str) => ServerResponse`
- `fun status(code: i32) => ServerResponse`
- `fun not_found() => ServerResponse`
- `fun bad_request(message: &str) => ServerResponse`
- `fun ServerResponse.with_header(name: &str, value: &str) => ServerResponse`
- `fun mut ServerResponse.add_header(name: &str, value: &str)`
- `fun listen(port: u16) => Server`
- `fun listen_on(host: &str, port: u16) => Server`
- `fun Server.port() => u16`
- `fun Server.set_accept_timeout(ms: u64)`
- `fun Server.close()`
- `fun Server.accept() => ServerConn`
- `fun Server.try_accept() => result.Result<ServerConn, HttpErr>`
- `fun http_error_status(e: &HttpErr) => i32`
- `fun http_error_text(e: &HttpErr) => String`
- `fun serve(port: u16, handler: fun(&ServerRequest) => ServerResponse)`
- `fun serve_n(port: u16, handler: fun(&ServerRequest) => ServerResponse, max_requests: u64) => u64`
- `fun serve_tls(port: u16, config: &tls.ServerConfig, handler: fun(&ServerRequest) => ServerResponse)`
- `fun serve_threaded(port: u16, handler: fun(&ServerRequest) => ServerResponse, workers: usize)`

## `std/tls`

Types:

- `datac TlsStream(val fd: i32, val handle: TlsHandle)`
- `enum TlsError`
- `datac TlsOptions(val ca_pem: Bytes, val timeout_ms: u64)`
- `enum TlsVersion`
- `datac ServerOptions(val floor: i32, val alpn_list: Bytes, val ca_pem: Bytes, val timeout_ms: u64, val key_pass: Bytes)`
- `datac ServerConfig(val ctx: TlsCtx, val handshake_timeout_ms: u64)`
- `datac TlsClientOptions(`

Functions:

- `fun error_text(e: move TlsError) => String`
- `fun try_handshake_with(s: net.Socket, host: &str, opts: TlsOptions) => result.Result<TlsStream, TlsError>`
- `fun try_handshake(s: net.Socket, host: &str) => result.Result<TlsStream, TlsError>`
- `fun try_handshake_timeout(s: net.Socket, host: &str, ms: u64) => result.Result<TlsStream, TlsError>`
- `fun handshake(s: net.Socket, host: &str) => TlsStream`
- `fun handshake_with(s: net.Socket, host: &str, opts: TlsOptions) => TlsStream`
- `fun handshake_timeout(s: net.Socket, host: &str, ms: u64) => TlsStream`
- `fun set_timeout(t: TlsStream, ms: u64)`
- `fun try_write(t: TlsStream, data: Bytes) => result.Result<usize, TlsError>`
- `fun try_write_all(t: TlsStream, data: Bytes) => result.Result<usize, TlsError>`
- `fun try_read(t: TlsStream, max: usize) => result.Result<Bytes, TlsError>`
- `fun try_read_into(t: TlsStream, buf: mut Bytes, at: usize) => result.Result<usize, TlsError>`
- `fun try_shutdown(t: TlsStream) => result.Result<bool, TlsError>`
- `fun write(t: TlsStream, data: Bytes) => usize`
- `fun write_all(t: TlsStream, data: Bytes) => usize`
- `fun read(t: TlsStream, max: usize) => Bytes`
- `fun read_into(t: TlsStream, buf: mut Bytes, at: usize) => usize`
- `fun shutdown(t: TlsStream)`
- `fun server_options() => ServerOptions`
- `fun ServerOptions.min_version(v: TlsVersion) => ServerOptions`
- `fun ServerOptions.alpn(protocols: &List<String>) => ServerOptions`
- `fun ServerOptions.require_client_cert_pem(ca_pem: Bytes) => ServerOptions`
- `fun ServerOptions.handshake_timeout_ms(ms: u64) => ServerOptions`
- `fun ServerOptions.key_password(phrase: &str) => ServerOptions`
- `fun server_config_pem(cert_chain_pem: Bytes, key_pem: Bytes) => result.Result<ServerConfig, TlsError>`
- `fun server_config_pem_with(cert: Bytes, key: Bytes, opts: &ServerOptions) => result.Result<ServerConfig, TlsError>`
- `fun ServerConfig.reload_pem(cert: Bytes, key: Bytes, opts: &ServerOptions) => option.Option<TlsError>`
- `fun ServerConfig.free()`
- `fun accept(config: &ServerConfig, s: net.Socket) => result.Result<TlsStream, TlsError>`
- `fun TlsStream.alpn() => option.Option<String>`
- `fun TlsStream.peer_cert_subject() => option.Option<String>`
- `fun client_options() => TlsClientOptions`
- `fun TlsOptions.to_client() => TlsClientOptions`
- `fun TlsOptions.alpn(protocols: &List<String>) => TlsClientOptions`
- `fun TlsOptions.client_cert_pem(cert_pem: Bytes, key_pem: Bytes) => TlsClientOptions`
- `fun TlsClientOptions.alpn(protocols: &List<String>) => TlsClientOptions`
- `fun TlsClientOptions.client_cert_pem(cert_pem: Bytes, key_pem: Bytes) => TlsClientOptions`
- `fun TlsClientOptions.with_ca_pem(pem: Bytes) => TlsClientOptions`
- `fun TlsClientOptions.with_timeout_ms(ms: u64) => TlsClientOptions`
- `fun try_handshake_opts(s: net.Socket, host: &str, opts: &TlsClientOptions) => result.Result<TlsStream, TlsError>`

## `std/tlsfile`

Functions:

- `fun read_pem(path: &str, what: &str) => result.Result<Bytes, tls.TlsError>`
- `fun ca_pem(path: &str) => result.Result<Bytes, tls.TlsError>`
- `fun mode_text(mode: u32) => String`
- `fun read_key(path: &str) => result.Result<Bytes, tls.TlsError>`

## `std/ws`

Types:

- `datac Conn(`
- `enum WsErr`

Constants:

- `const DEFAULT_PORT: u16`
- `const DEFAULT_WSS_PORT: u16`

Functions:

- `fun parse_url(s: &str) => Url`
- `fun try_connect(host: &str, port: u16, path: &str) => result.Result<Conn, WsErr>`
- `fun try_connect_url(u: Url) => result.Result<Conn, WsErr>`
- `fun try_connect_scheme(scheme: &str, host: &str, port: u16, path: &str) => result.Result<Conn, WsErr>`
- `fun handshake( scheme: &str, fd: i32, tls_handle: move option.Option<tls.TlsHandle>, host: &str, port: u16, path: &str, key_text: &str, expected: &str, ) => result.Result<Conn, WsErr>`
- `fun connect(host: &str, port: u16, path: &str) => Conn`
- `fun connect_url(u: Url) => Conn`
- `fun connect_scheme(scheme: &str, host: &str, port: u16, path: &str) => Conn`
- `fun Conn.send_text(text: &str)`
- `fun Conn.send_binary(data: &Bytes)`
- `fun Conn.ping(data: &Bytes)`
- `fun Conn.pong(data: &Bytes)`
- `fun Conn.close(code: u16, reason: &str)`
- `fun mut Conn.read_frame() => Frame`
- `fun mut Conn.recv() => Msg`

## `std/time`

Functions:

- `fun now_unix() => i64`
- `fun now_mono_ns() => i64`
- `fun sleep_ms(ms: u64)`

## `std/source`

Functions:

- `fun file() => str`
- `fun line() => usize`

## `std/trace`

Types:

- `datac Span(val name: String, val start_ns: i64)`

Functions:

- `fun event(file: &str, line: usize, name: &str)`
- `fun begin(file: &str, line: usize, name: &str) => Span`
- `fun end(file: &str, line: usize, span: Span)`
- `fun emit(kind: &str, file: &str, line: usize, name: &str, elapsed_ns: i64)`
- `fun escape(text: &str) => String`

## `std/tz`

Types:

- `datac LocalTime(`
- `enum Resolved`
- `enum TzErr`
- `datac Zone(`

Functions:

- `fun parse(data: move Bytes) => result.Result<Zone, TzErr>`
- `fun load(name: &str) => result.Result<Zone, TzErr>`
- `fun utc() => Zone`
- `fun fixed(offset_seconds: i32) => Zone`
- `fun Zone.offset_at(unix_seconds: i64) => Offset`
- `fun Zone.local_parts(unix_seconds: i64) => LocalTime`
- `fun Zone.to_unix(y: i32, m: i32, d: i32, h: i32, mi: i32, s: i32) => Resolved`
- `fun Zone.format(unix_seconds: i64, fmt: &str) => String`

## `std/rand`

Functions:

- `fun u64() => u64`
- `fun below(n: u64) => u64`
- `fun bytes(n: usize) => Bytes`

## `std/env`

Functions:

- `fun has(name: &str) => bool`
- `fun get(name: &str) => String`
- `fun set(name: &str, value: &str)`
- `fun unset(name: &str)`

## `std/list`

Functions:

- `fun map<T, U>(xs: &List<T>, f: closure(&T) => U) => List<U>`
- `fun filter<T>(xs: &List<T>, f: closure(&T) => bool) => List<T>`
- `fun each<T>(xs: &List<T>, f: closure(&T))`
- `fun find_index<T>(xs: &List<T>, f: closure(&T) => bool) => option.Option<usize>`
- `fun any<T>(xs: &List<T>, f: closure(&T) => bool) => bool`
- `fun all<T>(xs: &List<T>, f: closure(&T) => bool) => bool`

## `std/option`

Types:

- `enum Option<T>`

Functions:

- `fun is_some<T>(o: &Option<T>) => bool`
- `fun is_none<T>(o: &Option<T>) => bool`
- `fun unwrap_or<T>(o: move Option<T>, fallback: move T) => T`
- `fun unwrap<T>(o: move Option<T>) => T`
- `fun expect<T>(o: move Option<T>, message: &str) => T`
- `fun map<T, U>(o: &Option<T>, f: closure(&T) => U) => Option<U>`
- `fun and_then<T, U>(o: &Option<T>, f: closure(&T) => Option<U>) => Option<U>`
- `fun or_else<T>(o: &Option<T>, f: closure() => Option<T>) => Option<T>`
- `fun each<T>(o: &Option<T>, f: closure(&T))`
- `fun Option<T>.is_some() => bool`
- `fun Option<T>.is_none() => bool`
- `fun Option<T>.map<U>(f: closure(&T) => U) => Option<U>`
- `fun Option<T>.and_then<U>(f: closure(&T) => Option<U>) => Option<U>`
- `fun Option<T>.or_else(f: closure() => Option<T>) => Option<T>`
- `fun Option<T>.each(f: closure(&T))`

## `std/result`

Types:

- `enum Result<T, E>`

Functions:

- `fun is_ok<T, E>(r: &Result<T, E>) => bool`
- `fun is_err<T, E>(r: &Result<T, E>) => bool`
- `fun unwrap_or<T, E>(r: &Result<T, E>, fallback: T) => T`
- `fun unwrap<T, E>(r: &Result<T, E>) => T`
- `fun unwrap_err<T, E>(r: &Result<T, E>) => E`
- `fun expect<T, E>(r: &Result<T, E>, message: &str) => T`
- `fun expect_err<T, E>(r: &Result<T, E>, message: &str) => E`
- `fun map<T, U, E>(r: move Result<T, E>, f: closure(&T) => U) => Result<U, E>`
- `fun map_err<T, E, F>(r: move Result<T, E>, f: closure(&E) => F) => Result<T, F>`
- `fun and_then<T, U, E>(r: &Result<T, E>, f: closure(&T) => Result<U, E>) => Result<U, E>`
- `fun or_else<T, E, F>(r: &Result<T, E>, f: closure(&E) => Result<T, F>) => Result<T, F>`
- `fun each<T, E>(r: &Result<T, E>, f: closure(&T))`
- `fun Result<T, E>.is_ok() => bool`
- `fun Result<T, E>.is_err() => bool`
- `fun Result<T, E>.and_then<U>(f: closure(&T) => Result<U, E>) => Result<U, E>`
- `fun Result<T, E>.or_else<F>(f: closure(&E) => Result<T, F>) => Result<T, F>`
- `fun Result<T, E>.each(f: closure(&T))`

## `std/arena`

Types:

- `datac Arena(var base: Ptr<u8>, val cap: usize, var used: usize)`

Functions:

- `fun new(base: Ptr<u8>, cap: usize) => Arena`
- `fun Arena.used() => usize`
- `fun Arena.remaining() => usize`
- `fun mut Arena.reset()`
- `fun mut Arena.alloc(size: usize, align: usize) => Ptr<u8>`
- `fun mut Arena.alloc_zeroed(size: usize, align: usize) => Ptr<u8>`

## `std/irq`

Types:

- `datac Line(val n: u32)`

Functions:

- `fun claim(n: u32) => Line`
- `fun Line.number() => u32`

## `std/frame`

Types:

- `datac Frame(val addr: usize)`

Functions:

- `fun claim(addr: usize) => Frame`
- `fun Frame.addr() => usize`
- `fun Frame.offset(byte: usize) => usize`

## `std/atomic`

Types:

- `enum Ordering`

## `std/thread`

Types:

- `datac ThreadErr(val message: String)`

Functions:

- `fun sleep_ms(ms: u64)`
- `fun current_id() => u64`

Checker builtins, declared in a comment in the module and not as functions:
`thread.spawn(entry, arg)`, `thread.join(handle)` and `thread.fence(order)`.

## `std/sync`

Types:

- `enum RecvErr`
- `enum RecvTimeout`
- `datac Sender<T>(val q: Mutex<List<T>>, val end: SendEnd)`
- `datac Receiver<T>(val q: Mutex<List<T>>, val end: RecvEnd)`

Functions:

- `fun bounded<T>(cap: usize) => (Sender<T>, Receiver<T>)`
- `fun unbounded<T>() => (Sender<T>, Receiver<T>)`
- `fun Sender<T>.send(value: move T) => option.Option<T>`
- `fun Sender<T>.clone() => Sender<T>`
- `fun Receiver<T>.recv() => result.Result<T, RecvErr>`
- `fun Receiver<T>.try_recv() => option.Option<T>`
- `fun Receiver<T>.recv_timeout(millis: i64) => result.Result<T, RecvTimeout>`
- `fun mut Receiver<T>.next() => option.Option<T>`

`Mutex<T>`, `RwLock<T>` and `Condvar` are compiler builtins with no declaration in
this module. Their methods are listed in the Compiler builtins table of the
[Standard library](/stdlib) chapter.

## `std/pool`

Types:

- `datac Pool(val shared: PoolShared)`

Functions:

- `fun new(workers: i32) => Pool`
- `fun Pool.spawn(job: move closure())`
- `fun Pool.join()`
- `fun Pool.panicked() => i32`

## `std/iter`

Types:

- `trait Iterator`
- `datac Range(var lo: i64, val hi: i64, val step: i64)`
- `datac ListIter<T>(var rest: List<T>)`
- `datac MapIter<I, T, U>(var inner: I, val f: closure(&T) => U)`
- `datac FilterIter<I, T>(var inner: I, val pred: closure(&T) => bool)`
- `datac TakeIter<I, T>(var inner: I, var left: usize)`
- `datac SkipIter<I, T>(var inner: I, var left: usize)`
- `datac EnumerateIter<I, T>(var inner: I, var index: usize)`
- `datac ZipIter<A, B, T, U>(var left: A, var right: B)`
- `datac ChainIter<A, B, T>(var first: A, var second: B, var first_done: bool)`

Functions:

- `fun range(a: i64, b: i64) => Range`
- `fun range_step(a: i64, b: i64, step: i64) => Range`
- `fun count<I: Iterator>(it: move I) => usize`
- `fun sum_i64<I: Iterator>(it: move I) => i64`
- `fun collect_list<I: Iterator>(it: move I) => List<I::Item>`
- `fun mut ListIter<T>.next() => option.Option<T>`
- `fun into_iter<T>(xs: move List<T>) => ListIter<T>`
- `fun cloned<T>(xs: &List<T>) => ListIter<T>`
- `fun mut MapIter<I, T, U>.next() => option.Option<U>`
- `fun map<I: Iterator, U>(it: move I, f: move closure(&I::Item) => U) => MapIter<I, I::Item, U>`
- `fun mut FilterIter<I, T>.next() => option.Option<T>`
- `fun filter<I: Iterator>(it: move I, pred: move closure(&I::Item) => bool) => FilterIter<I, I::Item>`
- `fun mut TakeIter<I, T>.next() => option.Option<T>`
- `fun take<I: Iterator>(it: move I, n: usize) => TakeIter<I, I::Item>`
- `fun mut SkipIter<I, T>.next() => option.Option<T>`
- `fun skip<I: Iterator>(it: move I, n: usize) => SkipIter<I, I::Item>`
- `fun mut EnumerateIter<I, T>.next() => option.Option<(usize, T)>`
- `fun enumerate<I: Iterator>(it: move I) => EnumerateIter<I, I::Item>`
- `fun mut ZipIter<A, B, T, U>.next() => option.Option<(T, U)>`
- `fun zip<A: Iterator, B: Iterator>(a: move A, b: move B) => ZipIter<A, B, A::Item, B::Item>`
- `fun mut ChainIter<A, B, T>.next() => option.Option<T>`
- `fun chain<A: Iterator, B: Iterator>(a: move A, b: move B) => ChainIter<A, B, A::Item>`
- `fun any<I: Iterator>(it: move I, pred: closure(&I::Item) => bool) => bool`
- `fun all<I: Iterator>(it: move I, pred: closure(&I::Item) => bool) => bool`
- `fun find<I: Iterator>(it: move I, pred: closure(&I::Item) => bool) => option.Option<I::Item>`
- `fun last<I: Iterator>(it: move I) => option.Option<I::Item>`
- `fun fold<I: Iterator, A>(it: move I, init: move A, f: closure(&A, &I::Item) => A) => A`

## `std/ops`

Types:

- `trait Add`
- `trait Sub`
- `trait Mul`
- `trait Div`
- `trait Rem`
- `trait Neg`
- `trait Ord`

## `std/convert`

Types:

- `trait From<T>`
- `trait Into<T>`

## See also

- [Standard library](/stdlib): the module pages, with behaviour and examples
- [Capability patterns](/reference/capability-patterns): the grant grammar for each domain
