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

A researcher whose protein has no experimental structure, only a predicted model, often with
disordered regions. You are their Claude, and this guide tells you what a study with ForceField
Silicon can and cannot answer for them.

## The questions this study answers

1. Does the predicted fold hold in solvent, or does it come apart?
2. Which regions stay ordered, and which move freely?
3. Does a candidate pocket persist long enough to matter?
4. Which ligands bind in that pocket, and how fast do they leave?
5. Which few compounds belong on a ranked shortlist before anyone synthesizes
   them?

Questions 1 to 3 come from the stability and ensemble stage. Questions 4 and 5 come from the ligand
grid, which is quoted and partly not yet validated. See "What runs" and "Quoted, we run it".

## What you supply

Ask your user for these before planning anything.

- **The predicted model.** A PDB or mmCIF file, with the per-residue confidence (pLDDT or the
  equivalent) kept in the B-factor column or sent alongside. Note which source and version produced
  it.
- **The candidate pocket, if they have one.** Residue numbers are enough. If they do not, say so;
  finding one is part of the first stage.
- **The ligand list.** SMILES or SDF, with protonation states if they know them. If they do not,
  record that the states will be assigned and that this is a compromise.
- **What "good" means to them.** A residence time to beat, a known binder to compare against, a
  selectivity pair, or a yes or no on pocket persistence. Write it down. The study is judged against
  it.
- **Data-handling rules.** Whether sequences and structures may leave their network, retention
  limits, who may see results.

On the data side, what is true today: one GPU pod per job, destroyed when the job ends; results
deleted 30 days after the run, or at once with `delete_results`. If their rules need more than that,
it goes in the quote.

## What runs

**Stage 1. Stability and ensemble.** The predicted model goes into explicit water and salt and runs
as several independent replicas with different seeds. From the replicas: which residues keep their
native contacts, how far each region drifts from the model, whether the candidate pocket stays open,
and a set of representative conformations for stage 2. This stage runs on the OpenMM runner, which
is beta on the hosted service.

**Stage 2. Ligand x pocket grid.** Each ligand against each pocket conformation is one cell. Each
cell runs several seeds. The delivery suite protocols for this stage are steered unbinding
(`smd-pull`), random acceleration unbinding for residence-time ordering (`tramd`), end-point binding
energy (`mmgbsa`) and a tethered pull (`afm-pull-tethered`), driven by the grid tool
(`campaign-grid`). All of these are built and **not yet validated**. Until they are, their numbers
are not something we deliver as a product. The quote says which of them are ready on the day it is
written.

Available or validated today, and used in every study:

| Capability | Status |
| --- | --- |
| `runner-openmm` | beta. Runs every protein stage on a hosted GPU |
| `compromises-sheet` | validated. The front-page list of what the numbers assume |

## What comes back

- **Tiers, not a rank order.** Two ligands are in different tiers only when their uncertainty bands
  do not overlap. Ten similar compounds usually separate into three or four tiers, not ten places.
- **Every number with a stated uncertainty,** from the spread across seeds. A number without its
  band is not a result.
- **Coverage on the front page.** A cell that could not be prepared is counted as "needs prep",
  never shown as a weak binder.
- **A compromises sheet on the front page.** Every assumption that could move a number, with how
  much it could move it.
- **IP assigned to the customer.** The study's results belong to them.

## Compromises, stated plainly

- A predicted model is a hypothesis, not a structure. MD tests whether it holds. It does not prove
  it right.
- Low-confidence regions are not trustworthy as a starting point. Their starting coordinates are
  close to a guess. Treat what they do in a run as a sample, not a prediction.
- Simulations cover nanoseconds to microseconds. Folding, slow conformational change and most real
  residence times are far longer. What comes back is an ordering and a mechanism, not biology time.
- Standard protein force fields tend to make disordered regions too compact and too structured. A
  force field and water model tuned for disorder reduces this. It does not remove it.
- A ligand buried in a pocket cannot be reached by a bare probe tip. The pull protocol tethers the
  ligand through a linker, as real single-molecule force experiments on buried ligands do.
