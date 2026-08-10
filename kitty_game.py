from __future__ import annotations

import base64
import html
import random
from pathlib import Path

import streamlit as st


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@st.cache_data(show_spinner=False)
def _image_data_uri(path_value: str, modified_ns: int) -> str:
    del modified_ns
    path = Path(path_value)
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(path.suffix.lower(), "image/png")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_kitty_gift_game(gallery_dir: Path, prompt: str, reveal_text: str) -> None:
    images = sorted(
        path
        for path in gallery_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ) if gallery_dir.is_dir() else []
    if not images:
        return

    selected = random.SystemRandom().choice(images)
    image_uri = _image_data_uri(str(selected), selected.stat().st_mtime_ns)
    safe_prompt = html.escape(prompt)
    safe_reveal = html.escape(reveal_text)
    colors = ("#ff5577", "#ffd84d", "#57d9ff", "#9b73ff", "#62e6a7", "#ff8f45")
    confetti = "".join(
        f'<i style="--x:{(index * 29) % 100}%;--r:{(index * 47) % 360}deg;'
        f'--delay:{(index % 9) * 0.07}s;--duration:{1.8 + (index % 5) * 0.17}s;'
        f'--color:{colors[index % len(colors)]}"></i>'
        for index in range(42)
    )
    sparkles = "".join(
        f'<b style="--sx:{8 + (index * 19) % 84}%;--sy:{8 + (index * 31) % 78}%;'
        f'--delay:{(index % 6) * 0.16}s">✦</b>'
        for index in range(14)
    )

    document = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; background: transparent; color-scheme: dark; }}
        body {{ font-family: Inter, "Segoe UI", "Microsoft YaHei", sans-serif; overflow: hidden; }}
        .card {{
          position: relative; width: 100%; height: 630px; overflow: hidden;
          display: flex; align-items: center; justify-content: center;
          border: 1px solid rgba(255,255,255,.14); border-radius: 18px;
          background:
            radial-gradient(circle at 20% 15%, rgba(255,89,143,.17), transparent 28%),
            radial-gradient(circle at 84% 82%, rgba(92,200,255,.15), transparent 30%),
            linear-gradient(145deg, #151721, #0f1118 72%);
        }}
        .gift-trigger {{
          appearance: none; border: 0; background: transparent; color: #fff;
          display: flex; align-items: center; justify-content: center; gap: 34px;
          padding: 28px; cursor: pointer; width: min(820px, 92%);
          transition: opacity .25s ease, transform .25s ease;
        }}
        .gift-trigger:focus-visible {{ outline: 3px solid #72d8ff; outline-offset: 8px; border-radius: 18px; }}
        .gift-art {{ position: relative; width: 156px; height: 150px; flex: 0 0 156px; animation: giftShake 2.1s ease-in-out infinite; }}
        .gift-box {{
          position: absolute; left: 17px; bottom: 2px; width: 122px; height: 104px;
          border-radius: 8px 8px 14px 14px; background: linear-gradient(135deg, #ff5577, #dc2856);
          box-shadow: 0 18px 36px rgba(255,49,103,.28), inset 0 -8px 0 rgba(110,0,35,.16);
        }}
        .gift-box::before {{ content: ""; position: absolute; left: 51px; top: 0; width: 20px; height: 100%; background: #ffd84d; }}
        .gift-lid {{
          position: absolute; z-index: 3; left: 8px; top: 37px; width: 140px; height: 30px;
          border-radius: 8px; background: linear-gradient(#ff7691, #ef3b67);
          box-shadow: 0 8px 12px rgba(0,0,0,.25); transform-origin: 72% 100%;
        }}
        .gift-lid::before {{ content: ""; position: absolute; left: 59px; top: 0; width: 22px; height: 30px; background: #ffe16a; }}
        .bow-left, .bow-right {{
          position: absolute; z-index: 4; top: 5px; width: 59px; height: 43px;
          border: 12px solid #ffd84d; border-radius: 50% 50% 12% 50%;
        }}
        .bow-left {{ left: 22px; transform: rotate(19deg); }}
        .bow-right {{ right: 22px; transform: scaleX(-1) rotate(19deg); }}
        .prompt {{ max-width: 520px; text-align: left; font-size: clamp(23px, 3vw, 38px); font-weight: 800; line-height: 1.25; text-shadow: 0 3px 20px rgba(0,0,0,.45); }}
        .prompt small {{ display: block; margin-top: 13px; color: #ffc5d5; font-size: 15px; font-weight: 600; letter-spacing: .04em; }}
        .result {{
          position: absolute; inset: 18px; display: flex; flex-direction: column;
          align-items: center; justify-content: center; gap: 14px;
          opacity: 0; transform: translateY(85px) scale(.35); pointer-events: none;
        }}
        .photo {{
          position: relative; z-index: 4; max-width: min(90%, 620px); max-height: 490px;
          padding: 9px; border-radius: 18px; background: linear-gradient(135deg, #fff, #ffd8e5 46%, #bfefff);
          box-shadow: 0 22px 70px rgba(0,0,0,.55), 0 0 34px rgba(255,222,94,.28);
        }}
        .photo img {{ display: block; max-width: 100%; max-height: 465px; border-radius: 11px; object-fit: contain; }}
        .reveal-text {{ position: relative; z-index: 5; color: #fff; font-size: clamp(20px, 2.7vw, 31px); font-weight: 850; text-align: center; text-shadow: 0 3px 18px #000; }}
        .confetti, .sparkles {{ position: absolute; inset: 0; pointer-events: none; z-index: 7; }}
        .confetti i {{
          display: none; position: absolute; left: var(--x); top: -24px; width: 10px; height: 20px;
          border-radius: 3px; background: var(--color); transform: rotate(var(--r));
        }}
        .sparkles b {{
          display: none; position: absolute; left: var(--sx); top: var(--sy); color: #fff4a9;
          font-size: 28px; filter: drop-shadow(0 0 8px #fff) drop-shadow(0 0 15px #ffd84d);
        }}
        .opening .gift-art {{ animation: none; }}
        .opening .gift-lid {{ animation: lidOpen .62s cubic-bezier(.2,.9,.25,1) forwards; }}
        .opening .gift-box {{ animation: boxBounce .62s ease forwards; }}
        .revealed .gift-trigger {{ opacity: 0; transform: scale(.7); pointer-events: none; }}
        .revealed .result {{ opacity: 1; transform: translateY(0) scale(1); transition: opacity .45s ease, transform .68s cubic-bezier(.16,1.25,.3,1); }}
        .revealed .confetti i {{ display: block; animation: confettiFall var(--duration) cubic-bezier(.12,.55,.35,1) var(--delay) both; }}
        .revealed .sparkles b {{ display: block; animation: sparkle 1.25s ease-in-out var(--delay) infinite; }}
        @keyframes giftShake {{ 0%, 78%, 100% {{ transform: rotate(0); }} 82% {{ transform: rotate(-3deg); }} 86% {{ transform: rotate(3deg); }} 90% {{ transform: rotate(-2deg); }} 94% {{ transform: rotate(2deg); }} }}
        @keyframes lidOpen {{ 0% {{ transform: translate(0,0) rotate(0); }} 58% {{ transform: translate(-9px,-70px) rotate(-19deg); }} 100% {{ transform: translate(72px,-112px) rotate(31deg); opacity: 0; }} }}
        @keyframes boxBounce {{ 0%,100% {{ transform: scale(1); }} 48% {{ transform: scale(.92,1.08); }} 72% {{ transform: scale(1.05,.94); }} }}
        @keyframes confettiFall {{ 0% {{ opacity: 1; transform: translateY(-20px) rotate(var(--r)); }} 100% {{ opacity: .1; transform: translateY(650px) rotate(760deg); }} }}
        @keyframes sparkle {{ 0%,100% {{ opacity: .12; transform: scale(.25) rotate(0); }} 45% {{ opacity: 1; transform: scale(1.35) rotate(45deg); }} }}
        @media (max-width: 640px) {{
          .gift-trigger {{ flex-direction: column; gap: 18px; }}
          .prompt {{ text-align: center; font-size: 25px; }}
          .card {{ height: 630px; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
          .gift-art, .opening .gift-lid, .opening .gift-box, .revealed .confetti i, .revealed .sparkles b {{ animation-duration: .01ms !important; animation-iteration-count: 1 !important; }}
        }}
      </style>
    </head>
    <body>
      <section class="card" id="kitty-card">
        <button class="gift-trigger" type="button" onclick="openKittyGift()" aria-label="{safe_prompt}">
          <span class="gift-art" aria-hidden="true">
            <span class="bow-left"></span><span class="bow-right"></span>
            <span class="gift-lid"></span><span class="gift-box"></span>
          </span>
          <span class="prompt">{safe_prompt}<small>CLICK / 点击礼盒</small></span>
        </button>
        <div class="result" aria-live="polite">
          <div class="photo"><img src="{image_uri}" alt="Random kitty gift"></div>
          <div class="reveal-text">{safe_reveal}</div>
        </div>
        <div class="confetti" aria-hidden="true">{confetti}</div>
        <div class="sparkles" aria-hidden="true">{sparkles}</div>
      </section>
      <script>
        let opened = false;
        function openKittyGift() {{
          if (opened) return;
          opened = true;
          const card = document.getElementById('kitty-card');
          card.classList.add('opening');
          window.setTimeout(() => card.classList.add('revealed'), 520);
        }}
      </script>
    </body>
    </html>
    """
    st.iframe(document, height=650)
