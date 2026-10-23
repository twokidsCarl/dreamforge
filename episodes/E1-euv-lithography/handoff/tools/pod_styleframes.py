"""E1 P1 styleframes on one RunPod GPU: create pod -> sync worktree -> render -> pull back -> ALWAYS terminate.

  RUNPOD_API_KEY=... python3 pod_styleframes.py SHOTS_FILE [--cap-usd 3] [--procs 3]

SHOTS_FILE lines: "<shot> <frame>,<frame>,..." (frames 1-based, shot-relative). Renders land in
episodes/E1-euv-lithography/renders/shots/<shot>/sample/ on the box (gitignored). Writes a JSON summary next to
SHOTS_FILE (<name>.result.json) with pod id, rate, minutes and cost, for handoff/E1_SPEND.md.
Pattern copied from the E2 runs (docs/RUNPOD.md): CA-MTL-1 + network volume eigenlens-cache (Blender 5.2.2 on it).
"""
import argparse, glob, json, os, subprocess, sys, time

API = "https://rest.runpod.io/v1"
KEY = os.environ["RUNPOD_API_KEY"]
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
EP = os.path.join(REPO, "episodes/E1-euv-lithography")
SSHKEY = os.path.expanduser("~/.ssh/id_ed25519_gpu_laptop")
SSHO = ["-i", SSHKEY, "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR", "-o", "ServerAliveInterval=30"]
pod, t0, rate = None, None, 0.59


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def req(method, path, body=None):
    cmd = ["curl", "-s", "-w", "\n%{http_code}", "-X", method, API + path,
           "-H", f"Authorization: Bearer {KEY}", "-H", "Content-Type: application/json"]
    if body:
        cmd += ["-d", json.dumps(body)]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=90).stdout
    t, _, code = out.rpartition("\n")
    try:
        return int(code or 0), (json.loads(t) if t.strip() else None)
    except ValueError:
        return int(code or 0), t[:300]


def ssh(ip, port, cmd, timeout=300):
    return subprocess.run(["ssh", *SSHO, "-p", str(port), f"root@{ip}", cmd], capture_output=True, text=True, timeout=timeout)


def push(ip, port, src_dir, dst_dir, excludes=()):
    """tar over ssh (the box has no rsync); -h follows symlinks."""
    ex = " ".join(f"--exclude='{e}'" for e in excludes)
    cmd = (f"tar -C {src_dir} -chzf - {ex} . | ssh {' '.join(SSHO)} -p {port} root@{ip} "
           f"'mkdir -p {dst_dir} && tar -xzf - -C {dst_dir}'")
    return subprocess.run(["bash", "-o", "pipefail", "-c", cmd], capture_output=True, text=True)


