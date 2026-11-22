# 可观测性与收口依据

## 结论

本机 **user 构建不提供任何 shell 可读的内核崩溃记录**，因此 43499 的消费阶段崩溃无法定位到具体字段；在拿到 RIP 之前继续换参数只能是盲试。

## 逐项核查

| 途径 | 结果 |
|---|---|
| `/proc/last_kmsg` | **不存在**（bugreport 正文：`No such file or directory`） |
| `/sys/fs/pstore` | 已挂载，`0750 system:log`（`u:object_r:pstorefs:s0`）→ shell Permission denied |
| `dmesg` / `logcat -b crash` | 不可用 / 无内核记录 |
| `dumpsys dropbox --print SYSTEM_LAST_KMSG` | `No entries found` |
| `bugreport`（13 MB，已核查） | `FS/` 无 kmsg/pstore/ramoops；`Kernel panic` / `Unable to handle` / `Internal error` **零命中**；`pstore` 命中仅为应用包名列表 |
| 用户态日志 | 可用：程序自身逐行 fsync 到应用可写目录 |

## 为什么这不是"漏洞不可利用"

- 触发层每次都能到达（`trigger-ok` + `enter-pselect` + `consumer-boost-first`）。
- 盖章阶段已证明安全（stamp-only 长时间运行不崩）。
- 崩溃集中在同一内核函数入口，与环境（SELinux、权限、命名空间）无关，属于**载波数据与内核期望不一致**；但没有 oops 就无法知道是哪一处不一致。

## 收口动作

- 停止在本机重复运行利用二进制（每次崩溃消耗一次开机，且无新信息）。
- 保留全部源码、探针、日志摘要与结论，供换机/换观测手段后接续（见 [07-restart-conditions](07-restart-conditions.md)）。
