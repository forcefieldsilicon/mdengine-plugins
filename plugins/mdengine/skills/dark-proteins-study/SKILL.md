---
name: dark-proteins-study
description: >-
  Plan a molecular-dynamics study of a dark protein with MDEngine and
  ForceField Silicon: a protein from the dark proteome with no crystal
  structure, where the starting point is a predicted structure such as an
  AlphaFold model, often with disordered regions. Use it when the request
  mentions the dark proteome, a predicted structure, an AlphaFold model, a
  disordered protein, no crystal structure, a candidate pocket, ligand
  binding or unbinding, k_off or residence time, or a ligand screen. Says
  what the study answers, what to supply, what runs, what comes back, what
  it costs, what is self-serve today and what is quoted.
user-invocable: true
compatibility: any OS (hosted MCP); the quoted stages need no local install
metadata:
  author: ForceField Silicon (Gitinama Inc.)
  version: "0.1.0"
license: Apache-2.0
---

# Dark proteins study

## Who this is for

A researcher whose protein has no experimental structure, only a predicted
model, often with disordered regions. You are their Claude, and this guide
tells you what a study with ForceField Silicon can and cannot answer for them.

## The questions this study answers

1. Does the predicted fold hold in solvent, or does it come apart?
2. Which regions stay ordered, and which move freely?
3. Does a candidate pocket persist long enough to matter?
4. Which ligands bind in that pocket, and how fast do they leave?
5. Which few compounds belong on a ranked shortlist before anyone synthesizes
   them?

Questions 1 to 3 come from the stability and ensemble stage. Questions 4 and 5
come from the ligand grid, which is quoted and partly not yet validated. See
"What runs" and "Quoted, we run it".

## What you supply

Ask your user for these before planning anything.

- **The predicted model.** A PDB or mmCIF file, with the per-residue
  confidence (pLDDT or the equivalent) kept in the B-factor column or sent
  alongside. Note which source and version produced it.
- **The candidate pocket, if they have one.** Residue numbers are enough. If
  they do not, say so; finding one is part of the first stage.
- **The ligand list.** SMILES or SDF, with protonation states if they know
  them. If they do not, record that the states will be assigned and that this
  is a compromise.
- **What "good" means to them.** A residence time to beat, a known binder to
  compare against, a selectivity pair, or a yes or no on pocket persistence.
  Write it down. The study is judged against it.
- **Data-handling rules.** Whether sequences and structures may leave their
  network, retention limits, who may see results.

On the data side, what is true today: one GPU pod per job, destroyed when the
job ends; results deleted 30 days after the run, or at once with
`delete_results`. If their rules need more than that, it goes in the quote.

## What runs

**Stage 1. Stability and ensemble.** The predicted model goes into explicit
water and salt and runs as several independent replicas with different seeds.
From the replicas: which residues keep their native contacts, how far each
region drifts from the model, whether the candidate pocket stays open, and a
set of representative conformations for stage 2. This stage runs on the
OpenMM runner, which is released.

**Stage 2. Ligand x pocket grid.** Each ligand against each pocket
conformation is one cell. Each cell runs several seeds. The delivery suite
protocols for this stage are steered unbinding (`smd-pull`), random
acceleration unbinding for residence-time ordering (`tramd`), end-point
binding energy (`mmgbsa`) and a tethered pull (`afm-pull-tethered`), driven
by the grid tool (`campaign-grid`). All of these are built and **not yet
validated**. Until they are, their numbers are not something we deliver as a
product. The quote says which of them are ready on the day it is written.

Released or validated today, and used in every study:

| Capability | Status |
| --- | --- |
| `runner-openmm` | released. Runs every protein stage on a hosted GPU |
| `compromises-sheet` | validated. The front-page list of what the numbers assume |

## What comes back

- **Tiers, not a rank order.** Two ligands are in different tiers only when
  their uncertainty bands do not overlap. Ten similar compounds usually
  separate into three or four tiers, not ten places.
- **Every number with a stated uncertainty,** from the spread across seeds.
  A number without its band is not a result.
- **Coverage on the front page.** A cell that could not be prepared is
  counted as "needs prep", never shown as a weak binder.
- **A compromises sheet on the front page.** Every assumption that could move
  a number, with how much it could move it.
