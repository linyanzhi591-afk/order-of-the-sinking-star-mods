# 六职业彩色描边 / Character Highlight

> 因作者目前仍然在打一阶段，目前只确保能在一阶段可使用。
> 该 mod 可能会因游戏更新而失效（26/10/20 可用，2026-10-20）。
> 本项目的 mod 均由 AI 生成。
>
> The author is currently still playing Stage 1; usability is only assured for Stage 1 at present.
> Game updates may break this mod (working as of 2026-10-20).
> All mods in this project are AI-generated.

中文为默认说明语言；English follows each corresponding section.

## 说明 / Description

适用游戏：**Order of the Sinking Star**，Steam Build **26006400**。发行版本：**0.2.1**。

Target: **Order of the Sinking Star**, Steam Build **26006400**. Release version: **0.2.1**.

为六种职业添加彩色描边，默认开启，按 P 切换；关闭时恢复原版描边。战士深红、盗贼深绿、法师深蓝、牧师深黄、吟游诗人深紫、德鲁伊深青灰。覆盖 9 个已知职业模型，同职业实例共享颜色；保留深度遮挡，不增加透墙效果。加载界面没有描边绘制时不保证响应。

Adds colored outlines for six classes, enabled at startup and toggled with P. Disabling restores the original outlines. Colors: warrior dark red, thief dark green, wizard dark blue, cleric dark yellow, bard dark purple, druid dark blue-gray. Covers nine known class models; instances of a class share their color. Original depth occlusion is preserved. The toggle may not respond on loading screens without outline rendering.

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

公开包不附带原版资源。首次安装会从本机已验证的原版资源创建 `original/` 备份；状态检查不创建备份。旧版用户应先用旧安装器卸载，或将旧版的 `original/` 备份复制到新目录；资源已修改且没有备份时会拒绝操作。

The public package contains no original game assets. First installation backs up verified local original resources under `original/`; status checks create no backups. Existing users must uninstall with their old installer first, or copy their old `original/` backups into the new folder. Modified resources without originals are rejected.

## 使用 / Usage

按 P 切换。改键：编辑 toggle_config.json 的 key 后重新安装；支持 A–Z、0–9、F1–F12，不吞掉游戏原输入。 / Press P to toggle. To rebind, edit key in toggle_config.json and reinstall; supports A–Z, 0–9 and F1–F12. Original input is not consumed.

状态检查（自定义路径时同样追加对应的路径参数）： / Check status (also pass the custom path option if applicable):

```powershell
python -X utf8 patch.py status
```

## 卸载 / Uninstallation

正常退出游戏，双击 `restore.cmd`。自定义路径时，在下面的命令后追加安装时使用的路径参数。请保留安装目录及其生成的备份；不要用其他版本的整个 exe 覆盖组合安装。

Exit the game and run `restore.cmd`. For a custom game location, append the same path option used during installation. Keep the mod folder and generated backups. Do not overwrite combined installations with another version's complete executable.

```powershell
python -X utf8 patch.py restore
```

## 兼容与安装顺序 / Compatibility and order

支持已验证的原版、奔跑和俯视 v0.1.9 等基础程序。包内网格兼容模块仅用于保留既有安装，不代表本次发布网格 mod。世界单步必须最后安装；更改描边前先卸载世界单步。更改奔跑前先卸载描边及俯视。未知程序、资源或按键冲突会拒绝安装。

Supports verified original, toggle-run and camera v0.1.9 executable states, among other explicitly known versions. Bundled grid compatibility modules preserve existing installations; this release does not distribute the unfinished grid mod. Install world-step last and remove it before changing highlight. Remove highlight and camera before changing toggle-run. Unknown files and key conflicts are rejected.

## 实现与验证边界 / Implementation and validation

资源部分增加 6 份材质并替换 9 个模型的描边映射；P 开关使用原生代码载荷。保留全部原材质条目。已有资源、文件回滚及隔离 x64 开关测试；换装、特殊变形、其他模型及完整实机画面仍未验收。

Adds six materials and replaces nine outline mappings; the P toggle uses a native payload. Original material entries are preserved. Existing checks cover resources, restoration and isolated x64 toggle execution. Costumes, transformations, other models and complete in-game visuals remain unverified.

## 更新与故障反馈 / Updates and troubleshooting

游戏更新或 Steam 验证文件可能移除补丁。遇到版本不符、未知修改或损坏备份时，不要跳过哈希检查。请在本仓库 Issues 提供游戏 Build ID、mod 版本、安装顺序、已安装 mod、操作步骤和完整错误信息；不要上传存档或完整游戏文件。

Game updates or Steam file verification may remove the patch. Do not bypass hash checks for unsupported versions, unknown modifications or damaged backups. Report the game Build ID, mod version, installation order, installed mods, reproduction steps and full errors in this repository's Issues. Do not upload saves or complete game files.

## 源码与署名 / Source and credits

仓库提供安装器、必要载荷及开发源码。日常安装使用已生成并校验的载荷；修改原生载荷后须重新构建并同步哈希。既有开发测试可能依赖本地合法游戏样本及同级 mod 工作区，不能视为下载后即能独立运行的通用测试。

The repository includes installers, required payloads and development sources. Normal installation uses generated, verified payloads; native payload changes require rebuilding and updating hashes. Existing developer tests may require local legitimate game samples and sibling mod workspaces; they are not universally standalone tests.

本项目是非官方 AI 生成 mod，与游戏开发商、发行商及 Steam 无隶属关系。游戏及其资源属于原权利人。

This is an unofficial AI-generated mod, unaffiliated with the game's developer, publisher or Steam. The game and its assets belong to their respective rights holders.
