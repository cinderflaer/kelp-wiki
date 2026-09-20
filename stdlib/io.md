---
title: "`std/io`"
description: "Files as descriptors, buffered reading, and the print/read helpers. Ungated. std/io wraps descriptors, and it is std/fs that is gated on opening a path. A File handed to you by process or net..."
isPublished: true
tags: "stdlib"
---
Files as descriptors, buffered reading, and the print/read helpers. **Ungated.** `std/io` wraps descriptors, and it is `std/fs` that is gated on opening a path.
A `File` handed to you by `process` or `net` needs no capability.

```kelp
impl "std/io"
```

## Standard descriptors

| Function | Returns |
| --- | --- |
| `io.stdin()` / `io.stdout()` / `io.stderr()` | `File` over fd 0 / 1 / 2 |

## `File`

```kelp
datac File(val fd: i32)
```

| Method | Returns | Notes |
| --- | --- | --- |
| `is_open()` | `bool` | |
| `read(max: usize)` | `Bytes` | up to `max` bytes; empty at end of file |
| `read_into(buf: mut Bytes, at: usize)` | `usize` | reads into an existing buffer |
| `read_all()` | `Bytes` | to end of file |
| `write(data: Bytes)` | `usize` | |
| `write_text(text: String)` | `usize` | takes ownership of the text |
| `write_str(text: &str)` | `usize` | |
| `flush()` | `Unit` | |
| `close()` | `Unit` | |
| `set_nonblocking(on: bool)` | `Unit` | `mut` receiver |
| `wait_readable(timeout_ms: u64)` / `wait_writable(...)` | `bool` | readiness without blocking indefinitely |

## Reading lines

| Function | Returns | Notes |
| --- | --- | --- |
| `io.buf_reader(f: File)` | `BufReader` | |
| `BufReader.read_line_into(out: mut String)` | `bool` | fills `out`, `false` at EOF |
| `BufReader.read_line()` | `option.Option<String>` | `None` at EOF |
| `BufReader.read_all()` | `Bytes` | |
| `io.read_line()` | `option.Option<String>` | one line from stdin |
| `io.read_lines()` | `List<String>` | every line of stdin |
| `io.read_all()` | `Bytes` | all of stdin |

## Printing

| Function | Writes |
| --- | --- |
| `io.print(s: &str)` | the text and a newline, to stdout |
| `io.print_bare(s: &str)` | the text, no newline |
| `io.eprint(s: &str)` | the text and a newline, to stderr |
| `io.eprint_bare(s: &str)` | the text, no newline |

These take a `str`, so a `String` needs `.as_str()`. The builtin `print`/`print!`
handle scalars and templates; these two are for text you have already built.

```kelp
impl "std/io"

fun main() {
    io.print("to stdout")
    io.print_bare("no newline")
    io.print("")
    io.eprint("to stderr")

    val out = io.stdout()
    print(out.write_str("written through File\n"))
    out.flush()
}
```

## Errors

```kelp
datac IoErr(val errno: i32, val message: String)
```

A failed syscall, as a value: the POSIX `errno` and its text. `errno` is 0 when
the failure is not a syscall at all (a file that is not valid UTF-8), and
`message` is then the whole story. The fallible `fs` functions return it
([`fs.try_read`](/stdlib/fs) and friends), and `io.errno_text(errno)` turns any
number into its text, so `errno_text(13)` is `"Permission denied"`.

## Notes

- A `File` is a raw descriptor: `File(fd = 3)` is whatever the program happens to
  have open at 3. Nothing here validates that, and nothing here closes a
  descriptor you did not open.
- `read` returns **empty** `Bytes` at end of file, which is how the
  [`lineproto`](/libraries/lineproto) reader detects a closed peer.
- Reading and writing do not allocate a buffer per call: `read_all` grows one.
- There is no `fopen` mode here: opening by path is `fs.open(path, mode)`, which
  needs the `fs` grant. See [`std/fs`](/stdlib/fs).

## See also

- [`std/fs`](/stdlib/fs) for opening a path
- [`std/process`](/stdlib/process) for a child's pipes
- [`std/net`](/stdlib/net) for sockets
