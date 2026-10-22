# 水面网格显示 / Water Surface Grid

> 因作者目前仍然在打一阶段，目前只确保能在一阶段可使用。
> 该 mod 可能会因游戏更新而失效（26/10/22 可用）。
> mod 均由 AI 生成。
>
> The author is still playing Stage 1; usability is only assured for Stage 1 at present.
> Game updates may break this mod (working as of 2026-10-22).
> All mods are AI-generated.

## 说明 / Description

版本 **0.1.0**，适用 **Order of the Sinking Star / Steam Build 26006400 / Windows x64**。仅为 `water_flow`、`water_ripple`、`water_simple`、`ocean_D` 四类水面添加细网格，32 个像素程序。**启动默认关闭，O 键切换**；长按不重复，失焦不响应，切回后需松开再按。

Version **0.1.0** for **Order of the Sinking Star / Steam Build 26006400 / Windows x64**. Adds fine grid lines to four water-surface families: `water_flow`, `water_ripple`, `water_simple` and `ocean_D` (32 pixel programs). **Off at startup; O toggles it.** Holding does not repeat; unfocused input is ignored and held keys must be released after returning.

本项目与尚未完成的“网格显示”mod 分开：不提供地面网格、水下地表增强格线或 I 键控制。四类水面之外的特殊水材质不在保证范围内。用户于 **2026-10-22** 确认开发聊天中安装的版本可正常使用，并与现有 mod 兼容；本发行包重建结果与该版本逐字节一致。

This is separate from the unfinished general grid mod. It provides no ground grid, enhanced underwater-ground grid or I-key control. Other special water materials are outside its supported scope. On **2026-10-22**, the user confirmed the version installed during development worked and was compatible with existing mods. This release reconstructs exactly the same bytes.

