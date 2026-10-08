import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .engine import fresh

def save_folder():
    if os.name=='nt':return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData'/'Local'))/'MATCHTERM'
    return Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local'/'share'))/'MATCHTERM'

class Store:
    def __init__(self,folder=None):
        self.folder=Path(folder) if folder else save_folder();self.folder.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.folder/'seasons.sqlite3');self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS seasons(id INTEGER PRIMARY KEY, created TEXT NOT NULL, state TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0)')
        self.db.execute('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)');self.db.commit()
        row=self.db.execute("SELECT value FROM settings WHERE key='active'").fetchone()
        if row:
            self.id=int(row[0]);data=self.db.execute('SELECT state,revision FROM seasons WHERE id=?',(self.id,)).fetchone();self.state=json.loads(data[0]);self.revision=data[1]
            if self.state.get('schema')!=1:raise RuntimeError('This save was made by an unsupported version. Your database has been left intact.')
        else:self.new('Arsenal')
    def save(self):
        with self.db:
            result=self.db.execute('UPDATE seasons SET state=?,revision=revision+1 WHERE id=? AND revision=?',(json.dumps(self.state),self.id,self.revision))
            if result.rowcount!=1:raise RuntimeError('This season was changed in another app window. Close this window and reopen the game.')
        self.revision+=1
    def new(self,club):
        if hasattr(self,'state'):
            self.save()
            backup=sqlite3.connect(self.folder/'seasons-backup.sqlite3');self.db.backup(backup);backup.close()
        self.state=fresh(club)
        with self.db:
            cur=self.db.execute('INSERT INTO seasons(created,state) VALUES (?,?)',(datetime.now(timezone.utc).isoformat(),json.dumps(self.state)))
            self.id=cur.lastrowid;self.revision=0
            self.db.execute("INSERT OR REPLACE INTO settings VALUES ('active',?)",(str(self.id),))
    def export(self):
        path=self.folder/f'season-{self.id}.json';path.write_text(json.dumps(self.state,ensure_ascii=False,indent=2),encoding='utf-8');return path
    def close(self):self.db.close()
