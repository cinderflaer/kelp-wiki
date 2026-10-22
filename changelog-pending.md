---
title: "Pending changes"
description: "Changes that are in kelp but not in a released version yet. The release procedure reads this page; it replaces plan/CHANGELOG.pending.md."
isPublished: true
tags: "changelog, release"
---
> **Moved 2026-10-16.** This page replaces `plan/CHANGELOG.pending.md` in the kelp repository, which is removed. The release procedure now reads this page, not the kelp repository. Add a line here for every user-visible change, and wipe the lines back to this header when a version is released.

# Pending changes

Scratch file for changes that are not released yet. It lives on this page now: an edit here is the edit, and the wiki sync carries it.

Add a line here when a user-visible change lands in `kelp`. **Do not touch
`wiki/changelog.md` until a version is released**: the changelog page carries
releases only.

When a version drops, write that release's entry in `wiki/changelog.md` from
this file plus the tag's commits and the Gitea release body, then wipe this file
back to this header. No need to ask first.

Keep each line short and factual: what changed, and why it matters to someone
writing Kelp. Group under the headings below; delete the headings that stay
empty on release.

## added

- A `.ckp` package runs on any machine whose glibc is at least the one its files need. `build --package` bundles every library the executable and its files need, except the glibc family and `libgcc_s` (the base set), into `lib/`, and it refuses a package that needs `libstdc++` by name. `llvm-readelf` must be on `PATH` to build a package.
- A `.ckp` manifest has a `[requires]` table: `glibc` (the highest `GLIBC_x.y` any file references), `gcc_runtime`, `libstdcxx` (always `none`), `libc` (`glibc`) and `bundled` (the files under `lib/`). `coral inspect` prints them and a `host` line for the machine it runs on.
- `coral run` and `coral inspect` refuse a package whose `requires glibc` is newer than the host's glibc, or that has no glibc, before anything is unpacked. The reason is printed on standard error and the exit status is 1.
- A manual memory block, `block name: T { ... }`, frees its values when the block ends, on every exit (`return`, `break`, `continue`, `?`). Inside it, `name.box()?` makes one zeroed element of the block's type in its own chunk, counted against `heap_max`, and the block's value is `Result<T, BlockError>`. A block value cannot leave its block, be stored in a shared container, a static, a closure or a thread, and a block element holds scalars or a `datac` of scalars only. `block` stays an ordinary name everywhere else.

