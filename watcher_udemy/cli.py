import argparse
import logging
import os.path
from argparse import Namespace
from pathlib import Path
from typing import Tuple, Union

from watcher_udemy import ALL_VALID_BROWSER_STRINGS, DriverManager, Settings
from watcher_udemy.logging import get_logger
from watcher_udemy.runner import watch_courses_ui

logger = get_logger()


def enable_debug_logging() -> None:
    """
    Enable debug logging for the scripts

    :return: None
    """
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)
    logger.info(f"Enabled debug logging")





def run(
        browser: str,
        udemy_scraper_enabled: bool,
        max_pages: Union[int, None],
        delete_settings: bool,
        delete_cookie: bool,
        scrape_urls_from_file: bool,
        filename: str
):
    """
    Run the udemy enroller script

    :param str browser: Name of the browser we want to create a driver for
    :param bool udemy_scraper_enabled: Boolean signifying if udemy scraper scraper should run
    :param int max_pages: Max pages to scrape from sites (if pagination exists)
    :param bool delete_settings: Determines if we should delete old settings file
    :param bool delete_cookie: Determines if we should delete the cookie file
    :return:
    """
    settings = Settings(delete_settings, delete_cookie)
    if browser:
        dm = DriverManager(browser=browser)
        logger.debug("ci arrivo browser")
        if udemy_scraper_enabled:
            if scrape_urls_from_file:
                if os.path.exists(filename) and filename.endswith('.txt'):
                    watch_courses_ui(
                        dm.driver,
                        settings,
                        udemy_scraper_enabled,
                        max_pages,
                        scrape_urls_from_file,
                        filename
                    )
                else:
                    logger.error("The file you provided either doesn't have a .txt extension or"
                                 " doesn't actually exist.")
                    exit(-4)
            else:
                watch_courses_ui(
                    dm.driver,
                    settings,
                    udemy_scraper_enabled,
                    max_pages,
                    scrape_urls_from_file,
                    filename
                )
        else:
            logger.error("EXITING DUE TO NO SCRAPER ENABLED, "
                         "FUTURE IMPLEMENTATION INCOMING SOON")
            exit(-3)



def parse_args() -> Namespace:
    """
    Parse args from the CLI or use the args passed in

    :return: Args to be used in the script
    """
    parser = argparse.ArgumentParser(description="Watcher-udemy-learning")
    parser.add_argument(
        "--browser",
        required=False,
        type=str,
        choices=ALL_VALID_BROWSER_STRINGS,
        default="chrome",
        help="Browser to use for Udemy Enroller",
    )
    parser.add_argument(
        "--udemybase",
        action="store_true",
        default=True,
        help="Run base udemy scraper",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help=f"Max pages to scrape from sites (if pagination exists) (Default is 5)",
    )

    parser.add_argument(
        "--delete-settings",
        action="store_true",
        default=False,
        help="Delete any existing settings file",
    )

    parser.add_argument(
        "--delete-cookie",
        action="store_true",
        default=False,
        help="Delete existing cookie file",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=True,
        help="Enable debug logging",
    )
    parser.add_argument(
        "--file",
        action="store_true",
        default="file.txt",
        help="Name of the file you want to scrape urls from",
    )
    parser.add_argument(
        "--scrape_from_file",
        action="store_true",
        default=False,
        help="Enable scraping from file ",
    )

    args = parser.parse_args()
    logger.debug(args)
    return args


def main():
    args = parse_args()
    if args:
        if args.debug:
            enable_debug_logging()

        run(
            args.browser,
            args.udemybase,

            args.max_pages,
            args.delete_settings,
            args.delete_cookie,
            args.scrape_from_file,
            args.file
        )
