from pathlib import Path
import hashlib
import unittest

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


class PreviewStateTest(unittest.TestCase):
    def test_navigation_refinement_memory_and_region_number_toggle(self) -> None:
        files = [
            ("dagou.png", (ROOT / "assets" / "dagou.png").read_bytes(), "image/png"),
            ("maodie.png", (ROOT / "assets" / "maodie.png").read_bytes(), "image/png"),
        ]
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=180)
        self.assertTrue(
            any("第一步：请先在左侧选择部位预设" in item.value for item in app.info)
        )
        app.file_uploader[0].set_value(files).run(timeout=300)
        self.assertFalse(app.exception)

        first_identity = b"0:dagou.png:" + files[0][1]
        first_image_id = hashlib.sha1(first_identity).hexdigest()[:20]
        app.session_state["image_refinement_modes"] = {first_image_id: "interactive"}
        app.run(timeout=300)
        self.assertEqual(
            app.session_state["image_refinement_modes"][first_image_id], "interactive"
        )
        self.assertTrue(
            any(item.value == "交互式轮廓修正" for item in app.subheader)
        )
        self.assertTrue(
            any("当前所选部位没有可精修的检测区域" in item.value for item in app.warning)
        )
        self.assertFalse(
            any("对当前图片进行交互式精修" in item.label for item in app.button)
        )

        next(item for item in app.button if item.key == "preview_next_button").click().run(
            timeout=300
        )
        self.assertEqual(app.session_state["preview_index"], 1)

        next(
            item for item in app.button if item.key == "preview_previous_button"
        ).click().run(timeout=300)
        self.assertEqual(app.session_state["preview_index"], 0)
        self.assertEqual(
            app.session_state["image_refinement_modes"][first_image_id], "interactive"
        )
        self.assertTrue(
            any(item.value == "交互式轮廓修正" for item in app.subheader)
        )

        next(item for item in app.toggle if item.key == "show_region_numbers").set_value(
            False
        ).run(timeout=300)
        next(
            item for item in app.button if item.key == "detection_apply_current"
        ).click().run(timeout=300)
        self.assertFalse(
            next(item for item in app.toggle if item.key == "show_region_numbers").value
        )


if __name__ == "__main__":
    unittest.main()
