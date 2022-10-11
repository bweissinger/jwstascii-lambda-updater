from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
from bs4 import BeautifulSoup
from jinja2 import Environment, BaseLoader
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
            self.assertRaises(
                TemplateNotFound,
                site_file_tools.get_jinja_template,
                "not_a_template",
            )

    def test_returns_jinja_template(self):
        self.assertIsInstance(
            site_file_tools.get_jinja_template("main_index.html"), Template
        )


@patch("jwstascii_helpers.site_file_tools.write_file")
@patch("jwstascii_helpers.site_file_tools.get_jinja_template")
class TestGenerateFromTemplate(TestCase):
    def setUp(self) -> None:
        self.template_html = (
            "<p>my template</p><span>{{var_1}}</span><div>{{var_2}}</div>"
        )
        return super().setUp()

    def generate_template(self, template_str):
        return Environment(loader=BaseLoader).from_string(template_str)

    def test_get_jinja_template_call_correct(self, get_jinja_template, write_file):
        get_jinja_template.return_value = self.generate_template(self.template_html)
        output_path = Path("directory", "output.html")
        site_file_tools.generate_from_template(
            "test_template", output_path, {"var_1": "a", "var_2": "b"}
        )
        get_jinja_template.assert_called_with("test_template")

    def test_vars_unpacked_correctly(self, get_jinja_template, write_file):
        get_jinja_template.return_value = self.generate_template(self.template_html)
        output_path = Path("directory", "output.html")
        site_file_tools.generate_from_template(
            "test_template", output_path, {"var_1": "a", "var_2": "b"}
        )
        expected = "<p>my template</p><span>a</span><div>b</div>"
        write_file.assert_called_once_with(output_path, expected)

    def test_too_few_vars(self, get_jinja_template, write_file):
        get_jinja_template.return_value = self.generate_template(self.template_html)
        output_path = Path("directory", "output.html")
        site_file_tools.generate_from_template(
            "test_template", output_path, {"var_1": "a"}
        )
        expected = "<p>my template</p><span>a</span><div></div>"
        write_file.assert_called_once_with(output_path, expected)

    def test_too_many_vars(self, get_jinja_template, write_file):
        get_jinja_template.return_value = self.generate_template(self.template_html)
        output_path = Path("directory", "output.html")
        site_file_tools.generate_from_template(
            "test_template",
            output_path,
            {"var_1": "a", "var_2": "b", "var_3": "c"},
        )
        expected = "<p>my template</p><span>a</span><div>b</div>"
        write_file.assert_called_once_with(output_path, expected)

    def test_undefined_var(self, get_jinja_template, write_file):
        get_jinja_template.return_value = self.generate_template(self.template_html)
        output_path = Path("directory", "output.html")
        site_file_tools.generate_from_template(
            "test_template", output_path, {"var_1": "a", "var_3": "b"}
        )
        expected = "<p>my template</p><span>a</span><div></div>"
        write_file.assert_called_once_with(output_path, expected)


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
@patch("jwstascii_helpers.site_file_tools.soup_from_file")
class TestUpdatePriorPage(TestCase):
    def setUp(self) -> None:
        self.link_html = '<li id="tomorrow_link"><a href="a">b</a></li>'
        self.stylesheet_html = '<link href="/styles/main.css" rel="stylesheet"/>'
        return super().setUp()

    def test_correct_file_open(self, soup_from_file, write_file):
        soup_from_file.return_value = BeautifulSoup(
            self.stylesheet_html + self.link_html, "lxml"
        )
        file_path = Path("test/file/path.html")
        site_file_tools.update_prior_page(
            file_path,
            Path("outpath.html"),
            date.today(),
        )
        soup_from_file.assert_called_once_with(file_path)

    def test_link_not_found(self, soup_from_file, write_file):
        soup_from_file.return_value = BeautifulSoup(self.stylesheet_html, "lxml")
        self.assertRaises(
            RuntimeError,
            site_file_tools.update_prior_page,
            Path(""),
            Path("outpath.html"),
            date.today(),
        )

    def test_stylesheet_not_found(self, soup_from_file, write_file):
        soup_from_file.return_value = BeautifulSoup(self.link_html, "lxml")
        self.assertRaises(
            RuntimeError,
            site_file_tools.update_prior_page,
            Path(""),
            Path("outpath.html"),
            date.today(),
        )

    def test_properly_updated(self, soup_from_file, write_file):
        soup_from_file.return_value = BeautifulSoup(
            self.stylesheet_html + self.link_html, "lxml"
        )
        site_file_tools.update_prior_page(
            Path("file_path"), Path("new_file_path"), date.today()
        )
        write_file.assert_called_once_with(
            Path("file_path"),
            '<html>\n <head>\n  <link href="/styles/main.css" rel="stylesheet"/>\n </head>\n <body>\n  <li id="tomorrow_link">\n   <a href="new_file_path">\n    01|01|00\n   </a>\n  </li>\n </body>\n</html>',
        )


