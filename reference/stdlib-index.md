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

- `fun alloc(n: usize).return: Bytes`

## `std/str`

Types:

- `enum ParseErr`

Functions:

- `fun len(s: &str).return: usize`
- `fun byte(s: &str, i: usize).return: u8`
- `fun ptr(s: &str).return: Ptr<u8>`
- `fun is_empty(s: &str).return: bool`
- `fun substring(s: &str, from: usize).return: &str`
- `fun char_count(s: &str).return: usize`
- `fun index_of(s: &str, needle: &str).return: option.Option<usize>`
- `fun starts_with_at(s: &str, needle: &str, at: usize).return: bool`
- `fun starts_with(s: &str, prefix: &str).return: bool`
- `fun ends_with(s: &str, suffix: &str).return: bool`
- `fun contains(s: &str, needle: &str).return: bool`
- `fun eq(a: &str, b: &str).return: bool`
- `fun less(a: &str, b: &str).return: bool`
- `fun is_space(c: u8).return: bool`
- `fun is_digit(c: u8).return: bool`
- `fun trim_start(s: &str).return: &str`
- `fun trim_end(s: &str).return: String`
- `fun prefix(s: &str, n: usize).return: String`
- `fun trim(s: &str).return: String`
- `fun to_upper(s: &str).return: String`
- `fun to_lower(s: &str).return: String`
- `fun repeat(s: &str, n: usize).return: String`
- `fun copy_range(s: &str, from: usize, to: usize).return: String`
- `fun split(s: &str, sep: &str).return: List<String>`
- `fun copy_into(dst: mut Bytes, at: usize, src: &str).return: usize`
- `fun join(parts: List<String>, sep: &str).return: String`
- `fun concat(a: &str, b: &str).return: String`
- `fun from_u64(n: u64).return: String`
- `fun from_i64(n: i64).return: String`
- `fun from_f64(x: f64, decimals: i32).return: String`
- `fun parse_i64(s: &str).return: result.Result<i64, ParseErr>`
- `fun parse_u64(s: &str).return: result.Result<u64, ParseErr>`
- `fun parse_f64(s: &str).return: result.Result<f64, ParseErr>`
- `fun parse_err(s: &str).return: ParseErr`
- `fun replace(s: &str, from: &str, to: &str).return: String`
- `fun byte_index(s: &str, i: usize).return: usize`
- `fun decode_at(s: &str, at: usize).return: u32`
- `fun char_at(s: &str, i: usize).return: u32`

## `std/path`

Functions:

- `fun is_absolute(s: &str).return: bool`
- `fun normalize(s: &str).return: String`
- `fun absolute(base: &str, p: &str).return: String`
- `fun last_sep(s: &str).return: usize`
- `fun file_name(s: &str).return: &str`
- `fun extension(s: &str).return: &str`
- `fun stem(s: &str).return: String`
- `fun has_extension(s: &str, ext: &str).return: bool`
- `fun split(s: &str).return: List<String>`
- `fun join_all(parts: List<String>).return: String`
- `fun parent(s: &str).return: String`
- `fun join(a: &str, b: &str).return: String`

## `std/sys`

Functions:

- `fun os().return: str`
- `fun arch().return: str`

## `std/math`

Constants:

- `const PI: f64`
- `const E: f64`
- `const TAU: f64`

Functions:

- `fun sqrt(x: f64).return: f64`
- `fun pow(base: f64, exp: f64).return: f64`
- `fun floor(x: f64).return: f64`
- `fun ceil(x: f64).return: f64`
- `fun round(x: f64).return: f64`
- `fun trunc(x: f64).return: f64`
- `fun exp(x: f64).return: f64`
- `fun ln(x: f64).return: f64`
- `fun log2(x: f64).return: f64`
- `fun log10(x: f64).return: f64`
- `fun sin(x: f64).return: f64`
- `fun cos(x: f64).return: f64`
- `fun tan(x: f64).return: f64`
- `fun atan2(y: f64, x: f64).return: f64`
- `fun is_nan(x: f64).return: bool`
- `fun is_finite(x: f64).return: bool`
- `fun sign(x: f64).return: f64`
- `fun abs(x: i32).return: i32`
- `fun abs(x: i64).return: i64`
- `fun abs(x: f64).return: f64`
- `fun min(a: i32, b: i32).return: i32`
- `fun min(a: i64, b: i64).return: i64`
- `fun min(a: f64, b: f64).return: f64`
- `fun max(a: i32, b: i32).return: i32`
- `fun max(a: i64, b: i64).return: i64`
- `fun max(a: f64, b: f64).return: f64`
- `fun clamp(x: i32, lo: i32, hi: i32).return: i32`
- `fun clamp(x: i64, lo: i64, hi: i64).return: i64`
- `fun clamp(x: f64, lo: f64, hi: f64).return: f64`
- `fun sqrt(x: f32).return: f32`
- `fun floor(x: f32).return: f32`
- `fun ceil(x: f32).return: f32`
- `fun round(x: f32).return: f32`
- `fun trunc(x: f32).return: f32`
- `fun exp(x: f32).return: f32`
- `fun ln(x: f32).return: f32`
- `fun log2(x: f32).return: f32`
- `fun log10(x: f32).return: f32`
- `fun sin(x: f32).return: f32`
- `fun cos(x: f32).return: f32`
- `fun tan(x: f32).return: f32`
- `fun pow(base: f32, exp: f32).return: f32`
- `fun atan2(y: f32, x: f32).return: f32`
- `fun is_nan(x: f32).return: bool`
- `fun is_finite(x: f32).return: bool`
- `fun sign(x: f32).return: f32`
- `fun abs(x: f32).return: f32`
- `fun min(a: f32, b: f32).return: f32`
- `fun max(a: f32, b: f32).return: f32`
- `fun clamp(x: f32, lo: f32, hi: f32).return: f32`

