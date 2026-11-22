# 鸣谢

本研究的**结论与实验**均为本机实测；下列上游项目提供了思路、框架或工具。凡是"沿用了思路但未直接使用代码"的，也一并注明。

## 载波与利用框架

- **[IonStack](https://github.com/) / GhostLock 系（pselect 载波）** —— 提供 futex PI + pselect 栈上伪造 waiter 的整体框架与 `PSELECT_WAITER_WORD_SHIFT` 概念；本仓库的 shift 推导、res-encode 验证与消费阶段实验都建立在这套思路上。
- **[magicpad3-root-research](https://github.com/saltlyfish666/magicpad3-root-research)** —— 同 bug 在 6.1.157 荣耀设备上的公开研究：黄金命中日志、失败法证、`ashmem_miscs+0x10 → fops → pipe → init_task → cred` 的链路结构。本仓库的写目标语义与判据表参考了它；其核心利用未公开，我们的 0x58 布局参数是自行重推的。
- **[TimerRoot](https://github.com/MVN123-ai/TimerRoot)** —— 98260 的 conf 驱动实现（`boot.img` 静态推导 `do_timer_create` 的 `kmem_cache_alloc` 返回址、cred 零写）；本仓库的静态 conf 推导方法沿用其思路。
- **[cve-2026-98260-ppg-an00](https://github.com/yxc0915/cve-2026-98260-ppg-an00)** —— 98260 在另一台荣耀机上的移植笔记，提供了"延迟落地"等现场经验与 conf 字段清单。
- **[cve-2026-43499-aak-an00](https://github.com/hui191/cve-2026-43499-aak-an00)** —— 43499 在另一台荣耀机上的纯文档研究：`rt_sigreturn` 载波、线性映射别名免 KASLR、两段式 cred 改写等替代路径。
- **[CVE-2026-43499-Poc-Analysis](https://github.com/Linuxoid-cn/CVE-2026-43499-Poc-Analysis)** —— `LD_PRELOAD` 注入与"从 boot.img 生成 target.h"的工程化做法。

## 工具与运行时

- **[vmlinux-to-elf](https://github.com/marin-m/vmlinux-to-elf)** —— 从裸 `Image` 重建带符号的 ELF，是本仓库所有 kallsyms/BTF 推导的基石。
- **[KernelSU](https://github.com/tiann/KernelSU)** —— 提权后的 `ksud late-load` 交付端（本机未走到这一步）。
- **[Shizuku](https://github.com/RikkaApps/Shizuku)** —— 无 root 获取 shell 上下文的方案，是全部上机实验的执行前提（本仓库未包含其代码）。
- **[ExtractKit](https://github.com/qq2770355800/ExtractKit)** —— 内置多机型内核 profile；我们用它交叉核对了本机 `g5859fbdbad8c` 的若干符号地址（结论一致），但未使用其利用载荷。
- **capstone** —— 反汇编与函数对比工具。

## 说明

- 本仓库**不包含**上述任何项目的利用二进制或私有代码；只引用公开思路与公开文档。
- 带"实测"的结论（触发时序、载体命中数、slab 参数、帧几何、六次崩溃的停点、tracefs 拒绝、bugreport 内容）均为本机独立测量，未照抄上游。
