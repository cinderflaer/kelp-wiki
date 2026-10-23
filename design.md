---
title: "Design records"
description: "The full design records that were kept in the kelp repository's plan directory: the language reference, architecture, traits, incremental builds, Polyp v3 and the rest."
isPublished: true
tags: "design, reference"
---
# Design records

These are the design records that the kelp repository kept in its `plan/` directory until 2026-10-16. Each page keeps the full text of its record. The pages elsewhere in this wiki are the user-facing form of the same material.

- [Language design record: syntax](/design/syntax): the full language reference that the Language chapter cites by section.
- [Design record: architecture](/design/architecture): the compiler layout, the capability model, the v1 feature set and the standard library decisions.
- [Design record: traits and static dispatch](/design/traits): traits, bounds, trait objects, associated types and generic traits.
- [Design record: incremental compilation](/design/incremental-compilation): compilation units, the object cache and the measured numbers.
- [Design record: Polyp v3](/design/polyp-v3): the backend-neutral core, the software rasterizer and the freestanding proof.
- [Design record: capability threat model](/design/threat-model): assets, attacks, findings and known gaps.
- [Design record: sanitizer builds](/design/sanitizers): the retired sanitizer path and its sweep.
- [Design record: device capabilities](/design/device-caps): the mmio domain and its honest limits.
- [Design record: the display capability domain](/design/ffi-display-domain): the decision behind the ui domain.
- [Design record: user FFI gap analysis](/design/user-ffi-gap-analysis): what user extern covers and what it does not.

Open plans are not on this page. They are Gitea issues in the kelp repository, titled `[plan] <name>`, with the `plan` label.
