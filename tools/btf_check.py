#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 work/vmlinux/vmlinux.btf 读结构体成员偏移（本地内核 6.1.99）。
用法: python btf_check.py rt_mutex_waiter selinux_state cred task_struct
"""
import struct, sys

P = r"e:/CVE-2026-43499/Trae/CVE-2026-43499/work/vmlinux/vmlinux.btf"
d = open(P, "rb").read()
magic, ver, flags, hlen = struct.unpack_from("<HBBI", d, 0)
off_t, len_t, off_s, len_s = struct.unpack_from("<IIII", d, 8)
types = d[hlen + off_t: hlen + off_t + len_t]
strs = d[hlen + off_s: hlen + off_s + len_s]


def s(o):
    if o >= len(strs):
        return ""
    e = strs.find(b"\0", o)
    return strs[o:e if e >= 0 else len(strs)].decode("utf-8", "replace")


def extra(kind, vlen):
    return {1: 4, 3: 12, 4: 12 * vlen, 5: 12 * vlen, 6: 8 * vlen,
            13: 8 * vlen, 14: 4, 15: 12 * vlen, 17: 4, 19: 12 * vlen}.get(kind, 0)


t = []          # (name, kind, size, vlen, kflag, body_off)
p = 0
while p + 12 <= len(types):
    name, info, size = struct.unpack_from("<III", types, p)
    kind = (info >> 24) & 0x1f
    vlen = info & 0xffff
    kflag = info >> 31
    t.append((s(name), kind, size, vlen, kflag, p + 12))
    p += 12 + extra(kind, vlen)

want = set(sys.argv[1:]) or {"rt_mutex_waiter"}
for i, (name, kind, size, vlen, kflag, body) in enumerate(t):
    if kind in (4, 5) and name in want:
        print("== %s size=0x%x vlen=%d kflag=%d" % (name, size, vlen, kflag))
        for j in range(vlen):
            mn, mt, mo = struct.unpack_from("<III", types, body + 12 * j)
            bits = (mo >> 24) & 0xff if kflag else 0
            off = (mo & 0xffffff) if kflag else mo
            print("   +0x%03x %-28s type=%d%s" %
                  (off // 8, s(mn), mt, (" bit=%d" % bits) if kflag else ""))
