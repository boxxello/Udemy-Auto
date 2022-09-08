import asyncio
from typing import Union
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from watcher_udemy import (
    ScraperManager,
    Settings,
    UdemyActionsUI,
    UdemyStatus,
    exceptions,
)
from watcher_udemy.exceptions import CourseNotFoundException
from watcher_udemy.logging import get_logger
from watcher_udemy.utils import read_urls_from_file

logger = get_logger()


def _watch_courses_ui(

        driver,
        settings: Settings,
        scrapers: ScraperManager,
        get_random_links: bool,
        scrape_urls_from_file: bool,
        filename: str,
) -> None:
    """
    Method to scrape courses from the supported sites and enroll in them on udemy.

    :param WebDriver driver: WebDriver to use to complete enrolment
    :param Settings settings: Core settings used for Udemy
    :param ScraperManager scrapers:
    :return:
    """
    list_of_error_links = []
    logger.info("Creating the UdemyActionsUI object")
    udemy_actions = UdemyActionsUI(driver, settings)
    udemy_actions.login()

    loop = asyncio.get_event_loop()

    logger.info("launching the scrapers")

    if scrape_urls_from_file and filename:
        udemy_course_links = read_urls_from_file(filename)

        logger.info(f"LINKS FROM FILE {udemy_course_links}")
        # udemy_course_ids=[]
        # for x in udemy_course_links:
        #     crs_id=udemy_actions._get_course_id(x)
        #     logger.info(f"COURSE ID {crs_id}")
        #     if crs_id is not None and crs_id not in udemy_course_ids:
        #         udemy_course_ids.append(crs_id)
        # logger.info(f"COURSE IDs {udemy_course_ids}")
        # if len(udemy_course_ids)>0:
        #     udemy_course_links = []
        #     for x in udemy_course_ids:
        #         udemy_course_links.append(udemy_actions.URL_TO_COURSE_ID.format(x))
        # logger.info(f"Real course links {udemy_course_links}")


    elif scrape_urls_from_file and not filename:
        logger.error("this isn't a possible choice.")
        return
    else:

        udemy_course_progress_id = udemy_actions._get_already_rolled_courses()
        udemy_course_links = []
        for x in udemy_course_progress_id:
            udemy_course_links.append(udemy_actions.URL_TO_COURSE_ID.format(x))

        logger.debug("OLEE")
        if get_random_links:
            new_links = loop.run_until_complete(scrapers.run())
            logger.debug("NEW LINKS: {}".format(new_links))
            logger.info(f"LINKS FROM PAGE {udemy_course_links}")
            udemy_course_links.extend(new_links)

    while True:
        if udemy_course_links:
            for course_link in set(
                    udemy_course_links
            ):  # Cast to set to remove duplicate links

                try:
                    try:
                        cs_link, course_id = udemy_actions._get_course_link_wrapper(course_link, settings.domain)
                        logger.info("In the courses already rolled ")
                        status = UdemyStatus.ALREADY_ENROLLED.value
                    except CourseNotFoundException:
                        logger.info("Not in a rolled in course")
                        status, cs_link, course_id = udemy_actions.enroll(course_link)
                        pass
                    if status == UdemyStatus.ENROLLED.value or status == UdemyStatus.ALREADY_ENROLLED.value:

                        logger.info(f"Enrolled/Already enrolled in {cs_link}, trying to get it to finish")
                        course_details = udemy_actions._get_course_details(course_id)
                        course_details_complt = course_details.get('completion_ratio')
                        course_details_has_quizzes = course_details.get('num_quizzes')
                        if course_details_complt != 100:
                            if str(course_details_has_quizzes) == '0':
                                logger.info("It has got NO quizzes in it")
                            else:
                                logger.info("It has got quizzes in it")
                                # udemy_actions._solve_quiz(course_id)
                                udemy_actions._solve_single_quiz_test(course_id)
                            print(f"course link {cs_link}")
                            list_of_lectures_id = udemy_actions._get_all_lectures_id(cs_link)

                            logger.info(f"Printing list of lectures of {cs_link}: {list_of_lectures_id}")
                            print(udemy_actions._send_completition_req(cs_link, list_of_lectures_id, course_id,
                                                                       settings.domain))
                            course_details = udemy_actions._get_course_details(course_id)
                            course_details_complt = course_details['completion_ratio']
                            if course_details_complt != 100:
                                list_of_error_links.append(course_link)

                        else:
                            logger.info("Course was already finished")

                    udemy_course_links.remove(course_link)


                except NoSuchElementException as e:
                    logger.error(f"No such element: {e}")
                except TimeoutException:
                    logger.error(f"Timeout on link: {course_link}")
                except WebDriverException:
                    logger.error(f"Webdriver exception on link: {course_link}")
                except KeyboardInterrupt:
                    udemy_actions.stats.table()
                    logger.warning("Exiting the script")
                    return
                except exceptions.RobotException as e:
                    logger.error(e)
                    return
                except Exception as e:
                    logger.error(f"Unexpected exception: {e}", exc_info=True)
        else:
            udemy_actions.stats.table()
            if len(list_of_error_links) > 0:
                logger.warning(f"List of error links: {list_of_error_links}")
            logger.info("All scrapers complete")
            return


def watch_courses_ui(
        driver,
        settings: Settings,
        udemy_scraper_enabled: bool,
        get_random_links: bool,
        scrape_urls_from_file: bool,
        filename: str
) -> None:
    """
    Wrapper of _redeem_courses so we always close browser on completion

    :param WebDriver driver: WebDriver to use to complete enrolment
    :param Settings settings: Core settings used for Udemy
    :param bool udemy_scraper_enabled: Boolean signifying if udemy scraper scraper should run

    :return:
    """

    try:
        scrapers = ScraperManager(
            udemy_scraper_enabled,
            driver, settings
        )
        _watch_courses_ui(driver, settings, scrapers, get_random_links, scrape_urls_from_file, filename)
    except Exception as e:
        logger.error(f"Exception in redeem courses: {e}", exc_info=True)
    finally:
        logger.info("Closing browser")
        driver.quit()
