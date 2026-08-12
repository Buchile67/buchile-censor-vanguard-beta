from pathlib import Path
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
        app.file_uploader[0].set_value(files).run(timeout=300)
        self.assertFalse(app.exception)

        first_button = next(
            item
            for item in app.button
            if item.key and item.key.startswith("enable_interactive_")
        )
        first_image_id = first_button.key.removeprefix("enable_interactive_")
        first_button.click().run(timeout=300)
        self.assertEqual(
            app.session_state["image_refinement_modes"][first_image_id], "interactive"
        )

        next(item for item in app.button if item.key == "preview_next_button").click().run(
            timeout=300
        )
        second_button = next(
            item
            for item in app.button
            if item.key and item.key.startswith("enable_interactive_")
        )
        self.assertNotEqual(second_button.key, first_button.key)
        self.assertFalse(second_button.disabled)

        next(
            item for item in app.button if item.key == "preview_previous_button"
        ).click().run(timeout=300)
        restored_button = next(
            item
            for item in app.button
            if item.key == f"enable_interactive_{first_image_id}"
        )
        self.assertTrue(restored_button.disabled)

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
