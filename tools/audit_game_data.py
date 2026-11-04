"""Read-only audit of owner-supplied catalogs and saves; writes only its report.

Game files are not bundled. All save-write experiments run on temporary copies.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from catalog_core import parse_item_tbl,load_catalog_json
from catalog_visibility import is_visible_item,NON_INVENTORY_ITEM_IDS
from catalog_locale import catalog_locale
from cs4_save import CS4Save,TABLE_OFFSET,TABLE_END
from game_icons import quartz_rarity,icon_key
from original_item_icons import original_icon_for_item
from qt_backend import EditorCore


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--table',type=Path,required=True)
    parser.add_argument('--comparison-table',type=Path)
    parser.add_argument('--english',type=Path)
    parser.add_argument('--save',type=Path,action='append',default=[])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    catalog=parse_item_tbl(args.table)
    report={'table':{'name':args.table.name,'sha256':sha(args.table.read_bytes()),
              'records':len(catalog),'visible':sum(is_visible_item(r) for r in catalog.values()),
              'locale':catalog_locale(catalog)},'checks':{},'saves':[]}
    if args.comparison_table:
        other=parse_item_tbl(args.comparison_table)
        assert catalog.keys()==other.keys(),'Item ID mismatch between localized tables'
        for iid,r in catalog.items():
            for field in ('category','type_code','element','rarity','character','stats'):
                assert r.get(field)==other[iid].get(field),(iid,field)
        report['checks']['localized_native_metadata']='PASS'
    english=load_catalog_json(args.english) if args.english else {}
    if english:
        assert catalog_locale(english)=='en'
        assert all(r['name'].strip() and r.get('description','').strip() for r in english.values())
        assert catalog.keys()<=english.keys()
        for iid,record in catalog.items():
            for field in ('kind','category'):assert record.get(field)==english[iid].get(field),(iid,field)
            assert is_visible_item(record)==is_visible_item(english[iid]),('visibility',iid)
        assert not any(__import__('re').search('[А-Яа-яЁё]',r['name']+r.get('description','')) for r in english.values())
        report['english']={'records':len(english),'sha256':sha(args.english.read_bytes()),
                           'extra_ids':sorted(english.keys()-catalog.keys())}
        report['checks']['all_english_names_and_descriptions']='PASS'
    manifest=json.loads((ROOT/'icons/original/sources.json').read_text())
    for entry in manifest['files']:
        assert sha((ROOT/'icons/original'/entry['file']).read_bytes())==entry['sha256'],entry['file']
    report['checks']['original_asset_hashes']={'status':'PASS','files':len(manifest['files'])}
    rows=[];quartz_count=0;missing=[]
    for iid,record in sorted(catalog.items()):
        found=original_icon_for_item(iid,record)
        if record['kind']=='quartz':
            quartz_count+=1
        if not found:missing.append(iid)
        rows.append([iid,record['category'],record.get('element',''),record.get('rarity',''),
                     found.path.name if found else '',found.match if found else 'unverified',is_visible_item(record)])
    with (args.output/'CS4_ICON_MAPPING.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['ID','category','element','rarity','asset','match','visible']);writer.writerows(rows)
    report['checks']['quartz_records_parsed']={'status':'PASS','records':quartz_count}
    report['icons']={'resolved':len(catalog)-len(missing),'unverified_ids':missing,
                     'unverified_visible_ids':[i for i in missing if is_visible_item(catalog[i])],
                     'note':'Family matches use shared game artwork. This is not an in-game visual verification of every ID.'}
    for path in args.save:
        original=path.read_bytes();save=CS4Save(original)
        expected={e.item_id:e.quantity for e in save.items()};rng=random.Random(793)
        for _ in range(100):
            changes={iid:rng.randrange(100) for iid in rng.sample(sorted(catalog.keys()-NON_INVENTORY_ITEM_IDS),min(12,len(catalog.keys()-NON_INVENTORY_ITEM_IDS)))}
            for iid,qty in changes.items():
                if qty:expected[iid]=qty
                else:expected.pop(iid,None)
            save.set_quantities(changes);data=save.bytes()
            assert data[:12]==original[:12]
            assert data[16:TABLE_OFFSET]==original[16:TABLE_OFFSET]
            assert data[TABLE_END:]==original[TABLE_END:]
            assert [(e.item_id,e.quantity) for e in CS4Save(data).items()]==list(expected.items())
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{'APPDATA':temp}):
            source=Path(temp)/'save001.dat';source.write_bytes(original)
            core=EditorCore();core.open_file(source)
            first=core.save.items()[0];core.change({first.item_id:99 if first.quantity!=99 else 98})
            edited=core.save.bytes()
            assert core.undo() and core.save.bytes()==original
            core.change({first.item_id:99 if first.quantity!=99 else 98})
            assert core.save.bytes()==edited
            copy=Path(temp)/'copy.dat';core.save_copy(copy)
            assert source.read_bytes()==original and copy.read_bytes()==edited
            backup=core.overwrite_with_backup()
            assert backup.read_bytes()==original and source.read_bytes()==edited
            assert not core.save.changed and not core.undo_stack
        assert sha(path.read_bytes())==sha(original),'Input save changed'
        report['saves'].append({'name':path.name,'sha256':sha(original),'occupied':CS4Save(original).occupied_count,
            'random_batches':100,'copy_backup_reopen':'PASS','non_inventory_bytes_unchanged':True,'input_file_unchanged':True})
    (args.output/'CS4_GAME_DATA_CHECK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
