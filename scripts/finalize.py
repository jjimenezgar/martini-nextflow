#!/usr/bin/env python3
"""Assemble Martini 3 includes and verify INSANE coordinates against molecule counts."""
import argparse
from pathlib import Path
import re
import shutil
import zipfile

FF = ('martini_v3.0.0.itp', 'martini_v3.0.0_solvents_v1.itp', 'martini_v3.0.0_ions_v1.itp')


def section(text, name):
    match = re.search(r'^\s*\[\s*' + re.escape(name) + r'\s*\]\s*$', text, re.I | re.M)
    if not match:
        raise ValueError(f'Missing [{name}] section')
    return re.split(r'^\s*\[', text[match.end():], maxsplit=1, flags=re.M)[0]


def entries(text, name):
    return [line.split(';', 1)[0].split() for line in section(text, name).splitlines()
            if line.strip() and not line.lstrip().startswith((';', '#'))]


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.ff_archive) as archive:
        for basename in FF:
            member = f'martini_v300/{basename}'
            with archive.open(member) as source, (out / basename).open('wb') as dest:
                shutil.copyfileobj(source, dest)

    protein_top = Path(args.protein_top).read_text()
    protein_molecules = entries(protein_top, 'molecules')
    if len(protein_molecules) != 1 or int(protein_molecules[0][1]) != 1:
        raise ValueError('Expected one protein molecule in martinize2 topology')
    molecule_name = protein_molecules[0][0]
    itps = sorted(Path('.').glob('*.itp'))
    if not itps:
        raise ValueError('martinize2 produced no protein ITP')
    molecule_types = {row[0] for itp in itps for row in entries(itp.read_text(), 'moleculetype')[:1]}
    if molecule_name not in molecule_types:
        raise ValueError(f'No protein ITP defines {molecule_name}')
    for itp in itps:
        shutil.copy2(itp, out / itp.name)

    lines = Path(args.insane_top).read_text().splitlines()
    counts = []
    in_molecules = False
    for line in lines:
        if re.match(r'^\s*\[\s*molecules\s*\]', line, re.I):
            in_molecules = True
            continue
        if in_molecules and re.match(r'^\s*\[', line):
            break
        if in_molecules:
            row = line.split(';', 1)[0].split()
            if row:
                counts.append((row[0].removesuffix('+').removesuffix('-'), int(row[1])))
    if not counts or counts[0][1] != 1:
        raise ValueError('INSANE topology lacks a single protein entry')
    counts[0] = (molecule_name, 1)
    if not any(name == 'W' for name, _ in counts):
        raise ValueError('No Martini water in INSANE topology')
    if any(name not in {molecule_name, 'W', 'NA', 'CL'} for name, _ in counts):
        raise ValueError(f'Unexpected molecule names: {counts}')

    gro = Path(args.system).read_text().splitlines()
    n_atoms = int(gro[1].strip())
    if len(gro) != n_atoms + 3:
        raise ValueError('GRO atom count disagrees with file length')
    protein_itp = next(itp for itp in itps
                       if entries(itp.read_text(), 'moleculetype')[0][0] == molecule_name)
    protein_atoms = len(entries(protein_itp.read_text(), 'atoms'))
    expected_atoms = protein_atoms + sum(count for name, count in counts if name != molecule_name)
    if n_atoms != expected_atoms:
        raise ValueError(f'Coordinate/topology atom mismatch: {n_atoms} != {expected_atoms}')
    fixed = []
    for line in gro[2:-1]:
        if line[5:10].strip() in {'NA+', 'CL-'}:
            line = line[:5] + line[5:15].replace('+', ' ').replace('-', ' ') + line[15:]
        fixed.append(line)
    if len(fixed) != n_atoms:
        raise ValueError('GRO coordinate count mismatch')
    (out / 'system.gro').write_text('\n'.join(gro[:2] + fixed + gro[-1:]) + '\n')
    shutil.copy2(args.cg, out / 'protein_cg.pdb')
    topology = ['; Generated from martinize2 and INSANE; Martini 3 original release',
                '#include "martini_v3.0.0.itp"',
                '#include "martini_v3.0.0_solvents_v1.itp"',
                '#include "martini_v3.0.0_ions_v1.itp"']
    topology += [f'#include "{itp.name}"' for itp in itps]
    topology += ['', '[ system ]', 'Martini 3 solvated protein', '', '[ molecules ]']
    topology += [f'{name:<16} {count}' for name, count in counts]
    (out / 'system.top').write_text('\n'.join(topology) + '\n')
    shutil.copy2(args.mdp, out / 'em.mdp')
    (out / 'README.txt').write_text('Initial, unminimized configuration. Inspect and minimize before equilibration.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('cg', 'protein_top', 'insane_top', 'system', 'ff_archive', 'out', 'mdp'):
        parser.add_argument('--' + key.replace('_', '-'), required=True)
    run(parser.parse_args())
