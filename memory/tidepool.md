---
title: "Tidepool memory design"
description: "Index of the Tidepool memory design pages. Tidepool is in design, and its pages are empty placeholders."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool memory design

Tidepool is the planned memory design for Kelp. It puts blocks beside a shared pool.
It is in design, and nothing on these pages is final.

On `main`, every hosted build links the base collector, a non-moving mark-region
collector, and caps its heap with `[target] heap_max`. The Tidepool pieces are not on
`main` yet: no blocks, no growable root table (`main` has a fixed table of 1024 root
entries), no high-water index, no `[tidepool]` settings and no measured trigger.
Channels and the pool are refused until the first step lands.

## Pages

- [The idea](/memory/tidepool/idea)
- [The boundary](/memory/tidepool/boundary)
- [Blocks at runtime](/memory/tidepool/blocks)
- [The budget](/memory/tidepool/budget)
- [Settings in `[tidepool]`](/memory/tidepool/settings)
- [Safety rules](/memory/tidepool/safety-rules)
- [The allocation path](/memory/tidepool/allocation-path)
- [Safety tests](/memory/tidepool/safety-tests)
- [Build order](/memory/tidepool/build-order)
- [Performance claims and how they are measured](/memory/tidepool/performance-claims)
- [What the programmer writes, reads and sees](/memory/tidepool/programmer-view)
- [Test plan](/memory/tidepool/test-plan)
- [Tooling and release](/memory/tidepool/tooling-release)
- [Failure and recovery](/memory/tidepool/failure-recovery)

Most of these pages are placeholders until the design is settled. The idea and settings
pages describe the planned parts. The design text is kept outside `main`, and it is the
source for the planned parts.
