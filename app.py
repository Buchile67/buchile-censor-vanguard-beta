from __future__ import annotations

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit.elements.image as streamlit_image_module
from PIL import Image

# streamlit-image-coordinates 0.4 still imports this legacy type alias. It is
# annotation-only, so restoring the alias keeps the component compatible with
# current Streamlit without changing either installed package.
if not hasattr(streamlit_image_module, "UseColumnWith"):
    streamlit_image_module.UseColumnWith = str

from streamlit_image_coordinates import streamlit_image_coordinates

from core import (
    MODEL_SPECS,
    PART_LABELS,
    apply_censor,
    decode_image,
    decode_sticker,
    detect_regions,
    detections_for_parts,
    draw_detection_markers,
    encode_image,
    load_segmentation_models,
)
from sam_refine import (
    SAM_VARIANTS,
    build_sam_bundle,
    device_summary,
    draw_interaction_overlay,
    refine_detections,
    resolve_device,
)
from kitty_game import render_kitty_gift_game
from preview_navigation import render_preview_navigator
from refine_entry import render_refine_entry
from region_selection import (
    effective_selected_ids,
    region_selection_key,
    region_selection_signature,
    save_selected_ids,
)


ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"
CHECKPOINT_DIR = ROOT / "checkpoints"
BRAND_ICON = ROOT / "assets" / "buchile.jpg"
KITTY_GALLERY_DIR = ROOT / "assets" / "kitty_gallery"
PIXIV_URL = "https://www.pixiv.net/en/users/118035672"
GITHUB_PROFILE_URL = "https://github.com/Buchile67"
BASIC_REPO_URL = "https://github.com/Buchile67/buchile-censor"
VANGUARD_REPO_URL = "https://github.com/Buchile67/buchile-censor-vanguard-beta"
STICKER_SAMPLES = {
    "dagou": ROOT / "assets" / "dagou.png",
    "maodie": ROOT / "assets" / "maodie.png",
}

PARTS = list(PART_LABELS)
PRESETS = {
    "all": PARTS,
    "genitals": ["anus", "male_genital", "female_genital"],
    "female": ["breasts", "female_genital", "anus"],
    "male": ["male_genital", "anus"],
    "breasts": ["breasts"],
    "custom": PARTS,
}

DEFAULT_EFFECT_PROFILE = {
    "mode": "pixel",
    "block_size": 18,
    "feather": 1,
    "sticker_source": "dagou",
    "sticker_bytes": None,
}

DEFAULT_DETECTION_PROFILE = {
    "base_threshold": 0.35,
    "supplement_parts": (),
    "supplement_threshold": 0.12,
    "image_size": 960,
}

