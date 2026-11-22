# 被实验否掉的假设清单

按排除顺序记录。每一条都对应一次或多次实际运行，不是纸面推断。

| # | 假设 | 实验 | 预期（若假设成立） | 实测 | 结论 |
|---|---|---|---|---|---|
| 1 | 对齐只差一点，取 shift=3 | `enforce` | 越过消费，得到泄漏或写入 | 25 s 后看门狗复位（自旋/遍历不收敛） | 否 |
| 2 | shift 应为 1 | `enforce_s1` | 同上 | 立即复位（非法指针 oops） | 否 |
| 3 | 崩溃来自写目标（loggers/bootid 图） | `safetgt`（`SAFE_RB_TARGET`，读写全在假页内） | 崩溃点改变或不再崩 | 仍 `consumer-boost-first` 后立即复位 | 否 |
| 4 | 崩溃来自假锁 `owner=NULL`（用了 6.6 偏移） | `lock61`（`owner@0x18=fake_task`） | 越过 `adjust_prio_chain` | 仍同点复位 | 否 |
| 5 | 换写目标到 `ashmem_misc+0x10` 可绕过 | `ashmem`（`ASHMEM_SLIDE`） | 越过消费 | 仍同点复位 | 否 |
| 6 | `/dev/ashmem` 被拒 ⇒ 整条链堵死 | 别名 `open()` 测试 | 全部 EACCES | `/dev/ashmem` 拒绝，但 `/dev/ashmem<uuid>`（`ashmem_libcutils_device`，同一设备号 10,125）**`open_rc=0`** | **否掉**（触发端成立） |

## 仍然未被否掉的变量

崩溃发生在消费路径，而本机拿不到 oops，因此下列变量无法区分：

- `waiter->task` 的取值（伪造 task 与真实 task 的校验分支）；
- `lock->waiters` 遍历时对 top waiter 的字段读取；
- `adjust_prio_chain` 第二轮迭代对 `owner->pi_blocked_on` 的处理；
- `sched_setattr` 的目标 tid 与时机（consumer 线程是否抢在 pselect 内正确触发）。

没有 RIP/faulting address，继续改参数属于盲试，且每次都要消耗一次开机。

## 已确认的静态事实（非假设）

- `rt_mutex_waiter` 0x58、`rt_mutex_base` 6.1 顺序（BTF）。
- `selinux_state.enforcing` 在 +0（BTF + `sel_write_enforce` 反汇编）。
- 假页里 `+0x18/+0x20/+0x28` 写内核地址是 `rb_erase` 的**设计形态**，不是 bug。
- `miscdevice.fops` 在 +0x10（BTF），`ashmem_misc` 为单元素。
