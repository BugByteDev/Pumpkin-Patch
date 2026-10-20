"""Launch a compiled app from outside its source tree, with a hard timeout."""
import argparse,json,os,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--executable',required=True);p.add_argument('--report-dir',required=True);p.add_argument('--opengl-dir');args=p.parse_args()
exe=Path(args.executable).resolve();report=Path(args.report_dir).resolve();report.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.pop('QT_QPA_PLATFORM',None);env['PYTHONNOUSERSITE']='1'
if args.opengl_dir:
    driver=Path(args.opengl_dir).resolve();env['PUMPKIN_CI_OPENGL_DIR']=str(driver);env['QT_OPENGL_DLL']=str(driver/'opengl32.dll');env['GALLIUM_DRIVER']='llvmpipe';env['QT_OPENGL']='desktop'
with tempfile.TemporaryDirectory(prefix='pumpkin-launch-',ignore_cleanup_errors=True) as cwd:
    process=subprocess.Popen([str(exe),'--smoke-test',str(report)],cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:stdout,stderr=process.communicate(timeout=420)
    except subprocess.TimeoutExpired:
        if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
        else:process.kill()
        stdout,stderr=process.communicate(timeout=15)
        stderr+='\nCompiled app timed out.'
(report/'launch.log').write_text(stdout+'\n'+stderr,encoding='utf-8')
if process.returncode:raise SystemExit('Compiled app failed: '+str(process.returncode)+'; see '+str(report))
result=json.loads((report/'smoke.json').read_text());assert result['ok'] and result['frozen'],result
print(json.dumps(result,indent=2))
