---
title: "User FFI"
description: "extern fun and extern type bind a project's own modules to native symbols. A coral.toml section names the domain, the library and the allowed symbols. Covers handles, variadics and callbacks."
isPublished: true
tags: "language, capability"
---
`extern fun` and `extern type` are how a project reaches native code. Both are
legal only in a module the manifest assigned an `[extern."<module id>"]` section,
and the module is then gated exactly like a `std/...` one: an importer must
delegate a capability domain. The manifest keys are documented on
[Coral: the manifest](/tooling/coral#user-modules-that-bind-a-native-symbol-extern);
this page is the language side.

A raw `extern fun` would bypass `caps(...)` by construction, so nothing gates what
it reaches. The `[extern.*]` section is what restores the gate: it names the
domain, the native library and the exact `symbols` the module's declarations may
bind to.

kelpc compiles no C. Every native symbol a project binds must already exist in a
library the section names (or in libc, which every hosted program links). A
`header` key is validated but nothing reads it.

## `extern fun`

The declaration is an ordinary `fun` with `extern` in front and no body. Its bare
name must be in that module's `symbols` allowlist, and a `symbols` entry may
rename it `kelp_name=c_symbol`, so the Kelp name and the C symbol can differ.

```toml
# coral.toml
[extern."sys"]
domain = "process"
library = "c"
symbols = ["getpid"]
```

```kelp project
// src/sys.kp
pub extern fun getpid().return: i32
```

```kelp project
// src/main.kp
impl "sys" caps(process = ["/**"])

fun main() {
    print(sys.getpid() > 0)
}
```

```text
true
```

The section header names the module by the path it is imported under, quoted:
`"sys"` for `src/sys.kp`. A bare `[extern.sys]` is refused. A module gets at most
one `[extern.*]` entry, which appears before any other section except `[caps]`.

`library` is linked as `-l<library>`. `library_dirs` adds `-L`. `pkg_config` runs
one `pkg-config --cflags --libs` and puts the flags on the link line. `header` and
`include_dirs` are checked for their form and then not used.

The rename form is how two libraries that share a symbol name are both bound:

```toml
[extern."sys"]
domain = "process"
library = "c"
symbols = ["process_id=getpid"]
```

## `extern type`: opaque native handles

A native pointer that Kelp never dereferences is declared `extern type`. It is an
opaque, pointer-sized `Copy` value: no reading its contents, no arithmetic, no
conversion to or from an integer, and `print` refuses one by name. It is legal
only in an extern module and is exported and named across modules like a
`pub datac`.

```kelp
// src/mem.kp
pub extern type Buffer
pub extern fun malloc(size: usize).return: Buffer
pub extern fun free(buf: Buffer)
```

```kelp project
// src/main.kp
impl "mem" caps(process = ["/**"])

fun main() {
    val buf: mem.Buffer = mem.malloc(16)
    print(buf == buf)
    mem.free(buf)
}
```

```text
true
```

`==` and `!=` compare two handles of the same type (the pointers). Everything
else about one is a compile error.

### Parents and `cast`

`extern type Window: Widget` gives a handle a parent chain. A child converts
implicitly to any ancestor at an argument, a binding and a return, at zero runtime
cost, and `==`/`!=` accept an ancestor/descendant pair. A parent does **not**
convert back down implicitly.

```kelp
// src/mem.kp
pub extern type Block
pub extern type Buffer: Block

pub extern fun malloc(size: usize).return: Buffer
pub extern fun free(block: Block)

pub fun view(block: Block).return: Buffer = Buffer.cast(block)
```

```kelp project
// src/main.kp
impl "mem" caps(process = ["/**"])

fun main() {
    val buf = mem.malloc(16)
    val block: mem.Block = mem.malloc(8)
    print(mem.view(block) == block)
    mem.free(buf)
    mem.free(block)
}
```

```text
true
```

The parent may be declared in the same module or imported, and a cycle is an
error.

### `null()`, `is_null()` and `cast()`

Three operations are legal only inside an extern module, and all three are
constants of the handle type:

- `Widget.null()` is the null handle, the same value a native call returns on
  failure.
- `w.is_null()` tests for it.
- `Window.cast(w)` reinterprets an ancestor down to `Window` with **no runtime
  check**. It requires `w` to be `Window` or an ancestor of it.

```kelp
// src/file.kp
pub extern type File

pub extern fun fopen(path: str, mode: str).return: File

pub fun missing().return: File = File.null()
pub fun is_null_file(f: File).return: bool = f.is_null()
```

```kelp project
// src/main.kp
impl "file" caps(process = ["/**"])

fun main() {
    val f: file.File = file.fopen("/nonexistent-kelp-null-handle", "r")
    print(file.is_null_file(f))
    print(file.is_null_file(file.missing()))
}
```

```text
true
true
```

## Variadic externs

A user `extern fun` may end its parameter list with `...`. A call passes any
number of extra arguments after the fixed ones, each of an integer, `bool`,
`f32`, `f64`, `str` or opaque-handle type. Anything else is a compile error
naming the argument.

The type checker mints one fixed-arity wrapper per distinct list of extra argument
types, and the call goes through that wrapper. The wrapper is part of the program's
IR. The compiler applies no conversions of its own. A variadic extern cannot be
generic: nothing would specialize the wrapper's signature per instantiation.

A variadic extern needs its native symbol in a linked library.

## Callbacks: `move closure(...)`

A user `extern fun` parameter written `move closure(P0, P1, ...).return: T` expands in
place to three C-ABI arguments `(thunk, env, destroy)`, the shape GLib's
`(func, user_data, destroy_notify)` uses. `thunk` is a generated function in the
program's externs object that reorders the native `(args..., user_data)` into the
closure's own `(env, args...)`; `env` is a heap box holding the closure value;
`destroy` runs the closure's drop on that environment and frees the box.

The closure is **moved** into the native side, so `destroy` is the only thing that
frees the environment. A native side that never calls it leaks. The closure's
parameters and return must be a scalar, `bool`, `str`, an opaque handle or
`unit`, with no `move`/`mut` parameter, and an extern takes at most one.

The native function that takes such a callback must come from a linked library.
The example that used a C helper header was removed with the C compiler.

A plain function value widens to a closure with no environment, and the
destructor still frees the box.

## Plain function pointers: `fun(...)`

A `fun(P0, P1, ...).return: T` parameter or return in a user `extern fun` is a typed
plain C function pointer. Use it when the native function borrows the callback
for the call. For example, `fun(i32).return: i32` maps to `int (*)(int)`: the
`ffi_fn_pointer` regression passes one to a native function and receives one back.

The pointer carries no captured environment and the native side must not retain
it beyond the call. Use `move closure(...)` instead when the native API needs a
callback it owns after the call returns, because its thunk, environment and
destructor make that ownership explicit.

## What is not here yet

- **`extern "C"` block syntax.** Each symbol is one `extern fun` declaration.
- **Generated prototypes.** A declaration is the only prototype the compiler knows.
  A `header` key is not read, so no C declaration is included.
- **By-value aggregates.** A user `extern fun` that takes or returns by value a
  struct, `Bytes`, `String`, `View`, `List`, `Box`, `Map`, an array or a closure is
  refused by name. The message says the llvm backend cannot pass it to a native
  symbol yet, and asks for a pointer or a handle instead. An opaque handle crosses
  as a pointer.

## See also

- [Coral: the manifest](/tooling/coral#user-modules-that-bind-a-native-symbol-extern)
- [Capabilities](/language/capabilities)
- [Modules and imports](/language/modules)
- [Types](/language/types)
