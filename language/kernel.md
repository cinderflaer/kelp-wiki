---
title: "Kernel 0"
description: "The freestanding examples that boot under QEMU: the UART driver, traps, per-CPU statics, Sv39 tables, a syscall ABI, panic locations, device grants, a preemptive scheduler, and the x86-64 port."
isPublished: true
tags: "language, freestanding, kernel"
---
**Kernel 0** is the first proof that Kelp can be a kernel language: a bare-metal
image QEMU's RISC-V `virt` machine starts, which sets up a stack, writes a line
to the NS16550 UART at `0x10000000`, and halts, written in Kelp with no C and no
libc. The order of work that reached it is
[`language/kernel.md`](/language/kernel);
what could not be done is
[`language/kernel.md`](/language/kernel).
The build side is [Freestanding mode](/language/freestanding).

## Running one

The examples need `qemu-system-riscv64`, `qemu-system-aarch64`,
`qemu-system-x86_64` and `ld.lld`, which the repository's Nix shell supplies. Each has a
`run.sh` that builds the project, boots it under `timeout 20 qemu-system-riscv64
-machine virt -bios none -nographic -no-reboot -serial mon:stdio -kernel <elf>`,
reads QEMU's own stdout until the last expected line appears, kills QEMU, and
asserts every expected line appears whole. Nothing in the script reads the
kernel's intent: the assertion is a comparison against the bytes that came out
of the serial port.

```sh
examples/kernel0/run.sh
```

The script builds with `target/debug/kelpc` by default; `KELPC` points it at
another binary. The real output, from a build of the current tree:

```text
run.sh: booted examples/kernel0 and the UART printed:
hello from kelp
```

| Example | What it proves | Serial output |
| --- | --- | --- |
| `examples/kernel0` | the driver, the entry, the halt | `hello from kelp` |
| `examples/kernel0-trap` | a trap vector, an `ecall`, `mret` | `trap: ecall` then `done` |
| `examples/kernel0-panic` | the compiler's bounds check reaches the handler | `panic: Array.get: index out of bounds` |
| `examples/kernel0-panic2` | the location-carrying handler, one check per boot, and a double panic | `panic: <message> at <file>:<line>` per phase, then `double panic` |
| `examples/kernel0-bss` | `_start` erased a marker the image loaded into `.bss` | `bss clear` |
| `examples/kernel0-heap` | `List<i32>` over a bump allocator | `heap sum 55` then `balanced` |
| `examples/kernel0-string` | `String`/`Bytes` on the project allocator | `s: hello kelp!`, `n: 12345`, `b: 300`, `balanced` |
| `examples/kernel0-percpu` | `percpu static mut` on two harts | `cpu0 4`, `cpu1 7`, `idx 1`, `count 2` |
| `examples/kernel0-vm` | Sv39 tables, the S-mode drop, a high alias | nine `vm:` lines |
| `examples/kernel0-vm-fault` | the load and store page faults | `fault: scause 0xd stval 0x40000000`, `fault: scause 0xf stval 0x3ffffff000` |
| `examples/kernel0-stack` | an unmapped guard page and the stack probe | both faults print `stack overflow: scause 0xf stval 0x...` |
| `examples/kernel0-user` | the trap frame, `ecall`, U-mode | `hello from user`, `bad write -> E`, `user exited 7` |
| `examples/kernel0-aarch64` | the second architecture | `hello from kelp (aarch64)` |
| `examples/kernel0-caps` | `irq`/`frames` claims handed to a driver | `line 10`, `frame 0x80100000`, `offset 0x80100010` |
| `examples/kernel0-x86_64` | the third ISA, a COM1 port-I/O driver | `hello from kelp (x86_64)` |
| `examples/kernel0-x86_64-lmode` | long mode with paging, then a triple fault on purpose | `hello from kelp (x86_64)`, `long mode on` |
| `examples/kernel0-sched` | the machine timer, preemption and round-robin | `A`/`B`/`C` lines, then `sched: done ticks=40` |
| `examples/kernel0-x86_64-idt` | the IDT, four exceptions and the PIC+PIT timer | `exception 6 ...`, `exception 0 ...`, `tick 1`...`tick 5`, `x86: done`, `exception 14 ...` |

## IRQ lines and frames as capabilities

`examples/kernel0-caps` adds two device capabilities beside the `mmio` grant,
both narrowed in the manifest so the grant and the code say the
same thing.

```toml
[caps]
mmio = ["0x10000000+0x100"]
irq = ["10"]
frames = ["0x80100000+0x100000"]
```

