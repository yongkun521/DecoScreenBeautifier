import math
import unittest

import numpy as np

from processors.image import ImageProcessor


def _make_test_image(height: int = 6, width: int = 8) -> np.ndarray:
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            img[y, x] = [(x * 31) % 255, (y * 41) % 255, ((x + y) * 23) % 255]
    return img


class ImageProcessorTest(unittest.TestCase):
    def test_ascii_mode_keeps_requested_dimensions(self) -> None:
        processor = ImageProcessor()
        result = processor.process_array(
            _make_test_image(),
            width=8,
            height=4,
            render_mode="ascii",
            display_mode="stretch",
        )

        lines = result.plain.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertTrue(all(len(line) == 8 for line in lines))

    def test_pixel_mode_collapses_two_rows_into_one_character_row(self) -> None:
        processor = ImageProcessor()
        result = processor.process_array(
            _make_test_image(height=8, width=6),
            width=6,
            height=8,
            render_mode="pixel",
        )

        lines = result.plain.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertTrue(all(len(line) == 6 for line in lines))
        self.assertEqual(set("".join(lines)), {"▀"})

    def test_pixel_mode_handles_odd_height_without_overflow(self) -> None:
        processor = ImageProcessor()
        result = processor.process_array(
            _make_test_image(height=7, width=5),
            width=5,
            height=5,
            render_mode="pixel",
        )

        lines = result.plain.splitlines()
        self.assertEqual(len(lines), math.ceil(5 / 2))
        self.assertTrue(all(0 < len(line) <= 5 for line in lines))

    def test_display_modes_and_sample_scale_do_not_change_output_footprint(self) -> None:
        processor = ImageProcessor()

        for display_mode in ("fit", "fill", "stretch"):
            for sample_scale in (0.5, 1.0, 2.0):
                result = processor.process_array(
                    _make_test_image(height=10, width=16),
                    width=9,
                    height=4,
                    render_mode="ascii",
                    display_mode=display_mode,
                    sample_scale=sample_scale,
                )
                lines = result.plain.splitlines()
                self.assertTrue(0 < len(lines) <= 4)
                self.assertTrue(all(0 < len(line) <= 9 for line in lines))
                if display_mode == "stretch":
                    self.assertEqual(len(lines), 4)
                    self.assertTrue(all(len(line) == 9 for line in lines))
