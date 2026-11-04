from pathlib import Path
import hashlib
import json
import pytest
from beta_config import seed_beta_profile
from catalog_core import user_catalog_path,save_catalog_json
from cs4_save import CS4Save,SaveFormatError
from game_scan import config_dir,find_game_install,scan_game_tables,APP_ID
from game_icons import icon_cache_dir
from preview_demo import synthetic_demo_save
from qt_backend import EditorCore
from save_scan import save_directories,newest_compatible_save
from edit_changes import EditChanges
from test_catalog import native_table,native_item


@pytest.fixture
def core(tmp_path,monkeypatch):
    monkeypatch.setenv('APPDATA',str(tmp_path/'appdata'))
    c=EditorCore();source=tmp_path/'русский путь/save003.dat';source.parent.mkdir()
    source.write_bytes(synthetic_demo_save());c.open_file(source)
    return c


def test_profile_catalog_settings_and_icons_are_isolated_from_cs3(tmp_path,monkeypatch):
    monkeypatch.setenv('APPDATA',str(tmp_path))
    old=tmp_path/'CS3InventoryEditor_BETA';old.mkdir()
    (old/'settings.json').write_text(json.dumps({'game_root':'CS3','language':'en'}))
    save_catalog_json(old/'catalog_scanned.json',{20:{'id':20,'name':'WRONG CS3 data'}})
    c=EditorCore()
    assert c.settings['game_root']=='' and c.language=='ru' and not c.catalog
    assert 'CS4' in str(config_dir()) and 'CS4' in str(user_catalog_path()) and 'CS4' in str(icon_cache_dir())
    assert not (config_dir()/'catalog_scanned.json').exists()


def test_undo_edit_changes_and_reset(core):
    before=core.save.bytes();changes=EditChanges();changes.refresh(core.save)
    core.change({20:8,21:0,65000:2});changes.refresh(core.save)
    assert changes.counts()=={'added':1,'removed':1,'modified':1}
    assert core.undo() and core.save.bytes()==before
    changes.refresh(core.save);assert not changes.changes
    core.change({20:5});core.reset();assert core.save.bytes()==before


def test_copy_backup_overwrite_and_baseline(core):
    original=core.source.read_bytes();core.change({20:9});edited=core.save.bytes()
    copy=core.source.with_name('save004.dat');core.save_copy(copy)
    assert core.source.read_bytes()==original and copy.read_bytes()==edited
    with pytest.raises(FileExistsError):core.save_copy(copy)
    with pytest.raises(ValueError):core.save_copy(core.source)
    backup=core.overwrite_with_backup()
    assert backup.read_bytes()==original and core.source.read_bytes()==edited
    assert not core.save.changed and not core.undo_stack
    assert core.overwrite_with_backup() is None


def test_external_change_blocks_overwrite(core):
    other=CS4Save(core.source.read_bytes());other.set_quantity(20,33);core.source.write_bytes(other.bytes())
    core.change({20:9})
    with pytest.raises(RuntimeError):core.overwrite_with_backup()
    assert core.source.read_bytes()==other.bytes() and not list(core.source.parent.glob('*.bak'))


def test_second_race_check_blocks_write_and_keeps_backup(core,monkeypatch):
    original=core.source.read_bytes();core.change({20:8})
    write=core._atomic_write
    other=CS4Save(original);other.set_quantity(20,34);other_bytes=other.bytes()
    def race(path,payload,**kwargs):
        path.write_bytes(other_bytes)
        return write(path,payload,**kwargs)
    monkeypatch.setattr(core,'_atomic_write',race)
    with pytest.raises(RuntimeError):core.overwrite_with_backup()
    assert core.source.read_bytes()==other_bytes
    backups=list(core.source.parent.glob('*.bak'));assert len(backups)==1 and backups[0].read_bytes()==original


def test_compare_export_and_write_protection(core):
    raw=core.save.bytes();core.change({20:1})
    report=core.compare(core.source)
    assert report['modified']==[(20,1,15)] and report['other_changed_bytes']==0
    exported=core.export_csv(core.source.with_suffix('.csv'))
    assert exported.read_bytes().startswith(b'\xef\xbb\xbf')
    with pytest.raises(ValueError):core.export_csv(core.source)
    assert core.source.read_bytes()==raw


def test_auto_latest_skips_wrong_game_and_bad_crc(tmp_path,monkeypatch):
    home=tmp_path/'user';folder=home/'Saved Games/FALCOM/ed8_psv4';folder.mkdir(parents=True)
    old=home/'Saved Games/FALCOM/ed8_psv3';old.mkdir()
    good=folder/'save001.dat';good.write_bytes(synthetic_demo_save())
    bad=folder/'save002.dat';bad.write_bytes(b'bad')
    assert save_directories(home=home)==[folder]
    match,warnings=newest_compatible_save([folder])
    assert match.path==good.resolve() and warnings


