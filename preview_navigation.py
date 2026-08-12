from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image


_COMPONENT = components.declare_component(
    "buchile_preview_navigator",
    path=str(Path(__file__).resolve().parent / "components" / "preview_navigator"),
)


def _preview_data_url(image: np.ndarray, max_width: int = 1200) -> str:
    preview = Image.fromarray(np.asarray(image, dtype=np.uint8), mode="RGB")
    if preview.width > max_width:
        height = max(1, round(preview.height * max_width / preview.width))
        preview = preview.resize((max_width, height), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    preview.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_preview_navigator(
    image: np.ndarray,
    *,
    caption: str,
    previous_label: str,
    next_label: str,
    can_previous: bool,
    can_next: bool,
    position: int,
    total: int,
    key: str,
) -> str | None:
    """Render a preview whose left/right halves navigate between uploaded images."""
    result = _COMPONENT(
        image_data_url=_preview_data_url(image),
        caption=caption,
        previous_label=previous_label,
        next_label=next_label,
        can_previous=can_previous,
        can_next=can_next,
        position=position,
        total=total,
        default=None,
        key=key,
    )
    if not isinstance(result, dict):
        return None
    nonce = result.get("nonce")
    action = result.get("action")
    if not nonce or action not in {"previous", "next"}:
        return None
    state_key = f"_preview_navigation_nonce:{key}"
    if st.session_state.get(state_key) == nonce:
        return None
    st.session_state[state_key] = nonce
    return action
