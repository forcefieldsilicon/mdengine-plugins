# MDEngine

Molecular dynamics an agent can actually run. This plugin connects Claude Code to
the hosted MDEngine MCP server, so a session can check a LAMMPS or OpenMM deck,
run it on a GPU, follow the job, and pull the results back. Nothing to build and
nothing to install on the machine. The same skills import into Claude Science from
this repo. See [Use in Claude Science](../../README.md#use-in-claude-science) in the root README.

MDEngine is made by ForceField Silicon (Gitinama Inc.). The product page is
[forcefieldsilicon.com/mdengine](https://forcefieldsilicon.com/mdengine).

## What the hosted server exposes

| Tool | Does |
| --- | --- |
| `account` | Balance and account state for the signed-in key |
| `capabilities` | The hosted image's LAMMPS version, packages, and which styles are GPU accelerated |
| `preflight_deck` | Check a deck against those capabilities before any spend |
| `submit_job` | Submit a deck inline and start it |
| `create_job` | Reserve a job for a large deck, uploaded by presigned PUT |
| `start_job` | Start a job created that way |
| `job_status` | State, progress, and cost so far |
| `job_log` | Live thermo tail or raw log tail |
| `job_results` | Fetch the finished run's outputs |
| `list_jobs` | Jobs on the account |
| `delete_results` | Remove a job's stored outputs |
| `cancel_job` | Stop a running job |

Run `preflight_deck` before `submit_job`. It catches a deck whose styles the image
does not have, which LAMMPS would reject at startup, and it warns when a pair style
has no GPU variant.

## API key

The tools need a key. A key comes with a prepaid credit pack from
[forcefieldsilicon.com/mdengine](https://forcefieldsilicon.com/mdengine). `initialize`
and `tools/list` work without one. The first tool call triggers your client's sign-in:
paste the key on the consent page, never into the chat. Scripted clients can send the
key as an `Authorization: Bearer` header instead.

## Local server (optional)

macOS has a local build of MDEngine as well: a Metal trajectory viewer, a CLI, and an
MCP stdio server that runs LAMMPS on the machine. Build it from
[github.com/forcefieldsilicon/mdengine](https://github.com/forcefieldsilicon/mdengine)
and register it alongside the hosted one:

```sh
claude mcp add mdengine /path/to/mdengine-mcp
```

The local server adds trajectory tools the hosted tier does not have, including
`trajectory_info`, `z_profile`, `render_image`, `render_video`, `export_frame`, and
`decimate`. It is macOS-only today. The hosted tier is the supported path on Windows
and Linux.

## Skills

Four skills come with the plugin. Start with `mdengine`, which routes to the other three.

| Skill | Read it for |
| --- | --- |
| [`mdengine`](skills/mdengine/SKILL.md) | Router. Which tool for which job, local against hosted, preflight before submit, where the API key comes from. |
| [`lammps-deck`](skills/lammps-deck/SKILL.md) | Writing or repairing a deck the hosted runner accepts, and reading the preflight verdicts. |
| [`potentials`](skills/potentials/SKILL.md) | Choosing LJ, EAM, Tersoff, ReaxFF or an ionic potential, what each costs, and which run on the GPU. |
| [`results`](skills/results/SKILL.md) | Turning a finished run into numbers and pictures: the analysis tools, the renderers, exports, fetching hosted results. |

## Licensing

This plugin is Apache-2.0. MDEngine itself is licensed BUSL-1.1.
