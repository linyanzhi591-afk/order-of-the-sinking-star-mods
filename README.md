# 沉星之序 mod 导航与一键安装合集 / Order of the Sinking Star Mods

> 因作者目前仍然在打一阶段，目前只确保能在一阶段可使用。
> 该 mod 可能会因游戏更新而失效（26/10/20 可用）。
> mod 均由 AI 生成。
>
> The author is currently still playing Stage 1; usability is only assured for Stage 1 at present.
> Game updates may break these mods (working as of 2026-10-20).
> All mods are AI-generated.

中文为默认说明语言；各节附有英文。 / Chinese is the default; English accompanies each section.

## 说明 / Description

这是五个独立 mod 的总导航和统一安装入口，适用于 **Windows x64 / Steam Build 26006400**。合集版本 **1.0.0-test**。下载一个 ZIP、完整解压后运行根目录 `install.cmd`，即可安装全部五项；不包含尚未完成的网格显示 mod。

This repository is the navigation hub and unified installer for five standalone mods targeting **Windows x64 / Steam Build 26006400**. Bundle version: **1.0.0-test**. Download one ZIP, extract it completely and run the root `install.cmd` to install all five. The unfinished grid-display mod is excluded.

**[下载合集 ZIP / Download bundle ZIP](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-mods/releases/download/v1.0.0-test/order-of-the-sinking-star-mods-v1.0.0-test-build26006400.zip)** · **[Release 与 SHA-256 校验清单 / Release and checksums](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-mods/releases/tag/v1.0.0-test)**

| mod / Mod | 功能 / Function | 版本 / Version | 默认按键 / Default controls | 独立仓库 / Repository | 独立下载 / Download |
| --- | --- | --- | --- | --- | --- |
| 奔跑切换 / Toggle Run | 按一下开启奔跑，再按关闭 / Press to toggle running | 1.0.0 | Shift；RB/R1（沿用游戏绑定 / existing bindings） | [仓库 / Repo](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-toggle-run) | [下载 / Release](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-toggle-run/releases/tag/v1.0.0) |
| 俯视镜头 / Local Area View | 为受限关卡扩展俯视，拉远 17%、下移 6% / Adds overhead view, 17% farther distance, 6% downward framing shift | 0.1.9-test | Q；右摇杆按下 / right-stick button | [仓库 / Repo](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-local-area-view) | [下载 / Release](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-local-area-view/releases/tag/v0.1.9-test) |
| 六职业彩色描边 / Character Highlight | 六种职业使用不同颜色，默认开启 / Class-colored outlines, enabled at startup | 0.2.1 | P | [仓库 / Repo](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-character-highlight) | [下载 / Release](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-character-highlight/releases/tag/v0.2.1) |
| 粒子减量 / Particle Reduction | 减少所选装饰粒子，保留主体和独立光源 / Reduces selected decorative particles, preserves main effects and independent lights | 0.1.0-test | 自动生效，无开关键 / Automatic, no toggle | [仓库 / Repo](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-particle-reduction) | [下载 / Release](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-particle-reduction/releases/tag/v0.1.0-test) |
| 世界暂停与单步 / World Step | 暂停世界或按 33 毫秒逻辑步推进 / Pauses the world or advances 33 ms logic steps | 0.1.3-test | N 暂停/恢复，M 单步/长按连步 / N pause/resume; M step/hold to repeat | [仓库 / Repo](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-world-step) | [下载 / Release](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-world-step/releases/tag/v0.1.3-test) |

现有独立仓库继续保留。各 mod 的详细限制、源码及独立安装说明也保留在 `mods/<名称>/README.md` 中。

The standalone repositories remain available. Detailed limitations, source and standalone instructions are also retained under `mods/<name>/README.md`.

## 安装 / Installation

需要 **Windows x64 和 64 位 Python 3.10 或更高版本**，无需第三方 Python 包、编译器或额外后台程序。Python 应已启用 `py` 启动器或加入 PATH。合集直接调用原补丁的变换逻辑，奔跑部分复用已验证清单，不需要另行运行 PowerShell 安装器。

