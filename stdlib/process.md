---
title: "`std/process`"
description: "Arguments, children, and exiting. Gated on process."
isPublished: true
tags: "stdlib"
---
Arguments, children, and exiting. **Gated on `process`.**

```kelp
impl "std/process"                                      // argv only needs the empty grant
impl "std/process" caps(process = ["/usr/bin/curl"]) // spawn/run need a pattern
```

`process` patterns are absolute program paths, matched the same way `fs` paths
are: normalized, symlinks resolved. Reading `argv` needs no pattern: the empty
grant (`caps(process = [])`) is enough to name `process.args`, because there
is no resource argument to match.

## Types

```kelp
datac RunResult(val code: i32, val out: Bytes, val err: Bytes)

enum ProcErr {
    NotFound        // no such program
    NotExecutable   // present, but not executable
    DirNotFound     // the working directory does not exist
}

datac Child(
    val pid: i32,
    val stdin: io.File,
    val stdout: io.File,
    val stderr: io.File,
    var exited: bool,
    var code: i32,
)
```

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `args()` | `List<String>` | this process's argv, **including `argv[0]`** |
| `arg_count()` | `usize` | |
| `spawn(program, args)` | `Child` | pipes for all three streams |
| `spawn_in(dir, program, args)` | `Child` | with a working directory; `""` keeps the parent's |
| `run(program, args)` | `RunResult` | runs to completion, collects both streams; panics if it cannot start |
| `run_in(dir, program, args)` | `RunResult` | |
| `try_run(program, args)` | `result.Result<RunResult, ProcErr>` | the fallible form |
| `try_run_in(dir, program, args)` | `result.Result<RunResult, ProcErr>` | |
| `executable(program)` | `bool` | |
| `Child.wait()` | `i32` | exit code; `mut` receiver |
| `Child.is_running()` | `bool` | `mut` receiver |
| `Child.kill(signal: i32)` | `Unit` | |
| `exit(code: i32)` | — | ends the process with that status |
| `getpid()` | `i64` | |

`args` does **not** include the program itself: the child's argv is its own.

## Example

```kelp
impl "std/process"

fun main() {
    val argv = process.args()
    print(argv.len())            // at least 1: argv[0] is the program path

    var argv_tail: List<String> = List.empty()
    var i: usize = 1
    while i < argv.len() {
        argv_tail.push(argv.get(i).clone())
        i += 1
    }
    print(argv_tail.len())

    val res = process.run("/bin/echo", argv_tail)
    print(res.code)
    print(res.out.as_str())
    print(process.executable("/bin/echo"))
    print(process.executable("/nope/nope"))

    val bad = process.try_run("/nope/nope", argv_tail)
    print(result.is_err(bad))
}
```

## Notes

- `run` collects both streams into `Bytes`; read them with `.as_str()`. There is
  no streaming form other than `spawn` plus the `Child` pipes.
- A `Child` is not reaped automatically: call `wait()`, or `is_running()` to poll.
- `kill` takes a POSIX signal number.
- `try_run` decides everything it can (missing program, not executable, missing
  working directory) **before** the fork, which is why `ProcErr` has that
  particular shape.
- An exit code of a killed child is the signal-based value the OS reports, not a
  synthesized one.

## See also

- [`std/io`](/stdlib/io) for the pipes
- [Capability patterns](/reference/capability-patterns)