@patch("builtins.open", new_callable=mock_open, read_data="")
class TestSoupFromFile(TestCase):
    def test_file_not_found(self, mocked_open):
        mocked_open.side_effect = FileNotFoundError()
        self.assertRaises(
            FileNotFoundError, site_file_tools.soup_from_file, Path("file.path")
        )

    def test_soup_returned(self, mocked_open):
        open().read.return_value = "<p>test</p>"
        soup = site_file_tools.soup_from_file(Path("test.path"))
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertEqual(str(soup), "<html><body><p>test</p></body></html>")


@patch("jwstascii_helpers.site_file_tools.write_file")
@patch("jwstascii_helpers.site_file_tools.soup_from_file")
class TestAddLinkToArchiveList(TestCase):
    def setUp(self) -> None:
        self.html = """<html><body>
                <ol class="archive_list">
                <li><span>26 September 2022</span><a data-jwst_url="url_1.com" href="link 1">Second title</a></li>
                <li><span>25 September 2022</span><a data-jwst_url="url_2.com" href="link 2">Third image</a></li>
                </body></html>"""
        return super().setUp()

    def test_link_added(self, soup_from_file, write_file):
        soup_from_file.return_value = BeautifulSoup(self.html, "lxml")
        expected_html = """<html>\n <body>\n  <ol class="archive_list">\n   <li>\n    <span>\n     02 October 2022\n    </span>\n    <a data-jwst_url="some-url.com" href="path/to/page.html">\n     McTitle\n    </a>\n   </li>\n   <li>\n    <span>\n     26 September 2022\n    </span>\n    <a data-jwst_url="url_1.com" href="link 1">\n     Second title\n    </a>\n   </li>\n   <li>\n    <span>\n     25 September 2022\n    </span>\n    <a data-jwst_url="url_2.com" href="link 2">\n     Third image\n    </a>\n   </li>\n  </ol>\n </body>\n</html>"""

        site_file_tools.add_link_to_archive_list(
            "path/to/index.html",
            "path/to/page.html",
            date(2022, 10, 2),
            "McTitle",
            "some-url.com",
        )
        site_file_tools.write_file.assert_called_once_with(
            "path/to/index.html", expected_html
        )

    def test_soup_from_file_call(self, soup_from_file, write_file):
        soup_from_file.return_value = BeautifulSoup(self.html, "lxml")
        site_file_tools.add_link_to_archive_list(
            "path/to/index.html",
            "path/to/page.html",
            date(2022, 10, 2),
            "McTitle",
            "some-url.com",
        )
        site_file_tools.soup_from_file.assert_called_once_with("path/to/index.html")


