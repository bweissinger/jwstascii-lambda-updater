import lambda_function
from datetime import date
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch


@patch("jwstascii_helpers.site_file_tools.get_links_from_archive_list")
class TestGetNextImageUrl(TestCase):
    def setUp(self) -> None:
        self.scraper = Mock()
        return super().setUp()

    def test_first_page(self, links_from_archive):
        links_from_archive.return_value = ["link_1"]
        self.scraper.get_image_links_from_gallery_search.side_effect = [
            ["link_1", "link_2"]
        ]
        links = lambda_function.get_next_image_url(self.scraper, [], Path("some_path"))
        self.assertEqual(links, "link_2")

    def test_multiple_pages(self, links_from_archive):
        links_from_archive.return_value = ["link_1"]
        self.scraper.get_image_links_from_gallery_search.side_effect = [
            ["link_1"],
            ["link_1", "link_2"],
            ["link_3"],
        ]
        links = lambda_function.get_next_image_url(self.scraper, [], Path("some_path"))
        self.assertEqual(links, "link_3")

    def test_no_links_available(self, links_from_archive):
        links_from_archive.return_value = ["link_1"]
        self.scraper.get_image_links_from_gallery_search.side_effect = [
            [],
            [],
            [],
        ]
        self.assertRaises(
            RuntimeError,
            lambda_function.get_next_image_url,
            self.scraper,
            [],
            Path("some_path"),
        )

    def test_correct_path_for_archive_links(self, links_from_archive):
        links_from_archive.return_value = []
        self.scraper.get_image_links_from_gallery_search.side_effect = [["link_1"]]
        lambda_function.get_next_image_url(self.scraper, [], Path("some_path"))
        links_from_archive.assert_called_once_with(Path("some_path/archive"))

    def test_scraper_calls(self, links_from_archive):
        links_from_archive.return_value = []
        self.scraper.get_image_links_from_gallery_search.side_effect = [
            ["link_1"],
        ]
        lambda_function.get_next_image_url(
            self.scraper, ["ignore_1", "ignore_2"], Path("some_path")
        )
        self.scraper.get_next_gallery_search_page.assert_called_once()
        self.scraper.get_image_links_from_gallery_search.assert_called_with(
            ["ignore_1", "ignore_2"]
        )

    def test_ignore_n_links(self, links_from_archive):
        links_from_archive.return_value = ["link_1", "link_2", "link_3"]
        self.scraper.get_image_links_from_gallery_search.side_effect = [
            ["link_1", "link_2", "link_3"]
        ]
        link = lambda_function.get_next_image_url(
            self.scraper,
            [],
            Path("some_path"),
            ignore_all_archive_links=False,
            ignore_last_n_archive_links=2,
        )
        self.assertTrue(link == "link_3")


@patch("jwstascii_helpers.git_tools.Repo")
class TestPrepareRepo(TestCase):
    def test_returns_repo(self, repo):
        initialized_repo = lambda_function.prepare_repo(
            "ssh_key", "some_url.com", "some_branch", Path("/tmp")
        )
        self.assertEqual(repo(), initialized_repo)

    def test_sets_ssh_key(self, repo):
        lambda_function.prepare_repo(
            "ssh_key", "some_url.com", "some_branch", Path("/tmp")
        )
        repo().set_git_ssh_key_from_secrets.assert_called_once_with(
            "ssh_key", Path("/tmp/id_rsa")
        )

    def test_clones_repo(self, repo):
        lambda_function.prepare_repo(
            "ssh_key", "some_url.com", "some_branch", Path("/tmp")
        )
        repo().clone_repo.assert_called_once_with(
            "some_url.com", Path("/tmp/jwstascii")
        )

    def test_checks_out_correct_branch(self, repo):
        lambda_function.prepare_repo(
            "ssh_key", "some_url.com", "some_branch", Path("/tmp")
        )
        repo().checkout_branch.assert_called_once_with("some_branch")


