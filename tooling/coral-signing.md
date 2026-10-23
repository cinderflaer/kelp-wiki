---
title: "Signing archives"
description: "How to make a signing key, sign a Coral package, trust a key, and check a package with inspect and run, with each signature line explained."
isPublished: true
tags: "tooling, cli"
---
# Signing archives

This page shows how to sign a Coral package and how to check one before you run it.
It covers `coral key new`, `coral build --package`, `coral inspect` and `coral run`.

Signing is optional.
An unsigned package still builds and runs, but Coral prints a warning about it.

## Before you begin

Coral signs and checks with `ssh-keygen`, so it must be on `PATH`.
Signing needs OpenSSH 8.0 or later, with `ssh-keygen -Y`.
Only OpenSSH 10.5 was tested.

Signing has two roles.
The signer makes a key and builds the package.
The owner lists the signer's public key in a trust file, and everyone who checks a package uses that file.

## Make a key

Run `coral key new` with a label.
The label may hold only letters, digits, `-` and `_`.

```bash
coral key new alice
```

The command writes a private key named `alice` into the keys directory, with mode 0600.
The keys directory is `keys/` inside the Coral config directory: `$XDG_CONFIG_HOME/coral/keys`, or `~/.config/coral/keys` when `XDG_CONFIG_HOME` is not set.
`CORAL_CONFIG` does not change it.
The public half is written beside it as `alice.pub`.
The command refuses to replace a file that already exists at that path.

The key is made without a passphrase.
Passphrase-protected keys were not tested.

The command prints the key's public key and fingerprint.
It then prints two lines for the config file, but it does not write the config file itself.
This is what the output looks like, with placeholders in place of the real values:

```text
wrote private key /home/alice/.config/coral/keys/alice
mode: 0600
public key: ssh-ed25519 AAAA... alice
fingerprint: SHA256:<fingerprint>
to sign packages with it, add these lines to the coral config file:
  signing_key = "/home/alice/.config/coral/keys/alice"
  signing_fingerprint = "SHA256:<fingerprint>"
to trust it, give the public key line to the owner, who lists it under [trusted] in the trust file
```

Send the public key line to the owner.
Never send the private key file.

## Set the signing key

Add the two lines from the output to the Coral config file.
The config file is `$CORAL_CONFIG` when that is set, else `$XDG_CONFIG_HOME/coral/config.toml`, else `~/.config/coral/config.toml`.

```toml
signing_key = "/home/alice/.config/coral/keys/alice"
signing_fingerprint = "SHA256:<fingerprint>"
```

`signing_key` is the path to the private key.
`signing_fingerprint` is optional.
When it is set, Coral checks that the key's fingerprint matches it, and refuses to sign if it does not.

The environment does the same job.
`CORAL_SIGNING_KEY` replaces `signing_key`, and `CORAL_SIGNING_FINGERPRINT` replaces `signing_fingerprint`.
When both are set, the environment wins.

With no key configured, `build --package` writes an unsigned package and prints a warning.

## Add a key to the trust file

The owner adds the signer's public key line to the trust file under `[trusted]`.

```toml
[trusted]
alice = "ssh-ed25519 AAAA... alice"
```

The trust file has two sections.
`[trusted]` lists the keys whose packages are accepted.
`[revoked]` lists keys whose packages are refused.
Each entry is `name = "ssh-ed25519 <key>"`.
Any comment after the key is ignored, and `#` starts a comment outside quotes.

The rules for the file are these:

- The name may hold letters, digits, `-`, `_`, `.`, `@` and `+`.
- Only `ssh-ed25519` keys are accepted.
- An entry must appear after a `[trusted]` or `[revoked]` header.
- A missing file means no trusted keys.
- A malformed file is an error only when the package being checked is signed.

Coral finds the trust file in this order:
the `CORAL_TRUST` variable, then the `trust` key in the config file, then `trust.toml` in the same directory as the config file.

## Sign a package

Run `coral build --package` in the project directory.
The command builds the package and writes it to `build/<name>-<version>-<os>-<arch>.ckp`.
It prints the absolute path of the package.
When a signing key is configured, the package carries a `signature.sig` entry.

```bash
coral build --package
```

Add `--require-signed` to refuse to write an unsigned package.
Coral then stops with an error when no key is configured.

```bash
coral build --package --require-signed
```

A configured key that is missing or unreadable is an error.
Coral writes no package in that case.

The package does not name its signer.
It holds the manifest, the files, and the signature, and no principal name or UUID.
The name of the signer appears only in the trust file.

## Check a package with inspect

`coral inspect` prints the package's manifest, its signature line, and each file with its sha256 check.
It does not unpack or run the package.

```bash
coral inspect build/app-1.0.0-linux-x86_64.ckp
```

