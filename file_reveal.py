"""Reveal a completed export using the operating system's file manager."""
import subprocess,sys
from pathlib import Path

def reveal_file(path):
    path=Path(path).resolve()
    if not path.is_file():return False
    try:
        if sys.platform=='darwin':
            return subprocess.run(['open','-R',str(path)],check=False,capture_output=True).returncode==0
        if sys.platform=='win32':
            subprocess.Popen(['explorer.exe','/select,',str(path)]);return True
        try:
            result=subprocess.run(['dbus-send','--session','--dest=org.freedesktop.FileManager1','--type=method_call','/org/freedesktop/FileManager1','org.freedesktop.FileManager1.ShowItems','array:string:'+path.as_uri(),'string:'],check=False,capture_output=True)
            if result.returncode==0:return True
        except OSError:pass
        subprocess.Popen(['xdg-open',str(path.parent)]);return True
    except OSError:return False
