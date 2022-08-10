import argparse
import logging
from argparse import Namespace
from typing import Tuple, Union

from watcher_ibm import ALL_VALID_BROWSER_STRINGS, DriverManager, Settings
from watcher_ibm.logging import get_logger
from watcher_ibm.runner import redeem_courses_ui, redeem_courses

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
    :param bool tutorialbar_enabled:
    :param bool discudemy_enabled:
    :param int max_pages: Max pages to scrape from sites (if pagination exists)
    :param bool delete_settings: Determines if we should delete old settings file
    :param bool delete_cookie: Determines if we should delete the cookie file
    :return:
    """
    settings = Settings(delete_settings, delete_cookie)
    print("ci arrivo")

    if browser:
        dm = DriverManager(browser=browser, is_ci_build=settings.is_ci_build)
        print("ci arrivo browser")
        redeem_courses_ui(
            dm.driver,
            settings,
            udemy_scraper_enabled,
            max_pages,
            scrape_urls_from_file,
            filename
        )
    else:
        browser = "chrome"
        dm = DriverManager(browser=browser, is_ci_build=settings.is_ci_build)
        print("ci arrivo no browser")
        redeem_courses(
            dm.driver,
            settings,
            udemy_scraper_enabled,
            max_pages,

        )


def parse_args() -> Namespace:
    """
    Parse args from the CLI or use the args passed in

    :return: Args to be used in the script
    """
    parser = argparse.ArgumentParser(description="Udemy Enroller")
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
        "--tutorialbar",
        action="store_true",
        default=False,
        help="Run tutorialbar scraper",
    )

    parser.add_argument(
        "--discudemy",
        action="store_true",
        default=False,
        help="Run discudemy scraper",
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
        default=True,
        help="Enable scraping from file ",
    )

    args = parser.parse_args()
    print(args)
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
