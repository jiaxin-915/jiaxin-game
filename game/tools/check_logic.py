"""Execute the production SPX core as Go (no rewritten movement algorithm)."""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
TEST=r'''
package main
import "testing"

type levelCase struct { level int; moves [][2]int; expected int }
var levelCases []levelCase

func settle(t *testing.T) {
    t.Helper()
    for i:=0; i<200 && Moving; i++ { advance(0.017) }
    if Moving { t.Fatal("movement did not settle") }
}

// Independent cell-scanning oracle checks the animated implementation's outcomes.
func oracle(c,r,dx,dy int) (int,int,int,bool) {
    moved:=false
    for i:=0;i<8;i++ {
        nc,nr:=c+dx,r+dy
        if nc<0||nc>=6||nr<0||nr>=5 {return nc,nr,2,true}
        k:=LevelCells[nr*6+nc]
        if k==1 {return c,r,1,moved}
        c,r=nc,nr; moved=true
        if k==2 {return c,r,2,true}
        if k==3 {return c,r,3,true}
    }
    panic("oracle did not settle")
}

func TestAllCellsDirectionsAndFrameRates(t *testing.T) {
    dirs:=[][2]int{{0,-1},{0,1},{-1,0},{1,0}}
    for _,level:=range levelCases { for _,dt:=range []float64{0.004,0.016,0.033,0.05,0.8} {
        for r:=0;r<5;r++ {for c:=0;c<6;c++ {
            for _,d:=range dirs {
                Level=level.level; resetLevel(); if tileAt(c,r)!=0 {continue}
                Col=c; Row=r; PlayerX=cellX(c); PlayerY=cellY(r)
                ec,er,es,accepted:=oracle(c,r,d[0],d[1])
                if requestMove(d[0],d[1])!=accepted {t.Fatal("acceptance mismatch",c,r,d)}
                for n:=0;n<1000&&Moving;n++ {advance(dt)}
                if Moving||Col!=ec||Row!=er||Screen!=es {t.Fatal("outcome mismatch",c,r,d,dt,Col,Row,Screen,ec,er,es)}
                expected:=0; if accepted {expected=1}
                if Moves!=expected {t.Fatal("one slide must count exactly once")}
            }
        }}
    }}
}

func TestDocumentedSolutions(t *testing.T) {
    for _,level:=range levelCases { Level=level.level; resetLevel()
    for _,d:=range level.moves {
        if !requestMove(d[0],d[1]) {t.Fatal("solution step rejected")}; settle(t)
    }
    if Screen!=3||Moves!=level.expected {t.Fatal("solution failed",level.level,Screen,Moves,Col,Row)}
    if requestMove(1,0) {t.Fatal("won state accepted movement")}
    advance(10)
    if Moves!=level.expected||Screen!=3 {t.Fatal("terminal score changed")}
    }
}

func TestBusyResetHomeAndInvalidInput(t *testing.T) {
    Level=3; resetLevel(); requestMove(0,1); advance(0.05)
    if requestMove(1,0)||Moves!=1 {t.Fatal("mid-slide input accepted")}
    resetLevel(); advance(1)
    if Moving||Moves!=0||Level!=3||PlayerX!=cellX(Col)||PlayerY!=cellY(Row)||InputReady {t.Fatal("reset retained motion/input")}
    if requestMove(1,1)||requestMove(0,0)||requestMove(2,0) {t.Fatal("invalid direction accepted")}
    goHome(); if requestMove(0,-1)||Screen!=0 {t.Fatal("home accepted movement")}
}

func TestLevelProgression(t *testing.T) {
    Level=1; resetLevel(); nextLevel()
    if Level!=2||Screen!=1||Moves!=0 {t.Fatal("next level failed")}
    Level=5; resetLevel(); nextLevel()
    if Level!=1||Screen!=0 {t.Fatal("final level did not return home")}
}

var audioEvents []string
func recordPlay(name string, loop bool) { audioEvents=append(audioEvents,"play:"+name) }
func recordStop(name string) { audioEvents=append(audioEvents,"stop:"+name) }
func plays(name string) int { n:=0;for _,e:=range audioEvents {if e=="play:"+name {n++}};return n }
func TestPointerFollowsObject(t *testing.T) {
    if !pointerInside(10,20,10,20,40,30) {t.Fatal("center miss")}
    if pointerInside(31,20,10,20,40,30) {t.Fatal("outside accepted")}
    if pointerInside(10,20,110,120,40,30) {t.Fatal("old position still clickable")}
    if !pointerInside(110,120,110,120,40,30) {t.Fatal("new position miss")}
    if pointerInside(135,120,110,120,40,30) {t.Fatal("outside normal size")}
    if !pointerInside(135,120,110,120,80,60) {t.Fatal("scaled bounds miss")}
    if pointerInside(0,0,0,0,0,0) {t.Fatal("zero size accepted")}
}

func TestAudioTransitions(t *testing.T) {
    audioEvents=nil; Muted=false; AudioScreen=-1; AudioMoves=0; AudioMoving=false
    goHome(); syncAudio(); syncAudio()
    if plays("HomeMusic")!=1 {t.Fatal("home loop duplicated")}
    Level=3; resetLevel(); syncAudio(); syncAudio()
    if plays("GameMusic")!=1 {t.Fatal("game loop duplicated")}
    requestMove(0,1); syncAudio(); syncAudio()
    if plays("SlideSound")!=1 {t.Fatal("movement sound duplicated")}
    settle(t); syncAudio(); requestMove(0,0); syncAudio()
    if plays("SlideSound")!=1 {t.Fatal("invalid move emitted sound")}
    Level=3; resetLevel(); Col=4;Row=3; requestMove(0,-1);advance(.8);syncAudio();syncAudio()
    if plays("SplashSound")!=1||plays("EdgeSound")!=0 {t.Fatal("water event routing")}
    Level=1; resetLevel(); Col=5;Row=0; syncAudio();requestMove(1,0);advance(.8);syncAudio();syncAudio()
    if plays("EdgeSound")!=1 {t.Fatal("edge event routing")}
    Level=1; resetLevel();syncAudio();requestMove(0,-1);settle(t);syncAudio();requestMove(1,0);settle(t);syncAudio();requestMove(0,-1);settle(t);syncAudio();requestMove(1,0);settle(t);syncAudio();requestMove(0,-1);settle(t);syncAudio()
    if plays("HomeSound")!=1 {t.Fatal("win sound duplicated")}
    n:=len(audioEvents);Muted=true;goHome();syncAudio()
    if len(audioEvents)!=n {t.Fatal("muted audio emitted event")}
    Muted=false;AudioScreen=-1;syncAudio();syncAudio()
    if plays("HomeMusic")!=2 {t.Fatal("unmute did not resume once")}
}

func TestShortestSolutionByBFS(t *testing.T) {
    type node struct{c,r,steps int}
    for _,level:=range levelCases { Level=level.level; resetLevel(); q:=[]node{{Col,Row,0}}; seen:=map[[2]int]bool{{Col,Row}:true}
    shortest:=-1
    for len(q)>0&&shortest<0 {
        at:=q[0]; q=q[1:]
        for _,d:=range [][2]int{{0,-1},{0,1},{-1,0},{1,0}} {
            Level=level.level; resetLevel(); Col=at.c; Row=at.r
            if !requestMove(d[0],d[1]) {continue}; settle(t)
            if Screen==3 {shortest=at.steps+1;break}
            key:=[2]int{Col,Row}
            if Screen==1&&!seen[key] {seen[key]=true;q=append(q,node{Col,Row,at.steps+1})}
        }
    }
    if shortest!=level.expected {t.Fatal("wrong shortest solution",level.level,shortest,level.expected)}
    t.Log("Shortest verified route",level.level,level.expected,"moves")
    }
}
'''

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--go',default='go'); args=parser.parse_args()
    code=(ROOT/'game/project/main.spx').read_text()
    declarations=code[code.index('var ('):code.index('// CORE-BEGIN')]
    core=code.split('// CORE-BEGIN:',1)[1].split('\n',1)[1].split('// CORE-END',1)[0]
    audio=code[code.index('func syncAudio()'):code.index('\nonStart =>')]
    audio=re.sub(r'play "([^"]+)"(?:, (true|false))?',lambda m:'recordPlay("'+m[1]+'", '+(m[2] or 'false')+')',audio)
    audio=re.sub(r'stopPlaying "([^"]+)"',r'recordStop("\1")',audio)
    core += '\n'+audio
    levels=[json.loads(path.read_text()) for path in sorted((ROOT/'game/levels').glob('level-*.json'))]
    kinds={'.':0,'P':0,'#':1,'~':2,'H':3}
    arrays=re.findall(r'LevelCells = \[30\]int\{([^}]+)\}',core)
    assert len(arrays)==len(levels)==5, 'Expected five generated level arrays'
    for index,(actual,level) in enumerate(zip(arrays,levels),1):
        assert [int(x) for x in actual.split(',')] == [kinds[x] for row in level['grid'] for x in row], f'SPX map differs from level {index}'
    directions={'up':(0,-1),'down':(0,1),'left':(-1,0),'right':(1,0)}
    cases='var levelCases = []levelCase{'+','.join('{'+str(level['id'])+',[][2]int{'+','.join('{'+str(directions[d][0])+','+str(directions[d][1])+'}' for d in level['solution'])+'},'+str(level['expected_moves'])+'}' for level in levels)+'}\n'
    with tempfile.TemporaryDirectory(prefix='penguin-core-') as temp:
        tmp=Path(temp)
        (tmp/'go.mod').write_text('module penguin-core-check\n\ngo 1.22\n')
        (tmp/'core.go').write_text('package main\n'+declarations+core)
        (tmp/'core_test.go').write_text(TEST.replace('var levelCases []levelCase',cases))
        env=dict(os.environ,GOCACHE=str(ROOT/'game/.test-work/go-cache'),GOTOOLCHAIN='local',GOPROXY='off')
        result=subprocess.run([args.go,'test','-v','-count=1'],cwd=tmp,env=env,text=True,capture_output=True)
        print(result.stdout,end=''); print(result.stderr,end='')
        raise SystemExit(result.returncode)

if __name__=='__main__': main()
