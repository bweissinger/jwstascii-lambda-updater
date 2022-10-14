import lambda_function
import responses
import re
from tempfile import TemporaryDirectory
from unittest import TestCase
from pathlib import Path
from shutil import copytree
from freezegun import freeze_time
from unittest.mock import patch
from os import walk, chdir, getcwd


@freeze_time("2022-10-01")
@patch("jwstascii_helpers.git_tools.Repo")
@patch("lambda_function.boto3")
@patch("os.system")
class TestLambdaFunction(TestCase):
    def add_response_from_file(self, file_path, url, read_as_bytes=False):
        open_type = "r"
        if read_as_bytes:
            open_type = "rb"
        with open(file_path, open_type) as file:
            responses.add(
                responses.GET,
                url,
                body=file.read(),
                status=200,
            )

    def get_files_in_dir(self, directory):
        file_list = []
        for path, subdirs, files in walk(directory):
            for name in files:
                file_list.append(Path(path, name))
        return file_list

    def setUp(self) -> None:
        html_base_path = Path("tests", "resources", "html")
        self.add_response_from_file(
            Path(html_base_path, "jwst_site_search.html"),
            "https://webbtelescope.org/resource-gallery/images?Type=Observations&itemsPerPage=100&page=1",
        )
        self.add_response_from_file(
            Path(html_base_path, "jwst_image_page.html"),
            re.compile("https://webbtelescope.org/contents/media/images*"),
        )
        self.add_response_from_file(
            Path("tests", "resources", "images", "test_image.png"),
            "https://stsci-opo.org/STScI-01GEPRPG8PG0CT4CSKP46RR3JX.png",
            read_as_bytes=True,
        )
        self.event = {
            "key_name": "git_ssh_key",
            "repo_url": "url_of_git_repo",
            "git_branch": "automated",
            "ascii_art_num_columns": 25,
            "ascii_charset": "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ",
            "s3_bucket": "jwstascii",
            "temp_dir": "/tmp",
            "ignore_regex": ["(?i).*hubble.*"],
            "git_author": "jwstascii-bot",
            "git_email": "jwstascii-bot",
            "test_url": "https://webbtelescope.org/contents/media/images/01GEJB2906TM9VR2FSJ4TFMNQM",
        }
        return super().setUp()

    @responses.activate
    def test_normal_workflow(self, os_system, boto3, repo):
        with TemporaryDirectory() as tempdir:
            self.event["temp_dir"] = tempdir
            starting_directory = getcwd()
            expected_files_path = Path(
                starting_directory, "tests", "resources", "expected_site_files"
            )
            repo_path = Path(tempdir, "jwstascii")
            copytree(Path("tests", "resources", "site_files", ""), repo_path)
            repo().repo_dir = repo_path

            lambda_function.lambda_handler(self.event, None)

            # Find all files from the site repo parent directory
            # They should be the same for both output and expected
            chdir(expected_files_path)
            expected_files = self.get_files_in_dir(Path("."))

            chdir(repo_path)
            output_files = self.get_files_in_dir(Path("."))

            chdir(starting_directory)

            # Ensure sets are the same
            self.assertEqual(len(set(output_files) - set(expected_files)), 0)

            for output_file in output_files:
                with open(Path(repo_path, output_file), "rb") as a:
                    with open(Path(expected_files_path, output_file), "rb") as b:
                        self.assertEqual(a.read(), b.read())