## `std/fmt`

Types:

- `trait Display`

Functions:

- `fun int(n: i64).return: String`
- `fun uint(n: u64).return: String`
- `fun float(x: f64, decimals: i32).return: String`
- `fun hex(n: u64).return: String`
- `fun bytes(b: Bytes).return: String`
- `fun pad_left(s: &str, width: usize, fill: u8).return: String`
- `fun pad_right(s: &str, width: usize, fill: u8).return: String`
- `fun commas_u64(n: u64).return: String`
- `fun commas_i64(n: i64).return: String`
- `fun group_digits(text: &str).return: String`
- `fun human_size(bytes: u64).return: String`
- `fun human_scale(bytes: u64, div: u64, unit: &str).return: String`

## `std/encoding`

Types:

- `enum DecodeErr`

Functions:

- `fun base64_encode(data: &Bytes).return: String`
- `fun base64_decode(text: &str).return: result.Result<Bytes, DecodeErr>`
- `fun base32_encode(data: &Bytes).return: String`
- `fun base32_decode(text: &str).return: result.Result<Bytes, DecodeErr>`
- `fun base58_encode(data: &Bytes).return: String`
- `fun base58_decode(text: &str).return: result.Result<Bytes, DecodeErr>`
- `fun hex_upper(nibble: u8).return: u8`
- `fun hex_lower(nibble: u8).return: u8`
- `fun hex_value(c: u8).return: option.Option<u8>`
- `fun hex_encode(data: &Bytes).return: String`
- `fun hex_decode(text: &str).return: result.Result<Bytes, DecodeErr>`
- `fun dump(data: &Bytes).return: String`
- `fun percent_encode(text: &str).return: String`
- `fun percent_decode(text: &str).return: result.Result<String, DecodeErr>`
- `fun sha1(data: &Bytes).return: Bytes`
- `fun form_encode(text: &str).return: String`
- `fun form_decode(text: &str).return: result.Result<String, DecodeErr>`

## `std/regex`

Types:

- `datac RegexErr(val message: String, val offset: usize)`
- `datac Match(val start: usize, val end: usize, val text: String)`
- `datac Captures(val text: String, val slots: List<i32>)`
- `datac Regex(`

Functions:

- `fun compile(pattern: &str).return: result.Result<Regex, RegexErr>`
- `fun Regex.steps().return: i64`
- `fun mut Regex.reset_steps()`
- `fun Regex.group_count().return: usize`
- `fun mut Regex.is_match(text: &str).return: bool`
- `fun mut Regex.find_at(text: &str, start: usize).return: option.Option<Match>`
- `fun mut Regex.find(text: &str).return: option.Option<Match>`
- `fun mut Regex.captures(text: &str).return: option.Option<Captures>`
- `fun mut Regex.find_all(text: &str).return: List<Match>`
- `fun mut Regex.replace(text: &str, replacement: &str).return: String`
- `fun mut Regex.replace_all(text: &str, replacement: &str).return: String`
- `fun mut Regex.split(text: &str).return: List<String>`
- `fun is_match(pattern: &str, text: &str).return: bool`

## `std/io`

Types:

- `datac IoErr(val errno: i32, val message: String)`
- `datac File(val fd: i32)`
- `datac BufReader(val file: File, var buf: Bytes, var start: usize, var end: usize)`

Functions:

