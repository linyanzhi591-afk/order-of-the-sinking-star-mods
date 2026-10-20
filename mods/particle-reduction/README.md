# 粒子减量 / Particle Reduction

> 因作者目前仍然在打一阶段，目前只确保能在一阶段可使用。
> 该 mod 可能会因游戏更新而失效（26/10/20 可用，2026-10-20）。
> 本项目的 mod 均由 AI 生成。
>
> The author is currently still playing Stage 1; usability is only assured for Stage 1 at present.
> Game updates may break this mod (working as of 2026-10-20).
> All mods in this project are AI-generated.

中文为默认说明语言；English follows each corresponding section.

## 说明 / Description

适用游戏：**Order of the Sinking Star**，Steam Build **26006400**。发行版本：**0.1.0-test**。

Target: **Order of the Sinking Star**, Steam Build **26006400**. Release version: **0.1.0-test**.

降低选定装饰粒子：563 个环境发射器生成率减半，停止 75 个火焰附属发射器及 13 个光束附属发射器，并关闭所选光束附属突发发射。保留火焰、龙息、光束主体与独立光源。651 个发射器分布于 202 个资源条目，不是全局关闭粒子。

Reduces selected decorative particles: halves emission from 563 environmental emitters, stops 75 secondary fire emitters and 13 secondary beam emitters, and disables selected secondary beam bursts. Main flames, dragon breath, beams and independent lights are preserved. The 651 emitters span 202 resource entries; this is not a global particle disable.

## 安装 / Installation

Windows x64、Python 3（64 位），无需第三方 Python 包或日常安装用编译器。 / Windows x64 and 64-bit Python 3; no third-party Python packages or compiler needed for installation.

1. 解压完整发行包到独立文件夹，保留全部文件，不要直接覆盖游戏目录。 / Extract the complete release into its own folder; keep all files and do not extract over the game directory.
2. 正常退出游戏，双击 `install.cmd`，确认成功后再从 Steam 启动游戏。 / Exit the game normally, run `install.cmd`, confirm success, then launch through Steam.
3. 默认路径如下；游戏在其他位置时，打开终端进入本 mod 文件夹，使用下面的安装命令。 / The default path is below. For another location, open a terminal in this mod folder and use the command below.

```text
D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star
```

```powershell
python -X utf8 patch.py install --game-dir "你的游戏目录 / your game directory"
```


## 使用 / Usage

安装后自动生效，无开关键。preview.cmd 只读显示状态和范围。 / Applies automatically after installation, with no toggle key. preview.cmd displays status and scope without writing.

状态检查（自定义路径时同样追加对应的路径参数）： / Check status (also pass the custom path option if applicable):

```powershell
python -X utf8 patch.py status
```

## 卸载 / Uninstallation

正常退出游戏，双击 `uninstall.cmd`。自定义路径时，在下面的命令后追加安装时使用的路径参数。请保留安装目录及其生成的备份；不要用其他版本的整个 exe 覆盖组合安装。

Exit the game and run `uninstall.cmd`. For a custom game location, append the same path option used during installation. Keep the mod folder and generated backups. Do not overwrite combined installations with another version's complete executable.

```powershell
python -X utf8 patch.py uninstall
```

## 兼容与安装顺序 / Compatibility and order

只修改 data/levels.package，与其余四个 mod 的写入目标独立。未知关卡包修改会被拒绝。安装会在本目录 backups 中保存约 394 MB 的原包，另需同等大小临时空间；请保留备份。

Only modifies data/levels.package, separate from the other four mods' targets. Unknown changes to that package are rejected. Installation saves an approximately 394 MB original package under backups and requires a similar amount of temporary space. Keep the backup.

## 实现与验证边界 / Implementation and validation

实际字段及位置见 manifest.json。既有隔离测试覆盖资源结构、受保护效果和光源、安装卸载、损坏备份及未知修改拒绝。保留测试版版本号；未完成实机视觉或帧率验收，不保证每个场景都有性能收益，移除附属亮点也可能改变局部观感。

Exact fields and offsets are listed in manifest.json. Existing isolated checks cover resource structure, protected effects/lights, installation/restoration, damaged backups and unknown modifications. The test-version label is retained. In-game visuals and frame-rate gains remain unverified; performance benefits are not guaranteed, and removing decorative highlights can affect appearance.

## 更新与故障反馈 / Updates and troubleshooting

游戏更新或 Steam 验证文件可能移除补丁。遇到版本不符、未知修改或损坏备份时，不要跳过哈希检查。请在本仓库 Issues 提供游戏 Build ID、mod 版本、安装顺序、已安装 mod、操作步骤和完整错误信息；不要上传存档或完整游戏文件。

Game updates or Steam file verification may remove the patch. Do not bypass hash checks for unsupported versions, unknown modifications or damaged backups. Report the game Build ID, mod version, installation order, installed mods, reproduction steps and full errors in this repository's Issues. Do not upload saves or complete game files.

## 源码与署名 / Source and credits

仓库提供安装器、必要载荷及开发源码。日常安装使用已生成并校验的载荷；修改原生载荷后须重新构建并同步哈希。既有开发测试可能依赖本地合法游戏样本及同级 mod 工作区，不能视为下载后即能独立运行的通用测试。

The repository includes installers, required payloads and development sources. Normal installation uses generated, verified payloads; native payload changes require rebuilding and updating hashes. Existing developer tests may require local legitimate game samples and sibling mod workspaces; they are not universally standalone tests.

本项目是非官方 AI 生成 mod，与游戏开发商、发行商及 Steam 无隶属关系。游戏及其资源属于原权利人。

This is an unofficial AI-generated mod, unaffiliated with the game's developer, publisher or Steam. The game and its assets belong to their respective rights holders.