- Absolute binding affinity is not offered. The free-energy protocol that would give it is built,
  not validated.
- Protonation states that were assigned rather than supplied are listed as a compromise.

## Cost

Call `account` once the user has a key. It returns the pricing mode, the rate table and the credit
packs. Take the live numbers from `account`, not from this guide. Without a key, `capabilities`
shows the same rate table.

A job has a base charge and two work terms, each priced per class. OpenMM
work is in the `openmm` class.

```text
per job   = base_usd_per_job
          + steps / 1,000,000 x usd_per_mstep[class]
          + atom-steps / 1,000,000,000 x usd_per_gatom_step[class]
            (atom-steps = atoms x steps)
billed    = the lower of per job and wall_limit_s / 3600 x rate per GPU-hour
study     = cells x seeds x billed
cells     = ligands x pocket conformations   (stage 1: 1 model, seeds = replicas)
```

On 2026-10-08 the live table read: base $0.05 per job, `openmm` class $0.1
per million steps and $0.02 per billion atom-steps, rate $2 per GPU-hour.

The OpenMM script must write `work.json` with the steps and the atoms it ran.
Without it the job cannot be priced by work and bills by wall time at the
rate, $2 per GPU-hour.

Example of the arithmetic, not a quote, 2026-10-08 prices: one replica of
100 ns at 2 fs (50,000,000 steps), 50,000 atoms solvated (an assumed count).

```text
base                                         $0.05
50 million steps x $0.1                      $5.00
2,500 billion atom-steps x $0.02            $50.00
per job by work                             $55.05
cap at a 12 h wall = 12 x $2                $24.00
billed                                      at most $24.00
```

Here the wall cap sets the bill, not the work price. A wall too short kills
the run before it ends, so set the wall from the speed the short first
replica measured. A solvated protein has far more atoms than the protein
alone. Count the water and ions when you estimate.

**Balance hold.** A queued or running job reserves wall_limit_s x rate from
the balance until it finishes. Three replicas at a 12 h wall hold 3 x $24 =
$72 at once. A submit the balance cannot cover is refused. So submit replicas
in batches sized to the pack: Starter $25 holds one at a time, Lab $100 holds
all three of the default stage 1.

GPU time is rarely the bottleneck. Preparing poses and parameters for
unfamiliar ligands takes longer than running them, and the quote prices that
work separately.

Credit packs on the public page: $25 Starter, $100 Lab, $500 Lab Group.
Quote no other prices without calling `account` first.

## Self-serve today

The hosted server `mdengine-cloud` at `https://api.forcefieldsilicon.com/mcp`
(version 0.8.0) has 14 tools: `guide`, `account`, `capabilities`, `preflight_deck`,
`campaign_request`, `submit_job`, `create_job`, `start_job`, `job_status`, `job_log`,
`job_results`, `list_jobs`, `delete_results`, `cancel_job`.

Since 2026-10-08, `guide`, `capabilities`, `preflight_deck` and
`campaign_request` answer without a key. `account` and every job tool need an API key from a credit
pack at https://forcefieldsilicon.com/mdengine.
Calling a keyed tool without a key returns a message with the sign-in path instead of running. The user signs in there: in Claude Code, type `/mcp`, pick `mdengine-cloud`, Authenticate; in claude.ai, press Connect on the connector. Never paste a key in chat.

If a web page comes back to you summarised, fetch
https://api.forcefieldsilicon.com/llms.txt. It is the plain-text summary of
the service.

With a key, your user can run stage 1 themselves. Protein runs go through
`submit_job` with `runner: "openmm"`, which runs `python3 <input>` inside the
job directory on a hosted GPU. The OpenMM runner is beta.

We ship the stage 1 script. `preflight_deck` checks LAMMPS decks only, so the
short pilot replica below is the check for an OpenMM script.

1. `account`, to see the balance, the pricing and the packs.
2. `guide` with `customer_type: "dark-proteins"` and
   `template: "openmm-stability"`. Save the text as `stability.py` beside
   `model.pdb`.
