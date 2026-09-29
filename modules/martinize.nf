process MARTINIZE {
    tag "$id"
    input:
    tuple val(id), path(pdb)
    output:
    tuple val(id), path('protein_cg.pdb'), path('protein_only.top'), path('*.itp')
    script:
    """
    martinize2 -f "${pdb}" -x protein_cg.pdb -o protein_only.top -ff martini3001 -dssp -elastic
    test -s protein_cg.pdb
    test -s protein_only.top
    test -n "\$(find . -maxdepth 1 -name 'molecule_*.itp' -print -quit)"
    """
}
