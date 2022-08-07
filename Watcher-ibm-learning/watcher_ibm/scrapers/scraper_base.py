import asyncio
import logging
from typing import List, Any, Coroutine

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from watcher_ibm.http import get
from watcher_ibm.scrapers.base_scraper import BaseScraper
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger("watcher_ibm")


class UdemyScraper(BaseScraper):
    """
    Contains any logic related to scraping of data from ibm-learning.udemy.com
    """

    DOMAIN = "https://ibm-learning.udemy.com"

    def __init__(self, enabled, driver, max_pages=None):
        super().__init__(driver)

        self.scraper_name = "ibm-learning.udemy"
        if not enabled:
            self.set_state_disabled()
        self.max_pages = max_pages

    @BaseScraper.time_run
    async def run(self) -> List[str]:
        """
        Called to gather the udemy links

        :return: List of udemy course links
        """
        links = await self.get_links()
        logger.info(
            f"Page: {self.current_page} of {self.last_page} scraped from ibm-learning.udemy.com"
        )
        self.max_pages_reached()
        return links[1]

    async def get_links(self) -> tuple[List[str], List[str]]:
        """
        Scrape udemy links from ibm-learning.udemy.com

        :return: List of udemy course urls
        """

        self.current_page += 1
        # /home/my-courses/learning/?p=1
        coupons_data = await get(f"{self.DOMAIN}/home/my-courses/learning/?p={self.current_page}", driver=self.driver)
        soup = BeautifulSoup(coupons_data, "html.parser")
        # print(coupons_data)
        try:
            div_containing_rel_links = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".my-courses__course-card-grid"))
            )
            logger.info("Found the courses element")
            # rel_links=BeautifulSoup(div_containing_rel_links.get_attribute("innerHTML"), "html.parser")
            # udemy_links = self.get_relevant_links(rel_links)
            # for counter, course in enumerate(udemy_links):
            #     logger.debug(f"Received Link {counter + 1} : {course}")

            soup = self.driver.find_element_by_xpath("/html/body")
            all_links = BeautifulSoup(soup.get_attribute("innerHTML"), "html.parser")
            all_udemy_links = self.get_relevant_links(all_links)
            for counter, course in enumerate(all_udemy_links):
                logger.debug(f"All_links Received Link {counter + 1} : {course}")

        except TimeoutException:
            raise TimeoutException("TimeoutException: Unable to find the main content element")

        links_grp, links_crs = await self.gather_course_links_from_top(all_udemy_links)
        for counter, course in enumerate(links_grp):
            logger.debug(f"Received grp Link {counter + 1} : {course}")
        for counter, course in enumerate(links_crs):
            logger.debug(f"Received crs Link {counter + 1} : {course}")
        # if links:
        #     new_lins = await self.gather_udemy_course_links(links)

        # for counter, course in enumerate(links):
        #     logger.debug(f"Received Link {counter + 1} : {course}")

        self.last_page = self._get_last_page()

        return links_grp, links_crs

    def get_relevant_links(self, soup):
        udemy_links = []
        # url_end = course_card["href"].split("/")[-1]
        for course_card in soup.find_all("a"):
            if course_card.get("href") is not None:
                complete_url = f"{self.DOMAIN}{course_card['href']}"
                udemy_links.append(complete_url)

        return udemy_links

    async def gather_course_links_from_top(self, courses: List[str]) -> tuple:
        """
        Async fetching of the udemy course links from ibm-learning.udemy.com

        :param list courses: A list of ibm-learning.udemy.com course links we want to fetch the udemy links for
        :return: list of udemy links
        """
        list_of_grp = []
        list_of_crs = []
        for tuple in await asyncio.gather(*map(self.validate_courses_url, courses)):
            if tuple[1] is not None :
                if tuple[0] == 0:
                    list_of_grp.append(tuple[1])
                else:
                    list_of_crs.append(tuple[1])
        return list_of_grp, list_of_crs

    async def get_udemy_course_link(self, url: str) -> Coroutine[Any, Any, str | None]:
        """
        Gets the udemy course link

        :param str url: The url to scrape data from
        :return: Coupon link of the udemy course
        """

        data = await get(url, driver=self.driver)
        soup = BeautifulSoup(data, "html.parser")
        for link in soup.find_all("a", href=True):
            udemy_link = super().validate_course_url(link["href"])
            if udemy_link is not None:
                return udemy_link

    async def gather_udemy_course_links(self, courses: List[str]):
        """
        Async fetching of the udemy course links from ibm-learning.udemy.com

        :param list courses: A list of ibm-learning.udemy.com course links we want to fetch the udemy links for
        :return: list of udemy links
        """
        return [
            link
            for link in await asyncio.gather(*map(self.get_udemy_course_link, courses))
            if link is not None
        ]

    def _get_last_page(self) -> int:
        """
        Extract the last page number to scrape

        :param self:
        :return: The last page number to scrape
        """
        # find all the pagination numbers
        max_page = 0
        try:
            page_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pagination--pagination--Xzx5q"))
            )
            logger.info("Found the pagination element")
        except TimeoutException:
            raise TimeoutException("TimeoutException: Unable to find the pagination element")
        soup = BeautifulSoup(page_elements.get_attribute("innerHTML"), "html.parser")
        all_the_pages = soup.find_all("a")
        for x in all_the_pages:
            # print(f"printing text inside the <a> tags pag: {x.text}")
            try:
                if int(x.text) > max_page:
                    max_page = int(x.text)
            except ValueError:
                # logger.error("ValueError: Unable to convert the text to int")
                pass

        return max_page
