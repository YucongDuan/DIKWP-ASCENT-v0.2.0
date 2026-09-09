import sys, threading, json, tempfile, time, http.client, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from dikwp_ascent.server import make_server
from playwright.sync_api import sync_playwright
OUT=ROOT/'validation'
OUT.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    server=make_server(Path(tmp)/'controller',0)
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    errors=[];requests=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:requests.append(r.url))
            base=f'http://127.0.0.1:{server.server_port}'
            def local_request(path, body=None):
                conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=15)
                headers={'X-ASCENT-Token':server.service.token,'Content-Type':'application/json','Origin':base}
                conn.request('GET' if body is None else 'POST',path,body=None if body is None else json.dumps(body),headers=headers)
                response=conn.getresponse();raw=response.read();status=response.status;conn.close()
                return {'code':status,'payload':json.loads(raw)}
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port)
            conn.request('GET','/');content=conn.getresponse().read().decode();conn.close()
            start=content.index('async function api(');end=content.index('\nfunction message',start)
            content=content[:start]+"async function api(path,body){const r=await window.ASCENT_TEST_REQUEST(path,body);if(r.code!==200)throw Error(r.payload.message||r.payload.error);return r.payload}"+content[end:]
            page.expose_function('ASCENT_TEST_REQUEST',local_request)
            page.set_content(content,wait_until='domcontentloaded')
            page.click('#run')
            page.wait_for_function("document.querySelector('#runs').children.length===1",timeout=30000)
            page.click('#runs button')
            page.wait_for_function("document.querySelector('#decision').textContent==='REVIEWABLE'",timeout=10000)
            page.click('#approve');page.wait_for_function("!document.querySelector('#activate').disabled")
            page.click('#activate');page.wait_for_function("document.querySelector('#activeCount').textContent==='1'",timeout=10000)
            page.click('#infer');page.wait_for_function("document.querySelector('#inferenceOutput').textContent.includes('0.397302')",timeout=10000)
            page.screenshot(path=str(OUT/'ASCENT_CONSOLE_v0.2.0.png'),full_page=True)
            assert page.locator('#task option').count()==5
            page.select_option('#task',value='quadratic',timeout=3000);page.fill('#seed','17');page.click('#run')
            page.wait_for_function("document.querySelector('#runs').children.length===2",timeout=30000)
            buttons=page.locator('#runs tr')
            for i in range(buttons.count()):
                row=buttons.nth(i)
                if row.locator('td').first.inner_text()=='quadratic':row.locator('button').click()
            page.wait_for_function("document.querySelector('#decision').textContent==='NOT_PROMOTABLE'")
            assert page.locator('#approve').is_disabled()
            page.click('#stop');page.wait_for_function("document.querySelector('#health').textContent==='STOPPED'")
            assert page.locator('#run').is_disabled()
            page.click('#infer');page.wait_for_function("document.querySelector('#inferenceOutput').textContent.includes('stop')")
            page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(OUT/'ASCENT_MOBILE_v0.2.0.png'),full_page=True)
            overflow=page.evaluate('document.documentElement.scrollWidth>window.innerWidth')
            browser.close()
        results={'actual_loopback_navigation':False,'browser_navigation_limit':'ERR_BLOCKED_BY_ADMINISTRATOR','ui_test_transport':'Identical served HTML except fetch wrapper replaced by Playwright binding to real HTTP backend; API and headers tested separately','page_errors':errors,'external_requests':[u for u in requests if not u.startswith(base)],'mobile_horizontal_overflow':overflow,'run':True,'inspect':True,'approval_then_activation':True,'actual_inference':True,'strong_reference_rejection':True,'stop_blocks_inference':True,'scope':'Chromium DOM rendering and UI state transitions via real local backend bridge; not direct-navigation or CSP enforcement proof'}
        (OUT/'browser.json').write_text(json.dumps(results,indent=2))
        print(json.dumps(results,indent=2))
    finally:
        server.shutdown();server.server_close();t.join(timeout=5)
