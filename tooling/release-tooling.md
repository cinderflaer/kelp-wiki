---
title: "Release tooling"
description: "Reproducible release builds (build/release.sh, verify-reproducible.sh), the verifying installer build/install.sh, and kelpc version --verbose: usage, real output, and the honest limits (same toolchain only, Nix store paths embedded)."
isPublished: true
tags: "tooling, cli"
---
Four small pieces turn a commit into a binary somebody else can check and install:
`build/release.sh` builds it, `build/verify-reproducible.sh` proves the build is
repeatable, `build/install.sh` installs a downloaded one only after it verifies,
and `kelpc version --verbose` says what a binary was built from. The design is
[`tooling/release-tooling.md`](/tooling/release-tooling);
the installer and the version output are tested by `kelpc/tests/release_tooling.rs`.
They are scripts in the compiler repository, not subcommands of `kelpc`.

## `kelpc version --verbose`

The output below was copied from a `kelpc 26.09.5` build. The format is the same on
`kelpc 26.10.4`: the version, then the commit, build date, rustc and LLVM lines.

```text
$ kelpc version
kelpc 26.09.5
$ kelpc version --verbose
kelpc 26.09.5
commit: 1e05cc449ecab15b46ee6c82c8b5c07025d86389
build date: 1980-01-01
rustc: rustc 1.95.0 (59807616e 2026-04-14) (built from a source tarball)
llvm: 21.1.8
```

The extra lines are baked in by `kelpc/build.rs`: the commit from the
`KELPC_COMMIT` environment variable or else `git rev-parse HEAD`, the date from
`SOURCE_DATE_EPOCH` rendered as a UTC date (never the wall clock), the output of
`rustc -V`, and `llvm-config --version`. That output came from the prebuilt
compiler used to check these pages, which was built inside the development
`nix-shell`, and the shell exports a fixed `SOURCE_DATE_EPOCH` of 1980, which is
why the date reads `1980-01-01`. `release.sh` (below) does not take that value
from the environment: it uses the commit time.

## `build/release.sh`

Run it inside the development shell (it needs `cargo`, `rustc`, `llvm-config`,
`cc` and `git`). `cc` is the linker driver that `cargo` and `rustc` use for the Rust
binaries. kelpc does not run it:

```sh
nix-shell shell.nix --run 'sh build/release.sh'
```

It writes three files to `dist/` (or `DIST_DIR`):

| File | Holds |
| --- | --- |
| `kelpc-<version>-linux-x86_64` | the binary, for example `kelpc-26.09.5-linux-x86_64` |
| `SHA256SUMS` | its SHA-256, in `sha256sum` format |
| `BUILDINFO` | version, commit, `source_date_epoch`, rustc, cargo and LLVM versions, the profile, the exact `cargo` arguments and `RUSTFLAGS`, and the hash |

What it pins so the same source gives the same bytes: `CARGO_INCREMENTAL=0`,
`--locked` (and `--frozen` when the cargo registry cache exists), one codegen unit
and `strip=debuginfo` for the release profile, and `RUSTFLAGS` that remap the
checkout, the cargo home and the Rust sysroot to fixed names
(`/kelp-src`, `/cargo-home`, `/rust-sysroot`) and drop the build id. The build
timestamp is the last commit's time (override with `RELEASE_SOURCE_DATE_EPOCH`),
and the commit baked in is `HEAD` (override with `KELPC_COMMIT`).
`CARGO_TARGET_DIR` defaults to `target-release` in the checkout.

## `build/verify-reproducible.sh`

```sh
sh build/verify-reproducible.sh [work-dir]
```

It runs `git archive HEAD` into two directories with different absolute paths
(`alpha/source-tree` and `beta-longer-path/source-tree`, each with its own target
directory), runs `release.sh` in each, one after the other, and compares the
SHA-256 of the results. It prints `IDENTICAL: <hash>` and exits 0, or prints
`DIFFERENT: <a> vs <b>` and exits 1. Two things to know: it builds the
**committed** `HEAD`, so uncommitted changes are not part of the check, and it
needs two full release builds back to back (`KEEP=1` keeps the work directory).

The recorded result (from the plan, not re-run for this page: it takes two full
release builds): on 2026-10-03, with rustc 1.95.0, LLVM 21.1.8 and the nix
development shell, two builds of one commit in two differently-long directories
were identical, `beb7f8b7b3a3cb77a9775f4a7cce651fa8ac1772bccba3035e938fcd2531d722`
for `kelpc-26.09.5-linux-x86_64`. An earlier attempt had differed only because the
shell's `SOURCE_DATE_EPOCH` leaked into one run's baked build date, which is why
the script now ignores an ambient one.

### What it does not promise

