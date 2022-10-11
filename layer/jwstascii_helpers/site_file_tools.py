import jinja2
import re
from datetime import datetime, date
from pathlib import Path
from os import makedirs
from os.path import exists
from typing import Dict, List
from bs4 import BeautifulSoup


def get_jinja_template(template_name: Path) -> jinja2.Template:
    """
    Load the requested template.

    Args:
        template_name (str): File name of the desired template.

    Returns:
        jinja2.Template: The requested jinja2 template.
    """
    template_env = jinja2.Environment(
        loader=jinja2.PackageLoader("jwstascii_helpers"), autoescape=True
    )
    return template_env.get_template(template_name)


def write_file(output_path: Path, file_content: str) -> None:
    """
    Writes contents to file at specified path. Any necessary directories will be created
    in the process.

    Args:
        output_path (Path): Output path of the file.
        file_content (str): Contents to be written to the file.
    """
    if not exists(output_path.parent):
        makedirs(output_path.parent)
    with open(output_path, "w") as file:
        file.write(file_content)


def generate_from_template(
    template_name: str, output_path: Path, vars_dict: Dict[str, str]
) -> None:
    """
    Function for generating html from a jinja template.

    Args:
        template_name (str): File name of the desired template.
        output_path (Path): Path of the resulting html file.
        vars_dict (Dict[str, str]): Dictionary containing template variables and their
            values to be assigned.
    """
    template = get_jinja_template(template_name)
    output_html = template.render(**vars_dict)
    write_file(output_path, output_html)


def update_prior_page(
    path_to_html: Path, path_to_new_html: Path, new_page_date: date
) -> None:
    """Used for updating the prior displayed html page. Changes styling and adds link to
        the new page.

    Args:
        path_to_html (Path): Path of the previous page.
        path_to_new_html (Path): Path to the new page. Used as a link reference.
        new_page_date (date): The date of the new page. Ensures the date is correct,
            since updates may not be consistently daily.
    """
    soup = soup_from_file(path_to_html)
    tomorrow_link = soup.find("li", {"id": "tomorrow_link"})
    new_html = '<li id="tomorrow_link"><a href="%s">%s</a></li>' % (
        path_to_new_html,
        new_page_date.strftime("%d|%m|%y"),
    )
    tag = BeautifulSoup(new_html, "html.parser")
    try:
        tomorrow_link.replace_with(tag)
    except AttributeError as e:
        raise RuntimeError(
            """It looks like the next page element was not found, cannot set
            the href on a null reference. \n%s"""
            % e
        )

    stylesheet_tag = soup.find("link", {"rel": "stylesheet"})

    try:
        stylesheet_tag["href"] = "/styles/main.css"
    except TypeError as e:
        raise RuntimeError(
            """It looks like the next page element was not found, cannot set
             the href on a null reference. \n%s"""
            % e
        )

    write_file(path_to_html, soup.prettify())


def soup_from_file(file_path: Path) -> BeautifulSoup:
    """
    Get a BeautifulSoup object of the selected file.

    Args:
        file_path (Path): Path of the file to parse.

    Returns:
        BeautifulSoup: BeautifulSoup object of the parsed file.
    """
    with open(file_path, "r") as file:
        return BeautifulSoup(file.read(), "lxml")


def add_link_to_archive_list(
    index_path: Path, page_path: Path, page_date: date, image_title: str, image_url: str
) -> None:
    """
    Create a new link in the full archive list. The new link will be first on
    the page.

    Args:
        index_path (Path): Path to the full archive index file.
        page_path (Path): Path of the page to be linked in the archive list.
        page_date (date): Date for the page.
        image_title (str): Title used for the page image.
        image_url (str): The url of the image page on the jwst website.
    """
    soup = soup_from_file(index_path)

    list_item = """<li><span>%s</span><a data-jwst_url="%s" href="%s">%s</a></li>""" % (
        page_date.strftime("%d %B %Y"),
        image_url,
        page_path,
        image_title,
    )

    ordered_list = soup.find("ol", {"class": "archive_list"})

    # findChild will return the first list element
    ordered_list.findChild().insert_before(BeautifulSoup(list_item, "html.parser"))

    write_file(index_path, soup.prettify())


