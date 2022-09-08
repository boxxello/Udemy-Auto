import asyncio
import logging
import time
from typing import List, Any, Coroutine

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from watcher_udemy.http import get
from watcher_udemy.scrapers.base_scraper import BaseScraper
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger("watcher_udemy")


class UdemyScraper(BaseScraper):
    """
    Contains any logic related to scraping of data from business domain.udemy.com
    """


    def __init__(self, enabled, driver,settings):
        super().__init__(driver,settings)
        self.DOMAIN_BUSINESS_FULL=f"https://{self.settings.domain}.udemy.com"
        self.scraper_name = "udemy_watcher.solver"
        if not enabled:
            self.set_state_disabled()

    @BaseScraper.time_run
    async def run(self) -> List[str]:
        """
        Called to gather the udemy links

        :return: List of udemy course links
        """
        links = await self.get_links(self.settings.domain)
        return links[1]

    async def get_links(self, domain) -> tuple[List[str], List[str]]:
        """
        Scrape udemy links from domain

        :return: List of udemy course urls
        """
        logger.debug("Arrivo a get_links")
        # /home/my-courses/learning/?p=1
        course_linkss = await get(f"https://{domain}.udemy.com/organization/home/", driver=self.driver)
        logger.debug("Arrivo anche dopo il get di get_links")
        soup = BeautifulSoup(course_linkss, "html.parser")
        try:
            # button_of_any_container="//div[@data-purpose='container']"
            WebDriverWait(self.driver, 10). \
                until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            time.sleep(10)
            # div_containing_rel_links = WebDriverWait(self.driver, 20).until(
            #     EC.presence_of_element_located((By.XPATH, button_of_any_container))
            # )
            logger.info("Found the courses element")
            # rel_links=BeautifulSoup(div_containing_rel_links.get_attribute("innerHTML"), "html.parser")
            # udemy_links = self.get_relevant_links(rel_links)
            # for counter, course in enumerate(udemy_links):
            #     logger.debug(f"Received Link {counter + 1} : {course}")

            soup = self.driver.find_element(By.XPATH,"/html/body")
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

        return links_grp, links_crs

    def get_relevant_links(self, soup):
        udemy_links = []
        # url_end = course_card["href"].split("/")[-1]
        for course_card in soup.find_all("a"):
            if course_card.get("href") is not None:
                complete_url = f"{self.DOMAIN_BUSINESS_FULL}{course_card['href']}"
                udemy_links.append(complete_url)

        return udemy_links

    async def gather_course_links_from_top(self, courses: List[str]) -> tuple:
        """
        Async fetching of the udemy course links from domain

        :param list courses: A list of udemy business course links we want to fetch the udemy links for
        :return: list of udemy links
        """
        list_of_grp = []
        list_of_crs = []

        for tuple in await asyncio.gather(*map(lambda course: self.validate_courses_url(course, self.settings.domain), courses)):
            if tuple[1] is not None :
                if tuple[0] == 0:
                    list_of_grp.append(tuple[1])
                else:
                    list_of_crs.append(tuple[1])
        return list_of_grp, list_of_crs
    #we use coroutines and add the typing hint Any Any for .send() and .throw() defaults.
    #this typing hint str | None is actually new, from 3.10, 3.8 would have been Union[str, None]
    async def get_udemy_course_link(self, url: str) -> Coroutine[Any, Any, str | None]:
        """
        Gets the udemy course link

        :param str url: The url to scrape data from
        :return: Coupon link of the udemy course
        """

        data = await get(url, driver=self.driver)
        soup = BeautifulSoup(data, "html.parser")
        for link in soup.find_all("a", href=True):
            udemy_link = super().validate_course_url(link["href"], self.settings.domain)
            if udemy_link is not None:
                return udemy_link

    async def gather_udemy_course_links(self, courses: List[str]):
        """
        Async fetching of the udemy course links from domain

        :param list courses: A list of udemy business course links  we want to fetch the udemy links for
        :return: list of udemy links
        """
        return [
            link
            for link in await asyncio.gather(*map(self.get_udemy_course_link, courses))
            if link is not None
        ]