The header and the signature line look like this, with the file rows left out:

```text
name: app
version: 1.0.0
entry: app
os: linux
arch: x86_64
format: 1
capabilities: none
requires glibc: 2.39
requires gcc_runtime: 14.2
requires libstdcxx: none
requires libc: glibc
requires bundled: libssl.so.3, libcrypto.so.3
host: ok
signature: valid alice
files:
```

The `requires` lines come from the package's `[requires]` table, see [Portable packages](#portable-packages).
The `host` line reads `ok` when the glibc of the machine that runs `inspect` meets `requires glibc`.
When it does not, `host` reads `refused`, the reason is printed on standard error, and `inspect` exits with status 1.

Add `--require-signed` after the package to make `inspect` refuse an unsigned package or one from an unknown key.

```bash
coral inspect build/app-1.0.0-linux-x86_64.ckp --require-signed
```

## Run a package

`coral run` checks the package the same way before it runs it.
It checks each file's sha256 first, then the signature.

```bash
coral run build/app-1.0.0-linux-x86_64.ckp -- --verbose
```

Arguments for the program go after `--`.
Put `--require-signed` directly after the package path, before `--`.

```bash
coral run build/app-1.0.0-linux-x86_64.ckp --require-signed -- --verbose
```

## Portable packages

A package runs on any machine that has the glibc its files reference, and it needs no rebuild for each distro.
Coral makes it so at `build --package` time:

- The executable is linked dynamically against glibc. The glibc family (`ld-linux-x86-64.so.2`, `libc.so.6`, `libm.so.6`, `libpthread.so.0`, `libdl.so.2`, `librt.so.1`) and `libgcc_s.so.1` are never bundled. The host supplies them.
- Every other library that the executable or a bundled file needs is copied into `lib/` in the package, with its sha256 in `[files]`. The executable finds `lib/` through its `RUNPATH`, `$ORIGIN/lib`.
- A package that needs `libstdc++` is refused at build time, and the message names the library.
- `[requires]` states the glibc the package needs. It is the highest `GLIBC_x.y` version that any file references, found with `llvm-readelf --version-info`. `build --package` refuses when `llvm-readelf` is not on `PATH`.

Build a package in the oldest glibc you support. A package built on Ubuntu 24.04 (glibc 2.39) runs on every newer glibc.
A package built on a newer distro may name a newer glibc, and then it runs only on machines that have that glibc or a newer one.

`run` and `inspect` check `requires glibc` against the host before they unpack anything.
On a machine with an older glibc, or with no glibc, `run` refuses with a message such as `this package needs glibc 2.39 or newer; this machine has glibc 2.35`, exits with status 1, and creates no cache directory.

A bundled OpenSSL is a copy of the distro's 3.x library.
A security fix in OpenSSL therefore needs a new package, not only a system update.

## What each signature line means

`inspect` prints one of these lines.
`run` applies the same rules and prints the reason on standard error when it refuses.

- **`signature: valid <principal>`:** The package is signed by a key listed under `[trusted]`. Coral accepts it. The principal is the name in the trust file.
- **`signature: none`:** The package has no signature. Coral accepts it with a warning, unless `--require-signed` is set.
- **`signature: unknown key SHA256:<fingerprint>`:** The key is not in the trust file. Coral accepts it with a warning, unless `--require-signed` is set.
- **`signature: BAD`:** The signature does not match the package. The package changed after it was signed, or the signature is from another package or key. Coral always refuses it.
- **`signature: revoked <principal>`:** The key is listed under `[revoked]`. Coral always refuses it.

`inspect` prints the rest of the output before it exits.
When it refuses a package, it exits with status 1.

## When Coral refuses

Coral refuses a package in these cases:

- The signature is `BAD`. This is always refused.
- The key is revoked. This is always refused, even when the same key also appears under `[trusted]`, and even for packages built before the key was revoked.
- The package has no signature, and `--require-signed` is set.
- The key is unknown, and `--require-signed` is set.

Coral also stops `build --package` in these cases:

- The configured key is missing or unreadable.
- `signing_fingerprint` does not match the key.
- `--require-signed` is set and no key is configured.

## Retire or replace a key

Coral has no rotation command.
To stop trusting a key, the owner moves its entry from `[trusted]` to `[revoked]`.
To replace a key, the signer runs `coral key new` with a new label, the owner adds the new public key under `[trusted]`, and the signer updates `signing_key` and `signing_fingerprint`.

## Limits

- Passphrase-protected keys were not tested.
- OpenSSH 10.5 was the only version tested.
- There is no rotation tool beyond editing the trust file.

## See also

- [Coral](/tooling/coral): the command surface, the manifest and the config file.
- [Tooling](/tooling): the three programs and the pages for each.
