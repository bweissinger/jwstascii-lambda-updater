import jinja2
from pathlib import Path
from os import makedirs
from os.path import exists


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


def generate_main_index(
    template_dir: Path, output_path: Path, title: str, parent_dir_of_new_page: Path
) -> None:
    """
    Generates the main index html file from a jinja template.

    Args:
        template_dir (Path): Path of directory where jinja templates are stored.
        output_path (Path): Path to save the generated html file.
        title (str): Title string to render in template.
        parent_dir_of_new_page (Path): Path to the page that the index file will redirect to.
    """
    template = get_jinja_template(Path(template_dir, "main_index.html"))
    output_html = template.render(
        title=title,
        page_parent_dir=str(parent_dir_of_new_page),
    )
    write_file(output_path, output_html)


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