- `fun errno_text(errno: i32).return: String`
- `fun File.is_open().return: bool`
- `fun File.read(max: usize).return: Bytes`
- `fun File.read_into(buf: mut Bytes, at: usize).return: usize`
- `fun File.read_all().return: Bytes`
- `fun File.write(data: Bytes).return: usize`
- `fun File.write_text(text: String).return: usize`
- `fun File.write_str(text: &str).return: usize`
- `fun File.flush()`
- `fun File.close()`
- `fun mut File.set_nonblocking(on: bool)`
- `fun File.wait_readable(timeout_ms: u64).return: bool`
- `fun File.wait_writable(timeout_ms: u64).return: bool`
- `fun stdin().return: File`
- `fun stdout().return: File`
- `fun stderr().return: File`
- `fun buf_reader(f: File).return: BufReader`
- `fun mut BufReader.read_line_into(out: mut String).return: bool`
- `fun mut BufReader.read_line().return: option.Option<String>`
- `fun mut BufReader.read_all().return: Bytes`
- `fun read_line().return: option.Option<String>`
- `fun read_lines().return: List<String>`
- `fun read_all().return: Bytes`
- `fun print(s: &str)`
- `fun print_bare(s: &str)`
- `fun eprint(s: &str)`
- `fun eprint_bare(s: &str)`

## `std/fs`

Types:

- `datac Metadata(val size: u64, val mtime: i64, val mode: u32, val is_dir: bool, val is_file: bool)`

Functions:

- `fun read(path: &str).return: Bytes`
- `fun try_read(path: &str).return: result.Result<Bytes, io.IoErr>`
- `fun read_text(path: &str).return: String`
- `fun try_read_text(path: &str).return: result.Result<String, io.IoErr>`
- `fun write(path: &str, data: Bytes)`
- `fun try_write(path: &str, data: Bytes).return: option.Option<io.IoErr>`
- `fun write_text(path: &str, text: String)`
- `fun try_write_text(path: &str, text: String).return: option.Option<io.IoErr>`
- `fun cwd().return: String`
- `fun exists(path: &str).return: bool`
- `fun is_file(path: &str).return: bool`
- `fun is_dir(path: &str).return: bool`
- `fun is_symlink(path: &str).return: bool`
- `fun read_link(path: &str).return: String`
- `fun size(path: &str).return: u64`
- `fun remove(path: &str)`
- `fun try_remove(path: &str).return: option.Option<io.IoErr>`
- `fun rename(from: &str, to: &str)`
- `fun try_rename(from: &str, to: &str).return: option.Option<io.IoErr>`
- `fun mkdir(path: &str)`
- `fun append(path: &str, data: Bytes)`
- `fun try_append(path: &str, data: Bytes).return: option.Option<io.IoErr>`
- `fun sync(path: &str)`
- `fun list(path: &str).return: List<String>`
- `fun try_list(path: &str).return: result.Result<List<String>, io.IoErr>`
- `fun mkdir_all(path: &str)`
- `fun try_mkdir_all(path: &str).return: option.Option<io.IoErr>`
- `fun remove_all(target: &str)`
- `fun try_remove_all(target: &str).return: option.Option<io.IoErr>`
- `fun walk(dir: &str).return: List<String>`
- `fun copy(from: &str, to: &str)`
- `fun symlink(target: &str, link: &str)`
- `fun try_symlink(target: &str, link: &str).return: option.Option<io.IoErr>`
- `fun touch(path: &str)`
- `fun set_mode(path: &str, mode: u32)`
- `fun open(path: &str, mode: &str).return: io.File`
- `fun try_open(path: &str, mode: &str).return: result.Result<io.File, io.IoErr>`
- `fun read_lines(path: &str).return: List<String>`
- `fun temp_path(prefix: &str).return: String`
- `fun metadata(path: &str).return: Metadata`

## `std/process`

Types:

- `datac Child(`
- `datac RunResult(val code: i32, val signal: i32, val out: Bytes, val err: Bytes)`
- `enum ProcErr`

Functions:

- `fun args().return: List<String>`
- `fun arg_count().return: usize`
- `fun spawn_in(dir: &str, program: &str, args: List<String>).return: Child`
- `fun spawn(program: &str, args: List<String>).return: Child`
- `fun run_in(dir: &str, program: &str, args: List<String>).return: RunResult`
- `fun run(program: &str, args: List<String>).return: RunResult`
- `fun run_inherit_in(dir: &str, program: &str, args: List<String>).return: RunResult`
- `fun run_inherit(program: &str, args: List<String>).return: RunResult`
- `fun executable(program: &str).return: bool`
- `fun try_run_in(dir: &str, program: &str, args: List<String>).return: result.Result<RunResult, ProcErr>`
- `fun try_run(program: &str, args: List<String>).return: result.Result<RunResult, ProcErr>`
- `fun mut Child.wait().return: i32`
- `fun mut Child.is_running().return: bool`
- `fun Child.kill(signal: i32)`
- `fun exit(code: i32)`
- `fun getpid().return: i64`

