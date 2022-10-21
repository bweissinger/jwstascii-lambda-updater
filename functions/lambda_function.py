import os
import boto3
import random
from typing import Any, Dict, List
from pathlib import Path
from datetime import datetime, timedelta, date
from jwstascii_helpers import (
    git_tools,
    jwst_site_scraper,
    site_file_tools,
    ascii_conversion,
)


def lambda_handler(event: Dict[str, Any], context: object) -> Dict[str, Any]:

    # Lambda will sometimes hold resources between invocations, ensure dir is clean.
    os.system("rm -rf %s" % str(Path(event["temp_dir"], "*")))

    repo = prepare_repo(
        event["key_name"], event["repo_url"], event["git_branch"], event["temp_dir"]
    )
    os.chdir(repo.repo_dir)

    today_date = datetime.utcnow().date()
    previous_page_date = site_file_tools.get_date_of_current_page(Path("index.html"))
    if today_date == previous_page_date:
        raise RuntimeError(
            "Page for todays date of %s already exists"
            % today_date.strftime("%d %B %Y")
        )

    site_scraper = jwst_site_scraper.Scraper()
    image_info = get_new_image_info(
        site_scraper,
        event["ignore_regex"],
        repo.repo_dir,
        event["num_links_to_ignore_when_no_new"],
    )
    image_file_name = add_new_image(
        site_scraper,
        image_info["image_download_url"],
        event["ascii_art_num_columns"],
        event["ascii_charset"],
        event["s3_bucket"],
        event["temp_dir"],
    )

    new_page_path = Path(
        today_date.strftime("%Y"),
        today_date.strftime("%B").lower(),
        today_date.strftime("%d"),
        "index.html",
    )
    previous_page_path = Path(
        previous_page_date.strftime("%Y/%B/%d").lower(), "index.html"
    )

    if event["test_url"]:
        image_info["image_page_url"] = event["test_url"]

    site_file_tools.generate_from_template(
        "new_page.html",
        new_page_path,
        {
            "title_date": today_date.strftime("%d %B %Y"),
            "tomorrow_date": (today_date + timedelta(days=1)).strftime("%d|%m|%y"),
            "today_date": today_date.strftime("%d|%m|%y"),
            "previous_path": Path("/", previous_page_path),
            "previous_date": previous_page_date.strftime("%d|%m|%y"),
            "image_title": image_info["image_title"],
            "image_path": Path("/images", image_file_name),
            "link_to_jwst_website": image_info["image_page_url"],
            "image_credits": image_info["image_credits"],
            "image_description": image_info["image_description"],
        },
    )

    site_file_tools.generate_from_template(
        "main_index.html",
        Path("index.html"),
        {
            "page_parent_dir": "/" + str(new_page_path.parent),
            "image_title": image_info["image_title"],
        },
    )

    site_file_tools.update_prior_page(
        previous_page_path, Path("/", new_page_path), today_date
    )
    site_file_tools.update_archive(
        Path(repo.repo_dir, "archive"),
        Path(today_date.strftime("/%Y/%B/%d").lower()),
        today_date,
        image_info["image_title"],
        image_info["image_page_url"],
    )

    push_repo(repo, today_date, event["git_author"], event["git_email"])


def push_repo(repo: git_tools.Repo, page_date: date, author: str, email: str) -> None:
    """
    Adds and commits new files to the git repository, then pushes the changes.

    Args:
        repo (git_tools.Repo): Git repo object.
        page_date (date): Creation date of the newly added page.
        author (str): Author name to use for commit.
        email (str): Author email to use for commit.
    """
    repo.add(),
    repo.commit_files(
        "Created new page for %s" % page_date.strftime("%d %b %Y"), author, email
    )
    repo.push_files()


def add_new_image(
    site_scraper: jwst_site_scraper.Scraper,
    image_url: str,
    num_colums: int,
    charset: str,
    bucket_name: str,
    temp_dir: Path,
) -> str:
    """
    Creates an ascii art image from the jwst image at the given url, and uploads
    the result to the website S3 bucket.

    Args:
        site_scraper (jwst_site_scraper.Scraper): JWST site scraper.
        image_url (str): Url of the jwst image.
        num_colums (int): Number of text columns to use for the image conversion.
        charset (str): String of characters to use for ascii image generation.
        bucket_name (str): Name of the S3 bucket.
        temp_dir (str): Path of the temporary directory to use for image conversion. For
            AWS Lambda, /tmp is user writable.

    Returns:
        str: File name of the image.
    """
    site_scraper.download_image(image_url, temp_dir)
    for file in os.listdir(temp_dir):
        if file.endswith(".tif") or file.endswith(".png"):
            image_file_name = file
            image_path = Path(temp_dir, file)
    try:
        ascii_conversion.convert_image(image_path, num_colums, charset, image_path)
    except UnboundLocalError:
        raise RuntimeError("Could not find suitable image in directory: %s" % temp_dir)
    s3 = boto3.client("s3")
    s3.upload_file(str(image_path), bucket_name, str(Path("images", image_file_name)))
    return image_file_name


