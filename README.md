# Buchile Vanguard Beta / Buchile 先锋精修版

基础版负责把像素小被子盖上，先锋版还请来 SAM 2.1 帮忙把被角掖整齐。它在本地完成检测、轮廓精修与导出，不会把图片交给云端围观。

The base edition brings the pixel blanket; Vanguard Beta asks SAM 2.1 to tuck in the edges. Detection, refinement, and export all run locally—no cloud audience invited.

> Beta means adventurous, not magical. Automatic refinement can improve contours, while interactive points are there for the occasions when the AI confidently befriends the wrong leaf.
>
> Beta 的意思是敢于探路，不是会魔法。全自动精修能改善轮廓；如果 AI 热情地认错了一片树叶，还可以用交互点把它劝回来。

## 中文

### 先锋版多了什么

- **原始轮廓**：沿用双模型分割，速度最快。
- **全自动精修**：先定位目标，再由 SAM 2.1 自动细化像素轮廓。
- **交互式精修**：在图上添加绿色包含点或红色排除点，手动告诉 SAM 2.1“这里要”“那里不要”。
- **CPU / GPU 可选**：有可用的 NVIDIA CUDA 环境时可以用 GPU；CPU 也能跑，只是需要多一点耐心。
- **两档 SAM 2.1**：Tiny 偏速度，Base Plus 偏精度。
- **分图片、分区域参数**：每张图、每类区域都能保留自己的马赛克强度、贴图和轮廓柔化设置。
- **贴图小分队**：大狗、猫咪或自行上传，三选一。
- **批量出图**：多张图片分别处理，最后打成 ZIP 带走。

### 一键包

前往 [Releases](https://github.com/themedark23-oss/buchile-censor-vanguard-beta/releases) 下载完整包，解压后双击 `start_vanguard_beta.bat`。它会在当前文件夹里准备独立的 Miniconda 和 `.conda` 环境，不会改动基础版。

首次启动需要网络并会下载运行依赖，体积不小，适合泡杯茶再回来。模型、SAM 2.1 源码和 Tiny/Base Plus 检查点已经放在一键包中。

### 从源码启动

```powershell
git clone --recurse-submodules https://github.com/themedark23-oss/buchile-censor-vanguard-beta.git
cd buchile-censor-vanguard-beta
```

按照 [`models/README.md`](models/README.md) 和 [`checkpoints/README.md`](checkpoints/README.md) 放好模型，然后双击 `start_vanguard_beta.bat`。第一次运行会自动调用安装脚本。

## English

### What Vanguard adds

- **Original contours**: the fastest dual-model workflow.
- **Full auto refinement**: initial localization followed by automatic SAM 2.1 contour cleanup.
- **Interactive refinement**: green include points and red exclude points for telling SAM 2.1 “yes here, no there.”
- **CPU / GPU selection**: an NVIDIA CUDA setup gets the fast lane; CPU remains available with a larger patience budget.
- **Two SAM 2.1 sizes**: Tiny favors speed, while Base Plus favors detail.
- **Per-image and per-region profiles**: every image and region type can keep its own mosaic strength, sticker, and feathering.
- **Sticker squad**: dog, cat, or your own upload.
- **Batch export**: process multiple images and take the results home in one ZIP.

### One-click package

Download the complete bundle from [Releases](https://github.com/themedark23-oss/buchile-censor-vanguard-beta/releases), extract it, and double-click `start_vanguard_beta.bat`. It prepares a private Miniconda installation and `.conda` environment inside the folder, leaving the base edition untouched.

The first launch needs a network connection and downloads sizeable dependencies—an excellent tea break. The package already carries the two localization models, SAM 2.1 source, and both Tiny/Base Plus checkpoints.

### Run from source

```powershell
git clone --recurse-submodules https://github.com/themedark23-oss/buchile-censor-vanguard-beta.git
cd buchile-censor-vanguard-beta
```

Place the models listed in [`models/README.md`](models/README.md) and [`checkpoints/README.md`](checkpoints/README.md), then double-click `start_vanguard_beta.bat`. The setup script runs automatically on the first launch.

## Models and upstream projects / 模型与参考项目

- [Buchile Censor base edition / 基础版](https://github.com/themedark23-oss/buchile-censor)
- [Meta Segment Anything 2](https://github.com/facebookresearch/sam2) — SAM 2.1 source and refinement models.
- [frinkleko/AutoHajimiMosaic](https://github.com/frinkleko/AutoHajimiMosaic) — interaction and segmentation workflow.
- [spawner1145/auto-censor](https://github.com/spawner1145/auto-censor) — processing workflow and follow-up ideas.
- [Wenaka2004/auto-censor](https://github.com/Wenaka2004/auto-censor) — earlier YOLO masking workflow and model trail.
- [Ultralytics](https://github.com/ultralytics/ultralytics) — YOLO inference framework.

This project is released under GPL-3.0. The SAM 2 submodule and all model weights keep their respective upstream licenses and terms. The dog and cat sticker samples are provided by Buchile.

本项目按 GPL-3.0 发布。SAM 2 子模块及全部模型权重仍遵循各自上游许可证与条款。大狗与猫咪贴图样例由 Buchile 提供。

## Keep it sensible / 请文明使用

Only process files you own or are allowed to edit. Do not use this tool for illegal material, non-consensual private material, or anything involving minors. This repository contains no sample media of that kind.

请只处理自己拥有或获准编辑的文件。请勿用于违法内容、未经同意的私人内容或任何涉及未成年人的内容。仓库不会放置此类示例媒体。

## Buchile

- GitHub: [Buchile](https://github.com/themedark23-oss)
- Pixiv: [Buchile](https://www.pixiv.net/en/users/118035672)

## License / 许可证

[GPL-3.0](LICENSE)
