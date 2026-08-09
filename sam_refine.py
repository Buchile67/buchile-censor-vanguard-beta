from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Iterable

import cv2
import numpy as np
import torch

from core import Detection


SAM_VARIANTS = {
    "tiny": {
        "label": "SAM 2.1 Hiera Tiny",
        "config": "configs/sam2.1/sam2.1_hiera_t.yaml",
        "checkpoint": "sam2.1_hiera_tiny.pt",
    },
    "base_plus": {
        "label": "SAM 2.1 Hiera Base Plus",
        "config": "configs/sam2.1/sam2.1_hiera_b+.yaml",
        "checkpoint": "sam2.1_hiera_base_plus.pt",
    },
}


@dataclass
class SAMBundle:
    predictor: object
    device: str
    variant: str
    lock: Lock


@dataclass
class RefinementInfo:
    uid: str
    used_fallback: bool
    sam_score: float
    coarse_iou: float
    prompt_count: int


def build_sam_bundle(checkpoint_dir: Path, variant: str, device: str) -> SAMBundle:
    if variant not in SAM_VARIANTS:
        raise ValueError(f"Unknown SAM 2 variant: {variant}")
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    spec = SAM_VARIANTS[variant]
    checkpoint = checkpoint_dir / str(spec["checkpoint"])
    if not checkpoint.exists():
        raise FileNotFoundError(f"Missing SAM 2 checkpoint: {checkpoint}")
    model = build_sam2(
        str(spec["config"]),
        str(checkpoint),
        device=device,
        apply_postprocessing=True,
    )
    return SAMBundle(
        predictor=SAM2ImagePredictor(model),
        device=device,
        variant=variant,
        lock=Lock(),
    )


@contextmanager
def inference_context(device: str):
    with torch.inference_mode():
        if device.startswith("cuda"):
            with torch.autocast("cuda", dtype=torch.bfloat16):
                yield
        else:
            yield


def resolve_device(choice: str) -> str:
    cuda_ready = torch.cuda.is_available()
    if choice == "gpu":
        if not cuda_ready:
            raise RuntimeError("CUDA is not available in this environment.")
        return "cuda:0"
    if choice == "cpu":
        return "cpu"
    return "cuda:0" if cuda_ready else "cpu"


def device_summary() -> dict[str, object]:
    available = torch.cuda.is_available()
    result: dict[str, object] = {
        "cuda_available": available,
        "torch_version": torch.__version__,
        "torch_cuda": torch.version.cuda,
    }
    if available:
        result["gpu_name"] = torch.cuda.get_device_name(0)
        properties = torch.cuda.get_device_properties(0)
        result["vram_gb"] = round(properties.total_memory / (1024**3), 1)
    return result


def _mask_iou(first: np.ndarray, second: np.ndarray) -> float:
    first_bool = first > 0
    second_bool = second > 0
    union = np.logical_or(first_bool, second_bool).sum()
    if union == 0:
        return 0.0
    return float(np.logical_and(first_bool, second_bool).sum() / union)


def _mask_coverage(candidate: np.ndarray, coarse: np.ndarray) -> float:
    coarse_area = max(int((coarse > 0).sum()), 1)
    return float(np.logical_and(candidate > 0, coarse > 0).sum() / coarse_area)


def _auto_positive_points(mask: np.ndarray, count: int = 3) -> list[tuple[float, float, int]]:
    binary = (mask > 0).astype(np.uint8)
    if not np.any(binary):
        return []
    working = binary.copy()
    points: list[tuple[float, float, int]] = []
    height, width = binary.shape
    suppress_radius = max(8, int(np.sqrt(binary.sum()) * 0.18))
    for _ in range(count):
        distance = cv2.distanceTransform(working, cv2.DIST_L2, 5)
        _, maximum, _, location = cv2.minMaxLoc(distance)
        if maximum <= 0:
            break
        x, y = location
        points.append((float(x), float(y), 1))
        cv2.circle(working, (x, y), suppress_radius, 0, -1)
    return points


