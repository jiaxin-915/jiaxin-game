"""Generate XBuilder metadata and code-native UI from the phase-2 level.

User images are copied byte-for-byte; this script never crops or recolors them.
UI is authored as SVG, rendered to PNG by render_ui.cjs for engine portability.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import struct

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'game/project'
UI = ROOT / 'game/ui-source'
LEVELS = [json.loads(path.read_text()) for path in sorted((ROOT / 'game/levels').glob('level-*.json'))]
SPRITES = []
RENDER = []


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def uid(name):
    return hashlib.sha256(('penguin-home-journey:' + name).encode()).hexdigest()[:20]


def png_size(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    return struct.unpack('>II', data[16:24])


def svg(width, height, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width*3}" height="{height*3}" viewBox="0 0 {width} {height}">
<defs>
 <linearGradient id="ice" x2="0.8" y2="1"><stop stop-color="#f8fdff"/><stop offset="1" stop-color="#d6ecfa"/></linearGradient>
 <linearGradient id="blue" x2="0" y2="1"><stop stop-color="#d8effd"/><stop offset="1" stop-color="#9fcce7"/></linearGradient>
 <linearGradient id="gold" x2="0" y2="1"><stop stop-color="#fff0c2"/><stop offset="1" stop-color="#f7d681"/></linearGradient>
 <linearGradient id="water" x2="0" y2="1"><stop stop-color="#61afc5"/><stop offset="1" stop-color="#378da8"/></linearGradient>
</defs>{body}</svg>'''


def text(x, y, value, size=12, anchor='middle', color='#456488'):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-family="Arial Rounded MT Bold,DejaVu Sans,sans-serif" font-weight="bold" font-size="{size}">{value}</text>'


def pill(x, y, w, h, fill='ice'):
    return f'<rect x="{x}" y="{y+2}" width="{w}" height="{h}" rx="{h/2}" fill="#7da8bd" opacity=".2"/><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="url(#{fill})" stroke="#f2fcff" stroke-width="1"/>'


def button(cx, cy, symbol):
    body = f'<rect x="{cx-20}" y="{cy-17}" width="40" height="40" rx="12" fill="#86b6d2"/>'
    body += f'<rect x="{cx-20}" y="{cy-20}" width="40" height="40" rx="12" fill="url(#blue)" stroke="#effaff" stroke-width="1.5"/>'
    body += f'<path d="M {cx-14},{cy-14} Q {cx-5},{cy-19} {cx+1},{cy-15} T {cx+15},{cy-14}" fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"/>'
    points = {'up': '0,-8 -8,6 8,6', 'down': '0,8 -8,-6 8,-6', 'left': '-8,0 6,-8 6,8', 'right': '8,0 -6,-8 -6,8'}
    body += f'<polygon points="{points[symbol]}" transform="translate({cx},{cy+2})" fill="#f7fcff" stroke="#78a4c2" stroke-width="1" stroke-linejoin="round"/>'
    return body


def costume(name, filename, width, height, pivot=None):
    return {'name': name, 'path': filename, 'x': (pivot or (width/2, height/2))[0], 'y': (pivot or (width/2, height/2))[1],
            'bitmapResolution': 1, 'imageWidth': width, 'imageHeight': height, 'faceRight': 0, 'builder_id': uid(filename+name)}


def add_sprite(name, costumes, x=0, y=0, size=1, visible=False, script=None):
    directory = PROJECT / 'assets/sprites' / name
    directory.mkdir(parents=True, exist_ok=True)
    config = {'heading': 90, 'x': x, 'y': y, 'size': size, 'rotationStyle': 'none', 'physicsMode': 'no',
              'costumeIndex': 0, 'visible': visible, 'isDraggable': False,
              'collisionPivot': {'x': 0, 'y': 0}, 'collisionShapeType': 'rect', 'collisionShapeParams': [1, 1],
              'costumes': costumes, 'fAnimations': {}, 'animBindings': {}, 'builder_id': uid(name)}
    write_json(directory / 'index.json', config)
    if script is not None:
        (PROJECT / (name+'.spx')).write_text(script)
    SPRITES.append(name)
    return directory


def plain_visibility(condition):
    return 'onMsg "frame", => {\n    if '+condition+' { show } else { hide }\n}\n'


def raster_sprite(name, source, x=0, y=0, size=1, visible=False, pivot=None, script=None):
    w,h=png_size(source)
    d=add_sprite(name,[costume('default','art.png',w,h,pivot)],x,y,size,visible,script)
    shutil.copy2(source,d/'art.png')


def vector_sprite(name, body, width, height, condition, x=0, y=0):
    UI.mkdir(parents=True, exist_ok=True)
    src=UI/(name+'.svg'); src.write_text(svg(width,height,body))
    dst=add_sprite(name,[costume('default','art.png',width*3,height*3)],x,y,1/3,script=plain_visibility(condition))/'art.png'
    RENDER.append({'source':str(src.relative_to(ROOT)),'output':str(dst.relative_to(ROOT))})


def level_visibility(level):
    return f'Screen != 0 && Level == {level}'



def interactive(condition, width, height):
    return '''var baseScale float64
onStart => { baseScale = size }
onMsg "frame", => {
    if baseScale == 0 { baseScale = size }
    if '''+condition+''' {
        show
        if pointerInside(mouseX, mouseY, xpos, ypos, '''+str(width)+'''*baseScale, '''+str(height)+'''*baseScale) { setSize(baseScale * 1.06) } else { setSize baseScale }
    } else { hide; setSize baseScale }
}
'''


def ui(name,body,w,h,x,y,condition,clickable=False):
    vector_sprite(name,body,w,h,condition,x,y)
    if clickable: (PROJECT/(name+'.spx')).write_text(interactive(condition,w*3,h*3))


def label_button(name,label,w,x,y,condition,fill='ice'):
    ui(name,pill(2,2,w-4,34,fill)+text(w/2,24,label,12),w,40,x,y,condition,True)


def main():
    # Recreate only generated assets/scripts; gameplay files are preserved.
    for path in (PROJECT/'assets/sprites').iterdir():
        if path.is_dir(): shutil.rmtree(path)
    for path in PROJECT.glob('*.spx'):
        if path.name not in ['main.spx','Penguin.spx']: path.unlink()
    for path in UI.glob('*.svg'): path.unlink()
    assert len(LEVELS) == 5
    kinds={'.':0,'P':0,'#':1,'~':2,'H':3}
    for level in LEVELS:
        grid=level['grid']
        assert level['columns'] == 6 and level['rows'] == 5
        assert len(grid) == 5 and all(len(row) == 6 for row in grid)
        assert sum(row.count('P') for row in grid) == sum(row.count('H') for row in grid) == 1
    code=(PROJECT/'main.spx').read_text()
    generated='// LEVEL-DATA-BEGIN (generated from game/levels/level-*.json)\n'
    for index, level in enumerate(LEVELS, 1):
        grid=level['grid']; cells=[kinds[ch] for row in grid for ch in row]
        start=next((c,r) for r,row in enumerate(grid) for c,ch in enumerate(row) if ch=='P')
        if index == 1:
            generated += f'    if Level == {index} {{\n'
        elif index < len(LEVELS):
            generated += f'    }} else if Level == {index} {{\n'
        else:
            generated += '    } else {\n'
        generated += '        LevelCells = [30]int{'+','.join(map(str,cells))+'}\n'
        generated += f'        Col = {start[0]}\n        Row = {start[1]}\n'
    generated += '    }\n'
    generated += '    // LEVEL-DATA-END'
    (PROJECT/'main.spx').write_text(re.sub(r'// LEVEL-DATA-BEGIN.*?// LEVEL-DATA-END',generated,code,flags=re.S))
    background=ROOT/'assets/derived/ocean-pastel.png'; shutil.copy2(background,PROJECT/'assets/ocean.png'); bw,bh=png_size(background)
    play='Screen != 0'; active='Screen == 1'; result='(Screen == 2 || Screen == 3) && EndTime >= 0.35'
    # Each tile remains an independent editable sprite. Each level has its own set.
    for level in LEVELS:
      number=level['id']; grid=level['grid']
      for r,row in enumerate(grid):
        for c,ch in enumerate(row):
            if ch=='~':
                body='<rect x="1" y="1" width="44" height="44" rx="8" fill="url(#water)"/><path d="M 6,22 q 9,-6 17,0 t 17,0 M 7,32 q 9,-5 17,0" stroke="#94d3df" stroke-width="1.2" fill="none" opacity=".5"/>'
            else:
                body='<rect x="1" y="4" width="44" height="44" rx="8" fill="#90c3db"/><rect x="1" y="1" width="44" height="43" rx="8" fill="url(#ice)" stroke="#f6fdff" stroke-width="1.2"/><path d="M 8,8 L 25,8" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity=".55"/>'
            name=('WaterTile' if ch=='~' else 'IceTile')+f'L{number}'+str(r*6+c)
            ui(name,body,46,50,-189+c*46,73-r*46,level_visibility(number))
      for r,row in enumerate(grid):
        for c,ch in enumerate(row):
            if ch=='#': raster_sprite(f'RockL{number}'+str(r*6+c),ROOT/'assets/source/ice-rock.png',-189+c*46,75-r*46,0.056,pivot=(627,630),script=plain_visibility(level_visibility(number)))
            if ch=='H': raster_sprite(f'IglooL{number}',ROOT/'assets/source/igloo-goal.png',-189+c*46,75-r*46,0.052,pivot=(627,600),script=plain_visibility(level_visibility(number)))
    raster_sprite('Penguin',ROOT/'assets/derived/penguin-front.png',-189,-109,0.040)
    ui('GameTitle',pill(2,2,174,49)+text(89,22,'Penguin',17)+text(89,41,'Home Journey',16),178,54,-135,141,play)
    for level in LEVELS:
        ui(f'LevelLabel{level["id"]}',pill(2,2,68,28)+text(36,21,f'Level {level["id"]}',12),72,34,-2,146,level_visibility(level['id']))
    ui('MovesLabel',pill(2,2,80,28)+text(42,12,'Moves',8),84,34,82,146,play)
    home=pill(2,2,36,36)+'<path d="M 11,21 l 9,-9 9,9 v 10 h -6 v -7 h -6 v 7 h -6 z" fill="#577b9d"/>'
    # Match the retry mark's visual weight to the neighbouring home mark.
    retry=pill(2,2,36,36)+'<path d="M 28,17 A 9.5,9.5 0 1,0 29.5,23.5" stroke="#577b9d" fill="none" stroke-width="2.8" stroke-linecap="round"/><path d="M 28,11 v 6 h -6" fill="none" stroke="#577b9d" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>'
    ui('HomeButton',home,40,42,145,146,active,True)
    ui('RetryButton',retry,40,42,200,146,active,True)
    ui('GoalHint',text(70,18,'Find your way',14)+text(70,37,'back home.',14),140,44,145,69,play)
    ui('SlideHint',text(70,15,'Slide until an',10)+text(70,30,'ice rock stops you.',10),140,36,145,22,play)
    for name,direction,x,y in [('UpButton','up',145,-25),('LeftButton','left',101,-69),('RightButton','right',189,-69),('DownButton','down',145,-113)]:
        ui(name,button(24,24,direction),48,50,x,y,active,True)
    ui('RuleHint',pill(2,2,280,20)+text(142,16,'Use ice rocks to stop. Reach the igloo.',9.5),284,26,-80,-160,play)
    for digit in range(8):
        name='MoveDigit'+str(digit); costumes=[]
        for value in range(10):
            src=UI/f'digit-{value}.svg'; src.write_text(svg(10,18,text(5,14,str(value),13)))
            out=PROJECT/'assets/sprites'/name/f'{value}.png'
            RENDER.append({'source':str(src.relative_to(ROOT)),'output':str(out.relative_to(ROOT))})
            costumes.append(costume(str(value),f'{value}.png',30,54))
        divisor=10**digit
        script=f'onMsg "frame", => {{\n    if Screen == 0 || (Moves < {divisor} && {digit} > 0) {{ hide; return }}\n    setCostume((Moves / {divisor}) % 10)\n    show\n}}\n'
        # Leave a clear title/value gap inside the Moves pill.
        add_sprite(name,costumes,x=82-digit*9,y=144,size=1/3,script=script)
    ui('ResultShade','<rect width="480" height="360" fill="#d7eff5" opacity=".72"/>',480,360,0,0,result)
    ui('ResultPanel',pill(2,2,310,150),314,156,0,-1,result)
    for level in LEVELS:
        if level['id'] < 5:
            title='Home at last!'; subtitle=f'Level {level["id"]} complete.'
        else:
            title='Journey complete!'; subtitle='Every penguin is home.'
        ui(f'WinMessage{level["id"]}',text(150,28,title,24)+text(150,55,subtitle,11),300,66,0,35,f'Screen == 3 && Level == {level["id"]} && EndTime >= 0.35')
    ui('WaterMessage',text(150,28,'Splash!',24)+text(150,55,'Watch the water between the ice.',11),300,66,0,35,'Screen == 2 && FallKind == 2 && EndTime >= 0.35')
    ui('EdgeMessage',text(150,28,'Off the ice!',24)+text(150,55,'Use an ice rock to stop safely.',11),300,66,0,35,'Screen == 2 && FallKind == -1 && EndTime >= 0.35')
    label_button('ResultRetryButton','Retry',116,64,-45,'Screen == 2 && EndTime >= 0.35','gold')
    label_button('NextButton','Next Level',116,64,-45,'Screen == 3 && Level < 5 && EndTime >= 0.35','gold')
    label_button('AgainButton','Play Again',116,64,-45,'Screen == 3 && Level == 5 && EndTime >= 0.35','gold')
    label_button('ResultHomeButton','Home',116,-64,-45,result)
    source=ROOT/'assets/derived/cover-no-start.png'; cw,ch=png_size(source)
    raster_sprite('HomeCover',source,size=480/cw,visible=True,script=plain_visibility('Screen == 0'))
    raster_sprite('StartButton',ROOT/'assets/source/start-button.png',-2,-133,size=0.074,visible=True,script=interactive('Screen == 0',*png_size(ROOT/'assets/source/start-button.png')))
    # Sound toggle remains accessible on every screen; text reflects actual state.
    label_button('SoundOnButton','Sound: On',92,180,-151,'!Muted')
    label_button('SoundOffButton','Sound: Off',92,180,-151,'Muted')
    sound_ids=[]
    audio=json.loads((ROOT/'assets/audio/manifest.json').read_text())
    for item in audio['sounds']:
        folder=PROJECT/'assets/sounds'/item['name']; folder.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/item['file'],folder/'audio.wav')
        sid=uid('sound:'+item['name']); sound_ids.append(sid)
        write_json(folder/'index.json',{'path':'audio.wav','rate':item['rate'],'sampleCount':item['frames'],'builder_id':sid})
    stage={'backdrops':[{'name':'Arctic','path':'ocean.png','x':bw/2,'y':bh/2,'imageWidth':bw,'imageHeight':bh,'bitmapResolution':1,'builder_id':uid('Arctic')}],
           'backdropIndex':0,'map':{'width':480,'height':360,'mode':'fillRatio'},'run':{'width':480,'height':360},'camera':{'on':''},
           'physics':False,'stretchMode':True,'maxFPS':60,'audioAttenuation':0,'audioMaxDistance':768,
           'zorder':SPRITES,'builder_spriteOrder':[uid(s) for s in SPRITES],'builder_soundOrder':sound_ids,'fontPreferences':['default']}
    write_json(PROJECT/'assets/index.json',stage)
    meta=json.loads((ROOT/'game/platform-text.json').read_text()); write_json(PROJECT/'builder-meta.json',meta)
    shutil.copy2(ROOT/'assets/source/cover.png',PROJECT/'builder-thumbnail.png')
    write_json(ROOT/'game/ui-source/render-manifest.json',RENDER)
    print(f'Generated {len(SPRITES)} independent sprites and {len(sound_ids)} sounds.')


if __name__=='__main__': main()