def get_new_image_info(
    site_scraper: jwst_site_scraper.Scraper,
    ignore_regex: List[str],
    repo_dir: Path,
    ignore_last_n_links_when_no_new: int,
) -> Dict[str, str]:
    """Scrapes image info from the jwst website.


    Args:
        site_scraper (jwst_site_scraper.Scraper): Scraper object.
        ignore_regex (List[str]): A list of regex strings to use for filtering images.
        repo_dir (Path): _description_
        ignore_last_n_links_when_no_new (int): Number of previous images to ignore when there are no new images available. Positive values will ignore the latest n links. Negative values will ignore the oldest n links.

    Returns:
        Dict[str:str]: A dictionary object containing image attributes.

    """
    url = get_next_image_url(site_scraper, ignore_regex, repo_dir)

    # Get previously used image if no new images are available
    if not url:
        url = get_next_image_url(
            site_scraper,
            ignore_regex,
            repo_dir,
            ignore_archive_links=False,
            ignore_last_n_archive_links=ignore_last_n_links_when_no_new,
        )

    html = site_scraper.get_url_with_retries(url, {}, 5).text
    return {
        "image_title": site_scraper.get_image_title(html),
        "image_description": site_scraper.get_image_description(html),
        "image_credits": site_scraper.get_image_credits(html),
        "image_download_url": site_scraper.get_image_download_url(html),
        "image_page_url": url,
    }


def prepare_repo(
    ssh_key_name: str, repo_url: str, branch_name: str, temp_path: Path
) -> git_tools.Repo:
    """
    Clones and prepares the website repo.

    Args:
        ssh_key_name (str): Name of the ssh key in AWS secrets manager.
        repo_url (str): Url of the website repo.
        branch_name (str): Name of the git branch to use.
        temp_path (Path): Path of temporary working directory. For AWS Lambda
            this should be '/tmp'

    Returns:
        git_tools.Repo: Returns a repo object.
    """
    repo = git_tools.Repo()
    repo.set_git_ssh_key_from_secrets(ssh_key_name, Path(temp_path, "id_rsa"))
    repo.clone_repo(repo_url, Path(temp_path, "jwstascii"))
    repo.checkout_branch(branch_name)
    return repo


def get_next_image_url(
    scraper: jwst_site_scraper.Scraper,
    ignore_regex: List[str],
    repo_dir: Path,
    ignore_all_archive_links: bool = True,
    ignore_last_n_archive_links: int = 0,
) -> str:
    """
    Gets the url of an unused jwst image from the jwst website.

    Args:
        scraper (jwst_site_scraper.Scraper): JWST website scraper.
        ignore_regex (List[str]): A list of regex strings to use for filtering
            images from the jwst website.
        repo_dir (Path): Path of the git repo.
        ignore_all_archive_links (int, optional): Ignore all previously used links. Takes precedent over ignore_last_n_archive_links.
        ignore_last_n_archive_links (int, optional): Number of archive links to ignore. Positive numbers ignore the most recent n archive links, negative ignore the oldest n links.

    Returns:
        str: Url of the found image.
    """
    scraper.get_next_gallery_search_page()

    # At end of all available image links, no more pages to search
    if not scraper.get_image_links_from_gallery_search():
        return ""

    # Only use image links that do not fit search pattern in ignore_regex
    links = scraper.get_image_links_from_gallery_search(ignore_regex)
    used_links = site_file_tools.get_links_from_archive_list(Path(repo_dir, "archive"))
    if not ignore_all_archive_links:
        if ignore_last_n_archive_links < 0:
            used_links = used_links[ignore_last_n_archive_links:]
        elif ignore_last_n_archive_links > 0:
            used_links = used_links[:ignore_last_n_archive_links]

    available_links = set(links) - set(used_links)
    try:
        return random.sample(available_links, 1)[0]
    except ValueError:
        # Search next page for available links
        return get_next_image_url(
            scraper,
            ignore_regex,
            repo_dir,
            ignore_all_archive_links=ignore_all_archive_links,
            ignore_last_n_archive_links=ignore_last_n_archive_links,
        )
