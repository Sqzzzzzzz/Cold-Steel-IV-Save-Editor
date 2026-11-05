import struct
from pathlib import Path
import pytest
from catalog_core import parse_item_tbl, save_catalog_json,load_catalog_json
from catalog_visibility import is_visible_item
from game_icons import icon_key, icon_file_for_item
from original_item_icons import original_icon_for_item


def native_table(*rows):
    groups={kind:sum(k==kind for k,_ in rows) for kind,_ in rows}
    return struct.pack('<HI',len(rows),len(groups))+b''.join(k.encode()+b'\0'+struct.pack('<I',v) for k,v in groups.items())+b''.join(k.encode()+b'\0'+struct.pack('<H',len(v))+v for k,v in rows)


def native_item(i=42,category=0x8c,name='CS4 Sword',description='Weapon description',quartz=False,stats=None,character=7):
    meta=bytearray(150);meta[:2]=b'\xee\x99';meta[2]=category
    struct.pack_into('<10i',meta,100,*(stats or [50000,-40000,0,0,0,0,0,0,0,0]))
    tail=bytes(8)+(struct.pack('<6H',1,2,0,65535,3,3) if quartz else b'')
    return struct.pack('<HH',i,character)+b'flags\0'+meta+name.encode()+b'\0'+description.encode()+b'\0'+tail


@pytest.mark.parametrize('code,category',[(0x87,'material'),(0x8c,'weapon'),(0xbe,'armor'),(0xbf,'shoes'),(0xc0,'accessory'),(0xc1,'costume'),(0xc9,'quartz_master'),(0xd3,'food'),(0xdc,'fish'),(0x86,'card')])
def test_native_cs4_category_is_read_after_d1(code,category):
    data=parse_item_tbl(native_table(('item',native_item(category=code))))
    assert data[42]['category']==category and data[42]['character']==7
    assert data[42]['type_code']==code and data[42]['stats']=={'STR':50000,'DEF':-40000}


def test_native_quartz_arts_no_cs3_effect_guessing():
    r=parse_item_tbl(native_table(('item_q',native_item(category=0xc8,quartz=True))))[42]
    assert r['arts']==[1,2,3] and r['kind']=='quartz'
    assert not {'element','effects','rarity'} & r.keys()


def test_localized_names_and_signed_int32_json_roundtrip(tmp_path):
    row=native_item(name='Меч CS4',description='Описание',stats=[2**31-1,-2**31]+[0]*8)
    records=parse_item_tbl(native_table(('item',row)))
    file=tmp_path/'catalog.json';save_catalog_json(file,records)
    assert load_catalog_json(file)==records


@pytest.mark.parametrize('tail',[-1,1])
def test_wrong_native_length_is_rejected(tail):
    body=native_item();body=body[:tail] if tail<0 else body+b'\0'
    with pytest.raises(ValueError):parse_item_tbl(native_table(('item',body)))


def test_cs3_layout_is_rejected():
    body=struct.pack('<HH',42,0)+b'\0'+bytes(127)+b'CS3 Name\0Description\0'+bytes(8)
    with pytest.raises(ValueError):parse_item_tbl(native_table(('item',body)))


def test_visibility_does_not_reuse_cs3_id_rules():
    assert is_visible_item({'id':249,'name':'Actual CS4 item'})
    assert is_visible_item({'id':2125,'name':'reserve','description':'◆'})
    assert not is_visible_item({'id':42,'name':'unused item'})


@pytest.mark.parametrize('category',['weapon','food','fish','quartz_master','material','quest','orbment'])
def test_cs3_numeric_ids_do_not_choose_cs3_specific_icons(category):
    for i in (60,249,1200,2100,2250,3150,3207,3350):
        assert icon_key({'category':category},i)==category
    icon=original_icon_for_item(3207,{'category':category})
    assert icon is not None and icon.match=='family' and not icon.verified


def test_explicit_item_png_overrides_family(tmp_path):
    from catalog_core import resource_path
    folder=tmp_path/'by_id';folder.mkdir()
    png=resource_path('icons/original/Armour (Sen III Item).png').read_bytes()
    (folder/'3207.png').write_bytes(png)
    result=original_icon_for_item(3207,{'category':'quartz_master'},cache=tmp_path,manual=tmp_path)
    assert result.match=='item' and result.path==folder/'3207.png' and not result.verified