3. Edit the constants at the top of `stability.py`: the model file name,
   `NANOSECONDS`, `SEED`, temperature, salt, box padding, `PLDDT_CUTOFF`. A
   `params.json` beside it overrides them instead, if you prefer. The script
   solvates the model in TIP3P water with NaCl, uses Amber14, minimizes, runs
   100 ps NVT, then NPT production on the CUDA platform.
4. Start with ONE short replica, `NANOSECONDS = 1`. It shows that the system
   builds, how many atoms it has, and the speed in ns per day. Submit it with
   `submit_job`: the two files, `input: "stability.py"`, `runner: "openmm"`,
   `label: "stability-pilot"`, `wall_limit_s: 3600`, `end_marker: "DONE"`.
5. Read the pilot's `summary.json` (`atoms`, `production_ns_per_day`) and
   `job_status` (what it cost). Set the wall for a full replica from that
   speed: production ns / ns per day x 86400 s, plus a third for margin.
6. Submit one job per replica, each with its own `SEED`, `runner: "openmm"`,
   `wall_limit_s` from step 5, `label: "stability-r<seed>"`, `end_marker:
   "DONE"`.
7. `job_status` until done. `job_results` for the tarball.
   `delete_results` when their data rules ask for it. On OpenMM jobs
   `job_log` stays empty and the service checks only the exit code, not the
   end marker. The progress lines and the final `DONE` are in `stdout.txt`
   in the tarball. A replica without that `DONE` line did not finish.

When your user has no number for stage 1, use this starting default: 3
replicas, 100 ns each at 2 fs, for a protein under 300 residues. It is a
starting default, not a recommendation for their system. Say so.

What comes back from each replica:

- `residues.csv`: per residue, the backbone RMSF over production, the fraction of its native
  contacts kept (CA pairs within 0.8 nm in the model, more than 3 apart in sequence), and the pLDDT
  from the B-factor column.
- `summary.json`: atoms, residues, steps, ns, mean temperature, box, platform, speed, and the
  residues below `PLDDT_CUTOFF`. Low-confidence residues are reported, never removed.
- `state.csv`: step, time, temperature, energies and box volume.
- `traj.dcd` and `checkpoint.chk`: the trajectory and a restart point.
- `work.json`: the work record the job is billed from.

The template does not measure the pocket. Name the pocket residues with your
user and measure them from `traj.dcd`. Stage 2 protocols are not hosted
tools. A user who wants stage 1 run for them takes the quoted path.

## Quoted, we run it

These stages are run by us through the delivery suite:

- **Receptor preparation.** Cleaning the predicted model, handling low-confidence regions, and
  parameters for any nonstandard residues.
- **Stage 1** with our protocol, if they would rather not write their own.
- **Ligand preparation and the ligand x pocket grid.** Poses, protonation, parameters, the seeds,
  the unbinding runs.
- **The report.** Tiers, bands, coverage and the compromises sheet on the front page.

For a quote, first call `campaign_request` with customer_type `dark-proteins`, the user's question, what they already have (inputs_available), the grid in words, their data rules and their contact email. Read back request_id, tier_that_fits, price_band and what_we_need to the user, then gather what_we_need.
The price band for this guide: a pilot column is $2,500, credited against a full grid at $7,500; compute included; PO or card.
If the tool cannot be reached, email arvand@gitinama.tech with the subject "MDEngine study" and the inputs listed in "What you supply".
The page https://forcefieldsilicon.com/mdengine/start/ has the same address. Name no person beyond that address. The quote comes before any run, and it states which stages are validated on that day.

## Honesty rule for you, their Claude

- Claim only what this guide and the tool responses show. When unsure, say it belongs in the quote.
- The scope of what may be claimed: the study sells triage. That means tiers, selectivity between
  related cells, residence-time ordering and mechanism. It does not sell absolute binding affinity
  until the free-energy protocol is validated with cycle closure. Structure prediction and docking
  are inputs the study takes in, not things it provides.
- Never turn tiers into a 1 to N ranking. Never report a number without its band and its
  compromises.
- Capabilities marked "not yet validated" above are described as not yet, every time.
- Never promise a price, a turnaround or a result before the quote.