@patch("jwstascii_helpers.site_file_tools.write_file")
@patch("jwstascii_helpers.site_file_tools.soup_from_file")
@patch("jwstascii_helpers.site_file_tools.generate_from_template")
class TestAddNewMonthToArchive(TestCase):
    def setUp(self) -> None:
        self.html = """<div>
            <h1>Archive</h1>
            <h1 id="daily-list-link"><a href="./daily_list">View Daily List</a></h1>
            <h2>2022</h2>
            <div class="grid-container">
                <div class="grid-item">
                    <a href="./2022/september">September</a>
                </div>
            </div>
        </div>"""
        self.path_to_template = Path("path/to/template")
        self.path_to_new_month_index = Path("path/to/new/month/index")
        self.path_to_archive_overview = Path("path/to/archive/overview")
        return super().setUp()

    def add_month_call_wrapper(self, year, month):
        site_file_tools.add_month_to_archive(
            self.path_to_template,
            self.path_to_new_month_index,
            self.path_to_archive_overview,
            year,
            month,
        )

    def test_template_generation_call(
        self, generate_from_template, soup_from_file, write_file
    ):
        soup_from_file.return_value = BeautifulSoup(self.html, "lxml")
        self.add_month_call_wrapper("2022", "December")
        template_args = {
            "main_archive_html_path": self.path_to_archive_overview,
            "month_and_year": "December 2022",
        }
        generate_from_template.assert_called_once_with(
            self.path_to_template, self.path_to_new_month_index, template_args
        )

    def test_month_in_new_year(
        self, generate_from_template, soup_from_file, write_file
    ):
        soup_from_file.return_value = BeautifulSoup(self.html, "lxml")
        output_html = """<div>
            <h1>Archive</h1>
            <h1 id="daily-list-link"><a href="./daily_list">View Daily List</a></h1>
            <h2>2023</h2>
            <div class="grid-container">
                <div class="grid-item">
                    <a href="path/to/new/month/index">October</a>
                </div>
            </div>
            <h2>2022</h2>
            <div class="grid-container">
                <div class="grid-item">
                    <a href="./2022/september">September</a>
                </div>
            </div>
        </div>"""
        self.add_month_call_wrapper("2023", "October")
        write_file.assert_any_call(
            self.path_to_archive_overview, BeautifulSoup(output_html, "lxml").prettify()
        )

    def test_month_in_existing_year(
        self, generate_from_template, soup_from_file, write_file
    ):
        soup_from_file.return_value = BeautifulSoup(self.html, "lxml")
        output_html = """<div>
            <h1>Archive</h1>
            <h1 id="daily-list-link"><a href="./daily_list">View Daily List</a></h1>
            <h2>2022</h2>
            <div class="grid-container">
                <div class="grid-item">
                    <a href="path/to/new/month/index">December</a>
                </div>
                <div class="grid-item">
                    <a href="./2022/september">September</a>
                </div>
            </div>
        </div>"""
        self.add_month_call_wrapper("2022", "December")
        write_file.assert_called_with(
            self.path_to_archive_overview, BeautifulSoup(output_html, "lxml").prettify()
        )

    def test_month_already_present(
        self, generate_from_template, soup_from_file, write_file
    ):
        soup_from_file.return_value = BeautifulSoup(self.html, "lxml")
        self.add_month_call_wrapper("2022", "September")
        generate_from_template.assert_not_called()
        write_file.assert_not_called()


@patch("jwstascii_helpers.site_file_tools.write_file")
@patch("jwstascii_helpers.site_file_tools.soup_from_file")
@patch("jwstascii_helpers.site_file_tools.add_link_to_archive_list")
@patch("jwstascii_helpers.site_file_tools.add_month_to_archive")
class TestAddLinksToArchive(TestCase):
    def setUp(self) -> None:
        self.template_dir = Path("template", "dir")
        self.archive_path = Path("archive", "path")
        self.path_to_new_page = Path("path", "to", "new", "page")
        self.page_date = date(2022, 10, 1)
        self.image_title = "This is a test image"
        self.default_html = """<h1>Archive</h1>
            <h1><a href="/archive">Return to Overview</a></h1>
            <h2>September 2022</h2>
            <ol class="archive_list">
                <li>
                    <span>26</span><a href="path 1">Image description 1</a>
                </li>
                <li>
                    <span>25</span><a href="path 2">Image description 2</a>
                </li>
            </ol>"""
        self.default_soup = BeautifulSoup(self.default_html, "lxml")
        return super().setUp()

    def test_add_month_to_archive_call_correct(
        self, add_month_to_archive, add_link_to_archive, soup_from_file, write_file
    ):
        soup_from_file.side_effect = [FileNotFoundError(), self.default_soup]
        site_file_tools.update_archive(
            self.template_dir,
            self.archive_path,
            self.path_to_new_page,
            self.page_date,
            self.image_title,
        )
        add_month_to_archive.assert_called_with(
            Path(self.template_dir, "archive_month.html"),
            Path(self.archive_path, "2022", "october", "index.html"),
            Path(self.archive_path, "index.html"),
            "2022",
            "october",
        )

    def test_add_link_to_archive_list_call_correct(
        self, add_month_to_archive, add_link_to_archive, soup_from_file, write_file
    ):
        soup_from_file.return_value = self.default_soup
        site_file_tools.update_archive(
            self.template_dir,
            self.archive_path,
            self.path_to_new_page,
            self.page_date,
            self.image_title,
        )
        add_link_to_archive.assert_called_with(
            Path(self.archive_path, "daily_list", "index.html"),
            Path(self.path_to_new_page),
            self.page_date,
            self.image_title,
        )

    def test_modified_correctly(
        self, add_month_to_archive, add_link_to_archive, soup_from_file, write_file
    ):
        self.page_date = date(2022, 9, 30)
        soup_from_file.return_value = self.default_soup
        site_file_tools.update_archive(
            self.template_dir,
            self.archive_path,
            self.path_to_new_page,
            self.page_date,
            self.image_title,
        )
        expected = BeautifulSoup(
            """<h1>Archive</h1>
            <h1><a href="/archive">Return to Overview</a></h1>
            <h2>September 2022</h2>
            <ol class="archive_list">
                <li>
                    <span>30</span><a href="path/to/new/page">This is a test image</a>
                </li>
                <li>
                    <span>26</span><a href="path 1">Image description 1</a>
                </li>
                <li>
                    <span>25</span><a href="path 2">Image description 2</a>
                </li>
            </ol>""",
            "lxml",
        )
        write_file.assert_called_with(
            Path(self.archive_path, "2022", "september", "index.html"),
            expected.prettify(),
        )

    def test_modified_correctly_new_month(
        self, add_month_to_archive, add_link_to_archive, soup_from_file, write_file
    ):
        new_soup = BeautifulSoup(
            """<h1>Archive</h1>
            <h1><a href="/archive">Return to Overview</a></h1>
            <h2>October 2022</h2>
            <ol class="archive_list">
            </ol>""",
            "lxml",
        )
        soup_from_file.side_effect = [FileNotFoundError(), new_soup]
        site_file_tools.update_archive(
            self.template_dir,
            self.archive_path,
            self.path_to_new_page,
            self.page_date,
            self.image_title,
        )
        expected = BeautifulSoup(
            """<h1>Archive</h1>
            <h1><a href="/archive">Return to Overview</a></h1>
            <h2>October 2022</h2>
            <ol class="archive_list">
                <li>
                    <span>01</span><a href="path/to/new/page">This is a test image</a>
                </li>
            </ol>""",
            "lxml",
        )
        write_file.assert_called_with(
            Path(self.archive_path, "2022", "october", "index.html"),
            expected.prettify(),
        )


