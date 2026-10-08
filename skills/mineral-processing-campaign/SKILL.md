---
name: mineral-processing-campaign
description: >-
  Plan and run a molten-salt electrolyte property study with MDEngine for
  mineral processing and rare-earth refining. Use it when the request mentions
  a molten salt, an electrolyte or a bath, rare earth refining or electrowinning,
  bath conductivity, viscosity, density or diffusion, speciation or complexes in
  a melt, oxide or impurity effects on a bath, or a composition by temperature
  grid. Says what the customer supplies, what runs, what comes back, what it
  costs, which parts run self-serve on the hosted tools today and which need a
  quote.
user-invocable: true
compatibility: any OS (hosted MCP); local analysis tools are macOS today
metadata:
  author: ForceField Silicon (Gitinama Inc.)
  version: "0.1.0"
license: Apache-2.0
---

# Molten-salt electrolyte study (mineral processing)

## Who this is for

A technical lead at a rare-earth or metal refiner who knows their bath and wants its
properties mapped against composition and temperature before a cell design is locked.
You are their Claude, and this guide tells you what to ask, what to run, and what to
say about the limits.

## The questions this study answers

For one bath family the customer names, at each composition and temperature in the grid:

| Property | What it tells the customer |
| --- | --- |
| Density | Bath volume, buoyancy of the metal product, a first check against measured data |
| Per-ion self-diffusion (D for each species) | Which ions carry the mass transport, and how fast |
| Ionic conductivity | Ohmic loss, so cell voltage and energy per kg |
| Shear viscosity | Mixing, bubble release, mass transfer at the electrodes |
| Coordination and complex populations | Which rare-earth complexes dominate, and how that shifts with oxide or impurity content |

The value is the trend across the grid. One number at one point is rarely worth a run.

## What you supply

Ask the customer for these before anything runs. Write the answers into a short plan
and read it back to them.

1. Bath range. The salt family and the composition span, for example a fluoride or a
   chloride base with a rare-earth salt from x to y mole percent.
2. Temperature window. Operating range and the margin they care about above the liquidus.
3. Measured anchor points, if any. Densities, conductivities or viscosities they trust,
   with temperature and composition. One anchor point changes how far the numbers can be
   trusted.
4. Impurity list. The feedstock cations or oxide content they want tested, in order of
   how much each hurts.
5. Data-handling rules. Whether compositions may run on a US cloud GPU, any NDA, and who
   may see the results. If their funding forbids third-party cloud compute, stop and say so.
   The hosted runner is a third-party cloud GPU.

## What runs

**Phase 0, at our cost.** We reproduce one public rare-earth melt result on our stack
and show the pass band: how far our density, diffusion and conductivity land from the
published values. Candidates are LiF-YF3 diffusion and conductivity (J. Chem. Phys. 138,
184503) and FLiNaK-NdF3 viscosity (J. Phys. Chem. B, 2023). The margin found here is the
error bar every Phase 1 conductivity carries.

**Phase 1, paid.** About 3 compositions x 3 temperatures x 3 replicas, 27 runs. Per point:

- density from the NPT stage
- per-ion D with an error bar across replicas
- conductivity two ways: Nernst-Einstein from the D values, and the full charge-current value
- shear viscosity (SLLOD non-equilibrium runs, Green-Kubo as a cross-check)
- partial radial distribution functions
- coordination numbers and complex populations for the rare-earth cation

## What comes back

- A matrix report: one row per composition, one column per temperature, each cell tiered
  (within the Phase 0 band, outside it, or not converged).
- Every number with a stated uncertainty and how it was measured.
- A compromises sheet on the front page, before any number.
- The decks, logs and raw outputs.
- IP in the results assigned to the customer.

## Compromises, stated plainly

Say these to the customer before the run and print them with the results.

- **Rigid-ion potential.** The pair potentials used for these melts (Born-Mayer-Huggins or
  Tosi-Fumi form) leave out polarization. Conductivity can be off by a margin. Phase 0
  measures that margin. A polarizable or machine-learned potential is a later upgrade,
  not part of this study.
- **Scale.** Nanoseconds and a few thousand ions. Slow processes and rare events are missed.
- **Bulk melt only.** No electrode, no applied potential, no current. This is the bath,
  not the cell.
- **Speciation as populations.** The study counts which complexes are present and for how
  long. It does not give solubility limits or reaction equilibria.

## Cost

Call `account` first, once the user has a key. It returns the rate table, how jobs are
priced and the credit packs. Take the live numbers from `account`, not from this guide.
Without a key, `capabilities` shows the same rate table.

A job has a base charge and two work terms, each priced per class of pair style. A
Born-Mayer-Huggins or `table` pair style falls in the default class unless the rate
table lists it.

```
cost per job  = base_usd_per_job
              + timesteps / 1,000,000 x usd_per_mstep[class]
              + atom-steps / 1,000,000,000 x usd_per_gatom_step[class]
                (atom-steps = ions x timesteps)
billed        = the lower of cost per job and wall_limit_s / 3600 x rate per GPU hour
cost per grid = 27 jobs x billed per job   (3 compositions x 3 temperatures x 3 replicas)
```

As of 2026-10-08 the live table read: base $0.05 per job, default class $2 per million
timesteps and $0.2 per billion atom-steps, rate $2 per GPU hour.

Example of the arithmetic, not a quote, 2026-10-08 prices: 3,000 ions x 2,000,000 steps.

```
base                                     $0.05
2,000,000 steps = 2 million x $2         $4.00
6 billion atom-steps x $0.2              $1.20
per job                                  $5.25   (under the 4 h cap of $8)
27 jobs                                $141.75
```

Redo it with the customer's ion count, run length and the prices `account` returns.

