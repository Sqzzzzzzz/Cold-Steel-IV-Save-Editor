import sys
import os
import struct
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
os.environ.setdefault('QT_QPA_PLATFORM','windows' if os.name=='nt' else 'offscreen')


@pytest.fixture
def ng_plus_save_bytes():
    from cs4_save import CS4Save, TABLE_OFFSET, RECORD_SIZE, save_checksum
    from preview_demo import synthetic_demo_save

    raw = synthetic_demo_save()
    data = bytearray(raw)
    material = next(item for item in CS4Save(raw).items() if item.item_id == 60)
    struct.pack_into('<H', data, TABLE_OFFSET + material.slot * RECORD_SIZE + 2, 268)
    # The carryover inventory starts at this offset in real NISA PC NG+ saves.
    for slot, (item_id, quantity) in enumerate(((20, 80), (60, 238), (3229, 1))):
        struct.pack_into('<HH', data, 0x46F1C + slot * RECORD_SIZE, item_id, quantity)
    struct.pack_into('<I', data, 12, save_checksum(data))
    return bytes(data)
