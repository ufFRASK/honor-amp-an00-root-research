# HONOR 300 PRO (AMP-AN00) 提权研究笔记
## 目前进度：项目暂停，CVE-2026-43499和CVE-2026-98260（同机理64560）全部无法推进（[重启条件与后续方向](docs/07-restart-conditions.md)）

> **关于本仓库**
>
> - 本仓库的文档、分析与整理文字由 **AI 辅助生成**。
> - 实验在真实设备 **AMP-AN00（6.1.99-android14-11-g5859fbdbad8c）** 上由人工配合执行：命令、崩溃与日志均由人在设备上操作和采集，文中带"实测"的结论有对应运行记录支撑。
> - 引用前请自行复核，尤其是 **43499 消费阶段**：因本机无法获取 oops，该阶段只有"崩溃位置一致"的观测，没有可定位到具体字段的定论。
> - 本仓库**不含任何可利用二进制**（无 exploit、无镜像、无日志原件），只有文档与只读/零风险的小工具。

HONOR 300 PRO / **AMP-AN00** / Snapdragon 8 Gen 3 (SM8650) / Android 15 (MagicOS 9) 上的两条公开提权路线：

| 路线 | 结论 | 文档 |
|---|---|---|
| CVE-2026-98260（POSIX CPU timer UAF） | 触发层确定性成立；六类通用载体跨 cache 零命中；cred_jar 路线依赖 tracefs 分配跟踪，本机 **SELinux 全拒** ⇒ 环境死 | [docs/02](docs/02-98260-64560.md) |
| CVE-2026-43499（futex PI 栈上假 waiter） | 载波几何与盖章已验证；消费阶段（`rt_mutex_adjust_prio_chain`）六次崩溃，六个假设全部被实验否掉；本机 **无 oops 通道** ⇒ 结案 | [docs/03](docs/03-43499-carrier.md)、[docs/04](docs/04-excluded-hypotheses.md) |

## 目录

- [设备基线](docs/01-baseline.md)
- [98260 / 同机理 64560](docs/02-98260-64560.md)
- [43499：载波、盖章与消费崩溃](docs/03-43499-carrier.md)
- [43499：被否掉的假设清单](docs/04-excluded-hypotheses.md)
- [可观测性与收口依据](docs/05-observability.md)
- [其它排查面（eventpoll / kgsl / f2fs / perf / 厂商私有）](docs/06-other-surfaces.md)
- [2026-11-15 候选面批次（eventpoll / kgsl / f2fs / perf / 厂商私有，逐面判据）](docs/08-candidate-surfaces-20261115.md)
- [重启条件与后续方向](docs/07-restart-conditions.md)
- [工具](tools/README.md)
- [鸣谢](ACKNOWLEDGEMENTS.md)

## 一句话

**98260 与 43499 在本机都不是「漏洞不成立」，而是「环境不允许把它变成可控写并观测」**：前者卡在 tracefs 权限，后者卡在内核崩溃日志不可读。两条线的判据、实验方法与被排除项都在本仓库里，换机或拿到可读 pstore 后可以直接接续。

## 说明

- 全部结论基于**只读**分析与用户手动执行的少量用户态程序；仓库不含利用二进制、日志原件、镜像或设备标识。
- 带「实测」标记的是我们在这台设备上跑出来的；带「引用」标记的是沿用上游公开思路/代码。
