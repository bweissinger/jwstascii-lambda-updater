import os
import tempfile
from aws_lambda_powertools.utilities import parameters
from unittest import TestCase
from unittest.mock import Mock, patch, mock_open, call
from unittest import main
from pathlib import Path

from jwstascii_helpers.git_tools import Repo


class test_set_git_ssh_key_from_secrets(TestCase):
    @patch.dict("os.environ", {"GIT_SSH_COMMAND": "not_correct"})
    def setUp(self):
        parameters.get_secret = Mock()
        self.repo = Repo()
        self.file_path = tempfile.mkstemp()[1]
        os.chmod = Mock()
        self.ssh_key_name = "test_key_name"
        self.ssh_key_contents = "ssh_key_contents"
        parameters.get_secret.return_value = self.ssh_key_contents
        return super().setUp()

    def tearDown(self):
        os.remove(self.file_path)

    def test_ssh_key_retreival(self):
        self.repo.set_git_ssh_key_from_secrets(self.ssh_key_name, self.file_path)
        parameters.get_secret.assert_called_with(self.ssh_key_name)

    def test_ssh_key_writing(self):
        self.repo.set_git_ssh_key_from_secrets(self.ssh_key_name, self.file_path)
        contents = ""
        with open(self.file_path, "r") as file:
            for line in file:
                contents += line
        self.assertEqual(contents, self.ssh_key_contents)

    def test_ssh_key_permissions_set(self):
        self.repo.set_git_ssh_key_from_secrets(self.ssh_key_name, self.file_path)
        os.chmod.assert_called_with(self.file_path, 0o600)

    @patch("builtins.open", mock_open())
    def test_env_gitsshkey_set(self):
        # Mock open so that a custom file path can be used and the
        #   the ssh command explicitly typed for checking.
        self.repo.set_git_ssh_key_from_secrets(self.ssh_key_name, "test/path")
        assert os.environ["GIT_SSH_COMMAND"] == (
            "ssh -i test/path -o StrictHostKeyChecking=no"
        )

    def test_get_parameter_error(self):
        parameters.get_secret.side_effect = parameters.GetParameterError()
        self.assertRaises(
            ValueError,
            self.repo.set_git_ssh_key_from_secrets,
            self.ssh_key_name,
            self.file_path,
        )

    def test_transform_parameter_error(self):
        parameters.get_secret.side_effect = parameters.TransformParameterError
        self.assertRaises(
            ValueError,
            self.repo.set_git_ssh_key_from_secrets,
            self.ssh_key_name,
            self.file_path,
        )


