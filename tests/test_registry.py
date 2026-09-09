import copy
import json
import pytest
from dikwp_ascent.registry import Registry
from dikwp_ascent.engine import research
from dikwp_ascent.canonical import Invalid,Stopped

@pytest.fixture
def registry(tmp_path):
    r=Registry(tmp_path/"state",create=True)
    yield r
    r.close()

def run(r,seed=17):
    old=r.current("periodic")
    x=research("periodic",seed,incumbent_model=old["model"] if old else None,parent_version=old["version"] if old else None,stop_check=r.stopped,audit_register=r.claim_audit)["record"]
    r.store_run(x);return x

def test_full_lifecycle(registry):
    r=registry;x=run(r);ticket=r.approve(x["run_id"],"local-operator")
    p=r.promote(ticket)
    assert r.current("periodic")["version"]==p["version"]
    assert r.verify()["valid"]
    restored=r.rollback("periodic","Independent challenge requires review")
    assert restored["restored"] is None
    assert r.current("periodic") is None
    assert r.verify()["valid"]

def test_no_self_promotion(registry):
    x=run(registry)
    assert not registry.current("periodic")
    with pytest.raises(Invalid):registry.promote({"body":{"run_id":x["run_id"]},"mac":"bad"})

def test_approval_replay(registry):
    x=run(registry);ticket=registry.approve(x["run_id"],"reviewer")
    registry.promote(ticket)
    with pytest.raises(Invalid):registry.promote(ticket)
    assert registry.verify()["valid"]

def test_approval_expired(registry):
    x=run(registry);ticket=registry.approve(x["run_id"],"reviewer")
    with pytest.raises(Invalid):registry.promote(ticket,now=ticket["body"]["expires"])
    assert registry.current("periodic") is None

def test_approval_tamper(registry):
    x=run(registry);ticket=registry.approve(x["run_id"],"reviewer");ticket["body"]["scope"]="PAYMENT"
    with pytest.raises(Invalid):registry.promote(ticket)

def test_stop_revokes_ticket(registry):
    x=run(registry);ticket=registry.approve(x["run_id"],"reviewer")
    registry.stop("halt")
    with pytest.raises(Stopped):registry.promote(ticket)
    registry.resume("reviewer")
    with pytest.raises(Invalid):registry.promote(ticket)
    assert registry.verify()["valid"]

def test_no_implicit_restart(registry):
    registry.stop("halt")
    with pytest.raises(Stopped):run(registry)
    assert registry.stopped()

def test_holdout_reuse_rejected(registry):
    run(registry)
    with pytest.raises(Invalid,match="Holdout already"):run(registry)

def test_unregistered_demo_not_promotable(registry):
    x=research("periodic",17)["record"]
    with pytest.raises(Invalid,match="reservation"):registry.store_run(x)

def test_state_tampering_detected(registry):
    run(registry)
    registry.db.execute("UPDATE runs SET body='{}'")
    with pytest.raises(Invalid):registry.verify()

def test_history_truncation_detected(registry):
    run(registry)
    registry.db.execute("DELETE FROM events WHERE seq=(SELECT MAX(seq) FROM events)")
    with pytest.raises(Invalid):registry.verify()

def test_policy_fingerprint_tamper(registry,monkeypatch):
    x=run(registry);t=registry.approve(x["run_id"],"operator")
    monkeypatch.setattr("dikwp_ascent.registry.source_fingerprint",lambda:"changed")
    with pytest.raises(Invalid):registry.promote(t)

def test_second_ticket_stale_parent(registry):
    x=run(registry);a=registry.approve(x["run_id"],"a");b=registry.approve(x["run_id"],"b")
    registry.promote(a)
    with pytest.raises(Invalid,match="Incumbent changed"):registry.promote(b)

def test_invalid_reviewer(registry):
    x=run(registry)
    with pytest.raises(Invalid):registry.approve(x["run_id"],"")

def test_two_controller_connections_replay(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    path=tmp_path/"concurrent"
    r=Registry(path,create=True);x=run(r);t=r.approve(x["run_id"],"operator");r.close()
    def invoke(_):
        q=Registry(path)
        try:
            q.promote(t);return "promoted"
        except Invalid:return "rejected"
        finally:q.close()
    with ThreadPoolExecutor(max_workers=2) as ex:result=list(ex.map(invoke,range(2)))
    assert sorted(result)==["promoted","rejected"]
    q=Registry(path);assert q.verify()["valid"];q.close()

def test_failed_audit_still_consumed(registry):
    token=registry.claim_audit("a"*64)
    assert token
    with pytest.raises(Invalid):registry.claim_audit("a"*64)

def test_expired_ttl_rejected(registry):
    x=run(registry)
    with pytest.raises(Invalid):registry.approve(x["run_id"],"operator",ttl=0)
