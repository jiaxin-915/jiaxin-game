"""Validate resources and build/check the reproducible XBuilder ZIP package."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import argparse
import hashlib
import json
import struct
import wave
import re

ROOT=Path(__file__).resolve().parents[2]
PROJECT=ROOT/'game/project'
PACKAGE=ROOT/'game/Penguin-Home-Journey-v0.3.3.xbp'

def validate():
    read=lambda p:json.loads(p.read_text())
    stage=read(PROJECT/'assets/index.json')
    assert stage['run']=={'width':480,'height':360}
    assert stage['physics'] is False
    names=[]; ids=[]
    for folder in sorted((PROJECT/'assets/sprites').iterdir()):
        if not folder.is_dir(): continue
        name=folder.name; names.append(name)
        conf=read(folder/'index.json'); ids.append(conf['builder_id'])
        assert (PROJECT/(name+'.spx')).is_file(), name
        assert conf['physicsMode']=='no'
        for costume in conf['costumes']:
            p=(folder/costume['path']).resolve()
            assert p.is_relative_to(PROJECT.resolve()) and p.is_file(), str(p)
            data=p.read_bytes(); assert data[:8]==b'\x89PNG\r\n\x1a\n', str(p)
            assert struct.unpack('>II',data[16:24])==(costume['imageWidth'],costume['imageHeight']), str(p)
    assert len(ids)==len(set(ids)) and set(ids)==set(stage['builder_spriteOrder'])
    assert set(names)==set(stage['zorder']) and len(names)==len(stage['zorder'])
    for b in stage['backdrops']: assert (PROJECT/'assets'/b['path']).is_file()
    assert read(PROJECT/'builder-meta.json')['type']=='game'
    assert (PROJECT/'builder-thumbnail.png').is_file()
    source=(PROJECT/'main.spx').read_text()
    fields = re.findall(r'^\s*(\w+)\s+(?:\[.*?\])?(?:int|bool|float64|string)\b', source.split('// CORE-BEGIN')[0], re.M)
    conflicts = set(fields) & set(names)
    assert not conflicts, f'Stage fields conflict with sprite classes: {sorted(conflicts)}'
    sound_ids=[]
    sound_names=set()
    for folder in (PROJECT/'assets/sounds').iterdir():
        conf=read(folder/'index.json'); sound_ids.append(conf['builder_id']); sound_names.add(folder.name)
        with wave.open(str(folder/conf['path'])) as wav:
            assert wav.getframerate()==conf['rate'] and wav.getnframes()==conf['sampleCount']
            assert wav.getsampwidth()==2 and wav.getnframes()>0
    assert len(sound_ids)==len(set(sound_ids)) and set(sound_ids)==set(stage['builder_soundOrder'])
    referenced=set(re.findall(r'(?:play|stopPlaying) "([^"]+)"',source))
    assert referenced<=sound_names, referenced-sound_names
    assert 'inBox(' not in source, 'Buttons must use object hit detection'
    assert 'Board' not in names and 'Hud' not in names and 'Cover' not in names
    assert len([n for n in names if n.startswith(('IceTile','WaterTile'))]) == 150
    assert len([n for n in names if n.startswith('LevelLabel')]) == 5
    assert {'StartButton','UpButton','DownButton','LeftButton','RightButton','HomeCover','NextButton','AgainButton'} <= set(names)
    meta=read(PROJECT/'builder-meta.json')
    assert all(any('\u4e00'<=c<='\u9fff' for c in meta[key]) for key in ['description','instructions'])
    for marker in ['QAScenario','QAHUD','QACapacity']: assert marker not in source
    for p in PROJECT.glob('*.spx'):
        s=p.read_text(); event=s.find('onStart')
        assert 'mouseHitItem' not in s, f'Unsupported production API in {p.name}'
        # No CJK text is allowed in runtime scripts in this English-only build.
        assert not any('\u4e00'<=c<='\u9fff' for c in s),str(p)
    files={p.relative_to(PROJECT).as_posix():p.read_bytes() for p in PROJECT.rglob('*') if p.is_file()}
    return files,len(names)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    files,sprites=validate()
    if not args.check:
        with ZipFile(PACKAGE,'w',compression=ZIP_DEFLATED) as z:
            for name,data in sorted(files.items()):
                info=ZipInfo(name,(1980,1,1,0,0,0)); info.compress_type=ZIP_DEFLATED; info.external_attr=0o644<<16
                z.writestr(info,data)
    with ZipFile(PACKAGE) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        assert set(z.namelist())==set(files) and z.testzip() is None
        for name,data in files.items(): assert z.read(name)==data,name
    print(f'PASS: {sprites} sprites, {len(files)} files; archive equals source byte-for-byte.')
    print('SHA256',hashlib.sha256(PACKAGE.read_bytes()).hexdigest())

if __name__=='__main__': main()
