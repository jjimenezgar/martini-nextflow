nextflow.enable.dsl = 2

include { VALIDATE_INPUT } from './modules/validate_input'
include { MARTINIZE } from './modules/martinize'
include { DEFINE_BOX } from './modules/define_box'
include { SOLVATE } from './modules/solvate'
include { FINALIZE } from './modules/finalize'
include { FETCH_FORCEFIELD } from './modules/fetch_forcefield'

workflow {
    if (!params.pdb) error 'Provide --pdb (for example, --pdb examples/1ubq.pdb)'
    def inputPdb = file(params.pdb)
    if (!inputPdb.exists() || !inputPdb.isFile()) error "PDB does not exist: ${params.pdb}"
    if (!params.salt.toString().isNumber()) error '--salt must be numeric'
    if (!params.box_distance.toString().isNumber()) error '--box_distance must be numeric'
    def salt = params.salt.toString().toDouble()
    def boxDistance = params.box_distance.toString().toDouble()
    if (salt < 0 || salt > 2) error '--salt must be between 0 and 2 M'
    if (boxDistance <= 0) error '--box_distance must be positive (nm)'
    def sample = inputPdb.baseName.replaceAll(/[^A-Za-z0-9_-]/, '_')
    def checked = VALIDATE_INPUT(tuple(sample, inputPdb))
    def martinized = MARTINIZE(checked)
    def boxed = DEFINE_BOX(martinized.map { id, pdb, _top, _itps -> tuple(id, pdb) }, boxDistance)
    def solvated = SOLVATE(boxed, salt)
    def forcefield
    if (params.ff_archive) {
        def archive = file(params.ff_archive)
        if (!archive.exists() || !archive.isFile()) error "Force-field archive does not exist: ${params.ff_archive}"
        forcefield = channel.value(archive)
    } else {
        forcefield = FETCH_FORCEFIELD(file("${projectDir}/scripts/fetch_forcefield.py"))
    }
    FINALIZE(martinized, solvated, forcefield, file("${projectDir}/scripts/finalize.py"), file("${projectDir}/assets/em.mdp"))
}
