# martini-nextflow

[![CI](https://github.com/jjimenezgar/martini-nextflow/actions/workflows/ci.yml/badge.svg)](https://github.com/jjimenezgar/martini-nextflow/actions/workflows/ci.yml)

A small Nextflow DSL2 workflow that prepares a **single protein** for Martini 3 coarse-grained simulation:

**PDB → martinize2 → CG protein → GROMACS box → INSANE water/NaCl → GROMACS inputs**

This project extracts a small, self-contained protein-preparation workflow inspired by [MartiniSurf](https://github.com/jjimenezgar/MartiniSurf) and reimplements the orchestration layer using Nextflow DSL2. It contains no surface, immobilization, linker, production MD, or Streamlit code.

## Quick start

Requirements: Java 17+, [Nextflow](https://www.nextflow.io/docs/latest/install.html) 24.10+, and Conda or Mamba. Tested tool versions are in `environment.yml` (vermouth/martinize2 0.15.0, mdtraj 1.11.1, GROMACS 2025.3, INSANE 1.2.0). Linux x86_64 is the primary target.

```bash
nextflow run main.nf -profile conda \
  --pdb examples/1ubq.pdb \
  --salt 0.15 \
  --box_distance 1.2
```

`--salt` is molar NaCl concentration (zero still neutralizes); `--box_distance` is the minimum protein-to-box-edge distance in nm passed to `gmx editconf`. The example is a protein-only, single-chain PDB prepared from [RCSB 1UBQ](https://www.rcsb.org/structure/1UBQ). Supply a clean single-chain PDB with complete protein heavy atoms; the workflow deliberately rejects HETATM records and multiple models/chains instead of silently repairing them.

The first run downloads the official Martini 3 parameter archive and verifies its SHA-256 digest. On a cluster without internet on compute nodes, download the archive on a login node and pass `--ff_archive /path/to/martini_v300.zip`. Nextflow will stage the local file.

Run again with `-resume` to reuse cached process results. Add a site-specific config (`-c cluster.config`) and set `process.executor = 'slurm'` or another Nextflow executor for HPC. Use a shared work directory and Conda cache accessible to compute nodes. Nextflow separates workflow orchestration from external scientific tools, tracks each process, caches results, and can move the same modules between workstation and cluster executors. This small example is sequential because each preparation stage depends on the previous stage; independent samples could run in parallel in a later extension.

## Outputs

```text
results/1ubq/
  protein_cg.pdb
  system.gro
  system.top
  molecule_0.itp
  martini_v3.0.0.itp
  martini_v3.0.0_solvents_v1.itp
  martini_v3.0.0_ions_v1.itp
  em.mdp
  README.txt
results/pipeline_trace.txt
```

`system.gro` is an **unminimized** initial structure. `em.mdp` is a starting minimization parameter file, not an executed simulation. Inspect the structure/topology before running molecular dynamics. To check GROMACS preprocessing without running MD:

```bash
cd results/1ubq
gmx grompp -f em.mdp -c system.gro -p system.top -o em.tpr
```

The finalizer checks molecule names and atom counts and translates INSANE's `NA+`/`CL-` labels to the `NA`/`CL` molecule types defined by Martini 3. INSANE supplies the water and counterions; the pipeline assembles its molecule counts with the protein topology from martinize2.

## Workflow design

| Process | Input | Output |
| --- | --- | --- |
| `VALIDATE_INPUT` | Atomistic PDB | Checked PDB |
| `MARTINIZE` | Checked PDB | `protein_cg.pdb`, `protein_only.top`, protein `.itp` |
| `DEFINE_BOX` | CG PDB, distance | Centered cubic protein box (`.gro`) |
| `SOLVATE` | Box, salt | Solvated/ionized `.gro`, INSANE molecule list |
| `FETCH_FORCEFIELD` | Pinned official URL (unless `--ff_archive` is supplied) | SHA-256-verified archive |
| `FINALIZE` | Both topology branches, official force-field archive | Self-contained GROMACS inputs |

The archive is the original Martini 3 parameter download from the [Martini Force Field Initiative](https://cgmartini.nl/docs/downloads/force-field-parameters/martini3/particle-definitions.html), SHA-256 `204d83592ab46f0fd98358d98fc47dfabf3a0cc031bc422dcfe2929a56d1ccf2`. Only the three required `.itp` files are extracted per run. These third-party scientific parameters and the PDB example retain their own provenance and are not covered by this repository's MIT software license. Please cite the relevant Martini 3, martinize2 and INSANE work when using the outputs for research.

## Tests and limits

```bash
nextflow lint .
python -m unittest discover -s tests -v
nextflow run main.nf --pdb examples/1ubq.pdb -preview
nextflow run main.nf -profile conda --pdb examples/1ubq.pdb --salt 0.15
```

CI runs lint, parameter checks, a finalization unit test and the full 1UBQ smoke test including `gmx grompp`. No minimization/equilibration runs. The workflow uses martinize2's DSSP assignment through MDTraj and a default elastic network. Single-chain clean proteins are the supported scope; protonation, alternate locations, unresolved atoms, special residues and biological assembly choices require preparation outside this example.

For Apptainer on an HPC cluster, build or supply a container from the documented Conda environment and configure `process.container` in your cluster config. No unverified public image is claimed here. A Docker profile is omitted until a maintained, tested image is available.