Requires **Windows x64 and 64-bit Python 3.10 or newer**, with the `py` launcher or Python on PATH. No third-party Python packages, compiler or extra background process is needed. The bundle reuses the original transformation logic and verified toggle-run patch manifest; it does not need to invoke the separate PowerShell installer.

1. 从上方 Release 下载合集 ZIP 和 `SHA256SUMS.txt`。可用 `Get-FileHash -Algorithm SHA256 "ZIP 文件路径"` 核对下载。
2. 完整解压到一个可写、长期保留的独立目录。不要解压覆盖游戏目录，也不要在 ZIP 内直接运行。
3. 正常退出游戏，双击根目录 **`install.cmd`**。成功提示和退出码为 0 后，再按平常方式从 Steam 启动游戏。

1. Download the bundle ZIP and `SHA256SUMS.txt` from the Release above. Optionally verify it using `Get-FileHash -Algorithm SHA256 "path to ZIP"`.
2. Extract everything into its own writable folder that you will keep. Do not extract over the game directory or run inside the ZIP.
3. Exit the game yourself and run the root **`install.cmd`**. After a success message and exit code 0, launch the game normally through Steam.

安装器会查找 Steam 游戏目录；无法唯一定位时会询问路径。也可直接指定：

The installer searches Steam library locations and asks for a path if it cannot identify exactly one installation. You can also specify it explicitly:

```powershell
.\install.cmd --game-dir "D:\SteamLibrary\steamapps\common\Order of the Sinking Star"
```

安装顺序固定为 **奔跑切换 → 俯视镜头 → 彩色描边 → 粒子减量 → 世界暂停与单步**。安装器先按此顺序在内存中生成最终文件并校验，再完整备份四个目标文件、暂存输出，最后统一写入。不是依次盲目运行五个独立安装脚本。

The fixed order is **Toggle Run → Local Area View → Character Highlight → Particle Reduction → World Step**. The installer builds and verifies the final files in that order in memory, backs up all four target files, stages the outputs and then commits them as one recoverable operation.

首次完整安装大约需要 0.9 GB 备份与暂存空间，游戏盘另需约 0.4 GB 临时空间，并预留安全余量；同盘时要求合计可用空间。每次安装/卸载事务会保留自身恢复文件，不会自动清理历史备份。

A fresh full installation needs approximately 0.9 GB for backups/staging and another 0.4 GB of temporary game-drive space, plus a safety margin. The requirements are added together when both locations share a drive. Installation/uninstallation operations retain their recovery snapshots rather than deleting older backups automatically.

## 使用 / Usage

- **Shift / RB/R1**：切换奔跑，沿用游戏内奔跑动作的绑定。 / Toggle running using the game's run bindings.
- **Q / 右摇杆按下**：切换俯视；原本支持俯视的关卡沿用原版行为。 / Toggle overhead view; natively supported levels retain native behavior.
- **P**：切换六职业彩色描边。 / Toggle class-colored outlines.
- **粒子减量**：安装后自动生效。 / Particle reduction applies automatically.
- **N**：暂停/恢复世界。**M**：立即推进一次 33 毫秒逻辑更新，按住满 99 毫秒后开始约每 33 毫秒连步，每显示帧最多一步；松开保持暂停。 / N pauses/resumes; M immediately advances one 33 ms logic update, then repeats roughly every 33 ms after a 99 ms initial hold, at most once per display frame. Releasing keeps the world paused.

`status.cmd` 查看状态，不修改游戏或创建备份。`check.cmd` 执行完整安装预检，不写游戏，但会创建并清理一个临时映像以检查 Windows x64 格式。自定义游戏路径时，所有入口均使用同样的 `--game-dir` 参数。

`status.cmd` reports state without changing game files or creating backups. `check.cmd` performs full installation preflight without writing to the game; it briefly creates a temporary image to verify Windows x64 format. All launchers accept the same `--game-dir` option.

```powershell
python -B -X utf8 bundle.py status --game-dir "你的游戏目录 / your game directory"
python -B -X utf8 bundle.py check --game-dir "你的游戏目录 / your game directory"
```

