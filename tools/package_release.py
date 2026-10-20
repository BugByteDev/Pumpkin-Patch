"""Create portable beta archives; keep CI graphics drivers out of downloads."""
import hashlib,shutil,sys
from pathlib import Path
label=sys.argv[1];folder=Path('dist/Pumpkin Patch');out=Path('artifacts');out.mkdir(exist_ok=True)
assert folder.is_dir()
(folder/'READ ME.txt').write_text('Pumpkin Patch beta\n\nExtract the entire archive before starting the app. Keep the _internal folder beside the executable. Python and Blender are bundled or unnecessary; neither needs to be installed.\n\nLinux: run ./Pumpkin\\ Patch from the extracted folder. Requires a desktop session and OpenGL 3.3 capable graphics drivers.\n\nThese builds run automated geometry, UI, export and software OpenGL checks. Hardware graphics, printing and native file dialogs have not been manually tested on every system.\n',encoding='utf-8')
name=out/('Pumpkin-Patch-'+label+'-beta')
archive=Path(shutil.make_archive(str(name),'zip' if label.startswith('windows') else 'gztar',root_dir='dist',base_dir='Pumpkin Patch'))
(archive.parent/(archive.name+'.sha256')).write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(archive)
