from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO


PART_LABELS = {
    "anus": "肛门",
    "fluids": "体液",
    "male_genital": "男性生殖器",
    "breasts": "胸部",
    "female_genital": "女性生殖器",
}

MODEL_SPECS = {
    "hachimi": {
        "filename": "hachimi_segmentation.pt",
        "label": "Hachimi",
        "classes": {
            "breast": "breasts",
            "anus": "anus",
            "female_genital": "female_genital",
            "male_genital": "male_genital",
        },
    },
    "maodie": {
        "filename": "maodie_segmentation.pt",
        "label": "Maodie",
        "classes": {
            "anus": "anus",
            "cum": "fluids",
            "dick": "male_genital",
            "tits": "breasts",
            "vagina": "female_genital",
        },
    },
}


@dataclass
class Detection:
    uid: str
    part: str
    confidence: float
    source: str
    mask: np.ndarray
    bbox: tuple[int, int, int, int]

    @property
    def label(self) -> str:
        return PART_LABELS[self.part]


def load_segmentation_models(model_dir: Path) -> dict[str, YOLO]:
    models: dict[str, YOLO] = {}
    for key, spec in MODEL_SPECS.items():
        model_path = model_dir / str(spec["filename"])
        if not model_path.exists():
            raise FileNotFoundError(f"缺少模型：{model_path}")
        models[key] = YOLO(str(model_path))
    return models


def decode_image(data: bytes) -> np.ndarray:
    with Image.open(BytesIO(data)) as image:
        image = image.convert("RGB")
        return np.asarray(image).copy()


def encode_image(image: np.ndarray, image_format: str = "PNG") -> bytes:
    output = BytesIO()
    Image.fromarray(image.astype(np.uint8), mode="RGB").save(
        output,
        format=image_format.upper(),
        quality=95,
        optimize=True,
    )
    return output.getvalue()


def decode_sticker(data: bytes | None, default_path: Path) -> np.ndarray:
    if data is None:
        image = Image.open(default_path)
    else:
        image = Image.open(BytesIO(data))
    with image:
        return np.asarray(image.convert("RGBA")).copy()


def _model_class_name(model: YOLO, class_id: int) -> str:
    names = model.names
    if isinstance(names, dict):
        return str(names[class_id])
    return str(names[class_id])


def _resize_mask(mask: np.ndarray, height: int, width: int) -> np.ndarray:
    if mask.shape != (height, width):
        mask = cv2.resize(mask, (width, height), interpolation=cv2.INTER_LINEAR)
    return mask


def _split_and_refine_mask(
    mask: np.ndarray,
    min_area: int,
) -> list[np.ndarray]:
    binary = (mask >= 0.5).astype(np.uint8)
    if not np.any(binary):
        return []

    # A tiny close operation removes one-pixel holes but retains the predicted contour.
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
    )
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    components: list[np.ndarray] = []
    for index in range(1, count):
        if int(stats[index, cv2.CC_STAT_AREA]) < min_area:
            continue
        components.append((labels == index).astype(np.uint8))
    return components


def _mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return 0, 0, 0, 0
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _mask_iou(first: np.ndarray, second: np.ndarray) -> float:
    intersection = np.logical_and(first > 0, second > 0).sum()
    if intersection == 0:
        return 0.0
    union = np.logical_or(first > 0, second > 0).sum()
    return float(intersection / max(union, 1))


def _deduplicate(detections: list[Detection], iou_threshold: float = 0.62) -> list[Detection]:
    kept: list[Detection] = []
    for candidate in sorted(detections, key=lambda item: item.confidence, reverse=True):
        duplicate = any(
            candidate.part == existing.part
            and _mask_iou(candidate.mask, existing.mask) >= iou_threshold
            for existing in kept
        )
        if not duplicate:
            kept.append(candidate)
    kept.sort(key=lambda item: (list(PART_LABELS).index(item.part), item.bbox[1], item.bbox[0]))
    for index, item in enumerate(kept):
        item.uid = f"{item.part}:{index}:{item.source}:{item.bbox[0]}:{item.bbox[1]}"
    return kept


def detect_regions(
    image_rgb: np.ndarray,
    models: dict[str, YOLO],
    base_threshold: float = 0.35,
    supplement_parts: Iterable[str] = (),
    supplement_threshold: float = 0.12,
    image_size: int = 960,
    device: str | int | None = None,
) -> list[Detection]:
    height, width = image_rgb.shape[:2]
    min_area = max(12, int(height * width * 0.00002))
    supplement_set = set(supplement_parts)
    run_threshold = min(base_threshold, supplement_threshold) if supplement_set else base_threshold
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    detections: list[Detection] = []

    for source, model in models.items():
        spec = MODEL_SPECS[source]
        results = model.predict(
            source=image_bgr,
            conf=float(run_threshold),
            iou=0.5,
            imgsz=int(image_size),
            retina_masks=True,
            agnostic_nms=True,
            verbose=False,
            device=device,
        )
        result = results[0]
        if result.masks is None or result.boxes is None:
            continue

        masks = result.masks.data.detach().cpu().numpy()
        classes = result.boxes.cls.detach().cpu().numpy().astype(int)
        scores = result.boxes.conf.detach().cpu().numpy().astype(float)
        for raw_mask, class_id, score in zip(masks, classes, scores):
            raw_name = _model_class_name(model, int(class_id))
            part = spec["classes"].get(raw_name)
            if part is None:
                continue
            accepted = score >= base_threshold or (
                part in supplement_set and score >= supplement_threshold
            )
            if not accepted:
                continue
            resized = _resize_mask(raw_mask, height, width)
            for component_index, component in enumerate(_split_and_refine_mask(resized, min_area)):
                bbox = _mask_bbox(component)
                detections.append(
                    Detection(
                        uid=f"{source}:{part}:{len(detections)}:{component_index}",
                        part=part,
                        confidence=float(score),
                        source=str(spec["label"]),
                        mask=component,
                        bbox=bbox,
                    )
                )

    return _deduplicate(detections)


