# 按键切换奔跑 / Toggle Run

> 因作者目前仍然在打一阶段，目前只确保能在一阶段可使用。
> 该 mod 可能会因游戏更新而失效（26/10/20 可用，2026-10-20）。
> 本项目的 mod 均由 AI 生成。
>
> The author is currently still playing Stage 1; usability is only assured for Stage 1 at present.
> Game updates may break this mod (working as of 2026-10-20).
> All mods in this project are AI-generated.

中文为默认说明语言；English follows each corresponding section.

## 说明 / Description

适用游戏：**Order of the Sinking Star**，Steam Build **26006400**。发行版本：**1.0.0**。

Target: **Order of the Sinking Star**, Steam Build **26006400**. Release version: **1.0.0**.

将原来的按住奔跑改为按一下开启、再按一下关闭。默认键盘 Shift、手柄 RB/R1，沿用游戏内的奔跑绑定。键盘和手柄共用状态；重启游戏不保留状态，切出再切回可能需要重新开启。游戏菜单原有“按住奔跑”文字不变。

Changes hold-to-run into press-to-toggle running. The default controls are Shift and RB/R1, using the game's existing run bindings. Keyboard and controller share the same state. State resets on restart; switching away may require toggling again. The original menu wording is unchanged.

## 安装 / Installation

Windows x64、Windows PowerShell；无需额外后台程序。 / Windows x64 and Windows PowerShell; no additional background application.

1. 解压完整发行包到独立文件夹，保留全部文件，不要直接覆盖游戏目录。 / Extract the complete release into its own folder; keep all files and do not extract over the game directory.
2. 正常退出游戏，双击 `install.cmd`，确认成功后再从 Steam 启动游戏。 / Exit the game normally, run `install.cmd`, confirm success, then launch through Steam.
3. 默认路径如下；游戏在其他位置时，打开终端进入本 mod 文件夹，使用下面的安装命令。 / The default path is below. For another location, open a terminal in this mod folder and use the command below.

```text
D:\Program Files (x86)\Steam\steamapps\common\Order of the Sinking Star
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\manage.ps1 -Action Install -GameDir "你的游戏目录 / your game directory"
```

公开包不附带完整 exe；安装器根据 `manifest.json` 在玩家本机生成补丁，并把原程序备份为 `sinking_star.original.exe`。旧用户移动安装目录时须一并保留此备份。

The public package contains no complete executable. The installer generates the patch locally from `manifest.json` and saves the original as `sinking_star.original.exe`. Existing users must retain this backup when moving the mod folder.

## 使用 / Usage

安装后从 Steam 正常启动，按奔跑键切换。 / Launch normally through Steam and press the run binding to toggle.

状态检查（自定义路径时同样追加对应的路径参数）： / Check status (also pass the custom path option if applicable):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\manage.ps1 -Action Status
```

## 卸载 / Uninstallation

正常退出游戏，双击 `restore.cmd`。自定义路径时，在下面的命令后追加安装时使用的路径参数。请保留安装目录及其生成的备份；不要用其他版本的整个 exe 覆盖组合安装。

Exit the game and run `restore.cmd`. For a custom game location, append the same path option used during installation. Keep the mod folder and generated backups. Do not overwrite combined installations with another version's complete executable.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\manage.ps1 -Action Restore
```

## 兼容与安装顺序 / Compatibility and order

仅识别原版和奔跑版的完整 SHA-256。多 mod 建议先安装奔跑，再安装俯视、描边，世界单步最后安装；粒子减量独立。调整奔跑前先逆序卸载其他程序补丁。

Only the exact original and toggle-run executable hashes are accepted. Recommended order: toggle-run, camera, character highlight, then world-step last; particle reduction is independent. Remove dependent executable patches in reverse order before changing toggle-run.

## 实现与验证边界 / Implementation and validation

仅修改原生 HoldToRun 回调的 56 字节，其中 45 字节变化；其他程序字节、存档和按键配置不变。已有隔离机器码验证覆盖长按去重、松开保持、再次关闭、两绑定共用状态及原模式检查。未完成完整实机流程及实体手柄验收。

Replaces 56 bytes in the native HoldToRun callback; 45 bytes differ. Other executable bytes, saves and bindings are preserved. Existing isolated machine-code checks cover repeat filtering, release persistence, toggling off, shared bindings and mode guards. Full gameplay and physical-controller validation remain incomplete.

## 更新与故障反馈 / Updates and troubleshooting

游戏更新或 Steam 验证文件可能移除补丁。遇到版本不符、未知修改或损坏备份时，不要跳过哈希检查。请在本仓库 Issues 提供游戏 Build ID、mod 版本、安装顺序、已安装 mod、操作步骤和完整错误信息；不要上传存档或完整游戏文件。

Game updates or Steam file verification may remove the patch. Do not bypass hash checks for unsupported versions, unknown modifications or damaged backups. Report the game Build ID, mod version, installation order, installed mods, reproduction steps and full errors in this repository's Issues. Do not upload saves or complete game files.

## 源码与署名 / Source and credits

仓库提供安装器、必要载荷及开发源码。日常安装使用已生成并校验的载荷；修改原生载荷后须重新构建并同步哈希。既有开发测试可能依赖本地合法游戏样本及同级 mod 工作区，不能视为下载后即能独立运行的通用测试。

The repository includes installers, required payloads and development sources. Normal installation uses generated, verified payloads; native payload changes require rebuilding and updating hashes. Existing developer tests may require local legitimate game samples and sibling mod workspaces; they are not universally standalone tests.

本项目是非官方 AI 生成 mod，与游戏开发商、发行商及 Steam 无隶属关系。游戏及其资源属于原权利人。

This is an unofficial AI-generated mod, unaffiliated with the game's developer, publisher or Steam. The game and its assets belong to their respective rights holders.
