#!/usr/bin/env python3
"""Copy a folder out of a running vphone guest, recursively, through vphoned.

usage: pull_dir.py <guest-dir> <host-dir> [machine]
The host control socket answers one request per connection, so each
files.list and files.read opens its own.
"""
import base64
import json
import os
import socket
import sys

guest_root, host_root = sys.argv[1].rstrip("/"), sys.argv[2]
machine = sys.argv[3] if len(sys.argv) > 3 else "homeview"
sock_path = os.path.expanduser(f"~/.vphone/machines/{machine}/vphone.sock")


def rpc(method, params):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(60)
    s.connect(sock_path)
    s.sendall(json.dumps({"t": "rpc", "method": method, "params": params}).encode() + b"\n")
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        buf += chunk
    s.close()
    reply = json.loads(buf)
    if not reply.get("ok", True):
        raise RuntimeError(reply.get("error"))
    return reply["result"]


files = bytes_ = 0


def pull(guest, host):
    global files, bytes_
    os.makedirs(host, exist_ok=True)
    for e in rpc("files.list", {"path": guest})["entries"]:
        g, h = f"{guest}/{e['name']}", os.path.join(host, e["name"])
        if e.get("is_symlink"):
            continue
        if e.get("is_directory"):
            pull(g, h)
            continue
        if e.get("size", 0) >= 64 << 20:
            print(f"skipped, over files.read's 64 MiB limit: {g} ({e['size']} bytes)", file=sys.stderr)
            continue
        r = rpc("files.read", {"path": g, "binary": True, "limit": max(e.get("size", 0), 1)})
        if r.get("truncated"):
            print(f"truncated: {g}", file=sys.stderr)
        data = base64.b64decode(r["content"]) if r.get("encoding") == "base64" else r["content"].encode()
        with open(h, "wb") as f:
            f.write(data)
        files += 1
        bytes_ += len(data)


pull(guest_root, host_root)
print(f"{files} files, {bytes_ / 1e6:.1f} MB -> {host_root}")
