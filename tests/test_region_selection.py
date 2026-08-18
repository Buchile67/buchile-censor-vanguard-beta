import unittest

from region_selection import (
    effective_selected_ids,
    region_selection_key,
    region_selection_signature,
    save_selected_ids,
)


class RegionSelectionTest(unittest.TestCase):
    def test_key_is_stable_and_scoped_to_image_and_detection_profile(self) -> None:
        first = region_selection_key(
            "image-one",
            ("breasts", "anus"),
            {"image_size": 960, "base_threshold": 0.35, "device": "cpu"},
        )
        same = region_selection_key(
            "image-one",
            ("breasts", "anus"),
            {"device": "cpu", "base_threshold": 0.35, "image_size": 960},
        )
        other = region_selection_key(
            "image-two",
            ("breasts", "anus"),
            {"image_size": 960, "base_threshold": 0.35, "device": "cpu"},
        )
        self.assertEqual(first, same)
        self.assertNotEqual(first, other)

    def test_saved_selection_survives_switching_images(self) -> None:
        store = {}
        first_key = region_selection_key("first", ("breasts",), {"image_size": 960})
        second_key = region_selection_key("second", ("breasts",), {"image_size": 960})

        save_selected_ids(store, first_key, ("region-1", "region-3"))

        self.assertEqual(
            effective_selected_ids(store, second_key, ("region-4", "region-5")),
            {"region-4", "region-5"},
        )
        self.assertEqual(
            effective_selected_ids(store, first_key, ("region-1", "region-2", "region-3")),
            {"region-1", "region-3"},
        )

    def test_empty_selection_is_distinct_from_missing_selection(self) -> None:
        store = {}
        key = region_selection_key("first", ("breasts",), {"image_size": 960})
        self.assertEqual(effective_selected_ids(store, key, ("a", "b")), {"a", "b"})

        save_selected_ids(store, key, ())
        self.assertEqual(effective_selected_ids(store, key, ("a", "b")), set())
        self.assertEqual(region_selection_signature(store), ((key, ()),))

    def test_stale_ids_are_not_applied_to_new_detection_results(self) -> None:
        store = {}
        key = region_selection_key("first", ("breasts",), {"image_size": 960})
        save_selected_ids(store, key, ("old", "kept"))
        self.assertEqual(effective_selected_ids(store, key, ("kept", "new")), {"kept"})


if __name__ == "__main__":
    unittest.main()
