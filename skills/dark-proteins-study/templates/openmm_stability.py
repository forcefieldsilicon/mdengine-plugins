#!/usr/bin/env python3
# Stage 1 of the dark-proteins study: one stability replica of a predicted protein model in water and salt.
#
# The MDEngine openmm runner executes this as `python3 stability.py` inside the job directory, next to the
# files you submitted (at least model.pdb). Everything it writes there comes back in the results tarball:
#   traj.dcd        trajectory of the production run (no waters stripped)
#   state.csv       step, time, temperature, energies, box volume, speed
#   checkpoint.chk  restart point, rewritten every 1 ns
#   residues.csv    per residue: backbone RMSF, fraction of native contacts kept, pLDDT
#   summary.json    sizes, steps, mean temperature, box, platform, low-confidence residues
#   work.json       the work record the service bills from (schema mde.work/1)
# The last line printed is DONE. Submit with end_marker "DONE".
#
# Edit the constants below, or put a params.json beside this script; its keys override them.

import json, os, sys, time

PDB_FILE = "model.pdb"     # the predicted model; pLDDT is read from the B-factor column when present
NANOSECONDS = 100.0        # production length (NPT)
SEED = 1                   # one seed per replica
TEMPERATURE_K = 300.0
SALT_MOLAR = 0.15          # NaCl, on top of the neutralizing ions
PADDING_NM = 1.0           # water between the protein and the box edge
TIMESTEP_FS = 2.0
REPORT_PS = 100.0          # trajectory frame interval
STATE_PS = 10.0            # state.csv interval
EQUIL_PS = 100.0           # NVT equilibration before production
PLDDT_CUTOFF = 50.0        # residues below it are reported, not removed

if os.path.exists("params.json"):
    with open("params.json") as fh:
        for k, v in json.load(fh).items():
            if k in globals() and k.isupper(): globals()[k] = v
            else: print("params.json: unknown key %r ignored" % k)

import numpy as np
import openmm as mm
from openmm import app, unit

