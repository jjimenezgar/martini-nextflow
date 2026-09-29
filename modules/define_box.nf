process DEFINE_BOX {
    tag "$id"
    input:
    tuple val(id), path(pdb)
    val distance
    output:
    tuple val(id), path('protein_box.gro')
    script:
    """
    gmx editconf -f "${pdb}" -o protein_box.gro -c -d ${distance} -bt cubic
    """
}
