import argparse
import os
import time
from pathlib import Path
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, RichLog, Select, Static, TabbedContent, TabPane, Tabs
from . import engine as E
from .storage import Store

class Confirm(ModalScreen[bool]):
    CSS='''Confirm { align: center middle; background: $background 70%; } #confirm-box { width: 64; height: auto; border: heavy #8abf98; padding: 1 2; background: #102018; } #confirm-buttons { height: 3; align: center middle; }'''
    BINDINGS=[('escape','cancel','Cancel')]
    def __init__(self,message):super().__init__();self.message=message
    def compose(self):
        with Vertical(id='confirm-box'):
            yield Static(self.message)
            with Horizontal(id='confirm-buttons'):
                yield Button('Cancel',id='cancel');yield Button('Continue',id='yes',variant='success')
    def on_button_pressed(self,event):self.dismiss(event.button.id=='yes')
    def action_cancel(self):self.dismiss(False)


class Commentary(ModalScreen):
    CSS='''Commentary { align: center middle; background: $background 70%; } #saved-commentary { width: 90%; height: 85%; background: #102018; border: solid #8abf98; padding: 1; } #saved-log { height: 1fr; }'''
    BINDINGS=[('escape','close','Close')]
    def __init__(self,events):super().__init__();self.events=events
    def compose(self):
        with Vertical(id='saved-commentary'):
            yield RichLog(id='saved-log',wrap=True);yield Button('Close',id='close-commentary')
    def on_mount(self):
        for e in self.events:self.query_one('#saved-log',RichLog).write(f"{MatchtermApp.clock(e['t'])}  {e['text']}")
    def action_close(self):self.dismiss()
    def on_button_pressed(self,event):self.dismiss()