## `std/net`

Types:

- `datac Socket(val fd: i32)`
- `datac Listener(val fd: i32)`
- `datac ConnectErr(val reason: String)`
- `datac NetErr(val reason: String)`

Functions:

- `fun connect(host: &str, port: u16).return: Socket`
- `fun try_connect(host: &str, port: u16).return: result.Result<Socket, ConnectErr>`
- `fun try_send_all(s: Socket, data: Bytes).return: result.Result<usize, NetErr>`
- `fun try_recv(s: Socket, max: usize).return: result.Result<Bytes, NetErr>`
- `fun try_recv_into(s: Socket, buf: mut Bytes, at: usize).return: result.Result<usize, NetErr>`
- `fun listen(port: u16).return: Listener`
- `fun listen_on(host: &str, port: u16).return: Listener`
- `fun accept(l: Listener).return: Socket`
- `fun try_accept(l: Listener).return: result.Result<Socket, NetErr>`
- `fun mono_ms().return: i64`
- `fun close(s: Socket)`
- `fun Listener.close()`
- `fun shutdown_write(s: Socket)`
- `fun try_shutdown_write(s: Socket).return: bool`
- `fun send(s: Socket, data: Bytes).return: usize`
- `fun send_all(s: Socket, data: Bytes).return: usize`
- `fun send_text(s: Socket, text: &str)`
- `fun recv(s: Socket, max: usize).return: Bytes`
- `fun recv_into(s: Socket, buf: mut Bytes, at: usize).return: usize`
- `fun Socket.wait_readable(timeout_ms: u64).return: bool`
- `fun Socket.wait_writable(timeout_ms: u64).return: bool`
- `fun mut Socket.set_timeout(ms: u64)`
- `fun mut Listener.set_timeout(ms: u64)`
- `fun Listener.port().return: u16`
- `fun Socket.peer_addr().return: String`
- `fun resolve(host: &str).return: List<String>`

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

- `fun Conn.is_tls().return: bool`
- `fun Conn.tls().return: tls.TlsStream`
- `fun parse_url(s: &str).return: Url`
- `fun Response.has_header(name: &str).return: bool`
- `fun Response.header(name: &str).return: String`
- `fun Response.is_ok().return: bool`
- `fun Response.text().return: String`
- `fun Response.retry_after().return: option.Option<u64>`
- `fun Response.rate_limit().return: RateLimit`
- `fun Client.send(req: Request).return: Response`
- `fun Client.try_send(req: Request).return: result.Result<Response, HttpErr>`
- `fun pool(host: &str, port: u16).return: Pool`
- `fun Pool.size().return: usize`
- `fun Pool.len().return: usize`
- `fun mut Pool.warm(use_tls: bool)`
- `fun mut Pool.checkout(use_tls: bool).return: Lease`
- `fun mut Pool.try_checkout(use_tls: bool).return: result.Result<Lease, HttpErr>`
- `fun mut Pool.release(lease: Lease, reusable: bool)`
- `fun mut Pool.close_all()`
- `fun mut Pool.set_idle_timeout(ms: u64)`
- `fun mut Pool.close_idle(after_ms: u64).return: usize`
- `fun mut Pool.send(req: Request).return: Response`
- `fun mut Pool.try_send(req: Request).return: result.Result<Response, HttpErr>`
- `fun Client.try_send_tls(req: Request, opts: &tls.TlsClientOptions).return: result.Result<Response, HttpErr>`
- `fun try_get_tls(url: &str, opts: &tls.TlsClientOptions).return: result.Result<Response, HttpErr>`
- `fun get_tls(url: &str, opts: &tls.TlsClientOptions).return: Response`
- `fun get(url: &str).return: Response`
- `fun try_get(url: &str).return: result.Result<Response, HttpErr>`
- `fun make_get(url: &str).return: Request`
- `fun post_text(url: &str, body: &str, content_type: &str).return: Response`
- `fun multipart(boundary: &str).return: Multipart`
- `fun mut Multipart.add_field(name: &str, value: &str)`
- `fun mut Multipart.add_file(name: &str, filename: &str, content_type: &str, data: Bytes)`
- `fun Multipart.content_type().return: String`
- `fun mut Multipart.finish().return: Bytes`
- `fun multipart_request(url: &str, form: mut Multipart).return: Request`
- `fun Limits.with_timeouts(head_ms: u64, body_ms: u64, idle_ms: u64).return: Limits`
- `fun Limits.dup().return: Limits`
- `fun ServerRequest.header(name: &str).return: String`
- `fun ServerRequest.has_header(name: &str).return: bool`
- `fun ServerRequest.text().return: String`
- `fun ServerRequest.query_param(name: &str).return: option.Option<String>`
- `fun ServerRequest.path_segments().return: List<String>`
- `fun ok_text(text: &str).return: ServerResponse`
- `fun json(text: &str).return: ServerResponse`
- `fun html(text: &str).return: ServerResponse`
- `fun status(code: i32).return: ServerResponse`
- `fun not_found().return: ServerResponse`
- `fun bad_request(message: &str).return: ServerResponse`
- `fun ServerResponse.with_header(name: &str, value: &str).return: ServerResponse`
- `fun mut ServerResponse.add_header(name: &str, value: &str)`
- `fun listen(port: u16).return: Server`
- `fun listen_on(host: &str, port: u16).return: Server`
- `fun Server.port().return: u16`
- `fun Server.set_accept_timeout(ms: u64)`
- `fun Server.close()`
- `fun Server.accept().return: ServerConn`
- `fun Server.try_accept().return: result.Result<ServerConn, HttpErr>`
- `fun http_error_status(e: &HttpErr).return: i32`
- `fun http_error_text(e: &HttpErr).return: String`
- `fun serve(port: u16, handler: fun(&ServerRequest).return: ServerResponse)`
- `fun serve_n(port: u16, handler: fun(&ServerRequest).return: ServerResponse, max_requests: u64).return: u64`
- `fun serve_tls(port: u16, config: &tls.ServerConfig, handler: fun(&ServerRequest).return: ServerResponse)`
- `fun serve_threaded(port: u16, handler: fun(&ServerRequest).return: ServerResponse, workers: usize)`

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

