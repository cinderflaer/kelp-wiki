---
title: "`std/os`"
description: "The target, the process, the environment and the machine a program runs on, and temporary directories and files that clean up after themselves. Gated per item on env, machine and fs."
isPublished: true
tags: "stdlib"
---
The facts a program needs about the system it runs on, and the temporary
directories and files it makes for itself. Some items need no grant, and the
rest are gated per item: the table below says which.

```kelp
impl "std/os" caps(env = ["APP_*"], machine = [], fs = ["/tmp/**"])

fun main() {
    print(os.hostname())
    os.set_env_var("APP_MODE", "test")
    val template = str.concat(os.temp_dir(), "/app-XXXXXX")
    val made = os.make_temp_dir(template)
    let Ok(dir) = &made else { panic("no directory") }
    print(dir.path())
}
```

## Which items need a grant

| Items | Grant | What the grant names |
| --- | --- | --- |
| `os()`, `arch()` | none | the build target, fixed at build time |
| `pid()`, `parent_pid()`, `exe_path()`, `current_dir()`, `set_current_dir(path)`, `exit(code)` | none | this process |
| `cpu_count()`, `total_memory()` | none | the machine's processors and memory |
| `env_var(name)`, `set_env_var(name, value)`, `unset_env_var(name)` | `env` | the variable name, matched like `std/env` |
| `hostname()`, `user_name()`, `home_dir()`, `temp_dir()`, `uid()`, `gid()` | `machine` | no pattern: the grant is the domain |
| `make_temp_dir(template)`, `make_temp_file(template)`, and the drop of what they return | `fs` | the template, checked at the call |
| `TempDir.path()`, `TempFile.path()` | none | the path the module already made |

`machine` is a domain of its own, like `time` and `rand`. A machine fact is not
an environment variable, so reading it under `env` would let a grant of
`NO_COLOR` read the host name. `home_dir` and `temp_dir` read `HOME` and
`TMPDIR`, and the `machine` grant covers those two reads whatever `env` names.

`caps(*)` hands over every one of these domains.

## Target and process

```kelp
impl "std/os"

fun main() {
    if str.eq(os.os(), "linux") {
        print("built for linux on ${os.arch()}")
    }
    print(os.exe_path())
}
```

- `os()` and `arch()` are the names [`std/sys`](/stdlib/sys) also returns.
- `pid()` and `parent_pid()` are `i64`.
- `exe_path()` is the path the kernel reports for the running program.
- `current_dir()` and `set_current_dir(path)` change the process's working
  directory. Every grant pattern is absolute, so no grant changes meaning when
  the directory does.
- `exit(code)` ends the process. Temporary paths that are still registered are
  removed first, as they are on a panic. No destructor runs.
- `cpu_count()` is the number of online processors, at least 1.
- `total_memory()` is the physical memory in bytes, or 0 when it is not reported.

For the program's own arguments, use [`std/process`](/stdlib/process), which
gives `args()` with no grant.

## Environment

```kelp
impl "std/os" caps(env = ["APP_*"])

fun main() {
    os.set_env_var("APP_MODE", "test")
    val mode = os.env_var("APP_MODE")
    let Some(value) = mode else { panic("APP_MODE is unset") }
    print(value)
    os.unset_env_var("APP_MODE")
}
```

`env_var` returns `Option<String>`. Unlike [`std/env`](/stdlib/env), an unset
variable and a variable set to the empty string are different values here.

There is no `env_vars()`. Listing the environment reads every variable, and a
grant that names one variable should not allow that. `std/env` makes the same
decision.

## Machine

- `hostname()` is the host name, or the empty string when it is not known.
- `user_name()` is the name of the user the process runs as, or the empty string.
- `home_dir()` is `HOME`, or the home directory of the user database when `HOME`
  is unset. It is `None` when neither is known.
- `temp_dir()` is `TMPDIR`, or `/tmp` when `TMPDIR` is unset or empty.
- `uid()` and `gid()` are the numeric ids, as `u32`.

## Temporary directories and files

```kelp
impl "std/os" caps(fs = ["/tmp/**"], machine = [])
impl "std/fs" caps(fs = ["/tmp/**"])

fun main() {
    val td = os.temp_dir()
    val template = str.concat(td, "/build-XXXXXX")
    val made = os.make_temp_dir(template)
    let Ok(dir) = &made else { panic("no directory") }
    fs.write_text(str.concat(dir.path(), "/log.txt"), String.from_str("ok"))
    print(fs.is_dir(dir.path()))
}   // dir is dropped here, and the directory and its contents are removed
```

`make_temp_dir(template)` and `make_temp_file(template)` return
`Result<TempDir, OsError>` and `Result<TempFile, OsError>`. The template is the
path to create, and its six trailing `X`s are replaced by a random string, so
two programs do not collide. The template is a path, so it is checked against
the grant at the call, the way [`std/fs`](/stdlib/fs) checks its paths: a caller
whose `fs` grant does not cover the template is refused, whatever `std/os` was
granted. The module's own grant is checked again inside the call, when it has one.

| `OsError` | Meaning |
| --- | --- |
| `BadTemplate` | the template does not end in `XXXXXX` |
| `CreateFailed` | the system refused to create the directory or file |

A `TempDir` or `TempFile` owns its path. Its drop removes the directory with
everything in it, or the file, when the owning scope ends.

A panic runs no destructor, so the runtime keeps a list of the paths it made and
removes them when the process ends by a panic, by `exit`, or by returning from
`main`. A worker thread that panics removes only the paths that thread made.
Each entry records the process that made it, so a child process started with
`std/process` never removes its parent's files.

The drop removes only a path the runtime made in this process. A `TempDir`
built from a string by hand is a value whose drop does nothing.

## Errors

The panicking forms stop the program when the call is outside the grant, with
the usual capability message:

```text
panic: 'HOME' is outside the env capability granted to module 'main'
```

A call with no grant at all does not build. The refusal names the missing
domain and the function, for example `'std.os.hostname' needs the 'machine'
capability`.

## See also

- [`std/sys`](/stdlib/sys): the target names, re-exported from here
- [`std/env`](/stdlib/env): the variable functions this module mirrors
- [`std/process`](/stdlib/process): `args`, `spawn` and `run`
- [`std/fs`](/stdlib/fs): the file functions a temporary path is used with
- [Capability patterns](/reference/capability-patterns): how the grants are written