- A word from another language used as a keyword or type name gets its Kelp word in the `help:` line: `fn`, `def`, `function`, `struct`, `class`, `let`, `match`, `null`, `nil`, `None`, `True`, `False`, `println`, `as`, `int`, `string` and `elseif`. The first line of the message is unchanged.
- A string template outside `print` is a `String` value: `val part = "${out}.part"` binds it, and a `String` parameter takes it. A template in `print` or `print!` prints as before.
- `kelpc caps <project>` prints each module's capabilities and the caps each dependency reaches, sorted for CI diffs. A `[dependencies]` entry whose modules reach a domain its `coral.toml` list does not name is refused at build time.
- `[target] heap_max = N` sets a hosted program's heap cap in MiB (1 to 65536, default 256). A program that needs more stops with `out of memory`. A freestanding build refuses the key.
- `KELP_GC_VERIFY=1` poisons every dead object in the shared pool with the byte `0xA5` at each collection, so a read through a dangling reference sees the poison, not the old contents. The poison is written only in verify mode.
- `KELP_GC_STATS=1` prints one counter line to stderr at exit and before a fatal exit: collections, pause totals and maxima, live roots and charged bytes.
- `[build] emit = "html"` writes a Polyp view as a static HTML file. `[build] emit_entry` names the program that builds it. A Polyp HTML build needs no env grant.
- `let Some(user) = find(id) else { return Err("missing") }` (let-else) binds an enum variant's payload for the rest of the block when it matches. The else block must end in return, break, continue or panic.
- `errdefer EXPR` (6.5) runs its action only when the function leaves through its `Err` (or `None`), by `return` or `?`. A function that does not return `Result` or `Option` refuses it.
- `derive(eq, hash)` on a `datac` or `enum` writes its `eq` and `hash` methods field by field, so it is a `Map` key with no hand-written pair, and a field that has no `eq` or `hash` is refused by name (12.2).
- `kelpc doc --format json` writes the documentation as JSON: declarations, spans, imports, trait impls and builtin members.
- `kelpc stdlib --json --dir <dir>` writes the shipped std sources to `<dir>` and prints the module list with a SHA-256 per file as JSON.
- `[tidepool]` in `coral.toml` sets the hosted collector's first-clearing guesses (`start_low_mib`, `start_high_mib`), the headroom percent (`headroom_pct`) and the trigger rule (`trigger_rule = "two-size"`, `"last-size"` or `"gogc-style"`, default `"two-size"`). A project that sets `[tidepool]` needs a kelpc that reads that section.
- `[build] obfuscate = "names"` ("off" by default) keeps a hosted build's IR and objects in a temporary directory and links the binary with `ld.lld -s`, which drops its symbol table and debug sections. Names mode is not security: a backtrace shows no function names and the binary has no line information. A freestanding project that sets it is refused by name.
- `kelpc repl` reads one expression or single-line statement per line from stdin or `--script FILE`, checks and runs each line as its own program, and prints Int, Float, Bool and String values. Lines do not share state yet; a failed line makes the exit status nonzero.

- `tl var NAME: T = LITERAL` gives each thread its own scalar copy, starting from the literal on first access. A borrow of a `tl` cannot cross to a worker. A heap-owning or `Drop` type, and an initializer that is not a literal, are refused by name.
- A panicking worker runs the user `Drop` of each owned local and each user `Drop` thread argument, newest first, before its joiner sees the panic.
- Linux release packages for kelpc (issue 249): a `.deb` for Debian 13 and Ubuntu 24.04, an `.rpm` for Fedora, a pacman package for Arch and a `flake.nix` for NixOS. `build/release-packages.sh` in the kelp repository builds them in one container per distro and tests each one by installing it into a fresh container, which runs `kelpc run` on hello.kp and `kelpc build` on download.kp. The Debian packages bundle LLVM 21 because apt.llvm.org is not in a standard install. The `kelpc` launcher sets `ld.lld`, and the packages carry no collector archive, since kelpc embeds it. The kelp README has a Without Nix section with the install and source build steps.

- `std/os` is a new module: the target (`os()`, `arch()`), process facts (`pid`, `parent_pid`, `exe_path`, `current_dir`, `set_current_dir`, `exit`), `cpu_count`, `total_memory`, environment variables (`env_var`, `set_env_var`, `unset_env_var`, gated on `env`), and the machine facts `hostname`, `user_name`, `home_dir`, `temp_dir`, `uid` and `gid` (gated on the new `machine` domain, which takes no pattern).
- `std/os` has `make_temp_dir(template)` and `make_temp_file(template)`, which return a `TempDir` or `TempFile` owning a fresh path made from a template ending in `XXXXXX`. The grant is checked against the template at the call. Its drop removes the contents, and the runtime removes the path at exit or on a panic, since a panic runs no destructor.
- `std/sys` re-exports `os()` and `arch()` from `std/os`, so existing programs build as before.
- A freestanding project whose manifest names the `[target] alloc`/`dealloc` pair can call `Ptr.alloc`: the block comes from the project's own allocator, and a failed allocation is the `out of memory` panic, as it is for `Box` and `List`. `Ptr.free` stays refused in a freestanding build, because a project's `dealloc` needs the block's byte size and a pointer does not carry it; free through `Box`, `List` or `Map` instead.
- `Ptr.free_count(count)` is the sized free for a freestanding build with the `[target] alloc`/`dealloc` pair. It takes the element count `Ptr.alloc<T>(count)` was called with and hands the project's `dealloc` the same byte size and alignment (`count * size_of<T>`, `align_of<T>`). A count whose byte size wraps panics, and a null pointer is not passed on. A hosted build refuses it by name; `Ptr.free()` is unchanged.