- `fun error_text(e: move TlsError).return: String`
- `fun try_handshake_with(s: net.Socket, host: &str, opts: TlsOptions).return: result.Result<TlsStream, TlsError>`
- `fun try_handshake(s: net.Socket, host: &str).return: result.Result<TlsStream, TlsError>`
- `fun try_handshake_timeout(s: net.Socket, host: &str, ms: u64).return: result.Result<TlsStream, TlsError>`
- `fun handshake(s: net.Socket, host: &str).return: TlsStream`
- `fun handshake_with(s: net.Socket, host: &str, opts: TlsOptions).return: TlsStream`
- `fun handshake_timeout(s: net.Socket, host: &str, ms: u64).return: TlsStream`
- `fun set_timeout(t: TlsStream, ms: u64)`
- `fun try_write(t: TlsStream, data: Bytes).return: result.Result<usize, TlsError>`
- `fun try_write_all(t: TlsStream, data: Bytes).return: result.Result<usize, TlsError>`
- `fun try_read(t: TlsStream, max: usize).return: result.Result<Bytes, TlsError>`
- `fun try_read_into(t: TlsStream, buf: mut Bytes, at: usize).return: result.Result<usize, TlsError>`
- `fun try_shutdown(t: TlsStream).return: result.Result<bool, TlsError>`
- `fun write(t: TlsStream, data: Bytes).return: usize`
- `fun write_all(t: TlsStream, data: Bytes).return: usize`
- `fun read(t: TlsStream, max: usize).return: Bytes`
- `fun read_into(t: TlsStream, buf: mut Bytes, at: usize).return: usize`
- `fun shutdown(t: TlsStream)`
- `fun server_options().return: ServerOptions`
- `fun ServerOptions.min_version(v: TlsVersion).return: ServerOptions`
- `fun ServerOptions.alpn(protocols: &List<String>).return: ServerOptions`
- `fun ServerOptions.require_client_cert_pem(ca_pem: Bytes).return: ServerOptions`
- `fun ServerOptions.handshake_timeout_ms(ms: u64).return: ServerOptions`
- `fun ServerOptions.key_password(phrase: &str).return: ServerOptions`
- `fun server_config_pem(cert_chain_pem: Bytes, key_pem: Bytes).return: result.Result<ServerConfig, TlsError>`
- `fun server_config_pem_with(cert: Bytes, key: Bytes, opts: &ServerOptions).return: result.Result<ServerConfig, TlsError>`
- `fun ServerConfig.reload_pem(cert: Bytes, key: Bytes, opts: &ServerOptions).return: option.Option<TlsError>`
- `fun ServerConfig.free()`
- `fun accept(config: &ServerConfig, s: net.Socket).return: result.Result<TlsStream, TlsError>`
- `fun TlsStream.alpn().return: option.Option<String>`
- `fun TlsStream.peer_cert_subject().return: option.Option<String>`
- `fun client_options().return: TlsClientOptions`
- `fun TlsOptions.to_client().return: TlsClientOptions`
- `fun TlsOptions.alpn(protocols: &List<String>).return: TlsClientOptions`
- `fun TlsOptions.client_cert_pem(cert_pem: Bytes, key_pem: Bytes).return: TlsClientOptions`
- `fun TlsClientOptions.alpn(protocols: &List<String>).return: TlsClientOptions`
- `fun TlsClientOptions.client_cert_pem(cert_pem: Bytes, key_pem: Bytes).return: TlsClientOptions`
- `fun TlsClientOptions.with_ca_pem(pem: Bytes).return: TlsClientOptions`
- `fun TlsClientOptions.with_timeout_ms(ms: u64).return: TlsClientOptions`
- `fun try_handshake_opts(s: net.Socket, host: &str, opts: &TlsClientOptions).return: result.Result<TlsStream, TlsError>`

