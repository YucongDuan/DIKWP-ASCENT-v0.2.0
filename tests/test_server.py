import json
import threading
import time
import http.client
from pathlib import Path
import pytest
from dikwp_ascent.server import make_server, ResearchService
from dikwp_ascent.canonical import Invalid

@pytest.fixture
def server(tmp_path):
    s=make_server(tmp_path/'web',0)
    t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
    yield s
    s.shutdown();s.server_close();t.join(timeout=5)


def request(server,method,path,body=None,token=True,headers=None):
    conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
    h={'Content-Type':'application/json'}
    if token:h['X-ASCENT-Token']=server.service.token
    h.update(headers or {})
    conn.request(method,path,body=json.dumps(body) if body is not None else None,headers=h)
    r=conn.getresponse();status=r.status;raw=r.read();hh=dict(r.getheaders());conn.close()
    return status,raw,hh


def test_console_served_and_csp(server):
    code,body,headers=request(server,'GET','/',token=False)
    assert code==200 and b'ASCENT' in body
    assert "frame-ancestors 'none'" in headers['Content-Security-Policy']
    assert headers['Cache-Control']=='no-store'


def test_api_requires_token(server):
    assert request(server,'GET','/api/status',token=False)[0]==403


def test_dns_rebinding_host_rejected(server):
    assert request(server,'GET','/',token=False,headers={'Host':'malicious.example'})[0]==403


def test_cross_origin_rejected(server):
    assert request(server,'POST','/api/stop',{'reason':'evil'},headers={'Origin':'https://malicious.example'})[0]==403


def test_unknown_command_rejected(server):
    assert request(server,'POST','/api/shell',{'command':'echo hi'})[0]==404


def test_wrong_input_does_not_execute(server):
    code,body,_=request(server,'POST','/api/run',{'task':'periodic','seed':17,'cmd':'echo bad'})
    assert code==400 and not server.service.busy


def test_local_run_complete_and_stop(server):
    code,body,_=request(server,'POST','/api/run',{'task':'periodic','seed':17})
    assert code==200
    ident=json.loads(body)['job_id']
    deadline=time.monotonic()+15
    while time.monotonic()<deadline and server.service.busy:time.sleep(.05)
    jobs=server.service.job_snapshot()['jobs']
    assert jobs[-1]['id']==ident and jobs[-1]['status']=='COMPLETED'
    assert jobs[-1]['decision']=='REVIEWABLE'
    assert request(server,'POST','/api/stop',{'reason':'test stop'})[0]==200
    state=json.loads(request(server,'GET','/api/status')[1]);assert state['stopped']


def test_fresh_unknown_directory_preserved(tmp_path):
    p=tmp_path/'existing';p.mkdir();(p/'file').write_text('keep')
    with pytest.raises(Invalid):ResearchService(p)
    assert (p/'file').read_text()=='keep'
