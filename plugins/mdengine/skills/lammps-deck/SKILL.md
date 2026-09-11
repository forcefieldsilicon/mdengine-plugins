---
name: lammps-deck
description: >-
  Write or repair a LAMMPS input deck that the MDEngine hosted runner accepts.
  Use it when writing an input script or in.* deck, when a run exits at startup,
  when LAMMPS reports lost atoms, when a GPU run dies with an illegal address,
  when preflight says a style is missing or CPU-only, or when a deck needs to be
  made self-contained before it is submitted. Covers the deck checklist, the
  reflecting ceiling for gas over a slab, charge equilibration for reactive
  runs, and how to read the three preflight verdicts.
user-invocable: true
compatibility: macOS (local tools), any OS (hosted MCP)
metadata:
  author: ForceField Silicon (Gitinama Inc.)
  version: "0.1.0"
license: Apache-2.0
---

# Writing a deck the runner accepts

A hosted job ships **the deck's whole directory** and runs LAMMPS inside it. So the
deck is not one file, it is a directory that has to stand on its own.

## The checklist

1. **Self-contained directory.** Every file the deck reads sits next to it: the
   `read_data` file, the potential parameter file, molecule templates, restart
   files. Nothing outside the directory is shipped. The most common hosted failure
   is a deck that ran locally because one data file happened to be one level up.
2. **Relative paths only.** `read_data slab.data`, not `/Users/you/work/slab.data`.
   The job runs in its own directory on a pod, so an absolute path is a dead path.
3. **Header first.** `units`, `atom_style`, `boundary`, then geometry, then
   `pair_style` and `pair_coeff`, then fixes, then `run`. Getting `units` wrong is a
   silent factor of a thousand in the output.
4. **Define computes before the run that uses them.** A compute or a variable
   referenced by a `thermo_style`, a `fix print` or a gate must already exist when
   the first `run` starts. A variable that reads `pxx` also needs `pxx pyy` in the
   **active** `thermo_style`, not a later one.
5. **A `&` continuation must be the last character on its line.** Not before a
   trailing comment, not before a space you cannot see. This costs an hour every
   time.
6. **Avoid three levels of nested quotes.** Pass a numeric flag into the deck with
   `-var` instead and branch on it.
7. **Size `run` and `dump` together.** The results come back as a tarball. A dump
   every 100 steps of a 10 million step run is a trajectory nobody can download.
   Pick a dump cadence that gives a few hundred frames, and `decimate` afterwards if
   it is still too big.
8. **Preflight.** `mdengine capabilities deck.in` before every submission.

## Gas over a slab needs a ceiling

A box with an open face, `boundary p p f`, lets anything moving that way leave. Gas
above a slab reaches the top of the box within a few thousand steps at deposition
temperatures. Put a reflecting wall on the open face:

```
fix lid gasgroup wall/reflect zhi EDGE
```

Do the same at the bottom if the slab has a free bottom face, or give it at least
10 Å of empty box below so thermal motion cannot cross `zlo`.

What happens without it depends on which line you are on, and this is why the bug
hides. On the CPU line LAMMPS says **Lost atoms** and the step count keeps going.
Under KOKKOS on the GPU the atom is kept outside the box and the run dies later
with `cudaErrorIllegalAddress`, far from the step where the atom actually left.
A GPU run that crashes with an illegal address and has an open face is this bug
until proven otherwise.

## Reactive runs need charge equilibration

A ReaxFF deck does not work without a charge solver. Add it, in this order:

```
pair_style reaxff NULL
pair_coeff * * <parameter file> <element list>
fix qeq all qeq/reaxff 1 0.0 10.0 1.0e-6 reaxff
```

`atom_style charge` is required. `fix qeq/reaxff` must come after `pair_coeff`, and
it runs every step by default, which is a large part of what makes a reactive run
expensive. The **potentials** skill covers when a reactive potential is the right
call at all.

## Reading the preflight

`mdengine capabilities deck.in` (or MCP `preflight_deck`, or `cloud_capabilities`
with an `input`) prints a summary line and one note per problem. Exit code 0 means
clean, 2 means it found something.

```
runner: lammps  gpu-accelerated: 4  cpu-only: 1  missing: 0  uses_gpu: true
```

Three verdicts matter:

| Verdict | Line looks like | What to do |
| --- | --- | --- |
| **missing** | "not built into any hosted LAMMPS image ... LAMMPS would exit at startup" | Do not submit. LAMMPS will not start. Run it on the free local tier, or ask for the package. |
| **CPU-only** | "This deck will NOT use the GPU: pair_style X has no KOKKOS (/kk) version, so the pair force runs on the pod's CPU cores" | Usually stop. You would pay the GPU rate for CPU work and the free local run is often as fast. Pick a GPU-accelerated potential instead, or accept it deliberately. |
| **routed** | "Routed to the full LAMMPS image (lammps-full): X not in the fast default image" | Fine. Same rate, the launch takes about 40 seconds longer for the bigger image pull. |

A separate note, "CPU-side styles (normal, small cost)", is not a problem. Dump
writers and most fixes are CPU work in every LAMMPS build.

`--force` on the CLI and `force: true` on the MCP tools override the refusal. Use it
only when the user has said to.

## A deck that runs

This is the bundled Lennard-Jones argon melt from the MDEngine repository. It is the
smoke test: it needs no data file and no parameter file, so if it fails the problem
is the setup and not the physics.

```
# Lennard-Jones argon melt
units lj
atom_style atomic
lattice fcc 0.8442
region box block 0 10 0 10 0 10
create_box 1 box
create_atoms 1 box
mass 1 1.0
velocity all create 3.0 87287
pair_style lj/cut 2.5
pair_coeff 1 1 1.0 1.0 2.5
neighbor 0.3 bin
fix 1 all nve
thermo 500
dump d all xyz 200 lj_melt.xyz
dump_modify d element Ar
run 2000
```

Copy a bundled example and change it. Do not invent a potential and its coefficients
from scratch, because a wrong `pair_coeff` produces a number rather than an error.

## Running it

```sh
mdengine capabilities deck.in      # free preflight, always first
mdengine run deck.in               # local CPU, free, blocks
mdengine run --gpu deck.in --wall-hours 2
```

From the MCP side: `preflight_deck`, then `submit_job` with the deck inline for
anything under 8 MB, or `create_job` and `start_job` with a presigned PUT for
anything bigger. Locally, `submit_lammps` detaches the job so it survives the server
exiting and the machine sleeping.

## When a run fails

| Symptom | Cause |
| --- | --- |
| Exits at startup, "Unknown pair style" | The image lacks the style. Preflight said `missing`. |
| "Lost atoms" on the CPU line | Something left the box. Open face with no reflecting wall, or a timestep too large. |
| `cudaErrorIllegalAddress` on the GPU line | Same cause, seen later. Check the open faces first. |
| "Cannot open file" | The deck directory was not self-contained, or the path was absolute. |
| Blows up in the first hundred steps | Overlapping atoms from `create_atoms`, or a timestep too large for the potential. Minimize first. |
| Runs but the numbers are nonsense | Wrong `units`, or `pair_coeff` in the wrong order. |
