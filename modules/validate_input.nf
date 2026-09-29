process VALIDATE_INPUT {
    tag "$id"
    input:
    tuple val(id), path(pdb)
    output:
    tuple val(id), path('input.pdb')
    script:
    """
    python - "${pdb}" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
lines = p.read_text().splitlines()
assert any(line.startswith('ATOM  ') for line in lines), 'PDB contains no protein ATOM records'
assert not any(line.startswith('MODEL ') for line in lines), 'Select a single PDB model first'
assert not any(line.startswith('HETATM') for line in lines), 'Remove waters, ligands and other HETATM records first'
assert len({line[21] for line in lines if line.startswith('ATOM  ')}) == 1, 'This example supports one chain only'
PY
    cp "${pdb}" input.pdb
    """
}
