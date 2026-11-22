# 工具

| 文件 | 用途 | 依赖 |
|---|---|---|
| `frame_probe.py` | 从裸 `Image` + kallsyms 静态推导 `core_sys_select` 帧大小与 `stack_fds` 偏移，并给出 `PSELECT_WAITER_WORD_SHIFT` | Python 3、`capstone` |
| `btf_check.py` | 从 `vmlinux`/`Image` 的 BTF 打印结构布局（如 `rt_mutex_waiter`、`miscdevice`、`task_struct` 相关字段） | Python 3 |
| `psel_geom.c` | 用户态零风险探针：验证 pselect 回写通道与六区域地址（**不开竞态、不写内核**） | clang（aarch64 静态） |

## 用法

```bash
# 静态几何
python3 tools/frame_probe.py Image symbols.txt
python3 tools/btf_check.py vmlinux.btf rt_mutex_waiter

# 设备上（只验证回写，不会触发漏洞）
aarch64-linux-android21-clang -O2 -static -o psel_geom tools/psel_geom.c
adb push psel_geom /data/local/tmp/ && adb shell "cd /data/local/tmp && ./psel_geom echo"
```

预期输出（本机 6.1.99）：

```
[geom] core_sys_select frame=0x1c0 stack_fds=0x50 shift=10
[echo] rc=2 errno=0 ok=1
```

> `shift=10` 是 `stack_fds` 相对 SP 的字偏移；**不是** `PSELECT_WAITER_WORD_SHIFT`（本机该值为 3，见 [docs/03](../docs/03-43499-carrier.md)）。