@patch("lambda_function.get_next_image_url")
class TestGetNewImageInfo(TestCase):
    def setUp(self) -> None:
        self.scraper = Mock()
        return super().setUp()

    def test_get_next_image_url_call(self, get_next_image_url):
        get_next_image_url.return_value = "url"
        lambda_function.get_new_image_info(
            self.scraper, ["ignore_1"], Path("path/to/repo"), 1
        )
        get_next_image_url.assert_called_once_with(
            self.scraper, ["ignore_1"], Path("path/to/repo")
        )

    def test_get_next_image_url_called_twice(self, get_next_image_url):
        get_next_image_url.side_effect = ["", "url"]
        lambda_function.get_new_image_info(
            self.scraper, ["ignore_1"], Path("path/to/repo"), 1
        )
        get_next_image_url.assert_called_with(
            self.scraper,
            ["ignore_1"],
            Path("path/to/repo"),
            ignore_archive_links=False,
            ignore_last_n_archive_links=1,
        )

    def test_get_url_with_retries(self, get_next_image_url):
        get_next_image_url.side_effect = ["image_url", "image_url"]
        lambda_function.get_new_image_info(
            self.scraper, ["ignore_1"], Path("path/to/repo"), 1
        )
        self.scraper.get_url_with_retries.assert_called_once_with("image_url", {}, 5)

    def test_correct_return(self, get_next_image_url):
        get_next_image_url.side_effect = ["", "image_url"]
        self.scraper.get_image_title.return_value = "title"
        self.scraper.get_image_description.return_value = "description"
        self.scraper.get_image_credits.return_value = "credits"
        self.scraper.get_image_download_url.return_value = "download_url"
        output = lambda_function.get_new_image_info(
            self.scraper, ["ignore_1"], Path("path/to/repo"), 1
        )
        self.assertEqual(
            output,
            {
                "image_title": "title",
                "image_description": "description",
                "image_credits": "credits",
                "image_download_url": "download_url",
                "image_page_url": "image_url",
            },
        )


@patch("boto3.client")
@patch("os.listdir")
@patch("jwstascii_helpers.ascii_conversion.convert_image")
class TestAddNewImage(TestCase):
    def setUp(self) -> None:
        self.scraper = Mock()
        self.charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ "
        return super().setUp()

    def test_uses_png(self, convert_image, listdir, s3_client):
        listdir.return_value = ["myimage.png"]
        file_path = lambda_function.add_new_image(
            self.scraper, "img_url", 200, self.charset, "s3bucket", Path("tmppath")
        )
        self.assertEqual(file_path, "myimage.png")

    def test_uses_tif(self, convert_image, listdir, s3_client):
        listdir.return_value = ["myimage.tif"]
        file_path = lambda_function.add_new_image(
            self.scraper, "img_url", 200, self.charset, "s3bucket", Path("tmppath")
        )
        self.assertEqual(file_path, "myimage.tif")

    def test_ignores_other_extensions(self, convert_image, listdir, s3_client):
        listdir.return_value = ["myimage.jpg"]
        self.assertRaises(
            RuntimeError,
            lambda_function.add_new_image,
            self.scraper,
            "img_url",
            200,
            self.charset,
            "s3bucket",
            Path("tmppath"),
        )

    def test_download_image_call(self, convert_image, listdir, s3_client):
        listdir.return_value = ["myimage.png"]
        lambda_function.add_new_image(
            self.scraper, "img_url", 200, self.charset, "s3bucket", Path("tmppath")
        )
        self.scraper.download_image.assert_called_once_with("img_url", Path("tmppath"))

    def test_s3_upload(self, convert_image, listdir, s3_client):
        listdir.return_value = ["myimage.png"]
        lambda_function.add_new_image(
            self.scraper, "img_url", 200, self.charset, "s3bucket", Path("tmppath")
        )
        s3_client().upload_file.assert_called_once_with(
            "tmppath/myimage.png", "s3bucket", "images/myimage.png"
        )


class TestPushRepo(TestCase):
    def setUp(self) -> None:
        self.repo = Mock()
        self.page_date = date(2022, 10, 1)
        return super().setUp()

    def test_add_called(self):
        lambda_function.push_repo(
            self.repo, self.page_date, "some_author", "some_email"
        )
        self.repo.add.assert_called_once_with()

    def test_commit_called(self):
        lambda_function.push_repo(
            self.repo, self.page_date, "some_author", "some_email"
        )
        self.repo.commit_files.assert_called_once_with(
            "Created new page for 01 Oct 2022", "some_author", "some_email"
        )

    def test_push_called(self):
        lambda_function.push_repo(
            self.repo, self.page_date, "some_author", "some_email"
        )
        self.repo.push_files.assert_called_once_with()