I18N = {
    "zh": {
        "page_title": "Buchile Vanguard Beta 先锋精修",
        "subtitle": "双模型定位 · SAM 2.1 轮廓精修 · 自动/交互双模式 · CPU/GPU 可选 · 多图导出",
        "creator_link": "作者 Pixiv 主页",
        "free_notice": "本工具为免费开源工具，如果您是通过任何付费方式获得本工具，均为盗版！！😭",
        "project_links": "项目与源代码",
        "acknowledgements": "致谢与参考项目",
        "acknowledgements_intro": "感谢以下开源项目、模型与开发者提供的工作基础：",
        "gift_prompt": "送你一只小猫咪，点击即送！",
        "gift_reveal": "收下属于你的可爱耄耋吧！",
        "language": "界面语言 / Language",
        "settings": "打码设置",
        "refinement": "先锋精修",
        "refine_mode": "轮廓模式",
        "refine_original": "原始轮廓",
        "refine_auto": "全自动精修",
        "refine_interactive": "交互式精修",
        "refine_help": "自动模式由 YOLO 定位、SAM2 精修；交互模式还可用包含点和排除点修正边缘。",
        "runtime": "运行设备",
        "runtime_auto": "自动",
        "runtime_gpu": "GPU",
        "runtime_cpu": "CPU",
        "runtime_status_gpu": "正在使用 GPU：{name}（{vram} GB）",
        "runtime_status_cpu": "正在使用 CPU；SAM2 精修速度会明显较慢。",
        "gpu_unavailable": "当前独立环境未检测到可用的 NVIDIA GPU/CUDA，请选择 CPU 或检查驱动。",
        "sam_model": "SAM2 精修模型",
        "sam_tiny": "Tiny（速度优先）",
        "sam_base_plus": "Base Plus（精度优先）",
        "sam_model_help": "CPU 建议 Tiny；GPU 默认 Base Plus。",
        "preset": "部位预设",
        "preset_all": "全部敏感部位",
        "preset_genitals": "生殖器重点",
        "preset_female": "女性重点",
        "preset_male": "男性重点",
        "preset_breasts": "仅胸部",
        "preset_custom": "自定义",
        "selected_parts": "需要打码的部位",
        "selected_parts_help": "预设之后仍可手动增删。",
        "part_anus": "肛门",
        "part_fluids": "体液",
        "part_male_genital": "男性生殖器",
        "part_breasts": "胸部",
        "part_female_genital": "女性生殖器",
        "sensitivity": "检测灵敏度",
        "base_threshold": "常规识别阈值",
        "base_threshold_help": "越低越容易找到部位，也越可能误判。",
        "supplement_parts": "补检部位",
        "supplement_parts_help": "只对这些部位启用更低阈值，用于增添常规检测遗漏的区域。",
        "supplement_threshold": "补检阈值",
        "accuracy": "识别精度",
        "accuracy_help": "推理尺寸范围为 320–1920，按模型步长 32 调整。更高可能提升小目标细节，但会增加显存、内存和处理时间。",
        "detection_profiles": "识别阈值与精度",
        "detection_profiles_help": "设置常规阈值、补检参数和推理尺寸，再选择仅应用到当前图片或应用到全部图片。",
        "detection_profile_current": "当前图片正在使用独立识别参数。",
        "detection_profile_global": "当前图片正在使用全局识别参数。",
        "detection_apply_hint": "修改后请点击应用按钮；预览和批量导出仅使用已保存的识别参数。",
        "detection_applied_current": "已保存当前图片的独立识别参数。",
        "detection_applied_all": "已更新全部图片的识别参数，并清除旧的单图覆盖。",
        "mosaic_profiles": "分区域马赛克参数",
        "mosaic_profiles_help": "先选择区域类型和参数，再决定仅应用到当前图片或覆盖所有图片。批量导出会保留每张图片的独立状态。",
        "profile_target": "参数对应的敏感区域",
        "profile_all_parts": "全部敏感区域（统一设置）",
        "mode": "打码方式",
        "mode_pixel": "普通马赛克",
        "mode_sticker": "贴图马赛克",
        "block_size": "马赛克强度（像素块大小）",
        "feather": "轮廓内侧柔化",
        "feather_help": "仅在蒙版内部柔化边缘，不会越出识别轮廓。",
        "custom_sticker": "自定义贴图（可选）",
        "custom_sticker_help": "不上传时使用已选内置贴图；透明区域会使用贴图自身颜色填充，不会混入普通马赛克。",
        "sticker_source": "贴图来源",
        "sticker_dagou": "大狗叫（大狗样例）",
        "sticker_maodie": "耄耋（猫咪样例）",
        "sticker_custom": "自行上传",
        "saved_sticker": "当前配置已保存自定义贴图；不重新上传时会继续使用。",
        "apply_current": "仅应用到当前图片",
        "apply_all_images": "应用到所有图片",
        "applied_current": "已保存：当前图片的 {target} 使用独立马赛克参数。",
        "applied_all": "已保存：所有图片的 {target} 已统一为这组参数。",
        "independent_count": "当前图片有 {count} 类区域使用独立参数。",
        "profile_apply_hint": "修改后请点击下方应用按钮；预览和批量导出只使用已保存参数。",
        "output_format": "导出格式",
        "model_license": "模型与许可",
        "model_description": "使用 Hachimi 与 Maodie 两套 YOLO 分割模型进行互补检测。",
        "license_description": "本工具按 GPL-3.0 发布，不提供任何担保；模型权利归各自作者所有。",
        "upload": "上传一张或多张图片",
        "upload_help": "可一次选择多张图片。每张图片可保存独立的分区域马赛克参数，批量导出会逐张保留这些状态。",
        "initial_parts_guide": "第一步：请先在左侧选择部位预设，并在“需要打码的部位”中确认或增删目标；第二步：再上传图片开始识别。",
        "sidebar_parts_guide": "先选择预设，再检查下方部位列表；只有选中的部位会进入识别与打码流程。",
        "select_part_warning": "请至少选择一个需要打码的部位。",
        "preview_file": "当前预览图片",
        "detecting": "正在进行轮廓级检测…",
        "refining": "SAM2 正在精修轮廓…",
        "select_regions": "选择当前图片中需要遮挡的具体区域",
        "select_regions_help": "与 Hachimi 的部位选择相似，但这里每个实例都可单独开关。",
        "interaction_title": "交互式轮廓修正",
        "interaction_target": "要修正的区域",
        "point_type": "点击类型",
        "positive": "包含点（绿色）",
        "negative": "排除点（红色）",
        "interaction_help": "在图上点击：包含点让 SAM2 纳入该处，排除点让它避开树叶、衣物或背景。黄色线是初始轮廓。",
        "undo": "撤销上一点",
        "clear": "清空当前区域的点",
        "point_count": "当前区域已有 {count} 个修正点",
        "original": "原图",
        "preview": "精细打码预览",
        "previous_image": "上一张图片",
        "next_image": "下一张图片",
        "preview_position": "第 {current} / {total} 张",
        "interactive_refine_prefix": "对当前结果不满意？进行",
        "interactive_refine_word": "交互式精修",
        "interactive_refine_suffix": "！",
        "interactive_refine_entry_hint": "已进入当前图片的交互式精修",
        "interactive_refine_active": "当前图片的交互式精修已启用；下面的操作和结果会在切换图片后继续保留。",
        "interactive_no_detection": "当前所选部位没有可精修的检测区域。请先在左侧确认“需要打码的部位”；若仍未识别到，请展开“识别阈值与精度”，把对应部位加入“补检部位”、降低补检阈值，并点击“仅应用到当前图片”。",
        "interactive_no_selection": "已经识别到区域，但当前没有选中精修目标。请在上方“选择当前图片中需要遮挡的具体区域”中至少选择一项。",
        "show_region_numbers": "显示识别区域序号",
        "show_region_numbers_help": "红底白字序号仅显示在页面预览中，不会写入下载图片或批量导出结果。",
        "no_detection": "没有找到所选部位。可在左侧把对应部位加入“补检部位”，并降低补检阈值。",
        "diagnostics": "SAM2 精修状态",
        "diagnostic_line": "区域 {index}：SAM 分数 {score:.2f}，轮廓重合度 {iou:.2f}，提示点 {points} 个{fallback}",
        "fallback": "（安全回退到原轮廓）",
        "download_preview": "下载当前预览",
        "batch_title": "批量处理与导出",
        "batch_caption": "批量模式会逐张检测和精修，并按每张图片、每类敏感区域已保存的马赛克参数分别导出。",
        "process_all": "处理全部图片",
        "download_all": "下载全部结果（ZIP）",
        "batch_messages": "批量处理提示",
        "batch_prepare": "准备批量处理…",
        "batch_processing": "正在处理 {name}",
        "batch_done": "批量处理完成",
        "batch_not_found": "{name}：未找到所选部位，已原样导出",
        "batch_failed": "{name}：处理失败（{error}）",
    },
    "en": {
        "page_title": "Buchile Vanguard Beta",
        "subtitle": "Dual-model localization · SAM 2.1 refinement · Automatic/interactive modes · CPU/GPU · Batch export",
        "creator_link": "Creator on Pixiv",
        "free_notice": "This is a free and open-source tool. If you obtained it through any paid channel, it is an unauthorized copy!! 😭",
        "project_links": "Projects and Source Code",
        "acknowledgements": "Acknowledgements and References",
        "acknowledgements_intro": "Many thanks to the following open-source projects, models, and developers:",
        "gift_prompt": "A little kitty for you—click to receive!",
        "gift_reveal": "Take home your very own adorable kitty!",
        "language": "Language / 界面语言",
        "settings": "Censor Settings",
        "refinement": "Vanguard Refinement",
        "refine_mode": "Contour Mode",
        "refine_original": "Original Contours",
        "refine_auto": "Full Auto Refinement",
        "refine_interactive": "Interactive Refinement",
        "refine_help": "Auto uses YOLO for localization and SAM2 for refinement. Interactive also accepts include/exclude points.",
        "runtime": "Compute Device",
        "runtime_auto": "Auto",
        "runtime_gpu": "GPU",
        "runtime_cpu": "CPU",
        "runtime_status_gpu": "Using GPU: {name} ({vram} GB)",
        "runtime_status_cpu": "Using CPU; SAM2 refinement will be substantially slower.",
        "gpu_unavailable": "No usable NVIDIA GPU/CUDA was detected. Choose CPU or check the driver.",
        "sam_model": "SAM2 Refinement Model",
        "sam_tiny": "Tiny (Faster)",
        "sam_base_plus": "Base Plus (More Accurate)",
        "sam_model_help": "Tiny is recommended on CPU; Base Plus is the GPU default.",
        "preset": "Region Preset",
        "preset_all": "All Sensitive Regions",
        "preset_genitals": "Genitals Focus",
        "preset_female": "Female Focus",
        "preset_male": "Male Focus",
        "preset_breasts": "Breasts Only",
        "preset_custom": "Custom",
        "selected_parts": "Regions to Censor",
        "selected_parts_help": "You can add or remove regions after choosing a preset.",
        "part_anus": "Anus",
        "part_fluids": "Fluids",
        "part_male_genital": "Male Genitalia",
        "part_breasts": "Breasts",
        "part_female_genital": "Female Genitalia",
        "sensitivity": "Detection Sensitivity",
        "base_threshold": "Standard Detection Threshold",
        "base_threshold_help": "Lower values find more regions but may add false positives.",
        "supplement_parts": "Recovery Regions",
        "supplement_parts_help": "Apply a lower threshold only to these regions to recover possible misses.",
        "supplement_threshold": "Recovery Threshold",
        "accuracy": "Detection Resolution",
        "accuracy_help": "Inference size ranges from 320 to 1920 in model-stride steps of 32. Higher values may preserve small details but use more memory and processing time.",
        "detection_profiles": "Detection Threshold and Resolution",
        "detection_profiles_help": "Set standard/recovery thresholds and inference size, then apply them to the current image or every image.",
        "detection_profile_current": "This image is using independent detection parameters.",
        "detection_profile_global": "This image is using the global detection parameters.",
        "detection_apply_hint": "Click an apply button after editing. Preview and batch export use saved detection parameters only.",
        "detection_applied_current": "Saved independent detection parameters for the current image.",
        "detection_applied_all": "Updated detection parameters for all images and cleared previous per-image overrides.",
        "mosaic_profiles": "Per-Region Mosaic Profiles",
        "mosaic_profiles_help": "Choose a region type and parameters, then apply them only to this image or overwrite every image. Batch export preserves per-image states.",
        "profile_target": "Sensitive Region for These Parameters",
        "profile_all_parts": "All Sensitive Regions (Unified)",
        "mode": "Censor Mode",
        "mode_pixel": "Pixel Mosaic",
        "mode_sticker": "Sticker Mosaic",
        "block_size": "Mosaic Strength (Pixel Block Size)",
        "feather": "Inner Contour Feathering",
        "feather_help": "Softens only inside the mask and never paints beyond its contour.",
        "custom_sticker": "Custom Sticker (Optional)",
        "custom_sticker_help": "Uses the selected built-in sticker by default. Transparent margins are filled from the sticker itself and never mixed with pixel mosaic.",
        "sticker_source": "Sticker Source",
        "sticker_dagou": "Dog Sample",
        "sticker_maodie": "Cat Sample",
        "sticker_custom": "Custom Upload",
        "saved_sticker": "This profile already has a saved custom sticker; it will remain unless replaced.",
        "apply_current": "Apply to Current Image Only",
        "apply_all_images": "Apply to All Images",
        "applied_current": "Saved: {target} now has independent mosaic parameters for this image.",
        "applied_all": "Saved: {target} now uses these parameters for every image.",
        "independent_count": "This image has independent parameters for {count} region type(s).",
        "profile_apply_hint": "After editing, click an apply button. Preview and batch export use saved parameters only.",
        "output_format": "Export Format",
        "model_license": "Models and License",
        "model_description": "Uses the Hachimi and Maodie YOLO segmentation models for complementary detection.",
        "license_description": "Released under GPL-3.0 without warranty. Model rights remain with their respective authors.",
        "upload": "Upload One or More Images",
        "upload_help": "Upload multiple images at once. Each image can save independent mosaic parameters for every sensitive-region type.",
        "initial_parts_guide": "Step 1: choose a region preset in the sidebar and confirm the targets under Regions to Censor. Step 2: upload images to begin detection.",
        "sidebar_parts_guide": "Choose a preset, then review the list below. Only selected region types enter detection and censoring.",
        "select_part_warning": "Select at least one region to censor.",
        "preview_file": "Preview Image",
        "detecting": "Detecting precise contours…",
        "refining": "SAM2 is refining contours…",
        "select_regions": "Select Specific Regions to Censor in This Image",
        "select_regions_help": "Similar to Hachimi region selection, with an independent switch for every detected instance.",
        "interaction_title": "Interactive Contour Correction",
        "interaction_target": "Region to Correct",
        "point_type": "Click Type",
        "positive": "Include Point (Green)",
        "negative": "Exclude Point (Red)",
        "interaction_help": "Click the image: include points add an area; exclude points keep SAM2 away from leaves, clothing, or background. Yellow is the initial contour.",
        "undo": "Undo Last Point",
        "clear": "Clear Points for This Region",
        "point_count": "This region has {count} correction point(s)",
        "original": "Original",
        "preview": "Precision Censor Preview",
        "previous_image": "Previous Image",
        "next_image": "Next Image",
        "preview_position": "Image {current} of {total}",
        "interactive_refine_prefix": "Not satisfied with this result? Try ",
        "interactive_refine_word": "interactive refinement",
        "interactive_refine_suffix": "!",
        "interactive_refine_entry_hint": "Interactive refinement is open for this image",
        "interactive_refine_active": "Interactive refinement is active for this image. Its edits and result remain available after switching images.",
        "interactive_no_detection": "No editable detection was found for the selected region types. Confirm Regions to Censor in the sidebar. If the target is still missing, open Detection Threshold and Resolution, add the region under Recovery Regions, lower its threshold, and click Apply to Current Image Only.",
        "interactive_no_selection": "Regions were detected, but none is selected for refinement. Select at least one item under Select Specific Regions to Censor in This Image above.",
        "show_region_numbers": "Show Detected Region Numbers",
        "show_region_numbers_help": "Red numbered markers appear only in the page preview and are never written to downloaded or batch-exported images.",
        "no_detection": "No selected regions were found. Add the region under Recovery Regions and lower the recovery threshold.",
        "diagnostics": "SAM2 Refinement Status",
        "diagnostic_line": "Region {index}: SAM score {score:.2f}, contour overlap {iou:.2f}, {points} prompt(s){fallback}",
        "fallback": " (safety fallback to original contour)",
        "download_preview": "Download Current Preview",
        "batch_title": "Batch Processing and Export",
        "batch_caption": "Batch mode detects and refines each image, then exports it with its saved per-image and per-region mosaic profiles.",
        "process_all": "Process All Images",
        "download_all": "Download All Results (ZIP)",
        "batch_messages": "Batch Processing Messages",
        "batch_prepare": "Preparing batch processing…",
        "batch_processing": "Processing {name}",
        "batch_done": "Batch processing complete",
        "batch_not_found": "{name}: no selected region found; exported unchanged",
        "batch_failed": "{name}: processing failed ({error})",
    },
}


