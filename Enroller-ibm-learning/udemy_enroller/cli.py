import argparse
import logging
from argparse import Namespace
from typing import Tuple, Union

from udemy_enroller import ALL_VALID_BROWSER_STRINGS, DriverManager, Settings
from udemy_enroller.logging import get_logger
from udemy_enroller.runner import redeem_courses, redeem_courses_ui

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


def determine_if_scraper_enabled(
        udemy_scraper_enabled: bool,
        tutorialbar_enabled: bool,
        discudemy_enabled: bool,

) -> tuple[bool, bool, bool]:
    """
    Determine what scrapers should be enabled and disabled

    :return: tuple containing boolean of what scrapers should run
    """
    if (
            not udemy_scraper_enabled and
            not tutorialbar_enabled
            and not discudemy_enabled

    ):
        # Set all to True
        (udemy_scraper_enabled,
         tutorialbar_enabled,
         discudemy_enabled
         ) = (True, True, True)

    return (
        udemy_scraper_enabled,
        tutorialbar_enabled,
        discudemy_enabled,
    )


def run(
        browser: str,
        udemy_scraper_enabled: bool,
        tutorialbar_enabled: bool,
        discudemy_enabled: bool,

        max_pages: Union[int, None],
        delete_settings: bool,
        delete_cookie: bool,
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
        global dm
        dm = DriverManager(browser=browser, is_ci_build=settings.is_ci_build)
        redeem_courses_ui(
            dm.driver,
            settings,
            udemy_scraper_enabled,
            tutorialbar_enabled,
            discudemy_enabled,
            max_pages,
        )
    else:
        redeem_courses(
            settings,
            udemy_scraper_enabled,
            tutorialbar_enabled,
            discudemy_enabled,
            max_pages,
        )


def parse_args() -> Namespace:
    """
    Parse args from the CLI or use the args passed in

    :return: Args to be used in the script
    """
    parser = argparse.ArgumentParser(description="Udemy Enroller")
    print(ALL_VALID_BROWSER_STRINGS)
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

    args = parser.parse_args()
    print(args)
    return args


def main():
    args = parse_args()
    if args:
        if args.debug:
            enable_debug_logging()
        (
            udemy_scraper_enabled,
            tutorialbar_enabled,
            discudemy_enabled,

        ) = determine_if_scraper_enabled(
            args.udemybase,args.tutorialbar, args.discudemy
        )
        run(
            args.browser,
            udemy_scraper_enabled,
            tutorialbar_enabled,
            discudemy_enabled,

            args.max_pages,
            args.delete_settings,
            args.delete_cookie,
        )
