import re
from bs4 import BeautifulSoup, SoupStrainer


class Scraper:
    def get_image_description(self, html: str) -> str:
        """
        Scrapes the description text html for the provided jwst image page.

        Args:
            html (str): The html of the jwst image page.

        Returns:
            str: String of scraped description html.

        Raises:
            ValueError: Raised if image description cannot be found.
        """

        soup = BeautifulSoup(html, "lxml")
        header = soup.find("h4", string=re.compile("about", re.I))

        if not header or not soup.find("footer"):
            raise ValueError(
                "Could not find image description on page. This is caused by a missing header or footer. Provided html: \n'%s'"
                % html
            )

        image_description = ""
        for sibling in header.next_siblings:
            if sibling.name == "footer":
                break
            image_description += str(sibling)

        strainer = SoupStrainer(["a", "p"])
        return str(BeautifulSoup(image_description, "lxml", parse_only=strainer))
