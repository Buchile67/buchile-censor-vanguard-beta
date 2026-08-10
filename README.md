# Buchile Vanguard Beta / Buchile 先锋精修版

先锋版在基础版的轮廓检测流程上加入 SAM 2.1，提供自动与交互式轮廓精修。检测、精修和导出均在本地完成，程序不会主动上传输入文件。

Vanguard Beta extends the base contour-detection workflow with SAM 2.1 for automatic and interactive refinement. Detection, refinement, and export run locally, and the application does not upload input files.

> 该版本仍处于 Beta 阶段。SAM 2.1 可改善部分轮廓，但结果仍受初始检测、图像质量与交互提示影响。
>
> This release is still in beta. SAM 2.1 can improve some contours, but results remain dependent on initial detection, image quality, and interactive prompts.

## 中文

### 主要功能

- **原始轮廓**：使用基础版双模型分割结果，处理速度最快。
- **全自动精修**：由检测模型定位区域，再使用 SAM 2.1 细化轮廓。
- **交互式精修**：通过包含点和排除点修正目标边界。
- **CPU / GPU 选择**：支持自动选择、NVIDIA GPU 或 CPU 运行。
- **两种 SAM 2.1 模型**：Tiny 侧重速度，Base Plus 侧重精度。
- **独立参数**：支持按图片、按区域类型保存不同的马赛克设置。
- **遮挡方式**：支持像素马赛克、内置贴图与自定义贴图。
- **批量导出**：支持多图处理及 ZIP 导出。

### 安装与启动

从 [Releases](https://github.com/themedark23-oss/buchile-censor-vanguard-beta/releases) 下载完整包，解压后双击 `start_vanguard_beta.bat`。首次启动会在程序目录中准备独立的 Miniconda 与 `.conda` 环境，不会修改基础版环境。

从源码运行：

```powershell
git clone --recurse-submodules https://github.com/themedark23-oss/buchile-censor-vanguard-beta.git
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
- **Independent profiles**: separate mosaic settings for each image and region type.
- **Masking methods**: pixel mosaics, built-in stickers, and custom stickers.
- **Batch export**: multi-image processing with ZIP export.

### Setup

Download the complete package from [Releases](https://github.com/themedark23-oss/buchile-censor-vanguard-beta/releases), extract it, and run `start_vanguard_beta.bat`. The first launch prepares an isolated Miniconda installation and `.conda` environment inside the application folder without modifying the base edition.

To run from source:

```powershell
git clone --recurse-submodules https://github.com/themedark23-oss/buchile-censor-vanguard-beta.git
cd buchile-censor-vanguard-beta
```

Place the files described in [`models/README.md`](models/README.md) and [`checkpoints/README.md`](checkpoints/README.md), then run `start_vanguard_beta.bat`.

## Models and references / 模型与参考项目

- [Buchile Censor base edition / 基础版](https://github.com/themedark23-oss/buchile-censor)
- [Meta Segment Anything 2](https://github.com/facebookresearch/sam2) — SAM 2.1 source and refinement models.
- [frinkleko/AutoHajimiMosaic](https://github.com/frinkleko/AutoHajimiMosaic) — interaction and segmentation workflow.
- [spawner1145/auto-censor](https://github.com/spawner1145/auto-censor) — processing workflow and extensions.
- [Wenaka2004/auto-censor](https://github.com/Wenaka2004/auto-censor) — earlier YOLO masking workflow and model reference.
- [Ultralytics](https://github.com/ultralytics/ultralytics) — YOLO inference framework.

This project is released under GPL-3.0. The SAM 2 submodule and model weights remain subject to their upstream licenses and terms. Sticker samples are provided by Buchile.

本项目按 GPL-3.0 发布；SAM 2 子模块与模型权重仍遵循各自上游许可证及条款。贴图样例由 Buchile 提供。

## Responsible use / 使用边界

Only process files you own or are authorized to edit. Do not use this tool for illegal material, non-consensual private material, or any material involving minors.

请只处理自己拥有或获准编辑的文件。请勿用于违法内容、未经同意的私人内容或任何涉及未成年人的内容。

## Buchile

- GitHub: [Buchile](https://github.com/themedark23-oss)
- Pixiv: [Buchile](https://www.pixiv.net/en/users/118035672)

## License / 许可证

[GPL-3.0](LICENSE)
