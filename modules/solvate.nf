process SOLVATE {
    tag "$id"
    input:
    tuple val(id), path(boxed)
    val salt
    output:
    tuple val(id), path('system.gro'), path('insane.top')
    script:
    """
    dims=\$(tail -n 1 "${boxed}" | awk '{printf "%s,%s,%s", \$1, \$2, \$3}')
    insane -f "${boxed}" -o system.gro -p insane.top -pbc cubic -box "\$dims" -sol W -salt ${salt} -d 0
    test -s system.gro
    """
}
