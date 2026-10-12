---
title: "Capability threat model"
description: "What the capability system protects, who it assumes the attacker is, what is out of scope, the nine holes the attack tests found and closed (as behaviour changes), and the three gaps that are still open."
isPublished: true
tags: "reference, capability"
---
> **Note:** The C oracle that some runs below compare against, and the `KELPC_ORACLE=c` switch, were removed on 2026-10-10. Every `KELPC_ORACLE` setting is now refused by name. Read the runs marked with that switch as a record of the time they were made.

[Capabilities](/language/capabilities) say what a module may do. This page says
what that promise is worth: what is being protected, against whom, what the
compiler and runtime actually check, and where the promise stops. The design
notes are
[`plan/threat-model.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/threat-model.md)
and the attacks are
[`kelpc/tests/threat_model.rs`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/kelpc/tests/threat_model.rs):
75 tests, most of them one per numbered attack, each playing an author who holds
a narrow grant and tries to get more. An attack that works is a bug and its test stays as
the regression; a hole too large to close is `#[ignore]`d with the reason, never
deleted.

## Assets

- Files outside a module's `fs` grant.
- Programs a module may not start, and processes it may not signal.
- Environment variables outside the `env` grant (and the loader variables such as
  `LD_PRELOAD` that change what a later process does).
- Hosts, ports and network interfaces outside the `net` grant.
- Device authority: `mmio` ranges, `irq` lines, `frames`.
- The audit lists: `[unsafe] modules` and `[extern."module"]`.
- Descriptors another module opened.

## The attacker

1. **A program author** whose manifest grants a narrow window and who wants more.
2. **A dependency author**: a module in `src/` that holds fewer grants than the
   module that imports it, and can write any Kelp source. There is no separate
   dependency loader, so a dependency's authority is exactly what its importers
   delegate to it.

## In scope, out of scope

**In scope:** the compiler's gates (module resolution and the call-site checks),
the checking code the compiler links into every program (path normalization and
symlink resolution, host and port matching), the standard library's own bodies
and externs, and the manifest validators.

**Out of scope**, and so not something a grant can promise:

- The C compiler, the linker, the operating system and other processes.
- Native code reached through a granted FFI section or a granted program. A
  `process` grant for a shell is a grant of everything the shell can run.
- Races with another process that changes the filesystem between the check and
  the use (TOCTOU).
- A granted module's own bugs: a helper that reads any path for its caller uses
  *its* grant, and its callers get that reach (a confused deputy is by design).
- DNS trust: a `net` grant on `example.com` trusts whatever the resolver says.
- The manifest author, who is the root of trust.

## What was tried

Nine domains of attack, each with several shapes (`..`, `//`, a sibling
that shares a prefix, case, embedded NUL, paths past `PATH_MAX`, look-alike
Unicode, links of every kind, glob characters, aliases and numeric spellings of
a host, forged handles, `unsafe` hidden in twelve expression positions, and so
on). Apart from the nine holes below, every attack in the suite was refused, or
ran without getting the attacker anything, except the open gaps further down. The domains covered are `fs`, `process`, `env`, `net`, handles, `unsafe`
and `asm`, `mmio`, indirect use (closures, generics, trait defaults, re-exports)
and delegation. `irq` and `frames` are covered by their own suite
(`tests/irq_frames.rs`).

## The nine fixed holes

Each of these let a module do something its grant did not allow, or (item 8) behaved differently on the two backends. Each is a
behaviour change a program can see; items 1 to 7 were built and run on 2026-10-03 with `kelpc 26.09.5`, items 8 and 9 on 2026-10-04 with the compiler built from main, and the output is quoted as
printed (paths shortened to the scratch directory they ran in, and the output
was the same from the LLVM backend and from `KELPC_ORACLE=c` unless stated).

### 1. Writing through a dangling symlink

`fs` paths are resolved through symlinks before matching. The resolver resolved
the deepest *existing* ancestor and appended the rest verbatim, so a link inside
the grant that pointed at a file that did not exist yet looked harmless, and the
write created the file outside the grant. The resolver now follows the link at
the first missing component too (up to 40 hops).

```kelp
// util.kp, granted fs = [".../a/data/**"]; data/dangling -> .../a/secret/new.txt
impl "std/fs"

pub fun go() {
    fs.write_text(".../a/data/dangling", String.from_str("pwn"))
    print("wrote")
}
```

```text
$ ./prog_llvm; echo rc=$?
.../a/util.kp:4:5: panic: '.../a/secret/new.txt' is outside the fs capability granted to module 'util'
  granted:
    .../a/data/**
rc=1
$ ls a/secret
s.txt
```

The refusal names the *resolved* path, and `secret/` still holds only the
original file. The test suite (not run for this page) also covers a link into a missing
directory, a relative link, a chain of links, `mkdir_all` and `touch`.

### 2. `process.kill` and `process.wait` only reach your own children

A grant for one harmless program used to let a module signal any process the
user owned (`kill_raw`, or a forged `Child`). The runtime now keeps the pids that
`spawn` started, and `kill` and `wait` accept only those; a reaped pid leaves the
table.

```kelp
// util.kp, granted process = []; the pid of the parent shell comes in as argv[1]
process.kill_raw(pid.to_i32(), 0)
print("signalled a process that is not a child")
```

```text
$ ./prog_llvm $$; echo rc=$?
panic: process.kill: not a child this program started
rc=1
```

It prints the same line. A hand-built `Child(pid = ...)` goes through
the same primitive and fails the same way.

### 3. A loopback grant binds `127.0.0.1`

`net.listen(port)` has no host argument, and used to bind `0.0.0.0` whatever the
grant said, so a module granted `127.0.0.1:*` could serve the whole network
(`http.listen` too). The check now records whether any grant pattern admits every
interface: a pattern whose host part is `*`, `0.0.0.0`, a glob that matches
`0.0.0.0`, or that names no host. If none does, the listener binds `127.0.0.1`.

```kelp
// util.kp, granted net = ["127.0.0.1:*"], fs = ["/proc/*/net/tcp"]
val l = net.listen(0)
print(l.port())
val f = fs.open("/proc/net/tcp", "r")
print(String.from_bytes(f.read_all()))
```

Reading the listener's own line out of `/proc/net/tcp` (the first printed number
is the port, `0A` is `LISTEN`), the LLVM backend printed port 46837 and

