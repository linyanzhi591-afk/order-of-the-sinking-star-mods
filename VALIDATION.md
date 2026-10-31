# 五 mod 合集发行验证 / Five-mod release validation

版本 **1.2.0-test**；日期 **2026-10-31**；目标 **Steam Build 26249670**。

Version **1.2.0-test**; date **2026-10-31**; target **Steam Build 26249670**.

## 本版检查 / Checks for this version

- 水面网格源码、构建入口、独立安装器、载荷、差量和文档已从整合发行文件中移除。
- 只读旧层移除适配器仅接受 1.1.1-test 的完整主程序与着色器哈希；状态不一致、未知版本或任意字节变化均在写入前拒绝。
- 五模组输出不再修改 `shaders.package`。旧六模组输入会恢复已核验的基础着色器包，并精确拆除主程序尾部水面层。
- 16 项临时副本回归全部通过，覆盖 16 种四 mod 子组合、世界单步组合、旧水面层迁移、完整安装、重复安装、精确卸载、恢复、失败回滚、损坏备份、并发锁、空间与未知版本保护。
- 测试样本哈希保持不变，测试未启动游戏或写入实际游戏目录。
- 随后按用户授权迁移实际游戏；事务备份和最终哈希验证通过，只替换主程序与着色器，另外三个目标资源保持不变。未启动或控制游戏。

- Water-grid source, build entry points, standalone installers, payloads, deltas and documentation were removed from the bundle release files.
- The read-only legacy remover accepts only the complete 1.1.1-test executable and shader hashes. Inconsistent states, unknown versions and any byte changes are rejected before writes.
- The five-mod output no longer modifies `shaders.package`. A legacy six-mod input restores the verified base shader package and precisely removes the executable's appended water layer.
- All 16 temporary-copy regression tests passed, covering all 16 four-mod subsets, world-step combinations, legacy-water migration, full installation, repetition, exact removal, recovery, rollback, damaged backups, locking, disk-space and unknown-version guards.
- Fixture hashes remained unchanged; tests neither launched the game nor wrote to the actual game directory.
- The actual game was then migrated with user authorization. Transaction backups and final hashes passed; only the executable and shader package changed, while the other three managed resources remained unchanged. The game was not launched or controlled.

## 已验证输出哈希 / Verified output hashes

- `sinking_star.exe`：`31b5d25848666ea275d6d04d3d5ca7c676e0822a88360e630ebd6f092c000e9f`
- `data/shaders.package`：`405510e3856cd1988fe15b53bceb1fadd3be69830f67d6faea0f6b1678627104`
- `data/materials.package`：`856bcf7033447f50354ce5fb61e3d8e83f36067ffbdbe09514902b42a156cbdb`
- `data/levels.package`：`6c5af3666d3998bf5e42162200f9c7d814d8284f9dca6a1ecf898f8f45871a7c`
- `data/mesh_outlines.mesh_outlines`：`31d1cf232020a751c1f62251791a80ced9a5f0a9053accb529922936adffc4d0`

## 验收边界 / Acceptance boundary

上述结果证明旧水面层拆除、五模组构造、可逆性和安装事务符合预期。未进行本版实机启动、画面、输入和完整关卡验收，因此保留测试版标记。

These results establish legacy-water removal, five-mod construction, reversibility and installer transaction behavior. This release has not received gameplay startup, visual, input or full-level acceptance, so the test label is retained.

发行白名单仅含安装器、源码、必要载荷、文档、校验清单及旧层移除适配器，不含水面网格实现、完整游戏程序、资源包、存档、备份、测试样本或 Git 历史。

The release allowlist contains installers, source, required payloads, documentation, checksums and the legacy removal adapter. It excludes the water-grid implementation, complete game executables/packages, saves, backups, test fixtures and Git history.
