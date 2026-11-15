import hashlib
from pathlib import Path
import os
import struct
import zlib
import pytest
from cs4_save import (CS4Save, SaveFormatError, SAVE_SIZE,TABLE_OFFSET,TABLE_END,
                      RECORD_COUNT,RECORD_SIZE, EMPTY_ID,save_checksum,get_diff_summary)
from preview_demo import synthetic_demo_save


def checksum_bitwise(body):
    value=len(body)
    for byte in body:
        value ^= byte
        for _ in range(8):
            value=(value >> 1) ^ (0xEDB88320 if value & 1 else 0)
    return value


def refresh_crc(data):
    data[12:16]=save_checksum(data).to_bytes(4,'little')
    return bytes(data)


def test_crc_independent_bitwise_algorithm():
    data=bytes(range(16))+b'Known CRC input: CS4 inventory\x00\xff'
    assert save_checksum(data)==checksum_bitwise(data[16:])
    assert save_checksum(data)!=zlib.crc32(data[16:])


def test_lossless_round_trip_and_no_op():
    raw=synthetic_demo_save();s=CS4Save(raw)
    assert s.bytes()==raw and not s.changed
    s.set_quantity(20,s.get_quantity(20))
    assert s.bytes()==raw and not s.changed


def test_add_remove_change_crc_and_preserve_unrelated_data():
    raw=synthetic_demo_save();s=CS4Save(raw)
    s.set_quantities({20:1,21:0,65534:99})
    edited=s.bytes();reopened=CS4Save(edited)
    assert reopened.get_quantity(20)==1
    assert reopened.get_quantity(21)==0
    assert reopened.get_quantity(65534)==99
    assert edited[:12]==raw[:12] and edited[16:TABLE_OFFSET]==raw[16:TABLE_OFFSET]
    assert edited[TABLE_END:]==raw[TABLE_END:]
    assert edited[12:16]!=raw[12:16]
    diff=get_diff_summary(raw,edited)
    assert diff['other_changed_bytes']==0
    assert (65534,99) in diff['added'] and (21,8) in diff['removed']
    s.reset();assert s.bytes()==raw and not s.changed


@pytest.mark.parametrize('empty_active_inventory', [False, True])
def test_ng_plus_edits_only_active_inventory(ng_plus_save_bytes, empty_active_inventory):
    raw = ng_plus_save_bytes
    if empty_active_inventory:
        data = bytearray(raw)
        data[TABLE_OFFSET:0x46F1C] = struct.pack('<H30x', EMPTY_ID) * 2048
        raw = refresh_crc(data)
    save = CS4Save(raw)
    assert save.get_quantity(20) == (0 if empty_active_inventory else 15)
    assert save.get_quantity(60) == (0 if empty_active_inventory else 268)
    assert save.get_quantity(3229) == 0
    assert save.bytes() == raw

    changes = {20: 7, 21: 0, 60: 999, 3229: 1}
    save.set_quantities(changes)
    edited = save.bytes()
    reopened = CS4Save(edited)
    assert all(reopened.get_quantity(item_id) == quantity for item_id, quantity in changes.items())
    assert edited[:12] == raw[:12]
    assert edited[16:TABLE_OFFSET] == raw[16:TABLE_OFFSET]
    assert edited[0x46F1C:] == raw[0x46F1C:]
    assert get_diff_summary(raw, edited)['other_changed_bytes'] == 0


def test_compare_counts_changes_to_carryover_as_outside_active_inventory(ng_plus_save_bytes):
    data = bytearray(ng_plus_save_bytes)
    struct.pack_into('<H', data, 0x46F1C + 2, 81)
    assert get_diff_summary(ng_plus_save_bytes, refresh_crc(data)) == {
        'added': [], 'removed': [], 'modified': [], 'other_changed_bytes': 1,
    }


@pytest.mark.parametrize('changes',[{True:2},{-1:1},{65536:1},{9999:1},{20:True},{20:100},{20:-1},{20:'3'},{20:7,21:100},{20:7,60:1000}])
def test_invalid_batch_is_atomic(changes):
    s=CS4Save(synthetic_demo_save());before=s.bytes()
    with pytest.raises((ValueError,TypeError)):s.set_quantities(changes)
    assert s.bytes()==before


@pytest.mark.parametrize('offset,value',[(0,2),(4,1),(8,0),(12,0),(TABLE_OFFSET+4,1)])
def test_corrupt_header_crc_and_record_rejected(offset,value):
    data=bytearray(synthetic_demo_save());data[offset]=value
    if offset==TABLE_OFFSET+4:refresh_crc(data)
    with pytest.raises(SaveFormatError):CS4Save(bytes(data))


def test_cs3_save_rejected_even_if_crc_is_valid():
    raw=bytearray(0x1402c0);raw[:8]=struct.pack('<II',2,1)
    raw[8:12]=len(raw).to_bytes(4,'little');refresh_crc(raw)
    with pytest.raises(SaveFormatError):CS4Save(bytes(raw))


def test_duplicate_items_and_noncontiguous_inventory_rejected():
    raw=bytearray(synthetic_demo_save());raw[TABLE_OFFSET+32:TABLE_OFFSET+34]=raw[TABLE_OFFSET:TABLE_OFFSET+2]
    with pytest.raises(SaveFormatError):CS4Save(refresh_crc(raw))
    raw=bytearray(synthetic_demo_save());at=TABLE_OFFSET+30*32;raw[at:at+4]=struct.pack('<HH',65530,1)
    with pytest.raises(SaveFormatError):CS4Save(refresh_crc(raw))


def test_cs3_only_id_ban_is_not_reused():
    s=CS4Save(synthetic_demo_save());s.set_quantity(249,1)
    assert CS4Save(s.bytes()).get_quantity(249)==1


def test_capacity_failure_preserves_original():
    raw=bytearray(synthetic_demo_save())
    for slot in range(RECORD_COUNT-16):
        at=TABLE_OFFSET+slot*32;raw[at:at+32]=struct.pack('<HH',slot,1)+bytes(28)
    s=CS4Save(refresh_crc(raw));before=s.bytes()
    with pytest.raises(ValueError):s.set_quantity(65000,1)
    assert s.bytes()==before


def test_public_real_cs4_regression_sample(tmp_path):
    path=Path(os.environ.get('CS4_REFERENCE_SAVE',Path(__file__).resolve().parents[3]/'save-converters/tests/test_files/cold_steel_iv/SAVE.pc'))
    if not path.is_file():pytest.skip('Set CS4_REFERENCE_SAVE to a private test save; no real saves are distributed')
    raw=path.read_bytes();s=CS4Save(raw)
    assert len(s.items())==1024
    assert int.from_bytes(raw[12:16],'little')==0xfc048ca4
    assert s.bytes()==raw
    s.set_quantities({0:65,60:1,65534:1})
    target=tmp_path/'edited.dat';target.write_bytes(s.bytes())
    assert CS4Save.from_file(target).get_quantity(0)==65
    assert get_diff_summary(raw,target.read_bytes())['other_changed_bytes']==0
    assert path.read_bytes()==raw