T0 = time.time()
DT_PS = TIMESTEP_FS / 1000.0
NVT_STEPS = int(round(EQUIL_PS / DT_PS))              # equilibration at constant volume
PROD_STEPS = int(round(NANOSECONDS * 1000.0 / DT_PS))
# Frames for the trajectory and the analysis. A short pilot still gets about 10 frames.
FRAME_STEPS = max(1, min(int(round(REPORT_PS / DT_PS)), PROD_STEPS // 10 or 1))
STATE_STEPS = max(1, int(round(STATE_PS / DT_PS)))
CHECKPOINT_STEPS = int(round(1000.0 / DT_PS))         # every 1 ns


def first_model_lines(path):
    """The PDB lines up to the first ENDMDL, so a multi-model file is read as its first model."""
    out = []
    with open(path) as fh:
        for line in fh:
            if line.startswith("ENDMDL"): break
            out.append(line)
    return out


def plddt_by_residue(lines):
    """(chain, resSeq+iCode) -> B-factor of the CA atom, or {} when the column is empty."""
    out = {}
    for ln in lines:
        if ln.startswith(("ATOM", "HETATM")) and ln[12:16].strip() == "CA" and len(ln) >= 66:
            try: out[(ln[21].strip(), ln[22:27].strip())] = float(ln[60:66])
            except ValueError: pass
    return out


# 1. Read the model (first model only), keep the protein, rebuild hydrogens at pH 7.
lines = first_model_lines(PDB_FILE)
with open("_model_first.pdb", "w") as fh: fh.writelines(lines + ["END\n"])
pdb = app.PDBFile("_model_first.pdb")
plddt = plddt_by_residue(lines)
if plddt and max(plddt.values()) <= 0.0: plddt = {}
modeller = app.Modeller(pdb.topology, pdb.positions)
modeller.deleteWater()
modeller.delete([a for a in modeller.topology.atoms() if a.element is not None and a.element.symbol == "H"])
forcefield = app.ForceField("amber14-all.xml", "amber14/tip3p.xml")
modeller.addHydrogens(forcefield, pH=7.0)
protein_residues = list(modeller.topology.residues())  # before solvent is appended
n_protein_atoms = modeller.topology.getNumAtoms()

# 2. Solvate: TIP3P water with PADDING_NM of padding, neutralized, plus NaCl at SALT_MOLAR.
modeller.addSolvent(forcefield, model="tip3p", padding=PADDING_NM * unit.nanometer,
                    ionicStrength=SALT_MOLAR * unit.molar, positiveIon="Na+", negativeIon="Cl-")
system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.PME,
                                 nonbondedCutoff=1.0 * unit.nanometer, constraints=app.HBonds)
n_atoms = system.getNumParticles()
print("system: %d atoms, %d protein residues, %d protein atoms" % (n_atoms, len(protein_residues), n_protein_atoms), flush=True)


def make_simulation(platform_name):
    integ = mm.LangevinMiddleIntegrator(TEMPERATURE_K * unit.kelvin, 1.0 / unit.picosecond, DT_PS * unit.picoseconds)
    integ.setRandomNumberSeed(int(SEED))
    plat = mm.Platform.getPlatformByName(platform_name)
    props = {"Precision": "mixed"} if platform_name == "CUDA" else {}
    sim = app.Simulation(modeller.topology, system, integ, plat, props)
    sim.context.setPositions(modeller.positions)
    return sim


# 3. CUDA in mixed precision; CPU only as a fallback, with a warning (CPU is far slower).
try:
    sim = make_simulation("CUDA")
except Exception as e:  # no CUDA device or plugin
    print("WARNING: CUDA platform unavailable (%s); falling back to CPU, which is much slower" % str(e).splitlines()[0], flush=True)
    sim = make_simulation("CPU")
platform = sim.context.getPlatform().getName()
print("platform: %s" % platform, flush=True)

# 4. Minimize, then EQUIL_PS of NVT.
sim.minimizeEnergy()
sim.context.setVelocitiesToTemperature(TEMPERATURE_K * unit.kelvin, int(SEED))
sim.step(NVT_STEPS)

# 5. NPT production with a Monte Carlo barostat at 1 bar.
baro = mm.MonteCarloBarostat(1.0 * unit.bar, TEMPERATURE_K * unit.kelvin)
baro.setRandomNumberSeed(int(SEED))
system.addForce(baro)
sim.context.reinitialize(preserveState=True)
sim.currentStep = 0
sim.reporters.append(app.DCDReporter("traj.dcd", FRAME_STEPS))
sim.reporters.append(app.StateDataReporter("state.csv", STATE_STEPS, step=True, time=True, temperature=True,
                                           potentialEnergy=True, totalEnergy=True, volume=True, speed=True))
sim.reporters.append(app.StateDataReporter(sys.stdout, max(STATE_STEPS, PROD_STEPS // 20 or 1), step=True,
                                           temperature=True, speed=True, progress=True, remainingTime=True,
                                           totalSteps=PROD_STEPS))
sim.reporters.append(app.CheckpointReporter("checkpoint.chk", CHECKPOINT_STEPS))

# Backbone (N, CA, C) indices per protein residue, for RMSF; CA indices for contacts.
bb_res, bb_idx, ca_idx = [], [], []
for ri, res in enumerate(protein_residues):
    for a in res.atoms():
        if a.name in ("N", "CA", "C"): bb_res.append(ri); bb_idx.append(a.index)
        if a.name == "CA": ca_idx.append((ri, a.index))
bb_res = np.array(bb_res); bb_idx = np.array(bb_idx)
start = np.array(modeller.positions.value_in_unit(unit.nanometer))   # the starting model, before minimization

frames, done, T_PROD = [], 0, time.time()
while done < PROD_STEPS:
    n = min(FRAME_STEPS, PROD_STEPS - done)
    sim.step(n); done += n
    st = sim.context.getState(getPositions=True)
    frames.append(np.array(st.getPositions(asNumpy=True).value_in_unit(unit.nanometer))[bb_idx])
sim.saveCheckpoint("checkpoint.chk")
wall_s = time.time() - T0
prod_s = time.time() - T_PROD


# 6. Analysis: backbone RMSF after superposition on the mean structure.
def kabsch(P, Q):
    """Rotate and translate P onto Q (both n x 3); returns the moved P."""
    pc, qc = P.mean(0), Q.mean(0)
    U, _, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1.0, 1.0, d]) @ Vt
    return (P - pc) @ R + qc


X = np.array(frames)
ref = X[0]
for _ in range(2):  # align to the first frame, then twice to the running mean
    X = np.array([kabsch(f, ref) for f in X]); ref = X.mean(0)
