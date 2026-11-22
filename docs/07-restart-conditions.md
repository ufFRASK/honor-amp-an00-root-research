# 重启条件与后续方向

## 43499（优先）

按代价从低到高：

1. **可读的崩溃日志**：工程机，或能临时 root / 关闭 `PANIC_ON_OOPS` 的机器，拿到 `rt_mutex_adjust_prio_chain` 的 RIP 与 faulting address，一次修正即可；
2. **可读 pstore / ramoops**：`CONFIG_PSTORE_CONSOLE` + `pstorefs` 对 shell 可读，能把 `console-ramoops` 直接读出来；
3. **换目标机复现**：先在公开有成功日志的同类目标（如 6.1.157 的 MagicPad3）上跑通载波，再按 BTF 把 0x58 布局回迁到本机；
4. **内核源码对齐**：拿到与本机 `g5859fbdbad8c` 对应的 `kernel/locking/rtmutex.c`，静态核对 `adjust_prio_chain` 的字段校验顺序与两处 `rb_erase` 的调用条件。

## 98260（次优先）

唯一门槛是观测/门控：

1. 能写 `events/kmem/*/enable`（或 `instances/`）的环境 —— 决定 cred_jar 页复用路线是否成立；
2. 不能开 tracefs 时，退化为"同 cache 重占 + 可预测 node"的思路，需要新的对象选择；
3. 新机型的 `slabinfo` 必须先看 `posix_timers_cache` 的 order 与迁移类型，本机为 order-1（8 KiB）。

## 通用判据（两条经验）

- **命中扫描必须"立即 + 5 s 复扫"**：Honor 设备的利用存在"延迟落地"（数百 ms 到数秒），只扫一次会漏报。
- **shift 类参数必须按 build 重推**，不能在 6.1.x 之间互借：`stack_fds` 帧偏移、`RANDOMIZE_KSTACK_OFFSET` 步进、`nfds` 可控字数三者共同决定可用对齐。
