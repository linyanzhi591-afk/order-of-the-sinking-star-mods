# 五 mod 合集 v1.2.0-test / Five-mod bundle

本版适配 **Steam Build 26249670**，从整合包中移除水面网格。保留五项功能：Shift/RB 奔跑切换、Q 俯视、P 彩色描边、粒子减量、N/M 世界暂停与单步。

This release targets **Steam Build 26249670** and removes the water grid from the bundle. Five features remain: Shift/RB toggle run, Q camera, P class highlights, particle reduction, and N/M world pause/step.

水面网格源码、构建入口、独立安装器、载荷和文档均不再进入整合发行包。仅保留一个严格哈希限定的旧层移除适配器，使 1.1.1-test 可直接迁移为五模组状态；适配器不能生成或安装水面网格。

Water-grid source, build entry points, standalone installers, payloads and documentation are no longer shipped in the bundle. A hash-locked legacy removal adapter remains solely to migrate 1.1.1-test to the five-mod state; it cannot generate or install a water grid.

安装器继续完整备份五个目标并以可恢复事务统一提交。未知版本、其他修改、损坏备份、写入失败和中断状态均拒绝或回滚。版本不匹配错误现在明确显示支持的 Steam Build。

The installer still backs up all five targets and commits them as one recoverable transaction. Unknown versions, other modifications, damaged backups, write failures and interrupted states are rejected or rolled back. Version mismatch errors now identify the supported Steam build.

1.1.1-test 用户可将本版解压到新目录后直接安装。若旧目录存在待恢复事务，必须先用旧版 `recover.cmd` 完成恢复；不要混用旧 `.bundle-state`。

Users of 1.1.1-test can extract this release into a new folder and install directly. Complete any pending old transaction with the old `recover.cmd` first, and do not mix old `.bundle-state` data.

离线与隔离验证已通过；Build 26249670 尚未进行实机画面和完整关卡验收，因此保留 `test` 标记。

Offline and isolated validation passed. Build 26249670 has not yet received gameplay visual or full-level acceptance, so the `test` label remains.
