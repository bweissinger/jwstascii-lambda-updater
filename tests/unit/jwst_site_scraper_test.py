import responses
from unittest import TestCase
from requests.exceptions import RetryError
from jwstascii_helpers.jwst_site_scraper import Scraper
from tempfile import TemporaryDirectory
from os import path
from unittest.mock import patch
from urllib3.exceptions import MaxRetryError


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
        self.assertEqual(
            self.scraper.get_image_credits(html),
            "<p>\n NASA, ESA, CSA, STScI\n</p>",
        )

    def test_blank_credits(self):
        html = """<footer><strong>Credits:</strong><p>IMAGE: </p></footer>"""
        self.assertEqual(
            self.scraper.get_image_credits(html),
            "<p>\n IMAGE:\n</p>",
        )

    def test_valid_credits(self):
        html = """<footer><strong>Credits:</strong><p>IMAGE: NASA, ESA, CSA, STScI</p></footer>"""
        self.assertEqual(
            self.scraper.get_image_credits(html),
            "<p>\n IMAGE: NASA, ESA, CSA, STScI\n</p>",
        )

    def test_lowercase_image_prefix(self):
        html = """<footer><strong>Credits:</strong><p>image: NASA, ESA, CSA, STScI</p></footer>"""
        self.assertEqual(
            self.scraper.get_image_credits(html),
            "<p>\n image: NASA, ESA, CSA, STScI\n</p>",
        )

    def test_single_credit(self):
        html = """<footer><strong>Credits:</strong><p>image: NASA</p></footer>"""
        self.assertEqual(
            self.scraper.get_image_credits(html), "<p>\n image: NASA\n</p>"
        )

    def test_only_parses_credit_in_footer(self):
        html = """<p>image: NOT, CORRECT, CREDITS</p><footer><strong>Credits:</strong><p>image: NASA, ESA, CSA, STScI</p></footer>"""
        self.assertEqual(
            self.scraper.get_image_credits(html),
            "<p>\n image: NASA, ESA, CSA, STScI\n</p>",
        )


