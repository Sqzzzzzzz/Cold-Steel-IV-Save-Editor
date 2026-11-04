"""Extract the 31 CS4 master textures from the owner's assets.pka, read-only.

PKA layout: AdmiralCurtiss/SenPatcher native/sen/pka.{h,cpp}.
Only the known DX11 BC7 master textures are accepted. Pillow is already required.
Game archives and unpacked members are never copied into the distribution.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from game_icons import CS4_MASTER_NAMES


def decode_lz4(data,expected):
    if not 0<expected<=4*1024*1024:raise ValueError('Invalid texture size')
    out=bytearray();pos=0
    def length(value):
        nonlocal pos
        if value==15:
            while True:
                if pos>=len(data):raise ValueError('Truncated LZ4 length')
                n=data[pos];pos+=1;value+=n
                if n<255:break
        return value
    while pos<len(data):
        token=data[pos];pos+=1;n=length(token>>4)
        if pos+n>len(data) or len(out)+n>expected:raise ValueError('Invalid LZ4 literal')
        out.extend(data[pos:pos+n]);pos+=n
        if pos==len(data):break
        if pos+2>len(data):raise ValueError('Truncated LZ4 distance')
        distance=int.from_bytes(data[pos:pos+2],'little');pos+=2
        n=length(token&15)+4
        if not 0<distance<=len(out) or len(out)+n>expected:raise ValueError('Invalid LZ4 match')
        for _ in range(n):out.append(out[-distance])
    if len(out)!=expected:raise ValueError('LZ4 size mismatch')
    return bytes(out)


def read_textures(path):
    wanted={f'I_3D_MQUARTZ{i:02}.pkg':(i,name) for i,name in enumerate(CS4_MASTER_NAMES)}
    members={};locations={}
    with Path(path).open('rb') as stream:
        size=stream.seek(0,2);stream.seek(0)
        def read(n):
            if not 0<=n<=4*1024*1024:raise ValueError('Invalid PKA read size')
            data=stream.read(n)
            if len(data)!=n:raise ValueError('Truncated PKA')
            return data
        magic,count=struct.unpack('<II',read(8))
        if magic!=0x7ff7cf0d or count>65536:raise ValueError('Unsupported PKA header')
        for _ in range(count):
            package=read(32).split(b'\0')[0].decode('ascii');n,=struct.unpack('<I',read(4))
            if n>4096:raise ValueError('Invalid PKA member count')
            if package not in wanted:
                if stream.tell()+n*96>size:raise ValueError('Truncated PKA package')
                stream.seek(n*96,1);continue
            index,name=wanted[package]
            for _ in range(n):
                row=read(96);filename=row[:64].split(b'\0')[0].decode('ascii')
                if filename==f'mqua{index:02}_conv.dds.phyre':
                    members[row[64:]]=(package,filename,name)
        count,=struct.unpack('<I',read(4))
        if count>1000000 or stream.tell()+count*52>size:raise ValueError('Invalid PKA file table')
        for _ in range(count):
            row=read(52)
            if row[:32] in members:locations[row[:32]]=struct.unpack_from('<QIII',row,32)
        if len(members)!=31 or members.keys()!=locations.keys():raise ValueError('Missing master textures')
        for digest,(package,filename,name) in members.items():
            offset,compressed,uncompressed,flags=locations[digest]
            if flags!=4 or offset+compressed>size:raise ValueError('Unsupported PKA texture compression')
            stream.seek(offset);data=decode_lz4(read(compressed),uncompressed)
            if hashlib.sha256(data).digest()!=digest:raise ValueError('PKA texture hash mismatch')
            yield name,package,filename,data


def decode_texture(data):
    if data[:4]!=b'RYHP' or data[12:16]!=b'11XD':raise ValueError('Unsupported Phyre platform')
    marker=b'PTexture2D\0BC7\0';pos=data.find(marker)
    if pos<8:raise ValueError('Expected a BC7 texture')
    width,height=struct.unpack_from('<II',data,pos-8)
    pixel_size=struct.unpack_from('<I',data,80)[0]
    if (width,height,pixel_size)!=(512,512,349552) or pixel_size>=len(data):
        raise ValueError('Unsupported master texture layout')
    image=Image.frombytes('RGBA',(width,height),data[-pixel_size:][:width*height],'bcn',7)
    return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def extract(path,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    manifest=destination/'sources.json'
    metadata=json.loads(manifest.read_text('utf-8')) if manifest.exists() else {'files':[]}
    files={row['file']:row for row in metadata['files']}
    for name,package,member,data in read_textures(path):
        target=destination/f'{name} (Sen IV MQ).png'
        image=decode_texture(data);image.save(target,format='PNG',optimize=True)
        files[target.name]={'file':target.name,'game':'Trails of Cold Steel IV',
            'dimensions':list(image.size),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'source_kind':'owner_game_texture','native_source':{'archive':'assets.pka',
            'package':package,'member':member,'member_sha256':hashlib.sha256(data).hexdigest(),
            'size':list(image.size),'format':'BC7','processing':'BC7 decode and vertical orientation correction'}}
    metadata['files']=[files[name] for name in sorted(files)]
    metadata['game']='Trails of Cold Steel III / IV'
    metadata['cs4_master_source']='31 original master textures from owner CS4 assets.pka; no generated artwork'
    manifest.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'icons/original')
    args=parser.parse_args();extract(args.archive,args.output)
    print('Extracted 31 verified CS4 master textures.')