合集固定使用上述默认开关键；请勿直接编辑 `mods/` 中的配置、载荷或文件。发行文件完整性检查会拒绝修改后的内容。需要改键时，应先按本合集卸载，再按独立仓库的说明操作；修改后的任意组合不属于本合集已验证范围。

The bundle uses the listed default keys. Do not edit the vendored configurations, payloads or files under `mods/`; integrity verification rejects modified content. To customize bindings, uninstall the bundle first and follow the standalone instructions. Arbitrary rebound combinations are outside this bundle's verified scope.

## 卸载与失败恢复 / Uninstallation and recovery

### 正常卸载 / Normal uninstallation

正常退出游戏，双击根目录 **`uninstall.cmd`**。合集会核对当前四个目标文件及首次安装前的完整备份，然后精确恢复合集安装前的字节。

Exit the game and run the root **`uninstall.cmd`**. The bundle validates the four current target files and its complete original snapshot, then restores the exact bytes from before bundle installation.

**如果最初是原版，将移除全部五项；如果最初已单独安装部分或全部 mod，卸载会保留这些先前已有的 mod。** 已完整安装时重复运行 `install.cmd` 不重复写入、不替换首次基线。首次接管一个已完整安装五 mod 的目录，会保存该状态作为基线，因此卸载也会保留它们。重复卸载安全地不做任何游戏文件修改。

**A pristine starting installation returns to the original game. Mods already present before bundle installation are preserved.** Repeating `install.cmd` on an active complete installation does not rewrite files or replace the original baseline. Adopting an already complete five-mod installation records that state as its baseline, so uninstallation retains those pre-existing mods. Repeated uninstallation is a safe no-op.

### 失败或中断 / Failure or interruption

普通写入失败时，安装器会验证全部备份及当前文件，再自动恢复到**本次操作前**的状态。强制中断、断电、游戏在写入期间启动，或自动恢复未完成时：

On an ordinary write failure, all backups and current files are validated before automatic restoration to the **pre-operation** state. After forced interruption, power loss, the game starting during a write, or incomplete automatic recovery:

1. 保留整个合集目录，尤其隐藏的 **`.bundle-state/`**。不要启动游戏，也不要运行 `mods/` 内的单独安装器。
2. 确保游戏已退出，双击 **`recover.cmd`**（自定义路径时追加 `--game-dir`）。
3. 恢复成功后再运行 `status.cmd`，然后选择重新安装或正常卸载。中断的安装会恢复安装前；中断的卸载会恢复卸载前的已安装状态。

1. Keep the whole bundle directory, especially hidden **`.bundle-state/`**. Do not start the game or run the individual installers under `mods/`.
2. Ensure the game is closed and run **`recover.cmd`**, passing `--game-dir` when needed.
3. After recovery, run `status.cmd` and then install again or uninstall normally. An interrupted installation returns to its starting state; an interrupted uninstallation returns to its installed state.

存在未完成事务时，新的安装/卸载会被阻止。恢复可重复执行；发现任何未知文件修改或损坏备份时会在写入前停止，保留恢复材料，不强行覆盖。备份及事务记录位于 `.bundle-state/<游戏路径标识>/transactions/<事务编号>/`，`journal.json` 记录每个文件的前后哈希与阶段。

New installation/uninstallation is blocked while a transaction is pending. Recovery is repeatable. Unknown file changes or damaged backups stop recovery before any write, retaining the recovery material. Backups and journals are stored under `.bundle-state/<game-path-id>/transactions/<transaction-id>/`; `journal.json` records before/after hashes and operation phase.

移动合集时应连同隐藏状态目录一起移动。没有本目录的原始收据和备份时，不会擅自卸载独立安装的 mod。游戏文件在合集安装后被 Steam 更新、其他安装器或手动操作改变时，合集也会拒绝覆盖。

Move the hidden state directory together with the bundle. Without this installation's receipt and backups, the uninstaller will not remove independently installed mods. Steam updates, other installers and manual edits after bundle installation also cause the bundle to refuse overwriting changed files.

## 兼容性与已存在的 mod / Compatibility and existing mods

