import re
from bs4 import BeautifulSoup, SoupStrainer
from typing import List


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

    def get_image_credits(self, html: str) -> List[str]:
        """
        Parses image credits from the footer of a jwst website image page.

        Args:
            html (str): Html of jwst website image page.

        Raises:
            ValueError: Raises value error if no footer is found, if no image prefix
                is found, or if the resulting credits list is blank.

        Returns:
            List[str]: A list of the image credits parsed from the page.
        """
        soup = BeautifulSoup(html, "lxml")
        footer = soup.find("footer")

        if not footer:
            raise ValueError("Could not find footer in html: \n%s" % html)

        credits = footer.find("p", string=re.compile("IMAGE:*", re.I))

        if not credits:
            raise ValueError(
                "Could not find credits image prefix in footer: \n%s" % html
            )

        credits_list = []
        for credit in credits.text.split(":")[1].split(","):
            credit = credit.replace(" ", "")
            if credit:
                credits_list.append(credit)

        if not credits_list:
            raise ValueError("No credits parsed from html: \n%s" % html)

        return credits_list
