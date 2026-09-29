import subprocess
import tempfile
import unittest
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class FinalizerTest(unittest.TestCase):
    def test_ion_names_and_counts(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / 'protein_cg.pdb').write_text('ATOM      1  BB  ALA A   1       0.000   0.000   0.000\nEND\n')
            (p / 'protein_only.top').write_text('[ molecules ]\nmolecule_0 1\n')
            (p / 'molecule_0.itp').write_text('[ moleculetype ]\nmolecule_0 1\n[ atoms ]\n1 P5 1 ALA BB 1 0\n')
            (p / 'insane.top').write_text('[ molecules ]\nProtein 1\nW 2\nNA+ 1\nCL- 1\n')
            with zipfile.ZipFile(p / 'martini_v300.zip', 'w') as archive:
                for name in ('martini_v3.0.0.itp', 'martini_v3.0.0_solvents_v1.itp',
                             'martini_v3.0.0_ions_v1.itp'):
                    archive.writestr('martini_v300/' + name, '; test fixture\n')
            atoms = [f'{i:5d}{res:<5s}{res:>5s}{i:5d}{0.1*i:8.3f}{0.0:8.3f}{0.0:8.3f}'
                     for i, res in enumerate(('ALA', 'W', 'W', 'NA+', 'CL-'), 1)]
            (p / 'system.gro').write_text('system\n    5\n' + '\n'.join(atoms) + '\n  3.000  3.000  3.000\n')
            command = ['python', str(ROOT / 'scripts/finalize.py'), '--cg', 'protein_cg.pdb',
                       '--protein-top', 'protein_only.top', '--insane-top', 'insane.top',
                       '--system', 'system.gro', '--ff-archive', 'martini_v300.zip',
                       '--mdp', str(ROOT / 'assets/em.mdp'), '--out', 'final']
            subprocess.run(command, cwd=p, check=True)
            top = (p / 'final/system.top').read_text()
            self.assertIn('NA               1', top)
            self.assertIn('CL               1', top)
            self.assertNotIn('NA+', (p / 'final/system.gro').read_text())
            (p / 'system.gro').write_text('system\n    4\n' + '\n'.join(atoms[:4]) + '\n  3.000  3.000  3.000\n')
            with self.assertRaises(subprocess.CalledProcessError):
                subprocess.run(command, cwd=p, check=True, capture_output=True)
