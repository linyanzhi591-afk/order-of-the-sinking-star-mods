# 新 mod 整合流程 / Adding a mod

本仓库是此游戏后续 mod 的导航和合集入口。保留独立 mod 仓库及其历史；合集通过固定版本的发行文件进行集成，不自动拉取最新版本。

This repository is the navigation and bundle entry point for future mods for this game. Preserve standalone repositories and their histories. Integration vendors pinned release versions rather than automatically downloading the newest version.

1. 核对独立 mod 的当前源码、载荷、验证范围和发布版本，只复制可再分发的安装器、必要模块、载荷及文档到 `mods/<英文-kebab-case-名称>/`；不要复制 `.git`、游戏文件、备份或存档。
2. 更新 `bundle.json` 的版本、导航链接和安装顺序。在 `bundle.py` 中显式加入对应适配器；新增写入目标时同步扩展 `TARGETS`、预检、备份、事务和恢复验证。禁止执行来源不明的任意安装命令。
3. 优先复用原安装器的纯变换/校验逻辑。先生成所有输出并检查完整哈希，再备份所有将管理的目标，最后统一提交。未知状态、冲突或缺少恢复材料时必须拒绝覆盖。
4. 只对经过确认的发行文件重新生成 `bundle-files.json`。不要通过重算校验清单来“修复”未知的载荷变化。
5. 使用合法原版样本的临时副本扩展 `tests/test_bundle.py`：覆盖已支持的起始组合、新 mod 的各种共存状态、重复操作、逐文件失败、中断恢复、损坏备份和未知修改保护。不要测试安装到实际游戏。
6. 明确旧合集的升级方式。若不能证明保留最初基线的原位升级安全，应要求先用旧合集及其 `.bundle-state` 正常卸载，再安装新版本。现有 1.0.0-test 不提供自动跨版本升级承诺。
7. 更新中文优先的双语 README、验证记录及发行说明，保留所有尚未完成的实机验收边界。通过 `build_release.py` 生成不含运行状态及游戏文件的 ZIP，再发布新 tag、Release 和校验清单。

1. Verify the standalone mod's source, payloads, validation limits and release version. Vendor only redistributable installers, required modules, payloads and documentation under `mods/<english-kebab-case-name>/`; exclude `.git`, game files, backups and saves.
2. Update versions, links and order in `bundle.json`. Add an explicit adapter to `bundle.py`. If new files are managed, extend `TARGETS`, preflight, backups, transactions and recovery validation together. Do not execute arbitrary unreviewed installation commands.
3. Prefer the original installer's pure transformation/validation logic. Generate and verify every output, back up all managed targets, then commit them together. Reject unknown states, conflicts and missing recovery material.
4. Regenerate `bundle-files.json` only after verifying the exact vendored release files. Never hide unexplained payload changes by simply regenerating checksums.
5. Extend `tests/test_bundle.py` using temporary copies of legitimate pristine samples. Cover supported starting combinations, coexistence, repeated operations, per-file failures, interrupted recovery, damaged backups and unknown modifications. Never install into the real game for these tests.
6. Define the upgrade path. If an in-place upgrade cannot safely preserve the original baseline, require normal uninstallation with the old bundle and its `.bundle-state` before installing the new version. Version 1.0.0-test does not promise automatic cross-version upgrades.
7. Update the Chinese-first bilingual README, validation record and release notes, retaining unverified gameplay limits. Use `build_release.py` to produce a ZIP without runtime state or game files, then publish a new tag, Release and checksums.

## 开发验证 / Developer verification

提供一份合法的原版游戏样本副本，包含 `sinking_star.exe` 与 `data/` 中的三个目标资源。测试只读取该样本，再建立自己的临时游戏目录；测试结束会核对样本哈希未变。样本不应加入 Git 或发行包。

Provide a legitimate pristine fixture copy containing `sinking_star.exe` and the three target resources under `data/`. Tests only read that copy and create their own temporary game directories. Fixture hashes are checked after testing. Never commit or distribute the fixtures.

```powershell
python -B -X utf8 tests/test_bundle.py --fixtures "C:\temporary-pristine-game-copy" --report test-results.json
python -B -X utf8 build_release.py --output "C:\release-output"
```

原生 mod 内部的开发测试可能还依赖独立工作区样本。合集测试负责统一安装和恢复事务，不把旧测试记录当成新增代码的验证结果。

Constituent native-mod developer tests may additionally require standalone workspace fixtures. Bundle tests validate the unified installation and recovery transactions; previous test records do not validate new code automatically.
