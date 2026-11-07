from pathlib import Path
import argparse, json, hashlib
import soundfile as sf
import numpy as np
parser=argparse.ArgumentParser(); parser.add_argument('--source-dir',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[2]; out=root/'assets/audio';out.mkdir(parents=True,exist_ok=True)
inputs=[
 ('HomeMusic','wintery-loop.wav','Emma_MA','https://opengameart.org/content/wintery-loop',.11),
 ('GameMusic','magic-puzzle.ogg','MintoDog','https://opengameart.org/content/magic-puzzle-in-game-1',.10),
 ('SlideSound','swish/swishes/swish-1.wav','artisticdude','https://opengameart.org/content/swishes-sound-pack',.28),
 ('EdgeSound','swish/swishes/swish-7.wav','artisticdude','https://opengameart.org/content/swishes-sound-pack',.38),
 ('SplashSound','water/splash_01.ogg','rubberduck','https://opengameart.org/content/40-cc0-water-splash-slime-sfx',.42),
 ('HomeSound','rpg/OGG/handleCoins.ogg','Kenney','https://opengameart.org/content/50-rpg-sound-effects',.30),
 ('ClickSound','rpg/OGG/bookFlip1.ogg','Kenney','https://opengameart.org/content/50-rpg-sound-effects',.22),
]
items=[]
for name,file,author,url,peak in inputs:
 source=args.source_dir/file; data,rate=sf.read(source,always_2d=True); data=data.mean(axis=1)
 if name=='HomeSound':
  # A gentle rising triad accompanies the sourced metallic sparkle.
  length=max(len(data),int(rate*1.2)); mixed=np.zeros(length);mixed[:len(data)]=data*.25
  for i,f in enumerate([523.25,659.25,783.99]):
   t=np.arange(int(rate*.75))/rate; tone=np.sin(2*np.pi*f*t)*np.exp(-t*6)*(1-np.exp(-t*100))*.2
   start=int(i*.15*rate); mixed[start:start+len(tone)]+=tone[:min(len(tone),length-start)]
  data=mixed
 data=data/(max(abs(data).max(),1e-9))*peak
 path=out/(name+'.wav');sf.write(path,data,rate,subtype='PCM_16')
 items.append({'name':name,'file':path.relative_to(root).as_posix(),'original':file,'author':author,'source':url,'license':'CC0-1.0','rate':rate,'frames':len(data),'duration':round(len(data)/rate,3),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'processing':'Mono PCM16; level adjusted. HomeSound includes an original rising sine triad.'})
(out/'manifest.json').write_text(json.dumps({'sounds':items},ensure_ascii=False,indent=2)+'\n')
print([(i['name'],i['duration']) for i in items])
