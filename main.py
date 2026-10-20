"""Pumpkin Patch native Python entry point, including frozen worker startup."""
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import sys
    if '--smoke-test' in sys.argv:
        from smoke import run
        sys.exit(run(sys.argv[sys.argv.index('--smoke-test')+1]))
    from native import run
    run()
