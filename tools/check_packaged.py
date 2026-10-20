"""Launch a compiled app from outside its source tree, with a hard timeout."""
import argparse,json,os,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--executable',required=True);p.add_argument('--report-dir',required=True);p.add_argument('--opengl-dir');args=p.parse_args()
exe=Path(args.executable).resolve();report=Path(args.report_dir).resolve();report.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env.pop('QT_QPA_PLATFORM',None);env['PYTHONNOUSERSITE']='1'
if args.opengl_dir:
    driver=Path(args.opengl_dir).resolve();env['PUMPKIN_CI_OPENGL_DIR']=str(driver);env['QT_OPENGL_DLL']=str(driver/'opengl32.dll');env['GALLIUM_DRIVER']='llvmpipe'
with tempfile.TemporaryDirectory(prefix='pumpkin-launch-') as cwd:
    completed=subprocess.run([str(exe),'--smoke-test',str(report)],cwd=cwd,env=env,capture_output=True,text=True,timeout=180)
(report/'launch.log').write_text(completed.stdout+'\n'+completed.stderr,encoding='utf-8')
if completed.returncode:raise SystemExit('Compiled app failed: '+str(completed.returncode)+'; see '+str(report))
result=json.loads((report/'smoke.json').read_text());assert result['ok'] and result['frozen'],result
print(json.dumps(result,indent=2))
