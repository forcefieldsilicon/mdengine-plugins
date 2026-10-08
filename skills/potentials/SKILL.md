---
name: potentials
description: >-
  Choose an interatomic potential for an MD run and know what it costs. Use it
  when picking between LJ, EAM, Tersoff, Stillinger-Weber, ReaxFF, Vashishta or
  Buckingham, when asked "which force field for this material", when a run needs
  to model bond breaking or oxidation, when a deck's pair style turns out not to
  run on the GPU, or when looking for where a parameter file comes from and
  whether it can be shipped.
user-invocable: true
compatibility: macOS (local tools), any OS (hosted MCP)
metadata:
  author: ForceField Silicon (Gitinama Inc.)
  version: "0.1.0"
license: Apache-2.0
---

# Picking a potential

The potential decides three things at once: what physics the run can show, how much
it costs per atom-step, and whether it runs on the GPU at all. Decide it before you
build the geometry.

## The decision table

| Potential | Use it for | Not for | Relative cost per atom-step |
| --- | --- | --- | --- |
| `lj/cut` | Scaling tests, method checks, generic condensed matter, anything where the material does not matter | Any real material property | 1 |
| `eam`, `eam/alloy`, `eam/fs` | Metals and metal alloys: elasticity, melting, dislocations, grain boundaries, indentation, thermal transport | Anything with charge transfer, covalent directionality or bond chemistry | 2 to 5 |
| `adp` | Metals where EAM misses angular character | Reactions | 5 to 10 |
| `tersoff`, `tersoff/mod`, `sw` | Covalent solids: silicon, carbon, SiC, III-V. Bond-angle physics, amorphisation, defects | Metals, ionic solids, anything needing charges | 5 to 15 |
| `vashishta`, `buck`, `buck/coul/long` | Ionic and oxide solids where the charges are fixed and known | Changing oxidation states | 5 to 20, more with long-range Coulomb |
| `reaxff` | Reactive chemistry: bond breaking and forming, oxidation, combustion, surface reactions, variable charge | Anything a cheaper potential already answers | 10 to 50 |

Read it top down and stop at the first row that can answer the question. A reactive
potential run costs roughly an order of magnitude more per atom-step than EAM before
you count the charge solver, so choosing it when EAM would have done is the single
most expensive mistake available.

Two costs hide inside ReaxFF. `fix qeq/reaxff` runs a charge equilibration every step,
and the timestep has to be small because it resolves bond vibrations. A reactive run
at the same wall time covers far fewer picoseconds than the table alone suggests.

## Which of them use the GPU

The hosted image is KOKKOS built, and only styles with a `/kk` variant run the pair
force on the GPU. As of this writing, on the default image:

| Style | GPU |
| --- | --- |
| `lj/cut`, `lj/cut/coul/long`, `morse`, `table`, `zbl` | yes |
| `eam`, `eam/alloy`, `eam/fs`, `adp` | yes |
| `tersoff`, `tersoff/mod`, `sw` | yes |
| `reaxff` | yes |
| `vashishta`, `buck`, `coul/long` | yes |
| `hybrid`, `hybrid/overlay` | yes, if every sub-style is |
| `airebo`, `comb`, `comb3`, `born`, `eim` | no |
| `meam`, `snap` | only on the full image |
| `reax/c` | no, it is the retired name. Use `reaxff` |

**Do not trust this table, check it.** The image is rebuilt on its own schedule and
this list goes stale. Ask:

```sh
mdengine capabilities            # the image, its packages, the counts
mdengine capabilities deck.in    # the verdict for one deck
```

or MCP `capabilities` on the hosted server, `cloud_capabilities` locally. A style
that the default image lacks may still be on the full image, in which case the deck
is routed there automatically and the only cost is a slower launch.

A style with no GPU variant still runs, on the pod's CPU cores, at the GPU rate. That
is almost never what anyone wants. See the **lammps-deck** skill for the verdicts.

## Where parameter files come from

A pair style is half of the answer. The other half is the parameter file, and it has
to match both the elements and the physics you are modelling.

| Source | What it is |
| --- | --- |
| The LAMMPS `potentials/` directory | Ships with LAMMPS. First place to look. Files carry a header naming the paper they came from. |
| NIST Interatomic Potentials Repository | Curated, versioned, with the original citation and usually a test suite. |
| OpenKIM | Versioned models with a DOI each, plus verification checks. |
| The original paper's supporting information | The last resort, and the one to be careful with. |

Cite a potential the way a paper does: first author, year, and the DOI of the paper
that published the parameters. A parameter set is a result somebody produced, and the
run is only reproducible if the reader can find the same file.

**A parameter file taken from a paper's supporting information is for research use.**
Do not redistribute one inside a product, a container image, or a public repository
without permission from the authors or the publisher. Ship the citation and a script
that fetches the file, not the file. Files that ship with LAMMPS or come from NIST IPR
and OpenKIM carry their own license terms; read them, they are not all the same.

## Before you commit to one

- **A substrate is only valid for the potential it was relaxed against.** A slab
  equilibrated under one potential is under stress under another, and the run will
  show that stress as physics. Change the potential, rebuild the slab.
- **Validate on the file production reads.** Checking a potential against a fresh
  ideal lattice says nothing about the data file the production deck loads.
- **Run the cheap version first.** A short local run at the full atom count catches
  a wrong `pair_coeff`, a missing element in the element list, and a bad starting
  geometry, for free.
- **Check the elements line.** `pair_coeff * * <file> Al O` maps LAMMPS atom types to
  entries in the parameter file by position. Getting the order wrong is silent.
