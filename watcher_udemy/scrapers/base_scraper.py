import datetime
import logging
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

logger = logging.getLogger("watcher_udemy")


class ScraperStates(Enum):
    DISABLED = "DISABLED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"


class BaseScraper(ABC):
    def __init__(self, driver, settings):
        self.settings=settings
        self.driver = driver
        self._state = None
        self.scraper_name = None

    @abstractmethod
    async def run(self):
        return

    @abstractmethod
    async def get_links(self, *args, **kwargs):
        return

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if any([ss for ss in ScraperStates if ss.value == value]):
            self._state = value

    def set_state_disabled(self):
        self.state = ScraperStates.DISABLED.value
        logger.info(f"{self.scraper_name} scraper disabled")

    def set_state_running(self):
        self.state = ScraperStates.RUNNING.value
        logger.info(f"{self.scraper_name} scraper is running")

    def set_state_complete(self):
        self.state = ScraperStates.COMPLETE.value
        logger.info(f"{self.scraper_name} scraper complete")

    def is_disabled(self):
        return self.state == ScraperStates.DISABLED.value

    def is_complete(self):
        return self.state == ScraperStates.COMPLETE.value

    def should_run(self):
        should_run = not self.is_disabled() and not self.is_complete()
        if should_run:
            self.set_state_running()
        return should_run

    @staticmethod
    def time_run(func):
        async def wrapper(self):
            start_time = datetime.datetime.utcnow()
            try:
                response = await func(self)
            except Exception as e:
                logger.error(f"Error while running scraper: {e}", exc_info=True)
                self.is_complete()
                return []
            end_time = datetime.datetime.utcnow()
            logger.info(
                f"Function get_links finished in {(end_time - start_time).total_seconds():.2f} seconds"
            )
            return response

        return wrapper


    @staticmethod
    async def  validate_courses_url(url, domain)->tuple:
        url_pattern_grp_crs = rf"^https:\/\/(www\.)?{domain}\.udemy\.com\/courses\/.+\/..*$"
        # https://regex101.com/r/1E6RsB/1
        # https://regex101.com/r/yl2S3g/1

        url_pattern_course=rf"https:\/\/(www\.)?{domain}\.udemy\.com\/course-dashboard-redirect\/\?course_id=\d+.*$"
        url_pattern_course2 = rf"^https:\/\/(www\.)?{domain}\.udemy\.com\/course\/.*$"
        #https://regex101.com/r/ChoWhS/1
        #https://regex101.com/r/KHpL7F/1
        matching = re.match(url_pattern_grp_crs, url)

        if matching is not None:
            matching = matching.group()
            return 0, matching
        else:
            matching = re.match(url_pattern_course, url) or re.match(url_pattern_course2, url)
            if matching is not None:
                matching = matching.group()
                return 1, matching
            else:
                return None, None


    @staticmethod
    async def  validate_course_url(url, domain) -> Optional[str]:
        """
        Validate the udemy coupon url passed in
        If it matches the pattern it is returned else it returns None

        :param url: The url to check the udemy coupon pattern for
        :return: The validated url or None
        """
        url_pattern = fr"https:\/\/(www\.)?{domain}\.udemy\.com\/course\/.*$"
        #https://regex101.com/r/7bdkol/1
        matching = re.match(url_pattern, url)
        if matching is not None:
            matching = matching.group()
        return matching
