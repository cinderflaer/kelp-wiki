---
title: "Compiler"
description: "kelpc turns .kp sources into a program through a fixed pipeline: front end, module resolution, type checking, ownership, LLVM code generation and an `ld.lld` link. These pages map each stage."
isPublished: true
tags: "compiler"
---
How `kelpc` turns `.kp` sources into a program: the stages, the files that implement them and the gates that test them.

## Pages

- [Pipeline](/compiler/architecture): the stages in order, and what each one hands to the next.
- [Front end](/compiler/frontend): lexing, text aliases, parsing and the desugarings the parser does.
- [Modules and capabilities](/compiler/resolve): module loading, `impl` imports, visibility and the capability gate.
- [Types](/compiler/types): type checking, expected types, generics and traits.
- [Ownership and drops](/compiler/ownership): `defer`, moves, borrows and the drop plan.
- [Backends](/compiler/backends): the LLVM backend, the only code generator.
- [Driver](/compiler/driver): the commands, the build steps, linking and diagnostics.
- [Runtime](/compiler/runtime): the standard library sources, `extern fun` bodies and the C runtime files.
- [Incremental builds](/compiler/incremental): per-module units, the object cache and parallel workers.
- [Tests](/compiler/tests): the fixture suite, the backend gates and the fuzzers.
- [Benchmarks](/compiler/benchmarks): what the speed and write benchmarks measure.

## See also

- [Install and build](/getting-started/install): building `kelpc` and running a file
- [Language](/language): the surface syntax these stages implement
- [Capabilities](/language/capabilities): the model the resolver and the checker enforce
- [Changelog](/changelog): what each release changed in the language and in these stages

[Back to the home page](/)
