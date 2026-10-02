---
title: "`std/irq`"
description: "An interrupt line as a capability: `irq.claim(n)` is the only constructor, its argument is checked against the calling module's `irq` grant, and the `Line` it returns is the receipt. Hosted and freestanding."
isPublished: true
tags: "stdlib, capability, kernel"
---
An interrupt line as a **capability**: a module may name a line only if it was
granted that line, and the grant is a value the compiler checks at the call.

```kelp
impl "std/irq"
```

The module is gated on the `irq` domain (`kelpc/src/stdlib.rs::domain_of`), so
importing it is not enough: the `impl` line, or the importing module's `[caps]`
section, has to delegate `irq` with a pattern list. The design is
[`plan/irq-frame-caps.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/irq-frame-caps.md).

## Types

```kelp
datac Line(val n: u32)
```

The line's number. The field is not reachable from another module, so a `Line`
can only be built by `claim`; see [Capability by construction](#capability-by-construction).

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `claim(n: u32)` | `Line` | the receipt for an `irq` grant; the argument must fall inside a granted range |
| `Line.number()` | `u32` | the line's number |

`claim` is a module-level function reached through the `impl` alias:
`irq.claim(10)`. Both items need the `irq` domain, so a module that holds a
`Line` but no `irq` grant can carry it but not read it.

## The grant

`irq` is a range domain, written like `mmio` and `frames`. A pattern is a
decimal line number (`"10"`) or an inclusive decimal range (`"32-47"`); hex is
refused, so the number reads the same to a reviewer and to the checker. The
whole resource is the wildcard `["*"]` alone.

```toml
# coral.toml: the entry module's own grant, narrowed from the wildcard it holds by default
[caps]
irq = ["10", "32-47"]
```

```kelp
// a driver is delegated exactly its line
impl "uart" caps(irq = ["10"])
```

The grant is validated where it is written. A malformed line, a zero or
reversed range, and two ranges that share a line are each a compile error at the
`impl` line or the manifest line. The wildcard cannot be listed beside a range:

```text
error: the irq range '47-32' is empty - HI counts lines and must not be below LO
```

```text
error: `irq = ["*"]` grants every interrupt line and cannot be written beside a range; keep the wildcard alone, or name the ranges it needs
```

## What the check decides

The check runs in the front end, in `infer.rs`, for a **hosted and a
freestanding** program alike: `kelpc check` and `kelpc build` agree, and both
backends see the same refusal.

- A **constant** line must fall inside a granted range. The refusal names the
  value and the ranges the module holds:

  ```text
  error: 'irq.claim' would take the line 11, which no 'irq' grant of module 'main' covers (granted: 10)
  ```

- A **computed** line is refused unless the grant is `["*"]`, because the
  compiler cannot prove a runtime value lands in a range:

  ```text
  error: 'irq.claim' takes a line the compiler cannot fold, and module 'main' holds only the granted line(s) 10; a computed line needs the whole-resource grant `caps(irq = ["*"])`
  ```

- A module that holds **no** `irq` grant and reaches any item of the module is
  refused by the domain gate, before any value question is asked:

  ```text
  error: 'std.irq.claim' needs the 'irq' capability, which module 'drv' was not granted; the module that imports this one must delegate it (`impl "<this module>" caps(irq = ["<pattern>"])`)
  ```

## Capability by construction

The value, not the name, is the receipt for a grant, and `claim` is the only way
one enters a program. A shipped module exports every item (the transitional rule
in `plan/syntax.md` 13.4) and Kelp has no field-level `pub`, so a bare
`datac Line(val n: u32)` would be constructible from another module as
`irq.Line(n = 3)`. The compiler therefore carries a short list of sealed
capability types (`stdlib::SEALED_TYPES`) and refuses that spelling wherever the
caller is not the declaring module:

```text
error: 'irq.Line' is a capability value: its constructor is private to module 'std/irq', so another module cannot build one; take the value from a `claim` call instead
```

Inside `std/irq` the declaration is ordinary Kelp; outside, only `claim` builds
one. A `Line` is then handed around as an ordinary value, so a driver can be
given exactly what the entry claimed and nothing else.

## Example

A hosted program that claims one line and prints it:

```kelp
impl "std/irq"

fun main() {
    val line: irq.Line = irq.claim(10)
    print(line.number())
}
```

```toml
# coral.toml
name = "line_demo"

[caps]
irq = ["10"]
```

```text
10
```

`examples/kernel0-caps` does the same on bare metal: its `[caps]` section holds
exactly one line, its entry claims it and hands the `Line` to `src/drv.kp`,
which holds the same grant and prints `line 10` over the NS16550 UART.

## Freestanding

`std/irq` needs no allocator, no libc and no runtime, so it is one of the
modules the freestanding standard subset admits as-is
([Freestanding mode](/language/freestanding#the-freestanding-standard-subset)).
The one runtime behaviour is `claim` itself, and it is only a datac
construction: a constant argument was checked at compile time, and a computed
one was admitted only under `["*"]`.

## Honest limits

- **A line is a number.** Nothing ties it to an interrupt controller, a mask
  bit or an installed handler, and nothing says the line exists on the machine.
  The grant scopes authority, not meaning.
- **Compile time, not runtime.** The grant is a resolution-time fact. Nothing
  enables a line or installs a handler; the freestanding `interrupt` attribute
  is still open work ([Kernel 0](/language/kernel#what-is-still-missing)).
- **Born-at only.** A `Line` carries the number `claim` admitted, but nothing
  stops arithmetic on `Line.number()` afterwards.
- **A hosted program has no interrupt hardware.** A hosted program may import
  this module and claim a line as well; the check is a compile-time one, so the
  line it "claims" is only the number the compiler admitted. Freestanding is
  where the number names something.
- **`irq` is held by default.** Unlike `mmio`, the entry module holds `irq` as
  the wildcard unless its `[caps]` section narrows it, so an un-narrowed
  project can claim any line. A kernel that wants the narrow story writes the
  section.

## See also

- [`std/frame`](/stdlib/frame): the physical-frame half of the same stage
- [Capabilities](/language/capabilities#irq-and-frames-interrupt-lines-and-physical-frames):
  the domain, the grant syntax and the limits
- [Freestanding mode](/language/freestanding#the-freestanding-standard-subset):
  the admitted module table
- [Kernel 0](/language/kernel): the `kernel0-caps` boot
