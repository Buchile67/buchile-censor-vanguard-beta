from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


_COMPONENT = components.declare_component(
    "buchile_refine_entry",
    path=str(Path(__file__).resolve().parent / "components" / "refine_entry"),
)


def render_refine_entry(
    *,
    prefix: str,
    label: str,
    suffix: str,
    active: bool,
    active_hint: str,
    key: str,
) -> bool:
    """Render the red animated text as the interactive-refinement entry point."""
    result = _COMPONENT(
        prefix=prefix,
        label=label,
        suffix=suffix,
        active=active,
        active_hint=active_hint,
        default=None,
        key=key,
    )
    if not isinstance(result, dict) or result.get("action") != "open":
        return False
    nonce = result.get("nonce")
    if not nonce:
        return False
    state_key = f"_refine_entry_nonce:{key}"
    if st.session_state.get(state_key) == nonce:
        return False
    st.session_state[state_key] = nonce
    return True