def add_month_to_archive(
    template_path: Path,
    new_month_path: Path,
    archive_overview_path: Path,
    year: str,
    month: str,
) -> None:
    """
    Adds new month entry to the archive if the month is not already present.

    Args:
        template_path (Path): The path to the template file.
        new_month_path (Path): The path where the new month index file should be saved.
        archive_overview_path (Path): The path to the archive overview page.
        year (str): Year of new month, 4 digit. Used for headers in the html.
        month (str): Full month name (i.e. October). Used for headers in the html.
    """

    archive_overview_soup = soup_from_file(archive_overview_path)
    year_header = archive_overview_soup.find("h2", string=year)
    new_section_html = """
                <div class='grid-item'>
                    <a href='%s'>%s</a>
                </div>""" % (
        new_month_path,
        month.capitalize(),
    )

    try:
        current_month = year_header.find_next("div", {"class": "grid-item"})
        if current_month.find_next("a").string.lower() == month.lower():
            return None
        current_month.insert_before(BeautifulSoup(new_section_html, "html.parser"))
    except AttributeError:
        daily_list_link = archive_overview_soup.find("h1", {"id": "daily-list-link"})
        new_section_html = """<h2>%s</h2><div class='grid-container'>%s</div>""" % (
            year,
            new_section_html,
        )
        daily_list_link.insert_after(BeautifulSoup(new_section_html, "html.parser"))

    generate_from_template(
        template_path,
        new_month_path,
        {
            "main_archive_html_path": archive_overview_path,
            "month_and_year": "%s %s" % (month.capitalize(), year),
        },
    )

    write_file(archive_overview_path, archive_overview_soup.prettify())


def update_archive(
    template_dir: Path,
    archive_path: Path,
    path_to_new_page: Path,
    page_date: date,
    image_title: str,
) -> None:
    """
    Updates the archive to include a specified page.

    Args:
        template_dir (Path): The path to the template directory.
        archive_path (Path): The path to the archive directory.
        path_to_new_page (Path): The path to the page to be added to the archive.
        page_date (date): Date of page creation.
        image_title (str): Title of the image contained in the page.
    """
    daily_archive_path = Path(archive_path, "daily_list", "index.html")
    add_link_to_archive_list(
        daily_archive_path, path_to_new_page, page_date, image_title
    )
    try:
        year = page_date.strftime("%Y")
        month = page_date.strftime("%B").lower()
        month_file = Path(archive_path, year, month, "index.html")
        soup = soup_from_file(month_file)
    except FileNotFoundError:
        template_path = Path(template_dir, "archive_month.html")
        main_archive_path = Path(archive_path, "index.html")
        add_month_to_archive(template_path, month_file, main_archive_path, year, month)
        soup = soup_from_file(month_file)

    ordered_list = soup.find("ol", {"class": "archive_list"})
    html_to_insert = """<li><span>%s</span><a href=%s>%s</a></li>""" % (
        page_date.strftime("%d"),
        path_to_new_page,
        image_title,
    )
    list_element = ordered_list.find_next("li")
    try:
        list_element.insert_before(BeautifulSoup(html_to_insert, "html.parser"))
    except AttributeError:
        html_to_insert = "<ol class='archive_list'>%s</ol>" % html_to_insert
        ordered_list.replace_with(BeautifulSoup(html_to_insert, "html.parser"))

    write_file(month_file, soup.prettify())


def get_links_from_archive_list(path_to_archive_overview: Path) -> List[str]:
    """
    Get all previously used jwst image site links.

    Args:
        path_to_archive_overview (Path): Path to the archive overview directory.

    Returns:
        List[str]: A list containing previously used urls.
    """
    soup = soup_from_file(Path(path_to_archive_overview, "daily_list", "index.html"))
    list_items = soup.find_all("li")
    return [list_item.find("a")["data-jwst_url"] for list_item in list_items]


def get_date_of_current_page(path_to_main_index: Path) -> date:
    """
    Get the date of the current home page.

    Args:
        path_to_main_index (Path): Path of the main intex file.

    Returns:
        date: A datetime.date object containing the date of the current home page.
    """
    soup = soup_from_file(path_to_main_index)
    date_contents = soup.find("meta", {"content": re.compile("0; URL=*")})[
        "content"
    ].split("/")[-3:]
    return datetime.strptime("".join(date_contents), "%Y%B%d").date()
