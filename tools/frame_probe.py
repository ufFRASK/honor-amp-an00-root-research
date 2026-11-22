#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pselect 载波几何帧探针（只读，静态）。
从 Image + kallsyms 里定位 core_sys_select：
  - 读 prologue 的 `sub sp, sp, #FRAME`
  - 找 `add x0, sp, #OFF` 后跟 `mov w2, #0x100` 的 memset 调用 => stack_fds @ SP+OFF
  - shift = OFF / 8（0 基字索引，stack_fds 第一个 8 字节字）
同时打印 do_futex / __arm64_sys_pselect6 的帧大小作对照。
用法: python frame_probe.py <Image> <symbols.txt>
"""
import sys
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

img = open(sys.argv[1], 'rb').read()
syms = {}
for line in open(sys.argv[2], encoding='utf-8'):
    p = line.split()
    if len(p) >= 3:
        syms.setdefault(p[2], int(p[0], 16))
BASE = 0xffffffc008000000
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)


def insns(name, n=120):
    va = syms[name]
    off = va - BASE
    return list(md.disasm(img[off:off + n * 4], va))


def frame(name):
    for ins in insns(name, 6):
        if ins.mnemonic == 'sub' and ins.op_str.startswith('sp, sp, #'):
            return int(ins.op_str.rsplit('#', 1)[1], 0)
    return None


def stack_fds(name):
    seq = insns(name)
    for i, ins in enumerate(seq):
        if ins.mnemonic == 'add' and ins.op_str.startswith('x0, sp, #'):
            off = int(ins.op_str.rsplit('#', 1)[1], 0)
            nxt = seq[i + 1:i + 4]
            if any(x.mnemonic == 'mov' and x.op_str == 'w2, #0x100' for x in nxt):
                return off
            if any(x.mnemonic == 'mov' and x.op_str.startswith('w2, #0x100') for x in nxt):
                return off
    return None


sel = 'core_sys_select'
if sel not in syms:
    raise SystemExit('no core_sys_select in symbols')
fo = frame('do_futex') if 'do_futex' in syms else None
ps = frame('__arm64_sys_pselect6') if '__arm64_sys_pselect6' in syms else None
f = frame(sel)
o = stack_fds(sel)
print('core_sys_select @0x%x frame=0x%x' % (syms[sel], f))
print('stack_fds_off=0x%x  (memset 0x100)' % o if o is not None else 'stack_fds offset NOT FOUND')
print('do_futex frame=%s  __arm64_sys_pselect6 frame=%s' % (hex(fo) if fo else '-', hex(ps) if ps else '-'))
if o is not None:
    print('PSELECT_WAITER_WORD_SHIFT = %d   (0x%x/8, 0-based)' % (o // 8, o))
    print('controllable stack slots: SP+0x%x .. SP+0x%x (6 regions x size)' % (o, o + 6 * 8 - 1))
