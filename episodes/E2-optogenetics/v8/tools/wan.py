#!/usr/bin/env python3
"""Alibaba Wan image->video (DashScope intl). usage:
  wan.py ID MODEL DURATION PROMPT_FILE FIRST.png [LAST.png]
MODEL: wan2.6-i2v-flash (720P, img_url) | wan3.0-video (480P, first/last frame)
Writes v8/gen/vid/ID.mp4 and logs to v8/costs_wan.jsonl with a conservative cost estimate."""
import os, sys, json, time, base64, io, urllib.request
from PIL import Image
V8 = '/workspace/e2work/v8'; OUT = V8+'/gen/vid'; LOG = V8+'/costs_wan.jsonl'
EST = {'wan2.6-i2v-flash': 0.10, 'wan3.0-video': 0.15}      # USD per second, conservative upper estimate
env = {}
for l in open(os.path.expanduser('~/.config/dreamforge.env')):
    if '=' in l and not l.startswith('#'): k, v = l.strip().split('=', 1); env[k.replace('export ', '')] = v.strip('"\'')
KEY = env['DASHSCOPE_API_KEY']; B = 'https://dashscope-intl.aliyuncs.com/api/v1'
def spent():
    return sum(json.loads(l).get('est_usd', 0) for l in open(LOG)) if os.path.exists(LOG) else 0.0
def durl(p):
    im = Image.open(p).convert('RGB'); bio = io.BytesIO(); im.save(bio, 'JPEG', quality=92)
    return 'data:image/jpeg;base64,'+base64.b64encode(bio.getvalue()).decode()
def req(url, data=None):
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                               headers={'Authorization': 'Bearer '+KEY, 'Content-Type': 'application/json', 'X-DashScope-Async': 'enable'})
    try: return json.load(urllib.request.urlopen(r, timeout=120))
    except urllib.error.HTTPError as e: return {'HTTPError': e.code, 'body': e.read().decode()[:600]}
sid, model, dur, pf, first = sys.argv[1:6]; last = sys.argv[6] if len(sys.argv) > 6 else None
dur = int(dur); P = open(pf).read().strip()
if spent()+EST[model]*dur > 10.75: print('BUDGET STOP', spent()); sys.exit(2)   # round 14: cumulative 7.75 + round cap 3.00
if model.startswith('wan2.6'):
    body = {'model': model, 'input': {'prompt': P, 'img_url': durl(first)}, 'parameters': {'resolution': '720P', 'duration': dur, 'audio': False, 'prompt_extend': False}}
else:
    media = [{'type': 'first_frame', 'url': durl(first)}] + ([{'type': 'last_frame', 'url': durl(last)}] if last else [])
    body = {'model': model, 'input': {'prompt': P, 'media': media}, 'parameters': {'resolution': '480P', 'duration': dur, 'ratio': 'adaptive'}}
r = req(B+'/services/aigc/video-generation/video-synthesis', body); tid = r.get('output', {}).get('task_id')
print(sid, 'submit', json.dumps(r)[:300], flush=True)
rec = {'id': sid, 'model': model, 'duration': dur, 'first': first, 'last': last, 'prompt': P[:300]}
if not tid:
    rec['error'] = r; rec['est_usd'] = 0; open(LOG, 'a').write(json.dumps(rec, ensure_ascii=False)+'\n'); sys.exit(1)
t0 = time.time(); st = None
while time.time()-t0 < 900:
    time.sleep(15); r = req(B+'/tasks/'+tid); st = r.get('output', {}).get('task_status')
    if st in ('SUCCEEDED', 'FAILED', 'CANCELED', 'UNKNOWN'): break
rec['status'] = st; rec['usage'] = r.get('usage'); rec['elapsed'] = round(time.time()-t0)
u = r.get('output', {}).get('video_url')
if st == 'SUCCEEDED' and u:
    os.makedirs(OUT, exist_ok=True); urllib.request.urlretrieve(u, f'{OUT}/{sid}.mp4'); rec['est_usd'] = EST[model]*dur
else:
    rec['est_usd'] = 0; rec['error'] = json.dumps(r)[:500]
open(LOG, 'a').write(json.dumps(rec, ensure_ascii=False)+'\n')
print(sid, st, 'usage', rec.get('usage'), 'wan total est $%.2f' % spent(), flush=True)