def pull(ip, port, src_dir, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    cmd = (f"ssh {' '.join(SSHO)} -p {port} root@{ip} 'tar -C {src_dir} -cf - .' | tar -xf - -C {dst_dir}")
    return subprocess.run(["bash", "-o", "pipefail", "-c", cmd], capture_output=True, text=True)


def terminate():
    if not pod:
        return
    for _ in range(8):
        st, b = req("DELETE", f"/pods/{pod}")
        log("DELETE", st)
        time.sleep(5)
        st, lst = req("GET", "/pods")
        if st == 200 and not any(p.get("id") == pod for p in (lst or [])):
            log("TERMINATED_CONFIRMED", pod, "pods now:", [p.get("id") for p in lst or []])
            return
    log("TERMINATE_NOT_CONFIRMED", pod)


def main():
    global pod, t0, rate
    ap = argparse.ArgumentParser()
    ap.add_argument("shots_file")
    ap.add_argument("--cap-usd", type=float, default=3.0)
    ap.add_argument("--procs", type=int, default=3)
    a = ap.parse_args()
    jobs = [l.split() for l in open(a.shots_file) if l.strip() and not l.startswith("#")]
    # R17: a self-referencing symlink under renders/ (renders/plates/plates) made the `tar -h` sync recurse forever
    # (19.6 min of a rented pod). Fail before renting a GPU.
    lp = subprocess.run(["find", "-L", os.path.join(EP, "renders"), "-maxdepth", "6", "-type", "d"],
                        capture_output=True, text=True)
    if "loop" in lp.stderr.lower():
        sys.exit("SYMLINK_LOOP under renders/: " + lp.stderr.strip()[:300])
    st, lst = req("GET", "/pods")
    log("existing pods", [(p.get("id"), p.get("name")) for p in lst or []])
    pub = open(SSHKEY + ".pub").read().strip()
    body = {"name": "eigenlens-e1-p1", "imageName": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
            "cloudType": "SECURE", "gpuTypeIds": ["NVIDIA A40", "NVIDIA RTX A6000"], "gpuCount": 1,
            "dataCenterIds": ["CA-MTL-1"], "networkVolumeId": "3b6w9chaub", "volumeMountPath": "/workspace",
            "containerDiskInGb": 20, "ports": ["22/tcp"], "env": {"NVIDIA_DRIVER_CAPABILITIES": "all", "PUBLIC_KEY": pub}}
    for _ in range(6):
        st, b = req("POST", "/pods", body)
        if st in (200, 201) and isinstance(b, dict) and b.get("id"):
            break
        log("CREATE retry", st, str(b)[:200])
        time.sleep(20)
    else:
        sys.exit("CREATE_FAILED")
    pod, t0 = b["id"], time.time()
    rate = float(b.get("costPerHr") or rate)
    cap_s = max(600, (a.cap_usd - 0.1) / rate * 3600)
    log(f"POD {pod} {b.get('machine', {}).get('gpuDisplayName', '') if isinstance(b.get('machine'), dict) else ''} "
        f"${rate}/h, hard stop {cap_s/60:.0f} min")
    ip = port = None
    while time.time() - t0 < 900:
        st, p = req("GET", f"/pods/{pod}")
        if st == 200 and p.get("publicIp") and (p.get("portMappings") or {}).get("22"):
            ip, port = p["publicIp"], p["portMappings"]["22"]
            break
        time.sleep(8)
    if not ip:
        log("NO_SSH"); return
    for _ in range(40):
        if ssh(ip, port, "true", 30).returncode == 0:
            break
        time.sleep(8)
    else:
        log("SSH_NEVER_UP"); return
    log("SSH", ip, port)
    r = ssh(ip, port, "export DEBIAN_FRONTEND=noninteractive; apt-get update -qq && apt-get install -y -qq libxi6 "
                      "libxkbcommon0 libsm6 libxrender1 libxxf86vm1 libxfixes3 libgl1 libegl1 >/dev/null 2>&1; "
                      "ls /workspace/blender-5.2.2-linux-x64/blender; nvidia-smi -L", 500)
    log("setup", r.stdout.strip()[-300:])
    if "blender" not in r.stdout:
        log("SETUP_FAILED"); return
    excl = ["./.git", "./episodes/*/audio", "./episodes/*/renders", "*.mp4", "__pycache__", "./episodes/E2-optogenetics"]
    # R4: the single ~80 MB tar pipe broke twice mid-transfer; push in chunks, each retried up to 3 times
    chunks = [("shared/assets", "/root/repo/shared/assets"), ("shared/blender", "/root/repo/shared/blender"),
              ("shared/tools", "/root/repo/shared/tools"), ("brand", "/root/repo/brand"), ("docs", "/root/repo/docs"),
              ("episodes/E1-euv-lithography", "/root/repo/episodes/E1-euv-lithography")]
    for src, dst in chunks:
        for attempt in range(3):
            ex = [e.replace("./episodes/*/", "./") for e in excl if not e.startswith("./episodes/E2")]
            r = push(ip, port, os.path.join(REPO, src), dst, ex)
            log("sync", src, "try", attempt + 1, "rc", r.returncode, r.stderr[-200:])
            if r.returncode == 0:
                break
        else:
            return
    for fn in ("README.md",):
        push(ip, port, REPO, "/root/repo", [f"./{d}" for d in os.listdir(REPO) if d != fn])
    # dependency inputs some shots read (B1_15 sample frames, sample_b1 still)
    r = push(ip, port, os.path.join(EP, "renders"), "/root/r", ["./review", "./edit"])
    log("sync renders rc", r.returncode, r.stderr[-200:])
    jl = "\n".join(f"{s} {fr}" for s, fr in jobs)
    script = f"""cd /root/repo
export REPO=/root/repo DREAMFORGE_EPISODE=E1-euv-lithography DREAMFORGE_RENDER_DIR=/root/r DREAMFORGE_CYCLES_DEVICE=OPTIX
mkdir -p /root/r/logs
cat > /root/jobs.txt <<'J'
{jl}
J
run() {{ /workspace/blender-5.2.2-linux-x64/blender -b --factory-startup -P shared/tools/render_storyboard.py -- --shot $1 --quality sample --frames $2 > /root/r/logs/$1.txt 2>&1; echo "DONE $1 rc=$? $(ls /root/r/shots/$1/sample 2>/dev/null | wc -l)"; }}
export -f run
cat /root/jobs.txt | xargs -P {a.procs} -L 1 bash -c 'run "$0" "$1"'
"""
    remaining = cap_s - (time.time() - t0) - 240
    log(f"RENDER {len(jobs)} shots, P={a.procs}, budget {remaining/60:.0f} min")
    try:
        r = ssh(ip, port, script, timeout=max(120, remaining))
        log(r.stdout[-3000:], r.stderr[-500:])
    except subprocess.TimeoutExpired:
        log("RENDER_TIMEOUT (cap) - pulling what exists")
        ssh(ip, port, "pkill -f blender", 30)
    os.makedirs(os.path.join(EP, "renders/shots"), exist_ok=True)
    r = pull(ip, port, "/root/r/shots", os.path.join(EP, "renders/shots"))
    pull(ip, port, "/root/r/logs", os.path.join(EP, "renders/review/p1_logs"))
    log("pull rc", r.returncode, r.stderr[-200:])
    got = {s: len(glob.glob(os.path.join(EP, f"renders/shots/{s}/sample/*.png"))) for s, _ in jobs}
    log("GOT", got)


if __name__ == "__main__":
    ap_file = sys.argv[1] if len(sys.argv) > 1 else "jobs"
    try:
        main()
    finally:
        terminate()
        if t0:
            el = time.time() - t0
            res = {"pod": pod, "rate_usd_h": rate, "minutes": round(el / 60, 2), "cost_usd": round(el / 3600 * rate, 3),
                   "ended": time.strftime("%Y-%m-%d %H:%M")}
            log("COST", res)
            json.dump(res, open(os.path.splitext(ap_file)[0] + ".result.json", "w"), indent=1)
