import asyncio,tempfile
from matchterm.app import MatchtermApp
from matchterm.storage import Store
from textual.widgets import TabbedContent,Tabs
async def test():
 with tempfile.TemporaryDirectory() as folder:
  st=Store(folder);app=MatchtermApp(st)
  async with app.run_test(size=(140,42)) as pilot:
   await pilot.pause(.6);await pilot.click('#play');await pilot.pause(.6);assert st.state['match']['phase']=='prematch';await pilot.click('#play');await pilot.pause(.6);assert st.state['match']['phase']=='live';await pilot.click('#finish');await pilot.pause(.6);assert st.state['match']['phase']=='finished'
   app.action_season();await pilot.pause(.6);await pilot.click('#cancel');await pilot.pause(.6);assert len(st.state['results'])<380
   app.action_season();await pilot.pause(.6);await pilot.click('#yes');await pilot.pause(.6);assert len(st.state['results'])==380;assert app.query_one(TabbedContent).active=='table-tab'
   app.query_one(TabbedContent).active='players-tab';await pilot.pause(.6);panel=app.query_one('#player-scroll');assert app.focused is panel;before=panel.scroll_y;await pilot.press('down','down','down');await pilot.pause(.6);assert panel.scroll_y>before
   app.query_one(TabbedContent).active='results-tab';await pilot.pause(.6);results=app.query_one('#results');assert app.focused is results;await pilot.press(*(['down']*35));await pilot.pause(.6);assert results.cursor_row==35;assert results.scroll_y>0;app.refresh_tables();assert results.cursor_row==35
   results.move_cursor(row=0);await pilot.press('up');await pilot.pause(.6);assert isinstance(app.focused,Tabs)
   await pilot.press('left');await pilot.pause(.6);assert app.query_one(TabbedContent).active=='players-tab';assert isinstance(app.focused,Tabs)
   await pilot.press('down');await pilot.pause(.6);assert app.focused is panel
   panel.scroll_home(animate=False);await pilot.press('down','down');await pilot.pause(.6);assert panel.scroll_y>0
   panel.scroll_home(animate=False);await pilot.press('up');await pilot.pause(.6);assert isinstance(app.focused,Tabs)
   await pilot.press('right');await pilot.pause(.6);assert app.query_one(TabbedContent).active=='results-tab';await pilot.press('down');await pilot.pause(.6);assert app.focused is results
   await pilot.press('left','left');await pilot.pause(.6);assert app.query_one(TabbedContent).active=='table-tab' 
   app.action_new();await pilot.pause(.6);assert st.state['match'] is None
   await pilot.resize_terminal(95,30);await pilot.pause(.6);app.action_play();await pilot.pause(.6);assert st.state['match']['phase']=='prematch'
  st.close()
 print('PASS: UI load/start/finish, confirmation cancel/accept, complete season, reset, resize.')
asyncio.run(test())
