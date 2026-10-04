---
title: "`std/frame`"
description: "A physical frame as a capability: `frame.claim(addr)` is the only constructor, its argument is checked against the calling module's `frames` grant and must be 4 KiB-aligned, and the `Frame` it returns is the receipt. Hosted and freestanding."
isPublished: true
tags: "stdlib, capability, kernel"
---
A physical frame (one 4 KiB page) as a **capability**: a module may name a frame
address only if it was granted that frame, and the grant is a value the compiler
checks at the call.

```kelp
impl "std/frame"
```

The module is gated on the `frames` domain (`kelpc/src/stdlib.rs::domain_of`),
so importing it is not enough: the `impl` line, or the importing module's
`[caps]` section, has to delegate `frames` with a pattern list. The design is
[`plan/irq-frame-caps.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/irq-frame-caps.md).

## Types

```kelp
datac Frame(val addr: usize)
```

The frame's base address. The field is not reachable from another module, so a
`Frame` can only be built by `claim`.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `claim(addr: usize)` | `Frame` | the receipt for a `frames` grant; the address must fall inside a granted range and be 4 KiB-aligned |
| `Frame.addr()` | `usize` | the frame's base address |
| `Frame.offset(byte: usize)` | `usize` | the address `byte` bytes into the frame; `byte` is bounds-checked against the frame's own 4096 |

`claim` is a module-level function reached through the `impl` alias:
`frame.claim(0x80100000)`. Every item needs the `frames` domain, so holding a
`Frame` is not by itself authority to read it.

## The grant

`frames` is a byte-range domain, parsed and validated by the same code as
`mmio`: a pattern is `"0xBASE+0xLEN"` (`BASE` and `LEN` in hex or decimal, `+`
the separator, `LEN` in bytes), or the whole address space as `["*"]` alone.
The range covers `[base, base + len)`.

```toml
# coral.toml: the entry module's own grant, narrowed from the wildcard it holds by default
[caps]
frames = ["0x80100000+0x100000"]
```

```kelp
// a driver is delegated exactly its frame region
impl "drv" caps(frames = ["0x80100000+0x100000"])
```

A bare address, a zero length, a non-numeric part and two ranges that share a
byte are each a compile error at the `impl` line or the manifest line, and the
wildcard cannot be listed beside a range.

## What the check decides

The check runs in the front end, in `infer.rs`, for a **hosted and a
freestanding** program alike. A `frames` address is also checked for alignment,
and that check runs before the range question and before the wildcard too,
because a misaligned frame is not a frame.

- A **constant** address must be 4096-aligned and fall inside a granted range:

  ```text
  error: 'frame.claim' would take the address 0x80100001, which is not 4096-aligned: a frame is a 4096-byte-aligned physical address
  ```

  ```text
  error: 'frame.claim' would take the address 0x80200000, which no 'frames' grant of module 'main' covers (granted: 0x80100000+0x100000)
  ```

- A **computed** address is refused unless the grant is `["*"]`, and the message
  says so (the compiler's own wording is quoted here):

  ```text
  error: 'frame.claim' takes a address the compiler cannot fold, and module 'main' holds only the granted address(s) 0x80100000+0x100000; a computed address needs the whole-resource grant `caps(frames = ["*"])`
  ```

- A module that holds **no** `frames` grant is refused by the domain gate.

## Capability by construction

`claim` is the only way a `Frame` enters a program. As with `Line`, the
constructor is sealed to its declaring module (`stdlib::SEALED_TYPES`), so
`frame.Frame(addr = 0x80100000)` from another module is refused by name. A
`Frame` is then an ordinary value, handed to a driver exactly as the entry
claimed it.

## The two runtime checks

`Frame.claim` and `Frame.offset` carry the module's own `panic` calls, so they
are the only checks that fire at run time rather than at compile time:

```text
panic: Frame.claim: address is not 4096-aligned
```

```text
panic: Frame.offset: byte is outside the frame
```

The first exists because a computed address is admitted under the `["*"]` grant,
where the compiler cannot fold it and check the alignment itself. The second
bounds a byte against the frame's own 4096, so a caller cannot walk out of the
frame by asking for byte 4096.

## Example

A hosted program that claims one frame and prints its address and an offset:

```kelp
impl "std/frame"

fun main() {
    val f: frame.Frame = frame.claim(0x80100000)
    print(f.addr())
    print(f.offset(16))
}
```

```toml
# coral.toml
name = "frame_demo"

[caps]
frames = ["0x80100000+0x100000"]
```

```text
2148532224
2148532240
```

`examples/kernel0-caps` is the bare-metal version: one `Frame` claimed from its
`[caps]` grant and printed through `src/drv.kp` as `frame 0x80100000` and
`offset 0x80100010` over the NS16550 UART.

## Freestanding

`std/frame` needs no allocator, no libc and no runtime, so it is one of the
modules the freestanding standard subset admits as-is
([Freestanding mode](/language/freestanding#the-freestanding-standard-subset)).

## Honest limits

- **Born-at only.** `Frame.offset` bounds one byte against the frame's own
  4096, but the `usize` it returns is ordinary arithmetic afterwards: a caller
  that walks on with `+ n` is outside the frame and the compiler does not
  revisit it. Provenance (roadmap D-1) is what would close that.
- **Nothing says what is there.** A granted frame need not be RAM; the domain
  scopes authority, not meaning. Nothing ties the address to real memory.
- **DMA is not tracked.** A frame handed to a device for a DMA transfer is not
  followed: the module may free it, reuse it or hand out a second `Frame` for
  the same address, and the compiler will not see the conflict.
- **A hosted program has no physical frames.** A hosted program may import this
  module and claim a frame as well; the check is a compile-time one, so the
  frame it "claims" is only the address the compiler admitted.
- **`frames` is held by default.** Like `irq` and unlike `mmio`, the entry
  module holds `frames` as the wildcard unless its `[caps]` section narrows it.

## See also

- [`std/irq`](/stdlib/irq): the interrupt-line half of the same stage
- [Capabilities](/language/capabilities#irq-and-frames-interrupt-lines-and-physical-frames):
  the domain, the grant syntax and the limits
- [Freestanding mode](/language/freestanding#the-freestanding-standard-subset):
  the admitted module table
- [Kernel 0](/language/kernel): the `kernel0-caps` boot
