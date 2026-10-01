---
title: "Kernel 0"
description: "The freestanding examples that boot under QEMU: an NS16550 UART driver over `Ptr<u8>` volatile stores, a naked trap handler installed with `Ptr.from_fn`, the panic handler printing the check's own message, and a bump allocator behind `List`."
isPublished: true
tags: "language, freestanding, kernel"
---
**Kernel 0** is the first proof that Kelp can be a kernel language: a bare-metal
image QEMU's RISC-V `virt` machine starts, which sets up a stack, writes a line
to the NS16550 UART at `0x10000000`, and halts, written in Kelp with no C and no
libc. The order of work that reached it is
[`plan/kernel-path.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/kernel-path.md);
what could not be done is
[`plan/kernel0-status.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/kernel0-status.md).
The build side is [Freestanding mode](/language/freestanding).

## Running one

The examples need `qemu-system-riscv64`, `qemu-system-aarch64` and `ld.lld`,
which `dev-kernel.nix` supplies. Each has a `run.sh` that builds the project,
boots it under `timeout 20 qemu-system-riscv64 -machine virt -bios none
-nographic -no-reboot -serial mon:stdio -kernel <elf>`, reads QEMU's own stdout
until the last expected line appears, kills QEMU, and asserts every expected
line appears whole. Nothing in the script reads the kernel's intent: the
assertion is a comparison against the bytes that came out of the serial port.

```sh
nix-shell dev-kernel.nix --run 'examples/kernel0/run.sh'
```

The script builds with `target/debug/kelpc` by default; `KELPC` points it at
another binary. The real output, from a build of the current tree:

```text
run.sh: booted /home/juniper/Projects/kelp-native-ui/overnight/wt-docs2/examples/kernel0 and the UART printed:
hello from kelp
```

| Example | What it proves | Serial output |
| --- | --- | --- |
| `examples/kernel0` | the driver, the entry, the halt | `hello from kelp` |
| `examples/kernel0-trap` | a trap vector, an `ecall`, `mret` | `trap: ecall` then `done` |
| `examples/kernel0-panic` | the compiler's bounds check reaches the handler | `panic: Array.get: index out of bounds` |
| `examples/kernel0-bss` | `_start` erased a marker the image loaded into `.bss` | `bss clear` |
| `examples/kernel0-heap` | `List<i32>` over a bump allocator | `heap sum 55` then `balanced` |
| `examples/kernel0-aarch64` | the second architecture | `hello from kelp (aarch64)` |

The four RISC-V boots, run one after another:

```text
run.sh: booted .../examples/kernel0-trap and the UART printed:
trap: ecall
done
run.sh: booted .../examples/kernel0-panic and the UART printed:
panic: Array.get: index out of bounds
run.sh: booted .../examples/kernel0-bss and the UART printed:
bss clear
run.sh: booted .../examples/kernel0-heap and the UART printed:
heap sum 55
balanced
```

And the aarch64 boot, on QEMU's `virt` machine with `-cpu cortex-a57`:

```sh
nix-shell dev-kernel.nix --run 'examples/kernel0-aarch64/run.sh'
```

```text
run.sh: booted .../examples/kernel0-aarch64 and the UART printed:
hello from kelp (aarch64)
```

## The driver

The NS16550 `THR` (offset 0) is the byte to send; `LSR` (offset 5) bit 5 is set
while the transmit holding register is empty, so a byte is written only after
that bit reads back set. Every access goes through `Ptr<u8>` and is volatile, so
the compiler can neither merge, reorder nor elide it. The base, the offsets and
the bit are the driver's own claim about the hardware.

```kelp
impl "std/str"

const UART_BASE: usize = 0x10000000
const LSR_OFFSET: usize = 5

pub fun putc(c: u8) {
    unsafe {
        val lsr: Ptr<u8> = Ptr.from_addr(UART_BASE + LSR_OFFSET)
        while (lsr.read_volatile() / 32) % 2 == 0 {}
        val thr: Ptr<u8> = Ptr.from_addr(UART_BASE)
        thr.write_volatile(c)
    }
}

pub fun puts(s: str) {
    val n = str.len(s)
    var i: usize = 0
    while i < n {
        putc(str.byte(s, i))
        i = i + 1
    }
}

pub fun halt() {
    while true {
        unsafe {
            asm("wfi")
        }
    }
}
```

Text arrives as a `str`, the same type a hosted program writes, and
`str.len`/`str.byte` are the compiler's own byte loops, so no `strlen` and no
`[u8; N]` copy sits between the caller and the device. `wfi` has no Kelp
spelling, so the halt is inline `asm`; v1 has no bitwise operators, which is why
bit 5 of `LSR` is written `(value / 32) % 2`.

The entry and the panic handler are ordinary Kelp in the entry module:

