"""The same checked Windows release build for local use and GitHub Actions."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_info import VERSION,APP_NAME
from tools.package_release import package


def check_version():
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)',VERSION):
        raise ValueError('Stable releases require a MAJOR.MINOR.PATCH version')
    if (ROOT/'VERSION.txt').read_text(encoding='utf-8').strip()!=VERSION:
        raise ValueError('app_info.VERSION and VERSION.txt differ')
    if os.environ.get('GITHUB_REF_TYPE')=='tag' and os.environ.get('GITHUB_REF_NAME')!='v'+VERSION:
        raise ValueError('Release tag does not match the application version')
    if not (ROOT/f'docs/releases/v{VERSION}.md').is_file():
        raise ValueError('Release notes are missing')
    return VERSION


def build():
    check_version()
    if os.name!='nt':raise RuntimeError('Build the Windows release on Windows')
    system_root=Path(os.environ['SystemRoot'])
    environment=dict(os.environ)
    environment['PATH']=os.pathsep.join(map(str,(Path(sys.executable).parent,system_root/'System32',system_root)))
    for key in ('PYTHONHOME','PYTHONPATH','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','QML2_IMPORT_PATH'):
        environment.pop(key,None)
    def run(*args,cwd=ROOT,env=environment):
        print('Running:',subprocess.list2cmdline([str(arg) for arg in args]),flush=True)
        subprocess.run(list(map(str,args)),cwd=cwd,env=env,check=True,timeout=1200)

    checks=ROOT/'checks/release';checks.mkdir(parents=True,exist_ok=True)
    run(sys.executable,'-m','pytest','-q')
    run(sys.executable,ROOT/'qt_window.py','--self-test','--self-test-report',checks/'source-selftest.json')
    numbers=tuple(map(int,VERSION.split('.')))+(0,)
    version_file=checks/'windows-version.txt'
    version_file.write_text(
        'VSVersionInfo(ffi=FixedFileInfo(filevers='+repr(numbers)+',prodvers='+repr(numbers)+
        ',mask=0x3f,flags=0,OS=0x40004,fileType=1,subtype=0,date=(0,0)),kids=['
        "StringFileInfo([StringTable('040904B0',["+
        f"StringStruct('FileDescription',{APP_NAME!r}),StringStruct('ProductName',{APP_NAME!r}),"+
        f"StringStruct('FileVersion',{VERSION!r}),StringStruct('ProductVersion',{VERSION!r}),"+
        "StringStruct('OriginalFilename','CS4_Inventory_Editor.exe')])]),"
        "VarFileInfo([VarStruct('Translation',[1033,1200])])])\n",encoding='utf-8')
    assets=('cs4_cover.jpg','hud_arrow_up.svg','hud_arrow_down.svg','hud_check.svg')
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed',
             '--name','CS4_Inventory_Editor','--specpath',str(ROOT/'build'),
             '--distpath',str(ROOT/'dist'),'--workpath',str(ROOT/'build/pyinstaller'),
             '--icon',str(ROOT/'icons/app_icon.ico'),'--version-file',str(version_file),
             '--add-data',str(ROOT/'icons/original')+';icons/original',
             '--add-data',str(ROOT/'icons/app_icon.ico')+';icons']
    for name in assets:command+=['--add-data',str(ROOT/'assets'/name)+';assets']
    run(*command,ROOT/'qt_window.py')
    executable=ROOT/'dist/CS4_Inventory_Editor.exe'
    run(sys.executable,ROOT/'tools/extract_tk_icon.py','--verify-exe',executable,ROOT/'icons/app_icon.ico')
    import pefile
    with pefile.PE(str(executable)) as pe:
        if pe.FILE_HEADER.Machine!=0x8664 or pe.OPTIONAL_HEADER.Subsystem!=2:
            raise ValueError('Expected a 64-bit Windows GUI executable')
        versions={key:value for group in pe.FileInfo for entry in group
                  for table in getattr(entry,'StringTable',[]) for key,value in table.entries.items()}
        if versions.get(b'FileVersion')!=VERSION.encode():raise ValueError('EXE version metadata differs')
    # Run outside the checkout with no Python/development directories on PATH.
    with tempfile.TemporaryDirectory(prefix='cs4-release-') as directory:
        isolated={**environment,'PATH':os.pathsep.join(map(str,(system_root/'System32',system_root))),
                  'APPDATA':str(Path(directory)/'profile')}
        run(executable,'--self-test','--self-test-report',checks/'windows-selftest.json',cwd=directory,env=isolated)
        report=json.loads((checks/'windows-selftest.json').read_text(encoding='utf-8'))
        if report.get('status')!='passed' or not report.get('frozen') or report.get('version')!=VERSION:
            raise ValueError('Frozen self-test report is invalid')
        run(executable,'--demo','--smoke-test',cwd=directory,env=isolated)
    print('Release ready:',package(executable,ROOT/'release'),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-version',action='store_true')
    args=parser.parse_args()
    if args.check_version:print(check_version())
    else:build()