`kmain` holds exactly one line and one frame, claims them with the gated
constructors, and hands the receipts to `drv`, which holds the same two grants
and so may read them:

```kelp
section(".text.boot") fun kmain() {
    val line: irq.Line = irq.claim(10)
    val frm: frame.Frame = frame.claim(0x80100000)
    drv.report(line = line, frame = frm)
    uart.halt()
}
```

`irq.claim` and `frame.claim` are the only constructors: the compiler seals the
`Line`/`Frame` struct literals to their modules, so a driver cannot forge a
receipt, and every item of `std/irq`/`std/frame` needs the domain, so possession
of a value is not authority to read it. A constant argument must fall inside a
granted range (a frame must also be 4 KiB-aligned); a computed argument needs
the whole-resource `["*"]`. `src/ungranted.kp` is the compile-error fixture: the
entry grants it line 10 and it reaches for 11, which the test suite copies into
a scratch project and asserts is refused.

```sh
examples/kernel0-caps/run.sh
```

```text
run.sh: booted .../examples/kernel0-caps and the UART printed:
line 10
frame 0x80100000
offset 0x80100010
```

See [Capabilities](/language/capabilities#irq-and-frames-interrupt-lines-and-physical-frames),
[`std/irq`](/stdlib/irq) and [`std/frame`](/stdlib/frame).

## The x86-64 port

The third ISA boots the same way from the reader's side: a
`[target] triple = "x86_64-unknown-none"` project, built by `kelpc` and loaded
by QEMU. What differs is the loader. SeaBIOS' Xen PVH support scans the image's
`PT_NOTE` headers for the `XEN_ELFNOTE_PHYS32_ENTRY` note and jumps to the
32-bit physical address it names, in protected mode with paging off, so the
compiler's `_start` stub builds long mode before it calls Kelp. The full boot
flow, `noredzone` and the SSE enable are in [Freestanding
mode](/language/freestanding#the-x86-64-target).

`examples/kernel0-x86_64` is a COM1 driver: it polls the Line Status Register at
port `0x3FD` and writes the Transmit Holding Register at `0x3F8` through the
`in`/`out` instructions, both inline `asm` in the module the `[unsafe]` list
names. Port I/O is not memory-mapped, so the manifest carries no `mmio` grant:
`in`/`out` name a port number, not a `Ptr.from_addr`.

```sh
examples/kernel0-x86_64/run.sh
```

```text
run.sh: booted .../examples/kernel0-x86_64 and the UART printed:
hello from kelp (x86_64)
```

`examples/kernel0-x86_64-lmode` proves the stub really left protected mode: it
reads `CR0`, `CR4` and `EFER` through `asm`, prints `long mode on` only when
`EFER.LMA`, `CR0.PG` and `CR4.PAE` are all set, then loads a null IDT and
executes `ud2`. With no IDT that is a triple fault, so the machine resets and
`-no-reboot` turns the reset into an exit the test can read.

```sh
examples/kernel0-x86_64-lmode/run.sh
```

```text
run.sh: booted .../examples/kernel0-x86_64-lmode and the UART printed:
hello from kelp (x86_64)
long mode on
```

SeaBIOS prints its own banner on the same serial line first (the greeting's
leading `\n` separates it from `Booting from ROM..`), and `run.sh` asserts the
greeting and `long mode on` whole.

## x86-64 interrupts: the IDT, the exceptions and the timer

`examples/kernel0-x86_64-idt` covers the part the `lmode` boot leaves open: it builds a real IDT, handles four CPU exceptions and takes the
8254/8259 timer interrupt, with the same shape as the riscv64 trap examples (a
naked vector, a frame the compiler does not know about, a Kelp dispatcher, and a
resuming `iretq`). The design is
[`language/kernel.md`](/language/kernel).

An `IdtEntry` is a `repr(c)` 16-byte gate: the target's low 16 bits, the code
selector `0x08` (the boot GDT's 64-bit code segment, read out of the x86-64
`_start` stub's own GDT), an 8-bit IST (0, no stack switch), an 8-bit
type/attribute byte (`0x8E`: present, ring 0, 64-bit interrupt gate), the
offset's middle 16 bits, its high 32 bits and a reserved word. The table is
`static mut IDT: [IdtEntry; 256]`; `install` writes the five gates the kernel
owns (`#DE` 0, `#UD` 6, `#GP` 13, `#PF` 14 and the timer's 32) from
`Ptr.from_fn(gate).addr()`. The other 251 gates stay absent: an absent gate is a
`#GP`, which has a handler, so nothing points at zero. `lidt` reads a separate
`repr(packed)` ten-byte descriptor (a 16-bit limit and a 64-bit base), so the
gate cannot double as one. Both layouts are pinned by `tests/projects/x86_idt_layout` and re-checked at boot by
`trap.layout_ok`, because the gates' `asm` hardcodes the offsets and the
compiler checks neither end.

An exception taken in ring 0 pushes three words (`RIP`, `CS`, `RFLAGS`); a
privilege change would push `RSP` and `SS` too, but there is no user mode on
x86-64 here, so every gate sees three. Vectors 13 and 14 arrive with a CPU error
code below them; the gates for the rest push a zero first so one
`repr(c) TrapFrame` layout serves every vector. A gate then pushes the fifteen general
registers, pushes its vector number, moves the frame base to `rdi`, aligns `rsp`
down to 16 bytes, calls the Kelp `trap_dispatch`, restores the registers and ends
in `iretq`. Three details are not free: the dispatcher's address arrives through
the GS base (an `asm` operand would be materialised into a register before the
gate had saved anything); the frame base is kept in `rbx` across the call
because `rsp` moved; and the interrupted `rsp` is not saved, because a same-level
`iretq` does not restore one.

`trap_dispatch(frame)` reads the vector and prints
`exception <vector> err <code> rip <hex>`, plus ` cr2 <hex>` (from CR2) for
`#PF`. `#UD` and `#DE` are the two faults the kernel raises on purpose, and the
dispatcher resumes them by adding the faulting instruction's length from a small
table (`ud2` is two bytes, the 64-bit `div rcx` is three) to the saved `rip`.
`#GP` and `#PF` have no repair here: the dispatcher prints and halts.

The timer is the 8259 pair and the 8254 PIT. The BIOS maps the 8259s over
vectors 8..15, which collide with the CPU's own exceptions, so the boot remaps
them with ICW1..4: the master to 32..39 and the slave to 40..47, the slave on
IRQ2. Only IRQ0 is unmasked (master IMR `0xFE`, slave IMR `0xFF`). Channel 0 of
the 8254 is programmed through port `0x43` (mode 3, lo/hi, binary) with a
divisor of 11932, so the PIT's 1.193182 MHz input becomes about 100 Hz. The
timer's vector-32 gate is the same naked shape with a dummy-zero error code, so
the timer and the exceptions share one frame and one dispatcher. `pic.on_tick`
prints `tick <n>`, sends the EOI (`outb(0x20, 0x20)`) and, on the fifth tick,
masks the line itself before the boot returns.

The boot order is the proof. `kmain` builds the IDT, takes a `#UD` and a divide
by zero (both repaired and resumed), starts the timer, waits out five ticks,
masks the line, prints `x86: done`, and then stores through 8 GiB. The stub's
identity map covers the first 1 GiB only, so that store is a not-present
supervisor write: the `#PF` gate prints its line and halts, which makes it the
last thing the serial port ever sees. The manifest grants `mmio` exactly that one
page (`"0x200000000+0x1000"`). No compiler change was needed: `Ptr.from_fn`,
`naked fun`, `asm` operands, `align(N)` and the static array of a `datac` were
all in place.

```sh
KELPC=<kelpc> examples/kernel0-x86_64-idt/run.sh
```

```text
run.sh: booted .../examples/kernel0-x86_64-idt and the UART printed:
exception 6 err 0 rip 0x00000000001002f5
exception 0 err 0 rip 0x0000000000100305
tick 1
tick 2
tick 3
tick 4
tick 5
x86: done
exception 14 err 2 rip 0x0000000000100583 cr2 0x0000000200000000
```

`run.sh` matches the exception lines by prefix (the `rip` is the linker's
choice), pins the error codes and the `cr2`, requires the lines in order, and
requires no `tick 6`, because the line is masked after the fifth. The last line,
the `#PF` report, is what ends the run.

What is deliberately not here: the APIC (local and I/O), SMP, ACPI, a TSS or an
IST stack, a separate trap stack, `syscall`/`sysret`, x86 user mode, and the
SSE/XMM state in the frame (the gates save the general registers only, and
nothing in this kernel keeps a live `xmm` value across a fault). Priorities,
blocking and preemption of user mode are the same open work they are for
riscv64.

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
spelling, so the halt is inline `asm`. The example writes bit 5 of `LSR` as
`(value / 32) % 2` rather than `(value >> 5) & 1`, which keeps the reading simple.

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

`[target] panic = "kp_panic"` is what routes every compiler-inserted check to
that handler. `kernel0` and `kernel0-panic` declare the one-argument shape; the
three-argument shape that also carries the source location is the section below.
The message is the check's own text, which is why `kernel0-panic` can assert that the line contains
`index out of bounds` (the line the compiler writes, not one the example chose).

## Panic location and the double panic

A freestanding handler may take the compiler's location as well as the message:
`examples/kernel0-panic2` declares the three-argument form, and the compiler
refuses every other shape by name.

```kelp
fun kp_panic(msg: str, file: str, line: u32) {
    uart.puts("panic: ")
    uart.puts(msg)
    uart.puts(" at ")
    uart.puts(file)
    uart.puts(":")
    put_u32(line)
    uart.puts("\n")
    uart.halt()
}
```

`file` is the source file name the diagnostic's `-->` ends with (`main.kp`) and
`line` is the 1-based line of the statement the check was inserted into. The
location names the statement, not the exact sub-expression, because one `locate`
per statement is what the hosted line tables carry too. A check that lives
inside a generated accessor shared by every call site (`Array.get`, `List.get`,
`Bytes.get`, the allocator's out-of-memory path) reads the caller's statement
from two `.bss` globals the compiler stored before it, so the line it names is
the user's; a panic raised inside `std/option`'s own body names `option.kp`.

Every check calls one compiler-emitted entry, and the entry calls the handler
only once: it exchanges a `.bss` flag, and a check that fires while the handler
is already running reaches `kelp_double_panic` instead of recursing. The
compiler defines that weakly as a `wfi` loop; `examples/kernel0-panic2` links a
strong definition beside the object (the same link-time override the `memcpy`
fallbacks use) and prints `double panic`.

One boot can show only one check, because a panic ends the machine, so `run.sh`
rewrites the selector in a scratch copy and boots the project once per check:

```sh
examples/kernel0-panic2/run.sh
```

```text
phase 1: panic: Array.get: index out of bounds at main.kp:37
phase 2: panic: i32.to_u8: value out of range at main.kp:43
phase 3: panic: str.byte: index out of bounds at str.kp:24
phase 4: panic: deliberate panic at main.kp:54
phase 5: panic: Option.unwrap: value is None at option.kp:68
phase 6: double panic
run.sh: all six phases printed the lines the compiler named
```

Every expected line is computed from the source the compiler read (the message
from the check, the line from a `panic-line: <name>` comment in `main.kp` or
from the stdlib file), so the assertion is QEMU's serial bytes against the
compiler's own claim. Integer overflow wraps and division by zero is unchecked
UB, so neither has a message. [Freestanding
mode](/language/freestanding#panic-semantics) carries the whole table of checks.

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

## Address spaces: Sv39

The mapping example is `examples/kernel0-vm`. Its Sv39 module, `src/vm.kp`, is
written in the language the earlier examples build. The one construct it leans
on is `asm`: a linker-script symbol has no Kelp spelling, so the
frame region arrives through `asm("la {0}, __frames_start", out("r") _)`, the
same way the compiler's own `_start` reaches `__stack_top`. The design is
[`language/kernel.md`](/language/kernel).

The module carries the PTE bit constants (`V R W X U G A D`), the three-level
VPN split, the PTE and `satp` encoders and decoders, a bump frame allocator
over `__frames_start..__frames_end` (one zeroed 4 KiB frame per call, because a
fresh table's absent entries must read as invalid), `map_page`, `map_range`,
`unmap_page` and `translate(root, va) -> Option<usize>`. Every memory access is a
`Ptr<u64>` volatile load or store, and the only two CSRs are `satp` and
`sfence.vma`, both written through `asm`, so `vm` is on the manifest's
`[unsafe] modules` list.

The boot in `src/main.kp` prints one line per step: machine-mode start, a root
table, an identity map, the UART page, the high page, the drop to supervisor
mode, paging on, the alias and the unmap. The image, its stack and the frame
region are identity-mapped as one 4 MiB RWX span; splitting `.text`/`.rodata`/
`.data` apart needs section bounds the language cannot name, and the point of the
example is the walk, not W^X. One page at `0x3F_FFFF_F000` (one page below 2^38,
the highest canonical Sv39 low address) maps to a fresh frame. Under paging the
kernel writes `0xC0FFEE` through the high virtual name, reads it back, asks
`translate` for the physical address and reads the same bytes through the
identity map, then unmaps the high page, flushes the TLB and checks that
`translate` answers `None`.

The transition to S-mode is the standard path, all four steps in
`enter_supervisor`: `pmpaddr0` all ones with `pmpcfg0 = 0x1F` (one NAPOT entry
covering memory, without which every S-mode access faults because no entry
matches), `medeleg` granting the page faults to S-mode, `mstatus.MPP = S`, and
`mret` through `mepc`. The tables are built in machine mode, which does not
translate, and `satp` is written in supervisor mode, so the code that turns the
MMU on is already running at the privilege the MMU applies to.

The second example, `examples/kernel0-vm-fault`, is the S-mode handler. `stvec`
names a naked `align(4)` function, the `asm` idiom, which saves the
caller-saved registers, calls its report function through `sscratch`, and either
advances `sepc` by the faulting instruction's own length (read from its low bits,
because the target enables the compressed extension) and `sret`s, or halts.
`kmain` maps one leaf with R and no W, and `smain` takes two faults on purpose:
a load from an address no leaf maps (`scause` 13, `stval` the address) and a
store to the read-only leaf (15). One boot prints both.

```sh
examples/kernel0-vm/run.sh; examples/kernel0-vm-fault/run.sh
```

```text
run.sh: booted .../examples/kernel0-vm and the UART printed:
vm: m-mode
vm: root
vm: identity
vm: uart page
vm: high page
vm: s-mode
vm: paging on
vm: alias ok
vm: unmap ok
run.sh: booted .../examples/kernel0-vm-fault and the UART printed:
fault: m-mode
fault: paging on
fault: scause 0xd stval 0x40000000
fault: scause 0xf stval 0x3ffffff000
```

What this example deliberately leaves out: TLB shootdown (`flush_tlb` is one local
`sfence.vma`), ASIDs (`satp` always carries ASID 0), huge pages (the walker
translates a superpage leaf and refuses to split one, but `map_page` only writes
a 4 KiB leaf), Sv48 (only mode 8 is encoded), W^X, and demand paging. Frames are
never freed once a table holds them.

## Traps, user mode and the syscall ABI

`examples/kernel0-user` is the same Sv39 boot plus five things: `src/trap.kp`
(the `TrapFrame`, the naked `trap_entry`, `trap_dispatch` and `enter_user`),
`src/syscall.kp` (the numbers, `write` and `exit`, and the copy path),
`src/user.kp` (two hand-written user programs, each a naked function in its own
section, copied into its program's code page at boot), `src/vm.kp` (the walker
plus `user_page_pa`, the walk that demands the U and R bits), and a `kernel.ld`
with the hart's trap stack and the enlarged frame region. The design is
[`language/kernel.md`](/language/kernel).

The trap frame is a convention the compiler cannot see, so both ends pin it:

```kelp
repr(c) datac TrapFrame(
    val x1: u64, ... val x31: u64,
    val sepc: u64, val sstatus: u64)
```

`x1`..`x31` sit at offsets 0 to 240, `sepc` at 248 and `sstatus` at 256, so the
frame is 264 bytes and 8-byte aligned. Only `x2` is special: the hardware leaves
`sp` in the register, not the frame, so the entry recovers the interrupted `sp`
from `sscratch` and stores it in the `x2` slot, and the resume path puts it back
through `sscratch` as well. Each hart gets one 4 KiB trap stack, and `sscratch`
holds its top while user code runs, so the entry's first instruction is
`csrrw sp, sscratch, sp`. The 40 bytes above the frame are a slot block holding
the entry `sp`, the resume `ra` and `sp`, and the address of `trap_dispatch`, so
the naked entry has no instruction of its own to compute an address. The entry
calls `trap_dispatch` with `a0` = the frame address; a nonzero return resumes the
program, zero means the kernel leaves and picks up `enter_user`'s frame from the
slots. `enter_user(root, entry, sp)` writes `satp` and one `sfence.vma`, sets
`sepc`, `sscratch` and the entry slot, clears `sstatus.SPP` and sets `SPIE`, and
`drop_to_user`, a naked `sret`, is the last call. The boot prints
`user: frame ok` only when `size_of<TrapFrame>()`, `offset_of("x17")`,
`offset_of("sepc")` and `offset_of("sstatus")` agree with the same constants the
asm uses.

An `ecall` from U-mode puts the number in `a7`, the arguments in `a0`..`a5`, and
the result in `a0`; a negative result is an error. Registers move through the
frame, and `sepc` advances by 4 (an `ecall` is never the compressed form).

| number | name | arguments | returns |
| --- | --- | --- | --- |
| 0 | `write` | `a0` = fd (only 1), `a1` = pointer, `a2` = length | the length written |
| 1 | `exit` | `a0` = code | does not return |

Errors are the small negative errno values: `-9` (`EBADF`) for a file descriptor
other than 1, `-14` (`EFAULT`) for a pointer the kernel will not copy from, and
`-38` (`ENOSYS`) for a number the kernel does not know. `exit` is the one syscall
that does not return: the handler prints `user exited <code>` and the dispatcher
tells the entry to leave the kernel rather than resume the program.

`write` is the only way user memory crosses into the kernel, and it copies
through a kernel buffer. Before any byte moves, the pointer is validated:

- `len > 4096` is refused, so one call can never ask for more than the kernel's
  one-frame copy buffer.
- `ptr > USER_LIMIT - len`, with `USER_LIMIT = 2^38` (one past the highest
  canonical Sv39 low address), refuses a range that would wrap `ptr + len` and
  refuses every pointer at or above the user limit. The arithmetic is written so
  the addition itself cannot overflow, because a wrap would slip a range past
  the bound check instead of being refused.
- The copy walks the program's page table one page at a time with
  `vm.user_page_pa`, which answers only when the leaf has **both** `PTE_U` and
  `PTE_R`. A kernel address that happens to be mapped (the identity map is in
  every program's table) is not user-readable, so it is refused here and not by
  a lucky address range.
- Each page's bytes are read from the **physical** address the walk returned,
  through the identity map, into the buffer, and the buffer is what the UART
  driver writes. The user virtual address is never dereferenced, so a page the
  walk rejects cannot be reached by a second access that races a remap.

The refused pointer prints the demo's own line (`user: efault ok`) and returns
`-14`; the kernel keeps running and the program sees the error in `a0`.
Program one calls `write(1, "hello from user\n", 16)`, then
`write(1, 0x80000000, 16)` (a mapped kernel page), builds `bad write -> X` on its
stack, replaces `X` with `55 + (-a0)` (the hex digit of the errno magnitude, so
`-14` prints `E`), writes it, and calls `exit(7)`. Program two loads from
`0x40000000`, which no leaf maps in its address space: the load page fault is
`scause` 13, the handler prints `user killed: scause 13` and leaves, and the
kernel prints `kernel survived`.

```sh
examples/kernel0-user/run.sh
```

```text
run.sh: booted .../examples/kernel0-user and the UART printed:
user: m-mode
user: s-mode
user: paging on
user: frame ok
hello from user
user: efault ok
bad write -> E
user exited 7
user killed: scause 13
kernel survived
```

What is deliberately **not** here: no scheduler (one process at a time, one hart,
no run queue and no context switch between two live programs, since program two
starts only after program one has ended), no preemption (no timer interrupt is
armed, so a spinning program is never killed), no `fork`, `exec`, `wait` or
process teardown (pages are never freed and no address space is ever reused), no
ASIDs or TLB shootdown, no copy-on-write, demand paging, guard pages or address
space abstraction, and no interrupt path (`trap_entry` assumes the trap came from
U-mode; a kernel-mode fault would swap the stack pointer out from under the
running handler). There are no signals, and no more than six syscall arguments.
The timer-driven scheduler in the next section is a separate image,
`examples/kernel0-sched`.

## A timer interrupt and a preemptive scheduler

`examples/kernel0-sched` shows the machine timer and a
preemptive round-robin scheduler, still in machine mode with no paging. It is
the process-model half the user-mode example above leaves out. The design is
[`language/kernel.md`](/language/kernel).

The timer is the CLINT. A hart's compare register is at `0x02004000 + 8 * hart`
and the shared free-running counter is at `0x0200BFF8`; on this machine the
counter ticks at 10 MHz, so `10000` ticks are about a millisecond. The boot
arms `mtimecmp`, enables `mie.MTIE` and `mstatus.MIE`, and the manifest grants
exactly the two CLINT words plus the NS16550's block:

```toml
[caps]
mmio = ["0x10000000+0x100", "0x2004000+0x8", "0x200BFF8+0x8"]
```

Each address is delegated to the one module that builds a pointer from it,
exactly as [Capabilities](/language/capabilities#mmio-device-registers)
describes.

The task table is `static mut TASKS: [Task; 3]`, and a `Task` holds a saved
register file, the scheduler address the entry calls, a state, an id and its
own 4096-byte stack, so the whole table is one object in `.bss`. An array
static's element may now be a `datac` or another array, recursively, which is
the one compiler change this example forced; `tests/projects/static_datac_array`
pins it.

A timer tick is handled by a naked `trap_entry`. `mscratch` holds the address of
the *current* task's frame while that task runs, so the entry saves all 31
general registers, `mepc` and `mstatus` into the task table itself, calls
`schedule(frame: Ptr<TrapFrame>)`, restores whichever frame the scheduler
returns, and ends in `mret`. The word just past `mstatus` in each frame is the
address of `schedule`, which is how a naked function reaches a Kelp function
without spelling its mangled symbol (the same idiom the trap dispatch slot uses). `schedule` reads `mcause`: a machine timer interrupt re-arms
`mtimecmp`, counts the tick and may stop the machine, and an `ecall` advances
the saved `mepc` past the instruction; both then fall into the same `pick`,
which rotates to the next READY task and returns its frame.

The three tasks never yield. Each loops forever over its own counter and prints
its letter (`A`, `B`, `C`) and the counter every 50000 iterations. The line is
written under a spin lock, an `Atomic<bool>` whose acquisition also clears
`mstatus.MIE` first and whose release is a `defer uart.lock_release()`. On a
single hart that is what makes a line non-preemptible: no timer interrupt can
arrive with the lock held, so the scheduler never runs mid-line and can never
spin for a lock an interrupted task holds. Since no task ever yields, the only
way the letters can interleave is the timer preempting them, which is what makes
the serial log a proof of preemption rather than of cooperation. The kernel
stops itself after 40 ticks and prints `sched: done ticks=40`.

`run.sh` boots the image under `timeout 20`, reads QEMU's own stdout, and
asserts that all three letters appear, that the letter changes at least three
times, that no line is torn (each is exactly `<letter> <count>`) and that the
stop line is whole:

```sh
KELPC=<kelpc> examples/kernel0-sched/run.sh
```

```text
164 lines, 39 transitions, no torn lines
```

That is the whole of run.sh's output when it passes. The serial bytes behind
it, from a boot of the same image, begin and end like this (the letters and
counters depend on where each tick lands, so they differ between boots; the
invariants run.sh checks do not):

```text
A 50000
B 50000
B 100000
B 150000
B 200000
C 50000
C 100000
C 150000
C 200000
A 100000
A 150000
A 200000
A 250000
...
C 2700000
C 2750000
C 2800000
A 2700000
A 2750000
A 2800000
A 2850000
sched: done ticks=40
```

What is deliberately not in this example: priorities, blocking, sleep/wake, a run
queue with anything but "next READY", task exit and reaping (the state field
exists so those have somewhere to go); SMP (the image runs on hart 0 and the
lock's interrupt masking is a one-hart argument); and preemption of user mode
(these tasks run in machine mode).

Every manifest under `examples/kernel0*` also carries an `mmio` grant now, the
check that a freestanding module may name only an address it was
granted. The UART drivers hold exactly their device's window
(`0x10000000+0x100` for the riscv64 NS16550, `0x09000000+0x1000` for the aarch64
PL011), and the modules that build a pointer from a computed address (a
page-table frame, a trap-frame slot, a user page) hold the whole-address-space
`["*"]`. See [Capabilities](/language/capabilities#mmio-device-registers).
`examples/kernel0-caps` adds the two device-value domains beside it: a narrowed
`irq` grant and a narrowed `frames` grant; see [below](#irq-lines-and-frames-as-capabilities).

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
examples/kernel0-aarch64/run.sh
```

```text
run.sh: booted .../examples/kernel0-aarch64 and the UART printed:
hello from kelp (aarch64)
```

## Stack guards and probing

`examples/kernel0-stack` is the overflow made loud. Every function a freestanding
LLVM build emits carries LLVM's `"probe-stack"="inline-asm"` attribute, so a
frame larger than one page is built by touching each page in order from the top;
a frame that reaches the guard page below the stack faults instead of a single
`sub sp` stepping over the hole. Hosted builds carry no attribute, because a
hosted process has no guard page to probe for.

The linker script puts a 16 KiB trap stack below the image, an unmapped 4 KiB
guard page above it and the 8 KiB kernel stack above the guard. `kmain` identity
maps `[image, __guard_bottom)` and `[__guard_top, __frames_end)` and leaves the
guard page with no leaf.

One boot takes the two overflows on purpose. Phase a recurses with a 16-byte
frame until the frame that crosses `__stack_bottom` stores its saved `ra` into
the guard; the S-mode handler runs on the trap stack, prints the `scause` and
`stval` it saw, checks `stval` against the guard bounds and, for the first fault,
points `sepc` at phase b and returns. Phase b calls a function whose single
`[u8; 16384]` frame is larger than the whole kernel stack: the probe walks it
down page by page into the same guard, which is the case a `sub sp` alone would
miss.

```sh
examples/kernel0-stack/run.sh
```

```text
run.sh: booted .../examples/kernel0-stack and the UART printed:
stack: m-mode
stack: paging on
stack: guard 0x80007000 0x80008000
stack: phase a
stack overflow: scause 0xf stval 0x80007ff8
stack: stval in guard
stack: phase b
stack overflow: scause 0xf stval 0x80007de0
stack: stval in guard
stack: halted
```

Both faults are `scause 0xf`, a store page fault, and each `stval` falls inside
the guard the kernel printed. `run.sh` asserts the seven `stack:` lines, and the
suite's boot test parses the printed bounds and both fault addresses to check
the same range independently.

What this is not: the guard page is the linker script's, not the compiler's
(`probe-stack` only turns a large frame into stores, and whether they land on an
unmapped page is the script's business), the probe does not compare `sp` against
a bound and does not run on a `naked` function, and nothing maps a page to grow
the stack. See
[`language/kernel.md`](/language/kernel).

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
loads into `sp`. These two facts are the only ones a script could get wrong silently.

## What is still missing

The remaining gaps, from
[`language/kernel.md`](/language/kernel):

- **The interrupt path exists, but not as a language construct.** A riscv64
  machine timer interrupt and a preemptive round-robin scheduler are
  `examples/kernel0-sched` ([above](#a-timer-interrupt-and-a-preemptive-scheduler)),
  and an x86-64 IDT with four exception gates and the PIC+PIT timer is
  `examples/kernel0-x86_64-idt`
  ([above](#x86-64-interrupts-the-idt-the-exceptions-and-the-timer)). Both are
  naked bodies the compiler does not model as handlers. `kernel0-trap` still
  installs `mtvec` itself and enables nothing, and the line `kernel0-caps`
  claims is still not wired to a handler. Panic semantics with no OS, the row's
  other half, is the [section above](#panic-location-and-the-double-panic).
- **The `interrupt` and calling-convention attributes** are still open, so a trap handler is a naked body the compiler does not understand as a
  handler.
- **`Ptr.alloc`/`Ptr.free` still have no allocator hook.** The global allocator
  reroutes `Box`/`List`/`Map`/`String`/`Bytes`, and the
  [`std/arena`](/stdlib/arena) bump region and the fallible `Ptr.try_alloc` are
  available, but
  the `Ptr.alloc`/`free` pair is still the hosted `malloc`/`free` and is refused
  in freestanding.
- **Shipped:** user `Drop` ([`fun mut T.drop()`](/language/drop)), per-CPU
  statics ([Per-CPU storage](/language/percpu)), freestanding `String` and `Bytes`,
  the [`std/arena`](/stdlib/arena) bump region and `Ptr.try_alloc`, the stack guard
  and probe, the `mmio`, `irq` and `frames` grants, the
  [freestanding standard subset](/language/freestanding#the-freestanding-standard-subset),
  the x86-64 target, the machine timer with the preemptive scheduler, and the x86-64
  IDT with the PIC and PIT timer. The sections above show each one.
- **The remaining holes are the rest of the process model.** No `interrupt`
  attribute exists, so a trap handler is still a naked body the compiler does
  not understand as a handler, and `Ptr.alloc`/`Ptr.free` still have no hook. A
  preemptive scheduler exists for machine-mode riscv64 tasks, but
  there is no `fork`, no `exec`/`wait`, no priorities or blocking, no TLB
  shootdown, no SMP and no preemption of user mode; x86-64 has an IDT and a
  PIC+PIT timer, but no APIC, SMP, ACPI or user mode.

## See also

- [Freestanding mode](/language/freestanding): the `[target]` section, the
  allowed set and the allocator hook
- [Unsafe code and raw pointers](/language/unsafe): the `Ptr<u8>` volatile
  stores and `Ptr.from_fn`
- [Statics and `defer`](/language/statics-and-defer): `static mut`, the atomic
  static and cleanup on the way out
- [User `Drop`](/language/drop): the destructor a value runs on the way out
- [Per-CPU storage](/language/percpu): one copy of a static per CPU, and the two
  intrinsics that read it back
- [Capabilities](/language/capabilities#mmio-device-registers): the `mmio`
  grant every example carries, and the `irq`/`frames` domains
- [`std/arena`](/stdlib/arena): the bump region a kernel reaches for after the
  allocator hook
- [`std/irq`](/stdlib/irq), [`std/frame`](/stdlib/frame): the capability values
  `kernel0-caps` claims
