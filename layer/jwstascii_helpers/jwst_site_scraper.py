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

    def get_image_download_url(self, html: str) -> str:
        """
        Retrieves a valid image url from the provided jwst image page html.

        Args:
            html (str): Html for jwst website image page.

        Raises:
            ValueError: Raises value error if it is unable to find link in page.

        Returns:
            str: Url of the image.
        """
        soup = BeautifulSoup(html, "lxml")
        link_list = soup.find("div", {"class": "media-library-links-list"})

        if not link_list:
            raise ValueError("Unable to locate download link list in html: \n%s" % html)

        link_priority_regex = [
            re.compile(r"2000\s?x\s?\d+.*PNG.*", re.I),  # 2k PNG file
            re.compile(r"full\sres.*\d+\s?x\s?\d+.*PNG.*", re.I),  # Full res PNG
            re.compile(r"full\sres.*\d+\s?x\s?\d+.*TIF.*", re.I),  # Full res tif
        ]

        # Due to inner elements in the <a> tags, we cannot simply search by
        #   link_list.find('a', string=regex). The .string attribute resolves
        #   to None in this instance.
        link_list = link_list.find_all(
            "a", href=[re.compile(r".*.png"), re.compile(r".*.tif")]
        )

        for regex in link_priority_regex:
            for link in link_list:
                if re.match(regex, str(link.text)):
                    break
                else:
                    link = None
            if link:
                break

        if not link:
            raise ValueError(
                "Unable to locate valid download link in html: \n%s" % html
            )

        url = link["href"]

        if url.startswith("//"):
            url = "https:" + url

        return url

    def get_image_title(self, html: str) -> str:
        """
        Scrapes image title from page head meta tags.

        Args:
            html (str): Html of jwst image webpage.

        Raises:
            ValueError: Raises if the title cannot be located in the meta tags.

        Returns:
            str: A string containing the title of the image.
        """
        try:
            soup = BeautifulSoup(html, "lxml", parse_only=SoupStrainer("meta"))
            return soup.find("meta", property="og:title")["content"]
        except TypeError:
            raise ValueError("Could not find title in meta tags. \n%s" % html)