@patch("jwstascii_helpers.site_file_tools.soup_from_file")
class TestGetLinksFromArchiveList(TestCase):
    def test_link_retrieval(self, soup_from_file):
        html = """<h1>Archive List</h1>
            <h1><a href="/archive">Return to Overview</a></h1>
            <ol class="archive_list">
                <li>
                    <span>26 September 2022</span>
                    <a data-jwst_url="jwst_url_1.com" href="Path/1">Image Title 1</a>
                </li>
                <li>
                    <span>25 September 2022</span>
                    <a data-jwst_url="jwst_url_2.com" href="Path/2">Image Title 2</a>
                </li>
                <li>
                    <span>24 September 2022</span>
                    <a data-jwst_url="jwst_url_3.com" href="Path/3">Image Title 3</a>
                </li>
            </ol>"""
        soup_from_file.return_value = BeautifulSoup(html, "lxml")
        links = site_file_tools.get_links_from_archive_list(Path("path/to/archive"))
        self.assertEqual(links, ["jwst_url_1.com", "jwst_url_2.com", "jwst_url_3.com"])


@patch("jwstascii_helpers.site_file_tools.soup_from_file")
class TestGetDateOfCurrentPage(TestCase):
    def setUp(self) -> None:
        self.html = """<meta charset="utf-8"><meta http-equiv="refresh" content="0; URL=%s" />"""
        return super().setUp()

    def test_archive_file_opened(self, soup_from_file):
        soup_from_file.return_value = BeautifulSoup(
            self.html % "/2022/october/01", "lxml"
        )
        site_file_tools.get_date_of_current_page(Path("archive/path"))
        soup_from_file.assert_called_with(Path("archive/path"))

    def test_correct_date(self, soup_from_file):
        soup_from_file.return_value = BeautifulSoup(
            self.html % "/2022/october/01", "lxml"
        )
        return_date = site_file_tools.get_date_of_current_page(Path("archive/path"))
        self.assertEqual(return_date, date(2022, 10, 1))

    def test_mangled_date(self, soup_from_file):
        soup_from_file.return_value = BeautifulSoup(self.html % "/2022/10/01", "lxml")
        self.assertRaises(
            ValueError, site_file_tools.get_date_of_current_page, Path("archive/path")
        )
