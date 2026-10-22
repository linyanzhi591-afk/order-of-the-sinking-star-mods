# 六 mod 合集发行验证 / Six-mod release validation

版本 **1.1.0-test**；日期 **2026-10-22**。原五个 mod 的发行文件与版本不变；加入水面网格 **0.1.0**，O 键切换、启动默认关闭，不加入未完成的通用网格。

Version **1.1.0-test**; date **2026-10-22**. Original five-mod files and versions are unchanged. Adds Water Surface Grid **0.1.0**, off at startup and toggled with O, without the unfinished general grid.

## 本版检查 / Checks for this version

完整运行 **16 组测试，全部通过**。使用项目保留的合法样本及候选的私有临时副本；只读样本哈希未变。没有查找、安装到、卸载或控制实际游戏。

The complete suite of **16 test groups passed**, using private temporary copies of retained legitimate samples and candidates. Read-only fixture hashes remained unchanged. The actual game was not located, installed into, uninstalled or controlled.

- 原四项的16种子组合、原世界单步支持的6种组合及完整水面组合均生成相同六mod输出。
- 完整安装、重复安装保留首次基线、状态/预检、精确和重复卸载、重复恢复、卸载后重装；已有部分或全部mod的基线保留。
- 游戏运行、查询失败、未知/不一致状态、改键、未完成网格、空间不足、备份写入失败和损坏载荷均拒绝游戏写入。
- 五个目标全部备份并验证后才开始替换；第二文件写入失败自动回滚；安装/卸载中断后可恢复。
- 未知中断后修改、损坏恢复或初始备份、并发操作均受保护；预先存在的同名临时文件不被删除。
- 五个CMD入口的含空格路径与成功/失败退出码通过。
- 新增 shader 包的未知修改、水面程序/shader 不一致、旧1.0.0-test收据均拒绝，旧记录保持不变。

- All 16 original four-mod subsets, six world-step starting combinations and the complete water state produce identical six-mod outputs.
- Fresh/repeated installation preserving the first baseline, status/preflight, exact/repeated removal, repeated recovery and reinstallation; pre-existing partial/complete mod baselines are retained.
- Running game, failed query, unknown/inconsistent state, rebound keys, unfinished grid, insufficient space, backup failure and damaged payload block game writes.
- All five targets are completely backed up and verified before replacement; second-file failure rolls back; interrupted installation/removal can recover.
- Unknown post-interruption edits, damaged recovery/initial backups and concurrent operations are guarded; pre-existing scratch files are not deleted.
- All five CMD launchers passed spaced-path and success/failure exit-code checks.
- Unknown shader changes, inconsistent water executable/shaders and old 1.0.0-test receipts are rejected without changing old records.

## 水面与实机证据 / Water and gameplay evidence

独立水面发行的安装、重复、卸载、失败保护和恢复专项通过。原开发项目的隔离机器码测试重新通过：默认关闭、O-only、长按/失焦/I无效、后加载、原生上传包装器、参数/边界、重入和布局保护；窗口、按键、GPU均为桩。

Standalone water installation/repetition/removal/failure/recovery checks passed. Original isolated machine-code checks were rerun: startup-off, O-only, hold/focus/I behavior, late loading, upload wrapper, parameters/bounds, reentrancy and layout guards. Window, keyboard and GPU calls were stubs.

六mod exe SHA-256为 `5d537ef6726847d39df9e786e9e087b3135c0ca18ab9f60690ec5ee567216c29`；shader包为 `641edb243e436548dee1072ac6a0de1556774d4a26af5c2521ee4b579161e820`，与已确认候选逐字节一致。差量不重新编译/签名shader，完整输出一致性保留原32个水面程序的签名及保真结论。

Executable SHA-256: `5d537ef6726847d39df9e786e9e087b3135c0ca18ab9f60690ec5ee567216c29`; shader package: `641edb243e436548dee1072ac6a0de1556774d4a26af5c2521ee4b579161e820`, byte-identical to the confirmed candidate. Deltas do not recompile/re-sign shaders; exact matching retains the 32 original water programs' validated signatures and fidelity.

用户于 **2026-10-22** 确认水面可用并兼容现有mod。这是用户实机反馈，本次没有重新启动游戏，不扩大为全部关卡、水域或设备验收。原三项mod及合集的test标记保留。

On **2026-10-22**, the user confirmed water usability and compatibility. This is user-reported gameplay evidence; this run did not launch the game or expand it into acceptance of every level, water area or device. The three original test labels and bundle test label remain.

## 分发边界 / Distribution limits

白名单仅含安装器、源码、载荷、差量、文档和校验清单，不含完整exe、资源包、原版资源、存档、本机备份、临时样本或旧Git历史。原五个独立仓库、旧合集tag和Release保留。升级须先用旧合集恢复/卸载，再在新目录安装。

Allowlist packaging includes installers, source, payloads, deltas, documentation and checksums; no complete executable/package, original assets, saves, local backups, temporary fixtures or old Git history. The original five repositories and old bundle tags/Releases remain. Recover/remove with the old bundle before installing in a new folder.
