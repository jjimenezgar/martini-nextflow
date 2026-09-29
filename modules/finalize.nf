process FINALIZE {
    tag "$id"
    publishDir { "${params.outdir}/${id}" }, mode: 'copy', saveAs: { filename -> filename.toString().tokenize('/').last() }
    input:
    tuple val(id), path(cg), path(proteinTop), path(itps)
    tuple val(id2), path(system), path(insaneTop)
    path ffArchive
    path finalizer
    path mdp
    output:
    path('final/*')
    script:
    """
    test '${id}' = '${id2}'
    python "${finalizer}" --cg "${cg}" --protein-top "${proteinTop}" \\
      --insane-top "${insaneTop}" --system "${system}" \\
      --ff-archive "${ffArchive}" --mdp "${mdp}" --out final
    """
}
