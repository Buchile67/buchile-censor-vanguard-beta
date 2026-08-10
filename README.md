# Buchile Vanguard Beta / Buchile 先锋精修版

先锋版在基础版的轮廓检测流程上加入 SAM 2.1，提供自动与交互式轮廓精修。检测、精修和导出均在本地完成。

Vanguard Beta extends the base contour-detection workflow with SAM 2.1 for automatic and interactive refinement. Detection, refinement, and export run locally, and the application does not upload input files.

> 该版本仍处于 Beta 阶段。SAM 2.1 可改善部分轮廓，但结果仍受初始检测、图像质量与交互提示影响。
>
> This release is still in beta. SAM 2.1 can improve some contours, but results remain dependent on initial detection, image quality, and interactive prompts.

## 版本选择 / Edition guide

[基础版 / Base Edition](https://github.com/Buchile67/buchile-censor) · [先锋版 / Vanguard Beta](https://github.com/Buchile67/buchile-censor-vanguard-beta)

| 版本 / Edition | 主要优势 / Advantages | 适用场景 / Best for |
| --- | --- | --- |
| **[基础版 / Base Edition](https://github.com/Buchile67/buchile-censor)** | 环境更轻、启动与批量处理更快；保留轮廓级遮挡、贴图和低阈值补检等核心功能。<br>Lighter runtime and faster startup/batch processing while retaining contour masking, stickers, and low-threshold recovery. | 优先考虑易部署、处理速度和批量工作流。<br>Prioritizing simpler deployment, speed, and batch workflows. |
| **先锋版 / Vanguard Beta（当前 / Current）** | 增加 SAM 2.1 自动与交互式精修、包含/排除点、CPU/GPU 选择及按图片/区域保存参数。<br>Adds SAM 2.1 automatic and interactive refinement, include/exclude points, CPU/GPU selection, and per-image/per-region profiles. | 对轮廓控制要求更高，并可接受更大的环境和更长的处理时间。<br>Higher contour-control requirements where a larger runtime and longer processing time are acceptable. |

## 中文

### 主要功能

- **原始轮廓**：使用基础版双模型分割结果，处理速度最快。
- **全自动精修**：由检测模型定位区域，再使用 SAM 2.1 细化轮廓。
- **交互式精修**：通过包含点和排除点修正目标边界。
- **CPU / GPU 选择**：支持自动选择、NVIDIA GPU 或 CPU 运行。
- **两种 SAM 2.1 模型**：Tiny 侧重速度，Base Plus 侧重精度。
- **独立识别参数**：识别阈值、补检参数和推理尺寸可应用到当前图片或全部图片。
- **独立参数**：支持按图片、按区域类型保存不同的马赛克设置。
- **预览序号**：可在预览中显示区域序号，且不会写入导出文件。
- **遮挡方式**：支持像素马赛克、内置贴图与自定义贴图；贴图模式不会叠加像素马赛克。
- **批量导出**：支持多图处理及 ZIP 导出。
- **礼盒小游戏**：页面底部可离线随机领取一张内置猫咪图片。

### 安装与启动

从 [Releases](https://github.com/Buchile67/buchile-censor-vanguard-beta/releases) 下载完整包，解压后双击 `start_vanguard_beta.bat`。首次启动会在程序目录中准备独立的 Miniconda 与 `.conda` 环境，不会修改基础版环境。

从源码运行：

```powershell
git clone --recurse-submodules https://github.com/Buchile67/buchile-censor-vanguard-beta.git
cd buchile-censor-vanguard-beta
```

按照 [`models/README.md`](models/README.md) 和 [`checkpoints/README.md`](checkpoints/README.md) 放置模型，然后运行 `start_vanguard_beta.bat`。

## English

### Features

- **Original contours**: uses the base dual-model segmentation output and provides the fastest processing.
- **Full automatic refinement**: localization followed by SAM 2.1 contour refinement.
- **Interactive refinement**: include and exclude points for correcting region boundaries.
- **CPU / GPU selection**: automatic selection, NVIDIA GPU, or CPU execution.
- **Two SAM 2.1 variants**: Tiny prioritizes speed; Base Plus prioritizes accuracy.
- **Independent detection settings**: thresholds, recovery parameters, and inference size can apply to the current image or all images.
- **Independent profiles**: separate mosaic settings for each image and region type.
- **Preview markers**: optional numbered region markers that are never included in exports.
- **Masking methods**: pixel mosaics, built-in stickers, and custom stickers; sticker mode does not mix in pixel mosaics.
- **Batch export**: multi-image processing with ZIP export.
- **Gift-box mini-game**: receive a randomly selected built-in kitty image offline.

### Setup

Download the complete package from [Releases](https://github.com/Buchile67/buchile-censor-vanguard-beta/releases), extract it, and run `start_vanguard_beta.bat`. The first launch prepares an isolated Miniconda installation and `.conda` environment inside the application folder without modifying the base edition.

To run from source:

```powershell
git clone --recurse-submodules https://github.com/Buchile67/buchile-censor-vanguard-beta.git
cd buchile-censor-vanguard-beta
```

Place the files described in [`models/README.md`](models/README.md) and [`checkpoints/README.md`](checkpoints/README.md), then run `start_vanguard_beta.bat`.

## Models and references / 模型与参考项目

- [Buchile Censor base edition / 基础版](https://github.com/Buchile67/buchile-censor)
- [Meta Segment Anything 2](https://github.com/facebookresearch/sam2) — SAM 2.1 source and refinement models.
- [frinkleko/AutoHajimiMosaic](https://github.com/frinkleko/AutoHajimiMosaic) — interaction and segmentation workflow.
- [spawner1145/auto-censor](https://github.com/spawner1145/auto-censor) — processing workflow and extensions.
- [Wenaka2004/auto-censor](https://github.com/Wenaka2004/auto-censor) — earlier YOLO masking workflow and model reference.
- [Ultralytics](https://github.com/ultralytics/ultralytics) — YOLO inference framework.

This project is released under GPL-3.0. The SAM 2 submodule and model weights remain subject to their upstream licenses and terms. Sticker samples are provided by Buchile.

本项目按 GPL-3.0 发布；SAM 2 子模块与模型权重仍遵循各自上游许可证及条款。贴图样例由 Buchile 提供。

## Responsible use / 使用说明

Only process files you own or are authorized to edit. Do not use this tool for illegal material, non-consensual private material, or any material involving minors.

请只处理自己拥有或获准编辑的文件。请勿用于违法内容、未经同意的私人内容或任何涉及未成年人的内容。

## Buchile

- GitHub: [Buchile](https://github.com/Buchile67)
- Pixiv: [Buchile](https://www.pixiv.net/en/users/118035672)

## License / 许可证

[GPL-3.0](LICENSE)
