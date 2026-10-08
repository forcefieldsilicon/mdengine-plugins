# ForceField Silicon plugins

The plugin marketplace for [MDEngine](https://forcefieldsilicon.com/mdengine),
the molecular-dynamics workbench from ForceField Silicon (Gitinama Inc.).

## Install

```sh
claude plugin marketplace add forcefieldsilicon/mdengine-plugins
claude plugin install mdengine@forcefieldsilicon
```

## Use in Claude Science

1. Add the hosted server. In Settings > Connectors > Add connector > Remote, name it
   `mdengine-cloud` and set the server URL to `https://api.forcefieldsilicon.com/mcp`.
   Under Advanced settings, pick the Streamable HTTP transport. Sign in with the key
   from a credit pack.
2. Add the skills. In Settings > Skills > Add skill > Import from GitHub, enter
   `forcefieldsilicon/mdengine-plugins` and select the six skills: `mdengine`,
   `lammps-deck`, `potentials`, `results`, `mineral-processing-campaign` and
   `dark-proteins-study`.
3. `skills/` at the repo root mirrors `plugins/mdengine/skills/`, kept identical by
   `scripts/sync_skills.sh --check`.

## Plugins

| Plugin | What it gives an agent |
| --- | --- |
| [`mdengine`](plugins/mdengine/README.md) | The hosted MDEngine MCP server plus six skills: check a deck, run LAMMPS or OpenMM on a GPU, watch the job, pull the results, and read them. |

## Credits and API keys

The hosted tools need an API key. A key comes with a prepaid credit pack from
[forcefieldsilicon.com/mdengine](https://forcefieldsilicon.com/mdengine). Sign in
when your client asks and paste the key once on the consent page. The key stays
with you.

## Licensing

This repository is Apache-2.0. MDEngine itself is licensed BUSL-1.1 and lives at
[github.com/forcefieldsilicon/mdengine](https://github.com/forcefieldsilicon/mdengine).
