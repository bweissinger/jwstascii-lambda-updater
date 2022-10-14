from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
from os.path import exists
from os import makedirs

from jwstascii_helpers.ascii_conversion import convert_image


class TestConvertImage(TestCase):
    charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ "

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
            convert_image(image_path, 50, self.charset, a_path)
            convert_image(image_path, 25, self.charset, b_path)

            self.assertImageEqual(a_path, Path(test_image_dir, "test_ascii.png"))
            self.assertImageEqual(b_path, Path(test_image_dir, "test_ascii_small.png"))

    def test_image_path_does_not_exist(self):
        with TemporaryDirectory() as tempdir:
            incorrect_path = Path(tempdir, "image_does_not_exist.png")
            self.assertRaises(
                FileNotFoundError,
                convert_image,
                incorrect_path,
                200,
                self.charset,
                Path(tempdir, "out.png"),
            )

    def test_creates_directory_if_not_exists(self):
        with TemporaryDirectory() as tempdir:
            test_image_path = "tests/resources/images/test_image.png"
            out_path = Path(tempdir, "new_dir/image.png")
            convert_image(test_image_path, 20, self.charset, out_path)
            self.assertTrue(exists(out_path))

    def test_directory_not_overwritten(self):
        with TemporaryDirectory() as tempdir:
            test_file_a = Path(tempdir, "test.txt")
            test_file_b = Path(tempdir, "new_dir/test_file_b")
            makedirs(test_file_a)
            makedirs(test_file_b)

            test_image_path = "tests/resources/images/test_image.png"
            out_path = Path(tempdir, "new_dir/image.png")
            convert_image(test_image_path, 20, self.charset, out_path)

            self.assertTrue(exists(test_file_a))
            self.assertTrue(exists(test_file_b))
