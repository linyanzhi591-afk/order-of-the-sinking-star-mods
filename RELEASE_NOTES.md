# 五 mod 一键安装合集 v1.0.0-test / Five-mod bundle

一个 ZIP、一个根目录 `install.cmd`，按奔跑 → 俯视 → 描边 → 粒子 → 世界单步的顺序生成并安装全部五个已发布 mod。下载后完整解压，安装前正常退出游戏。需要 Windows x64 与 64 位 Python 3.10+，不包含未完成网格。

One ZIP and one root `install.cmd` build and install the five published mods in order: toggle-run → camera → highlight → particles → world-step. Extract fully and exit the game before installing. Requires Windows x64 and 64-bit Python 3.10+. The unfinished grid mod is excluded.

安装前验证完整文件状态，完整备份后再提交。重复安装不替换首次基线；`uninstall.cmd` 恢复合集安装前状态，保留原先已有的独立 mod。失败自动尝试恢复；中断后使用 `recover.cmd`。务必保留隐藏的 `.bundle-state/`。

All file states are verified and completely backed up before committing. Reinstallation preserves the original baseline. `uninstall.cmd` restores the pre-bundle state and retains independently installed mods that were already present. Failed operations attempt rollback; use `recover.cmd` after interruption. Keep hidden `.bundle-state/`.

保留各 mod 原测试版标记及实机验证边界。只在合法样本的临时副本中测试安装和恢复，未修改或控制实际游戏。阶段一以外和完整实机流程仍未验收。所有 mod 均由 AI 生成，游戏更新可能导致失效（2026-10-20 可用）。

Original test labels and gameplay-validation limits are retained. Installation and recovery were tested only on temporary copies of legitimate samples, without modifying or controlling the actual game. Later stages and full gameplay remain unverified. All mods are AI-generated and game updates may break them (working as of 2026-10-20).

ZIP 内含逐文件 `SHA256SUMS.txt`；本 Release 另附 ZIP 的 SHA-256 清单。完整操作和限制见 README。

The ZIP includes per-file `SHA256SUMS.txt`; this Release also provides the ZIP's SHA-256 checksum list. See README for complete instructions and limits.
