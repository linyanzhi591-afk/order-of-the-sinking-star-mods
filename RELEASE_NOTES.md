# 六 mod 合集 v1.1.0-test / Six-mod bundle

在原五项之后加入**水面网格显示 0.1.0**：O 键切换，启动默认关闭。顺序为奔跑 → 俯视 → 描边 → 粒子 → 世界单步 → 水面。不包含未完成的通用网格显示 mod，也没有 I 地面开关。

Adds **Water Surface Grid 0.1.0** after the original five mods: O toggles, off at startup. Order: toggle-run → camera → highlight → particles → world-step → water. The unfinished general-grid mod and I ground toggle are excluded.

管理目标增为五个，新增 `data/shaders.package` 的预检、完整备份、统一提交及精确恢复。水面原生载荷保持不变，32 条着色器差量重建后与已确认候选逐字节一致。

Five files are now managed, adding preflight, complete backup, transaction commit and exact restoration for `data/shaders.package`. The native water payload is unchanged; 32 shader deltas reconstruct the exact confirmed candidate.

**旧合集用户：先用旧 1.0.0-test 的 recover/uninstall 处理原安装，再将新版解压到新目录；不要覆盖旧目录或混入旧收据。** 已单独安装原五项、没有旧合集收据时，可由新版保留原状态并添加水面层。

**Old-bundle users: finish recovery/uninstallation using 1.0.0-test, then extract this release into a new folder. Do not overwrite the old folder or mix its receipts into this version.** Existing standalone five-mod installations can be preserved as the new baseline while water is added.

需要 Windows x64、64位 Python 3.10+。完整解压后运行 `install.cmd`；正常卸载 `uninstall.cmd`，中断恢复 `recover.cmd`，保留 `.bundle-state/`。重复操作不替换首次备份，未知文件或损坏备份拒绝覆盖。

Requires Windows x64 and 64-bit Python 3.10+. Extract fully and run `install.cmd`; use `uninstall.cmd` for normal removal and `recover.cmd` after interruption. Keep `.bundle-state/`. Repetition retains the first baseline, and unknown changes/damaged backups are rejected.

水面版本已由用户于2026-10-22确认可用并与其他mod兼容；本次只使用项目内样本的临时副本验证发行和整合，未查找或控制实际游戏。保留其他mod的测试版标记与全关卡验证边界。独立水面仓库及下载入口见总 README；ZIP 与 SHA-256 清单附于此 Release。

The user confirmed water usability and compatibility on 2026-10-22. This release/integration run only uses temporary copies of retained project fixtures, without locating or controlling the actual game. Other test labels and all-level validation limits are retained. See README for standalone water links; the ZIP and SHA-256 list are attached.