class TestGetImageDownloadUrl(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        self.full_res_png_html = '<a href="//stsci-opo.org/STScI-01G8GYD8B1H306SSPR4MY6NGN0.png"class="link-icon-added">Full Res, 11264 X 3904, PNG (47.84&nbsp;MB)&nbsp;<span class="link-icon svg-sprite -image-file-icon"><svg role="img" aria-label="(image File)" focusable="false"><use xlink:href="#image-file-icon"></use></svg></span></a>'
        self.full_res_tif_html = '<a href="//stsci-opo.org/STScI-01G8GY7CZNNQH69BJG1ZGQ4D5B.tif" class="link-icon-added">Full Res, 11264 X 3904, TIF (55.33&nbsp;MB)&nbsp;<span class="link-icon svg-sprite -image-file-icon"><svg role="img" aria-label="(image File)" focusable="false"><use xlink:href="#image-file-icon"></use></svg></span></a>'
        self.png_2k_html = '<a href="//stsci-opo.org/STScI-01G8GYE2PQWY96TDX66CHQRMPQ.png" class="link-icon-added">2000 X 693, PNG (1.65&nbsp;MB)&nbsp;<span class="link-icon svg-sprite -image-file-icon"><svg role="img" aria-label="(image File)" focusable="false"><use xlink:href="#image-file-icon"></use></svg></span></a>'
        self.div_start = '<div class="media-library-links-list">'
        self.download_options = "<p><strong>Download Options:</strong></p>"
        self.div_end = "</div>"
        return super().setUp()

    def test_2k_image_priority(self):
        html = (
            self.div_start
            + self.download_options
            + self.full_res_tif_html
            + self.png_2k_html
            + self.full_res_png_html
            + self.div_end
        )
        self.assertEqual(
            self.scraper.get_image_download_url(html),
            "https://stsci-opo.org/STScI-01G8GYE2PQWY96TDX66CHQRMPQ.png",
        )

    def test_full_res_png_priority(self):
        html = (
            self.div_start
            + self.download_options
            + self.full_res_tif_html
            + self.full_res_png_html
            + self.div_end
        )
        self.assertEqual(
            self.scraper.get_image_download_url(html),
            "https://stsci-opo.org/STScI-01G8GYD8B1H306SSPR4MY6NGN0.png",
        )

    def test_full_res_tif_priority(self):
        html = (
            self.div_start
            + self.download_options
            + self.full_res_tif_html
            + self.div_end
        )
        self.assertEqual(
            self.scraper.get_image_download_url(html),
            "https://stsci-opo.org/STScI-01G8GY7CZNNQH69BJG1ZGQ4D5B.tif",
        )

    def test_unknown_image(self):
        html = (
            self.div_start
            + self.download_options
            + '<a href="//dowload_link.png">Some other image</a>'
            + self.div_end
        )
        self.assertRaises(ValueError, self.scraper.get_image_download_url, html)

    def test_2k_image_title_unexpected_format(self):
        html = (
            self.div_start
            + self.download_options
            + '<a href="//dowload_link.png">2000 but nothing else</a>'
            + self.div_end
        )
        self.assertRaises(ValueError, self.scraper.get_image_download_url, html)

    def test_https_already_in_url(self):
        html = (
            self.div_start
            + self.download_options
            + '<a href="https://dowload_link.png">2000 x 1000 PNG</a>'
            + self.div_end
        )
        self.assertEqual(
            self.scraper.get_image_download_url(html),
            "https://dowload_link.png",
        )

    def test_no_download_link_list_found(self):
        html = self.download_options + self.full_res_tif_html
        self.assertRaises(ValueError, self.scraper.get_image_download_url, html)

    def test_no_links_found(self):
        html = ""
        self.assertRaises(ValueError, self.scraper.get_image_download_url, html)


class TestGetImageTitle(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        return super().setUp()

    def test_meta_title_property_not_defined(self):
        html = '<meta property="og:locale" content="en_US"><title>Some title</title>'
        self.assertRaises(ValueError, self.scraper.get_image_title, html)

    def test_meta_title_property_retrieved(self):
        html = '<meta property="og:title" content="Super Bangin Title"><title>Some title</title>'
        self.assertEqual(self.scraper.get_image_title(html), "Super Bangin Title")


class TestGetNextGallerySearchPage(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        return super().setUp()

    def tearDown(self) -> None:
        responses.reset()
        return super().tearDown()

    @patch("jwstascii_helpers.jwst_site_scraper.Scraper.get_url_with_retries")
    def test_exception_handling(self, mocked):
        mocked.side_effect = MaxRetryError(None, "a")
        self.scraper = Scraper()
        self.assertRaises(MaxRetryError, self.scraper.get_next_gallery_search_page)
        self.assertTrue(self.scraper.gallery_page_html is None)

    @responses.activate
    def test_html_attribute_set(self):
        html = "<p>My super sweet html</p>"
        responses.add(
            responses.GET,
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=1",
            status=200,
            body=html,
        )
        self.scraper.get_next_gallery_search_page()
        self.assertEqual(self.scraper.gallery_page_html, html)


class TestGetImageLinksFromGallerySearch(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        return super().setUp()

    def tearDown(self) -> None:
        responses.reset()
        return super().tearDown()

    def test_valid_links_found(self):
        self.scraper.gallery_page_html = """<a href="/contents/media/images/2022/047/01GE39QQCQ52JSF02RYJYCHH7J?Type=Observations&amp;itemsPerPage=100" class="link-wrap" title="some title"></a><a href="/contents/media/images/image_url_2" class="link-wrap" title="some title"></a><a href="/contents/image_url_3" class="link-wrap" title="some title"></a>"""
        expected = [
            "https://webbtelescope.org/contents/media/images/2022/047/01GE39QQCQ52JSF02RYJYCHH7J",
            "https://webbtelescope.org/contents/media/images/image_url_2",
        ]
        self.assertEqual(self.scraper.get_image_links_from_gallery_search(), expected)

    def test_no_valid_links_found(self):
        self.scraper.gallery_page_html = """<a href="/contents/image_url_2" class="link-wrap" title="some title"></a>"""
        self.assertRaises(
            RuntimeError, self.scraper.get_image_links_from_gallery_search
        )

    def test_ignore_list(self):
        with open("tests/resources/html/gallery_image_links.html", "r") as file:
            self.scraper.gallery_page_html = file.read()
        expected = [
            "https://webbtelescope.org/contents/media/images/2022/035/01G7DCWB7137MYJ05CSH1Q5Z1Z"
        ]
        self.assertEqual(
            self.scraper.get_image_links_from_gallery_search(
                ignore_regex_strings=["(?i).*hubble.*", "(?i).*Galileo.*"]
            ),
            expected,
        )


class TestGetUrlWithRetries(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        self.url = "https://my_url.com/"
        return super().setUp()

    @responses.activate
    def test_404_return(self):
        responses.add(
            responses.GET,
            self.url,
            status=404,
        )
        self.assertRaises(
            RuntimeError, self.scraper.get_url_with_retries, self.url, {}, 5
        )

    @responses.activate
    def test_requests_retry(self):
        json_codes = [500, 502, 503, 504]
        for code in json_codes:
            responses.add(
                responses.GET,
                self.url,
                status=code,
            )
            self.scraper = Scraper()
            self.assertRaises(
                RetryError, self.scraper.get_url_with_retries, self.url, {}, 5
            )

    @responses.activate
    def test_requests_call_correct(self):
        responses.add(
            responses.GET,
            self.url,
            status=200,
        )
        responses.add(
            responses.GET,
            self.url + "&a=1&b=2",
            status=200,
        )

        self.scraper.get_url_with_retries(self.url, {}, 5)
        self.scraper.get_url_with_retries(self.url, {"a": 1, "b": "2"}, 5)

        calls = responses.calls
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0].request.url,
            self.url,
        )
        self.assertEqual(
            calls[1].request.url,
            "https://my_url.com/?a=1&b=2",
        )


class TestDownloadImage(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        return super().setUp()

    @responses.activate
    def test_custom_image_name(self):
        with TemporaryDirectory() as tempdir:
            url = "https://stsci-opo.org/STScI-01GCCVK522S3SWM0TJN2ZA02ZZ.png"
            with open("tests/resources/images/test_image.png", "rb") as file:
                image = file.read()
            responses.add(responses.GET, url, status=200, body=image)
            self.scraper.download_image(url, tempdir, "image")
            with open(path.join(tempdir, "image.png"), "rb") as dl_image:
                self.assertEqual(image, dl_image.read())

    @responses.activate
    def test_image_downloaded_successfully(self):
        with TemporaryDirectory() as tempdir:
            url = "https://stsci-opo.org/STScI-01GCCVK522S3SWM0TJN2ZA02ZZ.png"
            with open("tests/resources/images/test_image.png", "rb") as file:
                image = file.read()
            responses.add(responses.GET, url, status=200, body=image)
            self.scraper.download_image(url, tempdir)
            with open(
                path.join(tempdir, "STScI-01GCCVK522S3SWM0TJN2ZA02ZZ.png"), "rb"
            ) as dl_image:
                self.assertEqual(image, dl_image.read())

    @responses.activate
    def test_image_url_invalid(self):
        with TemporaryDirectory() as tempdir:
            url = "https://stsci-opo.org/STScI-01GCCVK522S3SWM0TJN2ZA02ZZ.png"
            responses.add(responses.GET, url, status=404)
            self.assertRaises(RuntimeError, self.scraper.download_image, url, tempdir)
