from tempfile import TemporaryDirectory
from unittest import TestCase
from git import Repo
from os.path import join, exists
from pathlib import Path

from jwstascii_helpers import git_tools


class TestFunctionality(TestCase):
    def create_remote(self):
        self.repo_path = join(self.tempdir, "remote_repo")
        self.repo = Repo().init(self.repo_path, initial_branch="main")

        self.repo.git.checkout("-b", "main")
        with open(join(self.repo_path, "test_file.txt"), "w") as file:
            file.write("This is test data.")
        self.repo.git.add(".")
        config = self.repo.config_writer()
        config.set_value("user", "name", "fixture_author")
        config.set_value("user", "email", "fixture_email")
        self.repo.git.commit(
            "-m", "First commit.", author="fixture_author <fixture_email>"
        )

        self.repo.git.checkout("-b", "new_branch")
        with open(join(self.repo_path, "other_file.txt"), "w") as file:
            file.write("Do not touch.")
        self.repo.git.add(".")
        config.set_value("user", "name", "fixture_author")
        config.set_value("user", "email", "fixture_email")
        self.repo.git.commit(
            "-m", "Second commit.", author="fixture_author <fixture_email>"
        )
        self.repo.git.checkout("main")

    def create_local_push_changes(self):
        self.local_repo = git_tools.Repo()
        self.local_repo.clone_repo(
            Path(self.repo.git_dir).parent, join(self.tempdir, "local_repo")
        )
        self.local_repo.checkout_branch("new_branch")

        with open(join(self.local_repo.repo_dir, "new_file.txt"), "w") as file:
            file.write("Should not be this.")
        self.local_repo.add()
        self.local_repo.commit_files("Some commit", "some_author", "some_email")

        with open(join(self.local_repo.repo_dir, "new_file.txt"), "w") as file:
            file.write("This is a new file.")
        with open(join(self.local_repo.repo_dir, "test_file.txt"), "w") as file:
            file.write("This is a modified file.")
        self.local_repo.add()
        self.local_repo.commit_files("Newest commit", "new_author", "new_email")
        self.local_repo.push_files()

    def test_file_states_new_branch(self):
        with TemporaryDirectory() as self.tempdir:
            self.create_remote()
            self.create_local_push_changes()
            self.repo.git.checkout("new_branch")
            with open(join(self.repo_path, "new_file.txt"), "r") as file:
                assert file.readlines() == ["This is a new file."]

            with open(join(self.repo_path, "test_file.txt"), "r") as file:
                assert file.readlines() == ["This is a modified file."]

            with open(join(self.repo_path, "other_file.txt"), "r") as file:
                assert file.readlines() == ["Do not touch."]

    def test_file_states_main_branch(self):
        with TemporaryDirectory() as self.tempdir:
            self.create_remote()
            self.create_local_push_changes()

            with open(join(self.repo_path, "test_file.txt"), "r") as file:
                assert file.readlines() == ["This is test data."]

            assert not exists(join(self.repo_path, "new_file.txt"))

            assert not exists(join(self.repo_path, "other_file.txt"))

    def test_author_status_new_branch(self):
        with TemporaryDirectory() as self.tempdir:
            self.create_remote()
            self.create_local_push_changes()
            self.repo.git.checkout("new_branch")
            assert (
                self.repo.git.show("-s", "--format=Author: %an <%ae>")
                == "Author: new_author <new_email>"
            )

    def test_author_status_main_branch(self):
        with TemporaryDirectory() as self.tempdir:
            self.create_remote()
            self.create_local_push_changes()
            assert (
                self.repo.git.show("-s", "--format=Author: %an <%ae>")
                == "Author: fixture_author <fixture_email>"
            )

    def test_num_commits_new_branch(self):
        with TemporaryDirectory() as self.tempdir:
            self.create_remote()
            self.create_local_push_changes()
            self.repo.git.checkout("new_branch")
            assert self.repo.git.rev_list("--count", "HEAD") == "4"

    def test_num_commits_main_branch(self):
        with TemporaryDirectory() as self.tempdir:
            self.create_remote()
            self.create_local_push_changes()
            assert self.repo.git.rev_list("--count", "HEAD") == "1"
