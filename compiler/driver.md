---
title: "Driver"
description: "The kelpc command dispatch, the steps of a build, how the final binary is linked with ld.lld, and the exact shape of diagnostics. Diagnostics have no source excerpt and no caret."
isPublished: true
tags: "compiler"
---
The driver is the part of `kelpc` that reads the command line, runs the passes in order, calls the external tools and prints diagnostics.
This page covers the command dispatch, the build steps, linking and the diagnostic format.

## Subcommands

`real_main` dispatches on the first argument.
`main` runs it on a thread with a 512 MiB stack, because the compiler's frames for a deeply nested tree need more than the 8 MiB main-thread stack.

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
- `<out>.externs.o` when the program has a user `extern fun` or a capability-gated call;
- `<out>.units/` with `--incremental`;
- `index.html` when `coral.toml` sets `[build] emit = "html"`.

`run` executes the binary after the build.
With `emit = "html"` it writes `index.html` and does not start the program as an application.

## Linking

Every hosted link runs `ld.lld` directly. Nothing runs `cc` to link a program.

Every hosted program also gets `RUNPATH` set to `$ORIGIN/lib`, which is the last `-rpath` in the link line. A `.ckp` package keeps the libraries it bundles in `lib/` beside the executable, so the program finds them without an environment variable. The loader expands `$ORIGIN`. The RUNPATH applies to the libraries the program needs directly. A bundled library that another bundled library needs is found through `LD_LIBRARY_PATH`, which `coral run` sets as a fallback.

The program records the standard x86_64 dynamic loader, `/lib64/ld-linux-x86-64.so.2`, as its interpreter when the loader found on the build host is that same file. A distro's own path (for example GCC's `/usr/lib/gcc/x86_64-linux-gnu/13/../../../...`, or `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`) is recorded in canonical form. A binary built on one distro then starts on the others in the release matrix.

The base set, which a package never bundles because the host supplies it, is `ld-linux-x86-64.so.2`, `libc.so.6`, `libm.so.6`, `libpthread.so.0`, `libdl.so.2`, `librt.so.1` and `libgcc_s.so.1`.

A hosted build is the managed link, and every hosted build takes it. `driver::link_managed_object` links, in this order: the program's object, the embedded runtime object `kelp_rt_managed.o`, the program's `extern fun` object when there is one, the collector archive `libkelp_gc.a`, the libraries the manifest names, and `-ldl`. `driver::link_llvm_objects_with_archive` writes the runtime object to a temporary file, and the collector archive too when it is the embedded copy, runs `ld.lld` with the argument list from `sysroot::hosted_link_argv`, and removes the temporary files.

The collector archive is found by `driver::managed_archive`. `KELP_GC_LIB` names a file when it is set, and that file must exist, or the build fails before any code is written. Otherwise the archive is the copy `kelpc/build.rs` built from `kelpc/gc` and `include_bytes!` embeds in `kelpc`, so a `kelpc` binary needs no build tree and no environment variable.

The argument list uses `-m elf_x86_64`, `-pie`, the glibc dynamic loader and the glibc start files.
It adds the program object, the runtime object, the optional externs object, the collector archive, the library directories, `-lm -lpthread`, and `-lssl -lcrypto` when TLS is used.
It ends with `-lgcc -lgcc_s -lc`, with `--as-needed`.
The x86_64 ELF layout and glibc are fixed in this list. A hosted build for another target is not covered.

No C compiler runs for a hosted build, and no `.c` file is written.
The embedded archive `libkelp_rt.a` is still in the binary, for a link without a collector. No hosted build takes that path.
When the program has a user `extern fun` or a capability-gated call, kelpc writes the trampolines, the native-callback glue and the allowlist arrays as LLVM IR into `<out>.externs.o`, with the same target machine as the program's own object (`extern_object.rs`).
The stdlib's `extern fun` bodies are Rust exports in `kelp-rt`, so a program that uses `fs`, `net`, `process`, `env`, `time` or `rand` needs no C compiler either.

`pkg-config` runs for each `[extern."<id>"]` package that names one.

`kelpc` runs `cc -print-file-name` once, when `kelpc` itself is built (`kelpc/build.rs`), to record the glibc, gcc and OpenSSL directories. A program build does not run it.

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
`SourceMap::report_as` and `render_at` print it in this form:

```text
error: <message>
  --> <file path>:<line>:<column>
  help: <a fix, when the compiler has one>
  note: <note message>
  --> <note file path>:<line>:<column>
```

- The label is `error: `, `warning: ` or `outdated: `.
- A `help: ` line, when there is one, follows the primary location and names a fix.
- Each note is printed after the primary location, with the `note: ` prefix and its own location line.
- Line and column are 1-based.
  The column counts Unicode characters from the start of the line, and a tab counts as one.
- An empty module name prints the message only.

There is no source excerpt and no caret under the error.
The line and column are the only location information.

`kelpc check --json` uses `render_json`.
Each finding is an object with `severity`, `message`, `module`, `file`, `line`, `column`, `end_line`, `end_column` and `notes`, and a `help` key when the finding has a next step.
The end position is exclusive.

The lexer and the parser report only their first error for each module.
Type checking and borrow checking also stop at the first error they find.

## See also

- [Pipeline](/compiler/architecture)
- [Backends](/compiler/backends)
- [kelpc CLI](/tooling/kelpc-cli)
- [Install and build](/getting-started/install)
