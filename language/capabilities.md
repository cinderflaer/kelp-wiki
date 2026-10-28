---
title: "Capabilities"
description: "A program cannot read a file, open a socket, spawn a process or read the clock unless its module was granted that resource. The grant is written in the source."
isPublished: true
tags: "language, capability"
---
Source: [`syntax.md` §15](/design/syntax).

Kelp's headline feature: **a program cannot read a file, open a socket, spawn a
process or read the clock unless the module making the call was granted that
resource**, and the grant is written in the source.

```kelp
impl "std/http" caps(net = ["127.0.0.1:*"])
impl "std/fs"
```

Those two lines are `kelpc/tests/fixtures/examples/download.kp`'s entire network and filesystem
authority. "What can this code do?" is answered by the first few lines of a file
instead of by auditing it.

## The model

- Ten domains: **`fs`**, **`net`**, **`process`**, **`env`**, **`time`**,
  **`rand`**, **`ui`**, **`mmio`**, **`irq`** and **`frames`**.
- Each has a corresponding bare built-in namespace, and the *only* way to reach
  the outside is through a stdlib module that holds it (`kelpc/src/stdlib.rs`),
  or a **user** module a project's `coral.toml`
  assigns one of the seven name domains (`fs`, `net`, `process`, `env`, `time`,
  `rand`, `ui`) to, plus a native library and an
  allowlisted symbol set, so its own `extern fun` declarations can bind to a
  real C symbol. See [User FFI](/language/externs) and
  [Coral: the manifest](/tooling/coral#user-modules-that-bind-a-native-symbol-extern).
  `ui` is the display domain: no call argument names the display, so the only
  accepted grant is `ui = ["*"]`. `mmio` is the device-address domain a
  freestanding project uses to let a module name a hardware address; it is the
  one domain whose whole-resource wildcard the entry module does not hold by
  default (see [below](#mmio-device-registers)). `irq` and `frames` are the two
  device-capability domains a driver uses to claim an interrupt line and a
  physical frame, and unlike `mmio` the entry module holds them by default (see
  [below](#irq-and-frames-interrupt-lines-and-physical-frames)). The ten above
  are the whole set.
- **Every item a gated module declares is gated**, not only the wrapper
  functions a program normally calls: the `extern fun` primitives behind them
  and the module's receiver methods are gated names too, so `fs.read_raw` and
  `process.Child.kill` are refused in a module that does not hold the domain.
  The module that declares an item is the one module exempt from the gate, which
  is what lets a wrapper call its own primitive.
- A gated item is gated **wherever it is named**: a direct call, a receiver
  method call, a closure body and a `pd` initializer all go through the same
  gate, and a gated item **cannot be named as a function value at all**: the
  compiler refuses `val f = fs.read` and `val f = fs.read_raw` by name, whether
  the naming module holds the domain or not.
- **The entry module holds the wildcard for every domain** by default, so a
  single-file program needs no grant for its own calls. A project's
  `coral.toml` can narrow this with a `[caps]` section (see
  [Coral: the manifest](/tooling/coral#the-manifest)), which is the only way
  to give the entry module itself less than everything: a `caps(...)` clause
  on one of the entry module's own `impl` lines still grants the *imported*
  module, never the entry module.
- **Every other module holds exactly what its importer granted it, and nothing
  else.** A module can delegate less than it holds, never more: granting a pattern
  the importer does not hold is an error.
- Referencing a gated item without holding the domain is a **compile error
  naming the missing domain and the grant to write**: not a runtime refusal.
  Holding the domain is the whole check for an item that names no resource
  (`fs.cwd`, `time.nowMonoNs`, a receiver method); an item that does name one
  is additionally checked against the patterns at the call.

## Grants

```kelp
impl "std/fs"
impl "std/http" caps(net = ["api.example.com:443", "127.0.0.1:*"])
impl "logger" caps(fs = ["/var/log/myapp/**"], env = ["LOG_*"])
```

A grant is `domain = [pattern, ...]`, or the whole set in one clause, `caps(*)`
(below). Two domains in one line are fine. An **empty pattern list denies
everything**: `caps(process = [])` is a grant that permits no program, which is
also the smallest grant a consumer can write to satisfy the compiler for a module
it does not actually want to let out.

The `with` that used to introduce the clause (`impl "std/fs" with caps(...)`) is
**gone**, refused by the parser with a message that names the fix. The grant is
`caps(...)` on its own, and the patterns, the domains and the no-escalation rule
are unchanged.

### `caps(*)`

`impl "helper" caps(*)` is the whole grant in one clause: it delegates `/**` for
the path domains and `*` for the name domains, the same set the importing module
holds. It is for a caller that hands a library everything it may reach without
naming the domains one by one, and it is **not a way to acquire authority**: the
set it hands over is the delegator's own, and a module that received `caps(*)`
holds that wildcard and can delegate it onward exactly as it can delegate a
pattern it was given.

The `*` **stands alone**, and the clause is refused in three cases, each by name:

- **A named domain beside the `*`** (`caps(*, net = [...])`, in either order) is
  a parse error, because `*` already means every domain:

  ```text
  error: `caps(*)` already means every domain, so nothing can stand beside the `*`: write `caps(*)` alone, or name the domains it needs (`caps(net = ["host:port"])`, `caps(fs = ["/a/**"], env = ["HOME"])`)
  ```

- **The delegating module does not hold the wildcard itself.** The message names
  the wildcard and the domain that failed, never a pattern the writer would have
  to invent:

  ```text
  error: module 'mid' cannot give 'inner' the whole-resource wildcard for 'fs' with `caps(*)`: it does not hold that wildcard itself (it holds: /tmp/kelp_caps_star_esc/**); a module can delegate less than it has, never more
  ```

- **The import reaches no capability domain** (`std/str`, `std/math`): there is
  nothing to hand over, so the clause is noise at best and a sign that the wrong
  module was named at worst.

  ```text
  error: module 'std/str' is ungated: it reaches no capability domain, so `caps(*)` would grant it nothing; drop the clause
  ```

A module that reaches a gated one counts even when it is ungated itself:
`std/http` is ungated and holds `net`, so `impl "std/http" caps(*)` is a
legitimate line, while the clause on `std/str` is the refusal above.

### The manifest grant

A module that many files import can be granted once, in `coral.toml`, instead
of in every `impl` line that imports it:

```toml
# coral.toml
[caps."std/http"]
net = ["api.example.com:443"]
```

```kelp
impl "std/http"
```

- The named module holds the section's patterns whichever file imports it, so a
  bare `impl` line is enough. A module the manifest does not name holds nothing
  from a bare `impl` line, as before.
- The section is a **ceiling** for that module. A `caps(...)` clause on it may
  grant only the patterns the section covers in that domain. A clause on a
  domain the section does not list is refused, and so is a clause that asks for
  more than the section gives. A clause inside the ceiling is accepted and adds
  no authority the section does not already give.
- The section's own patterns must be ones the entry module holds: its `[caps]`
  section, or the whole resource when it has none.
- The section must name a module the program imports, a module that reaches a
  capability domain, and not the entry module (the entry module's grant is
  `[caps]`). Each module id appears once.
- The vocabulary and the checks are the ones `caps(...)` uses. See
  [Coral: the manifest](/tooling/coral#caps-module-id-the-grant-for-one-imported-module).

### Patterns

| Domain | Pattern forms | Matching |
| --- | --- | --- |
| `net` | `host`, `host:port`, `*.host`, `*:port`, `*` | against the **host string the program wrote**, never a resolved address |
| `fs` | absolute paths, `*` within a component, `**` across components | path normalized lexically and symlinks resolved **before** matching |
| `process` | absolute program paths | same normalization as `fs` |
| `env` | names, `*` | name matching |
| `time`, `rand` | no pattern | an empty list is the whole grant |
| `ui` | `*` only | the domain gate alone: no argument at a display call names the display, so any other pattern list is refused |
| `mmio` | `"0xBASE+0xLEN"` ranges, or `*` alone | an address against the half-open range; a computed address only against `*` (freestanding only) |
| `irq` | decimal line numbers and inclusive ranges (`"10"`, `"32-47"`), or `*` alone | a line against the range; a computed line only against `*` |
| `frames` | the `"0xBASE+0xLEN"` byte windows `mmio` uses, or `*` alone | an address against the half-open range; a constant address must be 4 KiB-aligned, a computed one only against `*` |

Consequences worth internalizing:

- `127.0.0.1:*` does **not** cover `localhost`, even though both are this machine.
  Two spellings of one address can fall under different grants, and the HTTP
  connection pool is keyed on the host as written for exactly that reason.
- A symlink inside a granted directory that points outside it is denied, because
  resolution happens first. That includes a link whose target does not exist yet:
  writing through `data/dangling -> ../secret/new.txt` is refused as writing
  `secret/new.txt`, not accepted because the target is missing.
- **A numeric host pattern admits IPv4 literals only.** `10.0.0.*` (digits, dots
  and `*`) matches `10.0.0.7` and does not match the name `10.0.0.xyz`, which
  DNS could point anywhere; `net.connect` and `net.resolve` both refuse it.
- **A listener binds as widely as the grant's host allows.** `net.listen(port)`
  has no host argument, so the grant decides: a pattern whose host is `*`,
  `0.0.0.0` or a glob matching it (or names no host) gives a listener on every
  interface, and a grant of only loopback or named hosts (`127.0.0.1:*`,
  `localhost:*`) gives one bound to `127.0.0.1`.
- **`process.kill` and `process.wait` only take a child this program spawned.** A
  pid the program did not start panics with `process.kill: not a child this
  program started`, whatever the grant.
- **A handle cannot be forged from a number by a module with no grant.**
  `io.File(fd = 3)`, `net.Socket(fd = 5)` and the other descriptor handles need
  the domain that mints them; a module holding none is refused at compile time.
  Two modules that both hold `fs` can still use each other's descriptors (a
  [known gap](/reference/capability-threat-model#known-gaps)).
- **An `fs` path passed to a gated call must be absolute and must not contain
  `..`.** Build one from a relative argument with
  `path.absolute(fs.cwd(), arg)`: `fs.cwd()` reads the process's working
  directory, it matches no pattern (holding `fs` is the whole grant for a call
  with no path argument), and `path.absolute` normalizes the join so the check
  accepts the result.

### `mmio`: device registers

The eighth domain belongs to a freestanding project. A grant is a list of
half-open address ranges, `"0xBASE+0xLEN"` (`BASE` and `LEN` in hex or decimal,
`+` the separator, `LEN` in bytes), or the whole address space as `["*"]` alone:

```kelp
impl "uart" caps(mmio = ["0x10000000+0x100"])
```

The range covers `[base, base + len)`, so `0x100000FF` is the last byte the
grant above admits and `0x10000100` is the first it does not. The grant is
validated where it is written: a bare address, a zero length, a non-numeric part
and two ranges that share a byte are each a compile error at the `impl` line or
the manifest line.

**What it gates is one call: `Ptr.from_addr(addr)` in a freestanding project.**
It is the only place either backend turns an integer into a pointer, so it is
the whole surface of "this module may name an address". A hosted project's
`Ptr.from_addr` is unchanged and ungated: this domain is about a machine whose
addresses are facts, and a hosted process has an OS between it and the hardware.

- A **constant** address (a literal, a `const`, or arithmetic over those) must
  fall inside a granted range. The refusal names the address and the ranges the
  module holds:

  ```text
  error: 'Ptr.from_addr' would take the address 0x20000000, which no 'mmio' grant of module 'main' covers (granted: 0x10000000+0x100)
  ```

- A **computed** address is refused unless the grant is `["*"]`, because the
  compiler cannot prove a runtime value lands inside a range. The message says
  so:

  ```text
  error: 'Ptr.from_addr' takes an address the compiler cannot fold, and module 'main' holds only the range(s) 0x10000000+0x100; a computed address needs the whole-address-space grant `caps(mmio = ["*"])`
  ```

- A module that holds **no** `mmio` grant and calls `Ptr.from_addr` is refused by
  name.

`mmio` is the one domain the entry module does **not** hold by default.
`caps(*)` hands over every other domain's whole resource and leaves `mmio` out,
because a fallback of `*` would make the feature a no-op, and a device's address
is a fact about the machine rather than a resource the root of trust owns. The
whole-address-space grant has to be written where a reviewer will see it,
`[caps] mmio = ["*"]` or `caps(mmio = ["*"])`. A range can only be delegated by
a module that holds it, the same no-escalation rule every other domain has.

A constant shift of 64 or more bits is not folded, and a `u32` operand folds at 32
bits, as the program computes it. So `0x10000000 + (0x100000 << 70)` is a
computed address (refused under a range grant) rather than being folded to the
granted `0x10000000`.

The limits are honest and worth writing down: the check is on the address a
pointer is **born** at, so an offset applied afterwards (`p.byte_offset(n)`,
`p.offset(n)`, `p.cast<U>()`) is not revisited, and a granted range admits any
address reachable from it by arithmetic; there is no runtime check and no
provenance model; and `mmio` says nothing about what is at the address (a fault
taken on a probe page is granted like a device register). Freestanding is LLVM-only by design. See
[Kernel 0](/language/kernel) for the grants the examples carry and
[`language/capabilities.md`](/language/capabilities)
for the design.

### `irq` and `frames`: interrupt lines and physical frames

Two more device capabilities. Both reuse the range vocabulary
above, and both are **values** rather than a pointer's birth address: a driver
is handed a `Line` or a `Frame` and the type is the record of the grant. A
grant is a list of patterns or the whole resource as `["*"]`:

```kelp
impl "uart" caps(mmio = ["0x10000000+0x100"])
impl "drv"  caps(irq = ["10"], frames = ["0x80100000+0x100000"])
```

- `irq` reads a decimal line number (`"10"`) or an inclusive decimal range
  (`"32-47"`). Hex is refused, so a line number reads the same to a reviewer
  and to the checker, and `"47-32"` is refused as the empty range it is.
- `frames` reads the same `"0xBASE+0xLEN"` byte window as `mmio`, parsed and
  validated by the same code (`stdlib::parse_byte_range`, `ranges_overlap`,
  `range_covers`). There is one range type for all three domains, and `irq`'s
  grammar lowers to the same `(start, len)` pair.

A grant is validated where it is written: a malformed pattern, a zero length, a
reversed line range and two ranges that share a line or a byte are each a
compile error, and `["*"]` cannot be listed beside a range, per domain.

**What it gates.** `irq.claim(<n>)` and `frame.claim(<addr>)`, the two calls
that build the capability values, and every other item of the two shipped
modules (`Line.number`, `Frame.addr`, `Frame.offset`). Both modules are gated
stdlib modules (`stdlib::domain_of` maps `std/irq` to `irq` and `std/frame` to
`frames`), so a module must hold the domain to call anything in them, and
possession of a `Line` is not by itself authority to read it.

- A **constant** line or address must fall inside a granted range. The refusal
  names the value and the ranges the module holds.
- A **computed** line or address is refused unless the grant is `["*"]`,
  because the compiler cannot prove a runtime value lands in a range.
- A `frames` constant must also be 4096-aligned; the check runs before the range
  question and of the wildcard too, because a misaligned frame is not a frame.
- A module with **no** grant that reaches either constructor is refused by the
  domain gate, before any value question is asked.

Unlike `mmio`, the check is in `infer.rs` in the front end and applies to a
hosted program and a freestanding image alike. A hosted program has no
hardware, so the line and the frame it claims are only the numbers the compiler
admitted, and nothing in the modules pretends otherwise.

**Capability by construction.** `claim` is the only constructor. Kelp has no
field-level `pub` and a shipped module exports every item, so the compiler
carries a short list of sealed capability types (`stdlib::SEALED_TYPES`) and
refuses `irq.Line(n = 3)` or `frame.Frame(addr = ...)` written from another
module by name:

```text
error: 'irq.Line' is a capability value: its constructor is private to module 'std/irq', so another module cannot build one; take the value from a `claim` call instead
```

The two runtime checks are `Frame.claim`'s 4096-alignment test for a computed
address and `Frame.offset`'s bounds test against the frame's own 4096.

**Honest limits.** The same shape as `mmio`: a granted line need not exist and a
granted frame need not be RAM, so the domain scopes authority, not meaning;
`Frame.offset` bounds one byte against the frame but the `usize` it returns is
ordinary arithmetic afterwards, so a caller that walks on with `+ n` is outside
the frame and the compiler does not revisit it; and DMA is not tracked, so a
frame handed to a device can be freed, reused or claimed twice. `irq` and
`frames` are held by the entry module by default, so an un-narrowed project can
claim any line and any frame; a kernel that wants the narrow story writes the
`[caps]` section, as `kelpc/tests/fixtures/examples/kernel0-caps` does. See [`std/irq`](/stdlib/irq)
and [`std/frame`](/stdlib/frame).

## Library grants

A library declares the grant it needs, and the *consumer* decides the pattern at
its own `impl` line:

```kelp
impl "deps/fsx/lib" caps(fs = ["/var/lib/myapp/**"])
impl "deps/log/lib" caps(time = [])
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])
```

`fsx` needs `fs`, `log` and `benchkit` need `time`, `term` needs `env` for
`NO_COLOR`, and `lineproto` needs `net`. A library that holds no authority, such
as a pure parser or a calculator, needs no grant at all. You can check that by
reading one line.

There is a subtle case worth knowing: a module can hold a domain *without using
it*, purely to satisfy the compiler on behalf of its own imports. `httpx` is the
example: it only builds and reads plain data, but importing `std/http` needs
`net` delegated, so `httpx` writes `caps(net = [])` internally: the smallest
grant that compiles, and it never dials.

`std/ws` is the two-domain case, and both domains are used. Its text names
`std/net` for the socket and `std/rand` for the sixteen bytes of
`Sec-WebSocket-Key` and the masking key of every frame, so a consumer writes both
on the line:

```kelp
impl "std/ws" caps(net = ["gateway.example.com:80"], rand = [])
```

A program that leaves `rand` off does not build: a module holds exactly what its
importer granted it, and the refusal names the call inside `std/ws`.

`std/tls` is a sharper version of the same subtlety: its own `impl "std/net"`
line carries **no** `caps()` clause at all, not even `caps(net = [])`. A
grant is resolved one hop from the *importing program's* own `impl` line, so
`net.connect` inside `std/http` is checked against whatever the program wrote
on `impl "std/http" caps(net = [...])`; a `net.connect` written inside
`std/tls` instead would be checked against `std/tls`'s own slot, which its
bare `impl` line leaves permanently empty. `std/tls` avoids this by never
dialing: `handshake` takes an already-connected `net.Socket` from `std/http`,
so its bare `impl "std/net"` line exists only to name the type, not to call
anything gated. See [`std/tls`](/stdlib/tls).

When that delegation is missing and the failing module is **not** the one you
wrote the call in, the diagnostic points at the link that broke: it names the
`impl` line that imported the module with no `caps(...)` clause, and that line is
the one to change.

## Why this is checkable

The capability matcher is written in Kelp, in the compiler's own runtime module, `std/rt`. The runtime crate `kelp-rt` declares its entry points as weak imports. A grant is checked statically *and* enforced at
runtime against the pattern list, at every call site that names a resource: a
wrapper, the primitive behind it, a receiver method, a closure body and a `pd`
initializer are each checked against the grant of the module they are written
in.

One shape is refused instead of checked, and the refusal is a language rule
rather than a backend gap: a gated item named as a *function value*
(`val f = fs.read`). The pattern check is emitted from the call's own callee key,
and which argument position holds the resource is a property of that signature, so
a call through the pointer has no check to emit and no place to put one. The
compiler therefore refuses the value by name, for the wrapper spelling and the
`extern fun` one alike, and whether or not the naming module holds the domain
(`kelpc/src/infer.rs::function_value_at`). A function *literal*
over a gated call (`val f = fun(p: &str) => Bytes = fs.read(p)`) is a different
shape: its body is a direct call in the module that wrote it, so it is checked at
run time like any other. Nothing in the shipped stdlib or in the examples uses a gated item as a
value.

## Testing a restriction

The entry module holds everything by default, so the interesting module has
traditionally sat one level down; `coral.toml`'s `[caps]` section can restrict
the entry module itself instead (see
[Coral: the manifest](/tooling/coral#the-manifest)). The one-level-down shape
below still works and is the simpler option for a quick test:

```kelp
// sandbox.kp: a module with exactly one directory
impl "std/fs" caps(fs = ["/srv/data/**"])

fun read(name: str) => String = fs.readText(str.concat("/srv/data/", name))
```

Anything outside `/srv/data/**` is refused at the call, and the caller sees the
failure as a panic from the gated call.

## See also

- [Capability threat model](/reference/capability-threat-model): the attacker, the
  nine holes fixed and the gaps that are still open
- [Capability patterns](/reference/capability-patterns): the pattern grammar in full
- [`std/fs`](/stdlib/fs), [`std/net`](/stdlib/net), [`std/process`](/stdlib/process),
  [`std/env`](/stdlib/env), [`std/time`](/stdlib/time), [`std/rand`](/stdlib/rand),
  [`std/ws`](/stdlib/ws), [`std/tls`](/stdlib/tls), [`std/irq`](/stdlib/irq),
  [`std/frame`](/stdlib/frame)
- [Coral: the manifest](/tooling/coral#user-modules-that-bind-a-native-symbol-extern):
  assigning a domain to a user FFI module
- [Kernel 0](/language/kernel): the freestanding examples, each with an `mmio`
  grant
- [Compiler](/compiler): how the check is implemented