def _guard_mask(coarse: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    radius = max(5, int(max(x2 - x1, y2 - y1) * 0.08))
    radius = min(radius, 28)
    kernel_size = radius * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return cv2.dilate((coarse > 0).astype(np.uint8), kernel)


def _expanded_box(
    bbox: tuple[int, int, int, int],
    image_shape: tuple[int, int],
) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    height, width = image_shape
    pad = max(3, int(max(x2 - x1, y2 - y1) * 0.04))
    return np.asarray(
        [max(0, x1 - pad), max(0, y1 - pad), min(width - 1, x2 + pad), min(height - 1, y2 + pad)],
        dtype=np.float32,
    )


def refine_detection(
    predictor,
    detection: Detection,
    image_shape: tuple[int, int],
    interactive_points: Iterable[tuple[float, float, int]] = (),
) -> tuple[Detection, RefinementInfo]:
    coarse = (detection.mask > 0).astype(np.uint8)
    auto_points = _auto_positive_points(coarse)
    user_points = list(interactive_points)
    prompts = auto_points + user_points
    point_coords = np.asarray([[x, y] for x, y, _ in prompts], dtype=np.float32)
    point_labels = np.asarray([label for _, _, label in prompts], dtype=np.int32)
    box = _expanded_box(detection.bbox, image_shape)

    masks, scores, low_res = predictor.predict(
        point_coords=point_coords,
        point_labels=point_labels,
        box=box,
        multimask_output=True,
        return_logits=False,
    )
    guard = _guard_mask(coarse, detection.bbox)
    best_index = 0
    best_rank = -1e9
    best_iou = 0.0
    for index, mask in enumerate(masks):
        candidate = np.logical_and(mask > 0, guard > 0).astype(np.uint8)
        iou = _mask_iou(candidate, coarse)
        coverage = _mask_coverage(candidate, coarse)
        area_ratio = candidate.sum() / max(coarse.sum(), 1)
        area_penalty = abs(np.log(max(float(area_ratio), 1e-4)))
        rank = float(scores[index]) * 0.48 + iou * 0.34 + coverage * 0.22 - area_penalty * 0.08
        if rank > best_rank:
            best_rank = rank
            best_index = index
            best_iou = iou

    # A second pass uses the chosen low-resolution logits and all manual corrections.
    final_masks, final_scores, _ = predictor.predict(
        point_coords=point_coords,
        point_labels=point_labels,
        box=box,
        mask_input=low_res[best_index : best_index + 1],
        multimask_output=False,
        return_logits=False,
    )
    refined = np.logical_and(final_masks[0] > 0, guard > 0).astype(np.uint8)
    refined_iou = _mask_iou(refined, coarse)
    coverage = _mask_coverage(refined, coarse)
    fallback = refined_iou < 0.22 or coverage < 0.35 or refined.sum() < 12
    final_mask = coarse if fallback else refined

    ys, xs = np.where(final_mask > 0)
    bbox = detection.bbox
    if len(xs):
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    updated = Detection(
        uid=detection.uid,
        part=detection.part,
        confidence=detection.confidence,
        source=f"{detection.source}+SAM2",
        mask=final_mask,
        bbox=bbox,
    )
    info = RefinementInfo(
        uid=detection.uid,
        used_fallback=fallback,
        sam_score=float(final_scores[0]),
        coarse_iou=float(refined_iou if not fallback else best_iou),
        prompt_count=len(prompts),
    )
    return updated, info


def refine_detections(
    image_rgb: np.ndarray,
    detections: Iterable[Detection],
    bundle: SAMBundle,
    interactive_points: dict[str, list[tuple[float, float, int]]] | None = None,
) -> tuple[list[Detection], list[RefinementInfo]]:
    selected = list(detections)
    if not selected:
        return [], []
    points = interactive_points or {}
    refined: list[Detection] = []
    diagnostics: list[RefinementInfo] = []
    with bundle.lock, inference_context(bundle.device):
        bundle.predictor.set_image(image_rgb)
        for detection in selected:
            updated, info = refine_detection(
                bundle.predictor,
                detection,
                image_rgb.shape[:2],
                interactive_points=points.get(detection.uid, []),
            )
            refined.append(updated)
            diagnostics.append(info)
        bundle.predictor.reset_predictor()
    return refined, diagnostics


def draw_interaction_overlay(
    image_rgb: np.ndarray,
    detection: Detection,
    points: Iterable[tuple[float, float, int]],
) -> np.ndarray:
    overlay = image_rgb.copy()
    contours, _ = cv2.findContours(
        (detection.mask > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(overlay, contours, -1, (255, 210, 40), 3)
    for x, y, label in points:
        center = (int(round(x)), int(round(y)))
        color = (45, 210, 90) if label == 1 else (240, 65, 65)
        cv2.circle(overlay, center, 8, (255, 255, 255), -1)
        cv2.circle(overlay, center, 6, color, -1)
        if label == 0:
            cv2.line(overlay, (center[0] - 4, center[1] - 4), (center[0] + 4, center[1] + 4), (255, 255, 255), 2)
            cv2.line(overlay, (center[0] + 4, center[1] - 4), (center[0] - 4, center[1] + 4), (255, 255, 255), 2)
    return overlay
