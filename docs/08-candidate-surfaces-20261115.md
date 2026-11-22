# 2026-11-15 候选面批次（参考资料）

本批与 98260 / 43499 主线并列，属于同一台设备（AMP-AN00，`6.1.99-android14-11-g5859fbdbad8c`，user 构建，Enforcing，shell `uid=2000`）上的**旁路排查**。每节结构一致：目标对象与版本 / 原语或缺陷位置 / 窗口量级 / 前置条件与权限 / 判定 / 被什么实测排除。

> 判定用语严格区分三类：
> **A. 可提权候选**（可控写 / 可命中 UAF / 越界写 / 类型混淆）；
> **B. 代码有洞但环境打不到**（原语成立，本机无法打开或无法稳定命中）；
> **C. 有缺陷但仅 DoS**（能崩，不能写、不能提权）。
> 本批没有任何一项落在 A。

## 1. eventpoll 引用计数 UAF（CVE-2025-38349 一族）——判定 B

- **目标对象**：`struct eventpoll`，`sizeof = 0xc0 = 192` → `kmalloc-192`（`do_epoll_create` 内联 `ep_alloc`）。源码：`fs/eventpoll.c`。
- **缺陷位置**：`ep_clear_and_put()` `:787-829`——`:824` 递减引用、`:825` `mutex_unlock`、`:827-828` 在需要 dispose 时 `ep_free()`→`kfree(ep)`；设备侧 `ep_clear_and_put @0xffffffc008273dfc` 指令序为 `lock → ldaddl(dec) → unlock → 慢路径 free`。
- **窗口量级**：**2–3 ns**。来源是 `__mutex_unlock_slowpath @0xffffffc009080ce8` 中 `CAS` 释放成功后到 `d5c` 的 4–6 条指令；`raw_spin_lock` 区段内抢占已关闭，不能计为窗口。
- **前置条件与权限**：需要多个 closer 与 waiter-spinner 在同一 ep 上竞争；shell 可创建 epoll，但无法扩大窗口（无 `userfaultfd`、无 FUSE、无 `SCHED_FIFO` 特权）。
- **判定**：**B（代码有洞但环境打不到）**。递减与释放的顺序确实"先 dec 后 unlock"，但窗口只有 ns 级，且已被两个结构性事实封死：最后一个引用永远由 `ep_clear_and_put` 自己递减、`ep_free` 前已无并发引用点。
- **实测排除**：**2.0M 次候选 unlock、0 命中**；按 `slept>20 µs` 估"释放时有等待者"的候选 unlock ≈ 0，实测 `p ≤ 1.5×10⁻⁶`（95% 上界 3/2M），比模型低三个数量级 ⇒ 不是喷涂形态问题，是窗口本身不可命中。

## 2. kgsl（`msm_kgsl.ko`）——判定 B（整面判死，非 DoS）

- **目标对象**：`/dev/kgsl-3d0`（478,0，`gpu_device`，DAC 0666）；驱动内 `kmalloc-192` 对象：cmd drawobj（`kgsl_drawobj_cmd_create` `0x75474` `kzalloc(0xa8)`）、sync drawobj（`kgsl_drawobj_sync_create` `0x749dc` `kmalloc_trace(0x98)`）、syncpoint 槽（`add_synclist` `0x76b28`，槽 0x88 B）。
- **缺陷位置**：逐接口审计（create/destroy、drawobj、syncpoint、GPU 命令提交、`IOCTL_KGSL_*` 全表），**未见可控写**；引用计数自洽，无 UAF；仅两处"确定性泄漏"（单线程可触发），属 DoS 级。
- **窗口量级**：不适用（未找到可命中的竞态或越界）。
- **前置条件与权限**：shell 域**可 open 并到达 handler**——实测三档：非法 req `0xdeadbeef` → `ENOTTY(25)`；合法 req + NULL 指针 → `EFAULT(14)`；合法 req + 有效缓冲 → `ENODEV(19)`。三档都不是 `EPERM`，说明 ioctl 分发确实执行到了驱动内部。
- **判定**：**B**。可达但无原语：整面（本轮范围）判死；不是"仅 DoS"（泄漏是 DoS 级，但主结论是无内存破坏）。
- **实测排除**：三档 errno 证明可达性；泄漏仅计数增长，不指向释放路径。

## 3. f2fs 私有 / 压缩 / atomic 面——判定 C（唯一内存安全缺陷仅 DoS）