def _pixelated_crop(crop: np.ndarray, block_size: int) -> np.ndarray:
    height, width = crop.shape[:2]
    block_size = max(2, int(block_size))
    small_width = max(1, int(np.ceil(width / block_size)))
    small_height = max(1, int(np.ceil(height / block_size)))
    small = cv2.resize(crop, (small_width, small_height), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)


def _sticker_effect(crop: np.ndarray, sticker_rgba: np.ndarray) -> np.ndarray:
    height, width = crop.shape[:2]
    sticker = cv2.resize(sticker_rgba, (width, height), interpolation=cv2.INTER_AREA)
    sticker_rgb = sticker[:, :, :3].astype(np.float32)
    sticker_alpha = sticker[:, :, 3:4].astype(np.float32) / 255.0
    visible = sticker_alpha[:, :, 0] > 0.02
    if np.any(visible):
        background = np.median(sticker_rgb[visible], axis=0).reshape(1, 1, 3)
    else:
        background = np.full((1, 1, 3), 32.0, dtype=np.float32)
    # Build an opaque sticker canvas. Transparent margins use a color sampled from
    # the sticker itself, so sticker mode never exposes the original or pixel mosaic.
    return np.clip(
        sticker_rgb * sticker_alpha + background * (1.0 - sticker_alpha),
        0,
        255,
    ).astype(np.uint8)


def _inside_only_alpha(mask_crop: np.ndarray, feather: int) -> np.ndarray:
    binary = (mask_crop > 0).astype(np.float32)
    if feather <= 0:
        return binary[:, :, None]
    kernel = int(feather) * 2 + 1
    softened = cv2.GaussianBlur(binary, (kernel, kernel), 0)
    # Never paint outside the segmentation contour.
    return np.minimum(softened, binary)[:, :, None]


def apply_censor(
    image_rgb: np.ndarray,
    detections: Iterable[Detection],
    selected_ids: set[str] | None,
    mode: str,
    block_size: int,
    sticker_rgba: np.ndarray | None = None,
    feather: int = 1,
) -> np.ndarray:
    output = image_rgb.copy()
    for detection in detections:
        if selected_ids is not None and detection.uid not in selected_ids:
            continue
        x1, y1, x2, y2 = detection.bbox
        if x2 <= x1 or y2 <= y1:
            continue
        crop = output[y1:y2, x1:x2]
        mask_crop = detection.mask[y1:y2, x1:x2]
        sticker_mode = mode == "sticker" and sticker_rgba is not None
        if sticker_mode:
            effect = _sticker_effect(crop, sticker_rgba)
        else:
            effect = _pixelated_crop(crop, block_size)
        alpha = _inside_only_alpha(mask_crop, 0 if sticker_mode else feather)
        blended = effect.astype(np.float32) * alpha + crop.astype(np.float32) * (1.0 - alpha)
        output[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)
    return output


def detections_for_parts(detections: Iterable[Detection], selected_parts: Iterable[str]) -> list[Detection]:
    selected = set(selected_parts)
    return [item for item in detections if item.part in selected]


def draw_detection_markers(
    image_rgb: np.ndarray,
    detections: Iterable[Detection],
) -> np.ndarray:
    output = image_rgb.copy()
    height, width = output.shape[:2]
    radius = int(np.clip(round(min(height, width) * 0.018), 11, 28))
    font_scale = max(0.45, radius / 20.0)
    thickness = max(1, round(radius / 9))
    for index, detection in enumerate(detections, 1):
        binary = (detection.mask > 0).astype(np.uint8)
        if binary.shape != (height, width):
            binary = cv2.resize(binary, (width, height), interpolation=cv2.INTER_NEAREST)
        distance = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        _, maximum, _, location = cv2.minMaxLoc(distance)
        if maximum <= 0:
            x1, y1, x2, y2 = detection.bbox
            location = ((x1 + x2) // 2, (y1 + y2) // 2)
        x = int(np.clip(location[0], radius + 2, max(radius + 2, width - radius - 3)))
        y = int(np.clip(location[1], radius + 2, max(radius + 2, height - radius - 3)))
        cv2.circle(output, (x, y), radius + 2, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(output, (x, y), radius, (220, 35, 45), -1, cv2.LINE_AA)
        text = str(index)
        (text_width, text_height), baseline = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )
        origin = (x - text_width // 2, y + (text_height - baseline) // 2)
        cv2.putText(
            output,
            text,
            origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA,
        )
    return output
