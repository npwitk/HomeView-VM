#!/usr/bin/env python3
"""Wait for a guest launchd job to settle: up for ~30 s, or exited with an error.

usage: watch_shell.py [label] [machine] [max-seconds]
"""
import json, os, socket, sys, time

label = sys.argv[1] if len(sys.argv) > 1 else "com.apple.BreadBoard"
machine = sys.argv[2] if len(sys.argv) > 2 else "homeview"
deadline = time.time() + float(sys.argv[3] if len(sys.argv) > 3 else 300)
sock = os.path.expanduser(f"~/.vphone/machines/{machine}/vphone.sock")


def services():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(20)
    s.connect(sock)
    s.sendall(b'{"t":"rpc","method":"services.list","params":{}}\n')
    buf = b""
    while not buf.endswith(b"\n"):
        c = s.recv(1 << 20)
        if not c:
            break
        buf += c
    s.close()
    res = json.loads(buf)["result"]
    return res.get("services", res) if isinstance(res, dict) else res


stable, last = 0, None
while time.time() < deadline:
    try:
        job = next((j for j in services() if j.get("label") == label), None)
    except Exception as e:
        job, err = None, e
        state = f"no answer yet ({type(err).__name__})"
    else:
        state = json.dumps(job)
    if state != last:
        print(time.strftime("%H:%M:%S"), state, flush=True)
        last = state
    if job:
        if job.get("running"):
            stable += 1
            if stable >= 6:
                print("RESULT: running and stable", flush=True)
                sys.exit(0)
        else:
            stable = 0
            if job.get("last_exit_status", 0) not in (0, None):
                print("RESULT: exited", job.get("last_exit_status"), flush=True)
                sys.exit(1)
    time.sleep(5)
print("RESULT: timed out", flush=True)
sys.exit(2)
