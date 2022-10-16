import git
import os
from aws_lambda_powertools.utilities import parameters
from pathlib import Path
from typing import List


class Repo:
    """
    Wraps the GitPython library and provides functionality for retrieving repos from github and interacting with them.

    Attributes:
        repo (git.Repo): Git repo object.
        repo_dir (PosixPath): Path of repo object.
        branch (str): Current checked out branch of repo.
    """

    def set_git_ssh_key_from_secrets(
        self, ssh_key_name: str, ssh_key_path: str
    ) -> None:
        """
        Retrieves the ssh key from AWS Secrets manger and adds it to the environment.

        Args:
            ssh_key_name (str): Name of ssh key in AWS Secrets Manager.
            ssh_key_path (str): Filepath where SSH key should be stored. Note that for Lambda, this path should be in the /tmp directory.
        Returns:
            None
        Raises:
            ValueError: Raised if ssh key retrieval from Secrets Manager fails.
        """

        with open(ssh_key_path, "w") as file:
            try:
                file.write(parameters.get_secret(ssh_key_name))
            except (
                parameters.TransformParameterError,
                parameters.GetParameterError,
            ) as e:
                raise ValueError("Unable to retrieve ssh key." + str(e))

            os.chmod(ssh_key_path, 0o600)
            os.environ["GIT_SSH_COMMAND"] = (
                "ssh -i %s -o StrictHostKeyChecking=no" % ssh_key_path
            )

    def add(self, files: List[str] = list(), ignore: List[str] = list()) -> None:
        """
        Stages specified files in repo. If no files are specified, then all modified
        and untracked files will be staged.

        Args:
            files (list, optional): A list of files to stage. Defaults to list().
            ignore (list, optional): A list of files to ignore. Takes precedence
                over files. Defaults to list().

        Returns:
            None
        """
        if not files:
            files = list(self.repo.untracked_files)
            for file in self.repo.git.diff(None, name_only=True).split("\n"):
                if file:
                    files.append(file)

        ignore = set(ignore)

        for file in files:
            if file not in ignore:
                self.repo.git.add(file)

    def commit_files(self, message: str, author: str, email: str) -> None:
        """
        Commit staged files with specified message under given author and email.

        Args:
            message (str): Message to provide git for commit.
            author (str): Author name to use for commit.
            email (str): Author email to use for commit.
        """

        if not self._config_writer:
            self._config_writer = self.repo.config_writer()

        self._config_writer.set_value("user", "name", author)
        self._config_writer.set_value("user", "email", email)

        author_string = "%s <%s>" % (author, email)
        self.repo.git.commit("-m", message, author=author_string)

    def push_files(self) -> None:
        """
        Push files to remote repository.
        """
        self.repo.git.push("origin", self.branch)

    def checkout_branch(self, branch: str) -> None:
        """
        Checkout the specified branch.

        Args:
            branch (str, optional): Name of branch to checkout.
        Returns:
            None
        """
        self.repo.git.checkout(branch)
        self.branch = branch

    def clone_repo(self, url: str, clone_to_path: str):
        """Clone repo from url. If using ssh the ssh environment key must be set
            prior to cloning.

        Args:
            url (str): Url of git repo to clone.
            clone_to_path (str): Path to clone repo to. Note that this path is
                the parent dir. For example, the repo files will be placed in
                'my/dir' not 'my/dir/repo_name
        """
        self.repo = git.Repo.clone_from(url, clone_to_path)
        self.repo_dir = Path(self.repo.git_dir).parent
        self.branch = self.repo.active_branch.name

    def __init__(self) -> None:
        self._config_writer = None