atom_rmsf = np.sqrt(((X - ref) ** 2).sum(-1).mean(0))
res_rmsf = {ri: float(atom_rmsf[bb_res == ri].mean()) for ri in set(bb_res.tolist())}

# Native contacts: CA pairs within 0.8 nm in the starting model with |i-j| > 3. A contact counts as kept in
# a frame when its distance is within 1.2 x the native distance. Per residue: mean over its contacts and frames.
ca_start = start[[i for _, i in ca_idx]]
pairs = [(a, b, float(np.linalg.norm(ca_start[a] - ca_start[b])))
         for a in range(len(ca_idx)) for b in range(a + 1, len(ca_idx))
         if abs(ca_idx[a][0] - ca_idx[b][0]) > 3 and np.linalg.norm(ca_start[a] - ca_start[b]) < 0.8]
ca_in_bb = [int(np.where(bb_idx == i)[0][0]) for _, i in ca_idx]
kept = {}
for a, b, d0 in pairs:
    d = np.linalg.norm(X[:, ca_in_bb[a]] - X[:, ca_in_bb[b]], axis=-1)
    f = float((d <= 1.2 * d0).mean())
    for r in (ca_idx[a][0], ca_idx[b][0]): kept.setdefault(r, []).append(f)

low = []
with open("residues.csv", "w") as fh:
    fh.write("index,chain,resid,resname,plddt,backbone_rmsf_nm,native_contacts,q_native\n")
    for ri, res in enumerate(protein_residues):
        p = plddt.get((res.chain.id, str(res.id) + (res.insertionCode or "").strip()))
        if p is not None and p < PLDDT_CUTOFF: low.append("%s%s" % (res.name, res.id))
        q = kept.get(ri)
        fh.write("%d,%s,%s,%s,%s,%s,%d,%s\n" % (ri, res.chain.id, res.id, res.name, "" if p is None else "%.2f" % p,
                 "%.4f" % res_rmsf[ri] if ri in res_rmsf else "", len(q or []), "%.3f" % (sum(q) / len(q)) if q else ""))

# Mean temperature from state.csv.
mean_t = None
with open("state.csv") as fh:
    head = fh.readline().strip().lstrip("#").replace('"', "").split(",")
    col = next((i for i, h in enumerate(head) if h.startswith("Temperature")), None)
    vals = [float(r.split(",")[col]) for r in fh if r.strip()] if col is not None else []
    if vals: mean_t = sum(vals) / len(vals)

box = sim.context.getState().getPeriodicBoxVectors(asNumpy=True).value_in_unit(unit.nanometer)
steps = NVT_STEPS + PROD_STEPS
summary = {
    "atoms": n_atoms, "protein_atoms": n_protein_atoms, "residues": len(protein_residues),
    "steps": steps, "production_steps": PROD_STEPS, "equilibration_steps": NVT_STEPS,
    "ns": PROD_STEPS * DT_PS / 1000.0, "timestep_fs": TIMESTEP_FS, "seed": SEED,
    "temperature_k": TEMPERATURE_K, "mean_temperature_k": mean_t, "salt_molar": SALT_MOLAR,
    "box_nm": [round(float(box[i][i]), 4) for i in range(3)], "platform": platform,
    "frames": len(frames), "wall_s": round(wall_s, 1),
    "production_ns_per_day": round(PROD_STEPS * DT_PS / 1000.0 / prod_s * 86400.0, 2) if prod_s > 0 else None,
    "plddt_present": bool(plddt), "plddt_cutoff": PLDDT_CUTOFF, "residues_below_plddt_cutoff": low,
    "native_contacts": len(pairs),
    "pocket": "not measured by this template; name the pocket residues and measure them from traj.dcd",
}
with open("summary.json", "w") as fh: json.dump(summary, fh, indent=2)

# The billing record: particles x steps of integration actually run (minimization is not counted).
work = {"schema": "mde.work/1", "runner": "openmm", "protocol": "stability", "particles": n_atoms,
        "steps": steps, "platform": platform, "wall_s": round(wall_s, 1), "dry_run": False}
with open("work.json", "w") as fh: json.dump(work, fh)
os.remove("_model_first.pdb")
print("residues.csv, summary.json, work.json written; %.1f s wall" % wall_s)
print("DONE", flush=True)
