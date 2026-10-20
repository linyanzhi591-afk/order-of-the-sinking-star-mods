# 发行验证 / Release validation

版本：**1.0.0-test**。日期：**2026-10-20**。原生 mod 的发行版本和验证边界保持不变。

Version: **1.0.0-test**. Date: **2026-10-20**. Constituent native-mod versions and gameplay-validation limits are retained.

## 已通过的检查 / Passed checks

- 旁支提供的五个 mod 目录逐文件匹配原发行版 SHA-256 清单；必需载荷和兼容模块完整保留。
- 16 种奔跑/镜头/描边/粒子子组合，以及 6 种原世界单步支持的起始组合，全部生成同一套最终哈希。
- 从原版完整安装、重复安装保持首次基线、状态检查、卸载精确恢复、重复卸载、恢复重复调用及卸载后重装。
- 已有部分 mod 安装后仍可补齐；卸载精确保留先前已有 mod。已有完整五 mod 时接管基线，不重写游戏文件。
- 每次首次游戏写入前，四份完整备份及必要输出暂存均已写入并核对哈希。
- 游戏运行、进程查询失败、空间不足、备份写入失败、发行载荷被修改、未知文件及不一致描边状态均会阻止游戏写入。
- 改键和网格层拒绝保护；并发操作锁；不删除预先存在的同名临时文件。
- 第二个目标替换失败后自动恢复；安装中断后可恢复；未知中断后修改或损坏备份会在恢复写入前拒绝操作。
- 卸载中断后恢复到已安装状态；当前文件被外部修改或最初备份损坏时拒绝卸载。
- 五个真实 CMD 入口均在含空格目录下通过成功/失败退出码、参数传递和暂停检查。入口会探测可用的 64 位 Python，并在 `py` 不可用时回退到 `python`。

- The five supplied mod directories match their original per-file SHA-256 lists, retaining required payloads and compatibility modules.
- All 16 toggle-run/camera/highlight/particle subsets and six starting combinations supported by world-step generate identical final hashes.
- Fresh installation, repeated installation preserving the first baseline, status, exact uninstallation, repeated uninstallation/recovery and reinstallation after removal passed.
- Partial installations are completed and their initial mods are retained on uninstallation. Adopting an already complete installation records a baseline without rewriting game files.
- All four complete backups and required staged outputs are written and checksum-verified before the first game-file replacement.
- Running game, failed process query, insufficient space, backup-write failure, changed payload, unknown files and inconsistent highlight states block game writes.
- Rebound keys and grid layers are rejected; concurrent operations are locked; pre-existing scratch files are not deleted.
- Failure replacing the second target automatically rolls back. Interrupted installation can recover. Unknown post-interruption edits or damaged backups block recovery before writes.
- Interrupted uninstallation recovers to the installed state. External changes and damaged initial backups block uninstallation.
- All five real CMD entry points passed success/failure exit-code, argument and pause checks in paths containing spaces. Launchers probe for usable 64-bit Python and fall back from unavailable `py` to `python`.

共 **15 组测试**通过：事务部分 14 组通过，CMD 专项修正后独立复测通过。测试使用合法原版样本的私有临时副本，并核对只读样本未被修改。进程状态只在测试调用范围内模拟；发行安装器保留真实进程检查。生成的程序通过 Windows x64 格式检查，不执行游戏入口。

**15 test groups** passed: 14 transaction groups and the corrected CMD group in a targeted rerun. Tests used private temporary copies of legitimate pristine fixtures and verified the read-only fixtures remained unchanged. Process state was mocked only inside tests; distributed installers retain real checks. Generated executables passed Windows x64 format validation without executing their entry points.

## 不属于本次验收的内容 / Outside this validation

没有安装到、卸载、修改、启动、关闭或控制用户当前实际游戏。这些检查不代表第一阶段以外、全关卡实机画面、完整游玩、实体手柄或性能验收。原 mod 的测试版标记、默认按键限制及其他边界见各自 README。

The user's actual game was not installed into, uninstalled, modified, started, stopped or controlled. These checks are not acceptance of later stages, all-level visuals, complete gameplay, physical controllers or performance. Original test labels, default-key restrictions and other limits remain documented in the constituent READMEs.

## 构建与分发 / Build and distribution

发行构建使用明确文件白名单，逐文件校验载荷，检查 Python 语法、CMD 换行、ZIP 完整性与归档内 SHA-256。发行包不含完整游戏程序、原版资源、存档、运行备份、临时测试数据或旧 Git 历史。ZIP 校验清单随 Release 单独提供。

The release builder uses an explicit allowlist, verifies vendored files, and checks Python syntax, CMD line endings, ZIP integrity and archived per-file SHA-256. The archive contains no complete game executables, original assets, saves, runtime backups, temporary test data or old Git history. ZIP checksums are provided separately with the Release.