```text
   0: 0100007F:B6F5 00000000:0000 0A 00000000:00000000 00:00000000 00000000  1000 ...
```

`0100007F` is `127.0.0.1` in the table's byte order and `B6F5` is 46837. The C
oracle printed port 41529 and a line with `0100007F:A239`, the same address.
The test suite also checks that `localhost:*` and `127.0.0.1:0` bind loopback and
that a grant of `*` binds `00000000`, every interface.

### 4. A numeric host pattern matches IPv4 literals only

A pattern made only of digits, dots and `*` (`10.0.0.*`) is a statement about
addresses. It used to match the *name* `10.0.0.xyz` too, and a name belongs to
whoever controls its DNS. Now a numeric-shaped pattern admits only a dotted-quad
IPv4 literal, in `connect` and in `resolve`.

```kelp
// util.kp, granted net = ["127.0.0.*:9"]
print(net.resolve("127.0.0.1").len())
print(net.resolve("127.0.0.zzz").len())
```

```text
$ ./prog_llvm; echo rc=$?
1
.../c/util.kp:5:11: panic: '127.0.0.zzz' is outside the net capability granted to module 'util'
  granted:
    127.0.0.*:9
rc=1
```

The literal resolves (to one address); the name is refused before any lookup.
It prints the same.

### 5. Descriptor handles cannot be built from numbers without a grant

`io.File(fd = 3)`, `net.Socket(fd = n)`, `net.Listener(fd = n)`, `process.Child`
and the `http`, `ws` and `tls` connection types are plain data holding a
descriptor number, so a module with no grant at all could build one and use every
descriptor the process had open. Building one outside the library now needs the
domain that mints that kind of handle. `std/io`'s own page is still ungated: a
`File` you were *given* needs nothing, only the integer constructor is checked.

```kelp
// util.kp, no grant; a module with an fs grant opened secret/s.txt and leaked it
impl "std/io"

pub fun go() {
    val f = io.File(fd = 3)
    print(String.from_bytes(f.read(16)))
}
```

```text
$ kelpc build e/main.kp -o e/prog
error: 'std.io.File' wraps an operating-system descriptor, so building one from a number needs the 'fs' capability, which module 'util' was not granted (any of fs, net, process would do); a module that holds no grant can only use the handles it is given
  --> .../e/util.kp:4:13
```

It is a compile error, and the C oracle prints the identical message. For
`net.Socket` and `net.Listener` the message names the `net` capability.

### 6. `unsafe` in a trait default method is audited

The `[unsafe] modules` audit walk skipped trait declarations, so a module that
was not listed could keep its `unsafe` block in a default method body and the
compiler accepted it. It now scans them.

```text
$ kelpc check f
error: module 'evil' is not listed in coral.toml [unsafe] modules
  --> .../f/src/evil.kp:5:16
rc=1
```

Line 5 is the `unsafe { p.read() }` inside the default method of `trait Poke`.
`check` is front end only; running it with `KELPC_ORACLE=c` printed the same
error.

### 7. Shifts of 64 bits or more do not fold into a device address

In a freestanding project `Ptr.from_addr(0x10000000 + (0x100000 << 70))` folded to
the granted address `0x10000000`, while the machine shifts by `70 mod 64` and
touches something else. A constant shift of 64 or more bits is no longer a
constant, in `mmio`, `irq` and `frames` alike, so it needs the whole-space grant.