## `std/tlsfile`

Functions:

- `fun read_pem(path: &str, what: &str).return: result.Result<Bytes, tls.TlsError>`
- `fun ca_pem(path: &str).return: result.Result<Bytes, tls.TlsError>`
- `fun mode_text(mode: u32).return: String`
- `fun read_key(path: &str).return: result.Result<Bytes, tls.TlsError>`

## `std/ws`

Types:

- `datac Conn(`
- `enum WsErr`

Constants:

- `const DEFAULT_PORT: u16`
- `const DEFAULT_WSS_PORT: u16`

Functions:

- `fun parse_url(s: &str).return: Url`
- `fun try_connect(host: &str, port: u16, path: &str).return: result.Result<Conn, WsErr>`
- `fun try_connect_url(u: Url).return: result.Result<Conn, WsErr>`
- `fun try_connect_scheme(scheme: &str, host: &str, port: u16, path: &str).return: result.Result<Conn, WsErr>`
- `fun handshake( scheme: &str, fd: i32, tls_handle: move option.Option<tls.TlsHandle>, host: &str, port: u16, path: &str, key_text: &str, expected: &str, ).return: result.Result<Conn, WsErr>`
- `fun connect(host: &str, port: u16, path: &str).return: Conn`
- `fun connect_url(u: Url).return: Conn`
- `fun connect_scheme(scheme: &str, host: &str, port: u16, path: &str).return: Conn`
- `fun Conn.send_text(text: &str)`
- `fun Conn.send_binary(data: &Bytes)`
- `fun Conn.ping(data: &Bytes)`
- `fun Conn.pong(data: &Bytes)`
- `fun Conn.close(code: u16, reason: &str)`
- `fun mut Conn.read_frame().return: Frame`
- `fun mut Conn.recv().return: Msg`

## `std/time`

Functions:

- `fun now_unix().return: i64`
- `fun now_mono_ns().return: i64`
- `fun sleep_ms(ms: u64)`

## `std/source`

Functions:

- `fun file().return: str`
- `fun line().return: usize`

## `std/trace`

Types:

- `datac Span(val name: String, val start_ns: i64)`

Functions:

- `fun event(file: &str, line: usize, name: &str)`
- `fun begin(file: &str, line: usize, name: &str).return: Span`
- `fun end(file: &str, line: usize, span: Span)`
- `fun emit(kind: &str, file: &str, line: usize, name: &str, elapsed_ns: i64)`
- `fun escape(text: &str).return: String`

## `std/tz`

Types:

- `datac LocalTime(`
- `enum Resolved`
- `enum TzErr`
- `datac Zone(`

Functions:

- `fun parse(data: move Bytes).return: result.Result<Zone, TzErr>`
- `fun load(name: &str).return: result.Result<Zone, TzErr>`
- `fun utc().return: Zone`
- `fun fixed(offset_seconds: i32).return: Zone`
- `fun Zone.offset_at(unix_seconds: i64).return: Offset`
- `fun Zone.local_parts(unix_seconds: i64).return: LocalTime`
- `fun Zone.to_unix(y: i32, m: i32, d: i32, h: i32, mi: i32, s: i32).return: Resolved`
- `fun Zone.format(unix_seconds: i64, fmt: &str).return: String`

## `std/rand`

Functions:

- `fun u64().return: u64`
- `fun below(n: u64).return: u64`
- `fun bytes(n: usize).return: Bytes`

## `std/env`

Functions:

- `fun has(name: &str).return: bool`
- `fun get(name: &str).return: String`
- `fun set(name: &str, value: &str)`
- `fun unset(name: &str)`

## `std/list`

Functions:

