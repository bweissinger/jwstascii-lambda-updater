import responses
from unittest import TestCase
from jwstascii_helpers.jwst_site_scraper import Scraper
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


class TestSearchNextGalleryPage(TestCase):
    def setUp(self) -> None:
        self.scraper = Scraper()
        return super().setUp()

    def tearDown(self) -> None:
        responses.reset()
        return super().tearDown()

    @responses.activate
    def test_404_return(self):
        responses.add(
            responses.GET,
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=1",
            status=404,
        )
        self.assertRaises(RuntimeError, self.scraper.search_next_gallery_page)

    @responses.activate
    def test_requests_retry(self):
        json_codes = [500, 502, 503, 504]
        for code in json_codes:
            responses.add(
                responses.GET,
                "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=1",
                status=code,
                body="""<a href="/contents/media/images/2022/047/01GE39QQCQ52JSF02RYJYCHH7J?Type=Observations&amp;itemsPerPage=100" class="link-wrap" title="some title">/a>""",
            )
            self.scraper = Scraper()
            self.assertRaises(MaxRetryError, self.scraper.search_next_gallery_page)

    @responses.activate
    def test_valid_links_found(self):
        responses.add(
            responses.GET,
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=1",
            status=200,
            body="""<a href="/contents/media/images/2022/047/01GE39QQCQ52JSF02RYJYCHH7J?Type=Observations&amp;itemsPerPage=100" class="link-wrap" title="some title"></a><a href="/contents/media/images/image_url_2" class="link-wrap" title="some title"></a><a href="/contents/image_url_2" class="link-wrap" title="some title"></a>""",
        )
        expected = [
            "https://webbtelescope.org/contents/media/images/2022/047/01GE39QQCQ52JSF02RYJYCHH7J?Type=Observations&itemsPerPage=100",
            "https://webbtelescope.org/contents/media/images/image_url_2",
        ]
        self.assertEqual(self.scraper.search_next_gallery_page(), expected)

    @responses.activate
    def test_requests_call_correct(self):
        responses.add(
            responses.GET,
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=1",
            status=200,
            body="""<a href="/contents/media/images/2022/047/01GE39QQCQ52JSF02RYJYCHH7J?Type=Observations&amp;itemsPerPage=100" class="link-wrap" title="some title"></a><a href="/contents/media/images/image_url_2" class="link-wrap" title="some title"></a><a href="/contents/image_url_2" class="link-wrap" title="some title"></a>""",
        )
        responses.add(
            responses.GET,
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=2",
            status=200,
            body="""<a href="/contents/media/images/2022/047/01GE39QQCQ52JSF02RYJYCHH7J?Type=Observations&amp;itemsPerPage=100" class="link-wrap" title="some title"></a>""",
        )
        self.scraper.search_next_gallery_page()
        self.scraper.search_next_gallery_page()
        calls = responses.calls
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0].request.url,
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=1",
        )
        self.assertEqual(
            calls[1].request.url,
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=2",
        )

    @responses.activate
    def test_no_valid_links_found(self):
        responses.add(
            responses.GET,
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=1",
            status=200,
            body="""<a href="/contents/image_url_2" class="link-wrap" title="some title"></a>""",
        )
        self.assertRaises(RuntimeError, self.scraper.search_next_gallery_page)