- **Reproducible per toolchain, not across them.** The binary contains no
  checkout, cargo-home or sysroot path, but it does embed the toolchain's **Nix
  store paths**: the dynamic loader and RPATH entries for glibc, gcc-lib and
  `libLLVM-21`, and a `...-nix-shell` entry from the shell's link flags. The same
  commit built with a different nixpkgs revision has different bytes.
- **Not portable as built.** Because of those paths, a binary built in the Nix
  shell is for machines that have those store paths. A binary for non-Nix users
  should be built in an environment where the loader and libraries are the
  distribution's own `/lib` paths (for example a Debian container with
  `llvm-21-dev`); the same scripts apply. The plan does not record such a build.
- `codegen-units=1` was set up front rather than found necessary; the build was not
  tried without it.
- It checks that two builds agree, not that the source is trustworthy.

## `build/install.sh`

A POSIX shell installer for a downloaded `kelpc-<version>-linux-x86_64`. It **never
downloads** and never uses `sudo`: you fetch the binary and `SHA256SUMS` from the
release page yourself, and the script refuses to install what it cannot verify.

```text
install.sh --from <file> (--sha256 <hex> | --sums <SHA256SUMS>) [--prefix <dir>]
install.sh --from <file> --insecure-skip-verify [--prefix <dir>]
install.sh --uninstall [--prefix <dir>]
```

The default prefix is `~/.local`: the binary goes to `<prefix>/bin/kelpc`, and a
manifest of what was installed goes to `<prefix>/share/kelpc/manifest`, which is
all `--uninstall` removes. Before installing it checks that the platform is
Linux x86_64, and that the linker `ld.lld` and the shared library `libLLVM-21.so`
are present, and it says what is missing when they are not. `KELP_INSTALL_SKIP_CHECKS=1`
skips that check and the hello-world run below. After installing it compiles and
runs a hello-world program with the new binary. Linux x86_64 is the only supported
platform.

A session, in a temporary prefix, inside the development `nix-shell` (which
supplies `ld.lld` and `libLLVM-21`), with a copy of a `kelpc` binary and a
`SHA256SUMS` made with `sha256sum` (paths shortened to `$T`):

```text
$ cat SHA256SUMS
be55498e5fcfa6cb723d37560a4c4a42836c80d8a0745d4f79c0cc5a5a6a03c3  kelpc-26.09.5-linux-x86_64

--- a wrong checksum
$ sh install.sh --from kelpc-26.09.5-linux-x86_64 --sha256 0000...0000 --prefix $T/p1
install.sh: error: checksum mismatch for kelpc-26.09.5-linux-x86_64: expected 0000000000000000000000000000000000000000000000000000000000000000, got be55498e5fcfa6cb723d37560a4c4a42836c80d8a0745d4f79c0cc5a5a6a03c3. Nothing was installed.
rc=1                      (and $T/p1 does not exist)

--- no verification given
$ sh install.sh --from kelpc-26.09.5-linux-x86_64 --prefix $T/p2
install.sh: error: refusing to install without verification: pass --sha256 <hex> or --sums <SHA256SUMS> (or, at your own risk, --insecure-skip-verify).
rc=1                      (and $T/p2 does not exist)

--- with the sums file
$ sh install.sh --from kelpc-26.09.5-linux-x86_64 --sums SHA256SUMS --prefix $T/p3
checksum ok (be55498e5fcfa6cb723d37560a4c4a42836c80d8a0745d4f79c0cc5a5a6a03c3)
installed $T/p3/bin/kelpc
note: $T/p3/bin is not on your PATH
hello-world check passed: hello from kelp
rc=0
$ $T/p3/bin/kelpc version
kelpc 26.09.5

--- uninstall
$ sh install.sh --uninstall --prefix $T/p3
removed $T/p3/bin/kelpc
removed $T/p3/share/kelpc/manifest
kelpc uninstalled from $T/p3
rc=0
```

`--sums` looks the binary up by its file name in `SHA256SUMS`, so keep the release
name; `--sha256` takes the hash directly. Giving both is an error, and a
`SHA256SUMS` with no line for the file is an error. `--insecure-skip-verify`
installs with a warning that prints the hash it saw; it exists for people who
verified the file some other way.

**What the check is worth.** A checksum fetched from the same place as the binary
only protects against a corrupted download. Against a hostile mirror it helps only
if you got `SHA256SUMS` (or the hash) over a different channel, or compare it with
the `BUILDINFO` hash of a build you reproduced yourself.

## Checking the examples

The wiki's examples are checked by `scripts/check-examples.sh` in the wiki
repository: one command, run from a checkout, that compiles every `kelp` program
with `kelpc` and compares the output of the ones that state it. It exits 1 on any
mismatch. See [Tooling](/tooling) for the fence attributes and the requirements.

## See also

- [`kelpc` CLI](/tooling/kelpc-cli): `kelpc version` among the subcommands
- [Install and build](/getting-started/install): building from source
- [Tooling](/tooling)
