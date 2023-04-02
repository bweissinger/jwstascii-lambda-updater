from jwstascii_helpers.rvmendillo_image_to_ascii import ImageToASCII
from os import makedirs
from os.path import exists
from pathlib import Path


def convert_image(
    image_path: str, num_columns: int, charset: str, output_path: str
) -> None:
    """
    Converts provided image into a colored ascii art image. Recommended to use
    png as the image extension

    Args:
        image_path (str): File path of the input image.
        num_columns (int): Number of text columns to use during conversion.
            200 columns is a good starting point.
        charset (str): String containing characters to be used in image creation.
        output_path (str): File path for the output image. Directories will be
            created if they do not exist.
    """
    app = ImageToASCII(image_path, charset=charset)
    image = app.generate_colored_ascii_image(num_columns)

    parent_directory = Path(output_path).parent
    if not exists(parent_directory):
        makedirs(parent_directory)
    app.save_image(image, output_path)
