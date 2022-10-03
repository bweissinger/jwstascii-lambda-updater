from rvmendillo_image_to_ascii import ImageToASCII


def convert_image(image_path: str, num_columns: int, output_path: str) -> None:
    """
    Converts provided image into a colored ascii art image. Recommended to use
    png as the image extension

    Args:
        image_path (str): File path of the input image.
        num_columns (int): Number of text columns to use during conversion.
            200 columns is a good starting point.
        output_path (str): File path for the output image.
    """
    app = ImageToASCII(image_path)
    image = app.generate_colored_ascii_image(num_columns)
    app.save_image(image, output_path)
