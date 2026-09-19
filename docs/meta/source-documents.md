# Source documents

This documentation is derived from files that live in the repositories. Where a
page here and its source disagree, the source is right and the page is a bug.

## `kelp`

| File | Authority for |
| --- | --- |
| [`plan/syntax.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md) | the language and the style: every section of the Language chapter cites it by number |
| [`plan/architecture.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/architecture.md) | the design: compiler layout, the capability model, the v1 surface, the standard library's decisions |
| [`plan/roadmap.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/roadmap.md) | the plan: the marks, the open items, the backlog |
| [`plan/done.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/done.md) | the milestone record of what has shipped |
| [`plan/mk7-own-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-own-backend.md) | the `asm` backend's working plan |
| [`plan/mk7-next-slice.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-next-slice.md) | the next slice of that work |
| [`README.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/README.md) | the front door: what the language has, how to build, the repository layout |
| `kelpc/std/*.kp` | the standard library, which is the authority for its own signatures: the [index](../reference/stdlib-index.md) is generated from it |
| `kelpc/src/*.rs` | the compiler; each file's `//!` header describes its job |
| `kelpc/tests/` | the fixture suite and the gates |
| `bench/speed/` | the four-workload benchmark |

## The other repositories

| Repository | Role | Authority |
| --- | --- | --- |
| [`coral`](https://homelabone.xenoo.dev/gittea/Juniper/coral) | the build tool and package manager: manifest, tasks, build cache, dependencies | its `README.md` is the source for [Coral](../tooling/coral.md) |
| [`lighthouse`](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse) | IDE support: the LSP server, the VS Code extension, the IntelliJ plugin | its `README.md` is the source for [Lighthouse](../tooling/lighthouse.md) |
| [`fpl`](https://homelabone.xenoo.dev/gittea/Juniper/fpl) | the first-party library catalogue, one folder per library | each library's `lib.kp`, and its page in the [Libraries chapter](../libraries/index.md) |
| [`kelp-wiki`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki) | this site's sources | `mkdocs.yml` and `docs/**` |

## How this site is built

MkDocs Material, one page per topic, chapters as directories. Two details:

- `hooks/kelp_lexer.py` teaches Pygments the `kelp` fence language, so Kelp code
  blocks are highlighted: Kelp lexes as Rust with its own keywords promoted.
- `mkdocs.yml` is the navigation tree. The build runs `--strict`, so a broken link
  or a bad page fails the build rather than publishing quietly. While chapters
  were still being written, `validation.links.not_found` was set to `ignore`; flip
  it back to `warn` once the last page lands.

On `homelabone` the site is built by `kelp-wiki-build.service` (a NixOS module,
`/etc/nixos/kelp-wiki.nix`) into `/var/lib/kelp-wiki/site`, served by nginx at
`https://homelabone.xenoo.dev/kelp/`, and rebuilt when a commit lands: a Gitea
webhook signs a request to a localhost receiver, which starts that unit. A
ten-minute timer is the safety net.

## See also

- [Contributing](contributing.md)
- [Known issues](known-issues.md)