[独立发行下载 / Standalone release](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-water-surface-grid/releases/tag/v0.1.0) · [总导航与六 mod 合集 / Hub and six-mod bundle](https://github.com/linyanzhi591-afk/order-of-the-sinking-star-mods)

## 安装 / Installation

需要 Windows x64、64 位 Python 3.10+，无需第三方包、编译器或后台工具。将完整 ZIP 解压到独立可写目录，正常退出游戏，运行根目录 `install.cmd`。成功退出码为 0 后自行启动游戏。

Requires Windows x64 and 64-bit Python 3.10+, without third-party packages, compiler or background tools. Extract the complete ZIP into its own writable folder, exit the game yourself and run the root `install.cmd`. Launch normally after success (exit code 0).

**此版独立载荷只接受已验证的奔跑切换＋俯视 0.1.9＋彩色描边 P＋世界单步 N/M 的完整程序组合**（粒子减量与之独立，原样保留）。它不支持直接给原版程序或任意子组合增加水面层。未具备基础组合时，请使用六 mod 合集，它会按正确顺序补齐。默认按键组合之外、旧网格或其他未知改动会被拒绝。

**This native payload only accepts the verified toggle-run + camera 0.1.9 + highlight P + world-step N/M executable combination.** Particle reduction is independent and preserved. It does not apply directly to the pristine executable or arbitrary subsets. Use the six-mod bundle to install missing prerequisites in order. Other bindings, the unfinished grid and unknown modifications are rejected.

```powershell
.\install.cmd --game-dir "D:\SteamLibrary\steamapps\common\Order of the Sinking Star"
```

不指定路径时查找 Steam 安装位置，无法唯一定位则询问路径。备份、暂存和游戏旁临时文件约需合计 0.4 GB，另有安全余量；以安装器预检为准。写入前会完整备份 exe 和着色器包并校验。只修改这两项，不修改材质包、角色描边映射、关卡包或存档。

Without a path, Steam locations are searched; ambiguous locations prompt for a directory. Backups, staging and game-side temporary files need roughly 0.4 GB combined plus a safety margin, checked before writing. The executable and shader package are completely backed up and verified first. Materials, outline mappings, levels and saves are not modified.

## 使用 / Usage

进入有水面的关卡，按 **O** 开启，再按关闭；每次启动默认关闭。没有本项目的 I 开关，也不改变 P/N/M/Q/Shift 等现有 mod 按键。`status.cmd` 查看状态；`check.cmd` 做完整预检但不写游戏。所有入口均支持 `--game-dir`。

Press **O** in a water area to enable the grid, and again to disable it. Each launch starts with it off. There is no I toggle, and P/N/M/Q/Shift remain unchanged. `status.cmd` reports state; `check.cmd` performs full preflight without writing game files. All launchers accept `--game-dir`.

## 卸载与恢复 / Uninstallation and recovery

正常退出游戏，运行 **`uninstall.cmd`**，精确恢复本目录首次安装前的 exe 和着色器包。保留隐藏的 **`.bundle-state/`**。普通失败自动尝试回滚；强制中断后先退出游戏，再运行 **`recover.cmd`**，恢复到本次操作前状态。恢复可重复执行；未知修改、损坏备份或游戏运行时拒绝写入。

Exit the game and run **`uninstall.cmd`** to restore the exact executable and shader package from before this folder's first installation. Keep hidden **`.bundle-state/`**. Ordinary failures attempt rollback. After interruption, exit the game and run **`recover.cmd`** to restore the pre-operation state. Recovery is repeatable and refuses unknown changes, damaged backups or a running game.

重复安装不覆盖首次基线。如果此前已经由开发版或其他安装器安装同一水面版本，本包将该已有状态作为基线，卸载仍保留原有水面 mod；请用原安装器及其备份卸载原安装。不要混用独立包和合集管理同一活动安装；变更底层程序 mod 前先用拥有该安装记录的安装器卸载水面层。

Reinstallation preserves the first baseline. If the same water mod was already installed by a development or different installer, that existing state becomes the baseline and remains after uninstallation; use its original installer and backups to remove it. Do not mix standalone and bundle installers for the same active installation. Remove the water layer with its owning installer before changing underlying executable mods.

## 兼容性与验证 / Compatibility and validation

原生载荷没有重编译或改变。差量在本机重建已签名的水面着色器，最终完整哈希必须与已验证候选一致。原有 RGB 着色计算、alpha/depth、顶点和根签名沿用原版本；地面条目保持原样。参见 [VALIDATION.md](VALIDATION.md) 和 [PROVENANCE.json](PROVENANCE.json)。

The native payload was not recompiled or changed. Deltas reconstruct the signed water shaders locally, and the complete final hashes must match the verified candidate. Original color calculations, alpha/depth, vertex shaders and root signatures are retained; ground entries remain unchanged. See [VALIDATION.md](VALIDATION.md) and [PROVENANCE.json](PROVENANCE.json).

用户确认的可用及兼容结论不等于全关卡验收。特殊水域、全部镜头与光照条件、后续游戏更新及所有设备仍未穷尽。本次发行验证只使用项目中已有样本的临时副本，不查找、安装或控制实际游戏。

The user's usability/compatibility confirmation is not all-level acceptance. Special water areas, every camera/lighting condition, future updates and all devices remain unexhausted. Release verification uses temporary copies of existing project samples without locating, installing into or controlling the actual game.

## 源码与反馈 / Source and feedback

包内为安装器、原生 C/汇编、着色器注入源码及必要载荷/差量，不含完整 exe、完整资源包、原版资源、存档、备份或旧 Git 历史。问题请附 Build ID、mod 组合、操作步骤和错误信息，不要公开上传游戏文件或存档。本 mod 非官方，与游戏开发商、发行商及 Steam 无隶属关系。

Includes installers, native C/assembly, shader-injection source and required payload/deltas; no complete executable/resource package, original assets, saves, backups or old Git history. Reports should include the Build ID, mod combination, steps and errors; do not publicly upload game files or saves. This unofficial mod is unaffiliated with the developer, publisher or Steam.
