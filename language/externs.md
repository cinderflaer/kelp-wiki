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
domain, the native library, the header and the exact `symbols` the module's
declarations may bind to.

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

`library` is linked as `-l<library>`. `header` names a C header
that is `#include`d after the runtime preamble; `include_dirs` and `library_dirs`
add `-I`/`-L`; `pkg_config` runs one `pkg-config --cflags --libs` and puts the
flags on both the compile and the link line.

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

The type checker mints one fixed-arity C wrapper per distinct list of extra types
and the call goes through it, so the C compiler applies the default argument
promotions and neither backend emits a variadic call itself. The compiler applies
no conversions of its own.

```toml
[extern."helper"]
domain = "env"
library = "c"
symbols = ["kelp_va_sum", "kelp_va_mix"]
header = "kelp_va_helper.h"
include_dirs = ["include"]
```

```c
/* include/kelp_va_helper.h */
#include <stdarg.h>
#include <string.h>

static inline int kelp_va_sum(int count, ...) {
    va_list ap;
    va_start(ap, count);
    int total = 0;
    for (int i = 0; i < count; i++) {
        total += va_arg(ap, int);
    }
    va_end(ap);
    return total;
}

static inline int kelp_va_mix(int count, ...) {
    va_list ap;
    va_start(ap, count);
    double d = va_arg(ap, double);
    const char* text = va_arg(ap, const char*);
    va_end(ap);
    return (int)(d * count) + (int)strlen(text);
}
```

```kelp
// src/helper.kp
pub extern fun kelp_va_sum(count: i32, ...).return: i32
pub extern fun kelp_va_mix(count: i32, ...).return: i32
```

```kelp project
// src/main.kp
impl "helper" caps(env = ["*"])

fun main() {
    print(helper.kelp_va_sum(0))
    print(helper.kelp_va_sum(1, 7))
    print(helper.kelp_va_sum(3, 1, 2, 3))
    val scale: f32 = 3.5
    print(helper.kelp_va_mix(2, scale, "abcd"))
}
```

```text
0
7
6
11
```

A variadic extern cannot be generic: nothing would specialize the wrapper's
signature per instantiation.

## Callbacks: `move closure(...)`

A user `extern fun` parameter written `move closure(P0, P1, ...).return: T` expands in
place to three C arguments `(thunk, env, destroy)`, the shape GLib's
`(func, user_data, destroy_notify)` uses. `thunk` is a generated C function that
reorders the native `(args..., user_data)` into the closure's own
`(env, args...)`; `env` is a heap box holding the closure value; `destroy` runs
the closure's drop on that environment and frees the box.

The closure is **moved** into the native side, so `destroy` is the only thing that
frees the environment. A native side that never calls it leaks. The closure's
parameters and return must be a scalar, `bool`, `str`, an opaque handle or
`unit`, with no `move`/`mut` parameter, and an extern takes at most one.

```toml
[extern."helper"]
domain = "env"
library = "c"
symbols = ["kelp_call_twice"]
header = "kelp_cb_helper.h"
include_dirs = ["include"]
```

```c
/* include/kelp_cb_helper.h */
static inline int kelp_call_twice(void (*fn)(int, void*), void* data, void (*destroy)(void*), int x) {
    fn(x, data);
    fn(x + 1, data);
    if (destroy) destroy(data);
    return 2;
}
```

```kelp
// src/helper.kp
pub extern fun kelp_call_twice(f: move closure(i32), x: i32).return: i32
```

```kelp project
// src/main.kp
impl "helper" caps(env = ["*"])

fun plain(x: i32) {
    print(x)
}

fun main() {
    val tag = String.from_str("cb")
    val f = fun(x: i32) {
        print(tag.len())
        print(x)
    }
    print(helper.kelp_call_twice(f, 3))
    print(helper.kelp_call_twice(plain, 8))
}
```

```text
2
3
2
4
2
8
9
2
```

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
- **Generated prototypes.** A `header` makes the real C declaration visible, so
  the compiler does not generate a second one.
- **`repr(C)` layout.** An opaque handle crosses as a pointer, but a C struct by
  value has no spelling yet.

## See also

- [Coral: the manifest](/tooling/coral#user-modules-that-bind-a-native-symbol-extern)
- [Capabilities](/language/capabilities)
- [Modules and imports](/language/modules)
- [Types](/language/types)
