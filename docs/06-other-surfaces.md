# 其它排查面

均为本仓库对应的设备（`6.1.99-android14-11-g5859fbdbad8c`，SM8650，Enforcing，无 root）上的静态审计结论。

| 面 | 结论 | 死因 |
|---|---|---|
| **eventpoll**（CVE-2025-38349 一族） | 代码形态仍是"修前"：`ep_clear_and_put` 顺序为 `mutex_lock → ldaddl(引用递减) → mutex_unlock → 慢路径 kfree`，即 **unlock 之后才 dec** | 可利用窗口为 ns 级精确竞争，无可控放大手段；`EPOLL_CTL_DEL` 路径无法拉长窗口 |
| **kgsl**（`msm_kgsl.ko`） | 全接口审计：`kmalloc-192` 对象与相关 ioctl 无"用户可控 → 内核写"的可用链；GPU 侧对象生命周期由驱动自身锁保护 | 应用侧无法在 untrusted 域触发目标路径（权限/SELinux 面），无稳定 reclaim |
| **f2fs 私有扩展** | 四个方向（`FS_IOC_*` 私有 ioctl、压缩、GC、checkpoint）逐一审计，无越界写/可控 UAF | 私有扩展的输入校验完整；需挂载权限与特定镜像 |
| **perf ring mmap 竞态** | 仍用 `atomic_t` 语义（`atomic_dec_and_mutex_lock`），不是 `refcount_t`；竞态存在 | 竞态窗口不可控，且 `perf_event_paranoid`/权限面在高版本 Android 上收紧 |
| **厂商私有：`logger.ko`** | hwlog 写路径"有缺陷但不可控"：长度/边界检查可绕，但落点与内容不对齐到可控写 | 无地址可控、无对象可控 |
| **厂商私有：`hw_memcheck.ko`** | `0xAF01–0xAF0B` 家族仍在；缺 pid 权限校验 | 缺校验 ≠ 内存破坏；无 UAF/越界写 |
| **厂商私有：`tango32.ko`** | `0x4008/0xc018/0x8004/0x4010/0x400c` 命令族未变 | 输入校验完整，未见类型混淆 |
| **OTA 6.1.128（待升级包）** | 与 6.1.99 在已知面**无利用性差异**：eventpoll/98260/perf 指令级一致；厂商三模块仍在、分发表未变；kgsl 模块存在且体积微变 | 升级不会让已知面变可利用；SPL 前移只减少未知面 |

## 备注

- 上述面的完整报告保存在本地（未公开），本仓库只保留结论与方法，避免直接可用的利用步骤。
- 若后续要重开任一方向，优先次序：eventpoll（需要窗口放大）→ kgsl（需要可触发上下文）→ perf（需要降 paranoid）。
