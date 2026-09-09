"""Trusted local controller. HMACs authenticate this installation, not civil identity.

No candidate executes Python. A same-OS-user adversary who can read the controller
key, replace code or access the DB is OUTSIDE this local trust boundary.
"""
from __future__ import annotations
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from .canonical import canonical,digest,Invalid,Stopped,integer
from .engine import verify_record,source_fingerprint
from .policy import CONTROL_DIGEST

class Registry:
    def __init__(self,workspace,create=False):
        self.root=Path(workspace).resolve()
        if create:
            self.root.mkdir(parents=True,exist_ok=True)
            keypath=self.root/"controller.key"
            if not keypath.exists():
                fd=os.open(keypath,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,"wb") as f:f.write(secrets.token_bytes(32))
        if not (self.root/"controller.key").is_file():raise Invalid("Run ascent init first")
        self.key=(self.root/"controller.key").read_bytes()
        if len(self.key)!=32:raise Invalid("Invalid controller key")
        self.db=sqlite3.connect(self.root/"registry.sqlite",timeout=5,isolation_level=None)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        if create:
            self.db.executescript('''
            CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY,body TEXT NOT NULL,used INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS versions(id TEXT PRIMARY KEY,task TEXT NOT NULL,run_id TEXT NOT NULL,parent TEXT,model TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_slots(id TEXT PRIMARY KEY,token TEXT NOT NULL,run_id TEXT);
            CREATE TABLE IF NOT EXISTS active(task TEXT PRIMARY KEY,version TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,body TEXT NOT NULL,prev TEXT NOT NULL,hash TEXT NOT NULL);
            ''')
            if self.db.execute("SELECT 1 FROM meta WHERE k='epoch'").fetchone() is None:
                self.db.execute("BEGIN IMMEDIATE")
                self.db.execute("INSERT INTO meta VALUES('epoch','0')")
                self.db.execute("INSERT INTO meta VALUES('stopped','false')")
                self._append("initialized",{"scope":"trusted-local-controller"})
                self.db.commit()
        self.verify()

    def close(self):self.db.close()
    def meta(self,key):
        r=self.db.execute("SELECT v FROM meta WHERE k=?",(key,)).fetchone()
        if r is None:raise Invalid("Missing controller state")
        return r[0]
    def stopped(self):return self.meta("stopped")=="true"
    def _mac(self,obj):return hmac.new(self.key,canonical(obj).encode(),hashlib.sha256).hexdigest()
    def _state(self):
        state={}
        for table,cols in (("audit_slots","id,token,run_id"),("runs","id,body"),("tickets","id,body,used"),("versions","id,task,run_id,parent,model"),("active","task,version")):
            state[table]=self.db.execute(f"SELECT {cols} FROM {table} ORDER BY 1").fetchall()
        state["control"]={"epoch":self.meta("epoch"),"stopped":self.meta("stopped")}
        return digest(state)
    def _append(self,kind,payload):
        row=self.db.execute("SELECT seq,hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        seq,prev=(row[0]+1,row[1]) if row else (1,"0"*64)
        body={"seq":seq,"kind":kind,"payload":payload,"state_digest":self._state()}
        d=digest({"prev":prev,"body":body})
        self.db.execute("INSERT INTO events VALUES(?,?,?,?)",(seq,canonical(body),prev,d))
        head={"seq":seq,"hash":d,"state_digest":body["state_digest"]}
        self.db.execute("INSERT OR REPLACE INTO meta VALUES('head',?)",(canonical(head),))
        self.db.execute("INSERT OR REPLACE INTO meta VALUES('head_mac',?)",(self._mac(head),))
    def verify(self):
        # Pin all audit reads to one SQLite snapshot while the web worker writes.
        own_transaction = not self.db.in_transaction
        if own_transaction: self.db.execute("BEGIN")
        try:
            return self._verify_snapshot()
        finally:
            if own_transaction: self.db.rollback()

    def _verify_snapshot(self):
        rows=self.db.execute("SELECT seq,body,prev,hash FROM events ORDER BY seq").fetchall()
        if not rows:raise Invalid("Missing event history")
        prev="0"*64
        for expected,(seq,raw,p,h) in enumerate(rows,1):
            if seq!=expected or p!=prev or digest({"prev":p,"body":json.loads(raw)})!=h:raise Invalid("Event integrity failure")
            prev=h
        head=json.loads(self.meta("head"))
        if not hmac.compare_digest(self._mac(head),self.meta("head_mac")):raise Invalid("Head authentication failed")
        if head!={"seq":rows[-1][0],"hash":rows[-1][3],"state_digest":self._state()}:raise Invalid("Controller state or history changed")
        if json.loads(rows[-1][1])["state_digest"]!=head["state_digest"]:raise Invalid("State commitment mismatch")
        return {"valid":True,"events":len(rows),"head":head["hash"],"scope":"Local authenticated state and event chain; not external truth"}
    @contextmanager
    def transaction(self,allow_stopped=False):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.verify()
            if self.stopped() and not allow_stopped:raise Stopped("Operator stop is active")
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback();raise
    def claim_audit(self,key):
        if not isinstance(key,str) or len(key)!=64:raise Invalid("Invalid audit key")
        with self.transaction():
            if self.db.execute("SELECT 1 FROM audit_slots WHERE id=?",(key,)).fetchone():raise Invalid("Holdout already consumed; use fresh audit data")
            token=secrets.token_hex(16)
            self.db.execute("INSERT INTO audit_slots VALUES(?,?,NULL)",(key,token))
            self._append("audit_consumed",{"audit_key":key,"token":token})
        return token
    def store_run(self,record):
        verify_record(record)
        if record["source_fingerprint"]!=source_fingerprint():raise Invalid("Source fingerprint changed")
        with self.transaction():
            if self.db.execute("SELECT 1 FROM runs WHERE id=?",(record["run_id"],)).fetchone():raise Invalid("Run already registered; replay refused")
            slot=self.db.execute("SELECT token,run_id FROM audit_slots WHERE id=?",(record["audit_key"],)).fetchone()
            if not slot or slot[0]!=record.get("audit_claim") or slot[1] is not None:raise Invalid("Missing/used controller audit reservation")
            self.db.execute("INSERT INTO runs VALUES(?,?)",(record["run_id"],canonical(record)))
            self.db.execute("UPDATE audit_slots SET run_id=? WHERE id=?",(record["run_id"],record["audit_key"]))
            self._append("research_recorded",{"run_id":record["run_id"],"record_digest":record["record_digest"],"status":record["status"]})
    def get_run(self,run_id):
        row=self.db.execute("SELECT body FROM runs WHERE id=?",(run_id,)).fetchone()
        if row is None:raise Invalid("Unknown run")
        return json.loads(row[0])
    def current(self,task):
        row=self.db.execute("SELECT v.id,v.model FROM active a JOIN versions v ON a.version=v.id WHERE a.task=?",(task,)).fetchone()
        return {"version":row[0],"model":json.loads(row[1])} if row else None
    def approve(self,run_id,operator,ttl=300):
        if not isinstance(operator,str) or not operator.strip() or len(operator)>80:raise Invalid("Named local reviewer label required")
        integer(ttl,1,3600,"ttl")
        with self.transaction():
            record=self.get_run(run_id);verify_record(record)
            if record["source_fingerprint"]!=source_fingerprint():raise Invalid("Source changed since research")
            if record["status"]!="REVIEWABLE" or not record["audit"]["eligible"] or not record.get("adoption",{}).get("eligible"):raise Invalid("Candidate did not pass audit")
            now=int(time.time())
            body={"id":secrets.token_hex(16),"run_id":run_id,"record_digest":record["record_digest"],"scope":"LOCAL_POLICY_PROMOTION",
                  "operator_label":operator,"epoch":self.meta("epoch"),"source_fingerprint":source_fingerprint(),"control_digest":CONTROL_DIGEST,"issued":now,"expires":now+ttl}
            envelope={"body":body,"mac":self._mac(body),"identity_boundary":"Local controller key; not a civil-identity or third-party certificate"}
            self.db.execute("INSERT INTO tickets VALUES(?,?,0)",(body["id"],canonical(envelope)))
            self._append("review_approved",{"run_id":run_id,"ticket_id":body["id"],"operator_label":operator})
        return envelope
    def promote(self,ticket,now=None):
        with self.transaction():
            body=ticket.get("body",{})
            if not hmac.compare_digest(self._mac(body),str(ticket.get("mac",""))):raise Invalid("Invalid approval MAC")
            row=self.db.execute("SELECT body,used FROM tickets WHERE id=?",(body.get("id"),)).fetchone()
            if row is None or row[1] or json.loads(row[0])!=ticket:raise Invalid("Unknown, changed or replayed approval")
            t=int(time.time()) if now is None else now
            if t<body["issued"] or t>=body["expires"] or body["epoch"]!=self.meta("epoch"):raise Invalid("Expired or revoked approval")
            if body["scope"]!="LOCAL_POLICY_PROMOTION" or body["control_digest"]!=CONTROL_DIGEST or body["source_fingerprint"]!=source_fingerprint():raise Invalid("Approval scope or source mismatch")
            r=self.get_run(body["run_id"]);verify_record(r)
            if r["record_digest"]!=body["record_digest"] or not r["audit"]["eligible"] or not r.get("adoption",{}).get("eligible") or r["source_fingerprint"]!=source_fingerprint():raise Invalid("Audit/evaluator mismatch")
            old=self.current(r["task"])
            if r["parent_version"]!=(old["version"] if old else None):raise Invalid("Incumbent changed after research")
            version="v-"+r["candidate_digest"][:16]+"-"+body["id"][:8]
            self.db.execute("INSERT INTO versions VALUES(?,?,?,?,?)",(version,r["task"],r["run_id"],r["parent_version"],canonical(r["search"]["champion"]["model"])))
            self.db.execute("INSERT OR REPLACE INTO active VALUES(?,?)",(r["task"],version))
            self.db.execute("UPDATE tickets SET used=1 WHERE id=?",(body["id"],))
            self._append("local_policy_promoted",{"version":version,"task":r["task"],"run_id":r["run_id"]})
        return {"version":version,"scope":"LOCAL_ONLY","external_execution":False}
    def rollback(self,task,reason):
        if not reason:raise Invalid("Rollback reason required")
        with self.transaction(allow_stopped=True):
            old=self.current(task)
            if old is None:raise Invalid("No active version")
            parent=self.db.execute("SELECT parent FROM versions WHERE id=?",(old["version"],)).fetchone()[0]
            if parent:self.db.execute("UPDATE active SET version=? WHERE task=?",(parent,task))
            else:self.db.execute("DELETE FROM active WHERE task=?",(task,))
            self.db.execute("UPDATE meta SET v=? WHERE k='epoch'",(str(int(self.meta("epoch"))+1),))
            self._append("rollback",{"task":task,"retired":old["version"],"restored":parent,"reason":reason})
        return {"restored":parent,"reason":reason}
    def stop(self,reason):
        if not reason:raise Invalid("Stop reason required")
        with self.transaction(allow_stopped=True):
            self.db.execute("UPDATE meta SET v='true' WHERE k='stopped'")
            self.db.execute("UPDATE meta SET v=? WHERE k='epoch'",(str(int(self.meta("epoch"))+1),))
            self._append("operator_stop",{"reason":reason})
    def resume(self,operator):
        if not operator:raise Invalid("Explicit operator label required")
        with self.transaction(allow_stopped=True):
            self.db.execute("UPDATE meta SET v='false' WHERE k='stopped'")
            self._append("operator_resume",{"operator_label":operator})
    def observe(self, kind, payload):
        """Record a controller-produced observation; not a self-reported external truth."""
        if kind not in {"inference_recorded", "canary_recorded", "campaign_started", "campaign_finished", "campaign_trial_failed"}:
            raise Invalid("Unknown observation kind")
        with self.transaction():
            self._append(kind, payload)

    def snapshot(self):
        audit=self.verify()
        return {"audit":audit,"stopped":self.stopped(),"epoch":self.meta("epoch"),
                "runs":[{"id":i,"status":json.loads(b)["status"],"task":json.loads(b)["task"]} for i,b in self.db.execute("SELECT id,body FROM runs ORDER BY id")],
                "active":[{"task":a,"version":b} for a,b in self.db.execute("SELECT task,version FROM active ORDER BY task")],"external_actions":0}
