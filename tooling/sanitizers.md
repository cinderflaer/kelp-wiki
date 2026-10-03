---
title: "Sanitizer builds"
description: "kelpc build and run with --sanitize=address, undefined or thread, or [build] sanitize in coral.toml: C backend only, the LLVM refusal, what each sanitizer catches in Kelp, and the real ASan and UBSan reports for an out-of-bounds Ptr write."
isPublished: true
tags: "tooling, cli, unsafe"
---
Safe Kelp cannot read or write out of bounds, but `unsafe`, `Ptr<T>`, `extern`
calls and inline `asm` can. A sanitizer build is the way to find those mistakes:
the program is compiled with Clang or GCC's runtime checks switched on, and a
bad access stops the program with a report that names the `.kp` file and line.
The plan behind it is
[`plan/sanitizers.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/sanitizers.md).
Everything below was run against the prebuilt compiler of the `main` branch.

## Turning one on

```text
KELPC_ORACLE=c kelpc run   --sanitize=address file.kp
KELPC_ORACLE=c kelpc build --sanitize=undefined -o out file.kp
```

Or put it in the project's manifest:

```toml
[build]
sanitize = "address"
```

The values are `address`, `undefined` and `thread`. When both are given the flag
wins over the manifest. A misspelled value, or the flag without `=`, is refused:

```text
$ kelpc build --sanitize=bogus src/main.kp
error: '--sanitize=bogus' is not a sanitizer; expected address, undefined or thread
$ kelpc build --sanitize address src/main.kp
error: '--sanitize' takes its value as '--sanitize=address|undefined|thread'
```

## C backend only

The default LLVM backend does not link LLVM's sanitizer passes, so it refuses the
flag and names the way out. The C backend (the compiler's oracle, reached with
`KELPC_ORACLE=c`) passes `-fsanitize=<kind> -fno-omit-frame-pointer -g` to `cc`,
which also links the sanitizer runtime:

```text
$ kelpc build --sanitize=address src/main.kp -o llvm_try
error: sanitizer 'address' is not available on the LLVM backend, which links no sanitizer passes; build with the C backend instead, which supports address, undefined and thread: KELPC_ORACLE=c kelpc build --sanitize=address src/main.kp
```

The refusal is the same when the sanitizer comes from `[build] sanitize`. A
freestanding project cannot be sanitized at all, since freestanding is LLVM-only.
The C compiler must be on `PATH` (`cc`); without one the build fails with
`error: could not invoke 'cc': No such file or directory (os error 2)`.

Two details of the C build: UBSan is built with `-fno-sanitize-recover=undefined`,
so the first finding ends the program with a nonzero status instead of scrolling
past, and `-fwrapv` stays on, so Kelp's wrapping integer arithmetic is defined
behavior and is not reported. The generated C carries `#line` directives, which
is why a report points at `main.kp:6` and not at generated code.

## What each one catches in Kelp

- **`address`** (AddressSanitizer plus LeakSanitizer): out-of-bounds and
  use-after-free through `Ptr<T>`, overflows of buffers handed to `extern`
  functions, heap overflows in the C runtime, and leaks.
- **`undefined`**: misaligned or too-small accesses through `Ptr`, shifts out of
  range, null dereferences, and bad `memcpy` arguments in the runtime.
- **`thread`**: data races between `thread.spawn` threads, including races on
  state reached through a `Ptr` or a `static mut`, which the safe rules do not
  cover.

Code that stays in safe Kelp gives them nothing to find, which is the point: the
value is in the `unsafe` blocks, the FFI and the runtime.

## An example: a deliberate out-of-bounds write

`kelpc/tests/hazards/sanitizer_oob` in the compiler repository is a project that
writes six bytes past the start of a four-byte array through a raw pointer. Its
manifest is only `name`, and `[unsafe] modules = ["main"]` (the module that may
use `unsafe`); `src/main.kp` is:

```kelp
fun main() {
    var buf: [u8; 4] = [1, 2, 3, 4]
    val bp: Ptr<[u8; 4]> = Ptr.from_ref(&buf)
    val p: Ptr<u8> = bp.cast<u8>()
    unsafe {
        p.offset(6).write(9)
        print(p.offset(6).read())
    }
    unsafe { print(p.read()) }
}
```

Built plainly, it is undefined behavior and happens to run: it prints the byte it
just wrote and then the first element.

```text
$ KELPC_ORACLE=c kelpc build src/main.kp -o plain_oob
$ ( ulimit -v 1048576; ulimit -t 10; timeout 10 ./plain_oob; echo "exit=$?" )
9
1
exit=0
```

With AddressSanitizer it stops on the write. (Run sanitized programs without
`ulimit -v`: the shadow memory needs terabytes of address space. Bound them with
`ulimit -t 10` and `timeout 10` instead.) The addresses, process id and absolute
paths differ from run to run and machine to machine; `...` below stands for the
checkout's path and the lines marked `[trimmed]` are shortened, nothing else is
edited:

```text
$ KELPC_ORACLE=c kelpc build --sanitize=address src/main.kp -o asan_oob
$ ( ulimit -t 10; ASAN_OPTIONS=hard_rss_limit_mb=1024 timeout 10 ./asan_oob; echo "asan-exit=$?" )
=================================================================
==4150798==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x756b2c300026 at pc 0x5685a840a2a2 bp 0x7fffb3ba5480 sp 0x7fffb3ba5478
WRITE of size 1 at 0x756b2c300026 thread T0
    #0 0x5685a840a2a1 in main .../src/main.kp:6
    #1 0x796b2e82b284 in __libc_start_call_main (...libc.so.6+0x2b284) [trimmed]
    #2 0x796b2e82b337 in __libc_start_main@GLIBC_2.2.5 (...libc.so.6+0x2b337) [trimmed]
    #3 0x5685a840a344 in _start (.../asan_oob+0x1344)

Address 0x756b2c300026 is located in stack of thread T0 at offset 38 in frame
    #0 0x5685a840a0ff in main .../asan_oob.c:1565

  This frame has 1 object(s):
    [32, 36) 'kelp_buf' <== Memory access at offset 38 overflows this variable
SUMMARY: AddressSanitizer: stack-buffer-overflow .../src/main.kp:6 in main
...
==4150798==ABORTING
asan-exit=1
```

The report names the line (`main.kp:6`, the `write`), the kind (`WRITE of size 1`)
and the object overrun: the 4-byte `buf` at frame offsets 32 to 36, written at 38.
The frame line names the generated `asan_oob.c` because that is where the frame
is, and `kelp_buf` is the generated name of the Kelp variable `buf`. The shadow
byte dump that follows the summary is left out above.

UBSan reports the same line in its own words, again ending the program with
status 1:

```text
$ KELPC_ORACLE=c kelpc build --sanitize=undefined src/main.kp -o ubsan_oob
$ ( ulimit -t 10; timeout 10 ./ubsan_oob; echo "ubsan-exit=$?" )
.../src/main.kp:6:52: runtime error: store to address 0x7ffd4f428b3a with insufficient space for an object of type 'struct kelp_Array__u8__4'
...
ubsan-exit=1
```

The same project with the manifest key instead of the flag (a `coral.toml` with
`[build]` `sanitize = "address"`) builds and reports the same AddressSanitizer
error with the C backend, and refuses with the message above on the default one.

## The sweep

The compiler repository's `kelpc/tests/run-sanitizers.sh [address|undefined|thread ...]`
(inside the nix shell, with `KELPC` pointing at a built compiler) runs every
fixture that needs no network, stdin or sleep and exits 0 in the plain C build
through the chosen sanitizer, and requires the same exit status and stdout as the
plain build and no sanitizer text on stderr. `kelpc/tests/sanitizers.rs` runs five
of them through ASan and UBSan as part of `cargo test`, plus the hazard project,
the manifest key and the LLVM refusal. The plan records one real bug the sweep
found, a thread handle dropped without `join` that leaked its allocations, now
fixed.

## See also

- [`kelpc` CLI](/tooling/kelpc-cli)
- [Unsafe](/language/unsafe)
- [Tooling](/tooling)