- `fun map<T, U>(xs: &List<T>, f: closure(&T).return: U).return: List<U>`
- `fun filter<T>(xs: &List<T>, f: closure(&T).return: bool).return: List<T>`
- `fun each<T>(xs: &List<T>, f: closure(&T))`
- `fun find_index<T>(xs: &List<T>, f: closure(&T).return: bool).return: option.Option<usize>`
- `fun any<T>(xs: &List<T>, f: closure(&T).return: bool).return: bool`
- `fun all<T>(xs: &List<T>, f: closure(&T).return: bool).return: bool`

## `std/option`

Types:

- `enum Option<T>`

Functions:

- `fun is_some<T>(o: &Option<T>).return: bool`
- `fun is_none<T>(o: &Option<T>).return: bool`
- `fun unwrap_or<T>(o: move Option<T>, fallback: move T).return: T`
- `fun unwrap<T>(o: move Option<T>).return: T`
- `fun expect<T>(o: move Option<T>, message: &str).return: T`
- `fun map<T, U>(o: &Option<T>, f: closure(&T).return: U).return: Option<U>`
- `fun and_then<T, U>(o: &Option<T>, f: closure(&T).return: Option<U>).return: Option<U>`
- `fun or_else<T>(o: &Option<T>, f: closure().return: Option<T>).return: Option<T>`
- `fun each<T>(o: &Option<T>, f: closure(&T))`
- `fun Option<T>.is_some().return: bool`
- `fun Option<T>.is_none().return: bool`
- `fun Option<T>.map<U>(f: closure(&T).return: U).return: Option<U>`
- `fun Option<T>.and_then<U>(f: closure(&T).return: Option<U>).return: Option<U>`
- `fun Option<T>.or_else(f: closure().return: Option<T>).return: Option<T>`
- `fun Option<T>.each(f: closure(&T))`

## `std/result`

Types:

- `enum Result<T, E>`

Functions:

- `fun is_ok<T, E>(r: &Result<T, E>).return: bool`
- `fun is_err<T, E>(r: &Result<T, E>).return: bool`
- `fun unwrap_or<T, E>(r: &Result<T, E>, fallback: T).return: T`
- `fun unwrap<T, E>(r: &Result<T, E>).return: T`
- `fun unwrap_err<T, E>(r: &Result<T, E>).return: E`
- `fun expect<T, E>(r: &Result<T, E>, message: &str).return: T`
- `fun expect_err<T, E>(r: &Result<T, E>, message: &str).return: E`
- `fun map<T, U, E>(r: move Result<T, E>, f: closure(&T).return: U).return: Result<U, E>`
- `fun map_err<T, E, F>(r: move Result<T, E>, f: closure(&E).return: F).return: Result<T, F>`
- `fun and_then<T, U, E>(r: &Result<T, E>, f: closure(&T).return: Result<U, E>).return: Result<U, E>`
- `fun or_else<T, E, F>(r: &Result<T, E>, f: closure(&E).return: Result<T, F>).return: Result<T, F>`
- `fun each<T, E>(r: &Result<T, E>, f: closure(&T))`
- `fun Result<T, E>.is_ok().return: bool`
- `fun Result<T, E>.is_err().return: bool`
- `fun Result<T, E>.and_then<U>(f: closure(&T).return: Result<U, E>).return: Result<U, E>`
- `fun Result<T, E>.or_else<F>(f: closure(&E).return: Result<T, F>).return: Result<T, F>`
- `fun Result<T, E>.each(f: closure(&T))`

## `std/arena`

Types:

- `datac Arena(var base: Ptr<u8>, val cap: usize, var used: usize)`

Functions:

- `fun new(base: Ptr<u8>, cap: usize).return: Arena`
- `fun Arena.used().return: usize`
- `fun Arena.remaining().return: usize`
- `fun mut Arena.reset()`
- `fun mut Arena.alloc(size: usize, align: usize).return: Ptr<u8>`
- `fun mut Arena.alloc_zeroed(size: usize, align: usize).return: Ptr<u8>`

## `std/irq`

Types:

- `datac Line(val n: u32)`

Functions:

- `fun claim(n: u32).return: Line`
- `fun Line.number().return: u32`

## `std/frame`

Types:

- `datac Frame(val addr: usize)`

Functions:

- `fun claim(addr: usize).return: Frame`
- `fun Frame.addr().return: usize`
- `fun Frame.offset(byte: usize).return: usize`

## `std/atomic`

Types:

- `enum Ordering`

## `std/thread`

Types:

- `datac ThreadErr(val message: String)`

Functions:

- `fun sleep_ms(ms: u64)`
- `fun current_id().return: u64`

Checker builtins, declared in a comment in the module and not as functions:
`thread.spawn(entry, arg)`, `thread.join(handle)` and `thread.fence(order)`.

## `std/sync`

Types:

