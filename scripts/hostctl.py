#!/usr/bin/env python3
"""Send one JSON line to a vphone VM's host control socket and print the reply.

usage: hostctl.py '<json>' [machine] [timeout-seconds]
e.g.   hostctl.py '{"t":"rpc","method":"device.info","params":{}}'
"""
import os
import socket
import sys

request = sys.argv[1]
machine = sys.argv[2] if len(sys.argv) > 2 else "homeview"
timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 60

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(timeout)
s.connect(os.path.expanduser(f"~/.vphone/machines/{machine}/vphone.sock"))
s.sendall(request.encode() + b"\n")
reply = b""
while not reply.endswith(b"\n"):
    chunk = s.recv(1 << 16)
    if not chunk:
        break
    reply += chunk
print(reply.decode(errors="replace").strip())
