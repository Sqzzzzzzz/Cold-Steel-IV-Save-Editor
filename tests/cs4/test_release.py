"""Release metadata and distribution checks; no real saves or GitHub access."""
import hashlib
import json
import zipfile
import pytest
from tools import build_release,package_release


def test_version_matches_source_and_tag(monkeypatch):
    monkeypatch.delenv('GITHUB_REF_TYPE',raising=False)
    assert build_release.check_version()==build_release.VERSION
    monkeypatch.setenv('GITHUB_REF_TYPE','tag')
    monkeypatch.setenv('GITHUB_REF_NAME','v'+build_release.VERSION)
    assert build_release.check_version()==build_release.VERSION
    monkeypatch.setenv('GITHUB_REF_NAME','v0.0.0')
    with pytest.raises(ValueError,match='tag'):build_release.check_version()


def test_mismatched_version_file_blocks_release(tmp_path,monkeypatch):
    monkeypatch.setattr(build_release,'ROOT',tmp_path)
    (tmp_path/'VERSION.txt').write_text('0.0.0')
    with pytest.raises(ValueError,match='differ'):build_release.check_version()


@pytest.fixture
def package_inputs(tmp_path,monkeypatch):
    source=tmp_path/'source';source.mkdir()
    for name in package_release.DOCUMENTS:(source/name).write_text('Notice '+name,encoding='utf-8')
    licenses=source/'licenses';licenses.mkdir();(licenses/'LICENSE.txt').write_text('Runtime notice')
    (licenses/'sources.json').write_text(json.dumps({'files':[{'file':'LICENSE.txt','sha256':hashlib.sha256((licenses/'LICENSE.txt').read_bytes()).hexdigest()}]}))
    (licenses/'personal.dat').write_text('Not a license notice')
    for name in ('personal.dat','settings.json','debug.py','game.tbl','nested.zip'):(source/name).write_text('Must not ship')
    executable=tmp_path/'app.exe';executable.write_bytes(b'MZ' + bytes(128))
    monkeypatch.setattr(package_release,'ROOT',source)
    return source,executable,tmp_path/'release'


def test_user_zip_contains_only_allowlisted_files_and_valid_checksum(package_inputs):
    source,executable,destination=package_inputs
    archive=package_release.package(executable,destination)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist())=={'CS4_Inventory_Editor.exe','VERSION.txt','LICENSES/LICENSE.txt','LICENSES/sources.json',*package_release.DOCUMENTS}
        assert bundle.read('VERSION.txt').decode().strip()==build_release.VERSION
        assert bundle.read('CS4_Inventory_Editor.exe')==executable.read_bytes()
    assert (destination/'SHA256SUMS.txt').read_text()==hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n'
    assert not list(destination.glob('*.tmp'))


def test_failed_packaging_preserves_previous_archive(package_inputs):
    source,executable,destination=package_inputs
    archive=package_release.package(executable,destination);previous=archive.read_bytes()
    (source/package_release.DOCUMENTS[0]).unlink()
    with pytest.raises(FileNotFoundError):package_release.package(executable,destination)
    assert archive.read_bytes()==previous and not list(destination.glob('*.tmp'))


def test_packaging_rejects_non_executable(package_inputs):
    source,executable,destination=package_inputs;executable.write_bytes(b'not an EXE')
    with pytest.raises(ValueError):package_release.package(executable,destination)
    assert not destination.exists()


def test_changed_license_notice_blocks_packaging(package_inputs):
    source,executable,destination=package_inputs
    (source/'licenses/LICENSE.txt').write_text('Changed')
    with pytest.raises(ValueError,match='manifest'):package_release.package(executable,destination)
    assert not destination.exists()