class test_add(TestCase):
    def setUp(self) -> None:
        Repo.repo = Mock()
        self.repo = Repo()
        self.untracked_1 = "new_file"
        self.untracked_2 = "new/file/in/dir"
        self.modified_1 = "changed_file"
        self.modified_2 = "changed/file/in/dir"
        self.modified_combined = self.modified_1 + "\n" + self.modified_2
        Repo.repo.untracked_files = []
        Repo.repo.git.diff.return_value = ""
        return super().setUp()

    def test_add_all_files(self):
        Repo.repo.untracked_files = [self.untracked_1, self.untracked_2]
        Repo.repo.git.diff.return_value = self.modified_combined
        self.repo.add()
        assert self.repo.repo.git.add.call_count == 4
        self.repo.repo.git.add.assert_has_calls(
            [
                call(self.untracked_1),
                call(self.untracked_2),
                call(self.modified_1),
                call(self.modified_2),
            ]
        )

    def test_add_all_files_no_untracked(self):
        Repo.repo.git.diff.return_value = self.modified_combined
        self.repo.add()
        assert self.repo.repo.git.add.call_count == 2
        self.repo.repo.git.add.assert_has_calls(
            [
                call(self.modified_1),
                call(self.modified_2),
            ]
        )

    def test_add_all_files_single_modified(self):
        Repo.repo.git.diff.return_value = self.modified_2
        self.repo.add()
        assert self.repo.repo.git.add.call_count == 1
        self.repo.repo.git.add.assert_has_calls([call(self.modified_2)])

    def test_add_all_files_no_modified(self):
        Repo.repo.untracked_files = [self.untracked_1, self.untracked_2]
        self.repo.add()
        assert self.repo.repo.git.add.call_count == 2
        self.repo.repo.git.add.assert_has_calls(
            [
                call(self.untracked_1),
                call(self.untracked_2),
            ]
        )

    def test_add_all_files_single_untracked(self):
        Repo.repo.untracked_files = [self.untracked_2]
        self.repo.add()
        assert self.repo.repo.git.add.call_count == 1
        self.repo.repo.git.add.assert_has_calls([call(self.untracked_2)])

    def test_add_all_files_with_ignore(self):
        Repo.repo.untracked_files = [self.untracked_1, self.untracked_2]
        Repo.repo.git.diff.return_value = self.modified_combined
        self.repo.add(ignore=[self.untracked_2, self.modified_1, "file/not/in/dir"])
        assert self.repo.repo.git.add.call_count == 2
        self.repo.repo.git.add.assert_has_calls(
            [
                call(self.untracked_1),
                call(self.modified_2),
            ]
        )

    def test_add_specified_files(self):
        Repo.repo.untracked_files = [self.untracked_1, self.untracked_2]
        Repo.repo.git.diff.return_value = self.modified_combined
        self.repo.add(files=[self.untracked_1, self.modified_2])
        assert self.repo.repo.git.add.call_count == 2
        self.repo.repo.git.add.assert_has_calls(
            [
                call(self.untracked_1),
                call(self.modified_2),
            ]
        )

    def test_add_specified_files_with_ignore(self):
        Repo.repo.untracked_files = [self.untracked_1, self.untracked_2]
        Repo.repo.git.diff.return_value = self.modified_combined
        self.repo.add(
            files=[self.modified_1, self.untracked_2], ignore=[self.untracked_2]
        )
        assert self.repo.repo.git.add.call_count == 1
        self.repo.repo.git.add.assert_has_calls(
            [
                call(self.modified_1),
            ]
        )


class test_commit_files(TestCase):
    def setUp(self) -> None:
        Repo.repo = Mock()
        self.repo = Repo()
        self.repo.commit_files("Test message", "test_author", "test_email")
        return super().setUp()

    def test_config_writer_calls(self):
        assert self.repo.repo.config_writer().set_value.call_count == 2
        self.repo.repo.config_writer().set_value.assert_has_calls(
            [call("user", "name", "test_author"), call("user", "email", "test_email")]
        )

    def test_git_commit_call(self):
        self.repo.repo.git.commit.assert_called_once_with(
            "-m", "Test message", author="test_author <test_email>"
        )


class test_push_files(TestCase):
    def setUp(self) -> None:
        Repo.repo = Mock()
        self.repo = Repo()
        self.repo.branch = "test_branch"
        return super().setUp()

    def test_git_push_call(self):
        self.repo.push_files()
        self.repo.repo.git.push.assert_called_once_with("origin", "test_branch")


class test_checkout_branch(TestCase):
    def setUp(self) -> None:
        Repo.repo = Mock()
        self.repo = Repo()
        self.repo.branch = "og_branch"
        self.repo.checkout_branch("new_branch")
        return super().setUp()

    def test_git_checkout_called(self):
        self.repo.repo.git.checkout.assert_called_once_with("new_branch")

    def test_repo_branch_var_modified(self):
        assert self.repo.branch == "new_branch"


class test_clone_repo(TestCase):
    def setUp(self) -> None:
        Repo.repo = Mock()
        self.repo = Repo()
        return super().setUp()

    @patch("jwstascii_helpers.git_tools.git")
    def test_git_clone_call(self, mocked_git):
        self.repo.clone_repo("repo_url", "test/dir")
        mocked_git.Repo.clone_from.assert_called_once_with("repo_url", "test/dir")

    @patch("jwstascii_helpers.git_tools.git")
    def test_repo_dir_set(self, mocked_git):
        mocked_git.Repo.clone_from().git_dir = "test/dir/.git"
        self.repo.clone_repo("repo_url", "test/dir")
        assert self.repo.repo_dir == Path("test/dir")

    @patch("jwstascii_helpers.git_tools.git")
    def test_branch_set(self, mocked_git):
        branch_name = "test_branch"
        mocked_git.Repo.clone_from().active_branch.name = branch_name
        self.repo.clone_repo("repo_url", "test/dir")
        assert self.repo.branch == branch_name


if __name__ == "__main__":
    main()
