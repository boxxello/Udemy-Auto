import asyncio
from functools import reduce
from typing import List

from watcher_udemy.scrapers.scraper_base import UdemyScraper



class ScraperManager:
    def __init__(
            self,
            udemy_scraper_enabled: bool,
            max_pages,
            driver,
            settings
    ):

        self.udemy_scraper = UdemyScraper(
            udemy_scraper_enabled,driver,settings,max_pages=max_pages
        )
        self._scrapers = (
            self.udemy_scraper,
        )

    async def run(self) -> List:
        """
        Runs any enabled scrapers and returns a list of links

        :return: list
        """
        urls = []
        enabled_scrapers = self._enabled_scrapers()
        if enabled_scrapers:
            urls = reduce(
                list.__add__,
                await asyncio.gather(*map(lambda sc: sc.run(), enabled_scrapers)),
            )
        return urls

    def _enabled_scrapers(self) -> List:
        """
        Returns a list of scrapers that should run

        :return:
        """
        return list(filter(lambda sc: sc.should_run(), self._scrapers))
