"""Event-driven simulation; all match events are locked before kickoff."""
import json
import math
import random
from importlib.resources import files

FIXTURES = json.loads(files('matchterm').joinpath('data/fixtures.json').read_text())
SQUADS = json.loads(files('matchterm').joinpath('data/squads.json').read_text())
CLUBS = sorted(SQUADS)
RATINGS = {'Arsenal':91,'Liverpool':89,'Manchester City':90,'Chelsea':86,'Manchester United':83,'Newcastle United':84,'Aston Villa':83,'Tottenham Hotspur':82}
ROLES = json.loads(files('matchterm').joinpath('data/roles.json').read_text())
FORWARDS, KEEPERS = set(ROLES['forwards']), set(ROLES['keepers'])

def role(p):
    return 'G' if p['name'] in KEEPERS else 'F' if p['name'] in FORWARDS else 'D' if 2 <= p['number'] <= 6 else 'M'

def fresh(club='Arsenal'):
    return {'schema':1,'club':club,'cursor':0,'results':{},'players':{},'match':None,'season':'2026/27'}

def pick(rng, club, kind, exclude=()):
    pool=[p for p in SQUADS[club] if p['name'] not in exclude and role(p)!='G']
    weights = {'goal':{'F':8,'M':1.4,'D':.3},'assist':{'F':3,'M':4,'D':1},'card':{'F':1,'M':2.5,'D':4},'pass':{'F':2,'M':4,'D':1}}[kind]
    return rng.choices(pool,weights=[weights[role(p)] for p in pool])[0]['name']

def next_fixture(state):
    return next((i for i,f in enumerate(FIXTURES) if i>=state['cursor'] and state['club'] in (f['h'],f['a'])),None)

def generate(index, seed=None):
    rng=random.Random(seed); f=FIXTURES[index]; names=[f['h'],f['a']]
    delta=RATINGS.get(f['h'],76)-RATINGS.get(f['a'],76)
    home_share=max(.32,min(.7,.56+delta/100))
    events=[]
    def add(t,kind,side,text,**extra):
        events.append({'t':t,'kind':kind,'side':side,'text':text,**extra})
    add(0,'system',0,'KICK OFF — '+f['h']+' v '+f['a'])
    t=110
    while t<5480:
        side=0 if rng.random()<home_share else 1; club=names[side]; z=rng.random()
        if z<.25:
            other=1-side; offender=pick(rng,names[other],'card')
            add(t,'foul',other,f'FOUL — {offender} ({names[other]}) stops the runner.',player=offender)
            if rng.random()<.25: add(t+7,'yellow',other,f'YELLOW CARD — {offender} ({names[other]}).',player=offender)
            if rng.random()<.018: add(t+9,'red',other,f'RED CARD — {offender} ({names[other]}) · dangerous challenge.',player=offender)
            if rng.random()<.06:
                add(t+20,'penalty',side,f'PENALTY — {club}. Ball on the spot…')
                xg=.76
            else:
                taker=pick(rng,club,'assist'); add(t+20,'free',side,f'FREE KICK — {taker} ({club}).',player=taker); xg=.09 if rng.random()<.5 else None
        elif z<.43:
            taker=pick(rng,club,'assist');add(t,'corner',side,f'CORNER — {taker} ({club}) delivers.',player=taker);xg=.09
        elif z<.78:
            passer=pick(rng,club,'pass');add(t,'attack',side,f'{passer} ({club}) moves into the final third…',player=passer);xg=.08+rng.random()*.18
        else:
            passer=pick(rng,club,'pass');add(t,'quiet',side,f'{passer} ({club}) keeps possession and looks for a pass.',player=passer);xg=None
        if xg is not None:
            scorer=pick(rng,club,'goal');u=rng.random();outcome='goal' if u<xg else 'save' if u<xg+.34 else 'wide'
            assist=None
            if outcome=='goal':
                if xg!=.76 and rng.random()>.18: assist=pick(rng,club,'assist',[scorer])
                text=f'GOAL — {scorer} ({club})'+(f' · Assist: {assist}' if assist else '')+'.'
            else:
                keeper=next((p['name'] for p in SQUADS[names[1-side]] if role(p)=='G'),'the goalkeeper')
                text=f'SHOT — {scorer} ({club}) · '+(f'saved by {keeper}.' if outcome=='save' else 'wide of the post.')
            add(t+65,'shot',side,text,player=scorer,assist=assist,xg=xg,outcome=outcome)
        t+=rng.randint(110,340)
    for t,kind,side,text in [(2700,'system',0,'HALF TIME'),(2760,'system',0,'SECOND HALF — play resumes.'),(5400,'system',0,'90 MINUTES — four added minutes.'),(5640,'full',0,'FULL TIME — result committed.')]: add(t,kind,side,text)
    # Resolve dismissals in order, then ensure sent-off players cannot appear again.
    events.sort(key=lambda e:e['t']);sent=[set(),set()];yellow=[{},{}]
    for e in events:
        side=e['side'];club=names[side]
        if e.get('player') in sent[side]:
            old=e['player'];new=pick(rng,club,'goal' if e['kind']=='shot' else 'card' if e['kind'] in ('yellow','red','foul') else 'pass',sent[side]);e['player']=new;e['text']=e['text'].replace(old,new)
        if e.get('assist') and (e['assist'] in sent[side] or e['assist']==e.get('player')):
            e['assist']=pick(rng,club,'assist',sent[side]|{e['player']})
            e['text']=e['text'].split(' · Assist:')[0]+f" · Assist: {e['assist']}."
        if e['kind']=='yellow':
            p=e['player'];yellow[side][p]=yellow[side].get(p,0)+1
            if yellow[side][p]>=2:
                e['second_yellow']=True;sent[side].add(p);e['text']+=' RED CARD — second yellow.'
        if e['kind']=='red':sent[side].add(e['player'])
    return {'fixture':index,'phase':'prematch','elapsed':0,'index':0,'events':events,'log':[],'score':[0,0],'stats':{k:[0,0] for k in ['shots','target','corners','fouls','yellow','red','free','xg','touches']}}