class MatchtermApp(App):
    TITLE='MATCHTERM'
    SUB_TITLE='2026/27 · Offline terminal edition'
    CSS='''Screen { background: #080e0b; color: #b4eac3; } Header, Footer { background: #12251a; } TabbedContent { height: 1fr; } ContentSwitcher { height: 1fr; } TabPane { height: 1fr; padding: 0; } Tabs { background: #102018; } #club { width: 40; margin: 0 1; } #top { height: 4; } #score { height: 4; padding: 1 2; border-bottom: solid #365443; color: #e8c780; text-style: bold; } #live { height: 1fr; } #commentary { width: 2fr; border: solid #365443; margin: 1; } #match-stats { width: 1fr; min-width: 27; border: solid #365443; padding: 1; margin: 1; } #buttons { height: auto; min-height: 3; } Button { margin: 0 1; min-width: 12; } #hint { height: auto; padding: 0 1; color: #799989; } DataTable { height: 1fr; } #record { height: auto; padding: 1; color: #e8c780; } .leader { height: auto; min-height: 8; border: solid #365443; margin: 1; padding: 1; } #speed-label { width: 16; padding: 1; }'''
    BINDINGS=[Binding('left','navigate_tabs(-1)','Previous tab',show=False,priority=True),Binding('right','navigate_tabs(1)','Next tab',show=False,priority=True),Binding('up','vertical_nav(-1)','Up',show=False,priority=True),Binding('down','vertical_nav(1)','Down',show=False,priority=True),Binding('space','play','Load / Start'),Binding('f','finish','Sim to FT'),Binding('s','season','Sim season'),Binding('n','new','New season'),Binding('1','speed(1)','1×',show=False),Binding('2','speed(2)','2×',show=False),Binding('4','speed(4)','4×',show=False),Binding('e','export','Export'),Binding('q','quit','Save / Quit')]
    def __init__(self,store):super().__init__();self.store=store;self.state=store.state;self.speed=1;self.last=time.monotonic();self.logged=0;self.ticks=0;self.busy=False;self.results_count=-1;self.nav_focus=False
    def compose(self)->ComposeResult:
        yield Header()
        with Horizontal(id='top'):
            yield Select([(c,c) for c in E.CLUBS],value=self.state['club'],allow_blank=False,id='club')
            yield Static('SPEED 1×',id='speed-label')
        with TabbedContent(initial='match'):
            with TabPane('MATCH',id='match'):
                yield Static(id='score')
                with Horizontal(id='live'):
                    yield RichLog(id='commentary',wrap=True,markup=False,highlight=False)
                    yield Static(id='match-stats')
                with Horizontal(id='buttons'):
                    yield Button('Play next match',id='play',variant='success');yield Button('Sim to full time',id='finish');yield Button('Sim whole season',id='season');yield Button('New season',id='new')
                yield Static(id='hint')
            with TabPane('TABLE',id='table-tab'):
                yield Static(id='record');yield DataTable(id='table',cursor_type='row',zebra_stripes=True)
            with TabPane('PLAYER STATS',id='players-tab'):
                with VerticalScroll(id="player-scroll"):
                    for k in ['goals','assists','yellow','red']:yield Static(id='leader-'+k,classes='leader')
            with TabPane('MATCH RESULTS',id='results-tab'):
                yield DataTable(id='results',cursor_type='row',zebra_stripes=True)
        yield Footer()
    def content_target(self):
        pane=self.query_one(TabbedContent).active
        return self.query_one({'match':'#commentary','table-tab':'#table','players-tab':'#player-scroll','results-tab':'#results'}[pane])
    def check_action(self,action,parameters):
        if action in ('navigate_tabs','vertical_nav'):
            if isinstance(self.screen,ModalScreen) or isinstance(self.focused,Select):return False
        return True
    def on_tabbed_content_tab_activated(self,event):
        if self.nav_focus:
            self.query_one(Tabs).focus();self.nav_focus=False
        else:self.content_target().focus()
    def action_navigate_tabs(self,step):
        panes=['match','table-tab','players-tab','results-tab'];tabs=self.query_one(TabbedContent)
        self.nav_focus=isinstance(self.focused,Tabs)
        tabs.active=panes[(panes.index(tabs.active)+step)%len(panes)]
    def action_vertical_nav(self,step):
        target=self.content_target()
        if isinstance(self.focused,Tabs):
            if step>0:target.focus()
            return
        target.focus()
        if isinstance(target,DataTable):
            if step<0 and target.cursor_row==0:self.query_one(Tabs).focus()
            elif step>0:target.action_cursor_down()
            else:target.action_cursor_up()
        elif step<0 and target.scroll_y<=0:self.query_one(Tabs).focus()
        elif step>0:target.scroll_down(animate=False)
        else:target.scroll_up(animate=False)
    def on_mount(self):
        self.query_one('#table',DataTable).add_columns('#','Club','P','W','D','L','GD','PTS')
        self.query_one('#results',DataTable).add_columns('Date','Home','Score','Away')
        self.refresh_view(full=True);self.set_interval(.2,self.tick)
        self.query_one('#commentary',RichLog).border_title='MATCH COMMENTARY'
        self.query_one('#match-stats',Static).border_title='MATCH STATISTICS'
    def persist(self):self.store.state=self.state;self.store.save()
    def refresh_view(self,full=False):
        m=self.state['match'];index=m['fixture'] if m else E.next_fixture(self.state);f=E.FIXTURES[index] if index is not None else None
        self.query_one('#club',Select).disabled=bool(m or self.state['results'])
        complete=len(self.state['results'])==380
        self.query_one('#play',Button).disabled=complete or bool(m and m['phase']=='live') or (E.next_fixture(self.state) is None and not(m and m['phase']=='prematch'))
        self.query_one('#play',Button).label='Start match' if m and m['phase']=='prematch' else 'Play next match'
        self.query_one('#finish',Button).disabled=not m or m['phase']=='finished'
        self.query_one('#season',Button).disabled=complete
        self.query_one('#new',Button).display=complete
        clock='PRE-MATCH' if not m or m['phase']=='prematch' else 'FULL TIME' if m['phase']=='finished' else self.clock(m['elapsed'])
        if f:
            score=m['score'] if m else [0,0]
            self.query_one('#score',Static).update(f"{f['h'].upper()}  {score[0]} - {score[1]}  {f['a'].upper()}\n{f['date']} · {f['time']} UK   |   {clock}")
            stats=m['stats'] if m else {k:[0,0] for k in ['shots','target','corners','fouls','yellow','red','free','xg','touches']}
            t=Table(expand=True,box=None,padding=(0,1));t.add_column('');t.add_column(f['h']+(' (YOU)' if f['h']==self.state['club'] else ''),justify='right');t.add_column(f['a']+(' (YOU)' if f['a']==self.state['club'] else ''),justify='right')
            touch=stats['touches'];p=round(100*touch[0]/sum(touch)) if sum(touch) else 50;t.add_row('Possession',str(p)+'%',str(100-p)+'%')
            for key,name in [('shots','Shots'),('target','On target'),('corners','Corners'),('fouls','Fouls'),('yellow','Yellow'),('red','Red'),('free','Free kicks'),('xg','xG')]:t.add_row(name,*[f'{v:.2f}' if key=='xg' else str(v) for v in stats[key]])
            self.query_one('#match-stats',Static).update(t)
        log=self.query_one('#commentary',RichLog)
        if full:log.clear();self.logged=0
        if m:
            for e in m['log'][self.logged:]:log.write(Text(f"{self.clock(e['t'])}  {e['text']}",style='bold #e8c780' if e.get('outcome')=='goal' else '#e8a4a4' if e['kind']=='red' else '#e4cf74' if e['kind']=='yellow' else '#b4eac3'))
            self.logged=len(m['log'])
        elif full:log.write('> Select your club, then load the next match. Kickoff waits for Start match.')
        self.query_one('#hint',Static).update('Season complete. Review all results, export, or start a new season.' if complete else 'Autosaved locally · Space: load/start · F: finish current match · S: whole season (confirmation)')
        if full:self.refresh_tables()
    @staticmethod
    def clock(seconds):
        sec=int(seconds);return f'90+{(sec-5400)//60}:{sec%60:02d}' if sec>=5400 else f'{sec//60:02d}:{sec%60:02d}'
    def refresh_tables(self):
        rows=E.standings(self.state);table=self.query_one('#table',DataTable);table.clear()
        for i,r in enumerate(rows):table.add_row(str(i+1),r['club']+(' ◀' if r['club']==self.state['club'] else ''),*[str(r[k]) for k in ['p','w','d','l']],str(r['gf']-r['ga']),str(r['pts']))
        own=next(r for r in rows if r['club']==self.state['club']);self.query_one('#record',Static).update(f"{self.state['club']} · {own['pts']} PTS · P {own['p']} / W {own['w']} / D {own['d']} / L {own['l']} · GF {own['gf']} / GA {own['ga']}")
        if len(self.state['results'])!=self.results_count:
            results=self.query_one('#results',DataTable);results.clear()
            for key,r in sorted(self.state['results'].items(),key=lambda x:int(x[0])):
                f=E.FIXTURES[int(key)];results.add_row(f['date'],f['h'],' - '.join(map(str,r['score'])),f['a'],key=key)
            self.results_count=len(self.state['results'])
        for key,title in [('goals','TOP GOAL SCORERS'),('assists','MOST ASSISTS'),('yellow','YELLOW CARDS'),('red','RED CARDS')]:
            t=Table(title=title,expand=True,box=None);t.add_column('Player');t.add_column('Club');t.add_column('#',justify='right')
            leaders=sorted((p for p in self.state['players'].values() if p[key]),key=lambda p:(-p[key],p['name']))[:10]
            for p in leaders:t.add_row(p['name'],p['club'],str(p[key]))
            if not leaders:t.add_row('None recorded yet','','')
            self.query_one('#leader-'+key,Static).update(t)
    def tick(self):
        now=time.monotonic();dt=min(now-self.last,1);self.last=now
        if self.busy or not self.state['match'] or self.state['match']['phase']!='live':return
        old=self.state['match']['phase'];events=E.advance(self.state,dt*30*self.speed);self.ticks+=1
        if events or self.ticks%5==0:self.persist()
        self.refresh_view()
        if events:self.refresh_tables()
    def action_play(self):
        m=self.state['match']
        if m and m['phase']=='live':return
        if m and m['phase']=='prematch':E.start(self.state)
        else:E.prepare(self.state)
        self.last=time.monotonic();self.persist();self.refresh_view(full=True)
    def action_finish(self):E.finish(self.state);self.persist();self.refresh_view(full=True)
    def action_season(self):
        if len(self.state['results'])==380:return
        self.push_screen(Confirm('Are you sure you want to continue with simulating the whole season?\n\nThis finishes the current match and all remaining fixtures. Existing results stay fixed.'),self.confirm_season)
    def confirm_season(self,yes):
        if yes:self.busy=True;E.simulate_season(self.state);self.persist();self.busy=False;self.refresh_view(full=True);self.call_after_refresh(self.show_table)
    def show_table(self):
        self.query_one(TabbedContent).active='table-tab'
        self.query_one('#table',DataTable).focus()
    def action_new(self):
        if len(self.state['results'])==380:
            self.store.new(self.state['club']);self.state=self.store.state;self.logged=0;self.refresh_view(full=True);self.query_one(TabbedContent).active='match'
    def action_speed(self,speed):self.speed=speed;self.query_one('#speed-label',Static).update(f'SPEED {speed}×')
    def action_export(self):self.notify(f'Exported: {self.store.export()}',timeout=8)
    def action_quit(self):self.persist();self.exit()
    def on_button_pressed(self,event):
        actions={'play':self.action_play,'finish':self.action_finish,'season':self.action_season,'new':self.action_new}
        if event.button.id in actions:actions[event.button.id]()
    def on_select_changed(self,event):
        if event.select.id=='club' and event.value!=Select.BLANK and not self.state['match'] and not self.state['results']:
            self.state['club']=event.value;self.persist();self.refresh_view(full=True)
    def on_data_table_row_selected(self,event):
        if event.data_table.id=='results':
            key=str(event.row_key.value);self.push_screen(Commentary(self.state['results'][key]['log']))

def main():
    parser=argparse.ArgumentParser(description='MATCHTERM terminal edition');parser.add_argument('--save-folder',type=Path,help='Override the local save location');parser.add_argument('--open-save-folder',action='store_true');args=parser.parse_args()
    store=Store(args.save_folder)
    if args.open_save_folder:
        if os.name=='nt':os.startfile(store.folder)
        else:print(store.folder)
        store.close();return
    try:MatchtermApp(store).run()
    finally:store.close()

if __name__=='__main__':main()
