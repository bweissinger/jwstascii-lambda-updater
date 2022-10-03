from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path

from jwstascii_helpers.ascii_conversion import convert_image


class TestConvertImage(TestCase):
    def assertImageEqual(self, image_path, other_image_path):
        with open(image_path, "rb") as output:
            with open(other_image_path, "rb") as expected:
                self.assertEqual(output.read(), expected.read())

    def test_image_generation(self):
        with TemporaryDirectory() as tempdir:
            test_image_dir = Path("tests/resources/images")
            image_path = Path(test_image_dir, "test_image.png")
            a_path = Path(tempdir, "a.png")
            b_path = Path(tempdir, "b.png")
            convert_image(image_path, 50, a_path)
            convert_image(image_path, 25, b_path)

            self.assertImageEqual(a_path, Path(test_image_dir, "test_ascii.png"))
            self.assertImageEqual(b_path, Path(test_image_dir, "test_ascii_small.png"))