@pytest.mark.parametrize('element',['water','Water','WATER'])
def test_explicit_quartz_element_is_case_insensitive(element):
    assert icon_key({'category':'quartz_normal','element':element},3350)=='quartz_water'


@pytest.mark.parametrize('character',[10,23])
def test_weapon_stances_with_localized_aliases_keep_first_record(character):
    first=native_item(name='Сокрушитель мечей',character=character)
    second=native_item(name='Мечелом',character=character,stats=[123]+[0]*9)
    rows=parse_item_tbl(native_table(('item',first),('item',second)))
    assert len(rows)==1 and rows[42]['name']=='Сокрушитель мечей'
    assert rows[42]['stats']['STR']==50000


@pytest.mark.parametrize('changes',[{'character':11},{'category':0xc1},{'description':'Other item'}])
def test_conflicting_items_are_not_mistaken_for_weapon_stances(changes):
    first=native_item(name='First',character=10)
    second=native_item(**{'name':'Second','character':10,**changes})
    with pytest.raises(ValueError,match='Конфликтующие'):
        parse_item_tbl(native_table(('item',first),('item',second)))


def test_icons_follow_cs4_character_metadata_and_master_names(tmp_path):
    for item_id in (42,3207,65000):
        weapon=original_icon_for_item(item_id,{'category':'weapon','character':11},cache=tmp_path,manual=tmp_path)
        assert weapon.path.name=='Twin Swords Kurt (Sen III Weapon).png'
        for name in ('Калейдо','Калейдо EX','Kaleido EX'):
            master=original_icon_for_item(item_id,{'category':'quartz_master','name':name},cache=tmp_path,manual=tmp_path)
            assert master.path.name=='Kaleido (Sen IV MQ).png' and master.verified
    unknown=original_icon_for_item(3207,{'category':'quartz_master','name':'Unknown CS4 quartz'},cache=tmp_path,manual=tmp_path)
    assert unknown.path.name=='Lost (Sen III Quartz).png'


def test_all_31_master_names_and_ex_variants_resolve_to_native_art(tmp_path):
    from game_icons import CS4_MASTER_NAMES
    paths=set()
    for name in CS4_MASTER_NAMES:
        for suffix in ('',' EX'):
            found=original_icon_for_item(65000,{'category':'quartz_master','name':name+suffix},cache=tmp_path,manual=tmp_path)
            assert found and found.verified and found.match=='item',name+suffix
            assert found.path.name==f'{name} (Sen IV MQ).png'
            paths.add(found.path)
    assert len(paths)==31
    for name in ('Эрда','Эрда EX','Воден','Воден EX','София','Динамис'):
        assert original_icon_for_item(42,{'category':'quartz_master','name':name},cache=tmp_path,manual=tmp_path).verified
    translated=original_icon_for_item(42,{'category':'quartz_master','name':'Другое имя','_english_name':'Erda'},cache=tmp_path,manual=tmp_path)
    assert translated.path.name=='Erda (Sen IV MQ).png'


def test_master_texture_extraction_rejects_invalid_data():
    from tools.extract_cs4_master_icons import decode_lz4,decode_texture
    assert decode_lz4(b'\x50hello',5)==b'hello'
    assert decode_lz4(b'\x10a\x01\x00',5)==b'aaaaa'
    for data,size in [(b'\xf0',1),(b'\x20a',2),(b'\x00\x00\x00',4),(b'\x50hello',4)]:
        with pytest.raises(ValueError):decode_lz4(data,size)
    with pytest.raises(ValueError):decode_texture(b'wrong texture')


def test_small_stock_dlc_tables_are_recognized_as_english():
    from catalog_locale import catalog_locale
    assert catalog_locale({3805:{'name':'Qilin Dress','description':'Eastern-style outfit.'}})=='en'
    assert catalog_locale({3805:{'name':'Qilin Dress','description':'Платье в восточном стиле.'}})=='ru'
@pytest.mark.parametrize('character',[[],{},'10',True,-1,65536])
def test_invalid_json_character_is_rejected(tmp_path,character):
    import json
    from catalog_core import load_catalog_json
    path=tmp_path/'catalog.json'
    path.write_text(json.dumps({'items':[{'id':42,'name':'Weapon','category':'weapon','character':character}]}),encoding='utf-8')
    with pytest.raises(ValueError,match='персонаж'):load_catalog_json(path)
