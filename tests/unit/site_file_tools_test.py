from distutils.file_util import write_file
from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
from jinja2.environment import Template
from jinja2.exceptions import TemplateNotFound
from os import makedirs

from jwstascii_helpers import site_file_tools

TEMPLATE_DIR = Path("layer/jwstascii_helpers/templates")
RESOURCES_DIR = Path("tests/resources")


class TestGetJinjaTemplate(TestCase):
    def test_fails_on_bad_template_path(self):
        with TemporaryDirectory() as tempdir:
            path = Path(tempdir, "not_exists.tpl")
            self.assertRaises(
                TemplateNotFound,
                site_file_tools.get_jinja_template,
                path,
            )

    def test_returns_jinja_template(self):
        with TemporaryDirectory() as tempdir:
            template_path = Path(tempdir, "template.tpl")
            with open(template_path, "w") as file:
                file.write("<p>{{var}}</p>")
            self.assertIsInstance(
                site_file_tools.get_jinja_template(template_path), Template
            )


class TestGenerateMainIndex(TestCase):
    def test_generated_correctly(self):
        with TemporaryDirectory() as tempdir:
            output_path = Path(tempdir, "output.html")
            site_file_tools.generate_main_index(
                TEMPLATE_DIR, output_path, "my title", "a/b/c"
            )

            with open(Path(output_path), "r") as generated:
                path_of_expected = Path(
                    RESOURCES_DIR, "html", "main_index_generation.html"
                )
                with open(path_of_expected, "r") as expected:
                    self.assertEqual(generated.read(), expected.read())


class TestWriteFile(TestCase):
    def test_file_written_in_new_directory(self):
        with TemporaryDirectory() as tempdir:
            output_path = Path(tempdir, "new_dir", "my_file.txt")
            site_file_tools.write_file(output_path, "contents")

            with open(output_path, "r") as file:
                self.assertEqual(file.read(), "contents")

    def test_directory_not_overwritten(self):
        with TemporaryDirectory() as tempdir:
            output_path = Path(tempdir, "new_dir", "do_not_erase.txt")
            site_file_tools.write_file(output_path, "contents")

            other_path = Path(tempdir, "new_dir/newer_dir", "file.txt")
            site_file_tools.write_file(other_path, "b")

            with open(output_path, "r") as file:
                self.assertEqual(file.read(), "contents")

    def test_handles_parent_dir_existing(self):
        with TemporaryDirectory() as tempdir:
            makedirs(Path(tempdir, "new_dir"))
            output_path = Path(tempdir, "new_dir", "my_file.txt")
            site_file_tools.write_file(output_path, "contents")

            with open(output_path, "r") as file:
                self.assertEqual(file.read(), "contents")
