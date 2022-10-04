import jinja2
from pathlib import Path
from os import makedirs
from os.path import exists
from typing import Dict


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
