"""Operator CLI. No shell, native candidate code, provider API or external effects."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .canonical import Invalid,Stopped,BudgetExceeded,load_json,save_json
from .policy import Limits
from .engine import research
from .registry import Registry
from .problems import TASKS
from .runtime import campaign, run_controlled, infer, canary, walkthrough
from .intake import csv_dataset, proposer_packet
from .reporting import run_markdown, export_policy


def main(argv=None):
    ap=argparse.ArgumentParser(prog="ascent",description="Bounded research, not demonstrated ASI")
    ap.add_argument("--version", action="version", version="ASCENT 0.2.0")
    sub=ap.add_subparsers(dest="command",required=True)
    p=sub.add_parser("init");p.add_argument("workspace")
    p=sub.add_parser("run");p.add_argument("workspace");p.add_argument("--task",choices=TASKS+("custom_regression",),default="quadratic");p.add_argument("--seed",type=int,default=17)
    p.add_argument("--proposals",type=int,default=96);p.add_argument("--work-units",type=int,default=8_000_000);p.add_argument("--seconds",type=int,default=30)
    p.add_argument("--data");p.add_argument("--candidate-file");p.add_argument("--output",default="run.json")
    p=sub.add_parser("approve");p.add_argument("workspace");p.add_argument("run_id");p.add_argument("--operator",required=True);p.add_argument("--output",default="approval.json");p.add_argument("--ttl",type=int,default=300)
    p=sub.add_parser("promote");p.add_argument("workspace");p.add_argument("ticket")
    p=sub.add_parser("rollback");p.add_argument("workspace");p.add_argument("--task",required=True);p.add_argument("--reason",required=True)
    p=sub.add_parser("stop");p.add_argument("workspace");p.add_argument("--reason",required=True)
    p=sub.add_parser("resume");p.add_argument("workspace");p.add_argument("--operator",required=True)
    for name in ("audit","status"):
        p=sub.add_parser(name);p.add_argument("workspace")
    p=sub.add_parser("demo");p.add_argument("--output",default="ascent-demo");p.add_argument("--seed",type=int,default=17)
    p=sub.add_parser("serve");p.add_argument("workspace");p.add_argument("--port",type=int,default=8765)
    p=sub.add_parser("walkthrough");p.add_argument("--output",default="ascent-walkthrough")
    p=sub.add_parser("campaign");p.add_argument("workspace");p.add_argument("--tasks",nargs="+",default=list(TASKS));p.add_argument("--seeds",nargs="+",type=int,default=[17,23,31]);p.add_argument("--output",required=True);p.add_argument("--seconds",type=int,default=300);p.add_argument("--proposals",type=int,default=96)
    p=sub.add_parser("infer");p.add_argument("workspace");p.add_argument("--task",required=True);p.add_argument("--input",required=True);p.add_argument("--output",default="inference.json")
    p=sub.add_parser("canary");p.add_argument("workspace");p.add_argument("--task",required=True);p.add_argument("--data",required=True);p.add_argument("--threshold",type=float,required=True);p.add_argument("--output",default="canary.json")
    p=sub.add_parser("export-policy");p.add_argument("workspace");p.add_argument("--task",required=True);p.add_argument("--output",default="active-policy.json")
    p=sub.add_parser("report");p.add_argument("record");p.add_argument("--output",default="experiment.md")
    p=sub.add_parser("csv-import");p.add_argument("input");p.add_argument("--output",default="custom-data.json")
    p=sub.add_parser("proposer-request");p.add_argument("--task",choices=TASKS+("custom_regression",),default="periodic");p.add_argument("--seed",type=int,default=17);p.add_argument("--data");p.add_argument("--output",default="proposer-request.json")
    p=sub.add_parser("doctor")
    args=ap.parse_args(argv)
    try:
        if args.command == "serve":
            from .server import serve
            serve(args.workspace,args.port);return 0
        if args.command in {"walkthrough","campaign","infer","canary","export-policy","csv-import","proposer-request","report","doctor"}:
            if args.command == "walkthrough": out=walkthrough(args.output)
            elif args.command == "campaign": out=campaign(args.workspace,args.output,args.tasks,args.seeds,Limits(proposals=args.proposals),args.seconds)
            elif args.command == "infer": out=infer(args.workspace,args.task,load_json(args.input));save_json(args.output,out)
            elif args.command == "canary": out=canary(args.workspace,args.task,load_json(args.data),args.threshold);save_json(args.output,out)
            elif args.command == "export-policy": out=export_policy(args.workspace,args.task);save_json(args.output,out)
            elif args.command == "csv-import": out=csv_dataset(args.input);save_json(args.output,out);out={"output":args.output,"train_rows":len(out["train"])}
            elif args.command == "proposer-request": out=proposer_packet(args.task,args.seed,load_json(args.data) if args.data else None);save_json(args.output,out);out={"output":args.output,"audit_included":False,"automatic_network":False}
            elif args.command == "report": Path(args.output).write_text(run_markdown(load_json(args.record)),encoding="utf-8");out={"output":args.output}
            elif args.command == "doctor":
                from importlib.resources import files
                from .engine import source_fingerprint
                out={"version":"0.2.0","python":sys.version.split()[0],"minimum_python":"3.10","runtime_dependencies":[],"console_resource_present":files("dikwp_ascent").joinpath("resources","console.html").is_file(),"source_fingerprint":source_fingerprint(),"provider_calls":0,"asi_established":False}
            print(json.dumps(out,indent=2,allow_nan=False));return 0
        if args.command=="demo":
            root=Path(args.output)
            if root.exists() and any(root.iterdir()):raise Invalid("Demo requires an empty directory; existing work is never reset")
            root.mkdir(parents=True,exist_ok=True)
            reports=[]
            for task in TASKS:
                result=research(task,args.seed)
                save_json(root/f"{task}.json",result)
                reports.append(result)
            save_json(root/"summary.json",reports)
            print(json.dumps([{ "task":r["record"]["task"],"status":r["record"]["status"],"baseline_worst":r["record"]["audit"]["worst_baseline"],"candidate_worst":r["record"]["audit"]["worst_candidate"]} for r in reports],indent=2))
            return 0
        reg=Registry(args.workspace,create=args.command=="init")
        try:
            if args.command in {"init","status"}:out=reg.snapshot()
            elif args.command=="audit":out=reg.verify()
            elif args.command=="run":
                reg.close(); reg=None
                result=run_controlled(args.workspace,args.task,args.seed,Limits(proposals=args.proposals,work_units=args.work_units,seconds=args.seconds),
                    custom=load_json(args.data) if args.data else None,proposals=load_json(args.candidate_file) if args.candidate_file else None)
                save_json(args.output,result);out={"run_id":result["record"]["run_id"],"status":result["record"]["status"],"output":args.output,"external_actions":0}
            elif args.command=="approve":out=reg.approve(args.run_id,args.operator,args.ttl);save_json(args.output,out)
            elif args.command=="promote":out=reg.promote(load_json(args.ticket))
            elif args.command=="rollback":out=reg.rollback(args.task,args.reason)
            elif args.command=="stop":reg.stop(args.reason);out=reg.snapshot()
            elif args.command=="resume":reg.resume(args.operator);out=reg.snapshot()
            print(json.dumps(out,indent=2,allow_nan=False))
        finally:
            if reg:reg.close()
        return 0
    except (Invalid,Stopped,BudgetExceeded,ValueError,OSError,KeyError,TypeError) as e:
        print(json.dumps({"error":type(e).__name__,"message":str(e)}),file=sys.stderr);return 2

if __name__=="__main__":raise SystemExit(main())