- **目标对象**：`/data` 为 f2fs（`background_gc=on`、`compress_mode=user`、`discard`）；私有 ioctl（`HP_PREALLOC` 等）、压缩、GC、checkpoint 四个方向。
- **缺陷位置**：唯一真实内存安全缺陷是 **`atomic_inode` 悬垂指针**——`inode.c:811-814` 在**无锁**下执行 `clear_inode_flag(cow, FI_COW_FILE); atomic_inode=NULL; iput(cow)`；使用侧 `f2fs_is_cow_file(inode) ? F2FS_I(inode)->atomic_inode->i_mapping : ...`。上游 `e0288584ba`（2026-05-21）修复。相关入口 `f2fs_ioc_start_atomic_write @0xffffffc008321b28`。
- **窗口量级**：free 走 RCU，回收窗口不可控；前台 GC ioctl 需要 `CAP_SYS_ADMIN`，本机 shell 没有。
- **前置条件与权限**：只能由**内核 `background_gc`** 命中（无需用户权限，但时机不可控）；用户态要在前台触发则需要 `CAP_SYS_ADMIN`，shell 不满足。
- **判定**：**C（有缺陷但仅 DoS）**：命中后果是 `BUG_ON`/GPF → panic，没有可用的写原语，**不是提权**。
- **实测排除**：其余三类差异（`f2fs_find_consecutive_secs` 取第一个满足段等）判为非内存安全；D9/D10 需要构造镜像挂载，shell 无权限，不在判据内。

## 4. perf ring buffer mmap 竞态（89791 / 23248 族）——判定 B（本树上限仅 DoS/无 UAF）

- **目标对象**：`perf_event` 的 `mmap_count` 与 ring buffer 生命周期；本树仍是 `atomic_t` 语义（`atomic_dec_and_mutex_lock`）。
- **缺陷位置**：`perf_mmap_close` 与 `perf_mmap` 的计数/映射竞态；CVE-2026-89791 需要 `refcount_set(&event->mmap_count, 1)` 这种"1→1 隐形写"，CVE-2026-23248 需要 `refcount_t` 的 addition-on-0 检查，**本树 `atomic_t` 两者都不具备**。
- **窗口量级**：约 **5 条指令（ns 级）**，必须靠抢占撑开；mmap 侧 `rb_alloc` 的 µs 级长路径不拓宽 close 侧的缝。
- **前置条件与权限**：shell 实测 `perf_event_open` OK（`perf_event_paranoid=-1`）、`mmap(2 pages)` OK ⇒ 面可达。
- **判定**：**B**：可达、窗口存在，但本树命中也不构成 UAF（计数语义不同）；若换到 6.18+ 的 `refcount_set` 形态才是另一种问题。
- **实测排除**：权限与 mmap 可用性已实测；语义差异由符号/指令确认（`atomic_dec_and_mutex_lock`，无 `refcount_dec_and_mutex_lock`）。

## 5. 厂商私有面（logger / hw_memcheck / tango32 / ashmem 别名）——判定 B+C 混合

| 对象 | 缺陷位置 | 可达性 | 判定 |
|---|---|---|---|
| `logger.ko`（`/dev/file_deleted`、`/dev/hwlog_exception`） | hwlog 写路径长度/边界检查可绕，但落点与内容不可控 | shell 可 open（RW） | **C**：有缺陷，不构成可控写 |
| `hw_memcheck.ko`（同节点 ioctl 转发） | `0xAF01–0xAF0B` 家族缺 pid 权限校验 | 分发可达，handler 执行 | **C**：缺校验 ≠ 内存破坏，无 UAF/越界写 |
| `tango32.ko`（`/dev/tango32`） | `0x4008/0xc018/0x8004/0x4010/0x400c` 命令族 | shell 可 open | **B**：输入校验完整，未见类型混淆 |
| ashmem（内建） | 无缺陷；别名 `/dev/ashmem<uuid>`（`ashmem_libcutils_device`，同 10,125）可 open | 可 open | 仅作为 43499 的写目标备选 |

- **前置条件**：上述节点 DAC 均为 0666，shell 可 open；被 SELinux 拒的私有节点族已单列（策略放宽才成为直接面）。
- **实测排除**：logger/hw_memcheck/tango32 的常量与分发表逐一反汇编核对，未见"用户可控 → 内核写"的路径。

## 6. 汇总

| # | 面 | 分类 | 一句话 |
|---|---|---|---|
| 1 | eventpoll 38349 | **B** | 窗口 2–3 ns；2.0M 候选 unlock 零命中（p ≤ 1.5e-6） |
| 2 | kgsl | **B** | ioctl 三档可达（ENOTTY/EFAULT/ENODEV），但无原语，整面判死 |
| 3 | f2fs atomic_inode | **C** | 唯一内存安全缺陷，仅 background_gc 可命中，需 CAP_SYS_ADMIN 才能前台触发，后果 panic |
| 4 | perf ring | **B** | 窗口 ~5 条指令；本树 `atomic_t`，即使命中也无 UAF |
| 5 | 厂商私有 | **B/C** | logger/hw_memcheck 有缺陷不可控；tango32 无类型混淆 |

## 7. 方法学备注

- 分类 B 与 C 不能混写：B 是"原语成立但环境不给你机会"，C 是"环境给你机会但原语只能崩"。
- 所有"可达"结论都以实测 errno / 实际 open 结果为准，不以 `ls -l` 权限位推断。
- 本批结论早于 43499 结案，作为"为什么没有继续在这些面上投入"的依据保留。
