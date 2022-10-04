import jinja2
from pathlib import Path


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
