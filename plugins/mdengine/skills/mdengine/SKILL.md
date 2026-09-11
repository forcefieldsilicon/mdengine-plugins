---
name: mdengine
description: >-
  Start here for any molecular-dynamics task with MDEngine: run a LAMMPS or
  OpenMM deck, run it on a hosted GPU, inspect a trajectory, measure something
  from a finished run, render a frame or a video, pick a potential, or work out
  why a deck was refused. Use it when the request mentions LAMMPS, OpenMM, a
  deck or input script, a trajectory, a dump file, an MD simulation, "run this
  on a GPU", "analyze this trajectory", or "render this run". Routes to
  lammps-deck, potentials and results.
user-invocable: true
compatibility: macOS (local tools), any OS (hosted MCP)
metadata:
  author: ForceField Silicon (Gitinama Inc.)
  version: "0.1.0"
license: Apache-2.0
---

# MDEngine (router)

MDEngine is a molecular-dynamics workbench from ForceField Silicon. It has three
surfaces and this skill picks between them.

| Surface | What it is |
| --- | --- |
| `mdengine-cloud` MCP server | Hosted GPU runs over HTTP. Works on any OS. Needs an API key. |
| `mdengine` MCP server (local) | A stdio server on the machine: trajectory tools, renderers, and a local job runner. macOS today. |
| `mdengine` CLI | The same things from a terminal. macOS today. |

## The lanes

| Lane | Read it for |
| --- | --- |
| **lammps-deck** | Writing or repairing a deck the hosted runner will accept. The self-contained rule, the open-face ceiling, the preflight verdicts. |
| **potentials** | Choosing LJ, EAM, Tersoff, ReaxFF or an ionic potential, and knowing which of them use the GPU. |
| **results** | Turning a finished run into numbers and pictures. Analysis tool ids, renders, exports, fetching hosted results. |

## Which tool

Local server, on a file that is already on the machine:

| Tool | Answers |
| --- | --- |
| `trajectory_info` | How many frames, how many atoms, which elements, what box |
| `analyze` | Everything measured. Call it with no `tool` first to get the catalogue |
| `z_profile` | Deposition and oxidation depth. Kept as an alias of `analyze(tool: 'z_profile')` |
| `render_image` | One frame to a PNG, so the agent can see the state |
| `render_video` | The trajectory to an MP4 or a GIF |
| `export_frame` | One frame out as XYZ, with charges if the dump carries them |
| `decimate` | Keep every Nth frame of a trajectory that is too big |
| `cloud_capabilities` | What the hosted image has, and preflight a deck against it |
| `submit_lammps` | A detached local job, or a remote host, or `host: cloud` |
| `job_status`, `job_log`, `job_files`, `list_jobs`, `cancel_job` | Follow a job |
| `fetch_job` | Pull a remote or hosted job's outputs back to the machine |
| `list_hosts` | Which execution hosts are configured |
| `run_lammps` | A synchronous run. Short tests only, it blocks |

Hosted server, from any OS:

| Tool | Answers |
| --- | --- |
| `account` | Balance and account state |
| `capabilities` | LAMMPS version, packages, which styles are GPU accelerated |
| `preflight_deck` | Would this deck run, and would it use the GPU. Nothing is billed |
| `submit_job` | Deck inline, up to 8 MB, and start it |
| `create_job` then `start_job` | A large deck, uploaded by presigned PUT |
| `job_status`, `job_log` | State, progress, thermo tail |
| `job_results` | The finished run's outputs |
| `list_jobs`, `delete_results`, `cancel_job` | Manage what is there |

## Rules

**Preflight before you submit.** Always. `preflight_deck` on the hosted server,
`mdengine capabilities <deck.in>` from the CLI, or `cloud_capabilities` locally.
It is free and it catches the two failures that cost the most: a style the image
does not have, which makes LAMMPS exit at startup, and a pair style with no GPU
variant, which makes the run crawl on the pod's CPU cores. Read the verdicts in
the **lammps-deck** skill.

**Local or hosted.** Run locally when the work is under about two minutes of CPU
time: a smoke test, a scaling probe, a deck you are still editing. Go hosted when
the pair style is GPU accelerated and the run is longer than a few minutes, or
when the machine is not a Mac. A deck whose preflight says `uses_gpu: false` is
usually faster and free on the local tier, so say that instead of submitting it.

```sh
mdengine capabilities deck.in     # free, always first
mdengine run deck.in              # local, CPU, free
mdengine run --gpu deck.in        # hosted GPU, spends credits
```

**The hosted tier needs a key.** A key comes with a prepaid credit pack at
[forcefieldsilicon.com/mdengine](https://forcefieldsilicon.com/mdengine). Store it
once with `mdengine login mde_...`, or let the MCP client's sign-in do it: the
client opens a consent page, the key is pasted there, and the client keeps a token.
Never ask a user to paste a key into the chat. Scripted clients can send
`Authorization: Bearer mde_...` instead.

**Prices are by the work the deck does**, not by the wall clock, so a number quoted
here would be wrong for the next deck. Point at
[forcefieldsilicon.com/mdengine](https://forcefieldsilicon.com/mdengine) for the
current packs, and use `account` or `mdengine account` for the live balance and rate
table. `job_status` carries the cost of the job in front of you.

**A deck is a program.** LAMMPS decks can run shell commands. Read a deck from
someone else before you submit it, exactly as you would read a shell script.

## Spending credits

Every hosted submission spends. Before `submit_job` or `mdengine run --gpu`:

1. Preflight came back clean, or the user said to go anyway.
2. The user knows a run is about to start. Say what the deck is and how long it
   should take.
3. `--wall-hours` is set to something the deck cannot silently exceed. The cap is
   billed if it is hit.

Infrastructure failures are not billed. A job that comes back `pod_lost`,
`no_capacity`, `launch_timeout` or `gpu_unavailable` cost nothing and is relaunched
once on its own. A job that comes back `lammps_error` is the deck's fault and
`job_log` holds the error text.

## When something is refused

| Symptom | What it means |
| --- | --- |
| 401 or "authentication required" | No key yet. Use the client's sign-in, or `mdengine login`. |
| "insufficient balance" | Top up at the product page. A submission needs credit for a minimum slice of GPU time. |
| `gpu_runners_open_soon` (503) | Runners are closed right now. Credits are safe. Retry later. |
| Preflight says `missing: N` | The image does not have that style. Run it locally, or ask ForceField Silicon to add the package. |
| Preflight says `uses_gpu: false` | It would run, on CPU cores, at the GPU rate. Usually the wrong call. |
| Job `failed` with `lammps_error` | The deck. Read `job_log`, then the **lammps-deck** skill. |

## Ask the tool, not this file

The hosted image and the analysis catalogue both move faster than this skill.
Take capability from the tool in front of you:

| Question | Ask |
| --- | --- |
| Which styles are GPU accelerated today | `capabilities` / `mdengine capabilities` |
| Which analyses exist and what they take | `analyze` with no `tool` / `mdengine analyze` |
| What a CLI subcommand accepts | `mdengine <subcommand> --help` |
| What a hosted job did | `job_status`, `job_log` |
