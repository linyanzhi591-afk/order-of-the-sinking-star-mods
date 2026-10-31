# 六 mod 合集 v1.1.1-test / Six-mod bundle

本版适配 **Steam Build 26249670**。六项功能和默认按键保持不变：Shift/RB 奔跑切换、Q 俯视、P 彩色描边、粒子减量、N/M 世界暂停与单步、O 水面网格。

This release targets **Steam Build 26249670**. Features and default controls are unchanged: Shift/RB toggle run, Q camera, P class highlights, particle reduction, N/M world pause/step, and O water grid.

新版游戏改变了主程序、材质包、关卡包及全部 32 个目标水面着色器。相应钩子、原生载荷、粒子清单和着色器差量均已重建；水面着色器重新签名并通过 `dxv`，同时验证原有顶点、根签名、alpha、深度和非水面条目保持不变。

The updated game changed the executable, material package, level package and all 32 target water shaders. Hooks, native payloads, the particle manifest and shader deltas were rebuilt. Water shaders were re-signed and passed `dxv`; vertex data, root signatures, alpha, depth and non-water entries remain unchanged.

安装器继续完整备份五个目标并以可恢复事务统一提交。未知版本、其他修改、损坏备份、写入失败和中断状态均拒绝或回滚。版本不匹配错误现在明确显示支持的 Steam Build。

The installer still backs up all five targets and commits them as one recoverable transaction. Unknown versions, other modifications, damaged backups, write failures and interrupted states are rejected or rolled back. Version mismatch errors now identify the supported Steam build.

旧合集用户必须先使用旧目录中的 `recover.cmd`（如有待恢复事务）和 `uninstall.cmd`，再把本版解压到新目录。不要混用旧 `.bundle-state`。

Users of older bundles must first run `recover.cmd` when needed and `uninstall.cmd` from the old folder, then extract this release into a new folder. Do not mix old `.bundle-state` data.

离线与隔离验证已通过；Build 26249670 尚未进行实机画面和完整关卡验收，因此保留 `test` 标记。

Offline and isolated validation passed. Build 26249670 has not yet received gameplay visual or full-level acceptance, so the `test` label remains.
