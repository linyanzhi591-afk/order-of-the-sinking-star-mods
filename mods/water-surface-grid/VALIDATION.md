# 发行验证 / Release validation

日期：2026-10-22；版本：0.1.0。用户已确认开发聊天安装的水面版本可正常使用，并与现有 mod 兼容；此记录不扩大为全关卡验收。

Date: 2026-10-22; version: 0.1.0. The user confirmed the development-installed water version works and is compatible with existing mods. This does not constitute all-level acceptance.

- 从项目保留的候选样本生成差量；不重编译原生载荷，不重新签名或改写 shader。发行适配器重建的 exe 和 shader package 与用户已确认版本逐字节一致：`5d537ef6…`、`641edb24…`。
- 重新运行原开发项目的隔离机器码测试：启动关闭、只查询 O、O 长按去重、失焦/I 无效、后加载、原生上传包装器、参数/边界、重入与长度/布局防护通过；窗口、按键、GPU 全部为桩。
- 独立发行入口在临时副本中通过安装、重复安装保留首次基线、状态/预检、精确卸载、重复卸载、第二文件失败自动回滚、中断恢复、重复恢复、未知资源拒绝；不管理的材质样本保持不变。
- 基础 shader 包和水面包只在本机样本与临时目录中使用。发行包仅含复制指令、新增差量、原生小载荷和源码，不附带完整游戏文件、资源包、原版资源、安装记录或备份。

- Deltas were generated from retained project candidates. Native payloads were not recompiled and shaders were not re-signed or rewritten. Reconstructed executable and shader package are byte-identical to the user-confirmed version (`5d537ef6…`, `641edb24…`).
- Original isolated machine-code checks were rerun: startup-off, O-only queries, held-key filtering, focus/I behavior, late loading, native upload wrapper, parameters/bounds, reentrancy and length/layout guards passed. Window, keyboard and GPU interfaces were stubs.
- The standalone release passed temporary-copy installation, repeated-install baseline retention, status/preflight, exact/repeated removal, automatic rollback after second-file failure, interrupted/repeated recovery and unknown-resource rejection. An unmanaged material sentinel remained unchanged.
- Original and water shader packages are used only as local fixtures and temporary copies. Distribution includes copy instructions, added deltas, small native payloads and source, without complete game files, packages, original assets, installation records or backups.

没有查找或操作实际游戏。本次不重新进行画面或游玩验收。原开发验证的 32 个水面程序、其他条目保真、DXIL 签名与原始着色计算结论，通过完整输出哈希一致性保留；用户确认仍不代表所有水域、设备和后续版本都已覆盖。

The actual game was not located or operated. No new visual or gameplay acceptance was performed. Existing validation of the 32 water programs, untouched resources, DXIL signatures and original math is retained through exact complete-output hash matching. User confirmation still does not cover every water area, device or future update.
