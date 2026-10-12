---
title: "Modules and capabilities"
description: "How kelpc loads the module graph from impl lines, qualifies and exports names, and enforces capability grants at compile time and at run time."
isPublished: true
tags: "compiler"
---
The resolver loads every module a program reaches, flattens them into one program and checks the capability grants.
This page covers the loader, the names it produces and the two places where capabilities are enforced.
The language-level rules are on the [Capabilities](/language/capabilities) page.

## Loading the program

`resolve::load` (`resolve.rs`) starts from the entry file or project directory.

1. A directory entry reads `coral.toml` there. Its `[caps]` section becomes the entry module's grant (`parse_manifest`, `resolve.rs`).
   A loose `.kp` file has no manifest, and its directory becomes the source root.
2. The `[alias]` entries are defined (`resolve.rs`).
3. `load_project` (`resolve.rs`) runs the discovery rounds and then a strict pass.
4. `visit_body` (`resolve.rs`) handles one module.
   It lexes and parses the module, lowers its `defer` statements and visits each `impl` import.

A module id is the path under `src/` without the `.kp` extension.
So `src/shapes/circle.kp` is the module `shapes/circle`.
Paths may not contain `..` and may not leave the project.
Dependencies under `src/deps/<key>/` use `lib.kp` and take the directory name as their module name (`module_id_of`, `resolve.rs`).

Standard library ids are read from text compiled into the binary, not from disk (`tokens_of`, `resolve.rs`).
See [Runtime](/compiler/runtime#the-standard-library-in-the-binary).

A cycle of imports is reported (`resolve.rs`).

## Import names

`impl "shapes/circle"` binds the module to the name `circle`.
The name is the last path segment (`default_alias`, `resolve.rs`).
A duplicate name is an error.
The parser reads the `impl` line in `parse_impl_decl` (`parser.rs`).

Names are qualified by the module name.
`qualify` (`resolve.rs`) rewrites `alias.item` into the module's prefix plus the item name.
An unknown alias is an error.
Inside a module, its own items are reached without a prefix.
`infer.rs` tries the prefixed spelling for a bare name (`qualify_own`, `infer.rs`).

## Visibility

Items are private unless they are declared `pub`.
`collect_exports` (`infer.rs`) records the `pub` items, and every item of a shipped standard library module.
`check_exported` (`infer.rs`) refuses a use of a private item from another module with a message that says to add `pub`.

Two more rules use the same export set:

- A `pub` declaration's signature may name only types that its module exports (`check_pub_signatures`, `infer.rs`).
- An `impl X for Y` whose type or trait comes from another module needs that item to be `pub` (`infer.rs`).

## Capability grants

A module may use a gated resource only when it holds a grant for that domain.
The domains are `fs`, `net`, `process`, `env`, `time`, `rand`, `ui`, `mmio`, `irq` and `frames` (`stdlib.rs`).

Grants come from two places.

- **The manifest.** `[caps]` in `coral.toml` gives the entry module `domain = ["pattern", ...]`.
  Without a `[caps]` section, the entry module holds every domain at the whole-resource pattern, except `mmio`.
- **The importer's `impl` line.** `impl "util" caps(fs = ["/tmp/scratch/**"])` grants `util` the `fs` domain for that pattern.
  `caps(*)` passes on every domain the importer holds (`AllGrantEdge`, `resolve.rs`).

A non-entry module holds only what its importers delegate.
A module may delegate only a pattern it holds itself (`pattern_covered`, `resolve.rs`).
A delegation that is wider than the module's own grant is refused at load time:

```text
error: module 'main' cannot grant 'fs' access to '/x/**': it does not hold that pattern itself (held: none); a module can delegate less than it has, never more
```

Importing a gated module also loads `std/rt`, the compiler's matcher module (`resolve.rs`).
The same happens for `std/path`.

The domain that a standard library module needs is set by `domain_of` (`stdlib.rs`).
`std/fs` needs `fs`. `std/net`, `std/tls` and `std/ws` need `net`. `std/http` is not in that table.

## Enforcement at compile time

`check_capability` (`infer.rs`) runs at each reference to a gated item.
That covers calls, function values and names used as values.
A reference passes when:

- the module's grant map has the domain, or
- the reference is inside the module that declares the item.

Otherwise the checker reports an error:

```text
error: '<function>' needs the 'fs' capability, which module 'util' was not granted; the module that imports this one must delegate it (`impl "<this module>" caps(fs = ["<pattern>"])`)
```

The exact text of the `<function>` part comes from `display_callee`, which this page does not trace.

## Enforcement at run time

Patterns that depend on a value, such as a path or a host, are checked when the program runs.

- `cap_plan` in `codegen_llvm.rs` finds the caller's patterns and the check that each gated call needs.
- `emit_cap_checks` in `codegen_llvm.rs` emits a `kelp_cap_check_*` call before the gated call.
  The kinds are `path`, `name`, `host`, `hostport` and `port`.
- A failed check calls `kelp_cap_deny`, which `kelp-rt` exports (`kelp-rt/src/cap.rs`).
  The message names the path and the module and exits with status 1:

```text
<file>:<line>: panic: '/etc/passwd' is outside the fs capability granted to module 'util'
  granted:
    /tmp/kelp_caps_denied/**
```

The matching logic is Kelp code in `std/rt.kp`. The buffer handling and the deny path are
Rust, in `kelp-rt`.
See [Runtime](/compiler/runtime#the-capability-runtime).

A `freestanding` project has a separate `mmio` requirement for `Ptr.from_addr`, checked in `freestanding.rs`.

## Tests

- Unit tests in `resolve.rs` cover manifest sections, aliases and grant parsing.
- `tests/compile_and_run.rs` checks the exact refusal messages for grants and visibility, and that a path outside a grant is denied at run time.
- `tests/cap_function_value.rs` covers gated items used as values.
- `tests/threat_model.rs` runs end-to-end grant and denial cases.

## See also

- [Pipeline](/compiler/architecture)
- [Front end](/compiler/frontend)
- [Capabilities](/language/capabilities)
- [Capability patterns](/reference/capability-patterns)