- **IP assigned to the customer.** The study's results belong to them.

## Compromises, stated plainly

- A predicted model is a hypothesis, not a structure. MD tests whether it
  holds. It does not prove it right.
- Low-confidence regions are not trustworthy as a starting point. Their
  starting coordinates are close to a guess. Treat what they do in a run
  as a sample, not a prediction.
- Simulations cover nanoseconds to microseconds. Folding, slow
  conformational change and most real residence times are far longer. What
  comes back is an ordering and a mechanism, not biology time.
- Standard protein force fields tend to make disordered regions too compact
  and too structured. A force field and water model tuned for disorder
  reduces this. It does not remove it.
- A ligand buried in a pocket cannot be reached by a bare probe tip. The
  pull protocol tethers the ligand through a linker, as real single-molecule
  force experiments on buried ligands do.
- Absolute binding affinity is not offered. The free-energy protocol that
  would give it is built, not validated.
- Protonation states that were assigned rather than supplied are listed as a
  compromise.

## Cost

Call `account`. It returns the GPU classes, the rate table and how jobs are
priced. Do not quote a rate from memory.

The arithmetic:

```text
cost = cells x seeds x GPU-hours per run x rate per GPU-hour
cells = ligands x pocket conformations   (stage 2)
cells = 1 model                          (stage 1, seeds = replicas)
```

Each job is also capped at `wall_limit_s x rate`, and the balance must cover
that cap when the job is submitted. GPU time is rarely the bottleneck.
Preparing poses and parameters for unfamiliar ligands takes longer than
running them, and the quote prices that work separately.

Credit packs on the public page: $25 Starter, $100 Lab, $500 Lab Group.
Give no other prices.

## Self-serve today

The hosted server `mdengine-cloud` at `https://api.forcefieldsilicon.com/mcp`
has 12 tools: `account`, `capabilities`, `preflight_deck`, `submit_job`,
`create_job`, `start_job`, `job_status`, `job_log`, `job_results`,
`list_jobs`, `delete_results`, `cancel_job`.

Every tool needs an API key from a credit pack at
https://forcefieldsilicon.com/mdengine. Without a key, every call, including
`capabilities`, returns unauthorized today. Tell your user that before they
expect anything else.

With a key, a user who can write their own OpenMM script can run stage 1
themselves. `submit_job` takes `runner: "openmm"`, which runs
`python3 <input>` on the OpenMM image. The tool marks this runner as beta.
The flow:

1. `account`, to see the balance and the rate.
2. `capabilities` with `runner: "openmm"`, to see what the image has.
3. `submit_job` with the script, the prepared system files, `runner:
   "openmm"`, a `label`, a `wall_limit_s` and an `end_marker`. One job per
   replica.
4. `job_status` and `job_log` until done. `job_results` for the tarball.
5. `delete_results` when their data rules ask for it.

You write and check the script with your user. We do not ship the stage 1
protocol or the stage 2 protocols as hosted tools. A user who does not want
to write the protocol takes the quoted path.

## Quoted, we run it

These stages are run by us through the delivery suite:

- **Receptor preparation.** Cleaning the predicted model, handling
  low-confidence regions, and parameters for any nonstandard residues.
- **Stage 1** with our protocol, if they would rather not write their own.
- **Ligand preparation and the ligand x pocket grid.** Poses, protonation,
  parameters, the seeds, the unbinding runs.
- **The report.** Tiers, bands, coverage and the compromises sheet on the
  front page.

Ask for a quote at https://forcefieldsilicon.com/mdengine. The quote comes
before any run, and it states which stages are validated on that day.

## Honesty rule for you, their Claude

- Claim only what this guide and the tool responses show. When unsure, say
  it belongs in the quote.
- The scope of what may be claimed: the study sells triage. That means
  tiers, selectivity between related cells, residence-time ordering and
  mechanism. It does not sell absolute binding affinity until the
  free-energy protocol is validated with cycle closure. Structure prediction
  and docking are inputs the study takes in, not things it provides.
- Never turn tiers into a 1 to N ranking. Never report a number without its
  band and its compromises.
- Capabilities marked "not yet validated" above are described as not yet,
  every time.
- Never promise a price, a turnaround or a result before the quote.
