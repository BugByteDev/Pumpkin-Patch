"""Pumpkin Patch native Python entry point, including frozen worker startup."""
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    import sys
    if '--smoke-test' in sys.argv:
        import json,traceback
        from pathlib import Path
        output=Path(sys.argv[sys.argv.index('--smoke-test')+1]);output.mkdir(parents=True,exist_ok=True)
        log=(output/'runtime.log').open('w',encoding='utf-8')
        if sys.stdout is None:sys.stdout=log
        if sys.stderr is None:sys.stderr=log
        try:
            from smoke import run
            code=run(output)
        except Exception:
            (output/'smoke.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()},indent=2))
            code=1
        sys.exit(code)
    from native import run
    run()
