#!/usr/bin/env python3
"""tripo.py poll TASK_ID NAME  -> waits, downloads glb to tripo/NAME.glb, logs tripo/tasks.jsonl
   tripo.py text NAME "prompt"   -> creates text_to_model task and polls"""
import json,subprocess,sys,time,os
from pathlib import Path
D=Path("/workspace/e2work/v8/tripo"); KEY=[l.split("=",1)[1].strip().strip('"') for l in open(os.path.expanduser("~/.config/tripo.env")) if "TRIPO_API_KEY" in l][0]
H=["-H",f"Authorization: Bearer {KEY}"]
def api(method,path,data=None):
    c=["curl","-sS","-X",method,f"https://api.tripo3d.ai/v2/openapi/{path}",*H]
    if data: c+=["-H","Content-Type: application/json","-d",json.dumps(data)]
    return json.loads(subprocess.run(c,capture_output=True,text=True).stdout)
def bal(): return api("GET","user/balance")["data"]["balance"]
def poll(tid,name,meta=None):
    b0=bal() if meta is None else meta.get("bal0")
    while True:
        r=api("GET",f"task/{tid}")["data"]; st=r["status"]
        if st in("success","failed","cancelled","banned","expired","unknown"): break
        time.sleep(10)
    out=r.get("output",{}); url=out.get("pbr_model") or out.get("model") or out.get("base_model")
    if url: subprocess.run(["curl","-sS","-o",str(D/f"{name}.glb"),url])
    if out.get("rendered_image"): subprocess.run(["curl","-sS","-o",str(D/f"{name}_preview.webp"),out["rendered_image"]])
    rec={"name":name,"task_id":tid,"status":st,"type":r.get("type"),"balance_after":bal(),"t":time.strftime("%H:%M:%S")}
    with open(D/"tasks.jsonl","a") as f: f.write(json.dumps(rec)+"\n")
    print(rec)
if sys.argv[1]=="poll": poll(sys.argv[2],sys.argv[3])
elif sys.argv[1]=="text":
    r=api("POST","task",{"type":"text_to_model","model_version":"v3.0-20250812","prompt":sys.argv[3],"texture":True,"pbr":True,"texture_quality":"detailed"})
    print(r); poll(r["data"]["task_id"],sys.argv[2])
elif sys.argv[1]=="bal": print(bal())
