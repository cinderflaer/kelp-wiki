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
`qemu-system-x86_64` and `ld.lld`. The repository's `shell.nix` supplies `ld.lld`
and LLVM 21, but not the QEMU binaries, so they must be on `PATH`. Each example
names its boot in a `[run]` table in its `coral.toml`: the QEMU machine (`qemu`),
the serial lines it must print (`expect`), and, when needed, `ramfb = true` for the
Polyp framebuffer and `smp = N` for more than one CPU. `kelpc boot <project dir>`
builds the project, boots it under `timeout 20` with that machine's flags (on
riscv64, `qemu-system-riscv64 -machine virt -bios none -nographic -no-reboot
-serial mon:stdio -kernel <elf>`), reads QEMU's own stdout until the last expected
line appears, kills QEMU, and asserts every expected line appears whole. Nothing in
the boot reads the kernel's intent: the assertion is a comparison against the bytes
that came out of the serial port. Only `kelpc boot` reads the `[run]` table; a
normal build ignores it.

The examples share their source files. `kelpc/tests/fixtures/examples/shared/`
holds one copy of each file that more than one example uses, such as the
NS16550 driver (`uart-kernel0.kp`), the Sv39 walker (`vm-kernel0-stack.kp`) and
the Polyp framebuffer platform (`fb_platform-polyp.kp`). An example's `src/`
names that copy with a relative symbolic link: `src/uart.kp` is a link to
`../../shared/uart-kernel0.kp`. The compiler reads the link as the file it
names, so the module keeps its id and the diagnostics keep their path, and the
manifest needs no change. To change a shared file, edit it under `shared/`:
every example that links it builds the new text. A new example that needs one
of these files links to it and does not copy it. `kelpc/tests/shared_examples.rs`
checks both rules.

```text
[run]
qemu = "riscv64"
expect = ["hello from kelp"]
```

```sh
kelpc boot kelpc/tests/fixtures/examples/kernel0
```

`kelpc boot` builds with the `kelpc` that runs it. Four examples keep a `run.sh`
instead, because their checks are not a list of lines: `kernel0-panic`,
`kernel0-panic2`, `kernel0-sched` and `kernel0-x86_64-idt`. Their scripts build with
`target/debug/kelpc` by default, and `KELPC` points them at another binary. The
real output of `kelpc boot`, from a build of the current tree:

```text
kelpc boot: booted kelpc/tests/fixtures/examples/kernel0 and the UART printed:
hello from kelp
```

| Example | What it proves | Serial output |
| --- | --- | --- |
| `kelpc/tests/fixtures/examples/kernel0` | the driver, the entry, the halt | `hello from kelp` |
| `kelpc/tests/fixtures/examples/kernel0-trap` | a trap vector, an `ecall`, `mret` | `trap: ecall` then `done` |
| `kelpc/tests/fixtures/examples/kernel0-panic` | the compiler's bounds check reaches the handler | `panic: Array.get: index out of bounds` |
| `kelpc/tests/fixtures/examples/kernel0-panic2` | the location-carrying handler, one check per boot, a double panic, and a panic that skips a `defer` and a `Drop` | `panic: <message> at <file>:<line>` per phase, then `double panic`; phase 7 prints `panic: cleanup skipped` and no `defer ran` or `drop ran` |
| `kelpc/tests/fixtures/examples/kernel0-bss` | `_start` erased a marker the image loaded into `.bss` | `bss clear` |
| `kelpc/tests/fixtures/examples/kernel0-heap` | `List<i32>` over a bump allocator | `heap sum 55` then `balanced` |
| `kelpc/tests/fixtures/examples/kernel0-string` | `String`/`Bytes` on the project allocator | `s: hello kelp!`, `n: 12345`, `b: 300`, `balanced` |
| `kelpc/tests/fixtures/examples/kernel0-percpu` | `percpu static mut` on two harts | `cpu0 4`, `cpu1 7`, `idx 1`, `count 2` |
| `kelpc/tests/fixtures/examples/kernel0-vm` | Sv39 tables, the S-mode drop, a high alias, the `Space` range check | eleven `vm:` lines |
| `kelpc/tests/fixtures/examples/kernel0-vm-fault` | the load and store page faults | `fault: scause 0xd stval 0x40000000`, `fault: scause 0xf stval 0x3ffffff000` |
| `kelpc/tests/fixtures/examples/kernel0-stack` | an unmapped guard page under each of the two stacks (the trap stack and the kernel stack) and the stack probe | three faults print `stack overflow: scause 0xf stval 0x...`, each followed by `stack: stval in guard` |
| `kelpc/tests/fixtures/examples/kernel0-user` | the trap frame, `ecall`, U-mode | `hello from user`, `bad write -> E`, `user exited 7` |
| `kelpc/tests/fixtures/examples/kernel0-aarch64` | the second architecture | `hello from kelp (aarch64)` |
| `kelpc/tests/fixtures/examples/kernel0-caps` | `irq`/`frames` claims handed to a driver | `line 10`, `frame 0x80100000`, `offset 0x80100010` |
| `kelpc/tests/fixtures/examples/kernel0-x86_64` | the third ISA, a COM1 port-I/O driver | `hello from kelp (x86_64)` |
| `kelpc/tests/fixtures/examples/kernel0-x86_64-lmode` | long mode with paging, then a triple fault on purpose | `hello from kelp (x86_64)`, `long mode on` |
| `kelpc/tests/fixtures/examples/kernel0-sched` | the machine timer, preemption and round-robin | `A`/`B`/`C` lines, then `sched: done ticks=40` |
| `kelpc/tests/fixtures/examples/kernel0-x86_64-idt` | the IDT, four exceptions and the PIC+PIT timer | `exception 6 ...`, `exception 0 ...`, `tick 1`...`tick 5`, `x86: done`, `exception 14 ...` |

## IRQ lines and frames as capabilities

`kelpc/tests/fixtures/examples/kernel0-caps` adds two device capabilities beside the `mmio` grant,
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
kelpc boot kelpc/tests/fixtures/examples/kernel0-caps
```

```text
kelpc boot: booted .../examples/kernel0-caps and the UART printed:
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

`kelpc/tests/fixtures/examples/kernel0-x86_64` is a COM1 driver: it polls the Line Status Register at
port `0x3FD` and writes the Transmit Holding Register at `0x3F8` through the
`in`/`out` instructions, both inline `asm` in the module the `[unsafe]` list
names. Port I/O is not memory-mapped, so the manifest carries no `mmio` grant:
`in`/`out` name a port number, not a `Ptr.from_addr`.

```sh
kelpc boot kelpc/tests/fixtures/examples/kernel0-x86_64
```

```text
kelpc boot: booted .../examples/kernel0-x86_64 and the UART printed:
hello from kelp (x86_64)
```

`kelpc/tests/fixtures/examples/kernel0-x86_64-lmode` proves the stub really left protected mode: it
reads `CR0`, `CR4` and `EFER` through `asm`, prints `long mode on` only when
`EFER.LMA`, `CR0.PG` and `CR4.PAE` are all set, then loads a null IDT and
executes `ud2`. With no IDT that is a triple fault, so the machine resets and
`-no-reboot` turns the reset into an exit the test can read.

```sh
kelpc boot kelpc/tests/fixtures/examples/kernel0-x86_64-lmode
```

```text
kelpc boot: booted .../examples/kernel0-x86_64-lmode and the UART printed:
hello from kelp (x86_64)
long mode on
```

SeaBIOS prints its own banner on the same serial line first (the greeting's
leading `\n` separates it from `Booting from ROM..`), and `kelpc boot` asserts the
greeting and `long mode on` whole.

## x86-64 interrupts: the IDT, the exceptions and the timer