def player_stat(state,club,name):
    return state['players'].setdefault(club+'|'+name,{'name':name,'club':club,'goals':0,'assists':0,'yellow':0,'red':0})

def reveal(state,m,e):
    m['log'].append(e);side=e['side'];kind=e['kind'];stats=m['stats'];club=FIXTURES[m['fixture']]['h' if side==0 else 'a']
    if kind=='shot':
        stats['shots'][side]+=1;stats['xg'][side]+=e['xg']
        if e['outcome'] in ('goal','save'):stats['target'][side]+=1
        if e['outcome']=='goal':
            m['score'][side]+=1;player_stat(state,club,e['player'])['goals']+=1
            if e.get('assist'):player_stat(state,club,e['assist'])['assists']+=1
    key={'foul':'fouls','corner':'corners','free':'free','yellow':'yellow','red':'red'}.get(kind)
    if key:stats[key][side]+=1
    if kind in ('yellow','red'):player_stat(state,club,e['player'])[kind]+=1
    if e.get('second_yellow'):stats['red'][side]+=1;player_stat(state,club,e['player'])['red']+=1
    if kind in ('attack','quiet','shot','corner','free'):stats['touches'][side]+=1

def finish_one(state,m):
    if str(m['fixture']) in state['results']:return
    while m['index']<len(m['events']):
        e=m['events'][m['index']];m['index']+=1;reveal(state,m,e)
    m['elapsed']=5640;m['phase']='finished';state['results'][str(m['fixture'])]={'score':m['score'][:],'log':m['log'][:],'stats':m['stats']}

def catch_up(state,index):
    for i in range(state['cursor'],index):
        if str(i) not in state['results']:finish_one(state,generate(i))
    state['cursor']=index+1

def prepare(state):
    if state['match'] and state['match']['phase']!='finished':return
    i=next_fixture(state)
    if i is not None:state['match']=generate(i)

def start(state):
    m=state['match']
    if m and m['phase']=='prematch':m['phase']='live';advance(state,0)

def advance(state,seconds):
    m=state['match']
    if not m or m['phase']!='live':return []
    m['elapsed']=min(5640,m['elapsed']+seconds);new=[]
    while m['index']<len(m['events']) and m['events'][m['index']]['t']<=m['elapsed']:
        e=m['events'][m['index']];m['index']+=1;reveal(state,m,e);new.append(e)
    if m['elapsed']>=5640:
        finish_one(state,m);catch_up(state,m['fixture'])
    return new

def finish(state):
    m=state['match']
    if m and m['phase']!='finished':finish_one(state,m);catch_up(state,m['fixture'])

def simulate_season(state):
    finish(state)
    for i in range(len(FIXTURES)):
        if str(i) in state['results']:continue
        m=generate(i);finish_one(state,m)
        if state['club'] in (FIXTURES[i]['h'],FIXTURES[i]['a']):state['match']=m
    state['cursor']=len(FIXTURES)

def standings(state):
    rows={c:{'club':c,'p':0,'w':0,'d':0,'l':0,'gf':0,'ga':0,'pts':0} for c in CLUBS}
    for key,result in state['results'].items():
        f=FIXTURES[int(key)];g=result['score']
        for side,club in enumerate([f['h'],f['a']]):
            r=rows[club];a,b=g[side],g[1-side];r['p']+=1;r['gf']+=a;r['ga']+=b;r['w' if a>b else 'd' if a==b else 'l']+=1;r['pts']+=3 if a>b else 1 if a==b else 0
    return sorted(rows.values(),key=lambda r:(-r['pts'],-(r['gf']-r['ga']),-r['gf'],r['club']))
