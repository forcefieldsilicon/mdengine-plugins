# ForceField Silicon plugins

The plugin marketplace for [MDEngine](https://forcefieldsilicon.com/mdengine),
the molecular-dynamics workbench from ForceField Silicon (Gitinama Inc.).

## Install

```sh
claude plugin marketplace add forcefieldsilicon/mdengine-plugins
claude plugin install mdengine@forcefieldsilicon
```

## Plugins

| Plugin | What it gives an agent |
| --- | --- |
| [`mdengine`](plugins/mdengine/README.md) | The hosted MDEngine MCP server plus four skills: check a deck, run LAMMPS or OpenMM on a GPU, watch the job, pull the results, and read them. |

## Credits and API keys

The hosted tools need an API key. A key comes with a prepaid credit pack from
[forcefieldsilicon.com/mdengine](https://forcefieldsilicon.com/mdengine). Sign in
when your client asks and paste the key once on the consent page. The key stays
with you.

## Licensing

This repository is Apache-2.0. MDEngine itself is licensed BUSL-1.1 and lives at
[github.com/forcefieldsilicon/mdengine](https://github.com/forcefieldsilicon/mdengine).