language = st.session_state.get("language", "zh")


def tr(key: str, **values) -> str:
    return I18N[language][key].format(**values)


def part_label(part: str) -> str:
    return tr(f"part_{part}")


st.set_page_config(page_title=tr("page_title"), page_icon=Image.open(BRAND_ICON), layout="wide")
st.markdown(
    """
    <style>
      .block-container {max-width: 1240px; padding-top: 2rem;}
      [data-testid="stImage"] img {border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_models():
    return load_segmentation_models(MODEL_DIR)


@st.cache_resource(show_spinner=False)
def get_sam_bundle(variant: str, device: str):
    return build_sam_bundle(CHECKPOINT_DIR, variant, device)


@st.cache_data(show_spinner=False, max_entries=32)
def cached_decode(data: bytes) -> np.ndarray:
    return decode_image(data)


@st.cache_data(show_spinner=False, max_entries=64)
def run_detection(
    data: bytes,
    base_threshold: float,
    supplement_parts: tuple[str, ...],
    supplement_threshold: float,
    image_size: int,
    device: str,
):
    image = cached_decode(data)
    return detect_regions(
        image,
        get_models(),
        base_threshold=base_threshold,
        supplement_parts=supplement_parts,
        supplement_threshold=supplement_threshold,
        image_size=image_size,
        device=device,
    )


@st.cache_data(show_spinner=False, max_entries=48)
def run_refinement(
    data: bytes,
    selected_uids: tuple[str, ...],
    variant: str,
    device: str,
    points_tuple: tuple[tuple[str, tuple[tuple[float, float, int], ...]], ...],
    _detections,
):
    uid_set = set(selected_uids)
    selected = [item for item in _detections if item.uid in uid_set]
    point_map = {uid: list(points) for uid, points in points_tuple}
    return refine_detections(cached_decode(data), selected, get_sam_bundle(variant, device), point_map)


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem.strip() or "image"
    return "".join(character if character.isalnum() or character in "-_." else "_" for character in stem)


def region_label(index, detection) -> str:
    return f"{index + 1}. {part_label(detection.part)}"


def file_key(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()[:16]


def refinement_store() -> dict[str, str]:
    return st.session_state.setdefault("image_refinement_modes", {})


def effective_refine_mode(image_id: str, default_mode: str) -> str:
    return refinement_store().get(image_id, default_mode)


def refinement_state_signature() -> tuple[tuple[str, str], ...]:
    return tuple(sorted(refinement_store().items()))


def points_for_image(data: bytes, detections) -> dict[str, list[tuple[float, float, int]]]:
    store = st.session_state.setdefault("sam_interactive_points", {})
    prefix = file_key(data)
    return {item.uid: list(store.get(f"{prefix}:{item.uid}", [])) for item in detections}


def points_as_tuple(points: dict[str, list[tuple[float, float, int]]]):
    return tuple(sorted((uid, tuple(items)) for uid, items in points.items() if items))


def upload_key(index: int, filename: str, data: bytes) -> str:
    identity = f"{index}:{filename}:".encode("utf-8") + data
    return hashlib.sha1(identity).hexdigest()[:20]


def move_preview(delta: int, total: int) -> None:
    current = int(st.session_state.get("preview_index", 0))
    st.session_state["preview_index"] = max(0, min(total - 1, current + delta))


def sync_region_number_visibility() -> None:
    st.session_state["region_numbers_visible"] = bool(
        st.session_state.get("show_region_numbers", True)
    )


def region_selection_store() -> dict[str, tuple[str, ...]]:
    return st.session_state.setdefault("image_region_selections", {})


def sync_region_selection(
    selection_key: str,
    widget_key: str,
    label_to_id: dict[str, str],
) -> None:
    selected_labels = st.session_state.get(widget_key, [])
    save_selected_ids(
        region_selection_store(),
        selection_key,
        (label_to_id[label] for label in selected_labels if label in label_to_id),
    )
    st.session_state.pop("batch_result", None)


def enable_interactive_refinement(image_id: str) -> None:
    refinement_store()[image_id] = "interactive"
    st.session_state.pop("batch_result", None)


def detection_store() -> dict:
    if "detection_profiles" not in st.session_state:
        st.session_state["detection_profiles"] = {
            "global": dict(DEFAULT_DETECTION_PROFILE),
            "images": {},
        }
    store = st.session_state["detection_profiles"]
    store["global"].setdefault("supplement_parts", ())
    return store


def effective_detection_profile(image_id: str) -> dict:
    store = detection_store()
    profile = store["images"].get(image_id, store["global"])
    result = dict(profile)
    result["supplement_parts"] = tuple(result.get("supplement_parts", ()))
    return result


def detection_state_signature() -> tuple:
    store = detection_store()

    def value(profile: dict) -> tuple:
        return (
            float(profile["base_threshold"]),
            tuple(profile.get("supplement_parts", ())),
            float(profile["supplement_threshold"]),
            int(profile["image_size"]),
        )

    return (
        value(store["global"]),
        tuple((image_id, value(profile)) for image_id, profile in sorted(store["images"].items())),
    )


def mosaic_store() -> dict:
    if "mosaic_profiles" not in st.session_state:
        st.session_state["mosaic_profiles"] = {
            "global": {part: dict(DEFAULT_EFFECT_PROFILE) for part in PARTS},
            "images": {},
        }
    store = st.session_state["mosaic_profiles"]
    for part in PARTS:
        store["global"].setdefault(part, dict(DEFAULT_EFFECT_PROFILE))
        global_profile = store["global"][part]
        global_profile.setdefault(
            "sticker_source", "custom" if global_profile.get("sticker_bytes") else "dagou"
        )
    for image_profiles in store["images"].values():
        for profile in image_profiles.values():
            profile.setdefault(
                "sticker_source", "custom" if profile.get("sticker_bytes") else "dagou"
            )
    return store


def effective_mosaic_profiles(image_id: str) -> dict[str, dict]:
    store = mosaic_store()
    overrides = store["images"].get(image_id, {})
    return {
        part: dict(overrides.get(part, store["global"][part]))
        for part in PARTS
    }


def apply_profiled_censor(image, detections, profiles: dict[str, dict]):
    output = image.copy()
    for part in PARTS:
        part_detections = [item for item in detections if item.part == part]
        if not part_detections:
            continue
        profile = profiles[part]
        sticker_rgba = None
        if profile["mode"] == "sticker":
            sticker_source = profile.get("sticker_source", "dagou")
            sticker_path = STICKER_SAMPLES.get(sticker_source, STICKER_SAMPLES["dagou"])
            sticker_bytes = profile.get("sticker_bytes") if sticker_source == "custom" else None
            sticker_rgba = decode_sticker(sticker_bytes, sticker_path)
        output = apply_censor(
            output,
            part_detections,
            selected_ids=None,
            mode=profile["mode"],
            block_size=int(profile["block_size"]),
            feather=int(profile["feather"]),
            sticker_rgba=sticker_rgba,
        )
    return output


def mosaic_state_signature() -> tuple:
    store = mosaic_store()

    def profile_value(profile: dict) -> tuple:
        sticker = profile.get("sticker_bytes") or b""
        return (
            profile["mode"],
            int(profile["block_size"]),
            int(profile["feather"]),
            profile.get("sticker_source", "dagou"),
            hashlib.sha1(sticker).hexdigest(),
        )

    global_values = tuple((part, profile_value(store["global"][part])) for part in PARTS)
    image_values = tuple(
        (
            image_id,
            tuple((part, profile_value(profile)) for part, profile in sorted(profiles.items())),
        )
        for image_id, profiles in sorted(store["images"].items())
    )
    return global_values, image_values


def build_zip(
    uploaded_files,
    selected_parts,
    output_format,
    refine_mode,
    sam_variant,
    device,
) -> tuple[bytes, list[str]]:
    buffer = BytesIO()
    warnings: list[str] = []
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        progress = st.progress(0, text=tr("batch_prepare"))
        for index, uploaded in enumerate(uploaded_files):
            progress.progress(index / len(uploaded_files), text=tr("batch_processing", name=uploaded.name))
            try:
                data = uploaded.getvalue()
                image = cached_decode(data)
                image_id = upload_key(index, uploaded.name, data)
                detection_settings = {
                    **effective_detection_profile(image_id),
                    "device": device,
                }
                detections = run_detection(data, **detection_settings)
                chosen = detections_for_parts(detections, selected_parts)
                selection_key = region_selection_key(
                    image_id, selected_parts, detection_settings
                )
                selected_ids = effective_selected_ids(
                    region_selection_store(),
                    selection_key,
                    (item.uid for item in chosen),
                )
                chosen = [item for item in chosen if item.uid in selected_ids]
                if not chosen:
                    warnings.append(tr("batch_not_found", name=uploaded.name))
                image_refine_mode = effective_refine_mode(image_id, refine_mode)
                if image_refine_mode != "original" and chosen:
                    saved_points = (
                        points_for_image(data, chosen)
                        if image_refine_mode == "interactive"
                        else {}
                    )
                    chosen, _ = run_refinement(
                        data,
                        tuple(item.uid for item in chosen),
                        sam_variant,
                        device,
                        points_as_tuple(saved_points),
                        chosen,
                    )
                processed = apply_profiled_censor(
                    image, chosen, effective_mosaic_profiles(image_id)
                )
                extension = "jpg" if output_format == "JPEG" else "png"
                filename = f"{index + 1:03d}_{safe_stem(uploaded.name)}_censored.{extension}"
                archive.writestr(filename, encode_image(processed, output_format))
            except Exception as error:
                warnings.append(tr("batch_failed", name=uploaded.name, error=error))
        progress.progress(1.0, text=tr("batch_done"))
    return buffer.getvalue(), warnings


brand_icon_column, brand_title_column = st.columns([0.07, 0.93], gap="small", vertical_alignment="center")
with brand_icon_column:
    st.image(BRAND_ICON, width=70)
with brand_title_column:
    st.title(tr("page_title"))
st.caption(tr("subtitle"))
st.markdown(f"{tr('creator_link')}: [Buchile]({PIXIV_URL})")
st.warning(tr("free_notice"), icon="⚠️")
st.markdown(
    f"{tr('project_links')}: "
    f"[Buchile GitHub]({GITHUB_PROFILE_URL}) · "
    f"[Base Edition]({BASIC_REPO_URL}) · "
    f"[Vanguard Beta]({VANGUARD_REPO_URL})"
)
with st.expander(tr("acknowledgements")):
    st.markdown(tr("acknowledgements_intro"))
    st.markdown(
        "- [Meta Segment Anything 2](https://github.com/facebookresearch/sam2)\n"
        "- [frinkleko/AutoHajimiMosaic](https://github.com/frinkleko/AutoHajimiMosaic)\n"
        "- [spawner1145/auto-censor](https://github.com/spawner1145/auto-censor)\n"
        "- [Wenaka2004/auto-censor](https://github.com/Wenaka2004/auto-censor)\n"
        "- [Ultralytics](https://github.com/ultralytics/ultralytics)"
    )

hardware = device_summary()
with st.sidebar:
    st.header(tr("settings"))
    st.subheader(tr("refinement"))
    refine_mode = st.radio(
        tr("refine_mode"),
        ["original", "auto", "interactive"],
        index=1,
        format_func=lambda value: tr(f"refine_{value}"),
        help=tr("refine_help"),
    )
    runtime_choice = st.radio(
        tr("runtime"),
        ["auto", "gpu", "cpu"],
        horizontal=True,
        format_func=lambda value: tr(f"runtime_{value}"),
    )
    try:
        device = resolve_device(runtime_choice)
    except RuntimeError:
        st.error(tr("gpu_unavailable"))
        st.stop()
    if device.startswith("cuda"):
        st.success(
            tr(
                "runtime_status_gpu",
                name=hardware.get("gpu_name", "NVIDIA GPU"),
                vram=hardware.get("vram_gb", "?"),
            )
        )
    else:
        st.info(tr("runtime_status_cpu"))
    default_variant = "base_plus" if device.startswith("cuda") else "tiny"
    sam_variant = st.selectbox(
        tr("sam_model"),
        list(SAM_VARIANTS),
        index=list(SAM_VARIANTS).index(default_variant),
        format_func=lambda value: tr(f"sam_{value}"),
        help=tr("sam_model_help"),
        disabled=refine_mode == "original",
    )

    st.divider()
    preset = st.selectbox(
        tr("preset"),
        list(PRESETS),
        index=0,
        format_func=lambda value: tr(f"preset_{value}"),
    )
    st.caption(tr("sidebar_parts_guide"))
    selected_parts = st.multiselect(
        tr("selected_parts"),
        options=PARTS,
        default=PRESETS[preset],
        key=f"parts_{language}_{preset}",
        format_func=part_label,
        help=tr("selected_parts_help"),
    )

    st.divider()
    output_format = st.radio(tr("output_format"), ["PNG", "JPEG"], horizontal=True)
    with st.expander(tr("model_license")):
        st.write(tr("model_description"))
        st.caption(tr("license_description"))


st.info(tr("initial_parts_guide"), icon="👈")
uploaded_files = st.file_uploader(
    tr("upload"),
    type=["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"],
    accept_multiple_files=True,
    help=tr("upload_help"),
)

st.radio(
    tr("language"),
    options=["zh", "en"],
    format_func=lambda value: "中文" if value == "zh" else "English",
    horizontal=True,
    key="language",
)

if not uploaded_files:
    st.divider()
    render_kitty_gift_game(KITTY_GALLERY_DIR, tr("gift_prompt"), tr("gift_reveal"))
    st.stop()

if not selected_parts:
    st.warning(tr("select_part_warning"))
    st.divider()
    render_kitty_gift_game(KITTY_GALLERY_DIR, tr("gift_prompt"), tr("gift_reveal"))
    st.stop()

pending_preview_index = st.session_state.pop("_pending_preview_index", None)
if pending_preview_index is not None:
    st.session_state["preview_index"] = max(
        0, min(len(uploaded_files) - 1, int(pending_preview_index))
    )
elif not 0 <= int(st.session_state.get("preview_index", 0)) < len(uploaded_files):
    st.session_state["preview_index"] = 0

preview_index = st.selectbox(
    tr("preview_file"),
    options=list(range(len(uploaded_files))),
    format_func=lambda index: f"{index + 1}. {uploaded_files[index].name}",
    key="preview_index",
)
current_file = uploaded_files[preview_index]
current_data = current_file.getvalue()
current_image = cached_decode(current_data)
current_image_id = upload_key(preview_index, current_file.name, current_data)

with st.expander(tr("detection_profiles"), expanded=True):
    st.caption(tr("detection_profiles_help"))
    detection_message = st.session_state.pop("detection_profile_message", None)
    if detection_message:
        st.success(detection_message)
    detection_source = effective_detection_profile(current_image_id)
    has_detection_override = current_image_id in detection_store()["images"]
    st.caption(
        tr("detection_profile_current")
        if has_detection_override
        else tr("detection_profile_global")
    )
    detection_revision = st.session_state.get("detection_editor_revision", 0)
    detection_key = f"{language}_{current_image_id}_{detection_revision}"
    draft_base_threshold = st.slider(
        tr("base_threshold"),
        min_value=0.15,
        max_value=0.80,
        value=float(detection_source["base_threshold"]),
        step=0.01,
        help=tr("base_threshold_help"),
        key=f"detection_base_{detection_key}",
    )
    draft_supplement_parts = tuple(
        st.multiselect(
            tr("supplement_parts"),
            options=PARTS,
            default=list(detection_source.get("supplement_parts", ())),
            format_func=part_label,
            help=tr("supplement_parts_help"),
            key=f"detection_parts_{detection_key}",
        )
    )
    draft_supplement_threshold = st.slider(
        tr("supplement_threshold"),
        min_value=0.03,
        max_value=0.35,
        value=float(detection_source["supplement_threshold"]),
        step=0.01,
        disabled=not draft_supplement_parts,
        key=f"detection_supplement_{detection_key}",
    )
    draft_image_size = st.slider(
        tr("accuracy"),
        min_value=320,
        max_value=1920,
        value=int(detection_source["image_size"]),
        step=32,
        help=tr("accuracy_help"),
        key=f"detection_size_{detection_key}",
    )
    st.caption(tr("detection_apply_hint"))
    draft_detection_profile = {
        "base_threshold": float(draft_base_threshold),
        "supplement_parts": draft_supplement_parts,
        "supplement_threshold": float(draft_supplement_threshold),
        "image_size": int(draft_image_size),
    }
    detection_current_column, detection_all_column = st.columns(2)
    with detection_current_column:
        apply_detection_current = st.button(
            tr("apply_current"),
            key="detection_apply_current",
            use_container_width=True,
        )
    with detection_all_column:
        apply_detection_all = st.button(
            tr("apply_all_images"),
            key="detection_apply_all",
            type="primary",
            use_container_width=True,
        )
    if apply_detection_current:
        detection_store()["images"][current_image_id] = dict(draft_detection_profile)
        st.session_state["detection_editor_revision"] = detection_revision + 1
        st.session_state["detection_profile_message"] = tr("detection_applied_current")
        st.session_state.pop("batch_result", None)
        st.rerun()
    if apply_detection_all:
        store = detection_store()
        store["global"] = dict(draft_detection_profile)
        store["images"].clear()
        st.session_state["detection_editor_revision"] = detection_revision + 1
        st.session_state["detection_profile_message"] = tr("detection_applied_all")
        st.session_state.pop("batch_result", None)
        st.rerun()

with st.expander(tr("mosaic_profiles"), expanded=True):
    st.caption(tr("mosaic_profiles_help"))
    saved_message = st.session_state.pop("mosaic_profile_message", None)
    if saved_message:
        st.success(saved_message)
    current_profiles = effective_mosaic_profiles(current_image_id)
    current_overrides = mosaic_store()["images"].get(current_image_id, {})
    st.caption(tr("independent_count", count=len(current_overrides)))
    profile_target = st.selectbox(
        tr("profile_target"),
        ["all", *PARTS],
        format_func=lambda value: tr("profile_all_parts") if value == "all" else part_label(value),
    )
    target_parts = PARTS if profile_target == "all" else [profile_target]
    source_profile = current_profiles[target_parts[0]]
    editor_revision = st.session_state.get("mosaic_editor_revision", 0)
    editor_key = f"{language}_{current_image_id}_{profile_target}_{editor_revision}"
    profile_mode = st.radio(
        tr("mode"),
        ["pixel", "sticker"],
        index=0 if source_profile["mode"] == "pixel" else 1,
        horizontal=True,
        format_func=lambda value: tr(f"mode_{value}"),
        key=f"profile_mode_{editor_key}",
    )
    profile_block_size = int(source_profile["block_size"])
    if profile_mode == "pixel":
        profile_block_size = st.slider(
            tr("block_size"),
            min_value=2,
            max_value=64,
            value=int(source_profile["block_size"]),
            step=1,
            key=f"profile_block_{editor_key}",
        )
    profile_feather = int(source_profile["feather"])
    if profile_mode == "pixel":
        profile_feather = st.slider(
            tr("feather"),
            min_value=0,
            max_value=5,
            value=int(source_profile["feather"]),
            help=tr("feather_help"),
            key=f"profile_feather_{editor_key}",
        )
    profile_sticker_file = None
    profile_sticker_source = source_profile.get(
        "sticker_source", "custom" if source_profile.get("sticker_bytes") else "dagou"
    )
    if profile_mode == "sticker":
        sticker_sources = ["dagou", "maodie", "custom"]
        profile_sticker_source = st.selectbox(
            tr("sticker_source"),
            sticker_sources,
            index=sticker_sources.index(profile_sticker_source),
            format_func=lambda value: tr(f"sticker_{value}"),
            key=f"profile_sticker_source_{editor_key}",
        )
        if profile_sticker_source == "custom":
            if source_profile.get("sticker_bytes"):
                st.caption(tr("saved_sticker"))
            profile_sticker_file = st.file_uploader(
                tr("custom_sticker"),
                type=["png", "jpg", "jpeg", "webp"],
                help=tr("custom_sticker_help"),
                key=f"profile_sticker_{editor_key}",
            )
    st.caption(tr("profile_apply_hint"))
    draft_sticker_bytes = None
    if profile_mode == "sticker" and profile_sticker_source == "custom":
        draft_sticker_bytes = (
            profile_sticker_file.getvalue()
            if profile_sticker_file is not None
            else source_profile.get("sticker_bytes")
        )
    draft_profile = {
        "mode": profile_mode,
        "block_size": int(profile_block_size),
        "feather": int(profile_feather),
        "sticker_source": profile_sticker_source,
        "sticker_bytes": draft_sticker_bytes,
    }
    current_column, all_column = st.columns(2)
    with current_column:
        apply_current = st.button(tr("apply_current"), use_container_width=True)
    with all_column:
        apply_all = st.button(tr("apply_all_images"), type="primary", use_container_width=True)
    target_name = tr("profile_all_parts") if profile_target == "all" else part_label(profile_target)
    if apply_current:
        image_profiles = mosaic_store()["images"].setdefault(current_image_id, {})
        for part in target_parts:
            image_profiles[part] = dict(draft_profile)
        st.session_state["mosaic_editor_revision"] = editor_revision + 1
        st.session_state["mosaic_profile_message"] = tr("applied_current", target=target_name)
        st.session_state.pop("batch_result", None)
        st.rerun()
    if apply_all:
        store = mosaic_store()
        for part in target_parts:
            store["global"][part] = dict(draft_profile)
            for image_profiles in store["images"].values():
                image_profiles.pop(part, None)
        st.session_state["mosaic_editor_revision"] = editor_revision + 1
        st.session_state["mosaic_profile_message"] = tr("applied_all", target=target_name)
        st.session_state.pop("batch_result", None)
        st.rerun()

detection_settings = {
    **effective_detection_profile(current_image_id),
    "device": device,
}

with st.spinner(tr("detecting")):
    detections = run_detection(current_data, **detection_settings)

candidate_detections = detections_for_parts(detections, selected_parts)
label_to_id = {region_label(index, item): item.uid for index, item in enumerate(candidate_detections)}
region_labels = list(label_to_id)
current_selection_key = region_selection_key(
    current_image_id, selected_parts, detection_settings
)
saved_selected_ids = effective_selected_ids(
    region_selection_store(),
    current_selection_key,
    (item.uid for item in candidate_detections),
)
default_region_labels = [
    label for label, uid in label_to_id.items() if uid in saved_selected_ids
]
region_widget_key = f"regions_{language}_{current_selection_key}"
selected_region_labels = st.multiselect(
    tr("select_regions"),
    options=region_labels,
    default=default_region_labels,
    key=region_widget_key,
    help=tr("select_regions_help"),
    on_change=sync_region_selection,
    args=(current_selection_key, region_widget_key, label_to_id),
)
selected_ids = {label_to_id[label] for label in selected_region_labels}
selected_detections = [item for item in candidate_detections if item.uid in selected_ids]

current_refine_mode = effective_refine_mode(current_image_id, refine_mode)
interactive_points = (
    points_for_image(current_data, selected_detections)
    if current_refine_mode == "interactive"
    else {}
)

diagnostics = []
if current_refine_mode == "original" or not selected_detections:
    output_detections = selected_detections
else:
    with st.spinner(tr("refining")):
        output_detections, diagnostics = run_refinement(
            current_data,
            tuple(item.uid for item in selected_detections),
            sam_variant,
            device,
            points_as_tuple(interactive_points),
            selected_detections,
        )

processed_preview = apply_profiled_censor(
    current_image,
    output_detections,
    effective_mosaic_profiles(current_image_id),
)

st.session_state.setdefault("region_numbers_visible", True)
st.session_state["show_region_numbers"] = st.session_state["region_numbers_visible"]
show_region_numbers = st.toggle(
    tr("show_region_numbers"),
    help=tr("show_region_numbers_help"),
    key="show_region_numbers",
    on_change=sync_region_number_visibility,
)
display_original = (
    draw_detection_markers(current_image, candidate_detections)
    if show_region_numbers
    else current_image
)
display_preview = (
    draw_detection_markers(processed_preview, candidate_detections)
    if show_region_numbers
    else processed_preview
)

left, right = st.columns(2, gap="medium")
with left:
    st.image(display_original, caption=tr("original"), use_container_width=True)
with right:
    preview_action = render_preview_navigator(
        display_preview,
        caption=tr("preview"),
        previous_label=tr("previous_image"),
        next_label=tr("next_image"),
        can_previous=preview_index > 0,
        can_next=preview_index < len(uploaded_files) - 1,
        position=preview_index + 1,
        total=len(uploaded_files),
        key="vanguard_preview_navigator",
    )

if preview_action:
    offset = -1 if preview_action == "previous" else 1
    st.session_state["_pending_preview_index"] = max(
        0, min(len(uploaded_files) - 1, preview_index + offset)
    )
    st.rerun()

previous_column, position_column, next_column = st.columns([1, 1.2, 1])
with previous_column:
    st.button(
        f"← {tr('previous_image')}",
        disabled=preview_index == 0,
        on_click=move_preview,
        args=(-1, len(uploaded_files)),
        key="preview_previous_button",
        use_container_width=True,
    )
with position_column:
    st.markdown(
        f"<p style='text-align:center;margin:.45rem 0 0;color:#8b91a1'>"
        f"{tr('preview_position', current=preview_index + 1, total=len(uploaded_files))}</p>",
        unsafe_allow_html=True,
    )
with next_column:
    st.button(
        f"{tr('next_image')} →",
        disabled=preview_index == len(uploaded_files) - 1,
        on_click=move_preview,
        args=(1, len(uploaded_files)),
        key="preview_next_button",
        use_container_width=True,
    )

refine_entry_clicked = render_refine_entry(
    prefix=tr("interactive_refine_prefix"),
    label=tr("interactive_refine_word"),
    suffix=tr("interactive_refine_suffix"),
    active=current_refine_mode == "interactive",
    active_hint=tr("interactive_refine_entry_hint"),
    key=f"interactive_refine_entry_{current_image_id}",
)
if refine_entry_clicked:
    enable_interactive_refinement(current_image_id)
    st.rerun()

if current_refine_mode == "interactive":
    st.caption(tr("interactive_refine_active"))
    st.subheader(tr("interaction_title"))
if current_refine_mode == "interactive" and not candidate_detections:
    st.warning(tr("interactive_no_detection"), icon="🧭")
elif current_refine_mode == "interactive" and not selected_detections:
    st.warning(tr("interactive_no_selection"), icon="🧭")
elif current_refine_mode == "interactive":
    target_uid = st.selectbox(
        tr("interaction_target"),
        options=[item.uid for item in selected_detections],
        format_func=lambda uid: next(
            region_label(index, item)
            for index, item in enumerate(candidate_detections)
            if item.uid == uid
        ),
        key=f"interaction_target_{current_image_id}",
    )
    target = next(item for item in selected_detections if item.uid == target_uid)
    point_kind = st.radio(
        tr("point_type"),
        [1, 0],
        horizontal=True,
        format_func=lambda value: tr("positive") if value == 1 else tr("negative"),
        key=f"interaction_point_type_{current_image_id}",
    )
    store = st.session_state.setdefault("sam_interactive_points", {})
    store_key = f"{file_key(current_data)}:{target_uid}"
    current_points = list(store.get(store_key, []))
    st.caption(tr("interaction_help"))
    overlay = draw_interaction_overlay(current_image, target, current_points)
    display_width = min(900, int(current_image.shape[1]))
    coordinates = streamlit_image_coordinates(
        Image.fromarray(overlay),
        width=display_width,
        key=f"sam_click_{store_key}_{len(current_points)}",
    )
    if coordinates:
        scale = current_image.shape[1] / display_width
        new_point = (
            float(np.clip(coordinates["x"] * scale, 0, current_image.shape[1] - 1)),
            float(np.clip(coordinates["y"] * scale, 0, current_image.shape[0] - 1)),
            int(point_kind),
        )
        store[store_key] = current_points + [new_point]
        st.session_state.pop("batch_result", None)
        st.rerun()
    undo_column, clear_column = st.columns(2)
    with undo_column:
        if st.button(
            tr("undo"),
            disabled=not current_points,
            key=f"interaction_undo_{store_key}",
            use_container_width=True,
        ):
            store[store_key] = current_points[:-1]
            st.session_state.pop("batch_result", None)
            st.rerun()
    with clear_column:
        if st.button(
            tr("clear"),
            disabled=not current_points,
            key=f"interaction_clear_{store_key}",
            use_container_width=True,
        ):
            store.pop(store_key, None)
            st.session_state.pop("batch_result", None)
            st.rerun()
    st.caption(tr("point_count", count=len(current_points)))

if not candidate_detections and current_refine_mode != "interactive":
    st.warning(tr("no_detection"))
if diagnostics:
    with st.expander(tr("diagnostics")):
        for index, item in enumerate(diagnostics, 1):
            st.write(
                tr(
                    "diagnostic_line",
                    index=index,
                    score=item.sam_score,
                    iou=item.coarse_iou,
                    points=item.prompt_count,
                    fallback=tr("fallback") if item.used_fallback else "",
                )
            )

extension = "jpg" if output_format == "JPEG" else "png"
preview_bytes = encode_image(processed_preview, output_format)
st.download_button(
    tr("download_preview"),
    data=preview_bytes,
    file_name=f"{safe_stem(current_file.name)}_censored.{extension}",
    mime=f"image/{'jpeg' if output_format == 'JPEG' else 'png'}",
    use_container_width=True,
)

st.divider()
st.subheader(tr("batch_title"))
st.caption(tr("batch_caption"))

batch_signature = hashlib.sha1(
    repr(
        (
            [(item.name, len(item.getvalue())) for item in uploaded_files],
            selected_parts,
            detection_state_signature(),
            region_selection_signature(region_selection_store()),
            output_format,
            refine_mode,
            refinement_state_signature(),
            sam_variant,
            repr(st.session_state.get("sam_interactive_points", {})),
            mosaic_state_signature(),
        )
    ).encode("utf-8")
).hexdigest()

if st.button(tr("process_all"), type="primary", use_container_width=True):
    zip_bytes, batch_warnings = build_zip(
        uploaded_files,
        selected_parts,
        output_format,
        refine_mode,
        sam_variant,
        device,
    )
    st.session_state["batch_result"] = (batch_signature, zip_bytes, batch_warnings)

batch_result = st.session_state.get("batch_result")
if batch_result and batch_result[0] == batch_signature:
    _, zip_bytes, batch_warnings = batch_result
    st.download_button(
        tr("download_all"),
        data=zip_bytes,
        file_name="buchile_vanguard_beta_results.zip",
        mime="application/zip",
        use_container_width=True,
    )
    if batch_warnings:
        with st.expander(f"{tr('batch_messages')} ({len(batch_warnings)})"):
            for warning in batch_warnings:
                st.write(f"- {warning}")

st.divider()
render_kitty_gift_game(KITTY_GALLERY_DIR, tr("gift_prompt"), tr("gift_reveal"))