- `enum RecvErr`
- `enum RecvTimeout`
- `datac Sender<T>(val q: Mutex<List<T>>, val end: SendEnd)`
- `datac Receiver<T>(val q: Mutex<List<T>>, val end: RecvEnd)`

Functions:

- `fun bounded<T>(cap: usize).return: (Sender<T>, Receiver<T>)`
- `fun unbounded<T>().return: (Sender<T>, Receiver<T>)`
- `fun Sender<T>.send(value: move T).return: option.Option<T>`
- `fun Sender<T>.clone().return: Sender<T>`
- `fun Receiver<T>.recv().return: result.Result<T, RecvErr>`
- `fun Receiver<T>.try_recv().return: option.Option<T>`
- `fun Receiver<T>.recv_timeout(millis: i64).return: result.Result<T, RecvTimeout>`
- `fun mut Receiver<T>.next().return: option.Option<T>`

`Mutex<T>`, `RwLock<T>` and `Condvar` are compiler builtins with no declaration in
this module. Their methods are listed in the Compiler builtins table of the
[Standard library](/stdlib) chapter.

## `std/pool`

Types:

- `datac Pool(val shared: PoolShared)`

Functions:

- `fun new(workers: i32).return: Pool`
- `fun Pool.spawn(job: move closure())`
- `fun Pool.join()`
- `fun Pool.panicked().return: i32`

## `std/iter`

Types:

- `trait Iterator`
- `datac Range(var lo: i64, val hi: i64, val step: i64)`
- `datac ListIter<T>(var rest: List<T>)`
- `datac MapIter<I, T, U>(var inner: I, val f: closure(&T).return: U)`
- `datac FilterIter<I, T>(var inner: I, val pred: closure(&T).return: bool)`
- `datac TakeIter<I, T>(var inner: I, var left: usize)`
- `datac SkipIter<I, T>(var inner: I, var left: usize)`
- `datac EnumerateIter<I, T>(var inner: I, var index: usize)`
- `datac ZipIter<A, B, T, U>(var left: A, var right: B)`
- `datac ChainIter<A, B, T>(var first: A, var second: B, var first_done: bool)`

Functions:

- `fun range(a: i64, b: i64).return: Range`
- `fun range_step(a: i64, b: i64, step: i64).return: Range`
- `fun count<I: Iterator>(it: move I).return: usize`
- `fun sum_i64<I: Iterator>(it: move I).return: i64`
- `fun collect_list<I: Iterator>(it: move I).return: List<I::Item>`
- `fun mut ListIter<T>.next().return: option.Option<T>`
- `fun into_iter<T>(xs: move List<T>).return: ListIter<T>`
- `fun cloned<T>(xs: &List<T>).return: ListIter<T>`
- `fun mut MapIter<I, T, U>.next().return: option.Option<U>`
- `fun map<I: Iterator, U>(it: move I, f: move closure(&I::Item).return: U).return: MapIter<I, I::Item, U>`
- `fun mut FilterIter<I, T>.next().return: option.Option<T>`
- `fun filter<I: Iterator>(it: move I, pred: move closure(&I::Item).return: bool).return: FilterIter<I, I::Item>`
- `fun mut TakeIter<I, T>.next().return: option.Option<T>`
- `fun take<I: Iterator>(it: move I, n: usize).return: TakeIter<I, I::Item>`
- `fun mut SkipIter<I, T>.next().return: option.Option<T>`
- `fun skip<I: Iterator>(it: move I, n: usize).return: SkipIter<I, I::Item>`
- `fun mut EnumerateIter<I, T>.next().return: option.Option<(usize, T)>`
- `fun enumerate<I: Iterator>(it: move I).return: EnumerateIter<I, I::Item>`
- `fun mut ZipIter<A, B, T, U>.next().return: option.Option<(T, U)>`
- `fun zip<A: Iterator, B: Iterator>(a: move A, b: move B).return: ZipIter<A, B, A::Item, B::Item>`
- `fun mut ChainIter<A, B, T>.next().return: option.Option<T>`
- `fun chain<A: Iterator, B: Iterator>(a: move A, b: move B).return: ChainIter<A, B, A::Item>`
- `fun any<I: Iterator>(it: move I, pred: closure(&I::Item).return: bool).return: bool`
- `fun all<I: Iterator>(it: move I, pred: closure(&I::Item).return: bool).return: bool`
- `fun find<I: Iterator>(it: move I, pred: closure(&I::Item).return: bool).return: option.Option<I::Item>`
- `fun last<I: Iterator>(it: move I).return: option.Option<I::Item>`
- `fun fold<I: Iterator, A>(it: move I, init: move A, f: closure(&A, &I::Item).return: A).return: A`

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
