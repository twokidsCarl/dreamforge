#!/usr/bin/env python3
"""gpt-image-2 via Token99 relay (curl). usage: gen.py ID SIZE QUALITY PROMPT_FILE_OR_TEXT [--ref img ...]
Logs every call (incl. usage + est cost) to v8/costs_image2.jsonl."""
import base64, json, subprocess, sys, time, os
from pathlib import Path
V8 = Path("/workspace/e2work/v8"); OUT = V8/"gen"; LOG = V8/"costs_image2.jsonl"
def env():
    e={}
    for l in Path.home().joinpath(".config/token99.env").read_text().splitlines():
        l=l.strip()
        if l and not l.startswith("#") and "=" in l:
            k,v=l.split("=",1); e[k.strip().replace("export ","")]=v.strip().strip('"\'')
    return e["RELAY_BASE_URL"].rstrip("/"), e["RELAY_API_KEY"]
def cost(u):
    if not u: return 0.0
    det=u.get("input_tokens_details") or {}
    ti=det.get("text_tokens", u.get("input_tokens",0)); ii=det.get("image_tokens",0)
    return ti*5e-6 + ii*10e-6 + u.get("output_tokens",0)*30e-6
def spent():
    if not LOG.exists(): return 0.0
    return sum(json.loads(l).get("est_usd",0) for l in LOG.read_text().splitlines() if l.strip())
def main():
    a=sys.argv[1:]; refs=[]
    if "--ref" in a:
        i=a.index("--ref"); refs=a[i+1:]; a=a[:i]
    sid,size,q,p=a[:4]
    prompt=Path(p).read_text() if os.path.exists(p) else p
    if spent()>14.5: print("BUDGET STOP", spent()); sys.exit(2)
    base,key=env(); OUT.mkdir(exist_ok=True)
    resp=OUT/f".resp_{sid}.json"; t0=time.time()
    if refs:
        cmd=["curl","-sS","-w","%{http_code}","-X","POST",f"{base}/images/edits","-H",f"Authorization: Bearer {key}","-H","User-Agent: curl/8.5.0",
             "-F","model=gpt-image-2","-F",f"prompt={prompt}","-F",f"size={size}","-F",f"quality={q}"]
        for r in refs: cmd+=["-F",f"image[]=@{r}"]
        cmd+=["-o",str(resp)]
    else:
        pl=OUT/f".pl_{sid}.json"; pl.write_text(json.dumps({"model":"gpt-image-2","prompt":prompt,"n":1,"size":size,"quality":q},ensure_ascii=False))
        cmd=["curl","-sS","-w","%{http_code}","-X","POST",f"{base}/images/generations","-H",f"Authorization: Bearer {key}","-H","Content-Type: application/json","-H","User-Agent: curl/8.5.0","--data-binary",f"@{pl}","-o",str(resp)]
    try: pr=subprocess.run(cmd,capture_output=True,text=True,timeout=400)
    except subprocess.TimeoutExpired:
        with LOG.open("a") as f: f.write(json.dumps({"id":sid,"http":"timeout","est_usd":0.13,"note":"client timeout; may be billed, counted at high-quality upper estimate"})+"\n")
        print("TIMEOUT",sid); sys.exit(3)
    http=(pr.stdout or "0")[-3:]; raw=resp.read_text() if resp.exists() else pr.stderr
    rec={"id":sid,"size":size,"quality":q,"http":http,"refs":refs,"elapsed":round(time.time()-t0,1),"prompt":prompt[:300]}
    if http!="200":
        rec["error"]=raw[:600]; rec["est_usd"]=0
    else:
        d=json.loads(raw); it=d["data"][0]
        png=base64.b64decode(it["b64_json"]) if it.get("b64_json") else subprocess.run(["curl","-sS",it["url"]],capture_output=True).stdout
        (OUT/f"{sid}.png").write_bytes(png); rec["usage"]=d.get("usage"); rec["est_usd"]=round(cost(d.get("usage")),4)
        resp.unlink(missing_ok=True)
    with LOG.open("a") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    print(json.dumps({k:rec.get(k) for k in ("id","http","est_usd","elapsed","error")},ensure_ascii=False), "total=%.3f"%spent())
main()
