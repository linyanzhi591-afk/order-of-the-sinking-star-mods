# 六 mod 合集发行验证 / Six-mod release validation

版本 **1.1.1-test**；日期 **2026-10-30**；目标 **Steam Build 26249670**。

Version **1.1.1-test**; date **2026-10-30**; target **Steam Build 26249670**.

## 本版检查 / Checks for this version

- 新版主程序钩子和全局地址逐函数迁移；奔跑、俯视、描边、世界单步载荷重新编译，无新增导入或运行时重定位。
- 粒子字段结构保持兼容，按新版 `levels.package` 重新生成 651 项字段修改；563 个环境效果减半、75 个火焰附属效果及 13 个光束附属效果关闭。
- 32 个目标水面像素程序全部由新版原始着色器重建、签名并通过 `dxv`；16 个地面变体和其余 2800 个条目保持逐字节不变。
- 水面原生隔离测试通过：默认关闭、仅 O 键、长按/失焦/I 无效、后加载、原生上传包装器、参数边界、重入和未知布局保护。
- 奔跑、俯视、描边和世界单步的隔离机器码/载荷行为通过；最终组合通过 Windows x64 映像检查。
- 合集临时副本回归覆盖 16 种四 mod 子组合、完整安装、重复安装、精确卸载、恢复、已有部分状态、失败回滚、损坏备份、并发锁、空间与未知版本保护。
- 所有测试使用工作区私有副本；没有启动游戏，也没有写入实际游戏目录。

- Executable hooks and globals were migrated function by function. Toggle-run, camera, highlight and world-step payloads were rebuilt without new imports or runtime relocations.
- Particle field layout remained compatible; 651 field edits were regenerated from the new `levels.package`: 563 ambient effects reduced, 75 flame auxiliaries and 13 beam auxiliaries disabled.
- All 32 target water pixel shaders were rebuilt from new originals, signed and passed `dxv`; 16 ground variants and all other 2800 entries remain byte-identical.
- Isolated water-native checks passed startup-off, O-only, hold/focus/I behavior, late loading, the original upload wrapper, bounds, reentrancy and unknown-layout guards.
- Isolated payload behavior passed for toggle-run, camera, highlight and world-step; the final composition passed Windows x64 image validation.
- Temporary-copy bundle regression covers all 16 four-mod subsets, installation, repetition, exact removal, recovery, partial starting states, rollback, damaged backups, locking, disk-space and unknown-version guards.
- All checks used private workspace copies. The game was not launched and the actual game directory was not written.

## 产物哈希 / Candidate hashes

- 六 mod 主程序：`a2433c02df3d6de2de4d3c152aa3328e778291bb7a2eea2464b7cba3b6884b5e`
- 水面着色器包：`1b6809717a8c1dd401a7d5cb8bb90b1e1e18bb586da9ca914d1076f4b23b8f16`

## 验收边界 / Acceptance boundary

上述结果证明补丁构造、可逆性、签名、资源范围和安装事务符合预期。Build 26249670 尚未进行实机启动、画面、输入和完整关卡验收；实机结果未知，保留测试版标记。

These results establish patch construction, reversibility, signing, resource scope and installer transaction behavior. Build 26249670 has not yet received gameplay startup, visual, input or full-level acceptance; runtime results remain unknown and the test label is retained.

发行白名单仅含安装器、源码、载荷、差量、文档和校验清单，不含完整游戏程序、资源包、存档、备份、测试样本或 Git 历史。

The release allowlist includes only installers, source, payloads, deltas, documentation and checksums. It excludes complete game executables/packages, saves, backups, test fixtures and Git history.
