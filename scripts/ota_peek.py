#!/usr/bin/env python3
"""List or pull files out of a decrypted, segmented Apple OTA archive (AA01).

The outer archive's YOP=E entries carry another uncompressed AA01 archive in
their DAT blob; this walks those in place, without copying them out.

usage: ota_peek.py <decrypted.aa> list [substring]
       ota_peek.py <decrypted.aa> get <path-suffix> <out-dir>
"""
import os
import struct
import sys

FIXED = {"1": 1, "2": 2, "4": 4, "8": 8, "F": 4, "G": 20, "H": 32, "I": 48, "J": 64, "S": 8, "T": 12, "*": 0}
BLOB = {"A": 2, "B": 4, "C": 8}


def read_header(f, pos):
    f.seek(pos)
    head = f.read(6)
    if len(head) < 6 or head[:4] != b"AA01":
        return None
    size = struct.unpack("<H", head[4:6])[0]
    body = head + f.read(size - 6)
    fields, blobs, i = {}, [], 6
    while i < size:
        key, kind = body[i:i + 3].decode(), chr(body[i + 3])
        i += 4
        if kind in FIXED:
            n = FIXED[kind]
            fields[key] = int.from_bytes(body[i:i + n], "little") if kind in "1248" else body[i:i + n]
            i += n
        elif kind == "P":
            n = struct.unpack("<H", body[i:i + 2])[0]
            fields[key] = body[i + 2:i + 2 + n].decode(errors="replace")
            i += 2 + n
        elif kind in BLOB:
            n = BLOB[kind]
            blobs.append((key, int.from_bytes(body[i:i + n], "little")))
            i += n
        else:
            raise ValueError(f"unknown field type {kind!r} for {key} at {pos}")
    return size, fields, blobs


def walk(f, start, end, depth=0):
    pos = start
    while pos < end:
        h = read_header(f, pos)
        if h is None:
            return
        size, fields, blobs = h
        data = pos + size
        offsets = {}
        for key, n in blobs:
            offsets[key] = (data, n)
            data += n
        yield depth, fields, offsets
        if fields.get("YOP") == ord("E") and "DAT" in offsets:
            o, n = offsets["DAT"]
            yield from walk(f, o, o + n, depth + 1)
        pos = data


def main():
    path, cmd = sys.argv[1], sys.argv[2]
    with open(path, "rb") as f:
        end = os.fstat(f.fileno()).st_size
        for depth, fields, offsets in walk(f, 0, end):
            pat = fields.get("PAT")
            if pat is None:
                continue
            n = offsets.get("DAT", (0, 0))[1]
            if cmd == "list":
                if len(sys.argv) < 4 or sys.argv[3] in pat:
                    print(f"{chr(fields.get('TYP', 63))} {n:>12} {pat}")
            elif cmd == "get" and pat.endswith(sys.argv[3]) and "DAT" in offsets:
                o, n = offsets["DAT"]
                out = os.path.join(sys.argv[4], os.path.basename(pat))
                f.seek(o)
                with open(out, "wb") as w:
                    while n:
                        chunk = f.read(min(n, 8 << 20))
                        w.write(chunk)
                        n -= len(chunk)
                print(f"wrote {out} ({offsets['DAT'][1]} bytes) from {pat}")


if __name__ == "__main__":
    main()