- 只接受完整哈希验证通过的 Build 26006400。支持原版、当前奔跑/俯视/描边/粒子四项的全部 16 种子组合，以及世界单步原安装器已支持的三种基础程序与两种粒子状态，共 6 种含世界单步组合。
- 俯视须为 0.1.9-test；描边和世界单步须使用当前已发布版本及默认 P/N/M。更旧版本、部分损坏安装、未知资源修改和网格层会在写入前被拒绝。
- 备份的是实际读到的完整初始状态。独立描边已安装时，安装器仅对严格匹配的当前资源执行可逆重建，并核对原版哈希和正向回放结果，无需附带原版资源。
- 操作前和逐文件替换前均检查游戏进程，查询失败则停止。不会自动启动、关闭或控制游戏。操作期间请保持游戏关闭。

- Only exact, verified Build 26006400 files are accepted. Supported inputs include the pristine game, all 16 subsets of the current toggle-run/camera/highlight/particle mods, and six world-step combinations covering its three supported executable bases and two particle states.
- Camera must be 0.1.9-test; highlight and world-step must be the current released versions with default P/N/M keys. Older versions, inconsistent installations, unknown resource edits and grid layers are rejected before writes.
- The complete actual starting state is backed up. Already installed highlight resources are reversed only when they strictly match the current known output, and both original hashes and forward replay are checked; no original assets need to be distributed.
- The game process is checked before the operation and before each replacement. A failed process query stops writes. The installer never starts, stops or controls the game. Keep the game closed throughout the operation.

## 验证边界 / Validation limits

合集及三个 mod 保留 `test` 标记。隔离安装与恢复测试不能代替全关卡实机验收；第一阶段以外、特殊交互、实体手柄、实际画面及性能收益均不能由这些测试保证。世界暂停不保证冻结音乐、界面动画、纯渲染效果或独立真实时间计时器；低帧率会降低连步速度。

The bundle and three constituent mods retain their `test` labels. Isolated installation/recovery tests are not complete gameplay acceptance. They do not guarantee later stages, special interactions, physical controllers, actual visuals or performance gains. World pause may leave music, UI animations, rendering-only effects and independent real-time timers running; low frame rates slow step repetition.

具体发行验证见 [VALIDATION.md](VALIDATION.md)。发行包不包含完整游戏 exe、原版资源、存档、本机备份、临时测试文件或独立仓库旧 Git 历史。`mods/` 中保留的网格兼容模块是原发行版的必需依赖，不是网格 mod 的安装入口。

See [VALIDATION.md](VALIDATION.md) for release validation. The release contains no complete game executables, original assets, saves, local backups, temporary test files or old standalone-repository Git history. Retained grid compatibility modules are required dependencies of the original releases, not an installer for the unfinished grid mod.

## 后续 mod 整合与源码 / Future integration and source

后续此游戏的 mod 继续以本仓库作为总导航与合集入口。版本、顺序及独立链接记录在 `bundle.json`，原发行文件校验记录在 `bundle-files.json`；新增 mod 必须更新适配、备份目标、兼容测试和发行包，不能只往 `mods/` 放一个文件夹。流程见 [INTEGRATING_MODS.md](INTEGRATING_MODS.md)。

This repository remains the navigation and bundle entry point for future mods for this game. `bundle.json` records versions, order and standalone links; `bundle-files.json` pins vendored release files. Adding a mod requires updating adapters, backup targets, compatibility tests and packaging, rather than merely dropping a folder under `mods/`. See [INTEGRATING_MODS.md](INTEGRATING_MODS.md).

问题反馈请提供合集版本、游戏 Build ID、起始 mod 组合、操作步骤和错误输出。不要在公开 Issues 上传游戏文件、备份或存档。本项目为非官方 AI 生成 mod，与游戏开发商、发行商或 Steam 无隶属关系；游戏及其资源属于原权利人。

When reporting an issue, include the bundle version, game Build ID, starting mod combination, steps and error output. Do not upload game files, backups or saves to public Issues. These are unofficial AI-generated mods, unaffiliated with the game's developer, publisher or Steam; the game and its assets belong to their respective rights holders.
