"""Loopback-only operator console. No proxy, provider, shell, or arbitrary path endpoints.

The process trusts its OS user. A page session token is a CSRF control, not civil
identity authentication or protection from a hostile host process.
"""
from __future__ import annotations

import hmac
import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from .canonical import Invalid, Stopped, BudgetExceeded, canonical, exact_keys, integer, _pairs
from .policy import Limits
from .problems import TASKS
from .registry import Registry
from .runtime import run_controlled, infer
from .intake import validate_proposals


class ResearchService:
    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()
        if not (self.workspace / "controller.key").exists():
            if self.workspace.exists() and any(self.workspace.iterdir()):
                raise Invalid("Refusing to initialize a nonempty unknown workspace")
            reg = Registry(self.workspace, create=True)
        else:
            reg = Registry(self.workspace)
        reg.close()
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        self.jobs: dict[str, dict] = {}
        self.busy = False

    def submit(self, params: dict) -> dict:
        exact_keys(params, {"task", "seed"}, {"proposals", "seconds", "data", "candidate_programs"})
        task = params["task"]
        if task not in TASKS + ("custom_regression",):
            raise Invalid("Unknown task")
        integer(params["seed"], 0, 2**31-1, "seed")
        limits = Limits(proposals=params.get("proposals", 96), seconds=params.get("seconds", 30))
        proposals = params.get("candidate_programs")
        if proposals is not None:
            proposals = validate_proposals(proposals, "scheduler" if task == "scheduling" else "basis")
        # Dataset validation happens again inside the controlled engine.
        with self.lock:
            if self.busy:
                raise Invalid("A research job is already active in this console")
            self.busy = True
            job_id = "job-" + secrets.token_hex(8)
            self.jobs[job_id] = {"id": job_id, "task": task, "seed": params["seed"], "status": "RUNNING"}
        def worker():
            try:
                result = run_controlled(self.workspace, task, params["seed"], limits,
                                        custom=params.get("data"), proposals=proposals)
                rec = result["record"]
                update = {"status": "COMPLETED", "run_id": rec["run_id"], "decision": rec["status"],
                          "seconds": result["telemetry"]["wall_seconds"]}
            except (Invalid, Stopped, BudgetExceeded, ValueError, OSError) as exc:
                update = {"status": "FAILED", "error_type": type(exc).__name__, "message": str(exc)}
            except Exception as exc:
                update = {"status": "FAILED", "error_type": type(exc).__name__, "message": "Unexpected local failure; inspect CLI and tests"}
            finally:
                with self.lock:
                    self.jobs[job_id].update(update)
                    self.busy = False
        thread = threading.Thread(target=worker, name=job_id, daemon=True)
        thread.start()
        return {"job_id": job_id, "status": "RUNNING", "automatic_adoption": False}

    def job_snapshot(self):
        with self.lock:
            return {"busy": self.busy, "jobs": [dict(x) for x in self.jobs.values()]}

    def stop_on_shutdown(self):
        reg = Registry(self.workspace)
        try:
            reg.stop("Local operator console shutdown")
        finally:
            reg.close()


def make_server(workspace: str | Path, port: int = 8765):
    integer(port, 0, 65535, "port")
    service = ResearchService(workspace)

    class Handler(BaseHTTPRequestHandler):
        server_version = "ASCENT/0.2"

        def log_message(self, fmt, *args):
            # Do not log keys, datasets, cookies, parameters, or content.
            pass

        def host_allowed(self):
            p = self.server.server_port
            return self.headers.get("Host") in {f"127.0.0.1:{p}", f"localhost:{p}"}

        def authorized(self):
            if not self.host_allowed():
                return False
            value = self.headers.get("X-ASCENT-Token", "")
            if not hmac.compare_digest(service.token, value):
                return False
            origin = self.headers.get("Origin")
            return origin is None or origin in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}

        def respond(self, code: int, value, html: bool = False, nonce: str = ""):
            body = value.encode("utf-8") if html else canonical(value).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8" if html else "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            if html:
                self.send_header("Content-Security-Policy", f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; connect-src 'self'; img-src data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.host_allowed():
                self.respond(403, {"error": "Untrusted Host"}); return
            url = urlsplit(self.path)
            if url.path == "/":
                nonce = secrets.token_urlsafe(20)
                page = files("dikwp_ascent").joinpath("resources", "console.html").read_text(encoding="utf-8")
                self.respond(200, page.replace("__SESSION_TOKEN__", service.token).replace("__NONCE__", nonce), True, nonce)
                return
            if not self.authorized():
                self.respond(403, {"error": "Local session token required"}); return
            reg = None
            try:
                if url.path == "/api/jobs":
                    result = service.job_snapshot()
                elif url.path == "/api/status":
                    reg = Registry(service.workspace); result = reg.snapshot()
                    result["workspace"] = str(service.workspace)
                elif url.path == "/api/run":
                    ident = parse_qs(url.query).get("id", [""])[0]
                    if len(ident) > 100: raise Invalid("Invalid run identifier")
                    reg = Registry(service.workspace); result = reg.get_run(ident)
                elif url.path == "/api/model":
                    task = parse_qs(url.query).get("task", [""])[0]
                    reg = Registry(service.workspace); result = reg.current(task)
                else:
                    self.respond(404, {"error": "Endpoint not found"}); return
                self.respond(200, result)
            except (Invalid, Stopped, ValueError, OSError) as exc:
                self.respond(400, {"error": type(exc).__name__, "message": str(exc)})
            finally:
                if reg: reg.close()

        def do_POST(self):
            if not self.authorized():
                self.respond(403, {"error": "Valid local session and same origin required"}); return
            reg = None
            try:
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise Invalid("Content-Type must be application/json")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 2_000_000:
                    raise Invalid("JSON body must be between 1 byte and 2 MB")
                data = json.loads(self.rfile.read(length), object_pairs_hook=_pairs,
                                  parse_constant=lambda s: (_ for _ in ()).throw(Invalid("Nonfinite JSON")))
                path = urlsplit(self.path).path
                if path == "/api/run":
                    result = service.submit(data)
                elif path == "/api/infer":
                    exact_keys(data, {"task", "input"})
                    result = infer(service.workspace, data["task"], data["input"])
                else:
                    reg = Registry(service.workspace)
                    if path == "/api/stop":
                        exact_keys(data, {"reason"}); reg.stop(data["reason"]); result = reg.snapshot()
                    elif path == "/api/resume":
                        exact_keys(data, {"operator"}); reg.resume(data["operator"]); result = reg.snapshot()
                    elif path == "/api/approve":
                        exact_keys(data, {"run_id", "operator"})
                        result = reg.approve(data["run_id"], data["operator"])
                    elif path == "/api/promote":
                        exact_keys(data, {"ticket"}); result = reg.promote(data["ticket"])
                    elif path == "/api/rollback":
                        exact_keys(data, {"task", "reason"}); result = reg.rollback(data["task"], data["reason"])
                    else:
                        self.respond(404, {"error": "Endpoint not found"}); return
                self.respond(200, result)
            except (Invalid, Stopped, ValueError, KeyError, TypeError, OSError) as exc:
                self.respond(400, {"error": type(exc).__name__, "message": str(exc)})
            finally:
                if reg: reg.close()

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.service = service
    return server


def serve(workspace: str | Path, port: int = 8765):
    server = make_server(workspace, port)
    print(f"ASCENT local console: http://127.0.0.1:{server.server_port}", flush=True)
    print("Ctrl+C stops the server and revokes local approval tickets. No automatic adoption.", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.service.stop_on_shutdown()
        server.server_close()
