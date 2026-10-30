"""Exercise only this installer/app in a disposable Windows CI user profile."""
import argparse,json,os,subprocess,time,traceback,winreg
from pathlib import Path
from pywinauto import Desktop
import win32com.client

p=argparse.ArgumentParser();p.add_argument('--opengl-dir',required=True);args=p.parse_args()
root=Path.cwd();report=root/'installer-results';report.mkdir(exist_ok=True)
setup=root/'installer-output/Pumpkin-Patch-Setup.exe'
install=Path(os.environ['LOCALAPPDATA'])/'Programs/Pumpkin Patch'
exe=install/'Pumpkin Patch.exe'
shell=win32com.client.Dispatch('WScript.Shell')
desktop=Path(shell.SpecialFolders('Desktop'))/'Pumpkin Patch.lnk'
start=Path(shell.SpecialFolders('Programs'))/'Pumpkin Patch.lnk'
saved=Path(os.environ['APPDATA'])/'PumpkinPatch/installer-test-user.pumpkin';saved.parent.mkdir(parents=True,exist_ok=True);saved.write_text('keep saved pumpkin')
result={'checks':[],'setup_bytes':setup.stat().st_size}
registry=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{D28EFED5-ED17-4DCC-AB98-D18B68C78BF8}_is1'

def check(value,message):
    if not value:raise AssertionError(message)
    result['checks'].append(message)

def wait_until(fn,timeout=180):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            value=fn()
            if value:return value
        except Exception:pass
        time.sleep(.3)
    raise TimeoutError('Timed out waiting for installer control')

def button(wizard,text):
    return next((b for b in wizard.descendants(class_name='TNewButton') if text.casefold() in b.window_text().replace('&','').casefold() and b.is_visible() and b.is_enabled()),None)

try:
    check(setup.stat().st_size<8*1024*1024,'setup is under 8 MB for Discord attachment')
    process=subprocess.Popen([str(setup),'/SP-','/NORESTART','/LOG='+str(report/'setup.log')])
    wizard=Desktop(backend='win32').window(title='Setup - Pumpkin Patch')
    wizard.wait('visible',timeout=40)
    wizard.capture_as_image().save(report/'welcome.png')
    wait_until(lambda:button(wizard,'Next'),30).click()
    wait_until(lambda:button(wizard,'Install'),30).click()
    finish=wait_until(lambda:button(wizard,'Finish'),240)
    wizard.capture_as_image().save(report/'finished.png')
    # Leave launching to the isolated app feature test below.
    lists=[c for c in wizard.descendants(class_name='TNewCheckListBox') if c.is_visible()]
    if lists:
        lists[0].set_focus();lists[0].type_keys('{HOME}{SPACE}')
    finish.click();check(process.wait(timeout=30)==0,'Next, Install and Finish complete successfully')
    check(exe.is_file() and (install/'_internal').is_dir(),'app and bundled libraries are installed')
    for label,path in [('desktop',desktop),('Start menu',start)]:
        check(path.is_file(),label+' shortcut exists')
        shortcut=shell.CreateShortcut(str(path))
        check(Path(shortcut.TargetPath).resolve()==exe.resolve(),label+' shortcut points to the app')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,registry) as key:
        check(winreg.QueryValueEx(key,'DisplayName')[0]=='Pumpkin Patch','per-user Windows uninstall entry exists')
    completed=subprocess.run(['python','tools/check_packaged.py','--executable',str(exe),'--report-dir',str(report/'app'),'--opengl-dir',args.opengl_dir],timeout=480)
    check(completed.returncode==0,'installed app passes all 18 feature checks')
    upgrade=subprocess.run([str(setup),'/VERYSILENT','/SUPPRESSMSGBOXES','/SP-','/NORESTART','/LOG='+str(report/'upgrade.log')],timeout=240)
    check(upgrade.returncode==0 and exe.exists(),'running setup again upgrades the existing installation')
    check(saved.read_text()=='keep saved pumpkin','install and upgrade preserve saved pumpkins')
    uninstall=subprocess.run([str(install/'unins000.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/LOG='+str(report/'uninstall.log')],timeout=90)
    wait_until(lambda:not exe.exists(),30)
    check(uninstall.returncode==0 and not exe.exists(),'Windows uninstall removes the program')
    check(not desktop.exists() and not start.exists(),'Windows uninstall removes app shortcuts')
    check(saved.read_text()=='keep saved pumpkin','Windows uninstall keeps saved pumpkins')
    result['ok']=True
except Exception:
    result['ok']=False;result['error']=traceback.format_exc()
    try:
        wizard.capture_as_image().save(report/'failure.png')
        (report/'controls.txt').write_text('\n'.join(c.class_name()+' '+c.window_text() for c in wizard.descendants()),encoding='utf-8')
    except Exception:pass
finally:
    (report/'installer.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
if not result['ok']:raise SystemExit(1)