`kelpc/tests/fixtures/examples/kernel0-x86_64-idt` covers the part the `lmode` boot leaves open: it builds a real IDT, handles four CPU exceptions and takes the
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
KELPC=<kelpc> kelpc/tests/fixtures/examples/kernel0-x86_64-idt/run.sh
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
`kelpc/tests/fixtures/examples/kernel0-panic2` declares the three-argument form, and the compiler
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
compiler defines that weakly as a `wfi` loop; `kelpc/tests/fixtures/examples/kernel0-panic2` links a
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

The full `asm` body, the register save list and `kelpc/tests/fixtures/examples/kernel0-trap/src/trap.kp`
are in the repository; the point here is that the vector is a naked function
plus one `asm`, and the language never sees the trap.

## The `interrupt` attribute

`interrupt fun trap()` marks a CPU handler: the CPU enters it when an interrupt or
a trap arrives, so Kelp code never calls it. The body is ordinary Kelp. The
compiler saves the registers the body uses and returns with the target's
interrupt-return instruction, so no `asm` has to save and restore anything:

```text
align(4) interrupt fun trap() {
    unsafe {
        TICKS = TICKS + 1
    }
}
```

The handler's address is taken with `Ptr.from_fn(trap).addr()` and written into the
trap vector, as `kernel0-trap` does for its naked vector. `align(4)` matters on riscv64,
where the low two bits of `mtvec` are the mode.

- **Where it is legal.** Only in a freestanding build, on the `riscv64` and `x86_64`
  triples. A hosted build refuses it by name, and so does an `aarch64` triple, which has
  no lowering yet.
- **Shape.** No parameters, no result, not generic, not a method, not `extern` and not
  `naked`. A `section(...)` or `align(N)` clause applies as it does to any `fun`.
- **Calls.** A direct call to a handler is refused, and the refusal says to take its
  address instead. A handler copied into a function value and called through that value
  is not refused yet.
- **Lowering.** On riscv64 the function carries LLVM's `interrupt("machine")` attribute,
  so the body saves what it touches and ends in `mret`. On x86-64 it uses the
  `x86_intrcc` calling convention: the CPU has pushed `RIP`, `CS`, `RFLAGS`, `RSP` and
  `SS`, the handler takes that frame by value as a hidden first argument that Kelp
  code never reads, and it returns with `iretq`.
- **Not yet.** The x86-64 vectors that push an error code (`#DF`, `#TS`, `#NP`, `#SS`,
  `#GP`, `#PF`, `#AC`) need a handler that takes the code too, so the IDT example keeps
  its `#GP` and `#PF` gates as naked bodies. The calling-convention attributes are
  still open.

`kelpc/tests/fixtures/examples/kernel0-sched` and `kernel0-x86_64-idt` keep their naked vectors; a new kernel
can write its handlers as `interrupt fun` instead.

## Address spaces: Sv39

The mapping example is `kelpc/tests/fixtures/examples/kernel0-vm`. Its Sv39 module, `src/vm.kp`, is
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

The second example, `kelpc/tests/fixtures/examples/kernel0-vm-fault`, is the S-mode handler. `stvec`
names a naked `align(4)` function, the `asm` idiom, which saves the
caller-saved registers, calls its report function through `sscratch`, and either
advances `sepc` by the faulting instruction's own length (read from its low bits,
because the target enables the compressed extension) and `sret`s, or halts.
`kmain` maps one leaf with R and no W, and `smain` takes two faults on purpose:
a load from an address no leaf maps (`scause` 13, `stval` the address) and a
store to the read-only leaf (15). One boot prints both.

```sh
kelpc/tests/fixtures/examples/kernel0-vm; kelpc/tests/fixtures/examples/kernel0-vm-fault
```

```text
kelpc boot: booted .../examples/kernel0-vm and the UART printed:
vm: m-mode
vm: root
vm: identity
vm: uart page
vm: high page
vm: s-mode
vm: paging on
vm: alias ok
vm: unmap ok
vm: align refused
vm: range refused
kelpc boot: booted .../examples/kernel0-vm-fault and the UART printed:
fault: m-mode
fault: paging on
fault: scause 0xd stval 0x40000000
fault: scause 0xf stval 0x3ffffff000
```

### The owner: `Space`, a checked range and frames as capabilities

The walker's functions are private to `vm.kp`. Every mapping in the example goes
through `vm.Space`, a datac that holds the root table as a `frame.Frame` and the
virtual range `[lo, hi)` its owner may map:

```kelp
pub datac Space(val root: frame.Frame, val lo: usize, val hi: usize)

fun Space.map(va: usize, pa: frame.Frame, flags: u64) => bool
fun Space.map_range(va: usize, first: frame.Frame, pages: usize, flags: u64) => bool
fun Space.unmap(va: usize) => bool
fun Space.translate(va: usize) => option.Option<usize>
fun Space.enable()
```

`map` answers `false` and writes nothing when `va` is not page-aligned, when the
whole page does not lie inside `[lo, hi)`, when no table frame is left, or when a
superpage is in the way. `unmap` takes the same range check, and `translate`
answers `None` for any address outside `[lo, hi)`. The example's boot ends with
two refusals on the owner: an unaligned page (`vm: align refused`) and a page at
`2^38`, one past the owner's range (`vm: range refused`).

The physical side is a capability. A `frame.Frame` exists only as the value
`frame.claim` returns, and `claim` checks the address against the `frames` grant
of the module that calls it ([`std/frame`](/stdlib/frame)). The example's
`[caps]` section names `frames = ["*"]`, and `vm` is delegated the same wildcard
with `impl "vm" caps(...)`, because the root table (claimed in `main`) and every
page `map_range` maps are computed addresses in the frame region, and a computed
claim cannot be folded against a range. A `[caps]` section that names no
`frames` line would leave the entry without the domain at all. Narrowing that grant to one range makes the module refuse the claim at the
check, before any boot: `kelpc/tests/irq_frames.rs` builds the example with the
narrowed grant and asserts the refusal says the address cannot be folded and names the wildcard it needs.

The owner does not stop a holder of a whole-resource `frames` grant from mapping
one frame into two spaces, and it does not free a frame, since frames are never
freed here. Only one space exists in the example. `kelpc/tests/fixtures/examples/kernel0-user` keeps
its own copy of the free-function walker, with the user-page check on top, so
`Space` is not used there yet.

What this example deliberately leaves out: TLB shootdown (`flush_tlb` is one local
`sfence.vma`), ASIDs (`satp` always carries ASID 0), huge pages (the walker
translates a superpage leaf and refuses to split one, but `map_page` only writes
a 4 KiB leaf), Sv48 (only mode 8 is encoded), W^X, and demand paging. Frames are
never freed once a table holds them.

## Traps, user mode and the syscall ABI

`kelpc/tests/fixtures/examples/kernel0-user` is the same Sv39 boot plus five things: `src/trap.kp`
(the `TrapFrame`, the naked `trap_entry`, `trap_dispatch` and `enter_user`),
`src/syscall.kp` (the number table, the typed refusals, `write` and `exit`, the
range check and the copy path),
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

Inside the kernel a refusal is a value of the enum `SysErr`, one variant per
errno the ABI names: `BadFd` (`-9`, `EBADF`) for a file descriptor other than 1,
`Fault` (`-14`, `EFAULT`) for a pointer the kernel will not copy from, and `NoSys`
(`-38`, `ENOSYS`) for a number the table does not know. Each call returns
`Reply`, which is either `Done(value)` or `Refused(err)`, and `errno` is the one
place a refusal becomes a register value, so a path cannot answer with a number
that is not one of these. `exit` is the one syscall that does not return: the
handler prints `user exited <code>` and the dispatcher tells the entry to leave
the kernel rather than resume the program.

Every call decodes the same shape: the number from `a7`, and exactly six argument
words from `a0`..`a5`. A call reads only the words it uses, so an extra argument
is never a reason to refuse a call and never a read the kernel has to justify.

