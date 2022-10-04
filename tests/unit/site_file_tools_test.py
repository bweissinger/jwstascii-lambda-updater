from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
from jinja2.environment import Template
from jinja2.exceptions import TemplateNotFound

from jwstascii_helpers import site_file_tools


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
