---
title: "Driver"
description: "The kelpc command dispatch, the steps of a build, how the final binary is linked with cc or ld.lld, and the exact shape of diagnostics. Diagnostics have no source excerpt and no caret."
isPublished: true
tags: "compiler"
---
The driver is the part of `kelpc` that reads the command line, runs the passes in order, calls the external tools and prints diagnostics.
This page covers the command dispatch, the build steps, linking and the diagnostic format.

## Subcommands

`real_main` (`main.rs:1531`) dispatches on the first argument.
`main` runs it on a thread with a 512 MiB stack (`main.rs:1516` to `1518`).

| Command | What it does |
| --- | --- |
| `build` | Compiles a file or project to a binary, and the files written beside it. |
| `run` | Builds the same way, then runs the binary and passes its exit status through. |
| `check` | Runs the front end and the borrow checker. No code is generated. |
| `fmt` | Formats source. `-w` rewrites files, and `--check` only reports. |
| `lint` | Prints warnings for style rules. It never writes. |
| `doc` | Writes documentation from `///` and `//!` comments. |
| `cache` | Shows or clears the incremental object cache. |
| `version` | Prints the release. `--verbose` adds the commit, the build date and the tool versions. |

There is no `stdlib` subcommand.
`stdlib.rs` is used only by `doc --std`.
The full flag list is on the [kelpc CLI](/tooling/kelpc-cli) page.

## The steps of a build

`build` (`main.rs:428`) runs these steps in order:

1. Read the flags. `-o` sets the output path, and the default is `build/<stem>`.
   `-O` sets the optimisation level. `-O2` is the default.
2. Choose the backend (`backend::resolve`). See [Backends](/compiler/backends).
3. Load the modules (`resolve::load`). See [Modules and capabilities](/compiler/resolve).
   Deprecation findings are reported here.
4. Type check (`infer::check_program`).
5. For a freestanding target, check the allowed set, prune the program and type check it again.
6. Check borrows and build the drop plan (`borrowck::check_program`).
7. Refuse the combinations that have no codegen path, such as freestanding with the C backend.
8. Run `pkg-config` once for all `[extern.*]` packages (`driver::pkg_config_flags`).
9. Generate code and link. The LLVM path is `codegen_llvm::compile` (`main.rs:616`).

The LLVM path writes `<out>.ll`, verifies the module, optimises it, writes `<out>.o`, and links.
The C path writes `<out>.c` and compiles it with `cc`.

Beside the binary, a build may write these files:

- `<out>.ll` and `<out>.o` for the LLVM backend, or `<out>.c` for the C backend;
- `<out>.externs.c` and `<out>.externs.o` when the program has `extern fun` bodies;
- `<out>.units/` with `--incremental`;
- `index.html` when `coral.toml` sets `[build] emit = "html"`.

`run` executes the binary after the build.
With `emit = "html"` it writes `index.html` and does not start the program as an application.

## Linking

The hosted LLVM link is `link_llvm_objects` (`driver.rs:273` to `348`).
It runs `cc` with this argument order:

```text
cc -O<level> -o <out> <unit or program .o> <runtime .o> -pthread [<externs .o>] -lm -L<dirs> <pkg-config flags> [-lssl -lcrypto] -l<lib>...
```

- The runtime object is `kelp_rt.o`, compiled by `build.rs` from `runtime/kelp_rt.c` and embedded in `kelpc` (`driver.rs:12`).
  The driver writes it to a temporary file named `kelp_rt_<pid>_<n>.o` in the system temp directory and removes it after the link.
  If `cc` cannot be started, the file is left behind, because the removal comes after that step.
- `-lssl -lcrypto` is added when the program uses TLS.
- `-fwrapv` is not passed on this link. A comment in `driver.rs` says the LLVM IR already wraps on overflow.

The C backend links with `cc -O<level> -o <out> <out>.c -fwrapv -pthread -lm` (`driver.rs:70` to `154`), with extra flags for sanitizers, include paths and libraries.

The freestanding link is different.
`link_freestanding_object` (`driver.rs:361` to `388`) runs `ld.lld` with the manifest's linker script and `--static`.
It does not run `cc`, and it does not link libc or the runtime object.
`ld.lld` is found on `PATH`.
A missing `ld.lld` is an error, and the driver does not fall back to `cc`.

`cc` also finds the C runtime start files and libc on the hosted path.
kelpc does not search for them.

`src/sysroot.rs` has code that would find `ld.lld`, the crt files, libc and the dynamic loader, and build a hosted `ld.lld` line.
Nothing calls it.
The file has `#![allow(dead_code)]`, so it is not on the build's path.

`driver.rs:16` also embeds `libkelp_rt.a`, the archive built from the Rust port in `kelp-rt/`.
The archive is embedded but not linked.
See [Runtime](/compiler/runtime#the-rust-port-kelp-rt).

## The memory guard

`build` and `run` start a watchdog (`guard.rs`).
It reads `MemAvailable` from `/proc/meminfo` every 200 ms.
When the free memory falls below `KELPC_MIN_AVAILABLE_MB` (default 384, `0` turns it off), it kills the child processes that kelpc started and exits with status 75.
It exits with `_exit` because the main thread may be inside LLVM.

`run` stops the guard before the program starts, so the program's own memory use is not limited by it.

## Diagnostics

Each diagnostic is a message, a module id and a byte span.
`SourceMap::report_as` and `render_at` (`diag.rs:200` to `213`) print it in this form:

```text
error: <message>
  --> <file path>:<line>:<column>
  note: <note message>
  --> <note file path>:<line>:<column>
```

- The label is `error: `, `warning: ` or `outdated: `.
- Each note is printed after the primary location, with the `note: ` prefix and its own location line.
- Line and column are 1-based.
  The column counts Unicode characters from the start of the line, and a tab counts as one.
- An empty module name prints the message only.

There is no source excerpt and no caret under the error.
The line and column are the only location information.

`kelpc check --json` uses `render_json` (`diag.rs:242`).
Each finding is an object with `severity`, `message`, `module`, `file`, `line`, `column`, `end_line`, `end_column` and `notes`.
The end position is exclusive.

The lexer and the parser report only their first error for each module.
Type checking and borrow checking also stop at the first error they find.

## See also

- [Pipeline](/compiler/architecture)
- [Backends](/compiler/backends)
- [kelpc CLI](/tooling/kelpc-cli)
- [Install and build](/getting-started/install)