```text
$ kelpc check g        # [caps] mmio = ["0x10000000+0x100"], freestanding riscv64
error: 'Ptr.from_addr' takes an address the compiler cannot fold, and module 'dev' holds only the range(s) 0x10000000+0x100; a computed address needs the whole-address-space grant `caps(mmio = ["*"])`
  --> .../g/src/dev.kp:2:31
rc=1
```

Freestanding mode is LLVM-only, so this one has no C-oracle run.

### 8. Shifts of any width are checked

A shift by the type's width or more was poison on LLVM and `0` or garbage in C
(the plan recorded `1u32 << 33` printing garbage on one backend and `0` on the
other), and the `irq` and `frames` constant folder masked to 64 bits rather than
the operand's width. It is now one rule, hosted and freestanding: an amount outside `0..width` (negative included) panics with
`shift amount out of range`, a constant amount out of range is a compile error
naming the type and the amount, and `wrapping_shl`/`wrapping_shr` mask the
amount. A `u32` line now folds at 32 bits, as the program computes it. No attack
on a grant was known; this closes a behaviour the plan listed as a gap. The full
rule and examples are in [Expressions](/language/expressions#bitwise).

```text
$ ./prog      # shift(1, 32) on a u32 with the amount hidden behind a parameter
panic: shift amount out of range
$ kelpc build shift_const_too_wide.kp -o prog     # x << 33 on a u32
error: a shift by 33 is not defined for a 'u32', whose width is 32 bits: the amount has to be in 0..32 (use wrapping_shl/wrapping_shr to mask it)
  --> .../shift_const_too_wide.kp:5:11
```

It prints the same (rerun on 2026-10-04: `u32`, `u64`, `u8 >>` and a
negative `i32` amount all panic with that line and exit with status 1, under the
LLVM backend and `KELPC_ORACLE=c`).

### 9. TLS `ca_file` and `ca_dir` are removed

The handshake opened the CA paths in `TlsOptions` with no `fs` check, so a module
with `net` and no `fs` could make the client read a PEM path and learn whether
verification succeeded. The options now take PEM bytes (`TlsOptions(ca_pem,
timeout_ms)`, `TlsClientOptions.with_ca_pem`), the runtime never opens a path,
and a file is read with `tlsfile.ca_pem(path)`, which goes through `fs`. `ca_dir`
has no bytes form and is gone.

```text
error: datac 'std.tls.TlsClientOptions' has no method 'with_ca_file'
error: 'std.fs.try_read' needs the 'fs' capability, which module 'std/tlsfile' was not granted; the module that imports this one must delegate it (`impl "<this module>" caps(fs = ["<pattern>"])`)
```

The first is the old spelling, the second a module that imports `std/tlsfile`
with no `fs` grant; a path outside the grant is the ordinary `fs` denial and is
never opened (`n09`, `n09b`, `n09c`). The migration is on
[`std/tls`](/stdlib/tls#reading-the-files-stdtlsfile).

## Known gaps

These are open and stated as such.

- **Descriptors shared between two *granted* modules.** Module B with
  `fs = data/**` can run `io.File(fd = 3).read(..)` and read a descriptor module A
  opened on `secret/`, because both hold `fs` and the check on `File(fd = ..)` is
  "holds one of the domains", not "owns this descriptor". The planned fix makes
  the handle types opaque and adds a gated `from_fd` for the legitimate hand-over
  to a thread; the test (`h03`) is ignored. Until then, do not give a module you
  do not trust a grant just to be tidy, and do not leave descriptors open.
- **Pointer offsets after birth.** An `mmio` range is checked at the address a
  pointer is *born* at; `p.byte_offset(n)` afterwards reaches anywhere (`m05`,
  ignored). The fix is provenance, which is on the roadmap.
- **Children inherit open descriptors.** There is no close-on-exec sweep, so a
  spawned program holds every descriptor the parent had open.
- **By design, not gaps:** a module with a broad grant serves any caller, and
  grants several importers make to one module are unioned (each still bounded by
  what its own importer holds).

## Table

| Domain | Enforced by | Fixed | Open |
| --- | --- | --- | --- |
| `fs` | resolution gate, path normalization and link resolution, glob match | dangling symlink write | none known |
| `process` | gate, program path check, table of spawned children | kill of a foreign pid | none (a shell grant is documented breadth) |
| `env` | gate, name check | none needed | none |
| `net` | gate, host, port and host-port checks, bind verdict | loopback listener, numeric pattern, TLS CA paths | none known |
| handles | constructor rule | forging a handle with no grant | forging between two granted modules |
| `unsafe` / `asm` | `[unsafe] modules` audit walk | trait default methods | none known |
| `mmio`, `irq`, `frames` | `Ptr.from_addr` fold and range check, sealed constructors | oversized shift, narrow-type shifts | offset after birth |
| indirect use, delegation | the lexical module of the call site, no-escalation rule | none needed | none |

## See also

- [Capabilities](/language/capabilities): the model, grants and patterns
- [Capability patterns](/reference/capability-patterns): the pattern grammar
- [`unsafe` and pointers](/language/unsafe): the audit list
- [Limits in v1](/language/limits)
