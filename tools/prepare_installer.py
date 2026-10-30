"""Pin the online installer to a public, already-tested Windows release."""
import hashlib,os,re
from pathlib import Path
release=os.environ['SOURCE_TAG'];repo=os.environ['GH_REPO']
assert re.fullmatch(r'[A-Za-z0-9._-]+',release)
assert re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo)
asset='Pumpkin-Patch-windows-x64-beta.zip'
expected=(Path('installer-input')/(asset+'.sha256')).read_text().split()[0].lower()
assert re.fullmatch('[0-9a-f]{64}',expected)
actual=hashlib.sha256((Path('installer-input')/asset).read_bytes()).hexdigest()
assert actual==expected,'Release archive does not match its checksum'
url=f'https://github.com/{repo}/releases/download/{release}/{asset}'
Path('installer/payload.iss').write_text(f'#define PayloadURL "{url}"\n#define PayloadSHA256 "{expected}"\n',encoding='utf-8')
print('Installer pinned to verified payload:',release)
