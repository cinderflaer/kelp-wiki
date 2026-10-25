---
title: "`std/sys`"
description: "The platform a program was built for: the target's operating system and architecture names. Ungated. Re-exports the target facts of std/os."
isPublished: true
tags: "stdlib"
---
The platform a program was built for. Ungated: both functions return a
constant fixed at build time, so they describe the **target**, not the machine
the binary later runs on.

`std/sys` is kept so existing programs still compile. The functions are the
target facts of [`std/os`](/stdlib/os), which is where new code should look.

```kelp
impl "std/sys"

fun main() {
    if str.eq(sys.os(), "linux") {
        print("built for linux on ${sys.arch()}")
    }
}
```

| Function | Returns | Notes |
| --- | --- | --- |
| `os()` | `str` | `"linux"`, `"macos"`, `"windows"`, `"freebsd"` or `"unknown"` |
| `arch()` | `str` | `"x86_64"`, `"aarch64"`, `"riscv64"`, `"arm"`, `"x86"` or `"unknown"` |

Compare with `str.eq`; `==` on a `str` is refused because it would compare
addresses.

## See also

- [`std/os`](/stdlib/os) for the target facts and the rest of the system facts
- [`std/source`](/stdlib/source) for the call site of a line of code
- [`std/str`](/stdlib/str) for `str.eq`, the comparison a `str` needs
