from datetime import date
import jinja2
from pathlib import Path
from os import makedirs
from os.path import exists
from typing import Dict
from bs4 import BeautifulSoup


def get_jinja_template(template_path: Path) -> jinja2.Template:
    """
    Load the requested template.

    Args:
        template_path (Path): Path object for the template file.

    Returns:
        jinja2.Template: The requested jinja2 template.
    """
    template_loader = jinja2.FileSystemLoader(searchpath=template_path.parent)
    template_env = jinja2.Environment(loader=template_loader, autoescape=True)
    return template_env.get_template(template_path.name)


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
    template_path: Path, output_path: Path, vars_dict: Dict[str, str]
) -> None:
    """
    Function for generating html from a jinja template.

    Args:
        template_path (Path): Path of the desired template.
        output_path (Path): Path of the resulting html file.
        vars_dict (Dict[str, str]): Dictionary containing template variables and their
            values to be assigned.
    """
    template = get_jinja_template(template_path)
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
    except AttributeError as e:
        raise RuntimeError(
            """It looks like the next page element was not found, cannot set
             the href on a null reference. \n%s"""
            % e
        )

    write_file(path_to_html, soup.prettify())


def soup_from_file(file_path: Path):
    """
    Get a BeautifulSoup object of the selected file.

    Args:
        file_path (Path): Path of the file to parse.

    Returns:
        BeautifulSoup: BeautifulSoup object of the parsed file.
    """
    with open(file_path, "r") as file:
        return BeautifulSoup(file.read(), "lxml")
