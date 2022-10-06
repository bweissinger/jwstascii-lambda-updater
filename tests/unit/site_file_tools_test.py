from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
from jinja2.environment import Template
from jinja2.exceptions import TemplateNotFound
from os import makedirs
from freezegun import freeze_time
from unittest.mock import patch, mock_open
from datetime import date

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


class TestGenerateFromTemplate(TestCase):
    def create_template(self, tempdir):
        self.template_path = Path(tempdir, "template.html")
        with open(self.template_path, "w") as file:
            file.write("<p>my template</p><span>{{var_1}}</span><div>{{var_2}}</div>")

    def test_vars_unpacked_correctly(self):
        with TemporaryDirectory() as tempdir:
            output_path = Path(tempdir, "output.html")
            self.create_template(tempdir)
            site_file_tools.generate_from_template(
                self.template_path, output_path, {"var_1": "a", "var_2": "b"}
            )

            with open(output_path, "r") as generated:
                expected = "<p>my template</p><span>a</span><div>b</div>"
                self.assertEqual(generated.read(), expected)

    def test_too_few_vars(self):
        with TemporaryDirectory() as tempdir:
            output_path = Path(tempdir, "output.html")
            self.create_template(tempdir)
            site_file_tools.generate_from_template(
                self.template_path, output_path, {"var_1": "a"}
            )
            with open(output_path, "r") as generated:
                expected = "<p>my template</p><span>a</span><div></div>"
                self.assertEqual(generated.read(), expected)

    def test_too_many_vars(self):
        with TemporaryDirectory() as tempdir:
            output_path = Path(tempdir, "output.html")
            self.create_template(tempdir)
            site_file_tools.generate_from_template(
                self.template_path,
                output_path,
                {"var_1": "a", "var_2": "b", "var_3": "c"},
            )
            with open(output_path, "r") as generated:
                expected = "<p>my template</p><span>a</span><div>b</div>"
                self.assertEqual(generated.read(), expected)

    def test_undefined_var(self):
        with TemporaryDirectory() as tempdir:
            output_path = Path(tempdir, "output.html")
            self.create_template(tempdir)
            site_file_tools.generate_from_template(
                self.template_path, output_path, {"var_1": "a", "var_3": "b"}
            )
            with open(output_path, "r") as generated:
                expected = "<p>my template</p><span>a</span><div></div>"
                self.assertEqual(generated.read(), expected)


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


@freeze_time("2000-01-01")
@patch("jwstascii_helpers.site_file_tools.write_file")
@patch("builtins.open", new_callable=mock_open, read_data="")
class TestUpdatePriorPage(TestCase):
    link_html = '<li id="tomorrow_link"><a href="a">b</a></li>'
    stylesheet_html = '<link href="/styles/main.css" rel="stylesheet"/>'

    def test_link_not_found(self, mocked_open, write_file):
        self.assertRaises(
            RuntimeError,
            site_file_tools.update_prior_page,
            Path(""),
            Path("outpath.html"),
            date.today(),
        )

    def test_stylesheet_not_found(self, mocked_open, write_file):
        self.assertRaises(
            RuntimeError,
            site_file_tools.update_prior_page,
            Path(""),
            Path("outpath.html"),
            date.today(),
        )

    @patch("jwstascii_helpers.site_file_tools.BeautifulSoup")
    def test_prettify_called(self, bs, mocked_open, write_file):
        open().read.return_value = self.stylesheet_html + self.link_html
        site_file_tools.update_prior_page(Path("file_path"), Path(""), date.today())
        bs().prettify.assert_called_once()

    def test_properly_updated(self, mocked_open, write_file):
        open().read.return_value = self.stylesheet_html + self.link_html
        site_file_tools.update_prior_page(
            Path("file_path"), Path("new_file_path"), date.today()
        )
        write_file.assert_called_once_with(
            Path("file_path"),
            '<html>\n <head>\n  <link href="/styles/main.css" rel="stylesheet"/>\n </head>\n <body>\n  <li id="tomorrow_link">\n   <a href="new_file_path">\n    01|01|00\n   </a>\n  </li>\n </body>\n</html>',
        )
