# 扩展俯视镜头 / Local Area View

> 因作者目前仍然在打一阶段，目前只确保能在一阶段可使用。
> 该 mod 可能会因游戏更新而失效（26/10/20 可用，2026-10-20）。
> 本项目的 mod 均由 AI 生成。
>
> The author is currently still playing Stage 1; usability is only assured for Stage 1 at present.
> Game updates may break this mod (working as of 2026-10-20).
> All mods in this project are AI-generated.

中文为默认说明语言；English follows each corresponding section.

## 说明 / Description

适用游戏：**Order of the Sinking Star**，Steam Build **26006400**。发行版本：**0.1.9-test**。

Target: **Order of the Sinking Star**, Steam Build **26006400**. Release version: **0.1.9-test**.

按 Q 或手柄右摇杆按下切换俯视，再按一次恢复。原生支持俯视的关卡沿用原版行为；为受限关卡提供新镜头，距离拉远 17%，画面向下偏移可视高度 6%，保持水平朝向与视野角。切换关卡或按 Tab 进入原生远距离模式时退出，不保证整张地图都可见。

Press Q or the right-stick button to toggle the overhead view. Levels with native support retain their original behavior. Restricted levels use a camera with 17% greater distance and a downward framing shift of 6% of visible height, preserving heading and field of view. Changing levels or entering the native distant mode with Tab exits the added view. Full-map visibility is not guaranteed.

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

沿用游戏内 Q／右摇杆按下的绑定，按一次进入、再按一次退出。 / Uses the existing Q / right-stick-button binding; press again to exit.

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

支持已知奔跑及描边组合，安装器会拆分并保留已识别的既有高亮／旧网格层。旧版安装器可能不认识新版组合。世界单步最后安装，更改镜头前先卸载世界单步；更改奔跑前先卸载描边和镜头。保留全部历史 camera_payload 文件，供旧版识别及升级。

Supports known toggle-run and highlight combinations and preserves recognized existing highlight/legacy-grid layers. Older installers may reject newer combinations. Install world-step last and remove it before changing camera. Remove highlight and camera before changing toggle-run. Keep all historical camera_payload files for version recognition and upgrades.

## 实现与验证边界 / Implementation and validation

追加原生镜头代码及状态节，不修改存档或关卡资源。已有 125 组镜头方向、连续更新、17% 距离、6% 偏移、原生回调、旧版升级、组合卸载及 Windows 映像加载检查。仍保留测试版版本号；全关卡实机画面和实体手柄未完整验收。

Appends native camera code and state sections without changing saves or level resources. Existing checks cover 125 camera orientations, repeated updates, the 17% distance/6% shift, native callbacks, upgrades, combined restoration and Windows image loading. The test-version label is retained; complete level coverage and physical-controller behavior remain unverified.

## 更新与故障反馈 / Updates and troubleshooting

游戏更新或 Steam 验证文件可能移除补丁。遇到版本不符、未知修改或损坏备份时，不要跳过哈希检查。请在本仓库 Issues 提供游戏 Build ID、mod 版本、安装顺序、已安装 mod、操作步骤和完整错误信息；不要上传存档或完整游戏文件。

Game updates or Steam file verification may remove the patch. Do not bypass hash checks for unsupported versions, unknown modifications or damaged backups. Report the game Build ID, mod version, installation order, installed mods, reproduction steps and full errors in this repository's Issues. Do not upload saves or complete game files.

## 源码与署名 / Source and credits

仓库提供安装器、必要载荷及开发源码。日常安装使用已生成并校验的载荷；修改原生载荷后须重新构建并同步哈希。既有开发测试可能依赖本地合法游戏样本及同级 mod 工作区，不能视为下载后即能独立运行的通用测试。

The repository includes installers, required payloads and development sources. Normal installation uses generated, verified payloads; native payload changes require rebuilding and updating hashes. Existing developer tests may require local legitimate game samples and sibling mod workspaces; they are not universally standalone tests.

本项目是非官方 AI 生成 mod，与游戏开发商、发行商及 Steam 无隶属关系。游戏及其资源属于原权利人。

This is an unofficial AI-generated mod, unaffiliated with the game's developer, publisher or Steam. The game and its assets belong to their respective rights holders.
