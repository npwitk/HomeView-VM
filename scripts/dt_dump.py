#!/usr/bin/env python3
"""Print properties of a decompressed Apple device tree whose name matches a regex.

usage: dt_dump.py <DeviceTree.bin> <name-regex>
"""
import re
import struct
import sys


def node(d, o, path, pat, out):
    nprops, nchild = struct.unpack_from("<II", d, o)
    o += 8
    props = {}
    for _ in range(nprops):
        name = d[o:o + 32].split(b"\0")[0].decode(errors="replace")
        size = struct.unpack_from("<I", d, o + 32)[0] & 0x7FFFFFFF
        props[name] = d[o + 36:o + 36 + size]
        o += 36 + ((size + 3) & ~3)
    here = path + "/" + props.get("name", b"?").split(b"\0")[0].decode(errors="replace")
    for k, v in props.items():
        if pat.search(k):
            s = v.split(b"\0")[0]
            text = s.decode() if s and all(32 <= c < 127 for c in s) else v[:32].hex()
            ints = struct.unpack_from(f"<{len(v)//4}I", v) if len(v) in (4, 8, 16) else ""
            out.append(f"{here} :: {k} = {text} {ints}")
    for _ in range(nchild):
        o = node(d, o, here, pat, out)
    return o


d = open(sys.argv[1], "rb").read()
out = []
node(d, 0, "", re.compile(sys.argv[2], re.I), out)
print("\n".join(out))