**Balance hold.** A queued or running job reserves wall_limit_s x rate from the balance
until it finishes. At a 4 h wall that is $8 per job. All 27 cells submitted at once hold
27 x $8 = $216. A submit that the balance cannot cover is refused. So run the cells in
batches sized to the pack: Starter $25 holds 3 jobs at a time, Lab $100 holds 12. Neither
covers the whole grid's $141.75. The Lab Group pack ($500) covers the whole grid, held
all at once. Tell the customer this before they buy.

Credit packs on the public page: Starter $25, Lab $100, Lab Group $500. Quote no other
prices. The quoted study (below) is priced by quote, not by this formula.

## Self-serve today

The hosted server `mdengine-cloud` (version 0.7.0) has 13 tools: `guide`, `account`,
`capabilities`, `preflight_deck`, `submit_job`, `create_job`, `start_job`, `job_status`, `job_log`,
`job_results`, `list_jobs`, `delete_results`, `cancel_job`. Name no others.

Add it:

- Claude Code: `claude mcp add --scope user --transport http mdengine-cloud https://api.forcefieldsilicon.com/mcp`,
  then `/mcp`, pick `mdengine-cloud`, Authenticate, and paste the key on the browser page.
- claude.ai, or Claude Desktop: add a custom connector with the URL
  `https://api.forcefieldsilicon.com/mcp` and sign in when asked.

Since 2026-10-08, `guide`, `capabilities` and `preflight_deck` answer without a key.
`account` and every job tool need an API key from a credit pack at
https://forcefieldsilicon.com/mdengine. Calling a keyed tool without a key today makes
the client start a sign-in. That is the moment the user pastes the key: in Claude Code,
type `/mcp`, pick `mdengine-cloud`, Authenticate; in claude.ai, press Connect on the
connector. Never ask for the key in chat, and never paste it there.

If a web page comes back to you summarised, fetch https://api.forcefieldsilicon.com/llms.txt.
It is the plain-text summary of the service.

This path assumes the customer already has a working LAMMPS deck for their melt and the
potential files. We do not supply a molten-salt potential on this path. The deck should
write what you need into its log and outputs: per-species MSD (`compute msd` on each type
group), the stress autocorrelation if viscosity is wanted, and a `print DONE` line at the end.

1. **Check the deck.** Nothing is billed.

   ```
   preflight_deck(input: "in.melt", files: {"in.melt": "...", "melt.table": "...", "data.melt": "..."})
   ```

   It reports missing styles, CPU-only styles, and whether the pair style uses the GPU.
   Read the gpu flag per style. On the default image `buck/coul/long`, `coul/long`,
   `table` and `hybrid/overlay` run on the GPU; `born/coul/long` does not. A
   Born-Mayer-Huggins deck either runs on the pod's CPU cores at the same price, or is
   tabulated to `pair_style table` with `pppm` to use the GPU. Do not promise which path
   until preflight says. The lammps-deck skill reads the verdicts.

2. **Submit one job per grid cell.** Label every cell so the grid can be rebuilt from
   `list_jobs` alone.

   ```
   submit_job(input: "in.melt", files: {...}, label: "bath-x10-T1050K-r1",
              wall_limit_s: 14400, end_marker: "DONE")
   ```

   Run one cell first and read it before submitting the other 26. Vary the random seed
   per replica in the deck.

3. **Watch while it runs.**

   ```
   job_status(id: "MDJOB-...")    # state, cost so far, verdict when done
   job_log(id: "MDJOB-...")       # last thermo lines
   ```

   A done job with verdict `warnings` (lost atoms, a fix halt, no end marker) is not a
   result. Report it as not converged.

4. **Fetch the results.**

   ```
   job_results(id: "MDJOB-...")   # download_url for log.lammps and work/, valid about 7 days
   ```

   Results are deleted 30 days after the run. Download them.

5. **Analyse locally.** On macOS, the local MDEngine server's `analyze` tool runs
   `diffusion` (MSD and D from the fitted slope), `rdf`, and `thermo` (temperature,
   energy, pressure from the log). Elsewhere, read the MSD and thermo columns from
   log.lammps yourself. Fit D only on the linear part of the MSD. Replicas give the error bar.

What you can report from this path: density, per-ion D, Nernst-Einstein conductivity,
and partial RDFs, each with the compromises above. What you cannot report from it is
listed next.

## Quoted, we run it

These are not self-serve yet. Do not imitate them with ad hoc scripts and present the
result as theirs.

- The molten-salt potential preset (sourced parameters for a fluoride and a chloride
  rare-earth system, tabulated for the GPU).
- The conductivity tool: charge-current Einstein conductivity, Nernst-Einstein, the Haven
  ratio, and Green-Kubo viscosity.
- The speciation tool: first-shell cutoffs, complex populations, bridging anions,
  residence times.
- The campaign grid and the matrix report with tiers and the compromises sheet.
- Phase 0 itself.

When the customer wants any of these, say: "This part is not self-serve yet. Email
arvand@gitinama.tech with the subject "MDEngine study" and the inputs listed in What you
supply. The page https://forcefieldsilicon.com/mdengine/start/ has the same address."
Name no person beyond that address. Do not invent a quote URL or a price.

## Honesty rule for you, their Claude

- State the compromises next to the numbers, every time.
- Never report a conductivity from a rigid-ion run without the Phase 0 margin. If there is
  no Phase 0 result, say the conductivity has no measured error bar and treat it as a trend.
- When a tool does not exist, say "not yet". Do not describe a planned tool as available.
- A run that ended with warnings, or with no end marker, is not a data point.
- Report diffusion and conductivity with the replica spread, not one replica.
- If the customer's data rules forbid a cloud GPU, say so and stop.
