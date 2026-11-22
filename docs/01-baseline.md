# 设备基线

| 项 | 值 |
|---|---|
| 机型 | HONOR 300 PRO，**AMP-AN00** |
| SoC | Snapdragon 8 Gen 3 (SM8650) |
| 系统 | Android 15 / MagicOS 9.0.0.189(C00E187R201P7) |
| 内核 | `6.1.99-android14-11-g5859fbdbad8c`，构建于 2025-07-22 08:25:07 UTC，clang 17.0.2 |
| 安全补丁 | SPL 2025-09-01 |
| 启动 | Bootloader 锁定，user 构建 |
| SELinux | **Enforcing** |
| 调试开关 | `kasan=off`；KFENCE（500 ms / 63 objects）；`PANIC_ON_OOPS=y`；`INIT_ON_ALLOC_DEFAULT_ON=y` |
| 命名空间 | `USER_NS=n`、`NF_TABLES=n` |
| 身份 | `uid=2000(shell)`，`u:r:shell:s0`，无 root |
| 崩溃观测 | **无** `/proc/last_kmsg`；`/sys/fs/pstore` 0750 `system:log`；dropbox 无 `SYSTEM_LAST_KMSG` |

## 关键派生值（本机 vmlinux + kallsyms + BTF 实测）

| 符号/结构 | 值 |
|---|---|
| kallsyms base | `0xffffffc008000000` |
| 线性别名 | 符号地址 − `0x4008000000`（如 `init_task` `0xffffffc00a09ee00` → `0xffffff800209ee00`） |
| `selinux_state.enforcing` | `+0x00`（BTF；`sel_write_enforce` 中 `strb` 落在指针首字节） |
| `rt_mutex_waiter` | size `0x58`：`pi_tree+0x18 / task+0x30 / lock+0x38 / wake_state+0x40 / prio+0x44 / deadline+0x48` |
| `rt_mutex_base` | `wait_lock+0x00 / waiters+0x08 / owner+0x18`（6.1 旧布局） |
| `miscdevice` | `minor+0 / name+0x08 / **fops+0x10**` |
| `ashmem_misc` | `0xffffffc00a51a028`（内建，非数组） |
| `task_struct.real_cred / cred` | `+0x830 / +0x838` |
| `core_sys_select` | 帧 `0x1c0`，`stack_fds` @ `SP+0x50`，`do_futex` 帧 `0x60`，`__arm64_sys_pselect6` 帧 `0x90` |

## tracefs 实测（决定性）

| 探测 | 结果 |
|---|---|
| `events/kmem/{kmem_cache_alloc,kmem_cache_free,mm_page_alloc,mm_page_free}/enable` 写 1 | 全部 `rc=1, Permission denied` |
| `trace_pipe` / `trace_pipe_raw` | 0 字节（EACCES） |
| `set_event_pid` | Permission denied |
| `instances/<name>` 自建 | `mkdir` Permission denied |
| `ls -Z` | `debugfs_tracing_debug` ← shell 域无权限；挂载本身 `gid=3012(readtracefs)`，DAC 放行，**是 SELinux 拒绝** |

结论：本机 shell 无法使用任何分配跟踪能力，也没有实例绕法。
