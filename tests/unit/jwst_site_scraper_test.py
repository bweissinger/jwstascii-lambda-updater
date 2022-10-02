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


class TestGetImageCredits(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        return super().setUp()

    def test_empty_string(self):
        self.assertRaises(ValueError, self.scraper.get_image_credits, "")

    def test_no_footer(self):
        html = """<strong>Credits:</strong><p>IMAGE: NASA, ESA, CSA, STScI</p>"""
        self.assertRaises(ValueError, self.scraper.get_image_credits, html)

    def test_no_image_prefix(self):
        html = (
            """<footer><strong>Credits:</strong><p>NASA, ESA, CSA, STScI</p></footer>"""
        )
        self.assertRaises(ValueError, self.scraper.get_image_credits, html)

    def test_blank_credits(self):
        html = """<footer><strong>Credits:</strong><p>IMAGE: </p></footer>"""
        self.assertRaises(ValueError, self.scraper.get_image_credits, html)

    def test_valid_credits(self):
        html = """<footer><strong>Credits:</strong><p>IMAGE: NASA, ESA, CSA, STScI</p></footer>"""
        self.assertEqual(
            self.scraper.get_image_credits(html), ["NASA", "ESA", "CSA", "STScI"]
        )

    def test_lowercase_image_prefix(self):
        html = """<footer><strong>Credits:</strong><p>image: NASA, ESA, CSA, STScI</p></footer>"""
        self.assertEqual(
            self.scraper.get_image_credits(html), ["NASA", "ESA", "CSA", "STScI"]
        )

    def test_single_credit(self):
        html = """<footer><strong>Credits:</strong><p>image: NASA</p></footer>"""
        self.assertEqual(self.scraper.get_image_credits(html), ["NASA"])

    def test_only_parses_credit_in_footer(self):
        html = """<p>image: NOT, CORRECT, CREDITS</p><footer><strong>Credits:</strong><p>image: NASA, ESA, CSA, STScI</p></footer>"""
        self.assertEqual(
            self.scraper.get_image_credits(html), ["NASA", "ESA", "CSA", "STScI"]
        )
