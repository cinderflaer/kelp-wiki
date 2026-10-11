---
title: "Driver"
description: "The kelpc command dispatch, the steps of a build, how the final binary is linked with ld.lld, and the exact shape of diagnostics. Diagnostics have no source excerpt and no caret."
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

`stdlib --json --dir <dir>` writes the std sources and a JSON listing.
`doc --std` documents the shipped std modules.
The full flag list is on the [kelpc CLI](/tooling/kelpc-cli) page.

## The steps of a build

`build` runs these steps in order:

1. Read the flags. `-o` sets the output path, and the default is `build/<stem>`.
   `-O` sets the optimisation level. `-O2` is the default.
2. Refuse the retired code generator selectors. `--backend`, `KELPC_BACKEND` and `KELPC_ORACLE` are refused by name.
   The LLVM backend is the only code generator. See [Backends](/compiler/backends).
3. Load the modules (`resolve::load`). See [Modules and capabilities](/compiler/resolve).
   Deprecation findings are reported here.
4. Type check (`infer::check_program`).
5. For a freestanding target, check the allowed set, prune the program and type check it again.
6. Check borrows and build the drop plan (`borrowck::check_program`).
7. Refuse the flags that have no code path, such as `--sanitize`. There are no sanitizer passes.
8. Run `pkg-config` once for all `[extern.*]` packages (`driver::pkg_config_flags`).
9. Generate code and link. The LLVM path is `codegen_llvm::compile`.

The LLVM path writes `<out>.ll`, verifies the module, optimises it, writes `<out>.o`, and links.

Beside the binary, a build may write these files:

- `<out>.ll` and `<out>.o` for the LLVM backend;
- `<out>.externs.c` and `<out>.externs.o` when the program has `extern fun` bodies or a capability-gated call;
- `<out>.units/` with `--incremental`;
- `index.html` when `coral.toml` sets `[build] emit = "html"`.

`run` executes the binary after the build.
With `emit = "html"` it writes `index.html` and does not start the program as an application.

## Linking

The hosted link runs `ld.lld` directly. The link does not run `cc`.
`driver::link_llvm_objects_with_archive` writes the embedded runtime archive `libkelp_rt.a` to a temporary file.
It then runs `ld.lld` with the argument list from `sysroot::hosted_link_argv`, and removes the temporary file.

The argument list uses `-m elf_x86_64`, `-pie`, the glibc dynamic loader and the glibc start files.
It adds the program object, the runtime archive, the optional externs object, the library directories, `-lm -lpthread`, and `-lssl -lcrypto` when TLS is used.
It ends with `-lgcc -lgcc_s -lc`, with `--as-needed`.
The x86_64 ELF layout and glibc are fixed in this list. A hosted build for another target is not covered.

`cc` still runs for one object. When the program has an `extern fun` or a capability-gated call, kelpc writes `<out>.externs.c` and compiles it with `cc -O<level> -fwrapv`.
That object holds the `extern fun` bodies and the capability glue.
So a program that uses `fs`, `net`, `process`, `env`, `time` or `rand`, or any `extern` in std, needs a C compiler.

`pkg-config` runs for each `[extern."<id>"]` package that names one.

The managed link (`[target] mode = "managed"`) links the runtime object `kelp_rt_managed.o` in place of the archive.
It adds the collector archive named by `KELP_GC_LIB` after the program's objects.

The freestanding link is different.
`link_freestanding_object` runs `ld.lld` with the manifest's linker script and `--static`.
It does not run `cc`, and it does not link libc or a runtime archive.
A missing `ld.lld` is an error, and the driver does not fall back to `cc`.

`ld.lld` is found through `KELPC_LLD`, then `PATH`.

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