def test_actual_cs4_install_and_localized_table_scan(tmp_path,core):
    steam=tmp_path/'steam';common=steam/'steamapps/common';game=common/'The Legend of Heroes Trails of Cold Steel IV'
    base=game/'data/text/dat_en';base.mkdir(parents=True)
    (base/'t_item.tbl').write_bytes(native_table(('item',native_item(name='CS4 Sword',description='Increases the strength of the equipped character'))))
    dlc=game/'data/dlc/text/0001/dat_en';dlc.mkdir(parents=True)
    (dlc/'t_item.tbl').write_bytes(native_table(('item',native_item(i=65000,category=0xc1,name='CS4 Outfit',description='Outfit for the equipped character'))))
    (steam/'steamapps'/f'appmanifest_{APP_ID}.acf').write_text('"installdir" "The Legend of Heroes Trails of Cold Steel IV"')
    assert APP_ID=='1198090' and find_game_install(steam_roots=[steam])==game.resolve()
    result=core.scan_game(game)
    assert result.base_count==1 and result.added_by_dlc==1
    assert core.catalog[42]['name']=='CS4 Sword' and core.english[65000]['name']=='CS4 Outfit'


def test_dlc_fallback_translates_names_and_descriptions_without_changing_english(core):
    core.base={3808:{'id':3808,'name':"Altina's Millium Hat",'description':'Original hat description','_source':'dlc','_locale':'en'},
               4200:{'id':4200,'name':"Rean's Casuals",'description':'Original clothes description','_source':'dlc','_locale':'en'},
               3803:{'id':3803,'name':'Magical Girl ☆ Allie','description':'Original magic description','_source':'dlc','_locale':'unknown'}}
    core.english={};core.rebuild_catalog()
    assert core.item_name(3808)=='Шапка Миллиум для Альтины'
    assert core.item_name(4200)=='Повседневная одежда Рина'
    assert 'Лехтер' in core.description(3803)
    assert core.base[4200]['name']=="Rean's Casuals"
    core.set_language('en')
    assert core.item_name(4200)=="Rean's Casuals" and core.description(4200)=='Original clothes description'
    assert core.item_name(3803)=='Magical Girl ☆ Allie'
    core.set_language('ru');core.rebuild_catalog()
    assert core.item_name(3803)=='Девочка-волшебница ☆ Элли'


def test_dlc_translation_respects_local_text_overrides_and_unrelated_ids(core):
    core.base={42:{'id':42,'name':"Rean's Casuals",'_source':'dlc','_locale':'ru'},
               43:{'id':43,'name':"Rean's Casuals",'_source':'dlc','_locale':'en'},
               44:{'id':44,'name':"Rean's Casuals",'_source':'base','_locale':'en'},
               4200:{'id':4200,'name':'Different mod item','_source':'dlc','_locale':'en'}}
    core.overrides={43:{'id':43,'name':'Мой перевод','description':'Моё описание'}}
    core.english={};core.rebuild_catalog()
    assert core.catalog[42]['name']=="Rean's Casuals"
    assert core.catalog[43]['name']=='Мой перевод' and core.description(43)=='Моё описание'
    assert core.catalog[44]['name']=="Rean's Casuals"
    assert core.catalog[4200]['name']=='Different mod item'


def test_cached_native_categories_are_refreshed_without_losing_user_override(core):
    core.base={60:{'id':60,'name':'U-материал','kind':'item','category':'other','type_code':0x87}}
    core.rebuild_catalog()
    assert core.catalog[60]['category']=='material'
    core.overrides={60:{'id':60,'name':'Мой предмет','category':'other'}};core.rebuild_catalog()
    assert core.catalog[60]['category']=='other'


def test_english_scan_fills_partial_cache_and_preserves_russian(core,tmp_path):
    core.base={0:{'id':0,'name':'Снадобье Тиа','description':'Лечит HP.','_locale':'ru'},
               3228:{'id':3228,'name':'Моя Эрда','description':'Мой перевод.','category':'quartz_master','_locale':'ru'}}
    core.english={3808:{'id':3808,'name':"Altina's Millium Hat",'description':'An English hat.'}}
    core.rebuild_catalog();assert core.needs_english_catalog()
    game=tmp_path/'CS4';folder=game/'data/text/dat_en';folder.mkdir(parents=True)
    (folder/'t_item_en.tbl').write_bytes(native_table(
        ('item',native_item(i=0,category=0x81,name='Tear Balm',description='Restores HP.')),
        ('item',native_item(i=3228,category=0xc9,name='Erda',description='Master quartz.'))))
    core.scan_game(game)
    assert not core.needs_english_catalog()
    core.set_language('en')
    assert core.item_name(0)=='Tear Balm' and core.description(0)=='Restores HP.'
    assert core.item_name(3228)=='Erda' and core.catalog[3228]['_english_name']=='Erda'
    assert core.item_name(3808)=="Altina's Millium Hat"
    core.set_language('ru')
    assert core.item_name(0)=='Снадобье Тиа' and core.description(0)=='Лечит HP.'
    assert core.item_name(3228)=='Моя Эрда'