- `tlsfile.ca_dir_pem(dir)` reads every `.pem` and `.crt` file directly inside a directory, each through the `fs` gate, and returns them as one PEM text for `with_ca_pem`, so a private CA directory needs no loop. A directory with no such file is a typed `TlsError.Io`, not an empty set of extra roots (issue 252).
- `[package]` in `coral.toml` takes `author`, `description`, `license`, `repository` and `homepage`, checked when the file is read. `coral init --author` and `--description` write them, and the new `coral info` prints them.
- `for x in xs.iter()` borrows a `List` and reads every element once. A mutator of that list during the loop (`set`, `remove`, a nested `push`) is refused by the same rule as `for x in xs` (issue 215).

## changed


- `()` is accepted as a type and means `unit`, so `Result<(), E>` is the same type as `Result<unit, E>` and a function can return it (issue 223). `unit` is still refused as a tuple element, and the `'()' is not a type` error is gone.
- Text aliases are written with a leading underscore: a reference is `_name` and a declaration is `alias _name = <text>`, and a `[alias]` key in `coral.toml` is `_name = "path"`. The old `%*name*%` form is refused as a syntax error. A `_name` that no alias declares is an ordinary identifier.

- The checked program has a node for a manual block region (`tir::ExprKind::Region`), and the collector releases a block's element when the block ends.
- The collector's tests cover the shared pool's refusal of a run past `heap_max` while live blocks hold the budget (R12).
- The collector's block runtime, which the `block name: T { ... }` form uses, charges each block's chunk against `heap_max`, the shared pool refills only within what the live blocks leave, and a block creation past the budget runs one clearing before it fails.
- The standard library, the examples and the tests no longer write `.as_str()` at call arguments whose parameter is `str` or `&str`, such as `str.concat(a, b)` or `out.push_str(...)`: the checker takes the same borrow implicitly. Sites that still need the explicit form (`String.from_str`, generic `Children` methods, trait methods, function-typed parameters and `Bytes` values) keep it.
- A parse error prints the token as written (`found ';'`, `found 'fun'`, `found end of file`) where it printed a Rust debug name (`found Semi`, `found Ident("fn")`).
- `kelpc repl` builds run under a resumable memory guard: when memory runs low the guard stops the build's child tools, the line is refused with a low-memory message, and the session continues. A parse error in a typed line points at its place in the line, and an unknown name in the REPL no longer tells the user to declare it with `val` or `var`.
- The return type is written `=>`: `fun f(a: i32) => i32`. The retired `=> ` marker still compiles and means the same, and `->` is an alias of `=>`. The `=> ` marker is removed, so `=> ` is now a parse error that names `=>`. Every example, the standard library, the runtime sources, the wiki and the messages the compiler prints now write `=>`.
- `=>` is accepted as the same arrow as `->` in `when` arms and in a trailing block's parameter header (`{ x => ... }`). Both spellings are one token, so no existing program changes; the arrow's error messages now name both.
- The `managed` target mode is removed: a `[target] mode = "managed"` line is refused with the replacement named. Every hosted build links the tracing collector, so `Box`, `List`, `Map`, `String` and `Bytes` values are freed by the collector, not by drops. Resources (files, sockets, processes, threads, locks, channel ends, pools) still drop at scope end. Delete the mode line; `heap_max` is read in every hosted build.
- `kelpc` embeds the collector archive it builds from `kelpc/gc`, as it embeds the runtime, so a hosted build needs no build tree, no `KELP_GC_LIB` and no launcher. The variable, when set, names a different archive to link.
- A resource (file, socket, process, TLS stream or capability receipt) cannot go in a `Box`, `List`, `Map`, array or closure environment, or be a thread's argument: the checker refuses it by name in every hosted build. A channel end, a pool, a `Mutex`, an `RwLock` and a `Condvar` may be a thread's argument and result.
- A `fun` literal written directly as the `thread.spawn` entry may capture a channel end, a `Mutex`, a `Condvar` or pool state; its captures are dropped when the worker ends, also on a panic. Every other closure still refuses a resource capture, and a closure value cannot be a thread's argument.
- A hosted build accepts channels that close when their senders or receiver drop, `select` over channels where one is ready, a `Mutex` shared through one handle, a `Mutex` block value that is returned or consumed by `into_inner`, and a `Mutex` guarding a `List` pushed from several workers. `sync.bounded(0)` still panics (`sync.bounded: the capacity must be at least 1`); `sync.rendezvous()` is the zero-capacity channel and does not panic.
- A hosted project whose `coral.toml` sets `[build] incremental = true` is built whole-program with a warning that names the reason (the collector's descriptor ids are per unit). The `--incremental` flag is still refused for a hosted build.
- A `String` argument is accepted where a `str` parameter is expected: it is borrowed for the call exactly as `.as_str()` would borrow it (11.2). A generic function or trait method's `str` parameter still needs `.as_str()`, and the compiler says so by name.
- The borrow checker refuses passing one `mut` parameter twice to one call, and reading a struct whole after one of its nested owned fields moved out.
- `std.http` keeps only plain connections in its pool: a TLS connection is not reused after a request, so a TLS request always dials a new connection.
- `Box<T>` blocks of up to 64 bytes are recycled through per-thread free lists instead of malloc and free (binary-trees runs about 1.9x faster). Programs with their own allocator are unchanged.
- A pooled `Box<T>` allocation or release calls `kelp_box_pool` once for the calling thread's free lists, then pops or pushes the block inline; an empty size class goes to `kelp_box_alloc`. Results are unchanged.
- When a thread cannot start, `thread.spawn` panics with the `pthread_create` return code (`errno N: ...`) and frees what it built, where it used to leak it.
- The `header` and `include_dirs` keys of `[extern."<module id>"]` are refused by name, since no C is compiled and they did nothing (`library_dirs` is unchanged). The refusals that said "in managed mode" now say "in a hosted build", and `build/install.sh` checks for `ld.lld` instead of `cc`.
- The Polyp HTML emit (`[build] emit = "html"`) imports `deps/polyp/backends/headless/polyp/lib`, so an HTML build needs no GTK binding and never builds the GTK widget tree.
- The Polyp GTK backend no longer keeps a `gtk.Widget` in its node tree, so a GTK Polyp build compiles in hosted mode (the resource refusal is unchanged). Each node holds scalars only, and its widget is found by its position among its parent's children. A new child appended to the end of a container now lands last, not first.
- The Polyp examples use the Polyp v5 impl ids (`deps/polyp/core/core`, `deps/polyp/backends/gtk/polyp/lib`, `deps/polyp/backends/gtk/gtk`, `deps/polyp/backends/gtk/queue`, `deps/polyp/backends/soft/...`). The `polyp` namespace is unchanged. The v0 examples are frozen.
- The Polyp examples' message queue is Kelp code now, so their `coral.toml` files name no C header.
- A user `extern fun` that takes or returns a `datac`, `Bytes` or `String` by value is lowered to LLVM IR with the System V register or memory classes, not to a C trampoline. A `List`, `Box`, `Map` or array passed or returned by value is still refused by name.
- The `Box` free lists read their per-thread state with the initial-exec TLS model, so each allocation skips a `__tls_get_addr` call.
- In the hosted collector bench (`kelpc/gc`, binary-trees, medians of 5 runs), total stop-the-world time falls from 217 ms to 131 ms (-39%); a 1.5 M-node live set falls from 880 ms to 633 ms (-28%), and the longest pause from 42 ms to 30 ms. Wall time is 11-12% lower on both.

- A hosted build accepts `thread.spawn` with a closure that captures values. A thread's argument and result may hold collected memory, such as a `List`, and a file, a socket or a process is refused as a thread argument by name, while a lock, a channel end and a pool cross under the crossing rule.
- A hosted build refuses a `thread.spawn` once 256 threads are open: it panics with `thread.spawn: 256 threads are already running; join or drop a thread before spawning another`, because the collector attaches at most 256 threads.
- A shared-pool array above 4294967295 elements is named in its own message, and so is a count times size that overflows.
- A `KELP_GC_` variable whose value is not a whole number prints one notice and is ignored. `KELP_GC_STOP_TIMEOUT_MS=0` is refused the same way.
- The collector's root table has no fixed limit: it starts with 1024 slots and doubles as it fills, so a count of roots is never refused.
- The first collection's trigger is capped at the size of the heap region, so a start guess larger than the heap cannot move the first clearing past the end of the region.
- A hosted program's collector starts with 10 percent headroom. Its first collection starts at the midpoint of the start guesses (1 and 4 MiB) plus the headroom, about 2.75 MiB, where it was 8 MiB before, so the first clearing comes sooner. Later collections fire at the larger of the 8 MiB floor and the live size plus the headroom, following the two latest live sizes (the default `two-size` trigger). `[tidepool]` in `coral.toml` changes the guesses, the headroom and the trigger rule.
- The language reference says `kelpc` emits LLVM IR, not C, and no longer says the binary is written next to a `.c` file.

- A misspelled or misplaced Tidepool section is refused by name: `[target.tidepool]`, `[[tidepool]]`, `[tidpool]`, `[tidepool.x]` and the old name `[gc]` each stop the build, and a `[tidepool]` key in a freestanding build is refused, where before the section was skipped without a word. An out-of-range `headroom_pct` (above 1000), a duplicate key and a `start_high_mib` above `heap_max` are refused by name.
- A `start_high_mib` below `start_low_mib` is refused by name, with both values in the message. An unset key counts as its default, so `start_low_mib = 5` alone is refused against the default `start_high_mib` of 4.
- `.return:` is refused by name: the parser says to write the return type with `=>`, as in `fun f(a: i32) => i32`. The migration to `=>` is complete, so no shipped module, example or fixture uses the old spelling.
- `else if` is the preferred spelling of a chain link, and `elif` stays legal and means the same. `kelpc lint` no longer warns about either spelling.
- The examples write `list.get(i)` and `list.set(i, v)` without argument names, and a guard whose body is one `return` that fits in 100 columns on one line: `if n < 2 { return n }`. Style only; no program changes.
- A `&` on a `List` or `str` parameter is redundant: `xs: &List<T>` and `s: &str` take the same arguments as `xs: List<T>` and `s: str`. `kelpc lint` warns about it; the examples no longer write it.
- The examples walk a list with `for item in xs { ... }` where they used `var i = 0` and `while i < xs.len()` with `xs.get(i)`. Style only; no program changes.

- The kernel0-user syscall layer names its refusals as a `SysErr` value (`BadFd`, `Fault`, `NoSys`) and turns one into a register value only in `errno`. `write` checks every page of its range before the first byte is copied, so a call refused at a later page prints nothing; the boot checks each refusal the ABI names (`syscall: refusals ok`) before any program runs (kernel stage 11, #253).

## compiler
- A program records the standard loader path `/lib64/ld-linux-x86-64.so.2` as its interpreter, not the path of the build host's GCC, so a program built on one distro starts on the others (the release matrix checks this on debian-trixie, ubuntu-noble, fedora and arch).

- A hosted program's link sets `RUNPATH` to `$ORIGIN/lib`, so a program finds the libraries bundled in the `lib/` directory beside its executable (a `.ckp` archive). No environment variable is read.
- A compiler error prints a `  help:` line under its location for the common mistakes: an undefined variable, an undefined local, an assignment to a `val`, a return type mismatch, a missing `main`, a use of a moved value, a second statement on one line, a module that cannot be found and a call to an undefined function. The message on the first line is unchanged, and `check --json` gives the same text in a `help` key that is there only when a finding has one.
- The link step uses `ld.lld`, not `cc`: a build with no `cc` can link, and `KELPC_LLD` selects the `ld.lld` binary (otherwise the first one on PATH).
- A TLS program finds OpenSSL's `libssl.so` and `libcrypto.so` through `pkg-config openssl` (then the build-time record, then the system directories), so a Nix build links without a hand-set library path.
- The C runtime is removed: `kelp-rt/`, a Rust `no_std` crate built by `kelpc/build.rs`, is linked into every LLVM-built program. Its symbol names, signatures and struct layouts are unchanged, so a program that calls a runtime helper links as before.
- The runtime's panic, I/O flush, env cache, child table, dial and capability checks are Rust (`kelp-rt/src/`), not C text spliced into each program; behaviour and denial messages are unchanged.
- The hosted build no longer compiles any C: the `extern fun` trampolines, the native-callback glue and the capability allowlists are LLVM IR in `<out>.externs.o`, written by the program's own target machine.
- `kelpc doc --text` reads one file's source from stdin in place of the file, for editor tools.
- `kelpc doc` output has no em or en dashes: dashes copied from doc comments become hyphens.
- Compiler messages and comments use commas, colons and plain hyphens, not em or en dashes. Only the text of a message that had a dash changes.
- The LLVM backend checks a `List` index of `x.to_usize()` (signed `x`) with one bounds branch instead of two; the same panics and messages, faster `List.get` and `List.set` in tight loops.
- The C backend is removed (2026-10-10): `kelpc` builds every program with the `llvm` backend. The `KELPC_ORACLE` switch no longer exists, and a set `KELPC_ORACLE` is refused by name, the same way `KELPC_BACKEND` and `--backend` already are.
- `--sanitize=` and `[build] sanitize` are refused: the sanitizers were built by the C backend, so no build can be sanitized now.
- The TLS and network externs (the `std/tls` handshake, server context, accept and ALPN calls, and `std/net` listen) no longer need a C compiler: they are part of the Rust runtime.
- The retired `--backend`, `KELPC_BACKEND` and `KELPC_ORACLE` refusals and the `--sanitize=` refusal no longer name the removed C backend or its date. The README and the code comments that described the removed backend are rewritten to say what the build does now.
- A function whose body ends in an `if` with no `else` now says to end the block with `return <value>`.
- `kelpc lint` warns on `== true` and on `.len() == 0`, which read better as the condition alone and `.is_empty()`. The warning does not fail the build.
- A string literal is accepted where a `String` is expected; the examples write it that way, without `String.from_str`.
- `kelpc doc --std --check` reports nothing for the shipped standard library: every public item has a doc comment.
- The drop plan keeps a table of each manual block region the function declares, with its name and element type. `DropPlan::has_regions` tells codegen that a program needs the collector's block entry points. Codegen lowers each region from its own `Region` node, which the `block` form produces, and does not read the table.
- The largest compiler source files are split into modules (`kelpc/src/infer/`, `codegen_llvm/`, `resolve/`, `parser/`, `borrowck/`, `llvm_ffi/`, `lexer/` and the integration test suites). The split moves code only: the language, the diagnostics and the generated IR are unchanged.

## stdlib

- `str.split` checks the first byte of the separator before comparing the whole separator, so splitting a long string does less work per position.
- The `net`, `thread`, `tlsfile`, `trace` and `frame` modules now have doc comments on their public items, so `kelpc doc --std --check` reports nothing for them.
- The `ops`, `sync` and `process` modules now have doc comments on their public items, so `kelpc doc --std --check` reports nothing for them.
- The `mem`, `atomic`, `rand`, `convert` and `irq` modules now have doc comments on their public items, so `kelpc doc --std --check` reports nothing for them.
- The `http`, `iter`, `ws` and `tls` modules now have doc comments on their public items, so `kelpc doc --std --check` reports nothing for them.
- The `regex` and `tz` modules now have doc comments on every item, private helpers included, so `kelpc doc --std --check` reports nothing for them.
- The `fs`, `io`, `arena`, `path` and `fmt` modules now have doc comments on every item, private helpers included, so `kelpc doc --std --check` reports nothing for them.
- The `process` and `str` modules now have doc comments on every item, private helpers included, so `kelpc doc --std --check` reports nothing for them.
- The `encoding` and `pool` modules now have doc comments on every item, private helpers included, so `kelpc doc --std --check` reports nothing for them.
- A `select { recv(rx) as v -> e, send(tx, x) -> e, timeout(ms) -> e, closed -> e }` form waits on several channel cases at once in a hosted build, with no polling: the first ready arm in source order runs, a blocked select sleeps until a channel it watches changes or its deadline passes, a send arm on a `sync.rendezvous` channel completes only once a receiver takes its value, and a `default` arm runs at once when nothing is ready.

## fixes

- The golden corpus index lists the two block fixtures added by the block parser: `block_names_stay_ordinary` is frozen from the LLVM output, and `block_region_not_built` is recorded as a refusal, so the golden manifest test passes.
- The `std/fs` tests write their scratch files under a directory unique to each test in each run, and remove it afterwards, so two kelpc suites running at once no longer delete each other's files.
- A hosted build refuses an `Atomic` as a `List`, `Map`, `Box` or array element, because the container's own routines read and write an element as a plain location. A `datac` field of atomic type is accepted.
- A hosted program whose worker panics no longer stalls the next collection until the stop timeout. The worker leaves the collector in its cleanup handler.
- The memory gate's `fs_*` fixtures write their scratch files under a directory unique to each run, not the shared `/tmp`, and remove it afterwards.
- A thread blocked in `join`, a `Mutex` or an `RwLock` wait no longer stalls a collection on another thread, and a long runtime string scan polls the collector every 64 KiB.
- The Rust runtime leaves the collector when a worker ends (also on a panic), waits in join, locks and condition waits as native, polls the collector in long text and map scans, frees a spawn whose thread cannot start and reports its errno, and the collector's personality routine lets a worker's forced unwind finish.
- A freestanding build refuses the `f32` overloads of `std` and `math` as it refuses the `f64` ones, so no soft-float compare routine is linked (`ld.lld` failed with an undefined `__ltsf2` on riscv).
- A `Mutex` or `RwLock` may hold a `List`, `String`, `Box`, `Map`, `Bytes` or a struct with a `List` field in a hosted build; the collector keeps the value alive while the lock holds it.
- The Polyp GTK backend reads a scrolled area's content box through the viewport GTK puts around it, so the todo example no longer prints GTK CRITICAL warnings; a keyed reorder emits the moves that reach the new order (old [a,b,c,d] to new [c,b,d,a] used to end [c,d,b,a]); a mount that disagrees with the view stops the program instead of writing into nothing; and `examples/polyp-todo/smoke.sh` fails on any CRITICAL line.
- A hosted TLS server no longer crashes when a request string is released.
- A `Map` whose value is an enum is refused when the checker reads the `Map` type, not later in codegen, and the refusal names the type and the `List` to use instead.
- The `kelpc fmt` corpus test skips symbolic links when it walks the examples, so the `deps/v4` link that leads back into its own package no longer loops until the kernel's symlink limit panics the test.
- A test holds the collector's fallback headroom to the manifest default of 10 percent, so the two copies cannot drift apart without a failing test.
- A hosted thread may take a `Sender`, `Receiver`, `Mutex`, `Condvar`, `Thread` or a `datac` of them as its argument or its result, and a worker that panics still closes the channels its `Sender`s belonged to.
- A hosted worker that panics while a later argument of a call is evaluated still drops the resource an earlier argument of that call holds, so a receiver of its `Sender` sees `Closed` instead of waiting.
- A worker that panics inside a `select` arm frees the select's waiter on the panic path. The test `a_select_worker_that_panics_frees_its_waiter` (kelp commit 30628097) runs the panic fixture under `KELP_RT_TEST_WAITERS=1`, which reports any waiter still live at exit.
- Bugfix pass (issue 240, release goal 2): a resolve test that had no `#[test]` attribute now runs and passes, and the compiler's own dead code (a duplicate runtime helper, two never-read or test-only items, an unused import) is removed. No behaviour changed. Left with reasons: the ignored goldens `enum_container`, `enum_in_containers` and `generic_owned` are stale since the 2026-10-12 fixture rewrite (the LLVM output matches the current source); the `carriage`, `level_differential`, `backend_coverage` and `golden` sweeps run a riscv64 freestanding binary on the host or lack `libkelpaggwit`, a harness bug; `tidepool_default_heap_max_is_256_mib` is an unwritten stub; the two `threat_model` known gaps (H3, M5) stay open; `List<Box<dyn Trait>>` in a hosted build is refused with the misleading 'declaration was not found' text (a feature gap, not fixed here).

## limits

- A thread argument that is a file, a socket or a closure value is still refused in a hosted build, and so is a `Mutex` of a resource.
- A hosted worker that panics while it evaluates a resource temporary inside a struct literal field leaks that resource, so a receiver waiting on its channel may block.
- A hosted worker that panics while it evaluates a resource temporary as a method receiver leaks that resource, so a receiver waiting on its channel may block.
- A hosted worker that panics while a later argument of a closure call, a function value call or a runtime call is evaluated leaks a resource an earlier argument holds, so a receiver waiting on its channel may block.
- A hosted build refuses an enum stored inside a `datac`: the collector does not describe that layout yet, so such a program is a compile error.
- A `Map` whose value is an enum is refused by the checker at the `Map` type, with a sentence that names the type and says to keep the values in a `List`; the hosted build's codegen does not describe an enum inside a map's entry yet, and a `datac` holding the enum is refused the same way.
- The Tidepool M7 gate (`m7_scan_roots_hw_1_and_hw_1024` in `kelpc/tests/gc/panic_loc.rs`) times the root scan with one live root only; no String case is measured in this release.
- The poison sweep runs only under `KELP_GC_VERIFY=1`. A release build does not write the poison byte, so a read through a dangling reference there still sees the old contents.
- A-11 (full borrow checking) is not finished.
- The kernel and OS stack (release goal 3, issue 253) is not finished: the syscall ABI with untrusted-pointer checks and address-space management are not in this release. The freestanding standard subset, `Ptr.alloc` and the `mmio`, `irq` and `frames` capabilities are in.
- `mem.release`, which would end an owned value before its scope ends, is not in this release (issue 197).
- Project-wide capability grants are not in this release (issue 19). A grant is written per module, in that module's `impl` line.
- Call-site borrow inference and a single text parameter type are not in this release (issue 12).
- Deferred to a later release (issues 6 to 15, 18, 218 to 229, 238, 247 and plans 184 to 203): user `extern fun` with variadics, function pointers or its own linkage; const generics beyond plain integer and `bool` parameters; Unicode case mapping and codepoint-aware `str` slicing; a client-only `std/ws` and an HTTP/1.1-only `std/http`; blanket impls and impls for one instantiation; async, coroutines and weaker atomic orderings; named nested functions, lifetime syntax and borrows in containers; capability narrowing and revocation through a module in the middle; a verification duty with no UB catalogue. Syntax items such as digit separators, multi-line string literals, `orExit` on `Result`, field shorthand and implicit `String` to `str` at call arguments are deferred too.
