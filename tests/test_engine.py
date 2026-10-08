import json
import tempfile
import unittest
from matchterm import engine as E
from matchterm.storage import Store
class EngineTests(unittest.TestCase):
 def test_resume(self):
  with tempfile.TemporaryDirectory() as folder:
   st=Store(folder);E.prepare(st.state);self.assertEqual(st.state['match']['phase'],'prematch');E.start(st.state);E.advance(st.state,600);locked=json.dumps(st.state['match']['events']);st.save();st.close();st=Store(folder);self.assertEqual(json.dumps(st.state['match']['events']),locked);E.finish(st.state);before=json.dumps(st.state);E.finish(st.state);self.assertEqual(before,json.dumps(st.state));st.close()
 def test_season(self):
  s=E.fresh();E.simulate_season(s);self.assertEqual(len(s['results']),380);self.assertTrue(all(r['p']==38 for r in E.standings(s)));goals=sum(sum(r['score']) for r in s['results'].values());self.assertEqual(goals,sum(p['goals'] for p in s['players'].values()));self.assertLessEqual(sum(p['assists'] for p in s['players'].values()),goals);self.assertFalse(any(p['goals'] and p['name'] in E.KEEPERS for p in s['players'].values()));before=json.dumps(s);E.simulate_season(s);self.assertEqual(before,json.dumps(s))
 def test_archive_and_concurrency(self):
  with tempfile.TemporaryDirectory() as folder:
   a=Store(folder);b=Store(folder);a.save()
   with self.assertRaises(RuntimeError):b.save()
   b.close();old=a.id;a.new('Chelsea');self.assertFalse(a.state['results']);self.assertTrue(a.db.execute('SELECT state FROM seasons WHERE id=?',(old,)).fetchone());a.close()
if __name__=='__main__':unittest.main()
