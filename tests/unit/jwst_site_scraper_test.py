from unittest import TestCase
from jwstascii_helpers.jwst_site_scraper import Scraper


class TestGetImageDescription(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        return super().setUp()

    def test_no_header(self):
        self.assertRaises(
            ValueError, self.scraper.get_image_description, "No header here."
        )

    def test_empty_string(self):
        self.assertRaises(ValueError, self.scraper.get_image_description, "")

    def test_correctly_parsed_html(self):
        html = """<h4>About This Image</h4><p>Some text<a href="some_url" target="_self">href_text</a> continued description.</p>
                <p>This is another paragraph</p>
                <div><button>some button</button><p>Include Me!</p></div>
                <footer>Footer stuff here</footer>"""

        expected = """<p>Some text<a href="some_url" target="_self">href_text</a> continued description.</p><p>This is another paragraph</p><p>Include Me!</p>"""

        self.assertEqual(self.scraper.get_image_description(html), expected)

    def test_no_footer(self):
        html = """<h4>About This Image</h4><p>Some text<a href="some_url" target="_self">href_text</a> continued description.</p>"""
        self.assertRaises(ValueError, self.scraper.get_image_description, html)