`write` is the only way user memory crosses into the kernel, and it copies
through a kernel buffer. The range check is `user_range_ok(ptr, len)`, a pure
function the boot exercises directly:

- `len > 4096` is refused, so one call can never ask for more than the kernel's
  one-frame copy buffer.
- `ptr > USER_LIMIT - len`, with `USER_LIMIT = 2^38` (one past the highest
  canonical Sv39 low address), refuses a range that would wrap `ptr + len` and
  refuses every pointer at or above the user limit. The arithmetic is written so
  the addition itself cannot overflow, because a wrap would slip a range past
  the bound check instead of being refused. `len` is tested first, so the
  subtraction cannot wrap either.
- The first pass walks the program's page table one page at a time with
  `vm.user_page_pa`, over every page the range touches, which answers only when
  the leaf has **both** `PTE_U` and `PTE_R`. A kernel address that happens to be
  mapped (the identity map is in every program's table) is not user-readable, so
  it is refused here and not by a lucky address range. A range whose second page
  is unmapped is refused before its first page is copied.
- Only after the first pass has passed does the copy run. Each page's bytes are
  read from the **physical** address the walk returned, through the identity map,
  into the buffer, and the buffer is what the UART driver writes. The user virtual
  address is never dereferenced, so a page the walk rejects cannot be reached by a
  second access that races a remap.

Before the first pass existed, a range that crossed into an unmapped page printed
the bytes of its first page and then refused. The two-pass copy makes a refusal
print nothing, so an `EFAULT` always means no byte of that call reached the UART.

The dispatcher, not `handle`, prints the demo's own line (`user: efault ok`) when a
program's call answers `EFAULT`, and the program sees `-14` in `a0`; the kernel
keeps running. The boot runs `syscall.self_test` before any program: it drives
`handle` against a throwaway address space built the same way a program's is, and
checks each reply the ABI names, one line per case: a valid write of three bytes
(`ok`), `EBADF` for fd 2, `EFAULT` for a 4097-byte write, a range that crosses the
user limit, a range that wraps past 2^64, a pointer exactly at the limit, an
unmapped user page, a mapped kernel page, a range that crosses into an unmapped
second page, and `ENOSYS` for number 99. Only when every reply matches does it
print `syscall: refusals ok`; a mismatch halts the boot with `syscall self test
failed`.

Capabilities do not gate the syscall ABI in this release. The capability model
([Capabilities](/language/capabilities)) grants a kernel module device registers
and frames at build time, from the manifest; it has no per-process handle that a
program could hold and pass in a call. The one resource a program reaches,
stdout, is already the only fd `write` accepts, so the fd check is the gate for
it. A per-process capability table is the design a later process model would
need, and it is not started here.
Program one calls `write(1, "hello from user\n", 16)`, then
`write(1, 0x80000000, 16)` (a mapped kernel page), builds `bad write -> X` on its
stack, replaces `X` with `55 + (-a0)` (the hex digit of the errno magnitude, so
`-14` prints `E`), writes it, and calls `exit(7)`. Program two loads from
`0x40000000`, which no leaf maps in its address space: the load page fault is
`scause` 13, the handler prints `user killed: scause 13` and leaves, and the
kernel prints `kernel survived`.

```sh
kelpc boot kelpc/tests/fixtures/examples/kernel0-user
```

```text
kelpc boot: booted .../examples/kernel0-user and the UART printed:
user: m-mode
user: s-mode
user: paging on
user: frame ok
ok
syscall: refusals ok
hello from user
user: efault ok
bad write -> E
user exited 7
user killed: scause 13
kernel survived
```

The `ok` line is the self test's one valid write; it comes before the refusals
line because the self test runs first.

What is deliberately **not** here: no scheduler (one process at a time, one hart,
no run queue and no context switch between two live programs, since program two
starts only after program one has ended), no preemption (no timer interrupt is
armed, so a spinning program is never killed), no `fork`, `exec`, `wait` or
process teardown (pages are never freed and no address space is ever reused), no
ASIDs or TLB shootdown, no copy-on-write, demand paging, guard pages or address
space abstraction, and no interrupt path (`trap_entry` assumes the trap came from
U-mode; a kernel-mode fault would swap the stack pointer out from under the
running handler). There are no signals, and six argument words is the most a call
takes.
The timer-driven scheduler in the next section is a separate image,
`kelpc/tests/fixtures/examples/kernel0-sched`.

## A timer interrupt and a preemptive scheduler

`kelpc/tests/fixtures/examples/kernel0-sched` shows the machine timer and a
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
KELPC=<kelpc> kelpc/tests/fixtures/examples/kernel0-sched/run.sh
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
`kelpc/tests/fixtures/examples/kernel0-caps` adds the two device-value domains beside it: a narrowed
`irq` grant and a narrowed `frames` grant; see [below](#irq-lines-and-frames-as-capabilities).

The four RISC-V boots, run one after another:

```text
kelpc boot: booted .../examples/kernel0-trap and the UART printed:
trap: ecall
done
run.sh: booted .../examples/kernel0-panic and the UART printed:
panic: Array.get: index out of bounds
kelpc boot: booted .../examples/kernel0-bss and the UART printed:
bss clear
kelpc boot: booted .../examples/kernel0-heap and the UART printed:
heap sum 55
balanced
```

And the aarch64 boot, on QEMU's `virt` machine with `-cpu cortex-a57`:

```sh
kelpc boot kelpc/tests/fixtures/examples/kernel0-aarch64
```

```text
kelpc boot: booted .../examples/kernel0-aarch64 and the UART printed:
hello from kelp (aarch64)
```

## Stack guards and probing

`kelpc/tests/fixtures/examples/kernel0-stack` is the overflow made loud. Every function a freestanding
LLVM build emits carries LLVM's `"probe-stack"="inline-asm"` attribute, so a
frame larger than one page is built by touching each page in order from the top;
a frame that reaches the guard page below the stack faults instead of a single
`sub sp` stepping over the hole. Hosted builds carry no attribute, because a
hosted process has no guard page to probe for.

The linker script puts an unmapped 4 KiB guard page below the 16 KiB trap stack,
and a second one below the 8 KiB kernel stack, with the kernel stack above its
guard. `kmain` identity maps the image up to `__trap_guard_bottom`, then
`[__trap_guard_top, __guard_bottom)` and `[__guard_top, __frames_end)`, and it
leaves each guard page with no leaf.

One boot takes three faults on purpose. Phase t stores into the trap stack's
guard, and the handler, which runs on the trap stack, prints it and resumes
phase a at the top of the kernel stack. Phase a recurses with a 16-byte frame
until the frame that crosses `__stack_bottom` stores its saved `ra` into the
kernel guard; the S-mode handler prints the `scause` and `stval` it saw, checks
`stval` against both guard bounds and, for the first two faults, points `sepc`
at the next phase and returns. Phase b calls a function whose single
`[u8; 16384]` frame is larger than the whole kernel stack: the probe walks it
down page by page into the kernel guard, which is the case a `sub sp` alone would
miss.

```sh
kelpc boot kelpc/tests/fixtures/examples/kernel0-stack
```

```text
kelpc boot: booted .../examples/kernel0-stack and the UART printed:
stack: m-mode
stack: paging on
stack: guard 0x80009000 0x8000a000
stack: trap guard 0x80004000 0x80005000
stack: phase t
stack overflow: scause 0xf stval 0x80004ff8
stack: stval in guard
stack: phase a
stack overflow: scause 0xf stval 0x80009ff8
stack: stval in guard
stack: phase b
stack overflow: scause 0xf stval 0x80009da0
stack: stval in guard
stack: halted
```

Each stack has its own hole. The trap stack's guard is one page below the trap
stack, so a store into it faults (phase t) before the handler, which runs on the
trap stack, has anything to say about the kernel stack. The kernel stack's guard
is one page below the kernel stack and takes the two overflows (phases a and b).
Every fault is `scause 0xf`, a store page fault, and each `stval` falls inside
one of the two guards the kernel printed. `kelpc boot` asserts the `stack:` lines,
and the suite's boot test parses both bounds and all three fault addresses to
check the same ranges independently.

The guards sit in the linker script, in this order from the bottom: the trap
stack's guard, the trap stack (16 KiB), the kernel stack's guard, the kernel
stack (8 KiB). The identity map covers the image and the trap stack, skips each
guard page, and covers the kernel stack and the page frames above it.

What this is not: the guard pages are the linker script's, not the compiler's
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
  `kelpc/tests/fixtures/examples/kernel0-sched` ([above](#a-timer-interrupt-and-a-preemptive-scheduler)),
  and an x86-64 IDT with four exception gates and the PIC+PIT timer is
  `kelpc/tests/fixtures/examples/kernel0-x86_64-idt`
  ([above](#x86-64-interrupts-the-idt-the-exceptions-and-the-timer)). Both are
  naked bodies the compiler does not model as handlers. `kernel0-trap` still
  installs `mtvec` itself and enables nothing, and the line `kernel0-caps`
  claims is still not wired to a handler. Panic semantics with no OS, the row's
  other half, is the [section above](#panic-location-and-the-double-panic).
- **Stack guards cover two of the kernel's stacks, not all of them.** The kernel
  stack and the trap stack of `kelpc/tests/fixtures/examples/kernel0-stack` have a guard page each.
  The task stacks of `kelpc/tests/fixtures/examples/kernel0-sched` are `[u8; 4096]` in `.bss` and run
  in machine mode with no page table, so no page can be left unmapped under them.
  The per-hart stacks of `kelpc/tests/fixtures/examples/kernel0-percpu` and `kelpc/tests/fixtures/examples/kernel0-user`,
  and the stacks of the aarch64 and x86-64 examples, have no guard. Each needs
  its own page layout (or a PMP entry, for machine mode). Tracked in issue 255.
- **The calling-convention attributes** are still open. The `interrupt` attribute
  ships for riscv64 and x86-64 ([above](#the-interrupt-attribute)), except for the
  x86-64 vectors that push an error code.
- **`Ptr.free` has a sized form.** The global allocator reroutes
  `Box`/`List`/`Map`/`String`/`Bytes`, `Ptr.alloc` and `Ptr.try_alloc` go through
  the project's `[target] alloc`, and the [`std/arena`](/stdlib/arena) bump region
  is available. The no-argument `Ptr.free` stays refused in freestanding, because a
  project's `dealloc` needs the block's byte size and a pointer does not carry it.
  `Ptr.free_count(count)` closes that: it takes the element count the block was
  allocated with and passes `dealloc` the same size and alignment the allocation
  got, and a count whose size wraps panics instead (see
  [Freestanding mode](/language/freestanding#what-freestanding-keeps)).
- **Shipped:** user `Drop` ([`fun mut T.drop()`](/language/drop)), per-CPU
  statics ([Per-CPU storage](/language/percpu)), freestanding `String` and `Bytes`,
  the [`std/arena`](/stdlib/arena) bump region and `Ptr.try_alloc`, the stack
  guards of the kernel stack and the trap stack and the probe, the `mmio`, `irq` and `frames` grants, the
  [freestanding standard subset](/language/freestanding#the-freestanding-standard-subset),
  the x86-64 target, the machine timer with the preemptive scheduler, the x86-64
  IDT with the PIC and PIT timer, and the sized `Ptr.free_count`. The sections
  above show each one.
- **The remaining holes are the rest of the process model.** A
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


## The path to a kernel written in Kelp

Moved here from the retired `plan/kernel-path.md`. The text is kept as the record it was.

*A plan, not a Mark. It orders the existing MK9/MK10 items ([`meta/roadmap.md`](/meta/roadmap) block B) by what a first kernel
needs, names the milestone that proves each step, and records the one decision it changes.*

### The decision this changes

B-6 (freestanding mode) was **deferred on 2026-09-26** because "nothing concrete (an actual kernel, firmware
image or embedded target) is asking for this today" and it said to "revisit the moment a real freestanding
target exists". A kernel is now the stated goal, so that condition is met and the deferral is lifted. The
ambient-runtime assumption stays the default: freestanding is a mode a project opts into in `coral.toml`.

### The driver: "kernel 0"

A kernel that boots under QEMU's RISC-V `virt` machine (`qemu-system-riscv64 -machine virt -bios none
-nographic -kernel kernel.elf`, headless), sets up a stack, writes a line to the NS16550 UART at
`0x10000000`, and halts, **written in Kelp with no C and no libc**. Every stage below is justified by the
piece of kernel 0 it unlocks. The acceptance test is a script that boots the image under QEMU with a timeout
and compares the serial output.

**Why RISC-V `virt` and not x86-64 first.** QEMU's `-kernel` loads a 64-bit RISC-V ELF directly and starts it
at its entry point in a clean machine mode, and the UART is plain memory-mapped I/O, so kernel 0 exercises
raw pointers and `volatile` honestly. The x86-64 equivalent needed a 32-bit PVH stub that enters long mode
before any Kelp runs: real work, but it is bootstrapping, not language. It followed once the stages were in
(kernel stage 20, [`language/kernel.md`](/language/kernel)).

### Order, and why

| # | Stage (roadmap id) | What it adds | Unlocks in kernel 0 |
| --- | --- | --- | --- |
| 1 | **MK9-S2 unsafe and pointers** (B-3) | `unsafe` blocks, raw pointer type `ptr<T>`, offset/cast/addr, `read`/`write`, `read_volatile`/`write_volatile` | Talking to a device register and to memory the language did not allocate |
| 2 | **MK9-S1-M2 layout** (B-2) | `repr(C)`, `packed`, alignment, `size_of`/`align_of`/`offset_of`, explicit enum discriminants | Page-table entries, trap frames, device-register blocks |
| 3 | **MK9-S8 data formats** (B-10) | endianness conversion, unaligned load/store | Reading a boot-info structure, later a disk format |
| 4 | **MK9-S4-M1/M2 freestanding** (B-6) | a `freestanding` project mode: no libc, no runtime preamble, custom entry point, custom panic handler, linker script, section control, target triple, static ELF | An ELF QEMU can load and start |
| 5 | **MK9-S7-M1/M3 ISA surface** (B-9, B-16) | inline asm with operands and clobbers, naked functions, interrupt/calling-convention attributes | `wfi`, setting the stack pointer, CSR reads and writes, the trap vector, the first context switch |
| 6 | **MK9-S6-M1 `defer`, `Drop`** (B-8) | deterministic cleanup a kernel can point at | Releasing locks and frames on every exit path |
| 7 | **MK9-S5 allocators** (B-7) | a global allocator hook, arenas, alignment, fallible allocation | The first frame allocator and a kernel heap |
| 8 | **MK9-S3-M3 per-CPU storage** (B-11) | a per-CPU storage class | Per-CPU run queues, current-task pointers |
| 9 | **MK9-S4-M4/M5/M8** (B-12, B-13) | mapping/unmapping and page-table walks (done: Sv39, [`language/kernel.md`](/language/kernel)); a syscall ABI and untrusted-pointer validation (done: [`language/kernel.md`](/language/kernel)) | Userspace |
| 10 | **MK9-S7-M2, MK9-S6-M2** (B-14, B-15) | stack guards and probing; panic semantics with no OS | A kernel that fails loudly instead of silently |
| 11 | **MK10-S1** (C-3) | MMIO regions, IRQ lines and frames as *capabilities* (done) | The safety story: a driver can only touch what it was granted |

Stages 1-5 are kernel 0. 6-11 turn it into something that can run more than one thing.

**Status: stages 1 to 5 are done.** Stage 1 (MK9-S2 unsafe and pointers): `unsafe` blocks and
`unsafe fun`, the raw pointer type `Ptr<T>`,
`offset`/`byte_offset`/`cast`/`addr`/`is_null`, `read`/`write` and their volatile twins,
`Ptr.alloc`/`free`, and the `coral.toml` `[unsafe] modules` audit list all work on both backends
([`language/unsafe.md`](/language/unsafe)).

Stage 2 (MK9-S1-M2 layout control) adds `repr(c)` (the default, now guaranteed), `repr(packed)`
and `repr(align(N))`, the compile-time queries `size_of<T>()`/`align_of<T>()`/`offset_of<T>("field")`,
and explicit discriminants on a field-less enum with `repr(u8|u16|u32|u64|i8|i16|i32|i64)` storage
and `to_int`/`from_int`. Both backends write the same layout (`__attribute__((packed))`/`aligned(N)`
and a packed struct body or an alignment anchor), and the C helper in `tests/projects/ffi_layout`
checks the packed byte layout against a real C compiler
([`language/kernel.md`](/language/kernel)).

Stage 3 adds the integer byte-order conversions (`x.swap_bytes()`, `x.to_be()`, `x.to_le()`,
`u32.from_be(x)`, `u32.from_le(x)` for every integer wider than a byte), the bounds-checked
`Bytes.read_*_le/be`/`write_*_le/be` accessors with no alignment requirement, and
`Ptr.read_unaligned`/`write_unaligned`. `to_le` is the identity because the target is
little-endian, asked of the target's own data layout on LLVM and of `__BYTE_ORDER__` on C, so a
big-endian target swaps instead ([`language/unsafe.md`](/language/unsafe)).

Stage 4 (MK9-S4-M1/M2 freestanding, LLVM-only by design) adds a `coral.toml` `[target]`
section (`mode`, `triple`, `entry`, `linker_script`, optional `panic`), the LLVM target machine
for a non-host triple (static relocation, medium code model, `generic-rv64`/`+m,+a,+c` for
riscv64), a compiler-emitted `_start` stub that sets `sp` from `__stack_top` and calls the
entry, the `section("...")` clause on a top-level `const`/`fun` (integer-array consts emitted
as read-only data in their section), and an `ld.lld -T <script>` link with no libc and no
runtime object. The allowed set (no `print`, no `panic`/`assert` builtins, no heap types, no
`std/*` except `std/atomic`, `std/option` and `std/result`, no `pd`) is enforced by
`kelpc check` and `kelpc build` alike, and the overflow and bounds checks call the project's
`panic` handler or a default infinite loop. The acceptance artifact is
`tests/projects/freestanding_min`, checked with the llvm tools under `shell.nix`
([`language/freestanding.md`](/language/freestanding), [`language/unsafe-ub-catalogue.md`](/language/unsafe-ub-catalogue)).

Stage 5 (MK9-S7-M1/M3 ISA surface, roadmap B-9/B-16) adds the statement and expression
`asm("<template>", in("...") e, out("...") place, inout("...") place, clobber("..."), volatile,
nomem, nostack)`, legal only inside `unsafe` and therefore only in a module the manifest
lists under `[unsafe] modules`; the anonymous `out("...") _` is the expression's value (`i64`
when the context names no type); and `naked fun`, whose body must be exactly one `asm` and
which lowers to LLVM's `naked` plus `noinline` (`__attribute__((naked, noinline))` on C) with
no prologue or epilogue. One template reads destination-first everywhere: the dialect is
Intel on x86 and the target's own syntax elsewhere, chosen per target so both backends
assemble the same text. Both backends carry the feature: LLVM through `LLVMGetInlineAsm` and
LLVM's `naked`/`noinline` enum attributes, the C oracle through GCC's extended asm and
`__attribute__((naked, noinline))`, and the run fixtures pass on both. `interrupt` and
calling-convention attributes are out of scope for this stage: a naked function whose body is
one `asm` covers a trap vector without them. [`language/unsafe.md`](/language/unsafe) is the design and
[`language/unsafe-ub-catalogue.md`](/language/unsafe-ub-catalogue) carries the stage's undefined behaviour.

**Kernel 0 boots.** The pieces above are now wired into `kelpc/tests/fixtures/examples/kernel0`: a `[target]`
freestanding riscv64 project whose `kmain` polls the NS16550 UART's LSR bit 5 and writes
`hello from kelp` to THR through `Ptr<u8>` volatile stores, then halts on `wfi`;
`kelpc/tests/fixtures/examples/kernel0-trap` installs `mtvec` at a naked handler, takes an `ecall`, prints
`trap: ecall` from the handler and `done` after `mret`. Both are built with `kelpc` and booted
under `timeout 20 qemu-system-riscv64 -machine virt -bios none -nographic -no-reboot
-serial mon:stdio -kernel <elf>`; `kelpc/tests/fixtures/examples/kernel0` and `kelpc/tests/fixtures/examples/kernel0-trap`
read QEMU's own stdout and assert the expected lines, and
`cargo test --test compile_and_run kernel0` runs both where the tools are present. No
compiler change was needed. What the examples could not do is in [`language/kernel.md`](/language/kernel), in
order: a libc-free `str` surface, an address-of-function form (plus the `interrupt` attribute
stage 5 deferred), and a usable panic message.

**Stage 7 closed two of those three.** A freestanding program now has `str.len`,
`str.byte`, `str.eq`, `str.starts_with` and `str.ptr`, lowered as byte loops inside
the module by the LLVM backend (no `strlen`, no C object), with every other
`std/str` function refused by name and pruned from the program before inference;
`kelpc/tests/fixtures/examples/kernel0` prints its greeting through `puts(s: str)` and its panic
handler prints `panic: ` plus the compiler's own message, and the new
`kelpc/tests/fixtures/examples/kernel0-panic` proves it by reading one element past an array on
purpose.

**Kernel gap 2 (the address of a function) is closed.** `Ptr.from_fn(f)` is the
address of a declared `fun` or a `fun` literal that captured nothing, as a
checked `Ptr<u8>`, legal outside `unsafe` on both backends; a closure is refused
by name, because it carries an environment its code address cannot describe. A
top-level `fun` may carry `align(N)` (a power of two up to 4096), lowered as the
function's alignment on both backends. `kelpc/tests/fixtures/examples/kernel0-trap` installs its
trap vector with `Ptr.from_fn(trap_handler).addr()` and names no mangled symbol,
and [`language/unsafe-ub-catalogue.md`](/language/unsafe-ub-catalogue) stage 8 is the UB catalogue for the new surface.
The calling-convention attributes stage 5 deferred are the remaining half of that
hole; the `interrupt` attribute ships ([above](#the-interrupt-attribute)).

**Stage 6's `defer` half is done** (MK9-S6-M1, [`language/statics-and-defer.md`](/language/statics-and-defer)): `defer EXPR` is a
statement whose action runs when its block is left, on every ordinary exit, last-in-first-out
against the block's other defers, by a lowering that duplicates the action at each exit before
type checking so both backends run ordinary code. A `defer` and a `?` in one block is refused
by name, a `return` inside a deferred action is refused, and a local moved before the exit is
the ordinary use-of-a-moved-value error. Both a hosted fixture set and a freestanding riscv64
project that releases a lock flag with a `defer` are in the suite.

**Stage 6's `Drop` half is done too** (MK9-S6-M1, [`language/drop.md`](/language/drop)): `fun mut T.drop()` on a
user `datac`/`enum` is that type's destructor, the same "the method name is the declaration"
shape A-12 slice 1 gave a declared `Map` key pair, so no trait keyword and no new syntax. The
generated `kelp_drop_<T>` calls the user body first and drops the fields after, on both
backends, so every drop point the `DropPlan` already had (block end, before `return`, owned
reassignment, a container element, a containing `datac`/`enum`, the `atexit` pd drop) reaches
it unchanged; a destructor type is excluded from every derived-copy fixpoint, so it is not
`Copy`, and an explicit `g.drop()` is refused by name. The fixtures cover order, early return,
reassignment, container removal, a moved-out value, an `enum` variant, a closure capture and
the RAII atomic lock guard, and a freestanding riscv64 project releases a lock flag through a
destructor with no undefined symbol. Both `defer` and `Drop` still have no panic-path cleanup:
there is no unwinding (`kelp issue #245` §2), so a panic leaks the frame.

**Row 7's hook half is done** (MK9-S5-M1, [`language/freestanding.md`](/language/freestanding)): a freestanding
manifest may name `alloc`, `dealloc` and an optional `realloc` in `[target]`, and
`Box<T>`, `List<T>` and `Map<V>` of allowed element types then allocate and free
through them instead of libc, on the LLVM backend that freestanding mode is.
Without the pair the three containers are refused exactly as before, with a
message that names the keys; `Thread` stays refused either way, and `View` is
admitted later (kernel stage 23) with `View.to_string` in the allocator set. A
failed
allocation reaches the project's panic handler with "out of memory".
`kelpc/tests/fixtures/examples/kernel0-heap` is the idiom: a bump allocator over a `static mut`
arena, a `List<i32>` of 1..=10, and a counting wrapper that prints `balanced`
when every allocation reached a matching free. Arenas as a language feature and
a fallible allocation surface are not in this stage.

**Row 7's `String`/`Bytes` half is done too** (MK9-S5-M2,
[`language/freestanding.md`](/language/freestanding)): with an allocator configured, `String` and
`Bytes` become legal and the operations a kernel needs - the constructors, the
length and byte accessors, `push`/`push_str`, `clone`, `reserve`, `clear`,
`str.concat` and the integer-to-text builders, and drop - are emitted as
libc-free byte loops into the object, growing by doubling through the project's
`realloc` when one is named and alloc + copy + dealloc otherwise. Every other
`String`/`Bytes`/`std/str` operation is refused at the call with "needs the
hosted runtime" (including `str.from_f64`), so nothing is left for the linker to
report. `kelpc/tests/fixtures/examples/kernel0-string` is the acceptance: it concatenates, formats
an integer, grows a `Bytes` past several doublings, prints four lines through
the UART under QEMU and proves `ALLOCS == DEALLOCS`; `llvm-nm -u` stays clean.
Without an allocator `String`/`Bytes` stay refused, and `Thread` stays
refused either way; `View` is admitted in stage 23.

**Row 7's arena and fallible-allocation halves are done too** (MK9-S5-M3,
[`stdlib/arena.md`](/stdlib/arena)): `Ptr.try_alloc<T>(count)` is `Ptr.alloc`'s non-panicking twin,
`unsafe` and aligned for `T`, libc's `malloc` on both hosted backends and the
manifest's own `[target] alloc` in a freestanding image, with a byte count that
would wrap `usize` answered by the null pointer rather than a short block. The
shipped `std/arena` is a bump arena over a caller-owned byte region, written in
Kelp with no libc call, so it is legal in a hosted program and in a freestanding
image with no allocator at all: `alloc(size, align)` aligns the returned
*address*, returns the null `Ptr<u8>` when the padded end would exceed `cap` or
wrap, and panics on a non-power-of-two `align`; `reset`, `used` and `remaining`
are the rest. `alloc_zeroed` writes through the returned pointer, which is why
`std/arena` is the first shipped module on the compiler's own `[unsafe]` list
(`stdlib::UNSAFE_MODULES`, consulted by `resolve.rs` beside the manifest's). The
acceptance is a hosted pair of fixtures/projects on both backends plus two
riscv64 freestanding projects under QEMU - one carving a `static mut [u8; 4096]`
arena with no allocator, one proving `Ptr.try_alloc` reaches the project's own
allocator - both with `llvm-nm -u` clean. Layouting a `Ptr<T>` `datac` field was
the one compiler-side change the arena needed; it is the same one-pointer reply
the opaque handle already had.

**Row 8's per-CPU half is done** (MK9-S3-M3, [`language/percpu.md`](/language/percpu)): a freestanding
project may write `percpu static mut NAME: T = INIT`, and a manifest's
`[target] cpus = N` (1 to 64, default 1) makes it `N` copies laid out as one
64-byte-aligned array in `.percpu`, indexed by the new `cpu_index()` intrinsic
(`tp` on riscv64, `TPIDR_EL1` on aarch64; the kernel sets the register).
`cpu_count()` folds to the manifest's constant, a `percpu` without `mut` is
refused, and both the class and the intrinsics are freestanding-only, refused
by `infer.rs` on both backends. The riscv64 `_start` stub now parks every hart
whose `mhartid` is not zero before it loads `sp`, so a `-smp 2` image with no
firmware does not have two harts racing through boot;
`kelpc/tests/fixtures/examples/kernel0-percpu` boots one, writes a per-CPU static on hart 0,
reads the other copy by setting `tp = 1` by hand, and asserts the four lines
from QEMU's stdout. A per-CPU allocator or run queue is still a kernel design,
not this stage.

**Row 11's MMIO half is done** (MK10-S1, roadmap C-3, [`language/capabilities.md`](/language/capabilities)):
the capability model now reaches devices. A new `mmio` domain takes a list of
half-open address ranges (`caps(mmio = ["0x10000000+0x100"])`) or the whole
address space as `["*"]`, and a freestanding `Ptr.from_addr` is a compile error
unless the module holds a grant that covers the address a constant expression
names, or holds `["*"]` for an address the compiler cannot fold. The grant lives
where every other domain's does, except that the entry module does **not** hold
`mmio` by default: the address of a device is a fact about the machine, so it
has to be written down in the manifest's `[caps]` section and delegated to a
driver with `impl "uart" caps(mmio = [...])`. `caps(*)` deliberately skips
`mmio`, so the whole-address-space escape hatch is always visible. Every
`examples/kernel0*` manifest grew a `[caps]` section and every driver its grant,
and all thirteen still boot under QEMU; `kelpc/tests/mmio.rs` covers the
accepting and refusing shapes with `kelpc check` (front end only, no `ld.lld`).
The check is on the address a pointer is *born* at, so an offset applied later
is not revisited; IRQ lines and physical frames are the rest of the row.

**Row 11's IRQ-line and frame halves are done too** (MK10-S1, roadmap C-3,
[`stdlib/irq.md`](/stdlib/irq)): the two remaining device capabilities are domains
now, `irq` with decimal line numbers and inclusive ranges
(`caps(irq = ["10", "32-47"])`) and `frames` with the same `BASE+LEN` byte
windows `mmio` uses, parsed and validated by the same code. A line or a frame
is a *value*: `irq.claim(n)` and `frame.claim(addr)` are gated constructors in
the shipped `std/irq` and `std/frame`, so a driver can be handed exactly what
it was granted, and a `Line`/`Frame`'s constructor is sealed to its module so
another module can only get one from a claim. A constant argument must fall
inside a granted range, a `frames` address must be 4096-aligned (a compile
error for a constant and a panic for a computed one), and a computed argument
needs the whole-resource `["*"]`. Unlike `mmio`, the check is in `infer.rs` and
applies to a hosted program and a freestanding image alike; the entry module
holds both domains by default, so a kernel narrows them in its `[caps]`
section. `kelpc/tests/fixtures/examples/kernel0-caps` is the acceptance, `kelpc/tests/irq_frames.rs`
the accepting and refusing front-end cases, and every other `examples/kernel0*`
image still boots.

**Stage 20 (a second ISA family) is done.** `[target] triple = "x86_64-unknown-none"`
(the `-elf` spelling too) now gets the X86 target machine and an x86-64 `_start` stub:
a `.note.Xen` `XEN_ELFNOTE_PHYS32_ENTRY` (type 18) note naming the entry, `.code32` code
that loads a GDT with a 64-bit code segment, builds an identity map for the first 1 GiB out
of 2 MiB pages in a `.boot_pt` NOBITS section, enables PAE and `EFER.LME`, loads CR3 and
sets `CR0.PG|PE`, then far-jumps into `.code64`, loads `rsp` from `__stack_top`, clears
`[__bss_start, __bss_end)`, turns SSE on and calls the entry; every emitted function is
`noredzone`. The manifest gets the `x86-64` CPU, the static relocation model and the
**small** code model, which is what links an image at 1 MiB. `kelpc/tests/fixtures/examples/kernel0-x86_64` is
the COM1 port-I/O driver (`hello from kelp (x86_64)`), and `kelpc/tests/fixtures/examples/kernel0-x86_64-lmode`
reads CR0/CR4/EFER through `asm`, prints `long mode on` and then takes a `ud2` with no IDT,
so it triple-faults; both boot under `qemu-system-x86_64 -M q35 -cpu qemu64 -no-reboot` and
three tests in `kelpc/tests/compile_and_run.rs` cover the ELF (the PVH note included) and
the two boots. What is not there: interrupts and an IDT, the APIC, SMP and ACPI;
`cpu_index()` has no x86-64 lowering, so a `percpu` static is refused by name.

**Release goal 3's freestanding standard subset is done** (kernel stage 19,
[`language/freestanding.md`](/language/freestanding)). `freestanding.rs` decides each shipped `std/*`
module with one table row (`Pure`, `Allocator`, `Subset`, `Present`,
`Hosted`) instead of two hand-kept lists, the call-site check and `prune` are
driven by the same row, and a whole-module refusal names the modules a
freestanding project may implement. Newly admitted: `std/math`'s integer
`abs`/`min`/`max`/`clamp`, and, with the `[target] alloc`/`dealloc` pair,
`std/list` and the `std/option`/`std/result` callback combinators. The
admitted list is `std/arena`, `std/atomic`, `std/frame`, `std/irq`,
`std/list`, `std/math`, `std/option`, `std/regex`, `std/result`, `std/str`; every
other module is refused by name with "needs a hosted runtime". `std/math`'s libm
externs and `f64` overloads and the rest of `std/str` are refused by name
inside the admitted module, and `std/mem` stays refused because its
`alloc_raw` is libc `malloc`. The `tests/projects/freestanding_std_*`
fixtures build with zero undefined symbols, and `freestanding_std_kernel`
boots under QEMU printing `option`/`result`/`arena` results over the UART.

**Kernel stage 23 closed the two gaps [`stdlib/regex.md`](/stdlib/regex) recorded.** A `datac`
whose fields include a `String` now compares and hashes in a freestanding image:
the derived key equality the compiler emits for every keyable type called the
hosted `kelp_map_key_eq`, and the LLVM backend now writes that helper into the
module as the same length-aware byte loop `View.eq` uses. `View` itself is a
borrowed two-word value with no storage, so `len`/`is_empty`/`get`/`slice`/`eq`
are admitted (with `View.to_string` in the allocator-only set) and the two
missing bodies are emitted. With both in place `std/regex` moved from the
hosted-only list to the allocator row of the table: `kelpc/tests/fixtures/examples/kernel0-eq` and
`kelpc/tests/fixtures/examples/kernel0-eq-x86_64` compare a `String`-field and a `Bytes`-field
`datac`, look the first up in a `Map`, slice a view, and match `[a-z]+(\d+)`
under QEMU on riscv64 and x86-64.
[`language/freestanding.md`](/language/freestanding) and [`stdlib/regex.md`](/stdlib/regex) carry the detail.

**What the next stages need.** `defer`/`Drop` (row 6), the whole of row 7 (the allocator hook,
arenas and the fallible allocation surface), per-CPU storage (row 8), mapping plus the syscall
ABI (row 9), both halves of row 10 (guards and probing, panic semantics) and the whole of row 11
(MMIO ranges, IRQ lines and physical frames) are all done. The language work the kernel path
names is complete; §"What is deliberately not here" is what is left.

**Stage 10 (a second architecture) is done.** The `_start` stub and the target machine are now
chosen by the manifest's `[target] triple` instead of assuming riscv64: `riscv64` keeps
`generic-rv64`/`+m,+a,+c`, the medium code model and the `la sp` stub, and `aarch64-unknown-none`
gets the `generic` CPU, the **small** code model (LLVM refuses medium on AArch64) and an AArch64
stub that loads `sp` with `ldr x0, =__stack_top; mov sp, x0`, clears `[__bss_start, __bss_end)`
the same word at a time and halts on `wfe`. Any other triple is refused by name at the stub.
`kelpc/tests/fixtures/examples/kernel0-aarch64` is the PL011 driver (`DR` at `0x09000000`, `FR` bit 5 the FIFO-full
flag) whose `kmain` prints `hello from kelp (aarch64)` and halts; it boots under
`qemu-system-aarch64 -M virt -cpu cortex-a57 -nographic -serial mon:stdio -kernel <elf>` and
`kelpc/tests/fixtures/examples/kernel0-aarch64` and two tests in `kelpc/tests/compile_and_run.rs` (an
`llvm-readelf`/`llvm-nm`/`llvm-objdump` check of the ELF and the boot) cover it. The riscv64
`examples/kernel0*` all still boot after the change.

**Row 9's mapping half is done** (MK9-S4-M8, [`language/kernel.md`](/language/kernel)): `kelpc/tests/fixtures/examples/kernel0-vm`
builds Sv39 tables in Kelp (the PTE bits, the VPN split, the PTE and `satp` encoders, a zeroing
frame allocator over the linker script's `__frames_start`..`__frames_end`, `map_page`,
`map_range`, `unmap_page` and `translate`), identity-maps the image and the UART, maps a page at
`0x3F_FFFF_F000`, drops from machine mode to supervisor mode through `pmpaddr0`/`medeleg`/`mstatus`
and `mret`, turns the MMU on, and proves the high virtual name and the identity-mapped physical
name are one frame. `kelpc/tests/fixtures/examples/kernel0-vm-fault` takes a load page fault (13) and a store page
fault (15) on purpose into a naked S-mode `stvec` handler that prints `scause` and `stval`. No
compiler change was needed: the only thing the language could not spell is a linker-script symbol,
and that is stage 5's `asm` with `la`. What this stage deliberately leaves out is TLB
shootdown, ASIDs, huge-page *creation*, Sv48 and a per-section (W^X) identity map.

**Row 9's other half is done too** (MK9-S4-M9, [`language/kernel.md`](/language/kernel)):
`kelpc/tests/fixtures/examples/kernel0-user` adds the `TrapFrame` and the naked `trap_entry` that builds it on a
per-hart trap stack (swapping `sp` with `sscratch`), the drop to U-mode through `sepc`,
`sstatus.SPP` and `sret`, one Sv39 address space per program with its code page at `0x10000` and
its stack page at `0x20000`, the `ecall` ABI (number in `a7`, arguments in `a0`..`a5`, result in
`a0`, a negative result an error) with `write` and `exit`, and the untrusted-pointer check that
makes `write` safe: a length cap, a range bound that cannot wrap before it is checked, and a
page-table walk that demands the U and R bits on every page before a byte is copied through a
kernel buffer. Two hand-written programs prove it, one ending in `exit(7)` and one dying on a
load page fault while the kernel prints the cause and keeps running. No compiler change was
needed, and what the stage leaves out is the process model: no scheduler, one process at a time,
no preemption or timer interrupt, no `fork`, no TLB shootdown, no ASIDs, no huge-page *creation*,
no Sv48 and no per-section (W^X) identity map.

**Row 10's stack half is done** (MK9-S7-M2, [`language/kernel.md`](/language/kernel)): every function a freestanding
LLVM build emits carries `probe-stack="inline-asm"`, so a frame larger than a page touches each
page in order and a guard page catches the overflow instead of the frame stepping over it;
hosted builds carry no attribute. `kelpc/tests/fixtures/examples/kernel0-stack` is the acceptance: an Sv39 riscv64
kernel whose kernel stack sits above an unmapped guard page, with a 16 KiB trap stack below the
hole, and a guard page under the trap stack too. One boot stores into the trap stack's guard,
then recurses with a small frame into the kernel guard, and the S-mode handler reports `scause`
and `stval` on the trap stack each time and resumes at the top of the kernel stack; the last
phase overflows the kernel guard with one `[u8; 16384]` frame. What the example forced is a
lowering fix: `[v; N]` now fills the local's own slot in place (`{array}__fill_into`) rather than
returning the array by value, because LLVM's instcombine exhausted memory folding the by-value
store of a frame-sized array at `-O2`.

**Row 10's panic half is done too** (MK9-S6-M2, [`language/freestanding.md`](/language/freestanding)): a freestanding panic
handler may be declared `fun(msg: str)` as before or
`fun(msg: str, file: str, line: u32)`, and the compiler refuses any other shape by name. Every
check calls one compiler-emitted entry that exchanges a `.bss` flag (so a check inside the handler
does not recurse) and, on re-entry, calls `kelp_double_panic`, which the compiler defines weakly as
a `wfi`/`wfe` loop and a project may override with a strong definition. The file and line are the
same per-statement `SourceMap` values the hosted line tables carry; generated accessor bodies read
them from two `.bss` globals the current statement stored. `kelpc/tests/fixtures/examples/kernel0-panic2` boots one
phase per check (array bounds, narrowing, `str.byte`, the `panic` builtin, `option.unwrap`, and a
double panic) and asserts each exact line; [`language/freestanding.md`](/language/freestanding) has the check table and
records that overflow wraps and division by zero stays an unchecked UB, so neither has a message.

**Kernel stage 21 is done: a timer interrupt and a preemptive round-robin scheduler**
([`language/kernel.md`](/language/kernel)). `kelpc/tests/fixtures/examples/kernel0-sched` is a bare-metal riscv64 image, still in machine
mode with no paging, that programs the CLINT's machine timer (`mtimecmp` at `0x02004000 + 8 *
hart`, `mtime` at `0x0200BFF8`, granted as exactly those two windows), enables `mie.MTIE` and
`mstatus.MIE`, and handles the interrupt in a naked `trap_entry` that saves all 31 general
registers, `mepc` and `mstatus` into the current task's frame in a `static mut [Task; 3]` table,
calls `schedule(frame)` and restores whichever frame it returns, ending in `mret`. Three tasks
that never yield each loop forever over their own counter and print `A`/`B`/`C` every 50000
iterations through an `Atomic<bool>` spin lock released by `defer`, so the letters can only
interleave because the timer preempted them; the kernel stops itself after 40 ticks with
`sched: done ticks=40`. `kelpc/tests/fixtures/examples/kernel0-sched/run.sh` boot-asserts all three letters, at least
three letter transitions and no torn line from QEMU's own stdout, and a test in
`compile_and_run.rs` runs it. The one compiler change is the table's type: an array static's
element may now be a `datac` or another array (recursively), which `tests/projects/static_datac_array`
pins on both backends, and `tests/projects/sched_task_layout` pins the layout the naked entry
hardcodes. In this stage: the timer interrupt and preemptive round-robin in M-mode. Not in it:
priorities, blocking, task exit, SMP, and preemption of user mode, which is why the U-mode process
of [`language/kernel.md`](/language/kernel) is still one program at a time.

**Kernel stage 22 is done: the x86-64 IDT, the CPU exceptions and the PIC+PIT timer**
([`language/kernel.md`](/language/kernel)). `kelpc/tests/fixtures/examples/kernel0-x86_64-idt` is a freestanding x86-64 image whose
`static mut IDT: [IdtEntry; 256]` gets five gates from `Ptr.from_fn(gate).addr()` - `#DE` 0,
`#UD` 6, `#GP` 13, `#PF` 14 and the timer's 32 - each a `repr(c)` 16-byte descriptor with
the offset split in three, selector `0x08` (the boot GDT's code segment), IST 0 and type
`0x8E`, loaded with `lidt [descriptor]` through `asm`. A gate is a naked function: it pushes
a dummy error code where the CPU pushed none, pushes its vector number and the fifteen
general registers into a `repr(c) TrapFrame`, calls a Kelp `trap_dispatch(frame)`, restores
and `iretq`s. The dispatcher prints `exception <vector> err <code> rip <hex>` (plus
`cr2 <hex>` for `#PF`) over COM1, resumes `#UD` and `#DE` by adding the faulting
instruction's length to the saved `rip`, and halts on `#GP`/`#PF`. The boot also remaps the
8259 pair (ICW1-4, master 32..39, slave 40..47), unmasks IRQ0 only, programs PIT channel 0
for about 100 Hz, and counts five ticks with an `outb(0x20, 0x20)` EOI each; the last act
is a store through an unmapped page, whose `#PF` report is the last line the serial port
sees. The gates read the dispatcher's address through the GS base rather than an `asm`
operand, because an operand is materialised into a register before the gate has saved
anything. Not in this stage: the APIC, SMP, ACPI, a TSS/IST stack and x86 user mode.

**Polyp's renderer is proved freestanding** (Polyp v3 stage 4, `design/polyp-v3`): `kelpc/tests/fixtures/examples/polyp-fb-riscv64`
and `kelpc/tests/fixtures/examples/polyp-fb-x86_64` boot the v3 core, the software raster and the soft backend on both targets and
draw the hosted run's exact pixels with no libc, which is the "custom operating system with a framebuffer"
case the kernel path wanted and `kelpc/tests/fixtures/examples/polyp/PLATFORM.md` is the contract it hands an OS.

### Two rules that keep the language honest

1. **`unsafe` is auditable, not ambient.** A module may contain `unsafe` only if `coral.toml` lists it
   (`[unsafe]` with `modules = [...]`), the same shape as `[extern.*]`: the set of modules that can leave the
   checked language is a short, reviewable list, and a dependency cannot grant itself the power.
2. **Both backends, always.** LLVM is the default backend and C is the oracle. A stage is not done until both
   produce the same observable behaviour, and freestanding output is an LLVM-backend feature first (the C
   backend's runtime preamble is libc), with the C oracle covering the hosted parts.

### What is deliberately not here

- A specific kernel design beyond the round-robin scheduler of kernel stage 21: priorities, blocking,
  a filesystem and drivers are still not here. The language work above is what they would sit on.
- x86-64 interrupts beyond the IDT and the PIC+PIT timer, the APIC, SMP and ACPI: the
  architecture boots, runs Kelp and takes its own exceptions and timer ticks (kernel stages
  20 and 22, [`language/kernel.md`](/language/kernel) and [`language/kernel.md`](/language/kernel)), and what a kernel still needs there is
  a local APIC, an I/O APIC, ACPI enumeration and x86 user mode. [`language/kernel.md`](/language/kernel)'s
  trap gap and stage 5's deferred `interrupt` attribute are the same hole on riscv64.
- Memory-safety proofs about `unsafe` code. D-1/D-2/D-3 stay open; the UB catalogue has to grow a section per
  stage, and each stage's design note says what it adds to it.
