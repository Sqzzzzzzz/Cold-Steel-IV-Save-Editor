"""Create the end-user archive from an explicit allowlist; never package a tree."""
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_info import VERSION

DOCUMENTS = ('QUICK_START.md','QUICK_START_RU.md','LICENSE','THIRD_PARTY_NOTICES.md')


def license_files():
    root=ROOT/'licenses'
    manifest=root/'sources.json'
    files=[manifest]
    for entry in json.loads(manifest.read_text(encoding='utf-8'))['files']:
        relative=PurePosixPath(entry['file'])
        path=root/relative
        if relative.is_absolute() or '..' in relative.parts or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Invalid license manifest path')
        if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('License notice does not match its manifest: '+str(relative))
        files.append(path)
    if len(files)==1:raise ValueError('Runtime license notices are missing')
    return files


def package(executable, destination):
    executable = Path(executable)
    destination = Path(destination)
    if not executable.is_file() or executable.read_bytes()[:2] != b'MZ':
        raise ValueError('A Windows executable is required')
    notices=license_files()
    destination.mkdir(parents=True,exist_ok=True)
    target = destination/f'Cold_Steel_IV_Inventory_Editor_v{VERSION}_Windows_x64.zip'
    fd,temporary=tempfile.mkstemp(prefix='.release-',suffix='.tmp',dir=destination)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            archive.write(executable,'CS4_Inventory_Editor.exe')
            for name in DOCUMENTS:archive.write(ROOT/name,name)
            for path in notices:archive.write(path,'LICENSES/'+path.relative_to(ROOT/'licenses').as_posix())
            archive.writestr('VERSION.txt',VERSION+'\n')
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:raise ValueError('Release archive failed CRC verification')
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    checksum = destination/'SHA256SUMS.txt'
    checksum_temporary=checksum.with_suffix('.tmp')
    try:
        checksum_temporary.write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n',encoding='ascii')
        os.replace(checksum_temporary,checksum)
    finally:checksum_temporary.unlink(missing_ok=True)
    return target


if __name__ == '__main__':
    print(package(ROOT/'dist/CS4_Inventory_Editor.exe',ROOT/'release'))
