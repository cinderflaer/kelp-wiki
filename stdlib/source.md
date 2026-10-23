---
title: "`std/source`"
description: "Call-site source locations for Kelp diagnostics and test reports. Ungated."
isPublished: true
tags: "stdlib, diagnostics"
---

`std/source` is ungated. It gives a Kelp library the source location of the
call that invoked it.

```kelp
impl "std/source"

fun check(ok: bool) {
    if !ok {
        print(source.file())
        print(source.line())
    }
}
```

- `source.file() => str` is the path Kelp compiled for the call site.
- `source.line() => usize` is the call site's 1-based line number.

Both values are resolved by the compiler at each call site. They are useful for
test reports and diagnostics; they are not generated-C or LLVM locations.

## See also

- [`std/trace`](/stdlib/trace), which records the call site of each event
- [`std/sys`](/stdlib/sys) for the build target
