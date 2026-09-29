process FETCH_FORCEFIELD {
    input:
    path fetcher
    output:
    path('martini_v300.zip')
    script:
    """
    python "${fetcher}" martini_v300.zip
    """
}
