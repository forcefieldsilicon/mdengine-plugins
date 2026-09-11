---
name: results
description: >-
  Turn a finished MD run into numbers and pictures. Use it when asked to analyze
  a trajectory or a dump file, measure crystallinity, grain size, diffusion,
  RDF, stress or strain, count contacts or hydrogen bonds, profile a deposited
  layer, render a frame or a movie of a simulation, export a frame, shrink a
  trajectory that is too big, or fetch the results of a hosted GPU job.
user-invocable: true
compatibility: macOS (local tools), any OS (hosted MCP)
metadata:
  author: ForceField Silicon (Gitinama Inc.)
  version: "0.1.0"
license: Apache-2.0
---

# Reading a finished run

## Get the files first

A hosted job's outputs live on the server until they are fetched.

```sh
mdengine jobs                 # hosted jobs, newest first
mdengine job <id>             # status
mdengine job <id> --log       # thermo tail
mdengine job <id> --fetch     # download the run directory
```

From MCP: `job_status`, then `job_results` on the hosted server, or `fetch_job` for a
job submitted through the local server to a remote host or to the cloud. `fetch_job`
is safe to call while the job is still running, because a dump file that is still
being written parses to its complete frames.

Trajectories are read whole into memory. A file over 2 GB is refused, and the fix is
`decimate` or splitting it. Decimating first also makes every later call faster.

## Then look at it

Always start here. It costs nothing and it catches a run that failed quietly.

```
trajectory_info(path)
```

Frames, atoms per frame, per-atom fields, the element histogram of the last frame,
the bounding box, the charge range. Fewer frames than the dump cadence implies means
the run stopped early. An element histogram that does not match the deck means the
type-to-element mapping is wrong, and every later number will be wrong with it.

## Then measure it

`analyze` runs the registered analysis tools, the same ones the app's inspector runs.
**Call it with no `tool` first** to get the live catalogue: each tool's id, what it
produces, what it requires, and its default parameters. From the CLI that is
`mdengine analyze` with no arguments.

| Tool id | Answers |
| --- | --- |
| `z_profile` | Where the deposited species went. Locates the substrate surface plane, then reports penetration depth, at-surface and in-flight counts, bound charge, and a z histogram |
| `crystallinity` | How ordered the structure is, by common neighbour analysis or a bond-order parameter |
| `ptm` | Polyhedral template matching: which atoms are fcc, hcp, bcc or icosahedral |
| `grains` | Grain segmentation, grain sizes, and grain-boundary misorientation |
| `rdf` | Radial distribution function. Structure, coordination, phase |
| `deformation` | Shear strain, non-affine displacement, stress profiles along an axis |
| `diffusion` | Mean squared displacement and a diffusion coefficient from its fitted slope |
| `thermo` | Temperature, energy and pressure from the log, plus stress-strain and an elastic modulus |
| `conformation` | RMSF, PCA and clustering for a biomolecule |
| `adhesion` | Contacts, hydrogen bonds, salt bridges, per residue and over time |
| `column_field` | Colour and profile the atoms by any per-atom column in the dump |

Add `frames` to turn a single-frame measurement into a time series. Add `params` to
override the defaults the catalogue printed. Ask for `include_field` only when the
per-atom values themselves are needed, because it is one number per atom.

```sh
mdengine analyze                          # the catalogue
mdengine analyze ptm dump.lammpstrj
mdengine analyze rdf dump.lammpstrj --param rMax=12 --param bins=300
mdengine analyze thermo log.lammps --all --csv thermo.csv
```

## Then show it

`render_image` puts one frame on the screen as a PNG, which is how an agent actually
sees what the run did. `render_video` does the whole trajectory as an MP4 or a GIF.
Both use the same camera arguments.

| Argument | Note |
| --- | --- |
| `pitch_deg` | 0 is the top view for z-up data. `-90` is the front view, which is the one you want for a slab |
| `yaw_deg` | Rotate around the vertical |
| `distance` | Default 2.8. Smaller is closer |
| `orbit_dps` | Video only. Degrees of yaw per second, for a turntable shot |
| `stride` | Render every Nth frame. Default targets about 15 seconds |
| `elements` | Map numeric type tokens to elements by position, for example `O,Al` |
| `style: "contrast"` | Enlarges and recolours the minority species so it is visible against the substrate |
| `overlay` | Image only. An analysis tool id whose per-atom field colours the atoms, with a baked legend |
| `annotations` | Scale bar and frame counter, on by default |

Rendering is synchronous and a long trajectory at high resolution takes minutes.
Decimate first.

`export_frame` writes one frame as XYZ, with `charges: true` for extended-XYZ
carrying the per-atom q column. `decimate` keeps every Nth frame and always keeps the
last one.

## A slab and gas run, end to end

```
trajectory_info(path: "dump.lammpstrj")
analyze(path: "dump.lammpstrj")                      # catalogue
analyze(path: "dump.lammpstrj", tool: "z_profile")   # where the gas ended up
analyze(path: "dump.lammpstrj", tool: "z_profile", frames: "all")   # over time
render_image(path: "dump.lammpstrj", out: "final.png",
             pitch_deg: -90, style: "contrast", elements: "O,Al")
render_video(path: "dump.lammpstrj", out: "run.mp4", pitch_deg: -90, stride: 5)
```

Read the depth profile against the substrate's own top plane, not against the box.
A surface plane that drops over the run is the substrate collapsing, and that is a
failed run rather than a result.

## A metal melt or a deformation run, end to end

```
trajectory_info(path: "melt.lammpstrj")
analyze(path: "melt.lammpstrj", tool: "thermo")        # did T and P do what the deck asked
analyze(path: "melt.lammpstrj", tool: "ptm", frames: "all")   # fcc fraction against time
analyze(path: "melt.lammpstrj", tool: "rdf")           # first peak sharp = still solid
analyze(path: "melt.lammpstrj", tool: "diffusion")     # non-zero D = melted
render_video(path: "melt.lammpstrj", out: "melt.mp4", orbit_dps: 20)
```

For a bicrystal or a polycrystal, `grains` after `ptm`. For a pull or a shear,
`deformation` with `reference_frame` set to the frame before the load starts.

## Reporting a result

Say what was measured, on which frames, with which parameters, and say what the run
gave up. A truncated model, a short equilibration, one seed instead of three, a
timestep chosen for speed: those belong next to the number, not in a footnote. A
number without them is not reusable.