```kelp
section(".text.boot") fun kmain() {
    uart.puts("hello from kelp\n")
    uart.halt()
}

fun kp_panic(msg: str) {
    uart.puts("panic: ")
    uart.puts(msg)
    uart.puts("\n")
    uart.halt()
}
```

`[target] panic = "kp_panic"` is what routes every bounds and overflow check to
that `fun(msg: str)`. The message is the check's own text, byte-identical to the
C backend's, which is why `kernel0-panic` can assert that the line contains
`index out of bounds` (the line the compiler writes, not one the example chose).

## The trap vector

`kernel0-trap` installs `mtvec` with `csrw mtvec, {0}` and takes a machine-mode
`ecall`. `mtvec`'s low two bits are the vector mode, so `trap_handler` carries
`align(4)` and its own `section(".text.trap")`; it is a `naked fun` whose whole
body is one `asm`, so no prologue, no epilogue and no compiler-generated `ret`
are emitted around it.

```kelp
pub fun install() {
    unsafe {
        asm("csrw mtvec, {0}", in("r") Ptr.from_fn(trap_handler).addr())
        asm("csrw mscratch, {0}", in("r") Ptr.from_fn(report).addr())
    }
}

section(".text.trap") align(4) naked fun trap_handler() {
    asm("
            csrr t0, mepc
            addi t0, t0, 4
            csrw mepc, t0
            addi sp, sp, -128
            sd ra, 0(sp)
            ... save the caller-saved registers ...
            csrr t0, mscratch
            jalr ra, t0, 0
            ... restore them ...
            addi sp, sp, 128
            mret
        ")
}
```

`Ptr.from_fn(trap_handler)` is the checked address of a declared `fun`, so no
mangled symbol is spelled in the file: the address the checker names is the one
the linker resolves. `report` is reached through `mscratch` for the same reason,
and because an inline-asm operand would make the compiler materialise a register
before the handler had saved anything.

The full `asm` body, the register save list and `examples/kernel0-trap/src/trap.kp`
are in the repository; the point here is that the vector is a naked function
plus one `asm`, and the language never sees the trap.

## The `.bss` clear

`_start` zeroes `[__bss_start, __bss_end)` after it loads `sp` and before it
calls the entry, with both bounds declared weak. `kernel0-bss` proves the loop
ran by having the image load a 64-byte marker into a `PROGBITS` section the
script places inside that range, so `bss clear` can only be printed if the bytes
were erased first. The marker is defined by assembler directives (`@progbits`),
because LLVM's own section-name heuristic turns any `.bss.*` name into `NOBITS`
and the initializer would be lost.

## The linker script

QEMU's `-bios none` starts the image at `0x80000000`, not at the ELF entry, so
`_start` has to hold that address. `.text.boot` is placed first, and naming it
first is not enough on its own: `lld` places an unnamed orphan (`.eh_frame`,
which LLVM emits for the driver functions' unwinding tables) *before* `.text`,
so the script names `.eh_frame` explicitly and gives it its own output section.
`kernel.ld` also defines `__stack_top` 16 KiB above the image, which the stub
loads into `sp`. These two facts are the only ones the stage-4 note said a
script could get wrong silently.

## What is still missing

The remaining gaps, in order, from
[`plan/kernel0-status.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/kernel0-status.md):

- **Interrupts are not set up.** `kernel0-trap` installs `mtvec` itself and
  nothing enables `mstatus.MIE` or models the privilege transition. Stage 10
  (panic semantics with no OS) and stage 11 (MMIO capabilities) are where that
  becomes a checked story.
- **The `interrupt`/calling-convention attributes** stage 5 deferred are still
  open, so a trap handler is a naked body the compiler does not understand as a
  handler.
- **No allocator hook for `Ptr.alloc`/`Ptr.free`.** The global allocator reroutes
  `Box`/`List`/`Map` only; the `Ptr` methods stay the hosted `malloc`/`free` and
  are refused in freestanding. Arenas as a language feature and a fallible
  allocation surface are not in this release.
- **Per-CPU storage (stage 8), the MMU and a syscall ABI (stage 9)**, stack
  guards and probing (stage 10), and MMIO regions and IRQ lines as capabilities
  (stage 11) are the rest of the plan.
- **No C-oracle coverage.** Freestanding is LLVM-only by design, so the usual
  "both backends, same behaviour" rule does not apply to these images. It still
  holds everywhere else.

## See also

- [Freestanding mode](/language/freestanding): the `[target]` section, the
  allowed set and the allocator hook
- [Unsafe code and raw pointers](/language/unsafe): the `Ptr<u8>` volatile
  stores and `Ptr.from_fn`
- [Statics and `defer`](/language/statics-and-defer): `static mut`, the atomic
  static and cleanup on the way out
